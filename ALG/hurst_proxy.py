"""
hurst_proxy.py
Hurst Proxy: R/S analizi proxy'si ile trend/mean reversion tespiti.
"""
import pandas as pd
import numpy as np
from typing import Dict

class HurstProxy:
    def __init__(self, max_lag: int = 100):
        self.max_lag = max_lag

    def calculate_hurst(self, prices: pd.Series) -> float:
        """Basitleştirilmiş Hurst üssü."""
        lags = range(2, min(self.max_lag, len(prices) // 4))
        tau = [np.std(np.subtract(prices[lag:], prices[:-lag])) for lag in lags]

        if len(tau) < 2 or any(t == 0 for t in tau):
            return 0.5

        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return poly[0]

    def generate_signal(self, prices: pd.Series) -> Dict:
        hurst = self.calculate_hurst(prices)

        if hurst > 0.55:
            signal = "TRENDING"
            desc = f"Hurst {hurst:.3f} > 0.55. Trend davranışı dominant."
        elif hurst < 0.45:
            signal = "MEAN_REVERTING"
            desc = f"Hurst {hurst:.3f} < 0.45. Mean reversion dominant."
        else:
            signal = "RANDOM_WALK"
            desc = f"Hurst {hurst:.3f} ≈ 0.5. Rastgele yürüyüş."

        return {
            "signal": signal,
            "hurst": round(float(hurst), 4),
            "description": desc,
            "strategy_suggestion": "Trend" if hurst > 0.55 else "MeanReversion" if hurst < 0.45 else "None"
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(200) * 2))
    print(HurstProxy().run(prices))
