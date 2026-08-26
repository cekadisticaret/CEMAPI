"""İşlemler ekranı — 5m / 15m / 1h BTC·ETH·SOL, CLOB anlık kotasyon + emir."""
from __future__ import annotations

import json
import math
import os
import re
import time
import urllib.request
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pm_trader_helpers as pmh

_TZ_TR = ZoneInfo("Europe/Istanbul")
_TZ_ET = ZoneInfo("America/New_York")
_DIR = os.path.dirname(os.path.abspath(__file__))
_STATE = os.path.join(_DIR, "desk_state.json")
_SYMS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
_SHORT = {"BTCUSDT": "BTC", "ETHUSDT": "ETH", "SOLUSDT": "SOL"}
_PERIODS = (5, 15, 60)
_BN_HDR = {"User-Agent": "CEMAPI"}
_MKT_CACHE: dict[tuple, tuple[float, dict | None]] = {}
_SPOT_CACHE: dict[str, tuple[float, float | None]] = {}
_FUT_CACHE: dict = {"t": 0.0, "rows": []}
_MVRVZ_CACHE: dict[str, tuple[float, dict]] = {}
_CONF_CACHE: dict[str, tuple[float, dict]] = {}
_SYM_RE = re.compile(r"^[A-Z0-9]{4,25}$")


def _norm_fut_symbol(symbol: str) -> str:
    s = (symbol or "").upper().strip()
    if not _SYM_RE.fullmatch(s) or not s.endswith("USDT") or "_" in s:
        return ""
    return s


def _now_tr() -> datetime:
    return datetime.now(_TZ_TR)


def _load() -> dict:
    if os.path.exists(_STATE):
        try:
            with open(_STATE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"open_positions": []}


def _save(state: dict) -> None:
    tmp = _STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _STATE)


