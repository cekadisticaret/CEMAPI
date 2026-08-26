"""
triple_ema.py
Triple EMA: 3 üssel hareketli ortalamanın kesişimi.
"""
import pandas as pd
import numpy as np
from typing import Dict

class TripleEMA:
    def __init__(self, short: int = 9, medium: int = 21, long: int = 50):
        self.short = short
        self.medium = medium
        self.long = long

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices})
        df["ema_short"] = prices.ewm(span=self.short, adjust=False).mean()
        df["ema_medium"] = prices.ewm(span=self.medium, adjust=False).mean()
        df["ema_long"] = prices.ewm(span=self.long, adjust=False).mean()

        # Sıralama
        df["alignment"] = np.where(
            (df["ema_short"] > df["ema_medium"]) & (df["ema_medium"] > df["ema_long"]), 1,
            np.where((df["ema_short"] < df["ema_medium"]) & (df["ema_medium"] < df["ema_long"]), -1, 0)
        )
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        alignment = latest["alignment"]
        prev_alignment = prev["alignment"]

        if prev_alignment != 1 and alignment == 1:
            signal = "BUY"
            desc = "3 EMA bullish alignment (short > medium > long)."
        elif prev_alignment != -1 and alignment == -1:
            signal = "SELL"
            desc = "3 EMA bearish alignment (short < medium < long)."
        elif alignment == 1:
            signal = "HOLD_LONG"
            desc = "Bullish EMA alignment devam."
        elif alignment == -1:
            signal = "HOLD_SHORT"
            desc = "Bearish EMA alignment devam."
        else:
            signal = "NEUTRAL"
            desc = "EMA'lar karışık. Trend yok."

        return {
            "signal": signal,
            "ema_short": round(float(latest["ema_short"]), 2),
            "ema_medium": round(float(latest["ema_medium"]), 2),
            "ema_long": round(float(latest["ema_long"]), 2),
            "alignment": "BULLISH" if alignment == 1 else "BEARISH" if alignment == -1 else "MIXED",
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(TripleEMA().run(prices))
