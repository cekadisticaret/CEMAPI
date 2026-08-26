"""
liquidity_sweep_proxy.py
Likidite Sweep Proxy: Stop hunt / likidite avı tespiti.
"""
import pandas as pd
import numpy as np
from typing import Dict

class LiquiditySweepProxy:
    def __init__(self, lookback: int = 20, sweep_threshold: float = 0.005):
        self.lookback = lookback
        self.sweep_threshold = sweep_threshold

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})
        df["prev_high"] = high.shift(1).rolling(self.lookback).max()
        df["prev_low"] = low.shift(1).rolling(self.lookback).min()
        df["range"] = df["prev_high"] - df["prev_low"]
        return df

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        # Sweep tespiti
        swept_high = latest["high"] > latest["prev_high"] and close.iloc[-1] < latest["prev_high"]
        swept_low = latest["low"] < latest["prev_low"] and close.iloc[-1] > latest["prev_low"]

        if swept_high:
            signal = "SWEEP_HIGH"
            desc = "Yüksek likidite avlandı (sweep) ve fiyat geri döndü. Bearish."
        elif swept_low:
            signal = "SWEEP_LOW"
            desc = "Düşük likidite avlandı (sweep) ve fiyat geri döndü. Bullish."
        else:
            signal = "NO_SWEEP"
            desc = "Likidite sweep tespit edilmedi."

        return {
            "signal": signal,
            "prev_high": round(float(latest["prev_high"]), 2) if not pd.isna(latest["prev_high"]) else None,
            "prev_low": round(float(latest["prev_low"]), 2) if not pd.isna(latest["prev_low"]) else None,
            "current_high": round(float(latest["high"]), 2),
            "current_low": round(float(latest["low"]), 2),
            "close": round(float(latest["close"]), 2),
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(LiquiditySweepProxy().run(high, low, close))
