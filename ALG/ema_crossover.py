"""
ema_crossover.py
EMA Crossover: Hızlı ve yavaş üssel hareketli ortalama kesişimi.
"""
import pandas as pd
import numpy as np
from typing import Dict

class EMACrossover:
    def __init__(self, fast: int = 12, slow: int = 26):
        self.fast = fast
        self.slow = slow

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices})
        df["ema_fast"] = prices.ewm(span=self.fast, adjust=False).mean()
        df["ema_slow"] = prices.ewm(span=self.slow, adjust=False).mean()
        df["signal_line"] = np.where(df["ema_fast"] > df["ema_slow"], 1, -1)
        df["cross"] = df["signal_line"].diff()
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        if latest["cross"] == 2:  # -1 -> 1 (bullish cross)
            signal = "BUY"
            desc = f"EMA{self.fast} EMA{self.slow}'yi yukarı kesti. Bullish cross."
        elif latest["cross"] == -2:  # 1 -> -1 (bearish cross)
            signal = "SELL"
            desc = f"EMA{self.fast} EMA{self.slow}'yi aşağı kesti. Bearish cross."
        elif latest["ema_fast"] > latest["ema_slow"]:
            signal = "HOLD_LONG"
            desc = f"EMA{self.fast} EMA{self.slow} üzerinde. Uptrend devam."
        else:
            signal = "HOLD_SHORT"
            desc = f"EMA{self.fast} EMA{self.slow} altında. Downtrend devam."

        return {
            "signal": signal,
            "ema_fast": round(float(latest["ema_fast"]), 2),
            "ema_slow": round(float(latest["ema_slow"]), 2),
            "description": desc,
            "price": round(float(latest["price"]), 2)
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(EMACrossover().run(prices))
