"""
cci.py
Commodity Channel Index (CCI): Fiyatın istatistiksel ortalamadan sapması.
"""
import pandas as pd
import numpy as np
from typing import Dict

class CCIIndicator:
    def __init__(self, period: int = 20, overbought: float = 100, oversold: float = -100):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        tp = (high + low + close) / 3
        sma_tp = tp.rolling(window=self.period).mean()
        mean_dev = tp.rolling(window=self.period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        cci = (tp - sma_tp) / (0.015 * mean_dev)
        return cci

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        cci = self.calculate(high, low, close)
        latest = cci.iloc[-1]
        prev = cci.iloc[-2] if len(cci) > 1 else latest

        if pd.isna(latest):
            return {"signal": "NO_DATA"}

        if prev < self.oversold and latest > self.oversold:
            signal = "BUY"
            desc = f"CCI {latest:.1f}. Oversold bölgeden yukarı çıktı."
        elif prev > self.overbought and latest < self.overbought:
            signal = "SELL"
            desc = f"CCI {latest:.1f}. Overbought bölgeden aşağı indi."
        elif latest > self.overbought:
            signal = "OVERBOUGHT"
            desc = f"CCI {latest:.1f}. Aşırı alım."
        elif latest < self.oversold:
            signal = "OVERSOLD"
            desc = f"CCI {latest:.1f}. Aşırı satım."
        else:
            signal = "NEUTRAL"
            desc = f"CCI {latest:.1f}. Tarafsız."

        return {
            "signal": signal,
            "cci": round(float(latest), 2),
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(CCIIndicator().run(high, low, close))
