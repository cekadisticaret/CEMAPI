"""ATR Kripto Trading Sistemi — PDF kuralları (15m paper).

Kaynak: ALG/ATR_Kripto_Trading_Sistemi.pdf
Yön vermez; volatiliteye göre stop, hedef ve işlem filtresi üretir.
"""
from __future__ import annotations

ATR_PERIOD = 14
ATR_SL_MULT = 1.5       # 5–15m / saatlik
ATR_TRAIL_MULT = 2.5    # Chandelier, 1R sonra
TP1_R = 1.5
TP2_R = 2.5
ATRP_NO_TRADE = 8.0     # üstü işlem yok


def true_range(high, low, close):
    prev = close.shift(1)
    import pandas as pd
    return pd.concat([
        high - low,
        (high - prev).abs(),
        (low - prev).abs(),
    ], axis=1).max(axis=1)


def atr_series(high, low, close, period: int = ATR_PERIOD):
    return true_range(high, low, close).rolling(window=period).mean()


def atr_last(df, period: int = ATR_PERIOD) -> float:
    if df is None or len(df) < period + 2:
        return 0.0
    try:
        s = atr_series(df["high"], df["low"], df["close"], period)
        v = float(s.iloc[-1])
    except Exception:
        return 0.0
    return v if v == v and v > 0 else 0.0


def atrp(atr: float, price: float) -> float:
    if price <= 0 or atr <= 0:
        return 0.0
    return 100.0 * atr / price


def levels(side: str, entry: float, atr: float) -> dict:
    """SL = giriş ± 1.5×ATR, TP1=1.5R, TP2=2.5R."""
    r = atr * ATR_SL_MULT
    if side == "LONG":
        sl = entry - r
        tp1 = entry + r * TP1_R
        tp2 = entry + r * TP2_R
    else:
        sl = entry + r
        tp1 = entry - r * TP1_R
        tp2 = entry - r * TP2_R
    return {"atr": atr, "r_dist": r, "sl": sl, "tp1": tp1, "tp2": tp2, "tp": tp2}


def sl_clears_liq(side: str, entry: float, sl: float, liq: float) -> bool:
    """SL likidasyonun güvenli tarafında, mesafenin %20'si kadar tampon."""
    if entry <= 0 or sl <= 0 or liq <= 0:
        return False
    if side == "LONG":
        gap = entry - sl
        return gap > 0 and sl > liq and (sl - liq) >= 0.20 * gap
    gap = sl - entry
    return gap > 0 and sl < liq and (liq - sl) >= 0.20 * gap


def trail_stop(side: str, extreme: float, atr: float) -> float:
    if side == "LONG":
        return extreme - ATR_TRAIL_MULT * atr
    return extreme + ATR_TRAIL_MULT * atr
