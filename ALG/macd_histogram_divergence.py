"""
macd_histogram_divergence.py
MACD Histogram Divergence: Histogram ile fiyat arasındaki uyumsuzluk.
"""
import pandas as pd
import numpy as np
from typing import Dict

class MACDHistogramDivergence:
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9, lookback: int = 20):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.lookback = lookback

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        ema_fast = prices.ewm(span=self.fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=self.signal, adjust=False).mean()
        hist = macd - signal_line

        df = pd.DataFrame({
            "price": prices,
            "macd": macd,
            "signal": signal_line,
            "hist": hist
        })
        return df

    def find_hist_divergence(self, df: pd.DataFrame) -> str:
        if len(df) < self.lookback * 2:
            return "NO_DATA"

        recent = df.iloc[-self.lookback:]
        earlier = df.iloc[-self.lookback*2:-self.lookback]

        # Bullish: price lower low, hist higher low
        if (recent["price"].min() < earlier["price"].min() and 
            recent["hist"].min() > earlier["hist"].min()):
            return "BULLISH_HIST_DIV"

        # Bearish: price higher high, hist lower high
        if (recent["price"].max() > earlier["price"].max() and 
            recent["hist"].max() < earlier["hist"].max()):
            return "BEARISH_HIST_DIV"

        return "NO_DIVERGENCE"

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        div = self.find_hist_divergence(df)
        latest = df.iloc[-1]

        if div == "BULLISH_HIST_DIV":
            signal = "BUY"
            desc = "Bullish MACD histogram divergence."
        elif div == "BEARISH_HIST_DIV":
            signal = "SELL"
            desc = "Bearish MACD histogram divergence."
        elif latest["hist"] > 0 and latest["hist"] > df["hist"].iloc[-2]:
            signal = "HOLD_LONG"
            desc = "Histogram pozitif ve genişliyor."
        elif latest["hist"] < 0 and latest["hist"] < df["hist"].iloc[-2]:
            signal = "HOLD_SHORT"
            desc = "Histogram negatif ve derinleşiyor."
        else:
            signal = "NEUTRAL"
            desc = "Histogram daralıyor."

        return {
            "signal": signal,
            "macd": round(float(latest["macd"]), 4),
            "hist": round(float(latest["hist"]), 4),
            "divergence": div,
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    print(MACDHistogramDivergence().run(prices))
