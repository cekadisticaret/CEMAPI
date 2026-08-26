"""
ichimoku_cloud.py
Ichimoku Cloud: Tenkan, Kijun, Senkou Span A/B, Chikou Span.
"""
import pandas as pd
import numpy as np
from typing import Dict

class IchimokuCloud:
    def __init__(self, tenkan: int = 9, kijun: int = 26, senkou_b: int = 52, displacement: int = 26):
        self.tenkan = tenkan
        self.kijun = kijun
        self.senkou_b = senkou_b
        self.displacement = displacement

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # Tenkan-sen (Conversion Line)
        df["tenkan"] = (high.rolling(window=self.tenkan).max() + low.rolling(window=self.tenkan).min()) / 2

        # Kijun-sen (Base Line)
        df["kijun"] = (high.rolling(window=self.kijun).max() + low.rolling(window=self.kijun).min()) / 2

        # Senkou Span A (Leading Span A)
        df["senkou_a"] = ((df["tenkan"] + df["kijun"]) / 2).shift(self.displacement)

        # Senkou Span B (Leading Span B)
        df["senkou_b"] = ((high.rolling(window=self.senkou_b).max() + low.rolling(window=self.senkou_b).min()) / 2).shift(self.displacement)

        # Chikou Span (Lagging Span)
        df["chikou"] = close.shift(-self.displacement)

        return df

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]

        price = latest["close"]
        tenkan = latest["tenkan"]
        kijun = latest["kijun"]
        senkou_a = latest["senkou_a"]
        senkou_b = latest["senkou_b"]

        # Bulut (Kumo)
        cloud_top = max(senkou_a, senkou_b) if not pd.isna(senkou_a) and not pd.isna(senkou_b) else np.nan
        cloud_bottom = min(senkou_a, senkou_b) if not pd.isna(senkou_a) and not pd.isna(senkou_b) else np.nan

        # Sinyaller
        tk_cross = tenkan > kijun if not pd.isna(tenkan) and not pd.isna(kijun) else False
        price_above_cloud = price > cloud_top if not pd.isna(cloud_top) else False
        price_below_cloud = price < cloud_bottom if not pd.isna(cloud_bottom) else False

        if tk_cross and price_above_cloud:
            signal = "STRONG_BUY"
            desc = "Tenkan>Kijun ve fiyat bulut üzerinde. Güçlü bullish."
        elif not tk_cross and price_below_cloud:
            signal = "STRONG_SELL"
            desc = "Tenkan<Kijun ve fiyat bulut altında. Güçlü bearish."
        elif price_above_cloud:
            signal = "BUY"
            desc = "Fiyat bulut üzerinde. Bullish bias."
        elif price_below_cloud:
            signal = "SELL"
            desc = "Fiyat bulut altında. Bearish bias."
        else:
            signal = "NEUTRAL"
            desc = "Fiyat bulut içinde. Kararsız."

        return {
            "signal": signal,
            "tenkan": round(float(tenkan), 2) if not pd.isna(tenkan) else None,
            "kijun": round(float(kijun), 2) if not pd.isna(kijun) else None,
            "senkou_a": round(float(senkou_a), 2) if not pd.isna(senkou_a) else None,
            "senkou_b": round(float(senkou_b), 2) if not pd.isna(senkou_b) else None,
            "cloud_top": round(float(cloud_top), 2) if not pd.isna(cloud_top) else None,
            "cloud_bottom": round(float(cloud_bottom), 2) if not pd.isna(cloud_bottom) else None,
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(IchimokuCloud().run(high, low, close))
