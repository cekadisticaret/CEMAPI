"""
squeeze_momentum.py
Squeeze Momentum: Bollinger Bands + Keltner Channel squeeze + momentum.
"""
import pandas as pd
import numpy as np
from typing import Dict

class SqueezeMomentum:
    def __init__(self, bb_period: int = 20, bb_mult: float = 2.0, 
                 kc_period: int = 20, kc_mult: float = 1.5, mom_period: int = 12):
        self.bb_period = bb_period
        self.bb_mult = bb_mult
        self.kc_period = kc_period
        self.kc_mult = kc_mult
        self.mom_period = mom_period

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # Bollinger Bands
        df["sma"] = close.rolling(self.bb_period).mean()
        df["bb_std"] = close.rolling(self.bb_period).std()
        df["bb_upper"] = df["sma"] + self.bb_mult * df["bb_std"]
        df["bb_lower"] = df["sma"] - self.bb_mult * df["bb_std"]

        # Keltner Channel
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr"] = tr.rolling(self.kc_period).mean()
        df["kc_upper"] = df["sma"] + self.kc_mult * df["atr"]
        df["kc_lower"] = df["sma"] - self.kc_mult * df["atr"]

        # Squeeze: BB içinde KC
        df["squeeze_on"] = (df["bb_lower"] > df["kc_lower"]) & (df["bb_upper"] < df["kc_upper"])

        # Momentum (Linear Regression slope proxy)
        df["momentum"] = close - close.shift(self.mom_period)

        return df

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        squeeze = latest["squeeze_on"]
        prev_squeeze = prev["squeeze_on"]
        mom = latest["momentum"]

        if prev_squeeze and not squeeze and mom > 0:
            signal = "BUY"
            desc = "Squeeze patladı + momentum pozitif. Bullish breakout."
        elif prev_squeeze and not squeeze and mom < 0:
            signal = "SELL"
            desc = "Squeeze patladı + momentum negatif. Bearish breakout."
        elif squeeze:
            signal = "SQUEEZE"
            desc = "Squeeze aktif. Volatilite patlaması beklenebilir."
        elif mom > 0:
            signal = "HOLD_LONG"
            desc = f"Momentum pozitif ({mom:.2f})."
        else:
            signal = "HOLD_SHORT"
            desc = f"Momentum negatif ({mom:.2f})."

        return {
            "signal": signal,
            "squeeze_on": bool(squeeze),
            "momentum": round(float(mom), 2),
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(SqueezeMomentum().run(high, low, close))
