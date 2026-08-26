"""
mean_reversion_zscore.py
Z-Score Mean Reversion: Fiyatın hareketli ortalamasından sapmasını ölçer.
"""
import pandas as pd
import numpy as np
from typing import Dict

class MeanReversionZScore:
    def __init__(self, lookback: int = 20, entry_z: float = 2.0, exit_z: float = 0.5):
        self.lookback = lookback
        self.entry_z = entry_z
        self.exit_z = exit_z

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices})
        df["sma"] = prices.rolling(window=self.lookback).mean()
        df["std"] = prices.rolling(window=self.lookback).std()
        df["zscore"] = (prices - df["sma"]) / df["std"]
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        z = latest["zscore"]

        if pd.isna(z):
            return {"signal": "NO_DATA", "zscore": None}

        if z < -self.entry_z:
            signal = "BUY"
            desc = f"Z-Score {z:.2f}. Aşırı negatif sapma. Mean reversion long fırsatı."
        elif z > self.entry_z:
            signal = "SELL"
            desc = f"Z-Score {z:.2f}. Aşırı pozitif sapma. Mean reversion short fırsatı."
        elif abs(z) < self.exit_z:
            signal = "EXIT"
            desc = f"Z-Score {z:.2f}. Ortalamaya dönüş tamamlandı. Pozisyon kapat."
        else:
            signal = "HOLD"
            desc = f"Z-Score {z:.2f}. Beklemede."

        return {
            "signal": signal,
            "zscore": round(float(z), 3),
            "sma": round(float(latest["sma"]), 2),
            "price": round(float(latest["price"]), 2),
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(MeanReversionZScore().run(prices))
