"""
bollinger_bands.py
Bollinger Bands + Squeeze tespiti.
"""
import pandas as pd
import numpy as np
from typing import Dict

class BollingerBands:
    def __init__(self, period: int = 20, std_dev: float = 2.0, squeeze_lookback: int = 120):
        self.period = period
        self.std_dev = std_dev
        self.squeeze_lookback = squeeze_lookback

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices})
        df["sma"] = prices.rolling(window=self.period).mean()
        df["std"] = prices.rolling(window=self.period).std()
        df["upper"] = df["sma"] + self.std_dev * df["std"]
        df["lower"] = df["sma"] - self.std_dev * df["std"]
        df["bandwidth"] = (df["upper"] - df["lower"]) / df["sma"]
        df["%b"] = (prices - df["lower"]) / (df["upper"] - df["lower"])

        # Squeeze: bandwidth son 120 periyodun en düşüğündeyse
        df["squeeze"] = df["bandwidth"] <= df["bandwidth"].rolling(window=self.squeeze_lookback).min()
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        pct_b = latest["%b"]
        is_squeeze = latest["squeeze"]

        if is_squeeze and not prev["squeeze"]:
            signal = "SQUEEZE_ON"
            desc = "Bollinger Squeeze aktif. Volatilite patlaması beklenebilir."
        elif pct_b > 1.0:
            signal = "OVERBOUGHT"
            desc = f"Fiyat üst band üzerinde (%B={pct_b:.2f}). Aşırı alım."
        elif pct_b < 0.0:
            signal = "OVERSOLD"
            desc = f"Fiyat alt band altında (%B={pct_b:.2f}). Aşırı satım."
        elif pct_b > 0.8:
            signal = "HOLD_SHORT"
            desc = f"Fiyat üst banda yakın (%B={pct_b:.2f})."
        elif pct_b < 0.2:
            signal = "HOLD_LONG"
            desc = f"Fiyat alt banda yakın (%B={pct_b:.2f})."
        else:
            signal = "NEUTRAL"
            desc = f"Fiyat band ortasında (%B={pct_b:.2f})."

        return {
            "signal": signal,
            "upper": round(float(latest["upper"]), 2),
            "lower": round(float(latest["lower"]), 2),
            "sma": round(float(latest["sma"]), 2),
            "pct_b": round(float(pct_b), 3),
            "squeeze": bool(is_squeeze),
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(BollingerBands().run(prices))
