"""
oi_divergence.py
Open Interest + Fiyat Diverjansı: OI ve fiyat arasındaki uyumsuzluk.
"""
import pandas as pd
import numpy as np
from typing import Dict

class OIDivergence:
    def __init__(self, lookback: int = 20):
        self.lookback = lookback

    def calculate(self, prices: pd.Series, oi: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices, "oi": oi})
        df["price_change"] = prices.pct_change(self.lookback)
        df["oi_change"] = oi.pct_change(self.lookback)
        return df

    def find_divergence(self, df: pd.DataFrame) -> str:
        latest = df.iloc[-1]

        if pd.isna(latest["price_change"]) or pd.isna(latest["oi_change"]):
            return "NO_DATA"

        p_chg = latest["price_change"]
        oi_chg = latest["oi_change"]

        # Bullish OI divergence: fiyat düşerken OI artıyor (short birikimi -> squeeze potansiyeli)
        if p_chg < -0.05 and oi_chg > 0.10:
            return "BULLISH_OI_DIV"
        # Bearish OI divergence: fiyat yükselirken OI düşüyor (trend zayıflığı)
        elif p_chg > 0.05 and oi_chg < -0.10:
            return "BEARISH_OI_DIV"
        # Normal confirmation
        elif p_chg > 0 and oi_chg > 0:
            return "CONFIRMED_UP"
        elif p_chg < 0 and oi_chg > 0:
            return "LIQUIDATION_RISK"
        else:
            return "NEUTRAL"

    def generate_signal(self, prices: pd.Series, oi: pd.Series) -> Dict:
        df = self.calculate(prices, oi)
        div = self.find_divergence(df)
        latest = df.iloc[-1]

        signals = {
            "BULLISH_OI_DIV": ("BUY", "Fiyat düşerken OI artıyor. Short squeeze potansiyeli."),
            "BEARISH_OI_DIV": ("SELL", "Fiyat yükselirken OI düşüyor. Trend zayıflığı."),
            "CONFIRMED_UP": ("HOLD_LONG", "Fiyat ve OI birlikte yükseliyor. Sağlam trend."),
            "LIQUIDATION_RISK": ("CAUTION", "Fiyat düşerken OI artıyor. Kaskad likidasyon riski."),
            "NEUTRAL": ("NEUTRAL", "OI ve fiyat uyumlu."),
            "NO_DATA": ("NO_DATA", "Yetersiz veri.")
        }

        sig, desc = signals.get(div, ("NEUTRAL", ""))

        return {
            "signal": sig,
            "divergence_type": div,
            "price_change": f"{latest['price_change']:.2%}" if not pd.isna(latest["price_change"]) else None,
            "oi_change": f"{latest['oi_change']:.2%}" if not pd.isna(latest["oi_change"]) else None,
            "description": desc
        }

    def run(self, prices: pd.Series, oi: pd.Series) -> Dict:
        return self.generate_signal(prices, oi)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    oi = pd.Series(1000000 + np.cumsum(np.random.randn(100) * 50000))
    print(OIDivergence().run(prices, oi))
