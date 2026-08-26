"""
atr_breakout.py
ATR Breakout: ATR bazlı volatilite patlaması ve breakout tespiti.
"""
import pandas as pd
import numpy as np
from typing import Dict

class ATRBreakout:
    def __init__(self, atr_period: int = 14, multiplier: float = 1.5, lookback: int = 20):
        self.atr_period = atr_period
        self.multiplier = multiplier
        self.lookback = lookback

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean()
        return atr

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})
        df["atr"] = self.calculate_atr(high, low, close)
        df["upper_band"] = close.rolling(window=self.lookback).max().shift(1)
        df["lower_band"] = close.rolling(window=self.lookback).min().shift(1)
        df["breakout_threshold"] = df["atr"] * self.multiplier
        return df

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        price = latest["close"]
        upper = latest["upper_band"]
        lower = latest["lower_band"]
        atr = latest["atr"]

        if price > upper + self.multiplier * atr:
            signal = "BREAKOUT_UP"
            desc = f"Fiyat {self.lookback} periyodun en yükseğini + {self.multiplier}x ATR ile kırdı."
        elif price < lower - self.multiplier * atr:
            signal = "BREAKOUT_DOWN"
            desc = f"Fiyat {self.lookback} periyodun en düşüğünü - {self.multiplier}x ATR ile kırdı."
        elif price > upper:
            signal = "BUY"
            desc = f"Fiyat {self.lookback} periyodun en yükseğini kırdı."
        elif price < lower:
            signal = "SELL"
            desc = f"Fiyat {self.lookback} periyodun en düşüğünü kırdı."
        else:
            signal = "NEUTRAL"
            desc = "Breakout yok. Range içinde."

        return {
            "signal": signal,
            "price": round(float(price), 2),
            "upper_band": round(float(upper), 2),
            "lower_band": round(float(lower), 2),
            "atr": round(float(atr), 2),
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(ATRBreakout().run(high, low, close))
