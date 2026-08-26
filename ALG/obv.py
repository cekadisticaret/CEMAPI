"""
obv.py
On Balance Volume (OBV): Hacim akışı momentum göstergesi.
"""
import pandas as pd
import numpy as np
from typing import Dict

class OBVIndicator:
    def __init__(self, ma_period: int = 20):
        self.ma_period = ma_period

    def calculate(self, prices: pd.Series, volumes: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices, "volume": volumes})
        df["price_change"] = df["price"].diff()

        # OBV
        obv = [0]
        for i in range(1, len(df)):
            if df["price_change"].iloc[i] > 0:
                obv.append(obv[-1] + df["volume"].iloc[i])
            elif df["price_change"].iloc[i] < 0:
                obv.append(obv[-1] - df["volume"].iloc[i])
            else:
                obv.append(obv[-1])

        df["obv"] = obv
        df["obv_ma"] = df["obv"].rolling(window=self.ma_period).mean()
        df["obv_slope"] = df["obv"].diff()
        return df

    def generate_signal(self, prices: pd.Series, volumes: pd.Series) -> Dict:
        df = self.calculate(prices, volumes)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        obv = latest["obv"]
        obv_ma = latest["obv_ma"]
        slope = latest["obv_slope"]

        if slope > 0 and prev["obv_slope"] <= 0:
            signal = "BUY"
            desc = "OBV momentum yukarı döndü. Hacim girişi."
        elif slope < 0 and prev["obv_slope"] >= 0:
            signal = "SELL"
            desc = "OBV momentum aşağı döndü. Hacim çıkışı."
        elif obv > obv_ma and slope > 0:
            signal = "HOLD_LONG"
            desc = "OBV MA üzerinde ve yükseliyor."
        elif obv < obv_ma and slope < 0:
            signal = "HOLD_SHORT"
            desc = "OBV MA altında ve düşüyor."
        else:
            signal = "NEUTRAL"
            desc = "OBV kararsız."

        return {
            "signal": signal,
            "obv": int(obv),
            "obv_ma": int(obv_ma) if not pd.isna(obv_ma) else None,
            "slope": int(slope) if not pd.isna(slope) else None,
            "description": desc
        }

    def run(self, prices: pd.Series, volumes: pd.Series) -> Dict:
        return self.generate_signal(prices, volumes)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    volumes = pd.Series(np.random.randint(1000, 10000, 100))
    print(OBVIndicator().run(prices, volumes))
