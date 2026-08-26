"""
fibonacci_retracement.py
Fibonacci Retracement: Son swing high/low'dan Fib seviyeleri.
"""
import pandas as pd
import numpy as np
from typing import Dict

class FibonacciRetracement:
    def __init__(self, lookback: int = 50):
        self.lookback = lookback
        self.levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        swing_high = high.iloc[-self.lookback:].max()
        swing_low = low.iloc[-self.lookback:].min()
        current = close.iloc[-1]

        diff = swing_high - swing_low
        fib_levels = {}
        for level in self.levels:
            fib_levels[f"fib_{int(level*1000)}"] = swing_high - diff * level

        # Hangi seviyede olduğumuzu bul
        nearest = None
        min_dist = float('inf')
        for level in self.levels:
            price_level = swing_high - diff * level
            dist = abs(current - price_level) / diff
            if dist < min_dist:
                min_dist = dist
                nearest = level

        # Golden zone (0.618-0.65) veya 0.382 yakınında mı?
        in_golden = 0.618 <= (swing_high - current) / diff <= 0.65

        return {
            "swing_high": round(float(swing_high), 2),
            "swing_low": round(float(swing_low), 2),
            "current": round(float(current), 2),
            "fib_levels": {f"{int(l*100)}%": round(float(swing_high - diff * l), 2) for l in self.levels},
            "nearest_level": f"{int(nearest*100)}%",
            "in_golden_zone": in_golden,
            "retracement_pct": f"{(swing_high - current) / diff:.1%}"
        }

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        data = self.calculate(high, low, close)

        retracement = (data["swing_high"] - data["current"]) / (data["swing_high"] - data["swing_low"])

        if 0.60 <= retracement <= 0.70:
            signal = "GOLDEN_ZONE"
            desc = f"Fiyat 0.618 golden zone'da ({data['retracement_pct']}). Alım fırsatı."
        elif 0.35 <= retracement <= 0.42:
            signal = "382_ZONE"
            desc = f"Fiyat 0.382 seviyesinde ({data['retracement_pct']}). Direnç/destek."
        elif retracement < 0.1:
            signal = "NEAR_HIGH"
            desc = "Fiyat swing high'a yakın. Yeni pozisyon riskli."
        elif retracement > 0.9:
            signal = "NEAR_LOW"
            desc = "Fiyat swing low'a yakın. Dip arayışı."
        else:
            signal = "NEUTRAL"
            desc = f"Fiyat {data['retracement_pct']} retracement'da."

        return {
            "signal": signal,
            "fib_data": data,
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(FibonacciRetracement().run(high, low, close))
