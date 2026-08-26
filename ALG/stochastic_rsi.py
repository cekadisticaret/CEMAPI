"""
stochastic_rsi.py
Stochastic RSI: RSI'nin stochastic dönüşümü. K ve D çizgileri.
"""
import pandas as pd
import numpy as np
from typing import Dict

class StochasticRSI:
    def __init__(self, rsi_period: int = 14, stoch_period: int = 14, k_period: int = 3, d_period: int = 3):
        self.rsi_period = rsi_period
        self.stoch_period = stoch_period
        self.k_period = k_period
        self.d_period = d_period

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        # RSI
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Stochastic RSI
        rsi_min = rsi.rolling(window=self.stoch_period).min()
        rsi_max = rsi.rolling(window=self.stoch_period).max()
        stoch_rsi = 100 * (rsi - rsi_min) / (rsi_max - rsi_min)

        df = pd.DataFrame({"rsi": rsi, "stoch_rsi": stoch_rsi})
        df["k"] = stoch_rsi.rolling(window=self.k_period).mean()
        df["d"] = df["k"].rolling(window=self.d_period).mean()
        df["price"] = prices
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        k = latest["k"]
        d = latest["d"]

        if prev["k"] < prev["d"] and k > d and k < 20:
            signal = "BUY"
            desc = "StochRSI K D'yi yukarı kesti. Aşırı satım bölgesinde."
        elif prev["k"] > prev["d"] and k < d and k > 80:
            signal = "SELL"
            desc = "StochRSI K D'yi aşağı kesti. Aşırı alım bölgesinde."
        elif k < 20:
            signal = "OVERSOLD"
            desc = f"StochRSI K={k:.1f}. Aşırı satım."
        elif k > 80:
            signal = "OVERBOUGHT"
            desc = f"StochRSI K={k:.1f}. Aşırı alım."
        else:
            signal = "NEUTRAL"
            desc = f"StochRSI K={k:.1f}, D={d:.1f}. Tarafsız."

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
    print(StochasticRSI().run(prices))
