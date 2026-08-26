"""
volume_profile.py
Volume Profile: POC (Point of Control), VAH, VAL seviyeleri.
"""
import pandas as pd
import numpy as np
from typing import Dict

class VolumeProfile:
    def __init__(self, lookback: int = 100, bins: int = 20):
        self.lookback = lookback
        self.bins = bins

    def calculate(self, prices: pd.Series, volumes: pd.Series) -> Dict:
        recent_prices = prices.iloc[-self.lookback:]
        recent_volumes = volumes.iloc[-self.lookback:]

        # Histogram
        hist, bin_edges = np.histogram(recent_prices, bins=self.bins, weights=recent_volumes)

        # POC: En yüksek hacimli fiyat seviyesi
        poc_idx = np.argmax(hist)
        poc = (bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2

        # Value Area (toplam hacmin %70'inin bulunduğu bölge)
        total_vol = np.sum(hist)
        target_vol = total_vol * 0.70

        sorted_indices = np.argsort(hist)[::-1]
        cum_vol = 0
        value_indices = []
        for idx in sorted_indices:
            cum_vol += hist[idx]
            value_indices.append(idx)
            if cum_vol >= target_vol:
                break

        vah = bin_edges[max(value_indices) + 1]
        val = bin_edges[min(value_indices)]

        current_price = prices.iloc[-1]

        return {
            "poc": round(float(poc), 2),
            "vah": round(float(vah), 2),
            "val": round(float(val), 2),
            "current_price": round(float(current_price), 2),
            "in_value_area": val <= current_price <= vah,
            "above_poc": current_price > poc
        }

    def generate_signal(self, prices: pd.Series, volumes: pd.Series) -> Dict:
        vp = self.calculate(prices, volumes)

        if not vp["in_value_area"] and vp["current_price"] < vp["val"]:
            signal = "BELOW_VALUE"
            desc = f"Fiyat Value Area altında ({vp['val']}). Aşırı satım / dip bölgesi."
        elif not vp["in_value_area"] and vp["current_price"] > vp["vah"]:
            signal = "ABOVE_VALUE"
            desc = f"Fiyat Value Area üzerinde ({vp['vah']}). Aşırı alım / zirve bölgesi."
        elif vp["current_price"] > vp["poc"]:
            signal = "ABOVE_POC"
            desc = f"Fiyat POC ({vp['poc']}) üzerinde. Bullish bias."
        else:
            signal = "BELOW_POC"
            desc = f"Fiyat POC ({vp['poc']}) altında. Bearish bias."

        return {
            "signal": signal,
            "volume_profile": vp,
            "description": desc
        }

    def run(self, prices: pd.Series, volumes: pd.Series) -> Dict:
        return self.generate_signal(prices, volumes)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(200) * 2))
    volumes = pd.Series(np.random.randint(1000, 10000, 200))
    print(VolumeProfile().run(prices, volumes))
