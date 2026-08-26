"""
rsi_divergence.py
RSI + Fiyat Diverjansı: Bullish/Bearish divergence tespiti.
"""
import pandas as pd
import numpy as np
from typing import Dict

class RSIDivergence:
    def __init__(self, period: int = 14, lookback: int = 20):
        self.period = period
        self.lookback = lookback

    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(window=self.period).mean()
        avg_loss = loss.rolling(window=self.period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def find_divergence(self, prices: pd.Series, rsi: pd.Series) -> str:
        if len(prices) < self.lookback * 2:
            return "NO_DATA"

        recent_prices = prices.iloc[-self.lookback:]
        recent_rsi = rsi.iloc[-self.lookback:]
        earlier_prices = prices.iloc[-self.lookback*2:-self.lookback]
        earlier_rsi = rsi.iloc[-self.lookback*2:-self.lookback]

        if len(earlier_prices) == 0:
            return "NO_DATA"

        # Bullish: price lower low, RSI higher low
        if recent_prices.min() < earlier_prices.min() and recent_rsi.min() > earlier_rsi.min():
            return "BULLISH_DIVERGENCE"
        # Bearish: price higher high, RSI lower high
        if recent_prices.max() > earlier_prices.max() and recent_rsi.max() < earlier_rsi.max():
            return "BEARISH_DIVERGENCE"

        return "NO_DIVERGENCE"

    def generate_signal(self, prices: pd.Series) -> Dict:
        rsi = self.calculate_rsi(prices)
        latest_rsi = rsi.iloc[-1]
        div = self.find_divergence(prices, rsi)

        if div == "BULLISH_DIVERGENCE":
            signal = "BUY"
            desc = "Bullish RSI divergence. Fiyat düşerken RSI yükseliyor."
        elif div == "BEARISH_DIVERGENCE":
            signal = "SELL"
            desc = "Bearish RSI divergence. Fiyat yükselirken RSI düşüyor."
        elif latest_rsi < 30:
            signal = "OVERSOLD"
            desc = f"RSI {latest_rsi:.1f}. Aşırı satım bölgesi."
        elif latest_rsi > 70:
            signal = "OVERBOUGHT"
            desc = f"RSI {latest_rsi:.1f}. Aşırı alım bölgesi."
        else:
            signal = "NEUTRAL"
            desc = f"RSI {latest_rsi:.1f}. Tarafsız bölge."

        return {
            "signal": signal,
            "rsi": round(float(latest_rsi), 2),
            "divergence": div,
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(RSIDivergence().run(prices))
