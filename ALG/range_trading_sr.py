"""
range_trading_sr.py
Range Trading S/R Bounce: Destek/Direnç seviyelerinden sekme tespiti.
"""
import pandas as pd
import numpy as np
from typing import Dict

class RangeTradingSR:
    def __init__(self, lookback: int = 50, touch_threshold: float = 0.005):
        self.lookback = lookback
        self.touch_threshold = touch_threshold

    def find_levels(self, high: pd.Series, low: pd.Series) -> Dict:
        """Destek ve direnç seviyelerini bulur."""
        recent_high = high.iloc[-self.lookback:]
        recent_low = low.iloc[-self.lookback:]

        resistance = recent_high.max()
        support = recent_low.min()

        # Pivot noktaları
        highs = recent_high.values
        lows = recent_low.values

        # Basit cluster analizi
        return {
            "resistance": float(resistance),
            "support": float(support),
            "range": float(resistance - support),
            "mid": float((resistance + support) / 2)
        }

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        levels = self.find_levels(high, low)
        current = close.iloc[-1]

        res = levels["resistance"]
        sup = levels["support"]
        range_size = levels["range"]

        # Fiyat seviyelere ne kadar yakın?
        near_res = abs(current - res) / range_size < self.touch_threshold
        near_sup = abs(current - sup) / range_size < self.touch_threshold

        if near_sup and current > close.iloc[-2]:
            signal = "BOUNCE_SUPPORT"
            desc = f"Fiyat destek {sup:.2f}'ten sekme gösterdi. Long fırsatı."
        elif near_res and current < close.iloc[-2]:
            signal = "REJECT_RESISTANCE"
            desc = f"Fiyat direnç {res:.2f}'ten red yedi. Short fırsatı."
        elif near_sup:
            signal = "NEAR_SUPPORT"
            desc = f"Fiyat destek {sup:.2f}'e yakın."
        elif near_res:
            signal = "NEAR_RESISTANCE"
            desc = f"Fiyat direnç {res:.2f}'e yakın."
        else:
            signal = "IN_RANGE"
            desc = f"Fiyat range içinde. Destek: {sup:.2f}, Direnç: {res:.2f}."

        return {
            "signal": signal,
            "support": round(sup, 2),
            "resistance": round(res, 2),
            "current": round(float(current), 2),
            "range_pct": f"{(current - sup) / range_size:.1%}",
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(RangeTradingSR().run(high, low, close))
