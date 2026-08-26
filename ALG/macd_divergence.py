"""
macd_divergence.py
MACD + Fiyat Diverjansı: MACD ile fiyat arasındaki uyumsuzlukları tespit eder.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple

class MACDDivergence:
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9, lookback: int = 20):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.lookback = lookback

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices})
        ema_fast = prices.ewm(span=self.fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow, adjust=False).mean()
        df["macd"] = ema_fast - ema_slow
        df["signal"] = df["macd"].ewm(span=self.signal, adjust=False).mean()
        df["hist"] = df["macd"] - df["signal"]
        return df

    def find_divergence(self, df: pd.DataFrame) -> str:
        """Bullish/Bearish divergence tespiti."""
        p = df["price"].values
        h = df["hist"].values
        n = len(df)

        # Son lookback periyodunda local min/max bul
        if n < self.lookback + 5:
            return "NO_DATA"

        recent = df.iloc[-self.lookback:]

        # Bullish divergence: fiyat lower low, MACD higher low
        price_low_idx = recent["price"].idxmin()
        price_low = recent["price"].min()
        hist_at_price_low = df.loc[price_low_idx, "hist"]

        # Önceki dönemdeki low ile karşılaştır
        earlier = df.iloc[-self.lookback*2:-self.lookback]
        if len(earlier) > 0:
            prev_price_low = earlier["price"].min()
            prev_hist_low_idx = earlier["hist"].idxmin()
            prev_hist_low = earlier["hist"].min()

            if price_low < prev_price_low and hist_at_price_low > prev_hist_low:
                return "BULLISH_DIVERGENCE"
            if price_low > prev_price_low and hist_at_price_low < prev_hist_low:
                return "BEARISH_DIVERGENCE"

        return "NO_DIVERGENCE"

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        div = self.find_divergence(df)

        if div == "BULLISH_DIVERGENCE":
            signal = "BUY"
            desc = "Bullish divergence: Fiyat düşerken MACD yükseliyor."
        elif div == "BEARISH_DIVERGENCE":
            signal = "SELL"
            desc = "Bearish divergence: Fiyat yükselirken MACD düşüyor."
        elif latest["macd"] > latest["signal"]:
            signal = "HOLD_LONG"
            desc = "MACD signal üzerinde."
        else:
            signal = "HOLD_SHORT"
            desc = "MACD signal altında."

        return {
            "signal": signal,
            "macd": round(float(latest["macd"]), 4),
            "signal_line": round(float(latest["signal"]), 4),
            "histogram": round(float(latest["hist"]), 4),
            "divergence": div,
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(MACDDivergence().run(prices))
