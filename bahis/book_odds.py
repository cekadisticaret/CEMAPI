"""Canlı 1X2 / 2.5 / KG / çifte şans / handikap-1 / doğru skor — Pinnacle. Vekil yok."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE = os.path.join(DATA, "book_odds.json")
TTL = 12 * 60

# Pinnacle web guest — tarayıcının gönderdiği genel anahtar
_PINN_KEY = "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R"
_PINN = "https://guest.api.arcadia.pinnacle.com/0.1"

PINN_LEAGUES = {
    "tr": 2592,
    "epl": 1980,
    "laliga": 2196,
    "seriea": 2436,
    "bundesliga": 1842,
    "ligue1": 2036,
    "bra": 1834,
}

SRC_LABEL = {
    "pinnacle": "Pinnacle",
    "fd": "football-data B365/Avg",
}


def src_label(src: str | None) -> str:
    if not src or src == "h2h":
        return "oran yok"
    return SRC_LABEL.get(src, src)


def _amer_dec(p) -> float | None:
    try:
        a = float(p)
    except (TypeError, ValueError):
        return None
    if a > 0:
        return round(a / 100.0 + 1.0, 2)
    if a < 0:
        return round(100.0 / abs(a) + 1.0, 2)
    return None


def _get(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Referer": "https://www.pinnacle.com/",
            "X-API-Key": _PINN_KEY,
        },
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


def _load() -> dict:
    if not os.path.isfile(CACHE):
        return {"leagues": {}, "updated": None}
    try:
        with open(CACHE, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            d.setdefault("leagues", {})
            return d
    except (OSError, json.JSONDecodeError):
        pass
    return {"leagues": {}, "updated": None}


def _save(pack: dict) -> None:
    pack["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    os.makedirs(DATA, exist_ok=True)
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False)
    os.replace(tmp, CACHE)


def _team_key(name: str) -> str:
    from bahis.league import team_key
    return team_key(name)


def _ml_by_id(markets: list) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for x in markets:
        if x.get("type") == "moneyline" and x.get("period") == 0:
            mid = x.get("matchupId")
            if mid is not None:
                out[mid] = x
    return out


def _priced(special: dict, market: dict | None) -> list[tuple[str, float]]:
    if not market:
        return []
    parts = {p.get("id"): (p.get("name") or "") for p in (special.get("participants") or []) if p.get("id")}
    out = []
    for pr in market.get("prices") or []:
        d = _amer_dec(pr.get("price"))
        name = parts.get(pr.get("participantId"))
        if d and name:
            out.append((name, d))
    return out


def _parse_cs_name(name: str) -> str | None:
    import re
    m = re.search(r"(\d+)\D+(\d+)\s*$", name or "")
    if not m:
        return None
    return f"{int(m.group(1))}-{int(m.group(2))}"


def _parse_specials(matchups: list, markets: list, parent_id) -> dict:
    """FT specials: KG, çifte şans, handikap ev -1, doğru skor. Korner Pinnacle'da yok."""
    ml = _ml_by_id(markets)
    extras: dict = {}
    for m in matchups:
        if m.get("parentId") != parent_id or m.get("type") != "special":
            continue
        desc = ((m.get("special") or {}).get("description") or "").strip()
        priced = _priced(m, ml.get(m.get("id")))
        if not priced:
            continue
        if desc == "Both Teams To Score?":
            btts = {}
            for name, d in priced:
                key = (name or "").strip().lower()
                if key == "yes":
                    btts["yes"] = d
                elif key == "no":
                    btts["no"] = d
            if len(btts) == 2:
                extras["btts"] = btts
        elif desc == "Double Chance":
            dc = {}
            for name, d in priced:
                low = (name or "").lower()
                if low.startswith("draw or"):
                    dc["X2"] = d
                elif " or draw" in low:
                    dc["1X"] = d
                else:
                    dc["12"] = d
            if len(dc) == 3:
                extras["dc"] = dc
        elif desc.startswith("3-Way Handicap ") and desc.endswith(" -1"):
            ah = {}
            for name, d in priced:
                low = (name or "").lower()
                if "draw" in low:
                    ah["X"] = d
                elif "(-1)" in name:
                    ah["1"] = d
                elif "(+1)" in name:
                    ah["2"] = d
            if len(ah) == 3:
                extras["ah_m1"] = ah
        elif desc == "Correct Score":
            cs = {}
            for name, d in priced:
                sc = _parse_cs_name(name)
                if sc:
                    cs[sc] = d
            if cs:
                extras["cs"] = cs
    return extras


