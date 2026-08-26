"""
stochastic_rsi_14_kd.py
Stochastic RSI (14) K/D Cross - Alternatif implementasyon.
"""
import pandas as pd
import numpy as np
from typing import Dict

class StochasticRSI14KD:
    def __init__(self, rsi_period: int = 14, k_smooth: int = 3, d_smooth: int = 3):
        self.rsi_period = rsi_period
        self.k_smooth = k_smooth
        self.d_smooth = d_smooth

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(self.rsi_period).mean()
        avg_loss = loss.rolling(self.rsi_period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        rsi_min = rsi.rolling(self.rsi_period).min()
        rsi_max = rsi.rolling(self.rsi_period).max()
        stoch = 100 * (rsi - rsi_min) / (rsi_max - rsi_min)

        k = stoch.rolling(self.k_smooth).mean()
        d = k.rolling(self.d_smooth).mean()

        return pd.DataFrame({"k": k, "d": d, "price": prices})

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        k, d = latest["k"], latest["d"]

        if prev["k"] < prev["d"] and k > d:
            signal = "BUY"
            desc = f"K ({k:.1f}) D'yi ({d:.1f}) yukarı kesti."
        elif prev["k"] > prev["d"] and k < d:
            signal = "SELL"
            desc = f"K ({k:.1f}) D'yi ({d:.1f}) aşağı kesti."
        elif k > 80:
            signal = "OVERBOUGHT"
            desc = f"K={k:.1f}. Aşırı alım."
        elif k < 20:
            signal = "OVERSOLD"
            desc = f"K={k:.1f}. Aşırı satım."
        else:
            signal = "NEUTRAL"
            desc = f"K={k:.1f}, D={d:.1f}."

        return {
            "signal": signal,
            "k": round(float(k), 2),
            "d": round(float(d), 2),
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(StochasticRSI14KD().run(prices))
