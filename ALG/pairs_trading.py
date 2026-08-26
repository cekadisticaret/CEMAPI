"""
pairs_trading.py
Pairs Trading: İki kointegre varlık arasındaki spread'i trade eder.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from scipy import stats

class PairsTrading:
    def __init__(self, lookback: int = 60, entry_z: float = 2.0, exit_z: float = 0.5):
        self.lookback = lookback
        self.entry_z = entry_z
        self.exit_z = exit_z

    def calculate_hedge_ratio(self, series1: pd.Series, series2: pd.Series) -> float:
        """OLS regression ile hedge ratio hesaplar."""
        x = series2.values.reshape(-1, 1)
        y = series1.values
        slope, _, _, _, _ = stats.linregress(x.flatten(), y)
        return slope

    def calculate_spread(self, series1: pd.Series, series2: pd.Series) -> pd.DataFrame:
        """Spread ve Z-Score hesaplar."""
        # Hedge ratio (son lookback periyodu)
        hr = self.calculate_hedge_ratio(series1.iloc[-self.lookback:], series2.iloc[-self.lookback:])

        spread = series1 - hr * series2
        spread_mean = spread.rolling(window=self.lookback).mean()
        spread_std = spread.rolling(window=self.lookback).std()
        zscore = (spread - spread_mean) / spread_std

        df = pd.DataFrame({
            "spread": spread,
            "spread_mean": spread_mean,
            "spread_std": spread_std,
            "zscore": zscore,
            "hedge_ratio": hr
        })
        return df

    def test_cointegration(self, series1: pd.Series, series2: pd.Series) -> Dict:
        """Engle-Granger cointegration testi."""
        from statsmodels.tsa.stattools import coint
        score, pvalue, _ = coint(series1, series2)
        return {
            "coint_score": float(score),
            "pvalue": float(pvalue),
            "is_cointegrated": pvalue < 0.05
        }

    def generate_signal(self, series1: pd.Series, series2: pd.Series) -> Dict:
        df = self.calculate_spread(series1, series2)
        latest = df.iloc[-1]
        z = latest["zscore"]

        if pd.isna(z):
            return {"signal": "NO_DATA"}

        coint_test = self.test_cointegration(series1, series2)

        if not coint_test["is_cointegrated"]:
            return {
                "signal": "NO_TRADE",
                "reason": "Varlıklar kointegre değil.",
                "coint_pvalue": coint_test["pvalue"]
            }

        if z < -self.entry_z:
            signal = "LONG_SPREAD"
            desc = f"Z-Score {z:.2f}. Series1 long, Series2 short."
        elif z > self.entry_z:
            signal = "SHORT_SPREAD"
            desc = f"Z-Score {z:.2f}. Series1 short, Series2 long."
        elif abs(z) < self.exit_z:
            signal = "EXIT"
            desc = "Spread ortalamasına döndü. Pozisyon kapat."
        else:
            signal = "HOLD"
            desc = f"Z-Score {z:.2f}. Beklemede."

        return {
            "signal": signal,
            "zscore": round(float(z), 3),
            "hedge_ratio": round(float(latest["hedge_ratio"]), 4),
            "spread": round(float(latest["spread"]), 4),
            "cointegration": coint_test,
            "description": desc
        }

    def run(self, series1: pd.Series, series2: pd.Series) -> Dict:
        return self.generate_signal(series1, series2)

if __name__ == "__main__":
    np.random.seed(42)
    s1 = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    s2 = pd.Series(100 + np.cumsum(np.random.randn(100) * 2) + np.random.randn(100) * 0.5)
    print(PairsTrading().run(s1, s2))
