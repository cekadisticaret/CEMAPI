"""
tema_crossover.py
Triple EMA (TEMA) Crossover: Üç kat üssel hareketli ortalama.
"""
import pandas as pd
import numpy as np
from typing import Dict

class TEMACrossover:
    def __init__(self, fast: int = 12, slow: int = 26):
        self.fast = fast
        self.slow = slow

    def tema(self, prices: pd.Series, period: int) -> pd.Series:
        ema1 = prices.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()
        tema = 3 * ema1 - 3 * ema2 + ema3
        return tema

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices})
        df["tema_fast"] = self.tema(prices, self.fast)
        df["tema_slow"] = self.tema(prices, self.slow)
        df["cross"] = np.where(df["tema_fast"] > df["tema_slow"], 1, -1)
        df["cross_signal"] = df["cross"].diff()
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        if prev["cross_signal"] == -2:  # bearish cross
            signal = "SELL"
            desc = f"TEMA{self.fast} TEMA{self.slow}'yi aşağı kesti."
        elif prev["cross_signal"] == 2:  # bullish cross
            signal = "BUY"
            desc = f"TEMA{self.fast} TEMA{self.slow}'yi yukarı kesti."
        elif latest["tema_fast"] > latest["tema_slow"]:
            signal = "HOLD_LONG"
            desc = "TEMA fast slow üzerinde."
        else:
            signal = "HOLD_SHORT"
            desc = "TEMA fast slow altında."

        return {
            "signal": signal,
            "tema_fast": round(float(latest["tema_fast"]), 2),
            "tema_slow": round(float(latest["tema_slow"]), 2),
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(TEMACrossover().run(prices))
