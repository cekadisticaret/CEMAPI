"""
schaff_trend_cycle.py
Schaff Trend Cycle (STC): MACD + Stochastic kombinasyonu.
"""
import pandas as pd
import numpy as np
from typing import Dict

class SchaffTrendCycle:
    def __init__(self, fast: int = 23, slow: int = 50, cycle: int = 10):
        self.fast = fast
        self.slow = slow
        self.cycle = cycle

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        ema_fast = prices.ewm(span=self.fast).mean()
        ema_slow = prices.ewm(span=self.slow).mean()
        macd = ema_fast - ema_slow

        # Stochastic of MACD
        lowest_macd = macd.rolling(self.cycle).min()
        highest_macd = macd.rolling(self.cycle).max()

        k = pd.Series(np.where(highest_macd != lowest_macd, 
                                100 * (macd - lowest_macd) / (highest_macd - lowest_macd), 
                                0), index=prices.index)

        d = k.ewm(span=self.cycle).mean()

        # STC
        stc = pd.Series(np.where(highest_macd != lowest_macd,
                                 100 * (k - k.rolling(self.cycle).min()) / (k.rolling(self.cycle).max() - k.rolling(self.cycle).min()),
                                 0), index=prices.index)

        df = pd.DataFrame({"stc": stc, "k": k, "d": d, "price": prices})
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        stc = latest["stc"]

        if prev["stc"] < 25 and stc > 25:
            signal = "BUY"
            desc = f"STC {stc:.1f}. 25 seviyesini yukarı kırdı."
        elif prev["stc"] > 75 and stc < 75:
            signal = "SELL"
            desc = f"STC {stc:.1f}. 75 seviyesini aşağı kırdı."
        elif stc < 25:
            signal = "OVERSOLD"
            desc = f"STC {stc:.1f}. Aşırı satım."
        elif stc > 75:
            signal = "OVERBOUGHT"
            desc = f"STC {stc:.1f}. Aşırı alım."
        else:
            signal = "NEUTRAL"
            desc = f"STC {stc:.1f}. Tarafsız."

        return {
            "signal": signal,
            "stc": round(float(stc), 2),
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(SchaffTrendCycle().run(prices))
