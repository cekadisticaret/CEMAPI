"""
onchain_netflow_whale.py
On-chain Exchange Netflow + Whale Accumulation: Borsa giris/cikis ve
whale cuzdan hareketlerinden kompozit skor uretir.
"""
import os
import requests
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta

class OnChainNetflowWhale:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GLASSNODE_API_KEY")
        self.base_url = "https://api.glassnode.com/v1/metrics"
        # Alternatif: CryptoQuant, Nansen, Arkham API'leri
        self.weights = {
            "whale_netflow": 0.40,
            "exchange_netflow": 0.35,
            "accumulation": 0.15,
            "whale_exchange_ratio": 0.10
        }

    def _mock_fetch(self, metric: str, asset: str = "BTC", days: int = 30) -> pd.Series:
        """Mock veri - gercek uygulamada Glassnode API cagrilmali."""
        np.random.seed(hash(metric) % 2**32)
        dates = pd.date_range(end=datetime.now(), periods=days, freq="D")

        if "exchange" in metric:
            # Borsalara giris = negatif (satis baskisi), cikis = pozitif
            data = np.random.randn(days) * 1000 + 500
        elif "whale" in metric:
            # Whale birikimi = pozitif
            data = np.random.randn(days) * 500 + 200
        else:
            data = np.random.randn(days) * 100

        return pd.Series(data, index=dates)

    def fetch_data(self, asset: str = "BTC", days: int = 30) -> pd.DataFrame:
        """On-chain verileri ceker (mock versiyon)."""
        df = pd.DataFrame()
        df["whale_netflow"] = self._mock_fetch("whale_netflow", asset, days)
        df["exchange_netflow"] = self._mock_fetch("exchange_netflow", asset, days)
        df["accumulation"] = self._mock_fetch("accumulation", asset, days)
        df["whale_exchange_ratio"] = self._mock_fetch("whale_exchange_ratio", asset, days)
        return df

    def calculate_composite(self, df: pd.DataFrame) -> pd.Series:
        """Agirlikli kompozit skor hesaplar."""
        composite = (
            df["whale_netflow"] * self.weights["whale_netflow"] +
            df["exchange_netflow"] * self.weights["exchange_netflow"] +
            df["accumulation"] * self.weights["accumulation"] +
            df["whale_exchange_ratio"] * self.weights["whale_exchange_ratio"]
        )
        # Normalize (z-score)
        return (composite - composite.rolling(30).mean()) / composite.rolling(30).std()

    def generate_from_tape(self, close: pd.Series, volume: Optional[pd.Series] = None) -> Dict:
        """Glassnode yokken mum + hacimden netflow / whale proxy."""
        c = close.astype(float).reset_index(drop=True)
        if volume is None or len(volume) != len(c):
            v = c.diff().abs().fillna(0) + 1.0
        else:
            v = volume.astype(float).reset_index(drop=True)
        ret = c.pct_change().fillna(0)
        exch = (-ret * v).rolling(8, min_periods=4).sum()
        whale = (v / v.rolling(20, min_periods=8).mean() - 1).fillna(0) * ret.rolling(3, min_periods=1).sum()
        acc = (c / c.rolling(20, min_periods=8).mean() - 1).fillna(0)
        composite = (
            whale * self.weights["whale_netflow"]
            + exch * self.weights["exchange_netflow"]
            + acc * self.weights["accumulation"]
        )
        std = composite.rolling(20, min_periods=8).std()
        z = (composite - composite.rolling(20, min_periods=8).mean()) / std.replace(0, pd.NA)
        latest = float(z.iloc[-1]) if not pd.isna(z.iloc[-1]) else 0.0
        if latest > 2.0:
            signal, desc = "STRONG_BUY", f"Tape skor {latest:.2f}. Hacimli birikim."
        elif latest > 1.0:
            signal, desc = "BUY", f"Tape skor {latest:.2f}. Pozitif akış."
        elif latest < -2.0:
            signal, desc = "STRONG_SELL", f"Tape skor {latest:.2f}. Hacimli dağıtım."
        elif latest < -1.0:
            signal, desc = "SELL", f"Tape skor {latest:.2f}. Negatif akış."
        else:
            signal, desc = "NEUTRAL", f"Tape skor {latest:.2f}. Tarafsız."
        return {
            "signal": signal,
            "composite_score": round(latest, 3),
            "description": desc,
            "note": "Glassnode yok — 15m mum/hacim proxy",
        }

    def generate_signal(self, asset: str = "BTC", days: int = 30) -> Dict:
        df = self.fetch_data(asset, days)
        composite = self.calculate_composite(df)
        latest = composite.iloc[-1]

        if pd.isna(latest):
            return {"signal": "NO_DATA"}

        # Skor yorumlama
        if latest > 2.0:
            signal = "STRONG_BUY"
            desc = f"On-chain skor {latest:.2f}. Guclu whale birikimi + borsa cikisi."
        elif latest > 1.0:
            signal = "BUY"
            desc = f"On-chain skor {latest:.2f}. Pozitif akis."
        elif latest < -2.0:
            signal = "STRONG_SELL"
            desc = f"On-chain skor {latest:.2f}. Whale satisi + borsa girisi."
        elif latest < -1.0:
            signal = "SELL"
            desc = f"On-chain skor {latest:.2f}. Negatif akis."
        else:
            signal = "NEUTRAL"
            desc = f"On-chain skor {latest:.2f}. Tarafsiz."

        return {
            "signal": signal,
            "composite_score": round(float(latest), 3),
            "components": {
                "whale_netflow": round(float(df["whale_netflow"].iloc[-1]), 1),
                "exchange_netflow": round(float(df["exchange_netflow"].iloc[-1]), 1),
                "accumulation": round(float(df["accumulation"].iloc[-1]), 1),
            },
            "description": desc,
            "note": "Gercek uygulamada Glassnode/CryptoQuant API kullanilmali"
        }

    def run(self, asset: str = "BTC", days: int = 30,
            close: Optional[pd.Series] = None, volume: Optional[pd.Series] = None,
            prices: Optional[pd.Series] = None) -> Dict:
        series = close if close is not None else prices
        if series is not None and len(series) >= 30:
            return self.generate_from_tape(series, volume)
        return self.generate_signal(asset, days)


if __name__ == "__main__":
    print(OnChainNetflowWhale().run("BTC"))
