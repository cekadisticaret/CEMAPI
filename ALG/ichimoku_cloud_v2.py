"""
ichimoku_cloud_v2.py
Ichimoku Cloud v2: Sadece Tenkan-Kijun kesişimi ve bulut pozisyonu.
"""
import pandas as pd
import numpy as np
from typing import Dict

class IchimokuCloudV2:
    def __init__(self, tenkan: int = 9, kijun: int = 26, senkou_b: int = 52, displacement: int = 26):
        self.tenkan = tenkan
        self.kijun = kijun
        self.senkou_b = senkou_b
        self.displacement = displacement

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})
        df["tenkan"] = (high.rolling(self.tenkan).max() + low.rolling(self.tenkan).min()) / 2
        df["kijun"] = (high.rolling(self.kijun).max() + low.rolling(self.kijun).min()) / 2
        df["senkou_a"] = ((df["tenkan"] + df["kijun"]) / 2).shift(self.displacement)
        df["senkou_b"] = ((high.rolling(self.senkou_b).max() + low.rolling(self.senkou_b).min()) / 2).shift(self.displacement)
        return df

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        price = latest["close"]
        tenkan = latest["tenkan"]
        kijun = latest["kijun"]
        cloud_top = max(latest["senkou_a"], latest["senkou_b"]) if not pd.isna(latest["senkou_a"]) else np.nan
        cloud_bottom = min(latest["senkou_a"], latest["senkou_b"]) if not pd.isna(latest["senkou_a"]) else np.nan

        # TK Cross
        tk_cross_up = prev["tenkan"] <= prev["kijun"] and tenkan > kijun
        tk_cross_down = prev["tenkan"] >= prev["kijun"] and tenkan < kijun

        if tk_cross_up and price > cloud_top:
            signal = "STRONG_BUY"
            desc = "TK Cross bullish + fiyat bulut üzerinde."
        elif tk_cross_down and price < cloud_bottom:
            signal = "STRONG_SELL"
            desc = "TK Cross bearish + fiyat bulut altında."
        elif tk_cross_up:
            signal = "BUY"
            desc = "TK Cross bullish."
        elif tk_cross_down:
            signal = "SELL"
            desc = "TK Cross bearish."
        elif price > cloud_top:
            signal = "HOLD_LONG"
            desc = "Fiyat bulut üzerinde."
        elif price < cloud_bottom:
            signal = "HOLD_SHORT"
            desc = "Fiyat bulut altında."
        else:
            signal = "NEUTRAL"
            desc = "Fiyat bulut içinde."

        return {
            "signal": signal,
            "tenkan": round(float(tenkan), 2) if not pd.isna(tenkan) else None,
            "kijun": round(float(kijun), 2) if not pd.isna(kijun) else None,
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
    print(IchimokuCloudV2().run(high, low, close))
