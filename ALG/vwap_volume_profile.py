"""
vwap_volume_profile.py
VWAP + Volume Profile kombinasyonu.
"""
import pandas as pd
import numpy as np
from typing import Dict

class VWAPVolumeProfile:
    def __init__(self, vwap_anchor: str = "D", vp_lookback: int = 100, vp_bins: int = 20):
        self.vwap_anchor = vwap_anchor
        self.vp_lookback = vp_lookback
        self.vp_bins = vp_bins

    def calculate_vwap(self, prices: pd.Series, volumes: pd.Series, timestamps: pd.DatetimeIndex = None) -> pd.Series:
        df = pd.DataFrame({"price": prices, "volume": volumes})
        if timestamps is not None:
            df.index = timestamps
        df["pv"] = df["price"] * df["volume"]

        if self.vwap_anchor == "D":
            cum_pv = df.groupby(df.index.date)["pv"].cumsum()
            cum_vol = df.groupby(df.index.date)["volume"].cumsum()
        else:
            cum_pv = df["pv"].cumsum()
            cum_vol = df["volume"].cumsum()

        vwap = cum_pv / cum_vol
        return vwap

    def calculate_vp(self, prices: pd.Series, volumes: pd.Series) -> Dict:
        recent = prices.iloc[-self.vp_lookback:]
        recent_vols = volumes.iloc[-self.vp_lookback:]

        hist, edges = np.histogram(recent, bins=self.vp_bins, weights=recent_vols)
        poc_idx = np.argmax(hist)
        poc = (edges[poc_idx] + edges[poc_idx + 1]) / 2

        total_vol = np.sum(hist)
        target = total_vol * 0.70
        sorted_idx = np.argsort(hist)[::-1]
        cum = 0
        va_indices = []
        for idx in sorted_idx:
            cum += hist[idx]
            va_indices.append(idx)
            if cum >= target:
                break

        return {
            "poc": round(float(poc), 2),
            "vah": round(float(edges[max(va_indices) + 1]), 2),
            "val": round(float(edges[min(va_indices)]), 2)
        }

    def generate_signal(self, prices: pd.Series, volumes: pd.Series, timestamps: pd.DatetimeIndex = None) -> Dict:
        vwap = self.calculate_vwap(prices, volumes, timestamps)
        vp = self.calculate_vp(prices, volumes)

        latest_price = prices.iloc[-1]
        latest_vwap = vwap.iloc[-1]

        # VWAP + VP kombinasyonu
        above_vwap = latest_price > latest_vwap
        in_value = vp["val"] <= latest_price <= vp["vah"]
        above_poc = latest_price > vp["poc"]

        if above_vwap and above_poc and in_value:
            signal = "STRONG_BUY"
            desc = "Fiyat VWAP ve POC üzerinde, Value Area içinde. Güçlü bullish."
        elif not above_vwap and not above_poc and not in_value:
            signal = "STRONG_SELL"
            desc = "Fiyat VWAP ve POC altında, Value Area dışında. Güçlü bearish."
        elif above_vwap:
            signal = "BULLISH"
            desc = "Fiyat VWAP üzerinde."
        else:
            signal = "BEARISH"
            desc = "Fiyat VWAP altında."

        return {
            "signal": signal,
            "vwap": round(float(latest_vwap), 2),
            "price": round(float(latest_price), 2),
            "volume_profile": vp,
            "description": desc
        }

    def run(self, prices: pd.Series, volumes: pd.Series, timestamps: pd.DatetimeIndex = None) -> Dict:
        return self.generate_signal(prices, volumes, timestamps)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(200) * 2))
    volumes = pd.Series(np.random.randint(1000, 10000, 200))
    print(VWAPVolumeProfile().run(prices, volumes))
