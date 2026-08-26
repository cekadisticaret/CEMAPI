"""
hull_ma.py
Hull Moving Average: Düşük gecikmeli, düzgün hareketli ortalama.
"""
import pandas as pd
import numpy as np
from typing import Dict

class HullMA:
    def __init__(self, period: int = 16):
        self.period = period

    def wma(self, prices: pd.Series, period: int) -> pd.Series:
        """Weighted Moving Average."""
        weights = np.arange(1, period + 1)
        return prices.rolling(window=period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

    def calculate(self, prices: pd.Series) -> pd.Series:
        half_period = self.period // 2
        sqrt_period = int(np.sqrt(self.period))

        wma_half = self.wma(prices, half_period)
        wma_full = self.wma(prices, self.period)

        raw_hma = 2 * wma_half - wma_full
        hma = self.wma(raw_hma, sqrt_period)
        return hma

    def generate_signal(self, prices: pd.Series) -> Dict:
        hma = self.calculate(prices)
        latest_hma = hma.iloc[-1]
        prev_hma = hma.iloc[-2] if len(hma) > 1 else latest_hma
        latest_price = prices.iloc[-1]

        if latest_price > latest_hma and prev_hma >= hma.iloc[-2] if len(hma) > 2 else True:
            signal = "BUY"
            desc = "Fiyat HMA üzerinde ve HMA yükseliyor."
        elif latest_price < latest_hma:
            signal = "SELL"
            desc = "Fiyat HMA altında."
        else:
            signal = "NEUTRAL"
            desc = "HMA yakınında."

        return {
            "signal": signal,
            "hma": round(float(latest_hma), 2),
            "price": round(float(latest_price), 2),
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(HullMA().run(prices))
