"""
heikin_ashi.py
Heikin Ashi Mumları: Trend yönü ve gücü tespiti.
"""
import pandas as pd
import numpy as np
from typing import Dict

class HeikinAshi:
    def __init__(self):
        pass

    def calculate(self, open_p: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"open": open_p, "high": high, "low": low, "close": close})

        ha_close = (open_p + high + low + close) / 4
        ha_open = pd.Series(index=df.index, dtype=float)
        ha_open.iloc[0] = (open_p.iloc[0] + close.iloc[0]) / 2

        for i in range(1, len(df)):
            ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2

        ha_high = pd.concat([high, ha_open, ha_close], axis=1).max(axis=1)
        ha_low = pd.concat([low, ha_open, ha_close], axis=1).min(axis=1)

        df["ha_open"] = ha_open
        df["ha_high"] = ha_high
        df["ha_low"] = ha_low
        df["ha_close"] = ha_close
        df["ha_body"] = ha_close - ha_open
        df["ha_trend"] = np.where(ha_close > ha_open, 1, -1)

        return df

    def generate_signal(self, open_p: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(open_p, high, low, close)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        body = latest["ha_body"]
        trend = latest["ha_trend"]
        prev_trend = prev["ha_trend"]

        # Upper/lower shadows
        upper_shadow = latest["ha_high"] - max(latest["ha_open"], latest["ha_close"])
        lower_shadow = min(latest["ha_open"], latest["ha_close"]) - latest["ha_low"]

        if trend == 1 and prev_trend == -1:
            signal = "BUY"
            desc = "Heikin Ashi bullish reversal."
        elif trend == -1 and prev_trend == 1:
            signal = "SELL"
            desc = "Heikin Ashi bearish reversal."
        elif trend == 1 and upper_shadow < abs(body) * 0.1:
            signal = "STRONG_BUY"
            desc = "Güçlü bullish Heikin Ashi. Üst gölge yok."
        elif trend == -1 and lower_shadow < abs(body) * 0.1:
            signal = "STRONG_SELL"
            desc = "Güçlü bearish Heikin Ashi. Alt gölge yok."
        elif trend == 1:
            signal = "HOLD_LONG"
            desc = "Heikin Ashi bullish."
        else:
            signal = "HOLD_SHORT"
            desc = "Heikin Ashi bearish."

        return {
            "signal": signal,
            "ha_open": round(float(latest["ha_open"]), 2),
            "ha_close": round(float(latest["ha_close"]), 2),
            "body": round(float(body), 2),
            "trend": "UP" if trend == 1 else "DOWN",
            "description": desc
        }

    def run(self, open_p: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(open_p, high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    open_p = close.shift(1).fillna(100)
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(HeikinAshi().run(open_p, high, low, close))
