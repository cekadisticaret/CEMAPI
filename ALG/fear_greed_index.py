"""
fear_greed_index.py
Fear & Greed Index: alternative.me API'den kripto piyasa duyarlılığı.
"""
import os
import requests
import pandas as pd
from typing import Dict, Optional
from datetime import datetime

class FearGreedIndex:
    def __init__(self):
        self.url = "https://api.alternative.me/fng/"

    def fetch_current(self) -> Dict:
        """Güncel Fear & Greed değerini çeker."""
        try:
            resp = requests.get(f"{self.url}?limit=1", timeout=15)
            data = resp.json()
            item = data["data"][0]
            return {
                "value": int(item["value"]),
                "classification": item["value_classification"],
                "timestamp": datetime.fromtimestamp(int(item["timestamp"])).strftime("%Y-%m-%d")
            }
        except Exception as e:
            return {"error": str(e)}

    def fetch_history(self, limit: int = 30) -> pd.DataFrame:
        """Geçmiş Fear & Greed verisi."""
        resp = requests.get(f"{self.url}?limit={limit}", timeout=15)
        data = resp.json()
        df = pd.DataFrame(data["data"])
        df["value"] = df["value"].astype(int)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        return df

    def generate_signal(self) -> Dict:
        data = self.fetch_current()
        if "error" in data:
            return data

        val = data["value"]

        if val <= 20:
            signal = "EXTREME_FEAR"
            desc = f"Fear & Greed {val}: Aşırı korku. Birikim fırsatı."
        elif val <= 40:
            signal = "FEAR"
            desc = f"Fear & Greed {val}: Korku bölgesi. Dikkatli olumlu."
        elif val <= 60:
            signal = "NEUTRAL"
            desc = f"Fear & Greed {val}: Tarafsız."
        elif val <= 80:
            signal = "GREED"
            desc = f"Fear & Greed {val}: Açgözlülük. Dikkatli olumsuz."
        else:
            signal = "EXTREME_GREED"
            desc = f"Fear & Greed {val}: Aşırı açgözlülük. Kâr realizasyonu düşün."

        return {
            "signal": signal,
            "value": val,
            "classification": data["classification"],
            "description": desc,
            "timestamp": data["timestamp"]
        }

    def run(self) -> Dict:
        return self.generate_signal()

if __name__ == "__main__":
    print(FearGreedIndex().run())