def slot_meta(period: int, now: datetime | None = None) -> dict:
    now = now or _now_tr()
    utc = now.astimezone(ZoneInfo("UTC"))
    if period == 60:
        start = now.replace(minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        et = now.astimezone(_TZ_ET)
        return {
            "period": 60,
            "ts": int(start.timestamp()),
            "start_tr": start,
            "end_tr": end,
            "slot_tr": f"{start:%H:%M}–{end:%H:%M}",
            "et_hour": et.hour,
            "left_sec": max(0, int((end - now).total_seconds())),
        }
    sec = period * 60
    ts = int(utc.timestamp()) // sec * sec
    start = datetime.fromtimestamp(ts, tz=ZoneInfo("UTC")).astimezone(_TZ_TR)
    end = start + timedelta(minutes=period)
    return {
        "period": period,
        "ts": ts,
        "start_tr": start,
        "end_tr": end,
        "slot_tr": f"{start:%H:%M}–{end:%H:%M}",
        "et_hour": None,
        "left_sec": max(0, int((end - now).total_seconds())),
    }


def find_market(symbol: str, period: int, slot: dict | None = None) -> dict | None:
    slot = slot or slot_meta(period)
    key = (symbol, period, int(slot["ts"]))
    hit = _MKT_CACHE.get(key)
    if hit and time.time() - hit[0] < 25:
        return hit[1]
    found = _find_market_raw(symbol, period, slot)
    _MKT_CACHE[key] = (time.time(), found)
    return found


def _find_market_raw(symbol: str, period: int, slot: dict) -> dict | None:
    if period == 60:
        pm = pmh.pm_find_market(symbol, int(slot["et_hour"]), _now_tr())
        if not pm:
            return None
        return {
            "slug": pm.get("slug"),
            "title": pm.get("title") or "",
            "closed": bool(pm.get("closed")),
            "up_token": pm.get("up_token") or "",
            "down_token": pm.get("down_token") or "",
            "up_price": float((pm.get("outcome_prices") or [0.5, 0.5])[0] or 0.5),
            "down_price": float((pm.get("outcome_prices") or [0.5, 0.5])[1] or 0.5),
            "tick_size": str(pm.get("tick_size") or "0.01"),
            "neg_risk": bool(pm.get("neg_risk")),
        }
    return pmh.pm_updown_find_market(int(slot["ts"]), symbol, period_min=period)


def _binance_last(symbol: str) -> float | None:
    hit = _SPOT_CACHE.get(symbol)
    if hit and time.time() - hit[0] < 1.5:
        return hit[1]
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
        req = urllib.request.Request(url, headers=_BN_HDR)
        with urllib.request.urlopen(req, timeout=8) as r:
            px = float(json.loads(r.read().decode()).get("price") or 0)
        _SPOT_CACHE[symbol] = (time.time(), px)
        return px
    except Exception:
        if hit:
            return hit[1]
        return None


def _binance_open(symbol: str, start: datetime, interval: str) -> float | None:
    ms = int(start.timestamp() * 1000)
    url = (
        "https://fapi.binance.com/fapi/v1/klines?"
        f"symbol={symbol}&interval={interval}&startTime={ms}&limit=1"
    )
    try:
        req = urllib.request.Request(url, headers=_BN_HDR)
        with urllib.request.urlopen(req, timeout=8) as r:
            rows = json.loads(r.read().decode())
        if not rows:
            return None
        return float(rows[0][1])
    except Exception:
        return None


def futures_symbols() -> list[dict]:
    """USDT-M perpetual (TRADING) — hacme göre, BTC/ETH/SOL üstte. 60s cache."""
    now = time.time()
    if _FUT_CACHE["rows"] and now - _FUT_CACHE["t"] < 60:
        return _FUT_CACHE["rows"]
    try:
        req = urllib.request.Request(
            "https://fapi.binance.com/fapi/v1/exchangeInfo", headers=_BN_HDR
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            info = json.loads(r.read().decode())
        req2 = urllib.request.Request(
            "https://fapi.binance.com/fapi/v1/ticker/24hr", headers=_BN_HDR
        )
        with urllib.request.urlopen(req2, timeout=15) as r:
            ticks = json.loads(r.read().decode())
    except Exception:
        return list(_FUT_CACHE["rows"] or [])
    tick_map = {
        t.get("symbol"): t
        for t in (ticks or [])
        if isinstance(t, dict) and t.get("symbol")
    }
    rows: list[dict] = []
    for s in info.get("symbols") or []:
        if s.get("contractType") != "PERPETUAL":
            continue
        if s.get("quoteAsset") != "USDT" or s.get("status") != "TRADING":
            continue
        sym = _norm_fut_symbol(str(s.get("symbol") or ""))
        if not sym:
            continue
        t = tick_map.get(sym) or {}
        try:
            last = float(t.get("lastPrice") or 0)
            chg = float(t.get("priceChangePercent") or 0)
            qv = float(t.get("quoteVolume") or 0)
        except (TypeError, ValueError):
            last, chg, qv = 0.0, 0.0, 0.0
        base = str(s.get("baseAsset") or sym[:-4])
        rows.append({
            "symbol": sym,
            "base": base,
            "price": last,
            "chg": chg,
            "qv": qv,
        })
    pin = {s: i for i, s in enumerate(_SYMS)}
    rows.sort(key=lambda x: (pin.get(x["symbol"], 99), -x["qv"]))
    _FUT_CACHE["t"] = now
    _FUT_CACHE["rows"] = rows
    return rows


def klines(symbol: str, interval: str = "1m", limit: int = 100) -> list[dict]:
    symbol = _norm_fut_symbol(symbol)
    if not symbol:
        return []
    if interval not in ("1m", "5m", "15m", "1h"):
        interval = "1m"
    url = (
        "https://fapi.binance.com/fapi/v1/klines?"
        f"symbol={symbol}&interval={interval}&limit={max(20, min(200, limit))}"
    )
    try:
        req = urllib.request.Request(url, headers=_BN_HDR)
        with urllib.request.urlopen(req, timeout=10) as r:
            rows = json.loads(r.read().decode())
    except Exception:
        return []
    out = []
    for k in rows:
        out.append({
            "t": int(k[0]),
            "o": float(k[1]),
            "h": float(k[2]),
            "l": float(k[3]),
            "c": float(k[4]),
            "v": float(k[5]),
        })
    return out


def _daily_closes(symbol: str, limit: int = 500) -> list[tuple[int, float]]:
    url = (
        "https://fapi.binance.com/fapi/v1/klines?"
        f"symbol={symbol}&interval=1d&limit={max(80, min(1000, limit))}"
    )
    try:
        req = urllib.request.Request(url, headers=_BN_HDR)
        with urllib.request.urlopen(req, timeout=12) as r:
            rows = json.loads(r.read().decode())
    except Exception:
        return []
    out: list[tuple[int, float]] = []
    for k in rows:
        try:
            out.append((int(k[0]), float(k[4])))
        except (TypeError, ValueError, IndexError):
            continue
    return out


def _pine_stdev(window: list[float]) -> float:
    n = len(window)
    if n < 2:
        return 0.0
    mean = sum(window) / n
    var = sum((x - mean) ** 2 for x in window) / n
    return math.sqrt(var) if var > 0 else 0.0


def _pine_ema(values: list[float], length: int) -> list[float]:
    out = [float("nan")] * len(values)
    if length < 1:
        return out
    valid = [i for i, v in enumerate(values) if not math.isnan(v)]
    if len(valid) < length:
        return out
    first = valid[:length]
    seed = sum(values[i] for i in first) / length
    last_i = first[-1]
    out[last_i] = seed
    prev = seed
    alpha = 2.0 / (length + 1)
    for i in range(last_i + 1, len(values)):
        if math.isnan(values[i]):
            continue
        prev = alpha * values[i] + (1.0 - alpha) * prev
        out[i] = prev
    return out


def mvrvz_risk(symbol: str) -> dict:
    """Pine MVRVZ-Risk (v6) — sentetik Z (grafik close). On-chain BTC/ETH yok."""
    symbol = _norm_fut_symbol(symbol)
    empty = {
        "ok": False, "symbol": symbol, "mode": "sentetik",
        "risk": None, "signal": None, "z": None, "al": False, "sat": False,
        "bars": [],
    }
    if not symbol:
        return empty
    hit = _MVRVZ_CACHE.get(symbol)
    if hit and time.time() - hit[0] < 90:
        return hit[1]

    period = 365
    z_max, z_min = 4.0, -2.0
    curve = 0.523
    sig_len = 14
    buy_th, sell_th = 0.35, 0.65

    daily = _daily_closes(symbol, 500)
    if len(daily) < max(30, sig_len + 5):
        return empty

    use_n = period if len(daily) >= period else max(30, len(daily) - 1)
    closes = [c for _, c in daily]
    risks: list[float] = []
    zs: list[float] = []
    for i in range(len(closes)):
        if i + 1 < use_n:
            risks.append(float("nan"))
            zs.append(float("nan"))
            continue
        window = closes[i + 1 - use_n:i + 1]
        std = _pine_stdev(window)
        sma = sum(window) / use_n
        z = ((closes[i] - sma) / std) if std else 0.0
        raw = (z - z_min) / (z_max - z_min)
        clamped = max(0.0, min(1.0, raw))
        risks.append(clamped ** curve)
        zs.append(z)

    signals = _pine_ema(risks, sig_len)
    bars = []
    last_al = last_sat = False
    last_risk = last_sig = last_z = None
    for i, ((t, _), risk, sig, z) in enumerate(zip(daily, risks, signals, zs)):
        if math.isnan(risk) or math.isnan(sig):
            continue
        al = sat = False
        if i > 0 and not math.isnan(risks[i - 1]) and not math.isnan(signals[i - 1]):
            al = risks[i - 1] <= signals[i - 1] and risk > sig and risk <= buy_th
            sat = risks[i - 1] >= signals[i - 1] and risk < sig and risk >= sell_th
        last_al, last_sat = al, sat
        last_risk, last_sig, last_z = risk, sig, z
        bars.append({
            "t": t,
            "risk": round(risk, 4),
            "signal": round(sig, 4),
            "al": al,
            "sat": sat,
        })

    out = {
        "ok": bool(bars),
        "symbol": symbol,
        "mode": "sentetik",
        "period": use_n,
        "risk": None if last_risk is None else round(last_risk, 4),
        "signal": None if last_sig is None else round(last_sig, 4),
        "z": None if last_z is None else round(last_z, 3),
        "al": last_al,
        "sat": last_sat,
        "bars": bars[-180:],
    }
    _MVRVZ_CACHE[symbol] = (time.time(), out)
    return out


def confluence_1h(symbol: str) -> dict:
    """Pine 1H Confluence — HTF + CVD + OI + ATR kapısı."""
    symbol = _norm_fut_symbol(symbol)
    empty = {
        "ok": False, "symbol": symbol, "htf": "NÖTR", "cvd": "NÖTR",
        "oi": "NÖTR", "vol_ok": False, "bull_score": 0, "bear_score": 0,
        "long": False, "short": False, "bars": [],
    }
    if not symbol:
        return empty
    hit = _CONF_CACHE.get(symbol)
    if hit and time.time() - hit[0] < 25:
        return hit[1]
    try:
        from confluence_1h import compute
        out = compute(symbol)
    except Exception as e:
        out = {**empty, "error": str(e)[:160]}
    _CONF_CACHE[symbol] = (time.time(), out)
    return out


def _mum_skor(patterns: list) -> int:
    """BursaApp: son 5 mumda yönlü formasyon oyu — küçük tam sayı."""
    from candle_pattern_engine import pattern_net_score
    score = 0
    for pd in patterns[-5:]:
        net = pattern_net_score(pd)
        if net >= 25:
            score += 1
        elif net <= -25:
            score -= 1
    return int(score)


def chart_overlay(bars: list[dict]) -> dict:
    """BursaApp grafik kutusu: Mum skor · S · D (tek destek, tek direnç)."""
    if len(bars) < 5:
        return {"ok": False}
    try:
        import numpy as np
        from candle_pattern_engine import CandleEngine
        o = np.array([b["o"] for b in bars], dtype=float)
        h = np.array([b["h"] for b in bars], dtype=float)
        l = np.array([b["l"] for b in bars], dtype=float)
        c = np.array([b["c"] for b in bars], dtype=float)
        engine = CandleEngine(o, h, l, c)
        patterns = engine.detect_patterns()
        conf = engine.confluence_score()
    except Exception as e:
        return {"ok": False, "error": str(e)}

    ns = conf.nearest_support
    nr = conf.nearest_resistance
    return {
        "ok": True,
        "mum_skor": _mum_skor(patterns),
        "support": round(float(ns[0].price), 4) if ns else None,
        "resistance": round(float(nr[0].price), 4) if nr else None,
    }


def live_quote(token_id: str, amount: float) -> dict:
    q = pmh.pm_buy_quote(token_id, float(amount))
    if not q:
        return {"ok": False, "error": "CLOB kotasyonu yok — likidite veya bağlanı yok"}
    return {
        "ok": True,
        "price": q["price"],
        "size": q["size"],
        "spent": q["spent"],
        "to_win": q["to_win"],
        "net": q["net"],
    }


def snapshot(period: int = 60) -> dict:
    if period not in _PERIODS:
        period = 60
    slot = slot_meta(period)
    iv = "1h" if period == 60 else (f"{period}m")
    markets = []
    for sym in _SYMS:
        pm = find_market(sym, period, slot)
        last = _binance_last(sym)
        start_px = _binance_open(sym, slot["start_tr"], iv)
        up_c = dn_c = None
        if pm:
            ua, da = pmh.pm_best_asks(pm.get("up_token") or "", pm.get("down_token") or "")
            up_c = ua if ua is not None else pm.get("up_price")
            dn_c = da if da is not None else pm.get("down_price")
        delta = None
        if last is not None and start_px:
            delta = round(last - start_px, 4)
        markets.append({
            "symbol": sym,
            "short": _SHORT[sym],
            "title": (pm or {}).get("title") or "",
            "slug": (pm or {}).get("slug") or "",
            "closed": bool((pm or {}).get("closed")),
            "up_cent": round(float(up_c) * 100) if up_c else None,
            "down_cent": round(float(dn_c) * 100) if dn_c else None,
            "up_price": round(float(up_c), 3) if up_c else None,
            "down_price": round(float(dn_c), 3) if dn_c else None,
            "up_token": (pm or {}).get("up_token") or "",
            "down_token": (pm or {}).get("down_token") or "",
            "tick_size": (pm or {}).get("tick_size") or "0.01",
            "neg_risk": bool((pm or {}).get("neg_risk")),
            "spot": last,
            "spot_open": start_px,
            "spot_diff": delta,
            "ok": bool(pm and not pm.get("closed") and pm.get("up_token")),
        })
    return {
        "period": period,
        "slot_tr": slot["slot_tr"],
        "left_sec": slot["left_sec"],
        "now_tr": _now_tr().strftime("%d.%m.%Y %H:%M:%S İST"),
        "markets": markets,
        "positions": list_positions(),
        "balance": _balance(),
    }


def _balance() -> float | None:
    try:
        b = pmh.pm_get_balance()
        return round(b, 2) if b >= 0 else None
    except Exception:
        return None


def quote_for(symbol: str, period: int, direction: str, amount: float) -> dict:
    if symbol not in _SYMS:
        return {"ok": False, "error": "sembol yok"}
    if period not in _PERIODS:
        return {"ok": False, "error": "periyot yok"}
    direction = direction.upper()
    if direction not in ("UP", "DOWN"):
        return {"ok": False, "error": "yön UP/DOWN"}
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return {"ok": False, "error": "tutar sayı olmalı"}
    if not (1.0 <= amount <= 500.0):
        return {"ok": False, "error": "tutar $1–$500"}
    slot = slot_meta(period)
    if slot["left_sec"] < 8:
        return {"ok": False, "error": "slot bitmek üzere — yeni slot bekle"}
    pm = find_market(symbol, period, slot)
    if not pm or pm.get("closed") or not pm.get("up_token"):
        return {"ok": False, "error": "aktif PM market yok"}
    tid = pm["up_token"] if direction == "UP" else pm["down_token"]
    q = live_quote(tid, amount)
    if not q.get("ok"):
        return q
    q.update({
        "symbol": symbol,
        "short": _SHORT[symbol],
        "dir": direction,
        "period": period,
        "slot_tr": slot["slot_tr"],
        "token_id": tid,
        "slug": pm.get("slug"),
        "tick_size": pm.get("tick_size") or "0.01",
        "neg_risk": bool(pm.get("neg_risk")),
        "title": pm.get("title") or "",
        "left_sec": slot["left_sec"],
    })
    return q


def open_trade(symbol: str, period: int, direction: str, amount: float) -> tuple[dict, int]:
    q = quote_for(symbol, period, direction, amount)
    if not q.get("ok"):
        return q, 400
    pmh.PM_DRY_RUN = False
    order = pmh.pm_place_order(
        q["token_id"], float(amount),
        str(q.get("tick_size") or "0.01"),
        bool(q.get("neg_risk")),
        label="Desk",
        interactive=True,
    )
    if not order:
        reason = getattr(pmh, "_PM_LAST_ORDER_ERROR", None) or "emir başarısız"
        return {"ok": False, "error": reason}, 400
    slot = slot_meta(period)
    last = _binance_last(symbol)
    pos = {
        "id": str(uuid.uuid4()),
        "symbol": symbol,
        "short": _SHORT[symbol],
        "dir": direction.upper(),
        "period": period,
        "slot_tr": slot["slot_tr"],
        "entry_time_tr": _now_tr().isoformat(),
        "amount": float(amount),
        "pm_spent": float(order["spent"]),
        "pm_size": float(order["size"]),
        "pm_entry_price": float(order["price"]),
        "pm_token_id": q["token_id"],
        "pm_slug": q.get("slug"),
        "pm_order_id": order.get("order_id"),
        "pm_tick_size": q.get("tick_size") or "0.01",
        "spot_entry": last,
        "title": q.get("title") or "",
    }
    st = _load()
    st.setdefault("open_positions", []).append(pos)
    _save(st)
    return {"ok": True, "position": pos, "quote": q}, 200


def list_positions() -> list[dict]:
    rows = []
    for p in _load().get("open_positions") or []:
        tid = p.get("pm_token_id") or ""
        shares = pmh.pm_conditional_shares(tid) if tid else 0.0
        if shares is not None and shares < 0.4:
            continue
        bid = None
        close_val = None
        try:
            bid = pmh.pm_best_bid(tid)
        except Exception:
            bid = None
        size = float(p.get("pm_size") or 0)
        if bid and size:
            close_val = round(size * bid, 2)
        spent = float(p.get("pm_spent") or 0)
        rows.append({
            **p,
            "shares_now": shares if shares and shares >= 0 else size,
            "close_val": close_val,
            "close_pnl": round(close_val - spent, 2) if close_val is not None else None,
        })
    return rows


def close_trade(pos_id: str) -> tuple[dict, int]:
    st = _load()
    opens = st.get("open_positions") or []
    pos = next((p for p in opens if p.get("id") == pos_id), None)
    if not pos:
        return {"ok": False, "error": "pozisyon yok"}, 404
    tid = pos.get("pm_token_id") or ""
    if not tid:
        return {"ok": False, "error": "token yok"}, 400
    want = float(pos.get("pm_size") or 0)
    if want < 0.4:
        return {"ok": False, "error": "kayıtlı pay yok — mirror bakiyesine dokunulmadı"}, 400
    pmh.PM_DRY_RUN = False
    before = pmh.pm_conditional_shares(tid)
    fill = pmh.pm_sell_position(
        tid, want,
        tick_size=str(pos.get("pm_tick_size") or "0.01"),
        label="Desk",
    )
    after = pmh.pm_conditional_shares(tid)
    sold = 0.0
    if before is not None and after is not None and before >= 0 and after >= 0:
        sold = max(0.0, before - after)
    if fill or sold >= min(want, 0.5) * 0.7:
        proceeds = float((fill or {}).get("proceeds") or 0)
        spent = float(pos.get("pm_spent") or 0)
        pnl = round(proceeds - spent, 2) if fill else None
        st["open_positions"] = [p for p in opens if p.get("id") != pos_id]
        _save(st)
        return {"ok": True, "closed": pos.get("short"), "pnl": pnl, "proceeds": proceeds}, 200

    slug = str(pos.get("pm_slug") or "")
    res = pmh.pm_fetch_resolution(slug, min_decisive=0.90) if slug else None
    if res:
        up_won = bool(res.get("up_won"))
        won = (str(pos.get("dir") or "").upper() == "UP") == up_won
        size = float(pos.get("pm_size") or 0)
        proceeds = round(size if won else 0.0, 2)
        spent = float(pos.get("pm_spent") or 0)
        pnl = round(proceeds - spent, 2)
        st["open_positions"] = [p for p in opens if p.get("id") != pos_id]
        _save(st)
        return {
            "ok": True,
            "closed": pos.get("short"),
            "pnl": pnl,
            "proceeds": proceeds,
            "settled": True,
        }, 200

    err = getattr(pmh, "_PM_LAST_ORDER_ERROR", None) or "satış olmadı — defterde alıcı yok"
    return {"ok": False, "error": err}, 409
