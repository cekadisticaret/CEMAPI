"""ALG klasöründeki indikatörleri sanal Binance USDT-M futures'ta çalıştırır.

Her algoritma: $1000 sanal bakiye, işlem $100 × 10x, en fazla 6 açık pozisyon.
Gerçek emir yok — dolum/komisyon/funding/likidasyon Binance kuralları gibi.
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import math
import os
import re
import threading
import time
import traceback
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo

from atr_sistem import (
    ATRP_NO_TRADE,
    ATR_SL_MULT,
    ATR_TRAIL_MULT,
    atr_last,
    atrp as _atrp,
    levels as _atr_levels,
    sl_clears_liq,
    trail_stop,
)

_TZ = ZoneInfo("Europe/Istanbul")
_DIR = os.path.dirname(os.path.abspath(__file__))
_ALG = os.path.join(_DIR, "..", "ALG")
_STATE = os.path.join(_DIR, "algo_paper_state.json")
_BN = "https://fapi.binance.com"
_HDR = {"User-Agent": "CEMAPI-ALG"}

START_CASH = 1000.0
MARGIN = 100.0
LEV = 10
MAX_POS = 6
NOTIONAL = MARGIN * LEV
FEE_RATE = 0.0005
MMR = 0.004
FUND_MS = 8 * 3600 * 1000
TP_PCT = 0.020
SL_PCT = 0.015
INTERVAL = "15m"
KLINE_N = 90
SCAN_SEC = 60

_SKIP_FILES = {"hmm_regime_detector (1).py"}
_SKIP_CLASSES = {"GridLevel", "ArbitrageOpportunity", "ChandelierLevels"}
_NO_AUTO = {
    "mvrv_zscore", "sopr_indicator", "funding_arbitrage",
    "oi_liquidation_analyzer", "oi_divergence", "pairs_trading",
    "multi_timeframe", "fear_greed_index", "lstm_predictor",
    "random_forest_predictor", "grid_bot", "hmm_regime_detector",
}
_FALLBACK_COINS = (
    "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT",
    "LINKUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "NEARUSDT",
    "APTUSDT", "INJUSDT", "ARBUSDT", "OPUSDT", "SUIUSDT",
    "FILUSDT", "TIAUSDT", "SEIUSDT", "RENDERUSDT", "FETUSDT",
    "WIFUSDT", "1000PEPEUSDT", "TAOUSDT", "KAVAUSDT",
    "UNIUSDT", "AAVEUSDT", "LDOUSDT", "ENAUSDT",
)

_lock = threading.RLock()
_state: dict | None = None
_thread: threading.Thread | None = None
_kline_cache: dict[str, tuple[float, object]] = {}
_px_cache: tuple[float, dict[str, dict]] = (0.0, {})
_book_cache: dict = {"t": 0.0, "rows": {}}
_filt_cache: dict = {"t": 0.0, "rows": {}}
_mods: dict[str, object] = {}


def _now() -> datetime:
    return datetime.now(_TZ)


def _ts() -> str:
    return _now().strftime("%m-%d %H:%M")


def _iso() -> str:
    return _now().isoformat(timespec="seconds")


def _http(url: str, timeout: int = 12):
    req = urllib.request.Request(url, headers=_HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _title_from_doc(text: str, fallback: str) -> str:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    for ln in lines:
        if ln.endswith(".py"):
            continue
        ln = re.sub(r"^[A-Za-z0-9_\.]+\s*:\s*", "", ln)
        return ln[:72]
    return fallback.replace("_", " ").title()


def _discover() -> list[dict]:
    rows = []
    files = sorted(
        f for f in os.listdir(_ALG)
        if f.endswith(".py") and not f.startswith("_") and f not in _SKIP_FILES
    )
    n = 0
    for fn in files:
        path = os.path.join(_ALG, fn)
        slug = fn[:-3]
        doc = ""
        cls_name = ""
        try:
            with open(path, encoding="utf-8") as f:
                src = f.read(2500)
            m = re.search(r'"""(.*?)"""', src, re.S)
            doc = m.group(1) if m else ""
            for cm in re.finditer(r"^class\s+(\w+)", src, re.M):
                if cm.group(1) not in _SKIP_CLASSES:
                    cls_name = cm.group(1)
                    break
        except OSError:
            continue
        if not cls_name:
            continue
        n += 1
        rows.append({
            "id": slug,
            "code": f"A1#{n:02d}",
            "file": fn,
            "class_name": cls_name,
            "title": _title_from_doc(doc, slug),
            "auto": slug not in _NO_AUTO,
        })
    return rows


def _blank_book(meta: dict) -> dict:
    return {
        "id": meta["id"],
        "code": meta["code"],
        "file": meta["file"],
        "class_name": meta["class_name"],
        "title": meta["title"],
        "auto": meta["auto"],
        "active": True,
        "cash": START_CASH,
        "fees": 0.0,
        "positions": [],
        "history": [],
        "error": "",
        "last_signal": "",
    }


def _load() -> dict:
    global _state
    if _state is not None:
        return _state
    catalog = {m["id"]: m for m in _discover()}
    raw: dict = {}
    if os.path.isfile(_STATE):
        try:
            with open(_STATE, encoding="utf-8") as f:
                raw = json.load(f) or {}
        except Exception:
            raw = {}
    books = raw.get("algos") or {}
    merged = {}
    for mid, meta in catalog.items():
        old = books.get(mid) or {}
        b = _blank_book(meta)
        b["active"] = bool(old.get("active", True))
        b["cash"] = float(old.get("cash", START_CASH))
        b["fees"] = float(old.get("fees", 0))
        b["positions"] = list(old.get("positions") or [])
        b["history"] = list(old.get("history") or [])[-400:]
        b["error"] = str(old.get("error") or "")
        b["last_signal"] = str(old.get("last_signal") or "")
        merged[mid] = b
    _state = {
        "algos": merged,
        "pending": list(raw.get("pending") or []),
        "last_scan": raw.get("last_scan") or "",
    }
    return _state


def _save() -> None:
    if _state is None:
        return
    tmp = _STATE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_state, f, ensure_ascii=False)
        os.replace(tmp, _STATE)
    except OSError:
        pass


def _filters() -> dict[str, dict]:
    now = time.time()
    if _filt_cache["rows"] and now - _filt_cache["t"] < 3600:
        return _filt_cache["rows"]
    try:
        info = _http(f"{_BN}/fapi/v1/exchangeInfo", timeout=20)
    except Exception:
        return _filt_cache["rows"]
    out: dict[str, dict] = {}
    for s in info.get("symbols") or []:
        if s.get("contractType") != "PERPETUAL" or s.get("quoteAsset") != "USDT":
            continue
        sym = str(s.get("symbol") or "")
        tick, step, min_n = 0.0001, 0.001, 5.0
        for f in s.get("filters") or []:
            kind = f.get("filterType")
            if kind == "PRICE_FILTER":
                tick = float(f.get("tickSize") or tick)
            elif kind == "LOT_SIZE":
                step = float(f.get("stepSize") or step)
            elif kind in ("MIN_NOTIONAL", "NOTIONAL"):
                min_n = float(f.get("notional") or f.get("minNotional") or min_n)
        out[sym] = {"tick": tick, "step": step, "min_notional": min_n}
    if out:
        _filt_cache["t"] = now
        _filt_cache["rows"] = out
    return out


def _round_tick(px: float, tick: float) -> float:
    if px <= 0 or not tick:
        return px
    dec = max(0, -int(math.floor(math.log10(tick))))
    return round(round(px / tick) * tick, dec)


def _round_step(qty: float, step: float) -> float:
    if qty <= 0 or not step:
        return qty
    dec = max(0, -int(math.floor(math.log10(step))))
    return round(math.floor(qty / step + 1e-12) * step, dec)


def _book() -> dict[str, dict]:
    now = time.time()
    if _book_cache["rows"] and now - _book_cache["t"] < 5:
        return _book_cache["rows"]
    out: dict[str, dict] = {}
    try:
        books = _http(f"{_BN}/fapi/v1/ticker/bookTicker", timeout=15)
        prem = _http(f"{_BN}/fapi/v1/premiumIndex", timeout=15)
    except Exception:
        return _book_cache["rows"]
    for r in books or []:
        sym = str(r.get("symbol") or "")
        try:
            out[sym] = {
                "bid": float(r.get("bidPrice") or 0),
                "ask": float(r.get("askPrice") or 0),
            }
        except (TypeError, ValueError):
            continue
    for r in prem or []:
        sym = str(r.get("symbol") or "")
        row = out.setdefault(sym, {})
        try:
            row["mark"] = float(r.get("markPrice") or 0)
            row["funding"] = float(r.get("lastFundingRate") or 0)
            row["next_fund"] = int(r.get("nextFundingTime") or 0)
        except (TypeError, ValueError):
            pass
    if out:
        _book_cache["t"] = now
        _book_cache["rows"] = out
    return out


def _fill_px(side: str, action: str, info: dict) -> float:
    if action == "open":
        px = info.get("ask") if side == "LONG" else info.get("bid")
    else:
        px = info.get("bid") if side == "LONG" else info.get("ask")
    return float(px or info.get("mark") or info.get("price") or 0)


def _fee_on(qty: float, px: float) -> float:
    return round(max(0.0, qty) * max(0.0, px) * FEE_RATE, 4)


def _liq_price(side: str, entry: float) -> float:
    if side == "LONG":
        return entry * (1.0 - 1.0 / LEV + MMR)
    return entry * (1.0 + 1.0 / LEV - MMR)


def _ga_coins() -> list[dict]:
    """Grafik Analiz ile aynı evren: /api/desk/futures."""
    try:
        import desk_trade
        rows = desk_trade.futures_symbols()
        if rows:
            return rows
    except Exception:
        pass
    return [
        {"symbol": s, "base": s.replace("USDT", ""), "price": 0.0, "chg": 0.0, "qv": 0.0}
        for s in _FALLBACK_COINS
    ]


def _marks() -> dict[str, dict]:
    global _px_cache
    now = time.time()
    if _px_cache[1] and now - _px_cache[0] < 8:
        return _px_cache[1]
    out: dict[str, dict] = {}
    book = _book()
    for r in _ga_coins():
        sym = str(r.get("symbol") or "")
        if not sym:
            continue
        b = book.get(sym) or {}
        try:
            last = float(r.get("price") or 0)
            mark = float(b.get("mark") or last)
            bid = float(b.get("bid") or last)
            ask = float(b.get("ask") or last)
            out[sym] = {
                "price": last,
                "mark": mark,
                "bid": bid,
                "ask": ask,
                "chg": float(r.get("chg") or 0),
                "qv": float(r.get("qv") or 0),
                "funding": float(b.get("funding") or 0),
                "next_fund": int(b.get("next_fund") or 0),
            }
        except (TypeError, ValueError):
            continue
    if out:
        _px_cache = (now, out)
    return out or _px_cache[1]


def _coin_universe(_marks: dict[str, dict] | None = None) -> list[str]:
    return [str(r["symbol"]) for r in _ga_coins() if r.get("symbol")]


def _klines(symbol: str):
    now = time.time()
    hit = _kline_cache.get(symbol)
    if hit and now - hit[0] < 90:
        return hit[1]
    try:
        rows = _http(
            f"{_BN}/fapi/v1/klines?symbol={symbol}&interval={INTERVAL}&limit={KLINE_N}",
            timeout=10,
        )
    except Exception:
        return hit[1] if hit else None
    import pandas as pd
    df = pd.DataFrame(rows, columns=list(range(12)))
    out = pd.DataFrame({
        "open": df[1].astype(float),
        "high": df[2].astype(float),
        "low": df[3].astype(float),
        "close": df[4].astype(float),
        "volume": df[5].astype(float),
    })
    _kline_cache[symbol] = (now, out)
    return out


def _load_instance(meta: dict):
    slug = meta["id"]
    if slug in _mods:
        return _mods[slug]
    path = os.path.join(_ALG, meta["file"])
    spec = importlib.util.spec_from_file_location(f"alg_{slug}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("modül yüklenemedi")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = getattr(mod, meta["class_name"])
    inst = cls()
    _mods[slug] = inst
    return inst


def _call_run(inst, df) -> dict:
    import pandas as pd
    fn = inst.run
    names = [p for p in inspect.signature(fn).parameters if p != "self"]
    close = df["close"]
    high = df["high"]
    low = df["low"]
    vol = df["volume"]
    opn = df["open"]
    kw = {}
    for n in names:
        if n in ("prices", "close", "series1"):
            kw[n] = close
        elif n == "high":
            kw[n] = high
        elif n == "low":
            kw[n] = low
        elif n in ("volume", "volumes"):
            kw[n] = vol
        elif n in ("open_p", "open"):
            kw[n] = opn
        elif n == "current_price":
            kw[n] = float(close.iloc[-1])
        elif n == "timestamps":
            kw[n] = pd.RangeIndex(len(df))
        elif n == "series2":
            return {"signal": "SKIP"}
        elif n in ("asset", "sopr_type", "symbol", "oi", "signals", "df"):
            return {"signal": "SKIP"}
    return fn(**kw) if kw or not names else fn()


def _side_of(sig: str) -> str | None:
    s = (sig or "").upper()
    if s in ("BUY", "LONG", "BULLISH"):
        return "LONG"
    if s in ("SELL", "SHORT", "BEARISH"):
        return "SHORT"
    return None


def _pnl(side: str, entry: float, px: float, qty: float) -> float:
    if entry <= 0 or qty <= 0:
        return 0.0
    if side == "SHORT":
        return (entry - px) * qty
    return (px - entry) * qty


def _fee(notional: float = NOTIONAL) -> float:
    return round(notional * FEE_RATE, 4)


def _qty_of(p: dict) -> float:
    q = float(p.get("qty") or 0)
    if q > 0:
        return q
    entry = float(p.get("entry") or 0)
    return (NOTIONAL / entry) if entry else 0.0


def _exit_px(p: dict, info: dict, reason: str = "") -> float:
    filt = _filters().get(p["symbol"]) or {}
    if reason == "liquidation":
        px = float(p.get("liq") or _liq_price(p["side"], float(p["entry"])))
    else:
        px = _fill_px(p["side"], "close", info)
    return _round_tick(px, float(filt.get("tick") or 0))


def _mark_pos(p: dict, marks: dict[str, dict]) -> dict:
    info = marks.get(p["symbol"]) or {}
    mark = float(info.get("mark") or info.get("price") or p.get("mark") or p["entry"])
    chg = float(info.get("chg") or 0)
    qty = _qty_of(p)
    exit_est = _exit_px(p, info)
    gross = _pnl(p["side"], float(p["entry"]), mark, qty)
    fee_open = float(p.get("fee_open") or 0)
    fee_close = _fee_on(qty, exit_est or mark)
    fund = float(p.get("funding_acc") or 0)
    net = gross - fee_open - fee_close + fund
    pct = (net / MARGIN) * 100 if MARGIN else 0
    out = dict(p)
    out.update({
        "mark": mark,
        "bid": float(info.get("bid") or 0),
        "ask": float(info.get("ask") or 0),
        "chg": chg,
        "qty": qty,
        "gross": round(gross, 2),
        "fee_close": fee_close,
        "commission": round(fee_open + fee_close, 2),
        "funding": round(fund, 4),
        "funding_rate": float(info.get("funding") or 0),
        "net": round(net, 2),
        "pct": round(pct, 2),
        "liq": float(p.get("liq") or _liq_price(p["side"], float(p["entry"]))),
        "mins": _hold_mins(p),
        "tp_usd": round(_pnl(p["side"], float(p["entry"]), float(p["tp"]), qty), 2),
        "sl_usd": round(_pnl(p["side"], float(p["entry"]), float(p["sl"]), qty), 2),
        "atr": round(float(p.get("atr") or 0), 8),
        "atrp": round(float(p.get("atrp") or 0), 2),
        "trail_on": bool(p.get("trail_on")),
        "tp1_done": bool(p.get("tp1_done")),
    })
    return out


def _book_view(b: dict, marks: dict[str, dict]) -> dict:
    poss = [_mark_pos(p, marks) for p in b.get("positions") or []]
    unreal = sum(p["net"] for p in poss)
    locked = MARGIN * len(poss)
    equity = round(float(b["cash"]) + locked + unreal, 2)
    hist = []
    for h in b.get("history") or []:
        row = dict(h)
        if row.get("mins") is None:
            row["mins"] = _hold_mins(row, str(row.get("closed_iso") or row.get("iso") or ""))
        if not row.get("closed"):
            row["closed"] = row.get("t") or ""
        hist.append(row)
    wins = sum(1 for h in hist if float(h.get("net") or 0) > 0)
    realized = sum(float(h.get("net") or 0) for h in hist)
    return {
        "id": b["id"],
        "code": b["code"],
        "title": b["title"],
        "auto": b["auto"],
        "active": b["active"],
        "error": b.get("error") or "",
        "cash_free": round(float(b["cash"]), 2),
        "equity": equity,
        "net_pnl": round(equity - START_CASH, 2),
        "unreal": round(unreal, 2),
        "fees": round(float(b.get("fees") or 0), 2),
        "open_n": len(poss),
        "wins": wins,
        "trades": len(hist),
        "win_pct": round(100.0 * wins / len(hist), 1) if hist else 0.0,
        "positions": poss,
        "history": hist[-80:][::-1],
        "last_signal": b.get("last_signal") or "",
        "realized": round(realized, 2),
    }


def overview() -> dict:
    with _lock:
        st = _load()
        marks = _marks()
        cards = [_book_view(b, marks) for b in st["algos"].values()]
        cards.sort(key=lambda x: (-float(x.get("equity") or 0), x["code"]))
        net = sum(c["net_pnl"] for c in cards)
        fees = sum(c["fees"] for c in cards)
        opens = sum(c["open_n"] for c in cards)
        names = " + ".join(c["code"] for c in cards[:6])
        if len(cards) > 6:
            names += " + …"
        return {
            "ok": True,
            "subtitle": (
                f"{names} → sanal Binance — ${START_CASH:.0f} — "
                f"${MARGIN:.0f}×{LEV}x — max:{MAX_POS} — "
                f"{len(cards)} defter — {len(_coin_universe())} coin (Grafik Analiz) — "
                f"VIP0 taker %0.05 · ATR SL {ATR_SL_MULT}× / trail {ATR_TRAIL_MULT}× · "
                f"ATRP>%{ATRP_NO_TRADE:.0f} yok — {INTERVAL} — 7/24"
            ),
            "coin_n": len(_coin_universe()),
            "net_pnl": round(net, 2),
            "fees": round(fees, 2),
            "open_n": opens,
            "algos": cards,
            "pending": st.get("pending") or [],
            "last_scan": st.get("last_scan") or "",
        }


def detail(aid: str) -> dict | None:
    with _lock:
        st = _load()
        b = st["algos"].get(aid)
        if not b:
            return None
        return _book_view(b, _marks())


def toggle(aid: str) -> dict | None:
    with _lock:
        st = _load()
        b = st["algos"].get(aid)
        if not b:
            return None
        b["active"] = not b["active"]
        _save()
        return _book_view(b, _marks())


def _close_one(b: dict, pos_id: str, marks: dict, reason: str) -> dict | None:
    poss = b.get("positions") or []
    hit = next((p for p in poss if p["id"] == pos_id), None)
    if not hit:
        return None
    info = marks.get(hit["symbol"]) or {}
    qty = _qty_of(hit)
    exit_px = _exit_px(hit, info, reason)
    if exit_px <= 0:
        exit_px = float(info.get("mark") or hit.get("entry") or 0)
    gross = _pnl(hit["side"], float(hit["entry"]), exit_px, qty)
    fee_open = float(hit.get("fee_open") or 0)
    fee_close = _fee_on(qty, exit_px)
    fund = float(hit.get("funding_acc") or 0)
    net = gross - fee_open - fee_close + fund
    if reason == "liquidation":
        net = min(net, -(MARGIN - 1.0))
    b["positions"] = [p for p in poss if p["id"] != pos_id]
    b["cash"] = round(float(b["cash"]) + MARGIN + net, 2)
    b["fees"] = round(float(b.get("fees") or 0) + fee_open + fee_close, 2)
    closed = _ts()
    closed_iso = _iso()
    opened = str(hit.get("opened") or "")
    opened_iso = str(hit.get("opened_iso") or "")
    mins = _hold_mins(hit, closed_iso)
    rec = {
        "id": hit["id"],
        "t": closed,
        "iso": closed_iso,
        "symbol": hit["symbol"],
        "base": hit["base"],
        "side": hit["side"],
        "entry": hit["entry"],
        "exit": exit_px,
        "reason": reason,
        "gross": round(gross, 2),
        "commission": round(fee_open + fee_close, 2),
        "funding": round(fund, 4),
        "net": round(net, 2),
        "opened": opened,
        "opened_iso": opened_iso,
        "closed": closed,
        "closed_iso": closed_iso,
        "mins": mins,
    }
    hist = b.setdefault("history", [])
    hist.append(rec)
    if len(hist) > 400:
        del hist[:-400]
    return rec


def close_pos(aid: str, pos_id: str, reason: str = "manuel") -> tuple[dict, int]:
    with _lock:
        st = _load()
        b = st["algos"].get(aid)
        if not b:
            return {"error": "algoritma yok"}, 404
        rec = _close_one(b, pos_id, _marks(), reason)
        if not rec:
            return {"error": "pozisyon yok"}, 404
        _save()
        return {"ok": True, "closed": rec, "book": _book_view(b, _marks())}, 200


def _open_pos(b: dict, symbol: str, side: str, marks: dict, df=None) -> dict | None:
    if not b.get("active") or not b.get("auto"):
        return None
    if len(b.get("positions") or []) >= MAX_POS:
        return None
    if any(p["symbol"] == symbol for p in b.get("positions") or []):
        return None
    info = marks.get(symbol) or {}
    filt = _filters().get(symbol) or {"tick": 0.0001, "step": 0.001, "min_notional": 5.0}
    tick = float(filt.get("tick") or 0.0001)
    step = float(filt.get("step") or 0.001)
    px = _round_tick(_fill_px(side, "open", info), tick)
    if px <= 0:
        return None
    atr = atr_last(df)
    if atr <= 0:
        return None
    ap = _atrp(atr, px)
    if ap >= ATRP_NO_TRADE:
        return None
    lv = _atr_levels(side, px, atr)
    sl = _round_tick(lv["sl"], tick)
    tp1 = _round_tick(lv["tp1"], tick)
    tp2 = _round_tick(lv["tp2"], tick)
    liq = _round_tick(_liq_price(side, px), tick)
    if not sl_clears_liq(side, px, sl, liq):
        return None
    qty = _round_step(NOTIONAL / px, step)
    if qty <= 0 or qty * px < float(filt.get("min_notional") or 5):
        return None
    fee = _fee_on(qty, px)
    if float(b["cash"]) < MARGIN + fee:
        return None
    now_ms = int(time.time() * 1000)
    pos = {
        "id": uuid.uuid4().hex[:12],
        "symbol": symbol,
        "base": symbol.replace("USDT", ""),
        "side": side,
        "entry": px,
        "mark": float(info.get("mark") or px),
        "qty": qty,
        "qty_orig": qty,
        "margin": MARGIN,
        "lev": LEV,
        "atr": atr,
        "atrp": round(ap, 2),
        "r_dist": lv["r_dist"],
        "sl": sl,
        "tp1": tp1,
        "tp": tp2,
        "tp2": tp2,
        "liq": liq,
        "peak": px,
        "trough": px,
        "trail_on": False,
        "tp1_done": False,
        "fee_open": fee,
        "funding_acc": 0.0,
        "last_funding_ms": 0,
        "opened": _ts(),
        "opened_iso": _iso(),
        "opened_ms": now_ms,
        "fill": "ask" if side == "LONG" else "bid",
    }
    b["cash"] = round(float(b["cash"]) - MARGIN - fee, 2)
    b["fees"] = round(float(b.get("fees") or 0) + fee, 2)
    b.setdefault("positions", []).append(pos)
    return pos


def _refresh_trail(p: dict, mark: float, df=None) -> None:
    atr = atr_last(df) if df is not None else 0.0
    if atr <= 0:
        atr = float(p.get("atr") or 0)
    if atr <= 0:
        return
    p["atr"] = atr
    entry = float(p["entry"])
    r = float(p.get("r_dist") or atr * ATR_SL_MULT)
    if p["side"] == "LONG":
        peak = max(float(p.get("peak") or entry), mark)
        p["peak"] = peak
        if peak - entry >= r:
            p["trail_on"] = True
        if p.get("trail_on"):
            trail = trail_stop("LONG", peak, atr)
            p["sl"] = max(float(p["sl"]), trail)
    else:
        trough = min(float(p.get("trough") or entry), mark)
        p["trough"] = trough
        if entry - trough >= r:
            p["trail_on"] = True
        if p.get("trail_on"):
            trail = trail_stop("SHORT", trough, atr)
            p["sl"] = min(float(p["sl"]), trail)


def _hit_exit(p: dict, mark: float) -> str | None:
    if mark <= 0:
        return None
    entry = float(p["entry"])
    liq = float(p.get("liq") or _liq_price(p["side"], entry))
    sl = float(p.get("sl") or 0)
    tp2 = float(p.get("tp") or p.get("tp2") or 0)
    tp1 = float(p.get("tp1") or 0)
    if p["side"] == "LONG":
        if mark <= liq:
            return "liquidation"
        if sl and mark <= sl:
            return "trailing_stop" if p.get("trail_on") else "stop_loss"
        if not p.get("tp1_done") and tp1 and mark >= tp1:
            return "take_profit_1"
        if tp2 and mark >= tp2:
            return "take_profit"
    else:
        if mark >= liq:
            return "liquidation"
        if sl and mark >= sl:
            return "trailing_stop" if p.get("trail_on") else "stop_loss"
        if not p.get("tp1_done") and tp1 and mark <= tp1:
            return "take_profit_1"
        if tp2 and mark <= tp2:
            return "take_profit"
    return None


def _close_partial(b: dict, pos: dict, marks: dict, frac: float, reason: str) -> dict | None:
    qty = _qty_of(pos)
    if qty <= 0 or frac <= 0 or frac >= 1 or pos.get("tp1_done"):
        return None
    close_qty = qty * frac
    remain = qty - close_qty
    info = marks.get(pos["symbol"]) or {}
    exit_px = _exit_px(pos, info, reason)
    if exit_px <= 0:
        exit_px = float(info.get("mark") or pos.get("entry") or 0)
    gross = _pnl(pos["side"], float(pos["entry"]), exit_px, close_qty)
    fee_open = float(pos.get("fee_open") or 0)
    fee_open_part = fee_open * frac
    fee_close = _fee_on(close_qty, exit_px)
    fund = float(pos.get("funding_acc") or 0) * frac
    net = gross - fee_open_part - fee_close + fund
    margin_back = MARGIN * frac
    b["cash"] = round(float(b["cash"]) + margin_back + net, 2)
    b["fees"] = round(float(b.get("fees") or 0) + fee_close, 2)
    pos["qty"] = remain
    pos["fee_open"] = fee_open - fee_open_part
    pos["funding_acc"] = float(pos.get("funding_acc") or 0) - fund
    pos["tp1_done"] = True
    pos["margin"] = MARGIN * (1.0 - frac)
    closed = _ts()
    rec = {
        "id": pos["id"] + "a",
        "t": closed,
        "iso": _iso(),
        "symbol": pos["symbol"],
        "base": pos["base"],
        "side": pos["side"],
        "entry": pos["entry"],
        "exit": exit_px,
        "reason": reason,
        "gross": round(gross, 2),
        "commission": round(fee_open_part + fee_close, 2),
        "funding": round(fund, 4),
        "net": round(net, 2),
        "opened": str(pos.get("opened") or ""),
        "opened_iso": str(pos.get("opened_iso") or ""),
        "closed": closed,
        "closed_iso": _iso(),
        "mins": _hold_mins(pos),
        "partial": True,
    }
    hist = b.setdefault("history", [])
    hist.append(rec)
    if len(hist) > 400:
        del hist[:-400]
    return rec


def _hold_mins(p: dict, closed_iso: str = "") -> int:
    start = _opened_ms(p)
    if closed_iso:
        try:
            end = int(datetime.fromisoformat(closed_iso).timestamp() * 1000)
        except Exception:
            end = int(time.time() * 1000)
    else:
        end = int(time.time() * 1000)
    if start <= 0:
        t0 = _parse_short_ts(str(p.get("opened") or ""))
        t1 = _parse_short_ts(str(p.get("t") or p.get("closed") or ""))
        if t0 and t1 and t1 >= t0:
            return max(0, int((t1 - t0).total_seconds() // 60))
        return 0
    return max(0, int((end - start) / 60000))


def _parse_short_ts(s: str) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    year = _now().year
    for fmt in ("%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(s[:16] if fmt.startswith("%m") else s[:19], fmt)
            if fmt.startswith("%m"):
                dt = dt.replace(year=year, tzinfo=_TZ)
            return dt
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _opened_ms(p: dict) -> int:
    if p.get("opened_ms"):
        try:
            return int(p["opened_ms"])
        except (TypeError, ValueError):
            pass
    iso = str(p.get("opened_iso") or "")
    try:
        return int(datetime.fromisoformat(iso).timestamp() * 1000)
    except Exception:
        return 0


def _apply_funding(p: dict, info: dict) -> float:
    now_ms = int(time.time() * 1000)
    next_f = int(info.get("next_fund") or 0)
    last_event = next_f - FUND_MS if next_f else 0
    if last_event <= 0:
        return 0.0
    last_paid = int(p.get("last_funding_ms") or 0)
    if _opened_ms(p) < last_event <= now_ms and last_paid < last_event:
        rate = float(info.get("funding") or 0)
        mark = float(info.get("mark") or p.get("entry") or 0)
        raw = _qty_of(p) * mark * rate
        paid = -raw if p["side"] == "LONG" else raw
        p["funding_acc"] = float(p.get("funding_acc") or 0) + paid
        p["last_funding_ms"] = last_event
        return paid
    return 0.0


def _prefetch_frames(coins: list[str]) -> dict:
    frames: dict = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        futs = {pool.submit(_klines, s): s for s in coins}
        for fut in as_completed(futs):
            df = None
            try:
                df = fut.result()
            except Exception:
                pass
            if df is not None and len(df) >= 30:
                frames[futs[fut]] = df
    return frames


def _eval_hits(b: dict, frames: dict, marks: dict[str, dict]) -> tuple[str, list[tuple], str]:
    last = ""
    try:
        inst = _load_instance(b)
    except Exception as e:
        return str(e)[:160], [], last
    hits: list[tuple] = []
    for sym, df in frames.items():
        try:
            res = _call_run(inst, df) or {}
        except Exception:
            continue
        sig = str(res.get("signal") or "")
        last = f"{sym.replace('USDT', '')} {sig}"
        side = _side_of(sig)
        if not side:
            continue
        info = marks.get(sym) or {}
        hits.append((
            float(info.get("qv") or 0),
            sym,
            side,
            str(res.get("description") or sig)[:48],
            float(info.get("chg") or 0),
        ))
    hits.sort(key=lambda x: -x[0])
    return "", hits, last


def _scan_once() -> None:
    import pandas as pd  # noqa: F401 — ALG dosyaları pandas ister
    marks = _marks()
    if not marks:
        return
    coins = _coin_universe(marks)
    frames = _prefetch_frames(coins)

    with _lock:
        st = _load()
        books = [b for b in st["algos"].values() if b.get("active") and b.get("auto")]
        for b in st["algos"].values():
            for p in list(b.get("positions") or []):
                info = marks.get(p["symbol"]) or {}
                mk = float(info.get("mark") or info.get("price") or 0)
                if mk <= 0:
                    continue
                _apply_funding(p, info)
                if p.get("atr") or p.get("r_dist"):
                    _refresh_trail(p, mk, frames.get(p["symbol"]))
                why = _hit_exit(p, mk)
                if why == "take_profit_1":
                    _close_partial(b, p, marks, 0.5, why)
                elif why:
                    _close_one(b, p["id"], marks, why)
        _save()

    scored: list[tuple] = []
    for b in books:
        err, hits, last = _eval_hits(b, frames, marks)
        scored.append((b["id"], err, hits, last))

    with _lock:
        st = _load()
        pending: list[dict] = []
        for aid, err, hits, last in scored:
            b = st["algos"].get(aid)
            if not b:
                continue
            b["error"] = err
            b["last_signal"] = last
            if err:
                continue
            held = {p["symbol"] for p in b.get("positions") or []}
            for qv, sym, side, desc, chg in hits:
                if sym in held:
                    continue
                if len(held) >= MAX_POS:
                    pending.append({
                        "symbol": sym,
                        "base": sym.replace("USDT", ""),
                        "side": side,
                        "note": desc,
                        "chg": chg,
                        "algo": b["code"],
                    })
                    continue
                if _open_pos(b, sym, side, marks, frames.get(sym)):
                    held.add(sym)
        st["pending"] = pending[:40]
        st["last_scan"] = _iso()
        _save()


def _loop() -> None:
    time.sleep(2)
    while True:
        try:
            _scan_once()
        except Exception:
            traceback.print_exc()
        time.sleep(SCAN_SEC)


def ensure_started() -> None:
    global _thread
    with _lock:
        _load()
        if _thread and _thread.is_alive():
            return
        _thread = threading.Thread(target=_loop, name="algo-paper", daemon=True)
        _thread.start()
