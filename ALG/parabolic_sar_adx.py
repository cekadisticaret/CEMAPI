"""
parabolic_sar_adx.py
Parabolic SAR + ADX filtreli trend takip.
"""
import pandas as pd
import numpy as np
from typing import Dict

class ParabolicSARADX:
    def __init__(self, af_start: float = 0.02, af_max: float = 0.2, adx_period: int = 14, adx_threshold: float = 25):
        self.af_start = af_start
        self.af_max = af_max
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold

    def calculate_sar(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Parabolic SAR hesaplar."""
        sar = pd.Series(index=close.index, dtype=float)
        trend = pd.Series(index=close.index, dtype=int)

        # İlk değerler
        trend.iloc[0] = 1  # 1 = up, -1 = down
        sar.iloc[0] = low.iloc[0]
        ep = high.iloc[0]  # Extreme point
        af = self.af_start

        for i in range(1, len(close)):
            prev_trend = trend.iloc[i-1]
            prev_sar = sar.iloc[i-1]

            if prev_trend == 1:  # Uptrend
                sar.iloc[i] = prev_sar + af * (ep - prev_sar)
                if low.iloc[i] < sar.iloc[i]:
                    trend.iloc[i] = -1
                    sar.iloc[i] = ep
                    ep = low.iloc[i]
                    af = self.af_start
                else:
                    trend.iloc[i] = 1
                    if high.iloc[i] > ep:
                        ep = high.iloc[i]
                        af = min(af + self.af_start, self.af_max)
            else:  # Downtrend
                sar.iloc[i] = prev_sar + af * (ep - prev_sar)
                if high.iloc[i] > sar.iloc[i]:
                    trend.iloc[i] = 1
                    sar.iloc[i] = ep
                    ep = high.iloc[i]
                    af = self.af_start
                else:
                    trend.iloc[i] = -1
                    if low.iloc[i] < ep:
                        ep = low.iloc[i]
                        af = min(af + self.af_start, self.af_max)

        return sar, trend

    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Basit ADX hesaplaması."""
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.adx_period).mean()

        plus_dm = (high - high.shift(1)).where((high - high.shift(1)) > (low.shift(1) - low), 0)
        minus_dm = (low.shift(1) - low).where((low.shift(1) - low) > (high - high.shift(1)), 0)

        plus_di = 100 * plus_dm.rolling(window=self.adx_period).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=self.adx_period).mean() / atr
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.rolling(window=self.adx_period).mean()
        return adx

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        sar, trend = self.calculate_sar(high, low, close)
        adx = self.calculate_adx(high, low, close)

        latest_sar = sar.iloc[-1]
        latest_trend = trend.iloc[-1]
        latest_adx = adx.iloc[-1]
        latest_close = close.iloc[-1]

        if pd.isna(latest_adx):
            return {"signal": "NO_DATA"}

        # ADX filtresi
        if latest_adx < self.adx_threshold:
            signal = "NO_TREND"
            desc = f"ADX {latest_adx:.1f} < {self.adx_threshold}. SAR sinyali zayıf trendte."
        elif latest_trend == 1 and latest_close > latest_sar:
            signal = "BUY"
            desc = f"SAR bullish + ADX {latest_adx:.1f}. Güçlü uptrend."
        elif latest_trend == -1 and latest_close < latest_sar:
            signal = "SELL"
            desc = f"SAR bearish + ADX {latest_adx:.1f}. Güçlü downtrend."
        else:
            signal = "NEUTRAL"
            desc = "SAR ve ADX uyumsuz."

        return {
            "signal": signal,
            "sar": round(float(latest_sar), 2),
            "adx": round(float(latest_adx), 2),
            "trend": "UP" if latest_trend == 1 else "DOWN",
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(ParabolicSARADX().run(high, low, close))
