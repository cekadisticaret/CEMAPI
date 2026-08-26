"""
donchian_channel.py
Donchian Channel: Son N periyodun en yüksek/düşük değerleri.
"""
import pandas as pd
import numpy as np
from typing import Dict

class DonchianChannel:
    def __init__(self, period: int = 20):
        self.period = period

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})
        df["upper"] = high.rolling(window=self.period).max()
        df["lower"] = low.rolling(window=self.period).min()
        df["middle"] = (df["upper"] + df["lower"]) / 2
        return df

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        price = latest["close"]
        upper = latest["upper"]
        lower = latest["lower"]

        if price >= upper:
            signal = "BREAKOUT_UP"
            desc = f"Fiyat {self.period} periyodun en yükseğini kırdı."
        elif price <= lower:
            signal = "BREAKOUT_DOWN"
            desc = f"Fiyat {self.period} periyodun en düşüğünü kırdı."
        elif prev["close"] < prev["upper"] and price >= upper:
            signal = "BUY"
            desc = "Donchian üst kanal kırılımı."
        elif prev["close"] > prev["lower"] and price <= lower:
            signal = "SELL"
            desc = "Donchian alt kanal kırılımı."
        else:
            signal = "NEUTRAL"
            desc = "Donchian kanalı içinde."

        return {
            "signal": signal,
            "upper": round(float(upper), 2),
            "lower": round(float(lower), 2),
            "middle": round(float(latest["middle"]), 2),
            "price": round(float(price), 2),
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(DonchianChannel().run(high, low, close))
