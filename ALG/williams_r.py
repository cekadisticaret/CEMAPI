"""
williams_r.py
Williams %R: Aşırı alım/satım osilatörü.
"""
import pandas as pd
import numpy as np
from typing import Dict

class WilliamsR:
    def __init__(self, period: int = 14, overbought: float = -20, oversold: float = -80):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        highest_high = high.rolling(window=self.period).max()
        lowest_low = low.rolling(window=self.period).min()
        wr = -100 * (highest_high - close) / (highest_high - lowest_low)
        return wr

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        wr = self.calculate(high, low, close)
        latest = wr.iloc[-1]
        prev = wr.iloc[-2] if len(wr) > 1 else latest

        if pd.isna(latest):
            return {"signal": "NO_DATA"}

        if latest > self.overbought and prev <= self.overbought:
            signal = "SELL"
            desc = f"Williams %R {latest:.1f}. Overbought bölgeden çıktı."
        elif latest < self.oversold and prev >= self.oversold:
            signal = "BUY"
            desc = f"Williams %R {latest:.1f}. Oversold bölgeden çıktı."
        elif latest > self.overbought:
            signal = "OVERBOUGHT"
            desc = f"Williams %R {latest:.1f}. Aşırı alım."
        elif latest < self.oversold:
            signal = "OVERSOLD"
            desc = f"Williams %R {latest:.1f}. Aşırı satım."
        else:
            signal = "NEUTRAL"
            desc = f"Williams %R {latest:.1f}. Tarafsız."

        return {
            "signal": signal,
            "williams_r": round(float(latest), 2),
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(WilliamsR().run(high, low, close))
