"""
rsi_divergence_strict.py
RSI Divergence (14) Katı: Sadece net diverjansları sinyal olarak üretir.
"""
import pandas as pd
import numpy as np
from typing import Dict

class RSIDivergenceStrict:
    def __init__(self, period: int = 14, lookback: int = 20, pivot_lookback: int = 5):
        self.period = period
        self.lookback = lookback
        self.pivot_lookback = pivot_lookback

    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(self.period).mean()
        avg_loss = loss.rolling(self.period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def find_pivots(self, series: pd.Series) -> pd.DataFrame:
        """Local min/max pivot noktalarını bulur."""
        pivots = pd.DataFrame({"value": series})
        pivots["is_high"] = (series == series.rolling(window=self.pivot_lookback*2+1, center=True).max())
        pivots["is_low"] = (series == series.rolling(window=self.pivot_lookback*2+1, center=True).min())
        return pivots

    def generate_signal(self, prices: pd.Series) -> Dict:
        rsi = self.calculate_rsi(prices)
        price_pivots = self.find_pivots(prices)
        rsi_pivots = self.find_pivots(rsi)

        # Son 2 pivot karşılaştırması
        recent = prices.iloc[-self.lookback:]
        recent_rsi = rsi.iloc[-self.lookback:]
        earlier = prices.iloc[-self.lookback*2:-self.lookback]
        earlier_rsi = rsi.iloc[-self.lookback*2:-self.lookback]

        if len(earlier) == 0 or pd.isna(recent_rsi.min()):
            return {"signal": "NO_DATA", "rsi": round(float(rsi.iloc[-1]), 2) if not pd.isna(rsi.iloc[-1]) else None}

        # Katı diverjans: price lower low + RSI higher low (bullish)
        if (recent.min() < earlier.min() and 
            recent_rsi.min() > earlier_rsi.min() and
            recent_rsi.min() < 40):  # RSI oversold bölgede olmalı
            signal = "BUY"
            desc = f"Katı Bullish RSI Divergence. Price LL, RSI HL. RSI={recent_rsi.min():.1f}"
        elif (recent.max() > earlier.max() and 
              recent_rsi.max() < earlier_rsi.max() and
              recent_rsi.max() > 60):  # RSI overbought bölgede olmalı
            signal = "SELL"
            desc = f"Katı Bearish RSI Divergence. Price HH, RSI LH. RSI={recent_rsi.max():.1f}"
        else:
            signal = "NEUTRAL"
            desc = "Katı RSI diverjansı tespit edilmedi."

        return {
            "signal": signal,
            "rsi": round(float(rsi.iloc[-1]), 2),
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(RSIDivergenceStrict().run(prices))
