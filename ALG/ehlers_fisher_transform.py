"""
ehlers_fisher_transform.py
Ehlers Fisher Transform: Fiyati Gaussian dagilima sikistirir; donus
noktalarini erken tespit eder. Trend filtresiyle birlikte kullanilmali.
"""
import pandas as pd
import numpy as np
from typing import Dict

class EhlersFisherTransform:
    def __init__(self, period: int = 10, trend_filter_period: int = 50):
        """
        Args:
            period: Fisher Transform periyodu
            trend_filter_period: Trend filtresi EMA periyodu
        """
        self.period = period
        self.trend_filter_period = trend_filter_period

    def _normalize(self, prices: pd.Series) -> pd.Series:
        """Fiyati -1 ile +1 arasina normalize eder."""
        highest = prices.rolling(window=self.period).max()
        lowest = prices.rolling(window=self.period).min()

        # 0.001 ekleyerek sifira bolunmeyi onle
        value = 0.33 * 2 * ((prices - lowest) / (highest - lowest + 0.001) - 0.5)

        # Smooth
        smoothed = pd.Series(index=prices.index, dtype=float)
        smoothed.iloc[0] = value.iloc[0]
        for i in range(1, len(value)):
            smoothed.iloc[i] = 0.5 * value.iloc[i] + 0.5 * smoothed.iloc[i-1]

        return smoothed.clip(-0.999, 0.999)

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        norm = self._normalize(prices)

        # Fisher Transform
        fisher = 0.5 * np.log((1 + norm) / (1 - norm))

        # Trigger (1 bar gecikmeli)
        trigger = fisher.shift(1)

        # Trend filtresi
        ema = prices.ewm(span=self.trend_filter_period).mean()
        trend = np.where(prices > ema, 1, -1)

        df = pd.DataFrame({
            "price": prices,
            "fisher": fisher,
            "trigger": trigger,
            "trend": trend,
            "ema": ema
        })
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        fisher = latest["fisher"]
        trigger = latest["trigger"]
        trend = latest["trend"]

        if pd.isna(fisher) or pd.isna(trigger):
            return {"signal": "NO_DATA"}

        # Cross tespiti
        cross_up = prev["fisher"] <= prev["trigger"] and fisher > trigger
        cross_down = prev["fisher"] >= prev["trigger"] and fisher < trigger

        if cross_up and trend == 1:
            signal = "BUY"
            desc = "Fisher Trigger'i yukari kesti + uptrend."
        elif cross_down and trend == -1:
            signal = "SELL"
            desc = "Fisher Trigger'i asagi kesti + downtrend."
        elif cross_up:
            signal = "WEAK_BUY"
            desc = "Fisher yukari kesti ama trend uyumsuz."
        elif cross_down:
            signal = "WEAK_SELL"
            desc = "Fisher asagi kesti ama trend uyumsuz."
        elif fisher > 2.0:
            signal = "OVERBOUGHT"
            desc = f"Fisher {fisher:.2f}. Asiri alim."
        elif fisher < -2.0:
            signal = "OVERSOLD"
            desc = f"Fisher {fisher:.2f}. Asiri satim."
        else:
            signal = "NEUTRAL"
            desc = f"Fisher {fisher:.2f}. Tarafsiz."

        return {
            "signal": signal,
            "fisher": round(float(fisher), 3),
            "trigger": round(float(trigger), 3),
            "trend": "UP" if trend == 1 else "DOWN",
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)


if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(200) * 2))
    print(EhlersFisherTransform().run(prices))
