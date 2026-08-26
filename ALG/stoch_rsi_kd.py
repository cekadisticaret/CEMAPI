"""
stoch_rsi_kd.py
Stochastic RSI K/D Cross: K ve D çizgilerinin kesişimi odaklı.
"""
import pandas as pd
import numpy as np
from typing import Dict

class StochRSIKD:
    def __init__(self, rsi_period: int = 14, stoch_period: int = 14, k_period: int = 3, d_period: int = 3):
        self.rsi_period = rsi_period
        self.stoch_period = stoch_period
        self.k_period = k_period
        self.d_period = d_period

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        rsi_min = rsi.rolling(window=self.stoch_period).min()
        rsi_max = rsi.rolling(window=self.stoch_period).max()
        stoch_rsi = 100 * (rsi - rsi_min) / (rsi_max - rsi_min)

        k = stoch_rsi.rolling(window=self.k_period).mean()
        d = k.rolling(window=self.d_period).mean()

        df = pd.DataFrame({"k": k, "d": d, "price": prices})
        df["cross"] = np.where(k > d, 1, -1)
        df["cross_signal"] = df["cross"].diff()
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        k = latest["k"]
        d = latest["d"]

        if prev["cross_signal"] == 2 and k < 30:  # K D'yi yukarı kesti, oversold
            signal = "BUY"
            desc = f"K D'yi yukarı kesti (K={k:.1f}, D={d:.1f}). Oversold bölgede."
        elif prev["cross_signal"] == -2 and k > 70:  # K D'yi aşağı kesti, overbought
            signal = "SELL"
            desc = f"K D'yi aşağı kesti (K={k:.1f}, D={d:.1f}). Overbought bölgede."
        elif k > d:
            signal = "HOLD_LONG"
            desc = f"K D üzerinde (K={k:.1f}, D={d:.1f})."
        else:
            signal = "HOLD_SHORT"
            desc = f"K D altında (K={k:.1f}, D={d:.1f})."

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
    print(StochRSIKD().run(prices))
