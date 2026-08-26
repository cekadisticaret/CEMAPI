"""
supertrend.py
Supertrend: ATR bazlı trend takip göstergesi.
"""
import pandas as pd
import numpy as np
from typing import Dict

class Supertrend:
    def __init__(self, period: int = 10, multiplier: float = 3.0):
        self.period = period
        self.multiplier = multiplier

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # ATR
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift(1)).abs()
        tr3 = (df["low"] - df["close"].shift(1)).abs()
        df["tr"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr"] = df["tr"].rolling(window=self.period).mean()

        # Basic Upper/Lower Bands
        df["basic_ub"] = (df["high"] + df["low"]) / 2 + self.multiplier * df["atr"]
        df["basic_lb"] = (df["high"] + df["low"]) / 2 - self.multiplier * df["atr"]

        # Final Upper/Lower Bands
        df["final_ub"] = df["basic_ub"].copy()
        df["final_lb"] = df["basic_lb"].copy()

        for i in range(1, len(df)):
            if df["close"].iloc[i-1] > df["final_ub"].iloc[i-1]:
                df.loc[df.index[i], "final_ub"] = max(df["basic_ub"].iloc[i], df["final_ub"].iloc[i-1])
            if df["close"].iloc[i-1] < df["final_lb"].iloc[i-1]:
                df.loc[df.index[i], "final_lb"] = min(df["basic_lb"].iloc[i], df["final_lb"].iloc[i-1])

        # Supertrend
        df["supertrend"] = np.nan
        for i in range(1, len(df)):
            if df["close"].iloc[i] > df["final_ub"].iloc[i-1]:
                df.loc[df.index[i], "supertrend"] = df["final_lb"].iloc[i]
            elif df["close"].iloc[i] < df["final_lb"].iloc[i-1]:
                df.loc[df.index[i], "supertrend"] = df["final_ub"].iloc[i]
            else:
                df.loc[df.index[i], "supertrend"] = df["supertrend"].iloc[i-1]

        df["direction"] = np.where(df["close"] > df["supertrend"], 1, -1)
        return df

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        if prev["direction"] == -1 and latest["direction"] == 1:
            signal = "BUY"
            desc = "Supertrend bullish flip. Fiyat Supertrend üzerine çıktı."
        elif prev["direction"] == 1 and latest["direction"] == -1:
            signal = "SELL"
            desc = "Supertrend bearish flip. Fiyat Supertrend altına düştü."
        elif latest["direction"] == 1:
            signal = "HOLD_LONG"
            desc = "Supertrend bullish. Trend yukarı."
        else:
            signal = "HOLD_SHORT"
            desc = "Supertrend bearish. Trend aşağı."

        return {
            "signal": signal,
            "supertrend": round(float(latest["supertrend"]), 2),
            "close": round(float(latest["close"]), 2),
            "direction": "UP" if latest["direction"] == 1 else "DOWN",
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(Supertrend().run(high, low, close))
