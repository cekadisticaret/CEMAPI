"""
keltner_channel.py
Keltner Channels: EMA + ATR bazlı volatilite kanalları.
"""
import pandas as pd
import numpy as np
from typing import Dict

class KeltnerChannel:
    def __init__(self, ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0):
        self.ema_period = ema_period
        self.atr_period = atr_period
        self.multiplier = multiplier

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # EMA
        df["ema"] = close.ewm(span=self.ema_period, adjust=False).mean()

        # ATR
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr"] = tr.rolling(window=self.atr_period).mean()

        # Keltner Channels
        df["upper"] = df["ema"] + self.multiplier * df["atr"]
        df["lower"] = df["ema"] - self.multiplier * df["atr"]

        return df

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]

        price = latest["close"]
        upper = latest["upper"]
        lower = latest["lower"]
        ema = latest["ema"]

        if price > upper:
            signal = "OVERBOUGHT"
            desc = f"Fiyat üst kanal üzerinde. Aşırı alım."
        elif price < lower:
            signal = "OVERSOLD"
            desc = f"Fiyat alt kanal altında. Aşırı satım."
        elif price > ema:
            signal = "BULLISH"
            desc = "Fiyat EMA ve kanal ortasında, üst yarıda."
        else:
            signal = "BEARISH"
            desc = "Fiyat EMA ve kanal ortasında, alt yarıda."

        return {
            "signal": signal,
            "upper": round(float(upper), 2),
            "lower": round(float(lower), 2),
            "ema": round(float(ema), 2),
            "price": round(float(price), 2),
            "description": desc
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(KeltnerChannel().run(high, low, close))
