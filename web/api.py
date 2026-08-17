#!/usr/bin/env python3
"""Dashboard veri katmanı — defter state/history'sini ekranın beklediği şekle çevirir.

Sunum tarafı (dashboard.py) buradan gelen sözlükleri olduğu gibi basar; PM
ağına çıkan tek yer `pm_snapshot()` ve `live_signals()`.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_DIR = os.path.dirname(os.path.abspath(__file__))
_POLY = os.path.join(_DIR, "..", "poly")
sys.path.insert(0, _POLY)

# CoptC/.env — trader'lar kendi başlarına yüklüyor, dashboard süreci de görsün
_ENV = os.path.join(_DIR, "..", ".env")
if os.path.exists(_ENV):
    with open(_ENV, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

_TZ_TR = ZoneInfo("Europe/Istanbul")

BOOKS = {
    "live": {
        "badge": "LIVE",
        "title": "CoptC Live Control",
        "subtitle": "Kaynak defter · BTC · ETH · SOL · Saatlik",
        "live": "live",
        "group": "coptc_live",
        "amount_key": "coptc_live",
        "amount_def": (4.0, 5.0, 6.0),
        "metric": "engine",
        "timeline": [(":02", "Live kapat"), (":05:10–:08", "Kaynak API poll → PM emri")],
    },
}

_SETTINGS = os.path.join(_POLY, "coptc_settings.json")
_SETTINGS_LEGACY = os.path.join(_POLY, "analiz5_settings.json")


# ── dosya yardımcıları ───────────────────────────────────────────
def _path(key: str, kind: str) -> str:
    return os.path.join(_POLY, f"coptc_{key}_{kind}.json")


def _load(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def state(key: str) -> dict:
    return _load(_path(key, "state"), {"balance": 0.0, "open_positions": [], "total_pnl": 0.0})


def history(key: str) -> list:
    h = _load(_path(key, "history"), [])
    return h if isinstance(h, list) else []


# ── ayarlar / live anahtarı ──────────────────────────────────────
_COLD_CUT_KEY = "coptc_live_cold_hour_cut_enabled"


def amounts(book: str) -> dict:
    cfg = BOOKS[book]
    s = _load(_SETTINGS, {}) or _load(_SETTINGS_LEGACY, {})
    k = cfg["amount_key"]
    lo, mid, hi = cfg.get("amount_def", (4.0, 5.0, 6.0))
    legacy = "b1_05"
    cold = s.get(_COLD_CUT_KEY)
    return {
        "low": float(s.get(f"{k}_amount_low", s.get(f"{legacy}_amount_low", lo))),
        "mid": float(s.get(f"{k}_amount_mid", s.get(f"{legacy}_amount_mid", mid))),
        "high": float(s.get(f"{k}_amount_high", s.get(f"{legacy}_amount_high", hi))),
        "cold_hour_cut_enabled": bool(cold) if cold is not None else True,
    }


def save_amounts(
    book: str,
    low: float,
    mid: float,
    high: float,
    *,
    cold_hour_cut_enabled: bool | None = None,
) -> dict:
    k = BOOKS[book]["amount_key"]
    s = _load(_SETTINGS, {})
    s[f"{k}_amount_low"], s[f"{k}_amount_mid"], s[f"{k}_amount_high"] = low, mid, high
    if cold_hour_cut_enabled is not None:
        s[_COLD_CUT_KEY] = bool(cold_hour_cut_enabled)
    tmp = _SETTINGS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
    os.replace(tmp, _SETTINGS)
    return amounts(book)


_ACTIVE_KEY = "coptc_active_book"


def _load_control() -> dict:
    from coptc_guard import get_coptc_control
    return get_coptc_control()


def live_open(book: str) -> bool:
    from coptc_guard import is_group_paused
    return not is_group_paused(BOOKS[book]["group"])


def active_book() -> str:
    c = _load_control()
    ab = c.get(_ACTIVE_KEY, "live")
    if ab == "b1_05":
        ab = "live"
    return ab if ab in BOOKS else "live"


def live_on() -> bool:
    return not bool(_load_control().get("coptc_live_paused", True))


def set_active(book: str, on: bool) -> dict:
    """Tek otorite: coptc_control.json — panel ve cron aynı dosyayı okur."""
    from coptc_guard import patch_control, set_group_paused
    set_group_paused("coptc_live", not bool(on), source="coptc-dashboard")
    patch_control(
        coptc_active_book=book if book in BOOKS else "live",
        updated_by="coptc-dashboard",
    )
    return {"active": active_book(), "live_on": live_on()}


def weekend_info() -> dict:
    from coptc_guard import effective_live_on, weekend_status
    st = weekend_status()
    st["effective_live_on"] = effective_live_on()
    return st


def set_weekend_pause(enabled: bool) -> dict:
    from coptc_guard import set_weekend_pause_enabled
    set_weekend_pause_enabled(bool(enabled), source="coptc-dashboard")
    return weekend_info()


def set_live(book: str, open_: bool) -> bool:
    set_active(book, open_)
    return live_open(book)


# ── mirror kaynağı (bursaapp) ────────────────────────────────────
from coptc_guard import MIRROR_BOOKS_MAX  # noqa: E402

_MIRROR_KEY = "coptc_mirror_book"
_MIRROR_DEF = "a2_05"
_mirror_cache: dict = {"at": 0.0, "rows": []}


def mirror_book_list() -> list[str]:
    """Live işlemin yönünü kopyaladığı kaynak defterler (1–3 adet)."""
    from coptc_guard import mirror_books_selected
    return mirror_books_selected(_load_control())


def mirror_book() -> str:
    """Birincil kaynak — tekil gösterim ve eski çağrılar için."""
    return mirror_book_list()[0]


def set_mirror_book_list(books) -> list[str]:
    from coptc_guard import set_mirror_books
    return set_mirror_books(books, source="coptc-dashboard")


def set_mirror_book(book: str) -> str:
    return set_mirror_book_list([book])[0]


def _short_of(book: str) -> str:
    for b in _mirror_cache.get("rows") or []:
        if b.get("book") == book:
            return str(b.get("short") or book)
    return book


def mirror_label() -> str:
    """Seçili kaynakların kısa adı — birden fazlaysa hepsi artı ile."""
    return " + ".join(_short_of(b) for b in mirror_book_list())


def mirror_meta() -> dict:
    """Birincil kaynağın API satırı — başlık/bakiye için."""
    mb = mirror_book()
    rows = _mirror_cache.get("rows") or []
    for b in rows:
        if b.get("book") == mb:
            return b
    return {"book": mb, "short": mb, "label": mb}


def mirror_books(*, max_age: float = 25.0) -> dict:
    """Kaynaktaki tüm defterler + her birinin şu anki yönü.

    29 defter tek tek sorulduğu için sonuç kısa süre önbelleklenir; panel
    5 sn'de bir yenilendiğinde API'yi dövmesin.
    """
    import time

    now = time.time()
    if _mirror_cache["rows"] and now - _mirror_cache["at"] < max_age:
        return {"books": _mirror_cache["rows"], "selected": mirror_book_list(),
                "cached": True, "error": None}

    sys.path.insert(0, _POLY)
    try:
        import coptc_mirror as ms
        if not ms.enabled():
            return {"books": [], "selected": mirror_book_list(), "cached": False,
                    "error": "MIRROR_API_TOKEN tanımsız"}
        listing = ms.book_list()
    except Exception as e:
        return {"books": _mirror_cache["rows"], "selected": mirror_book_list(),
                "cached": bool(_mirror_cache["rows"]), "error": str(e)}

    def _one(b: dict) -> dict:
        row = {
            "book": b.get("book"),
            "label": b.get("label") or b.get("book"),
            "short": b.get("short") or b.get("book"),
            "open": b.get("open", 0),
            "balance": b.get("balance"),
            "pnl": b.get("pnl") if b.get("pnl") is not None else b.get("total_pnl"),
            "wr": b.get("wr"),
            "trades": b.get("trades"),
            "positions": [],
            "algo": "",
        }
        if not row["open"]:
            return row
        try:
            d = ms.fetch_book(row["book"], timeout=12)
        except Exception:
            return row
        for p in d.get("positions") or []:
            row["positions"].append({
                "symbol": p.get("symbol"),
                "dir": p.get("dir"),
                "entry": p.get("pm_entry_price"),
                "now": p.get("pm_price_now"),
                "current_slot": bool(p.get("is_current_slot", True)),
                "prediction_tr": p.get("prediction_tr"),
                "slot_tr": p.get("slot_tr"),
            })
            if not row["algo"]:
                row["algo"] = (p.get("algo_name") or "").split("—")[0].strip()
        return row

    with ThreadPoolExecutor(max_workers=10) as ex:
        rows = list(ex.map(_one, listing))

    _mirror_cache.update({"at": now, "rows": rows})
    return {"books": rows, "selected": mirror_book_list(), "cached": False, "error": None}


# ── istatistik ───────────────────────────────────────────────────
def _wr(hist: list) -> tuple[int, int, float | None]:
    graded = [t for t in hist if t.get("win") is not None]
    w = sum(1 for t in graded if t.get("win"))
    return w, len(graded), (round(w / len(graded) * 100, 1) if graded else None)


def hour_grid(hist: list) -> list[dict]:
    buckets: dict[int, list] = {h: [] for h in range(24)}
    for t in hist:
        h = t.get("entry_hour_tr")
        if isinstance(h, int) and 0 <= h < 24 and t.get("win") is not None:
            buckets[h].append(bool(t["win"]))
    out = []
    for h in range(24):
        b = buckets[h]
        out.append({
            "h": h, "n": len(b),
            "wr": round(sum(b) / len(b) * 100) if b else None,
        })
    return out


def recent(hist: list, n: int = 25) -> list[dict]:
    rows = []
    for t in reversed(hist[-400:]):
        if t.get("win") is None:
            continue
        ts = str(t.get("exit_time_tr") or t.get("entry_time_tr") or "")
        rows.append({
            "symbol": (t.get("symbol") or "").replace("USDT", ""),
            "pred": t.get("predicted_dir"),
            "actual": t.get("actual_dir"),
            "win": bool(t.get("win")),
            "pnl": round(float(t.get("pnl") or 0), 2),
            "time": ts[5:16].replace("T", " "),
        })
        if len(rows) >= n:
            break
    return rows


# ── PM tarafı ────────────────────────────────────────────────────
import time
import urllib.request

_QUOTE_CACHE: dict[str, tuple[float, float]] = {}   # slug -> (ts, up_price)
_BOOK_CACHE: dict[str, tuple[float, dict]] = {}     # token_id -> (ts, book)
_SPOT_CACHE: dict[str, tuple[float, dict]] = {}     # pairs key -> (ts, prices)
_QUOTE_TTL = 20.0
_BOOK_TTL = 9.0
_SPOT_TTL = 12.0


def _token_price(slug: str, direction: str) -> float | None:
    """Gamma'dan slot kotasyonu; UP tarafının fiyatı, DOWN = 1 − UP."""
    if not slug:
        return None
    hit = _QUOTE_CACHE.get(slug)
    now = time.time()
    if hit and now - hit[0] < _QUOTE_TTL:
        up = hit[1]
    else:
        try:
            req = urllib.request.Request(
                f"https://gamma-api.polymarket.com/markets?slug={slug}",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            if not data:
                return None
            m = data[0] if isinstance(data, list) else data
            prices = m.get("outcomePrices")
            if isinstance(prices, str):
                prices = json.loads(prices)
            if not prices:
                return None
            up = float(prices[0])
            _QUOTE_CACHE[slug] = (now, up)
        except Exception:
            return None
    return up if (direction or "UP").upper() == "UP" else round(1.0 - up, 4)


def _clob_book(token_id: str) -> dict:
    """CLOB order book — anlık satış (bid) fiyatı."""
    if not token_id:
        return {"bid": None, "ask": None, "mid": None}
    hit = _BOOK_CACHE.get(token_id)
    now = time.time()
    if hit and now - hit[0] < _BOOK_TTL:
        return hit[1]
    try:
        url = f"https://clob.polymarket.com/book?token_id={token_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "CoptC Live Control", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            book = json.loads(r.read().decode())
        bids = [float(x["price"]) for x in (book.get("bids") or [])]
        asks = [float(x["price"]) for x in (book.get("asks") or [])]
        bid = max(bids) if bids else None
        ask = min(asks) if asks else None
        mid = round((bid + ask) / 2, 4) if bid and ask else (bid or ask)
        out = {"bid": bid, "ask": ask, "mid": mid}
        _BOOK_CACHE[token_id] = (now, out)
        return out
    except Exception:
        return {"bid": None, "ask": None, "mid": None}


def _spot_prices(pairs: list[str]) -> dict[str, float | None]:
    """Binance futures anlık fiyat."""
    uniq = sorted({p for p in pairs if p})
    if not uniq:
        return {}
    key = ",".join(uniq)
    hit = _SPOT_CACHE.get(key)
    now = time.time()
    if hit and now - hit[0] < _SPOT_TTL:
        return hit[1]
    out: dict[str, float | None] = {}
    for pair in uniq:
        try:
            url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={pair}"
            req = urllib.request.Request(url, headers={"User-Agent": "CoptC Live Control"})
            with urllib.request.urlopen(req, timeout=6) as r:
                out[pair] = float(json.loads(r.read().decode())["price"])
        except Exception:
            out[pair] = None
    _SPOT_CACHE[key] = (now, out)
    return out


def _slot_label(p: dict) -> str:
    h = p.get("entry_hour_tr")
    if h is not None:
        try:
            h = int(h)
            return f"{h:02d}:00–{(h + 1) % 24:02d}:00 İST"
        except (TypeError, ValueError):
            pass
    ts = str(p.get("entry_time_tr") or "")
    return ts[11:16] + " İST" if len(ts) >= 16 else "—"


def _position_row(p: dict, spot_map: dict[str, float | None]) -> dict:
    """Tek açık pozisyon — dashboard kartı için zengin alanlar."""
    pair = p.get("symbol") or ""
    direction = p.get("predicted_dir") or p.get("pm_token_dir") or "UP"
    spent = float(p.get("pm_spent") or p.get("amount") or 0)
    size = float(p.get("pm_size") or p.get("to_win") or 0)
    entry = float(p.get("entry_price") or 0)

    now_spot = spot_map.get(pair)
    spot_diff = spot_pct = None
    winning = None
    if now_spot is not None and entry:
        spot_diff = round(now_spot - entry, 2)
        spot_pct = round((now_spot - entry) / entry * 100, 2)
        winning = (now_spot > entry) if direction == "UP" else (now_spot < entry)

    book = _clob_book(p.get("pm_token_id") or "")
    bid = book.get("bid")
    token_bid = round(float(bid), 3) if bid is not None else None
    # Anlık kapatma yalnızca CLOB bid — gamma fiyatı kaybeden pozisyonda yanıltıcı olur
    close_val = round(size * float(bid), 2) if bid is not None and size else None
    close_pnl = round(close_val - spent, 2) if close_val is not None and spent else None
    no_liquidity = bool(p.get("pm_token_id")) and bid is None
    pnl_pct = round(close_pnl / spent * 100, 1) if close_pnl is not None and spent else None
    win_profit = round(size - spent, 2) if size and spent else None

    return {
        "symbol": pair.replace("USDT", ""),
        "dir": direction,
        "entry": round(entry, 2) if entry else None,
        "spent": round(spent, 2),
        "to_win": round(size, 2) if size else None,
        "close_val": close_val,
        "close_pnl": close_pnl,
        "pnl_pct": pnl_pct,
        "win_profit": win_profit,
        "slot": _slot_label(p),
        "source": _short_of(str(p.get("mirrored_from_source") or "")) if p.get("mirrored_from_source") else "",
        "title": p.get("pm_title") or p.get("pm_slug") or "",
        "spot_now": round(now_spot, 2) if now_spot is not None else None,
        "spot_diff": spot_diff,
        "spot_pct": spot_pct,
        "winning": winning,
        "token_bid": token_bid,
        "no_liquidity": no_liquidity,
        "token_id": p.get("pm_token_id"),
        "source_book": p.get("mirrored_from_source"),
        "entry_hour": p.get("entry_hour_tr"),
        "live": bool(p.get("pm_token_id")),
    }


def pm_snapshot(book: str) -> dict:
    """Nakit + açık pozisyonların anlık durumu. Cüzdan yoksa nakit None."""
    cfg = BOOKS[book]
    live_state = state(cfg["live"])
    opens = [p for p in live_state.get("open_positions") or [] if _is_real_pm(p)]
    pairs = [p.get("symbol") for p in opens if p.get("symbol")]
    spot_map = _spot_prices(pairs)

    cash = None
    if os.getenv("POLY_PRIVATE_KEY"):   # cüzdan yoksa boşuna 3 kez denemesin
        try:
            from pm_trader_helpers import pm_get_balance
            b = pm_get_balance()
            cash = round(float(b), 2) if b is not None and float(b) >= 0 else None
        except Exception:
            pass

    rows, risk, to_win, upnl, close_tot = [], 0.0, 0.0, 0.0, 0.0
    for p in opens:
        row = _position_row(p, spot_map)
        spent = row["spent"]
        risk += spent
        to_win += row["to_win"] or 0.0
        if row["close_val"] is not None:
            close_tot += row["close_val"]
            upnl += row["close_pnl"] or 0.0
        rows.append(row)

    hist = history(cfg["live"])
    w, n, wr = _wr(hist)
    pnl = round(sum(float(t.get("pnl") or 0) for t in hist), 2)
    live_st = state(cfg["live"])
    manual_n = sum(
        1 for t in hist
        if t.get("manual_close") or "manual" in str(t.get("settle_source") or "")
    )
    pending = pm_pending_cash()
    book_pnl = round(float(live_st.get("total_pnl") or 0), 2)
    eq = round((cash or 0) + close_tot, 2) if cash is not None else None
    start_est = round(eq - pnl, 2) if eq is not None else None
    return {
        "cash": cash,
        "redeem_pending": pending.get("value", 0.0),
        "live_pnl": pnl,
        "live_w": w, "live_l": n - w, "live_wr": wr, "live_trades": n,
        "equity": eq,
        "pm_book_pnl": book_pnl,
        "pm_manual_count": manual_n,
        "pm_redeem_winners": pending.get("count", 0),
        "pm_start_balance": start_est,
        "risk": {
            "total": round(risk, 2), "to_win": round(to_win, 2),
            "open": len(rows), "upnl": round(upnl, 2),
            "close_total": round(close_tot, 2),
        },
        "positions": rows,
    }


def _mirror_signals(sources: list[str]) -> list[dict]:
    """Seçili kaynakların açık pozisyonları + anlık fiyat — sembol kartları.

    Birden fazla kaynakta aynı sembol zıt yönde geliyorsa çelişki sayılır;
    o sembolde emir açılmayacağı için kart da yön göstermez.
    """
    if not _mirror_cache.get("rows"):
        mirror_books()
    rows = _mirror_cache.get("rows") or []
    metas = [
        next((b for b in rows if b.get("book") == s), {"book": s, "short": s})
        for s in sources
    ]
    all_shorts = " + ".join(str(m.get("short") or m.get("book")) for m in metas)
    spots = _spot_prices(["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    out = []
    for sym in ("BTC", "ETH", "SOL"):
        hits = []
        for m in metas:
            p = next((x for x in m.get("positions") or []
                      if x.get("symbol") == sym and x.get("dir")), None)
            if p:
                hits.append((str(m.get("short") or m.get("book")), p, m.get("wr")))
        dirs = {h[1].get("dir") for h in hits}
        if not hits:
            direction = None
            foot = "bu slotta kaynakta açık yok"
        elif len(dirs) > 1:
            direction = None
            foot = "çelişki — " + " / ".join(
                f"{s} {'↑' if p.get('dir') == 'UP' else '↓'}" for s, p, _ in hits)
        else:
            direction = hits[0][1].get("dir")
            pred = hits[0][1].get("prediction_tr") or hits[0][1].get("slot_tr") or ""
            foot = f"{direction} · {pred}".strip(" ·")
            if len(hits) > 1:
                foot += f" · {len(hits)} kaynak"
        wrs = [h[2] for h in hits if h[2] is not None]
        out.append({
            "name": sym,
            "price": spots.get(f"{sym}USDT"),
            "dir": direction,
            "metric_label": "KAYNAK",
            "metric_value": " + ".join(h[0] for h in hits) or all_shorts,
            "gauge": (sum(wrs) / len(wrs) / 100.0) if wrs else 0.5,
            "foot": foot,
        })
    return out


def live_signals(book: str) -> list[dict]:
    """Kaynak API'deki o slot tahminleri — yerel algo yok."""
    sys.path.insert(0, _POLY)
    try:
        import coptc_mirror as ms
        selected = mirror_book_list()
        if ms.enabled() and selected:
            return _mirror_signals(selected)
    except Exception:
        pass
    return [{"name": s, "price": None, "dir": None, "metric_label": "KAYNAK",
             "metric_value": "—", "gauge": 0.5, "foot": "MIRROR_API_TOKEN tanımsız veya kaynak seçilmedi"}
            for s in ("BTC", "ETH", "SOL")]


# ── Polymarket'ten para çekme ────────────────────────────────────
_WITHDRAW_LOG = os.path.join(_POLY, "withdraw_log.jsonl")
_MAX_FAILS = 5
_LOCK_SEC = 900.0
_fails = {"n": 0, "until": 0.0}


def _audit(event: str, **fields) -> None:
    """Her çekim denemesi diske yazılır — tutar/adres evet, kod asla."""
    rec = {"ts": datetime.now(_TZ_TR).isoformat(), "event": event, **fields}
    try:
        with open(_WITHDRAW_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _valid_address(a: str) -> bool:
    import re
    return bool(re.fullmatch(r"0x[0-9a-fA-F]{40}", (a or "").strip()))


def withdraw_info() -> dict:
    """Cüzdan durumu — panelde çekim kartının üst satırı."""
    import time

    out = {
        "code_set": bool(os.getenv("COPTC_WITHDRAW_CODE")),
        "locked_for": max(0, int(_fails["until"] - time.time())),
        "funder": "", "eoa": "", "proxy_match": False,
        "balance": None, "builder_ready": False, "error": "",
    }
    try:
        import pm_transfer
        info = pm_transfer.wallet_info()
        bal = info.get("balance_usd")
        out.update({
            "funder": info.get("funder") or "",
            "eoa": info.get("eoa") or "",
            "proxy_match": bool(info.get("proxy_match")),
            "balance": round(float(bal), 2) if bal is not None and float(bal) >= 0 else None,
            "builder_ready": bool(info.get("builder_ready")),
        })
    except Exception as e:
        out["error"] = str(e)[:160]
    return out


def withdraw_send(to: str, amount: float, code: str, token: str = "PUSD") -> tuple[dict, int]:
    """Proxy cüzdandan relayer ile gerçek gönderim. (yanıt, http_kodu) döner."""
    import time

    expected = os.getenv("COPTC_WITHDRAW_CODE", "")
    if not expected:
        return {"error": "Çekim kodu tanımsız — .env dosyasına COPTC_WITHDRAW_CODE ekle."}, 400

    now = time.time()
    if now < _fails["until"]:
        return {"error": f"Çok fazla hatalı kod. {int(_fails['until'] - now)} sn sonra tekrar dene."}, 429

    if not secrets.compare_digest(code or "", expected):
        _fails["n"] += 1
        if _fails["n"] >= _MAX_FAILS:
            _fails["until"] = now + _LOCK_SEC
            _fails["n"] = 0
            _audit("kod_kilidi", to=to, amount=amount)
            return {"error": f"Çok fazla hatalı kod — {int(_LOCK_SEC / 60)} dk kilitlendi."}, 429
        _audit("kod_hatali", to=to, amount=amount, kalan=_MAX_FAILS - _fails["n"])
        return {"error": f"Kod hatalı. Kalan deneme: {_MAX_FAILS - _fails['n']}"}, 403
    _fails["n"] = 0

    to = (to or "").strip()
    if not _valid_address(to):
        return {"error": "Hedef adres geçersiz (0x + 40 karakter olmalı)."}, 400
    try:
        amount = round(float(amount), 2)
    except (TypeError, ValueError):
        return {"error": "Tutar sayı olmalı."}, 400
    if amount <= 0:
        return {"error": "Tutar sıfırdan büyük olmalı."}, 400

    info = withdraw_info()
    if info.get("balance") is None:
        return {"error": "PM bakiyesi okunamadı — cüzdan tanımlı mı? " + (info.get("error") or "")}, 400
    if amount > info["balance"]:
        return {"error": f"Bakiye yetersiz: ${info['balance']:.2f} var, ${amount:.2f} istendi."}, 400
    if not info["proxy_match"]:
        return {"error": "Cüzdan adresi POLY_FUNDER ile uyuşmuyor — gönderim durduruldu."}, 400
    if not info["builder_ready"]:
        return {"error": "Relayer anahtarı eksik (RELAYER_API_KEY + ADDRESS veya POLY_BUILDER trio)."}, 400

    _audit("gonderim_basladi", to=to, amount=amount, token=token)

    # pm_transfer global POLY_DRY_RUN'a bakıyor; o bayrak alım-satım içindi.
    # Çekimin kendi kapısı (kod + onay) geçildiği için yalnız bu çağrı boyunca devre dışı.
    prev = os.environ.get("POLY_DRY_RUN")
    os.environ["POLY_DRY_RUN"] = "false"
    try:
        import pm_transfer
        res = pm_transfer.relay_send_erc20(
            to=to, amount_usd=amount, token=token, confirm=True, wait=True,
        )
    except Exception as e:
        err = str(e)[:300]
        if "401" in err and "invalid authorization" in err.lower():
            err = (
                "Relayer kimlik doğrulaması başarısız (401). "
                "Kişisel hesap için polymarket.com/settings → API Keys → Relayer API Keys "
                "(RELAYER_API_KEY + RELAYER_API_KEY_ADDRESS). "
                "Builder trio yalnızca builder programı içindir."
            )
        elif "batch would revert" in err.lower() or "execution reverted" in err.lower():
            err = (
                "Çekim zincirde reddedildi — cüzdanda seçilen token yok veya bakiye yetersiz. "
                "Polymarket nakit bakiyesi genelde PUSD olarak tutulur; USDC.e seçmeyi dene değil, PUSD kullan."
            )
        _audit("gonderim_hata", to=to, amount=amount, hata=err)
        return {"error": err}, 500
    finally:
        if prev is None:
            os.environ.pop("POLY_DRY_RUN", None)
        else:
            os.environ["POLY_DRY_RUN"] = prev

    _audit("gonderim_bitti", to=to, amount=amount,
           tx=res.get("transaction_hash") or res.get("transaction_id"))
    return res, 200


def withdraw_history(n: int = 10) -> list[dict]:
    if not os.path.exists(_WITHDRAW_LOG):
        return []
    try:
        with open(_WITHDRAW_LOG, encoding="utf-8") as f:
            rows = [json.loads(x) for x in f if x.strip()]
    except Exception:
        return []
    return [r for r in rows if r.get("event") == "gonderim_bitti"][-n:][::-1]


def _is_real_pm(p: dict) -> bool:
    """Gerçek para pozisyonu mu — DRY_RUN kaydı ekrana çıkmasın."""
    return bool(p.get("pm_token_id")) and str(p.get("pm_order_id") or "") != "DRY_RUN"


def _open_token_ids() -> set[str]:
    ids: set[str] = set()
    for cfg in BOOKS.values():
        for p in state(cfg["live"]).get("open_positions") or []:
            if _is_real_pm(p) and p.get("pm_token_id"):
                ids.add(str(p["pm_token_id"]))
    return ids


_CASH_OUT_AT = 0.0


def pm_pending_cash() -> dict:
    from pm_trader_helpers import pm_pending_cash_snapshot
    return pm_pending_cash_snapshot(open_token_ids=_open_token_ids())


def auto_cash_out(*, force: bool = False) -> dict | None:
    """Redeem + kazanan satış — panel yenilenince otomatik."""
    global _CASH_OUT_AT
    if not os.getenv("POLY_PRIVATE_KEY"):
        return None
    try:
        from pm_trader_helpers import pm_cash_out_pending, pm_pending_cash_snapshot
        snap = pm_pending_cash_snapshot(open_token_ids=_open_token_ids())
        if snap.get("count", 0) == 0:
            return snap
        # Bekleyen varsa sık dene; başarılı olunca 15 sn ara ver
        if not force and time.time() - _CASH_OUT_AT < 15:
            return {"pending": snap, "skipped": True}
        result = pm_cash_out_pending(
            label="CoptC-auto",
            open_token_ids=_open_token_ids(),
            wait=True,
        )
        if result.get("sold") or result.get("redeemed"):
            _CASH_OUT_AT = time.time()
        return {**snap, "cash_out": result}
    except Exception as e:
        print(f"[CoptC-auto] cash-out: {e}", file=sys.stderr)
        return {"error": str(e)[:200]}


def cash_out_now() -> dict:
    global _CASH_OUT_AT
    _CASH_OUT_AT = time.time()
    from pm_trader_helpers import pm_cash_out_pending
    snap = pm_pending_cash()
    return {
        **snap,
        "cash_out": pm_cash_out_pending(
            label="CoptC-dashboard",
            open_token_ids=_open_token_ids(),
            wait=True,
        ),
    }


_OPEN_LOCK = os.path.join(_POLY, ".coptc_open.lock")
_MANUAL_CLOSE_ALL_ENABLED = False
_MANUAL_CLOSE_ONE_ENABLED = False


def manual_close_all() -> tuple[dict, int]:
    """Açık live pozisyonların tamamını piyasa fiyatından sat.

    Ayna turu (:05:10–:08) aynı state dosyasına yazıyor — runner'ın kilidini
    alamazsak hiç başlama; iki süreç state'i birbirinin üzerine yazar.
    """
    if not _MANUAL_CLOSE_ALL_ENABLED:
        return {"error": "Tümünü kapat panelden kapalı"}, 403
    import fcntl

    opens = [p for p in state(BOOKS["live"]["live"]).get("open_positions") or [] if _is_real_pm(p)]
    if not opens:
        return {"error": "Açık pozisyon yok"}, 400

    with open(_OPEN_LOCK, "w") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"error": "Açılış turu sürüyor — birkaç saniye sonra tekrar dene"}, 409
        try:
            import coptc_live_core as core
            from coptc_live import SPEC
            res = core.run_manual_close(SPEC)
        except Exception as e:
            print(f"[CoptC-dashboard] manuel kapatma: {e}", file=sys.stderr)
            return {"error": str(e)[:200]}, 500
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    return res, 200


def manual_close_position(
    token_id: str,
    *,
    source: str | None = None,
    hour_tr: int | None = None,
) -> tuple[dict, int]:
    """Tek açık pozisyonu piyasa fiyatından sat."""
    if not _MANUAL_CLOSE_ONE_ENABLED:
        return {"error": "Manuel kapatma panelden kapalı"}, 403
    if not token_id:
        return {"error": "token_id gerekli"}, 400
    import fcntl

    opens = [p for p in state(BOOKS["live"]["live"]).get("open_positions") or [] if _is_real_pm(p)]
    if not opens:
        return {"error": "Açık pozisyon yok"}, 400

    with open(_OPEN_LOCK, "w") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"error": "Açılış turu sürüyor — birkaç saniye sonra tekrar dene"}, 409
        try:
            import coptc_live_core as core
            from coptc_live import SPEC
            res = core.run_manual_close(
                SPEC, token_id=token_id, source=source, hour_tr=hour_tr,
            )
        except Exception as e:
            print(f"[CoptC-dashboard] tek pozisyon kapatma: {e}", file=sys.stderr)
            return {"error": str(e)[:200]}, 500
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    if res.get("closed"):
        return res, 200
    if res.get("failed"):
        return res, 502
    return res, 404


def open_positions_all() -> tuple[list[dict], dict]:
    """Tüm modellerin açık live pozisyonları — seçili model ne olursa olsun görünür."""
    per_book: dict[str, list] = {}
    pairs: list[str] = []
    for b, cfg in BOOKS.items():
        opens = [p for p in state(cfg["live"]).get("open_positions") or [] if _is_real_pm(p)]
        per_book[b] = opens
        pairs += [p.get("symbol") for p in opens if p.get("symbol")]

    spot = _spot_prices(pairs)
    rows, risk, to_win, upnl, close_tot = [], 0.0, 0.0, 0.0, 0.0
    for b, opens in per_book.items():
        for p in opens:
            r = _position_row(p, spot)
            r["book"] = b
            r["badge"] = BOOKS[b]["badge"]
            risk += r["spent"]
            to_win += r["to_win"] or 0.0
            if r["close_val"] is not None:
                close_tot += r["close_val"]
                upnl += r["close_pnl"] or 0.0
            rows.append(r)

    rows.sort(key=lambda r: (r["book"], r["symbol"], r.get("source") or ""))
    return rows, {
        "total": round(risk, 2), "to_win": round(to_win, 2),
        "open": len(rows), "upnl": round(upnl, 2),
        "close_total": round(close_tot, 2),
    }


def overview(book: str) -> dict:
    """Yalnız gerçek PM (live) verisi — sanal defter ekrana hiç çıkmaz."""
    cfg = BOOKS[book]
    if not _mirror_cache.get("rows"):
        try:
            mirror_books()
        except Exception:
            pass
    src = mirror_meta()
    auto_cash_out(force=True)
    pm = pm_snapshot(book)
    lhist = history(cfg["live"])
    _, ln, _ = _wr(lhist)
    all_rows, all_risk = open_positions_all()
    pm["pm_redeem_winners"] = pm_pending_cash().get("count", 0)

    sub: list[str] = []
    if src.get("balance") is not None:
        sub.append(f"Bakiye ${float(src['balance']):.2f}")
    if src.get("wr") is not None:
        sub.append(f"WR %{src['wr']}")
    if src.get("trades"):
        sub.append(f"{src['trades']} işlem")
    if src.get("open"):
        sub.append(f"{src['open']} açık")
    src_sub = " · ".join(sub) if sub else "API kaynağı · saatlik"
    selected = mirror_book_list()
    if len(selected) > 1:
        # Bakiye/WR birincil deftere ait; başlıkta hepsi görünsün ki
        # rakamların tek kaynağa ait olduğu karışmasın.
        src_sub = f"{len(selected)} kaynak birlikte · birincil: {src_sub}"
    src_name = mirror_label() if len(selected) > 1 else (src.get("short") or mirror_label())

    wk = weekend_info()
    return {
        "book": book,
        "badge": src.get("short") or mirror_label(),
        "title": src_name,
        "subtitle": src_sub,
        "timeline": [(":02", "Live kapat"), (":05:10–:08", "Kaynak aynası poll → PM emri")],
        "live_open": live_open(book),
        "active": active_book(),
        "live_on": live_on(),
        "weekend": wk,
        "effective_live_on": wk["effective_live_on"],
        "mirror_book": mirror_book(),
        "mirror_books": mirror_book_list(),
        "mirror_short": mirror_label(),
        "mirror_balance": src.get("balance"),
        "mirror_pnl": src.get("pnl"),
        "models": [
            {"key": k, "badge": c["badge"], "title": c["title"]}
            for k, c in BOOKS.items()
        ],
        "now": datetime.now(_TZ_TR).strftime("%H:%M:%S"),
        "amounts": {**amounts(book), "wr": pm["live_wr"], "trades": ln, "open": pm["risk"]["open"]},
        "hours": hour_grid(lhist),
        "history": recent(lhist),
        **pm,
        # Açık gerçek para pozisyonları model seçiminden bağımsız gösterilir
        "positions": all_rows,
        "risk": all_risk,
        "redeem_pending": pm.get("redeem_pending", 0.0),
    }


# ── mobil uygulama sözleşmesi ────────────────────────────────────

def _money_tr(v) -> str:
    if v is None:
        return "—"
    n = float(v)
    sign = "-" if n < 0 else ""
    whole, frac = f"{abs(n):.2f}".split(".")
    groups: list[str] = []
    while whole:
        groups.append(whole[-3:])
        whole = whole[:-3]
    return f"{sign}${'.'.join(reversed(groups))},{frac}"


def mobile_live(book: str | None = None) -> dict:
    book = book or active_book()
    on = live_on()
    return {
        "on": on,
        "book": book,
        "label": "Live açık" if on else "Live kapalı",
    }


def mobile_home() -> dict:
    """iOS ana ekran: live + cüzdan + açık pozisyonlar + son işlemler."""
    book = active_book()
    o = overview(book)
    cash = o.get("cash")
    equity = o.get("equity")
    on = bool(o.get("live_on"))
    src = o.get("mirror_short") or o.get("mirror_book") or "—"
    footer = f"{src} aynası · PM emri açık" if on else "Live kapalı"
    if equity is not None:
        subtitle = f"Anlık toplam {_money_tr(equity)} · serbest USDC"
    elif cash is None:
        subtitle = "cüzdan tanımsız"
    else:
        subtitle = "Serbest USDC"
    ring = None
    if cash is not None:
        ring = round(min(1.0, max(0.0, float(cash) / 1000.0)), 3)
    positions = []
    for p in o.get("positions") or []:
        positions.append({
            "id": p.get("token_id") or f"{p.get('symbol')}-{p.get('slot')}",
            "symbol": p.get("symbol"),
            "dir": p.get("dir"),
            "dir_label": "YÜKSELİR" if p.get("dir") == "UP" else "DÜŞER",
            "badge": p.get("badge") or "",
            "source": p.get("source") or "",
            "slot": p.get("slot") or "",
            "entry": p.get("entry"),
            "spot_now": p.get("spot_now"),
            "spot_diff": p.get("spot_diff"),
            "close_pnl": p.get("close_pnl"),
            "pnl_pct": p.get("pnl_pct"),
            "close_val": p.get("close_val"),
            "spent": p.get("spent"),
            "to_win": p.get("to_win"),
            "token_bid": p.get("token_bid"),
            "winning": p.get("winning"),
            "no_liquidity": bool(p.get("no_liquidity")),
        })
    return {
        "live": mobile_live(book),
        "wallet": {
            "label": "POLYMARKET",
            "cash": cash,
            "equity": equity,
            "cash_text": _money_tr(cash),
            "subtitle": subtitle,
            "footer": footer,
            "warn": cash is not None and float(cash) <= 1000,
            "ring_pct": ring,
            "ring_text": f"{int(round(ring * 100))}%" if ring is not None else "—",
        },
        "positions": positions,
        "history": [
            {
                "symbol": t.get("symbol"),
                "pred": t.get("pred"),
                "actual": t.get("actual"),
                "win": bool(t.get("win")),
                "pnl": t.get("pnl"),
                "time": t.get("time"),
            }
            for t in (o.get("history") or [])
        ],
    }


def mobile_settings() -> dict:
    """iOS ayarlar: giriş tutarlarını manuel girme."""
    book = active_book()
    a = amounts(book)
    return {
        "book": book,
        "amounts": {
            "low": a["low"],
            "mid": a["mid"],
            "high": a["high"],
        },
        "min": 1.0,
        "max": 500.0,
        "labels": {
            "low": "Low (WR < 50%)",
            "mid": "Mid",
            "high": "High",
        },
    }


def mobile_save_amounts(low: float, mid: float, high: float) -> dict:
    save_amounts(active_book(), low, mid, high)
    return mobile_settings()


def mobile_set_live(on: bool) -> dict:
    set_active(active_book(), on)
    return {"live": mobile_live()}
