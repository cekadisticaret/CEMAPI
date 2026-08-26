"""
money_flow_index.py
Money Flow Index (MFI): Hacim ağırlıklı RSI benzeri gösterge.
"""
import pandas as pd
import numpy as np
from typing import Dict

class MoneyFlowIndex:
    def __init__(self, period: int = 14, overbought: float = 80, oversold: float = 20):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        typical_price = (high + low + close) / 3
        raw_money_flow = typical_price * volume

        price_change = typical_price.diff()
        positive_flow = raw_money_flow.where(price_change > 0, 0)
        negative_flow = raw_money_flow.where(price_change < 0, 0)

        positive_sum = positive_flow.rolling(window=self.period).sum()
        negative_sum = negative_flow.rolling(window=self.period).sum()

        money_ratio = positive_sum / negative_sum
        mfi = 100 - (100 / (1 + money_ratio))
        return mfi

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> Dict:
        mfi = self.calculate(high, low, close, volume)
        latest = mfi.iloc[-1]
        prev = mfi.iloc[-2] if len(mfi) > 1 else latest

        if pd.isna(latest):
            return {"signal": "NO_DATA"}

        if latest < self.oversold:
            signal = "OVERSOLD"
            desc = f"MFI {latest:.1f}. Aşırı satım."
        elif latest > self.overbought:
            signal = "OVERBOUGHT"
            desc = f"MFI {latest:.1f}. Aşırı alım."
        elif prev < self.oversold and latest > prev:
            signal = "BUY"
            desc = f"MFI oversold bölgeden dönüyor ({latest:.1f})."
        elif prev > self.overbought and latest < prev:
            signal = "SELL"
            desc = f"MFI overbought bölgeden dönüyor ({latest:.1f})."
        else:
            signal = "NEUTRAL"
            desc = f"MFI {latest:.1f}. Tarafsız."

        return {
            "signal": signal,
            "mfi": round(float(latest), 2),
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> Dict:
        return self.generate_signal(high, low, close, volume)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    volume = pd.Series(np.random.randint(1000, 10000, 100))
    print(MoneyFlowIndex().run(high, low, close, volume))
