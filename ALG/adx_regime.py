"""
adx_regime.py
ADX Regime: ADX + DI+/DI- ile trend gücü ve yönü.
"""
import pandas as pd
import numpy as np
from typing import Dict

class ADXRegime:
    def __init__(self, period: int = 14, adx_threshold: float = 25.0):
        self.period = period
        self.adx_threshold = adx_threshold

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # True Range
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift(1)).abs()
        tr3 = (df["low"] - df["close"].shift(1)).abs()
        df["tr"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # +DM, -DM
        df["+dm"] = df["high"].diff()
        df["-dm"] = -df["low"].diff()
        df["+dm"] = np.where((df["+dm"] > df["-dm"]) & (df["+dm"] > 0), df["+dm"], 0)
        df["-dm"] = np.where((df["-dm"] > df["+dm"]) & (df["-dm"] > 0), df["-dm"], 0)

        # Smoothed
        atr = df["tr"].rolling(window=self.period).mean()
        plus_di = 100 * df["+dm"].rolling(window=self.period).mean() / atr
        minus_di = 100 * df["-dm"].rolling(window=self.period).mean() / atr

        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.rolling(window=self.period).mean()

        df["adx"] = adx
        df["+di"] = plus_di
        df["-di"] = minus_di
        return df

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]

        adx = latest["adx"]
        pdi = latest["+di"]
        mdi = latest["-di"]

        if pd.isna(adx):
            return {"signal": "NO_DATA"}

        if adx > self.adx_threshold and pdi > mdi:
            signal = "STRONG_TREND_UP"
            desc = f"ADX {adx:.1f}. Güçlü uptrend. DI+ > DI-."
        elif adx > self.adx_threshold and pdi < mdi:
            signal = "STRONG_TREND_DOWN"
            desc = f"ADX {adx:.1f}. Güçlü downtrend. DI- > DI+."
        elif adx < 20:
            signal = "NO_TREND"
            desc = f"ADX {adx:.1f}. Zayıf trend. Range piyasası."
        elif pdi > mdi:
            signal = "WEAK_UP"
            desc = f"ADX {adx:.1f}. Zayıf uptrend."
        else:
            signal = "WEAK_DOWN"
            desc = f"ADX {adx:.1f}. Zayıf downtrend."

        return {
            "signal": signal,
            "adx": round(float(adx), 2),
            "+di": round(float(pdi), 2),
            "-di": round(float(mdi), 2),
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(ADXRegime().run(high, low, close))