def _fetch_league(lid: str) -> dict:
    pinn_id = PINN_LEAGUES[lid]
    matchups = _get(f"{_PINN}/leagues/{pinn_id}/matchups")
    markets = _get(f"{_PINN}/leagues/{pinn_id}/markets/straight")
    if not isinstance(matchups, list):
        matchups = []
    if not isinstance(markets, list):
        markets = []
    ml_by: dict[int, dict] = {}
    ou_by: dict[int, dict] = {}
    for x in markets:
        if x.get("period") != 0:
            continue
        mid = x.get("matchupId")
        if mid is None:
            continue
        if x.get("type") == "moneyline" and len(x.get("prices") or []) == 3:
            ml_by[mid] = x
        if x.get("type") == "total":
            prices = x.get("prices") or []
            if any(pr.get("points") == 2.5 for pr in prices) and mid not in ou_by:
                ou_by[mid] = x
    rows = []
    for m in matchups:
        if m.get("type") != "matchup" or m.get("parentId"):
            continue
        parts = m.get("participants") or []
        home = next((p.get("name") for p in parts if p.get("alignment") == "home"), None)
        away = next((p.get("name") for p in parts if p.get("alignment") == "away"), None)
        if not home or not away:
            continue
        ml = ml_by.get(m.get("id"))
        if not ml:
            continue
        trip: dict[str, float] = {}
        for pr in ml.get("prices") or []:
            des = (pr.get("designation") or "").lower()
            d = _amer_dec(pr.get("price"))
            if des in ("home", "draw", "away") and d:
                trip[des] = d
        if len(trip) < 3:
            continue
        ou: dict[str, float] = {}
        tot = ou_by.get(m.get("id"))
        if tot:
            for pr in tot.get("prices") or []:
                des = (pr.get("designation") or "").lower()
                d = _amer_dec(pr.get("price"))
                if des in ("over", "under") and d:
                    ou[des] = d
        extras = _parse_specials(matchups, markets, m.get("id"))
        rows.append({
            "hk": _team_key(home),
            "ak": _team_key(away),
            "home_name": home,
            "away_name": away,
            "kickoff": m.get("startTime"),
            "home": trip["home"],
            "draw": trip["draw"],
            "away": trip["away"],
            "ou25": ou or None,
            **extras,
        })
    return {"ts": time.time(), "n": len(rows), "rows": rows, "ok": True}


def refresh_league(lid: str) -> dict:
    pack = _load()
    try:
        row = _fetch_league(lid)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as e:
        old = pack.get("leagues", {}).get(lid) or {}
        old = dict(old)
        old["ok"] = False
        old["err"] = str(e)[:160]
        pack.setdefault("leagues", {})[lid] = old
        _save(pack)
        return old
    pack.setdefault("leagues", {})[lid] = row
    _save(pack)
    return row


def refresh_all() -> dict:
    out = {}
    for lid in PINN_LEAGUES:
        out[lid] = refresh_league(lid)
    return out


def ensure(lid: str, max_age: float = TTL) -> dict:
    pack = _load()
    row = pack.get("leagues", {}).get(lid) or {}
    ts = float(row.get("ts") or 0)
    if row.get("rows") is not None and time.time() - ts < max_age:
        return row
    return refresh_league(lid)


def _ko_ts(s: str | None) -> float | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except ValueError:
        return None


def for_match(m: dict) -> dict | None:
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
    want = _ko_ts(m.get("kickoff"))
    best = None
    best_dt = 10**12
    for r in pack.get("rows") or []:
        if r.get("hk") != hk or r.get("ak") != ak:
            continue
        if want is None:
            best = r
            break
        got = _ko_ts(r.get("kickoff"))
        if got is None:
            best = r
            continue
        dt = abs(got - want)
        if dt < best_dt and dt < 20 * 3600:
            best, best_dt = r, dt
    if not best:
        return None
    out = {
        "home": best["home"],
        "draw": best["draw"],
        "away": best["away"],
        "src": "pinnacle",
        "book": "pinnacle",
    }
    if best.get("ou25"):
        out["ou25"] = best["ou25"]
    for k in ("btts", "dc", "ah_m1", "cs"):
        if best.get(k):
            out[k] = best[k]
    return out


def real_book(m: dict) -> tuple[dict, str | None]:
    """Gerçek kota: oynanmış maçta football-data, yaklaşanda Pinnacle. Vekil yok."""
    csv_od = dict(m.get("odds") or {})
    csv_ok = bool(csv_od.get("home") and csv_od.get("draw") and csv_od.get("away"))
    if m.get("played") and csv_ok:
        return csv_od, "fd"
    live = for_match(m)
    if live:
        out = dict(csv_od)
        out["home"] = live["home"]
        out["draw"] = live["draw"]
        out["away"] = live["away"]
        if live.get("ou25"):
            prev = dict(out.get("ou25") or {})
            prev.update(live["ou25"])
            out["ou25"] = prev
        for k in ("btts", "dc", "ah_m1", "cs"):
            if live.get(k):
                out[k] = live[k]
        return out, "pinnacle"
    if csv_ok:
        return csv_od, "fd"
    empty = {
        "home": None,
        "draw": None,
        "away": None,
    }
    for k in ("open", "close", "avg", "max", "ou25"):
        if csv_od.get(k):
            empty[k] = csv_od[k]
    return empty, None
