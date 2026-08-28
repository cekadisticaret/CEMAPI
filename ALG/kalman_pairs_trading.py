"""
kalman_pairs_trading.py
Kalman Filtresi ile Dinamik Hedge Ratio: Iki varlik arasindaki beta(t)
zamanla kayan gizli durum olarak tahmin eder. Spread = Y - beta(t)*X.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class KalmanState:
    beta: float
    spread: float
    spread_mean: float
    spread_std: float
    zscore: float

class KalmanPairsTrading:
    def __init__(self, delta: float = 1e-5, R: float = 0.001):
        """
        Args:
            delta: Adaptasyon hizi (kucuk = yavas, buyuk = hizli)
            R: Olcum gurultusu varyansi
        """
        self.delta = delta
        self.R = R
        self.wt = 1.0  # Tahmin hatasi varyansi
        self.theta = 0.0  # Beta tahmini
        self.vt = 0.0  # Tahmin hatasi

    def _kalman_update(self, x: float, y: float) -> float:
        """Tek adimlik Kalman guncellemesi."""
        # Tahmin hatasi
        self.vt = y - self.theta * x

        # Tahmin hatasi varyansi
        self.wt = self.wt + self.delta

        # Kalman kazanci
        K = (self.wt * x) / (self.wt * x**2 + self.R)

        # Beta guncelleme
        self.theta = self.theta + K * self.vt

        # Varyans guncelleme
        self.wt = (1 - K * x) * self.wt

        return self.theta

    def calculate(self, series_x: pd.Series, series_y: pd.Series) -> pd.DataFrame:
        """Tum seri uzerinde Kalman filtresi calistirir."""
        df = pd.DataFrame({"x": series_x, "y": series_y})
        df = df.dropna()

        betas = []
        spreads = []

        # Reset state
        self.wt = 1.0
        self.theta = 0.0

        for i in range(len(df)):
            x = df["x"].iloc[i]
            y = df["y"].iloc[i]
            beta = self._kalman_update(x, y)
            spread = y - beta * x
            betas.append(beta)
            spreads.append(spread)

        df["beta"] = betas
        df["spread"] = spreads
        df["spread_mean"] = df["spread"].rolling(window=60).mean()
        df["spread_std"] = df["spread"].rolling(window=60).std()
        df["zscore"] = (df["spread"] - df["spread_mean"]) / df["spread_std"]

        return df

    def generate_signal(self, series_x: pd.Series, series_y: pd.Series,
                       entry_z: float = 2.0, exit_z: float = 0.5) -> Dict:
        df = self.calculate(series_x, series_y)
        latest = df.iloc[-1]

        if pd.isna(latest["zscore"]):
            return {"signal": "NO_DATA", "reason": "Yetersiz veri"}

        z = latest["zscore"]
        beta = latest["beta"]

        if z < -entry_z:
            signal = "LONG_SPREAD"
            desc = f"Z-Score {z:.2f}. Y long, X short. Beta: {beta:.4f}"
        elif z > entry_z:
            signal = "SHORT_SPREAD"
            desc = f"Z-Score {z:.2f}. Y short, X long. Beta: {beta:.4f}"
        elif abs(z) < exit_z:
            signal = "EXIT"
            desc = "Spread ortalamasina dondu. Pozisyon kapat."
        else:
            signal = "HOLD"
            desc = f"Z-Score {z:.2f}. Beklemede."

        return {
            "signal": signal,
            "beta": round(float(beta), 4),
            "spread": round(float(latest["spread"]), 4),
            "zscore": round(float(z), 3),
            "hedge_ratio": round(float(beta), 4),
            "description": desc
        }

    def run(self, series_x: pd.Series, series_y: pd.Series,
            entry_z: float = 2.0, exit_z: float = 0.5) -> Dict:
        return self.generate_signal(series_x, series_y, entry_z, exit_z)


if __name__ == "__main__":
    np.random.seed(42)
    x = pd.Series(100 + np.cumsum(np.random.randn(300) * 2))
    y = pd.Series(100 + np.cumsum(np.random.randn(300) * 2) + np.random.randn(300) * 0.5)
    print(KalmanPairsTrading().run(x, y))
