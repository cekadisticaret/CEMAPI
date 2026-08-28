"""
garch_volatility_targeting.py
GARCH(1,1) Volatilite Hedefleme: Bir sonraki barin volatilitesini tahmin eder;
kademeyi target_vol / forecast_vol oraniyla ayarlar. Kaldırasli pozisyon
boyutlandirmasi icin kullanilir.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class GARCHResult:
    forecast_vol: float
    target_vol: float
    position_scalar: float
    signal: str

class GARCHVolatilityTargeting:
    def __init__(self, target_vol: float = 0.015, omega: float = 1e-6,
                 alpha: float = 0.1, beta: float = 0.85, lookback: int = 252):
        """
        Args:
            target_vol: Hedeflenen gunluk volatilite (default %1.5)
            omega: GARCH sabit terim
            alpha: GARCH alpha (sok tepkisi)
            beta: GARCH beta (kalicilik)
            lookback: Egitim periyodu
        """
        self.target_vol = target_vol
        self.omega = omega
        self.alpha = alpha
        self.beta = beta
        self.lookback = lookback

    def _fit_garch(self, returns: pd.Series) -> float:
        """GARCH(1,1) parametreleriyle volatilite tahmini."""
        returns = returns.dropna().iloc[-self.lookback:]
        n = len(returns)

        if n < 30:
            return returns.std()

        # Basit GARCH(1,1) recursive tahmin
        var = np.zeros(n)
        var[0] = returns.var()

        for t in range(1, n):
            var[t] = (self.omega 
                     + self.alpha * returns.iloc[t-1]**2 
                     + self.beta * var[t-1])

        # Bir sonraki periyod tahmini
        next_var = self.omega + self.alpha * returns.iloc[-1]**2 + self.beta * var[-1]
        return np.sqrt(next_var)

    def calculate(self, prices: pd.Series) -> GARCHResult:
        returns = prices.pct_change().dropna()
        forecast_vol = self._fit_garch(returns)

        # Pozisyon skaleri: hedef vol / tahmin vol
        # Eger tahmin vol > hedef vol -> pozisyon kucult
        # Eger tahmin vol < hedef vol -> pozisyon buyult
        scalar = self.target_vol / forecast_vol if forecast_vol > 0 else 1.0
        scalar = np.clip(scalar, 0.1, 3.0)  # Limitler

        if scalar > 1.2:
            signal = "INCREASE_SIZE"
        elif scalar < 0.8:
            signal = "DECREASE_SIZE"
        else:
            signal = "MAINTAIN_SIZE"

        return GARCHResult(
            forecast_vol=round(float(forecast_vol), 6),
            target_vol=self.target_vol,
            position_scalar=round(float(scalar), 3),
            signal=signal
        )

    def generate_signal(self, prices: pd.Series, current_position_size: float = 1.0) -> Dict:
        result = self.calculate(prices)

        new_size = current_position_size * result.position_scalar

        return {
            "signal": result.signal,
            "forecast_volatility": f"{result.forecast_vol:.4%}",
            "target_volatility": f"{result.target_vol:.4%}",
            "position_scalar": result.position_scalar,
            "current_size": current_position_size,
            "recommended_size": round(new_size, 3),
            "description": f"GARCH tahmini vol: {result.forecast_vol:.4%}. "
                          f"Pozisyon {result.position_scalar:.2f}x ile ayarlanmali."
        }

    def run(self, prices: pd.Series, current_position_size: float = 1.0) -> Dict:
        return self.generate_signal(prices, current_position_size)


if __name__ == "__main__":
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 300)
    prices = pd.Series(100 * np.exp(np.cumsum(returns)))
    print(GARCHVolatilityTargeting().run(prices, current_position_size=1.0))
