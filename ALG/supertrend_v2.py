"""
supertrend_v2.py
SuperTrend v2: Periyot 7, Çarpan 2.0 parametreleriyle optimize edilmiş.
"""
import pandas as pd
import numpy as np
from typing import Dict

class SuperTrendV2:
    def __init__(self, period: int = 7, multiplier: float = 2.0):
        self.period = period
        self.multiplier = multiplier

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        df["atr"] = self._atr(df)
        hl2 = (df["high"] + df["low"]) / 2
        df["upper"] = hl2 + self.multiplier * df["atr"]
        df["lower"] = hl2 - self.multiplier * df["atr"]

        df["supertrend"] = np.nan
        df["direction"] = 1

        for i in range(1, len(df)):
            if df["close"].iloc[i] > df["upper"].iloc[i-1]:
                df.loc[df.index[i], "direction"] = 1
            elif df["close"].iloc[i] < df["lower"].iloc[i-1]:
                df.loc[df.index[i], "direction"] = -1
            else:
                df.loc[df.index[i], "direction"] = df["direction"].iloc[i-1]

            if df["direction"].iloc[i] == 1:
                df.loc[df.index[i], "supertrend"] = max(df["lower"].iloc[i], df["supertrend"].iloc[i-1] if not pd.isna(df["supertrend"].iloc[i-1]) else df["lower"].iloc[i])
            else:
                df.loc[df.index[i], "supertrend"] = min(df["upper"].iloc[i], df["supertrend"].iloc[i-1] if not pd.isna(df["supertrend"].iloc[i-1]) else df["upper"].iloc[i])

        return df

    def _atr(self, df: pd.DataFrame) -> pd.Series:
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift(1)).abs()
        tr3 = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=self.period).mean()

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        if prev["direction"] == -1 and latest["direction"] == 1:
            signal = "BUY"
            desc = f"SuperTrend v2 ({self.period},{self.multiplier}) bullish flip."
        elif prev["direction"] == 1 and latest["direction"] == -1:
            signal = "SELL"
            desc = f"SuperTrend v2 ({self.period},{self.multiplier}) bearish flip."
        elif latest["direction"] == 1:
            signal = "HOLD_LONG"
            desc = "SuperTrend v2 bullish."
        else:
            signal = "HOLD_SHORT"
            desc = "SuperTrend v2 bearish."

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
    print(SuperTrendV2().run(high, low, close))
