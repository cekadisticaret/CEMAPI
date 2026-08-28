"""
volatility_scaled_tsmom.py
Volatilite-Olcekli Time-Series Momentum: Mutlak momentum + vol targeting.
Moskowitz-Ooi-Pedersen (2012) cercevesi.
"""
import pandas as pd
import numpy as np
from typing import Dict

class VolatilityScaledTSMOM:
    def __init__(self, lookback: int = 12, vol_lookback: int = 63, 
                 target_vol: float = 0.15, max_leverage: float = 3.0):
        """
        Args:
            lookback: Momentum periyodu (gun)
            vol_lookback: Volatilite tahmini periyodu
            target_vol: Hedef yillik volatilite (%15)
            max_leverage: Maksimum kaldiras
        """
        self.lookback = lookback
        self.vol_lookback = vol_lookback
        self.target_vol = target_vol
        self.max_leverage = max_leverage

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices})
        df["returns"] = prices.pct_change()

        # Momentum: lookback donemlik getiri
        df["momentum"] = prices.pct_change(self.lookback)

        # Gerçeklesen volatilite (yilliklandirilmis)
        df["realized_vol"] = df["returns"].rolling(self.vol_lookback).std() * np.sqrt(365)

        # Volatilite olcekleme
        df["vol_scalar"] = self.target_vol / df["realized_vol"]
        df["vol_scalar"] = df["vol_scalar"].clip(0.1, self.max_leverage)

        # Pozisyon isareti ve boyutu
        df["position_sign"] = np.sign(df["momentum"])
        df["position_size"] = df["position_sign"] * df["vol_scalar"]

        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]

        if pd.isna(latest["momentum"]):
            return {"signal": "NO_DATA"}

        momentum = latest["momentum"]
        vol = latest["realized_vol"]
        scalar = latest["vol_scalar"]
        position = latest["position_size"]

        if momentum > 0.05 and scalar > 0.5:
            signal = "STRONG_BUY"
            desc = f"Momentum {momentum:.2%}, vol {vol:.1%}, kaldiras {scalar:.2f}x. Guclu long."
        elif momentum > 0:
            signal = "BUY"
            desc = f"Momentum {momentum:.2%}, kaldiras {scalar:.2f}x. Long."
        elif momentum < -0.05 and scalar > 0.5:
            signal = "STRONG_SELL"
            desc = f"Momentum {momentum:.2%}, vol {vol:.1%}, kaldiras {scalar:.2f}x. Guclu short."
        elif momentum < 0:
            signal = "SELL"
            desc = f"Momentum {momentum:.2%}, kaldiras {scalar:.2f}x. Short."
        else:
            signal = "NEUTRAL"
            desc = f"Momentum zayif. Bekle."

        return {
            "signal": signal,
            "momentum": f"{momentum:.2%}",
            "realized_vol": f"{vol:.1%}",
            "vol_scalar": round(float(scalar), 2),
            "recommended_position": round(float(position), 2),
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)


if __name__ == "__main__":
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 500)
    prices = pd.Series(100 * np.exp(np.cumsum(returns)))
    print(VolatilityScaledTSMOM().run(prices))
