"""
bollinger_squeeze.py
Bollinger Bands + Squeeze: Daralan band tespiti.
"""
import pandas as pd
import numpy as np
from typing import Dict

class BollingerSqueeze:
    def __init__(self, period: int = 20, std_dev: float = 2.0, squeeze_period: int = 120):
        self.period = period
        self.std_dev = std_dev
        self.squeeze_period = squeeze_period

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices})
        df["sma"] = prices.rolling(self.period).mean()
        df["std"] = prices.rolling(self.period).std()
        df["upper"] = df["sma"] + self.std_dev * df["std"]
        df["lower"] = df["sma"] - self.std_dev * df["std"]
        df["bandwidth"] = (df["upper"] - df["lower"]) / df["sma"]
        df["squeeze"] = df["bandwidth"] <= df["bandwidth"].rolling(self.squeeze_period).min()
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        if not prev["squeeze"] and latest["squeeze"]:
            signal = "SQUEEZE_START"
            desc = "Bollinger Squeeze başladı. Volatilite patlaması yakın."
        elif prev["squeeze"] and not latest["squeeze"]:
            signal = "SQUEEZE_END"
            desc = "Squeeze bitti. Breakout yaşanıyor."
        elif latest["squeeze"]:
            signal = "SQUEEZE"
            desc = "Squeeze devam. Bekle."
        else:
            signal = "NO_SQUEEZE"
            desc = "Normal volatilite."

        return {
            "signal": signal,
            "bandwidth": f"{latest['bandwidth']:.4f}" if not pd.isna(latest["bandwidth"]) else None,
            "squeeze": bool(latest["squeeze"]),
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(BollingerSqueeze().run(prices))
