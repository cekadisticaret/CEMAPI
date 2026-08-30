"""Korner piyasa oranı — Pinnacle 'related markets' (special) uç noktası.

book_odds.py'nin ana akışına dokunmadan aynı Pinnacle guest API'sini
kullanır. DİKKAT: bu uç nokta (`/matchups/{id}/related`) ve korner
market'inin category/type alan adları, bu ortamdan pinnacle.com'a
network erişimi olmadığı için CANLI DOĞRULANAMADI — genel Pinnacle
Arcadia API kalıbına göre yazıldı (aynı /0.1 base, aynı auth deseni).

İlk çalıştırmada boş/None dönerse: `python3 -m bahis.corner_odds debug <lid>`
ile bir maçın ham /related yanıtını yazdırır — o JSON'u paylaş,
_CORNER_CATEGORY / _parse_related'i kesin alanlara göre düzeltirim.
Mevcut 1X2/O2.5 akışını bozmaz: her hata sessizce None döner.
"""
from __future__ import annotations

import json
import os
import sys
import time

from bahis.book_odds import DATA, PINN_LEAGUES, _PINN, _amer_dec, _get, _team_key

CACHE = os.path.join(DATA, "corner_odds.json")
TTL = 12 * 60
# Pinnacle "special" marketlerinde korner genelde bu kategori/başlık adlarıyla gelir.
# Doğrulanamadı — canlı yanıta göre genişlet/düzelt.
_CORNER_CATEGORY_HINTS = ("corner", "korner")
LINES = (8.5, 9.5, 10.5, 11.5)


def _load() -> dict:
    if not os.path.isfile(CACHE):
        return {"matches": {}, "updated": None}
    try:
        with open(CACHE, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            d.setdefault("matches", {})
            return d
    except (OSError, json.JSONDecodeError):
        pass
    return {"matches": {}, "updated": None}


def _save(pack: dict) -> None:
    os.makedirs(DATA, exist_ok=True)
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False)
    os.replace(tmp, CACHE)


def _fetch_matchup_ids(lid: str) -> list[dict]:
    pinn_id = PINN_LEAGUES[lid]
    matchups = _get(f"{_PINN}/leagues/{pinn_id}/matchups")
    if not isinstance(matchups, list):
        return []
    out = []
    for m in matchups:
        if m.get("type") != "matchup" or m.get("parentId"):
            continue
        parts = m.get("participants") or []
        home = next((p.get("name") for p in parts if p.get("alignment") == "home"), None)
        away = next((p.get("name") for p in parts if p.get("alignment") == "away"), None)
        if not home or not away or m.get("id") is None:
            continue
        out.append({"id": m["id"], "home": home, "away": away, "kickoff": m.get("startTime")})
    return out


def raw_related(matchup_id: int) -> list:
    """Ham /related yanıtı — alan adlarını doğrulamak için."""
    data = _get(f"{_PINN}/matchups/{matchup_id}/related")
    return data if isinstance(data, list) else []


def _parse_corner_total(related: list) -> dict | None:
    """related listesinden korner toplam O/U pazarını çıkarır.

    Beklenen (doğrulanmadı): related içindeki her eleman ayrı bir
    'sub-matchup'; special.category / special.description alanında
    'Corners' geçen ve type == 'total' olan market aranıyor.
    """
    for sub in related:
        special = sub.get("special") or {}
        cat = f"{special.get('category', '')} {special.get('description', '')}".lower()
        if not any(h in cat for h in _CORNER_CATEGORY_HINTS):
            continue
        # Pinnacle related-market gövdesi düz de gelebilir (markets/straight ile aynı şema)
        prices = sub.get("prices") or []
        line = None
        ou: dict[str, float] = {}
        for pr in prices:
            des = (pr.get("designation") or "").lower()
            pts = pr.get("points")
            d = _amer_dec(pr.get("price"))
            if des in ("over", "under") and d:
                ou[des] = d
                line = pts if pts is not None else line
        if len(ou) == 2 and line is not None:
            return {"line": float(line), "over": ou["over"], "under": ou["under"]}
    return None


def _fetch_league(lid: str) -> dict:
    rows = []
    for mu in _fetch_matchup_ids(lid):
        try:
            related = raw_related(mu["id"])
            ou = _parse_corner_total(related)
        except Exception:
            ou = None
        if not ou:
            continue
        rows.append({
            "hk": _team_key(mu["home"]),
            "ak": _team_key(mu["away"]),
            "kickoff": mu.get("kickoff"),
            "corner_ou": ou,
        })
    return {"ts": time.time(), "n": len(rows), "rows": rows, "ok": True}


def refresh_league(lid: str) -> dict:
    pack = _load()
    try:
        row = _fetch_league(lid)
    except Exception as e:
        old = dict(pack.get("matches", {}).get(lid) or {})
        old["ok"] = False
        old["err"] = str(e)[:160]
        pack.setdefault("matches", {})[lid] = old
        _save(pack)
        return old
    pack.setdefault("matches", {})[lid] = row
    _save(pack)
    return row


def ensure(lid: str, max_age: float = TTL) -> dict:
    pack = _load()
    row = pack.get("matches", {}).get(lid) or {}
    ts = float(row.get("ts") or 0)
    if row.get("rows") is not None and time.time() - ts < max_age:
        return row
    return refresh_league(lid)


def for_match(m: dict) -> dict | None:
    """dixon_coles/corners.py kartlarındaki maç dict'i için korner O/U döner, yoksa None."""
    lid = m.get("league")
    if not lid:
        from bahis.leagues_cfg import current_league
        lid = current_league()
    if lid not in PINN_LEAGUES:
        return None
    pack = ensure(lid)
    hk = (m.get("home") or {}).get("key")
    ak = (m.get("away") or {}).get("key")
    if not hk or not ak:
        return None
    for r in pack.get("rows") or []:
        if r.get("hk") == hk and r.get("ak") == ak:
            return r.get("corner_ou")
    return None


if __name__ == "__main__":
    # python3 -m bahis.corner_odds debug tr   -> ilk maçın ham /related yanıtını basar
    if len(sys.argv) >= 3 and sys.argv[1] == "debug":
        lid = sys.argv[2]
        mus = _fetch_matchup_ids(lid)
        if not mus:
            print("maç bulunamadı"); sys.exit(1)
        mu = mus[0]
        print(f"{mu['home']} - {mu['away']} (id={mu['id']})")
        print(json.dumps(raw_related(mu["id"]), ensure_ascii=False, indent=2)[:4000])
