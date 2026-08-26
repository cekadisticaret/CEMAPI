"""
vwap.py
Volume Weighted Average Price (VWAP): Hacim ağırlıklı ortalama fiyat.
"""
import pandas as pd
import numpy as np
from typing import Dict

class VWAPIndicator:
    def __init__(self, anchor: str = "D"):
        """
        anchor: "D" (günlük), "W" (haftalık), "M" (aylık) reset
        """
        self.anchor = anchor

    def calculate(self, prices: pd.Series, volumes: pd.Series, timestamps: pd.DatetimeIndex = None) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices, "volume": volumes})
        if timestamps is not None:
            df.index = timestamps

        # Günlük gruplama ile VWAP
        df["tp"] = df["price"]  # Typical price = close (basit versiyon)
        df["pv"] = df["tp"] * df["volume"]

        if self.anchor == "D":
            df["cum_pv"] = df.groupby(df.index.date)["pv"].cumsum()
            df["cum_vol"] = df.groupby(df.index.date)["volume"].cumsum()
        else:
            df["cum_pv"] = df["pv"].cumsum()
            df["cum_vol"] = df["volume"].cumsum()

        df["vwap"] = df["cum_pv"] / df["cum_vol"]
        df["deviation"] = (df["price"] - df["vwap"]) / df["vwap"]

        return df

    def generate_signal(self, prices: pd.Series, volumes: pd.Series, timestamps: pd.DatetimeIndex = None) -> Dict:
        df = self.calculate(prices, volumes, timestamps)
        latest = df.iloc[-1]

        dev = latest["deviation"]
        price = latest["price"]
        vwap = latest["vwap"]

        if dev > 0.02:
            signal = "OVERBOUGHT"
            desc = f"Fiyat VWAP üzerinde %{dev*100:.2f}. Aşırı alım."
        elif dev < -0.02:
            signal = "OVERSOLD"
            desc = f"Fiyat VWAP altında %{abs(dev)*100:.2f}. Aşırı satım."
        elif price > vwap:
            signal = "BULLISH"
            desc = "Fiyat VWAP üzerinde. Bullish bias."
        else:
            signal = "BEARISH"
            desc = "Fiyat VWAP altında. Bearish bias."

        return {
            "signal": signal,
            "vwap": round(float(vwap), 2),
            "price": round(float(price), 2),
            "deviation": f"{dev:.2%}",
            "description": desc
        }

    def run(self, prices: pd.Series, volumes: pd.Series, timestamps: pd.DatetimeIndex = None) -> Dict:
        return self.generate_signal(prices, volumes, timestamps)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    volumes = pd.Series(np.random.randint(1000, 10000, 100))
    print(VWAPIndicator().run(prices, volumes))
