"""1H Confluence Sistemi — Pine v5 portu (BTC/ETH/SOL ve diğer USDT perp).

Bileşenler (aynı varsayılanlar):
  1) 4H EMA20/EMA50 trend
  2) 1m CVD proxy (close>open = alım hacmi)
  3) OI + fiyat eğimi (ikisi aynı yönde / OI↑ fiyat↓)
  4) ATR kapısı (yön değil)

lookahead_off: kapalı 4H bar; son (açık) 1H barda oluşan 4H EMA kullanılır.
"""
from __future__ import annotations

import json
import math
import urllib.request
from concurrent.futures import ThreadPoolExecutor

_BN = "https://fapi.binance.com"
_HDR = {"User-Agent": "CEMAPI"}
_HOUR = 3_600_000
_H4 = 4 * _HOUR

# Pine girdileri (sabit — panelde değiştirilmez)
HTF_FAST, HTF_SLOW = 20, 50
CVD_SMA, OI_LOOKBACK = 20, 14
ATR_LEN, VOL_SMA, VOL_MIN = 14, 50, 0.5
MIN_CONF = 2


def _get(url: str, timeout: float = 10) -> object:
    req = urllib.request.Request(url, headers=_HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _klines(symbol: str, interval: str, limit: int, end_time: int | None = None) -> list[dict]:
    q = f"symbol={symbol}&interval={interval}&limit={max(20, min(1500, limit))}"
    if end_time is not None:
        q += f"&endTime={int(end_time)}"
    try:
        rows = _get(f"{_BN}/fapi/v1/klines?{q}")
    except Exception:
        return []
    out = []
    for k in rows or []:
        try:
            out.append({
                "t": int(k[0]),
                "o": float(k[1]),
                "h": float(k[2]),
                "l": float(k[3]),
                "c": float(k[4]),
                "v": float(k[5]),
            })
        except (TypeError, ValueError, IndexError):
            continue
    return out


def _klines_1m(symbol: str, hours: int = 50) -> list[dict]:
    """Son ~hours saat 1m — CVD için. 1500 bar/istek."""
    need = min(1500 * 3, hours * 60)
    pages = max(1, math.ceil(need / 1500))
    chunks: list[list[dict]] = []
    end: int | None = None
    for _ in range(pages):
        part = _klines(symbol, "1m", 1500, end)
        if not part:
            break
        chunks.append(part)
        end = part[0]["t"] - 1
        if len(part) < 1400:
            break
    merged: dict[int, dict] = {}
    for part in chunks:
        for b in part:
            merged[b["t"]] = b
    return [merged[t] for t in sorted(merged)]


def _oi_hist(symbol: str, limit: int = 200) -> dict[int, float]:
    url = f"{_BN}/futures/data/openInterestHist?symbol={symbol}&period=1h&limit={min(500, limit)}"
    try:
        rows = _get(url, timeout=8)
    except Exception:
        return {}
    out: dict[int, float] = {}
    for row in rows or []:
        try:
            ts = int(row["timestamp"])
            # Binance: timestamp dönem sonu
            t_open = (ts - 1) - ((ts - 1) % _HOUR)
            out[t_open] = float(row["sumOpenInterest"])
        except (TypeError, ValueError, KeyError):
            continue
    return out


def _sma(values: list[float], length: int) -> list[float]:
    out = [float("nan")] * len(values)
    if length < 1:
        return out
    for i in range(length - 1, len(values)):
        window = values[i + 1 - length:i + 1]
        if any(math.isnan(x) for x in window):
            continue
        out[i] = sum(window) / length
    return out


def _ema(values: list[float], length: int) -> list[float]:
    out = [float("nan")] * len(values)
    if length < 1 or len(values) < length:
        return out
    seed = sum(values[:length]) / length
    out[length - 1] = seed
    prev = seed
    alpha = 2.0 / (length + 1)
    for i in range(length, len(values)):
        prev = alpha * values[i] + (1.0 - alpha) * prev
        out[i] = prev
    return out


def _rma(values: list[float], length: int) -> list[float]:
    out = [float("nan")] * len(values)
    if length < 1 or len(values) < length:
        return out
    seed = sum(values[:length]) / length
    out[length - 1] = seed
    prev = seed
    alpha = 1.0 / length
    for i in range(length, len(values)):
        prev = alpha * values[i] + (1.0 - alpha) * prev
        out[i] = prev
    return out


def _atr(bars: list[dict], length: int) -> list[float]:
    trs: list[float] = []
    for i, b in enumerate(bars):
        hl = b["h"] - b["l"]
        if i == 0:
            trs.append(hl)
            continue
        pc = bars[i - 1]["c"]
        trs.append(max(hl, abs(b["h"] - pc), abs(b["l"] - pc)))
    return _rma(trs, length)


def _dir_label(bull: bool, bear: bool) -> str:
    if bull:
        return "YUKARI"
    if bear:
        return "AŞAĞI"
    return "NÖTR"


def _htf_emas(h4: list[dict], t: int, live: bool) -> tuple[float, float]:
    """lookahead_off: kapanmış 4H; live son barda oluşan 4H."""
    if not h4:
        return float("nan"), float("nan")
    closes = [b["c"] for b in h4]
    fast = _ema(closes, HTF_FAST)
    slow = _ema(closes, HTF_SLOW)
    idx = None
    for i, b in enumerate(h4):
        close_t = b["t"] + _H4
        if close_t <= t:
            idx = i
        elif live and b["t"] <= t < close_t:
            idx = i
    if idx is None:
        return float("nan"), float("nan")
    return fast[idx], slow[idx]


def _cvd_hourly(m1: list[dict]) -> dict[int, float]:
    delta: dict[int, float] = {}
    for b in m1:
        hour = b["t"] - (b["t"] % _HOUR)
        d = b["v"] if b["c"] > b["o"] else (-b["v"] if b["c"] < b["o"] else 0.0)
        delta[hour] = delta.get(hour, 0.0) + d
    return delta


def compute(symbol: str) -> dict:
    empty = {
        "ok": False, "symbol": symbol, "htf": "NÖTR", "cvd": "NÖTR",
        "oi": "NÖTR", "vol_ok": False, "bull_score": 0, "bear_score": 0,
        "long": False, "short": False, "long_new": False, "short_new": False,
        "ema_fast": None, "ema_slow": None, "sl": None, "tp": None, "bars": [],
    }
    with ThreadPoolExecutor(max_workers=4) as ex:
        f_1h = ex.submit(_klines, symbol, "1h", 220)
        f_4h = ex.submit(_klines, symbol, "4h", 180)
        f_oi = ex.submit(_oi_hist, symbol, 220)
        f_1m = ex.submit(_klines_1m, symbol, 50)
        h1 = f_1h.result()
        h4 = f_4h.result()
        oi_map = f_oi.result()
        m1 = f_1m.result()
    if len(h1) < VOL_SMA + ATR_LEN:
        return empty

    atrs = _atr(h1, ATR_LEN)
    atr_avg = _sma(atrs, VOL_SMA)
    hour_delta = _cvd_hourly(m1)
    cvd_hours = sorted(hour_delta)
    cvd_cum_map: dict[int, float] = {}
    run = 0.0
    for ht in cvd_hours:
        run += hour_delta[ht]
        cvd_cum_map[ht] = run
    cvd_series = [cvd_cum_map[t] for t in cvd_hours]
    cvd_sma_s = _sma(cvd_series, CVD_SMA)
    cvd_sma_map = {t: cvd_sma_s[i] for i, t in enumerate(cvd_hours)}

    bars_out = []
    last_long = last_short = False
    for i, b in enumerate(h1):
        t = b["t"]
        live = i == len(h1) - 1
        ema_f, ema_s = _htf_emas(h4, t, live)
        htf_bull = (not math.isnan(ema_f)) and (not math.isnan(ema_s)) and ema_f > ema_s
        htf_bear = (not math.isnan(ema_f)) and (not math.isnan(ema_s)) and ema_f < ema_s

        cvd_ok = t in cvd_cum_map and t in cvd_sma_map and not math.isnan(cvd_sma_map[t])
        cvd_bull = cvd_ok and cvd_cum_map[t] > cvd_sma_map[t]
        cvd_bear = cvd_ok and cvd_cum_map[t] < cvd_sma_map[t]

        oi_t = t if t in oi_map else (max((k for k in oi_map if k <= t), default=None) if live else None)
        oi_now = oi_map.get(oi_t) if oi_t is not None else None
        oi_prev_t = (oi_t - OI_LOOKBACK * _HOUR) if oi_t is not None else None
        oi_prev = oi_map.get(oi_prev_t) if oi_prev_t is not None else None
        oi_avail = oi_now is not None and oi_prev is not None
        price_slope = b["c"] - h1[i - OI_LOOKBACK]["c"] if i >= OI_LOOKBACK else float("nan")
        oi_slope = (oi_now - oi_prev) if oi_avail else float("nan")
        oi_bull = oi_avail and oi_slope > 0 and (not math.isnan(price_slope)) and price_slope > 0
        oi_bear = oi_avail and oi_slope > 0 and (not math.isnan(price_slope)) and price_slope < 0

        atr = atrs[i]
        avg = atr_avg[i]
        vol_ok = (not math.isnan(atr)) and (not math.isnan(avg)) and atr > avg * VOL_MIN

        bull = (1 if htf_bull else 0) + (1 if cvd_bull else 0) + (1 if oi_bull else 0)
        bear = (1 if htf_bear else 0) + (1 if cvd_bear else 0) + (1 if oi_bear else 0)
        long_c = bull >= MIN_CONF and vol_ok
        short_c = bear >= MIN_CONF and vol_ok
        long_new = long_c and not last_long
        short_new = short_c and not last_short
        last_long, last_short = long_c, short_c

        bars_out.append({
            "t": t,
            "ema_fast": None if math.isnan(ema_f) else round(ema_f, 6),
            "ema_slow": None if math.isnan(ema_s) else round(ema_s, 6),
            "long": long_c,
            "short": short_c,
            "long_new": long_new,
            "short_new": short_new,
            "bull": bull,
            "bear": bear,
            "vol_ok": vol_ok,
            "cvd_ok": cvd_ok,
            "oi_ok": oi_avail,
            "htf": _dir_label(htf_bull, htf_bear),
            "cvd": _dir_label(cvd_bull, cvd_bear) if cvd_ok else "n/a",
            "oi": _dir_label(oi_bull, oi_bear) if oi_avail else "n/a",
        })

    last = bars_out[-1]
    atr_last = atrs[-1]
    sl = None if math.isnan(atr_last) else round(atr_last * 1.5, 6)
    tp = None if sl is None else round(sl * 1.5, 6)
    return {
        "ok": True,
        "symbol": symbol,
        "htf": last["htf"],
        "cvd": last["cvd"],
        "oi": last["oi"],
        "vol_ok": last["vol_ok"],
        "bull_score": last["bull"],
        "bear_score": last["bear"],
        "long": last["long"],
        "short": last["short"],
        "long_new": last["long_new"],
        "short_new": last["short_new"],
        "ema_fast": last["ema_fast"],
        "ema_slow": last["ema_slow"],
        "sl": sl,
        "tp": tp,
        "cvd_n/a": last["cvd"] == "n/a",
        "oi_n/a": last["oi"] == "n/a",
        "bars": bars_out[-120:],
    }
