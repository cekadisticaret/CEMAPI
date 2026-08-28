"""
connors_rsi2.py
Connors RSI(2) Mean Reversion: Kisa bakisli RSI ile asiri bolgelerden
donus yakalar. Trend filtresi ve hizli cikis ile kullanilir.
"""
import pandas as pd
import numpy as np
from typing import Dict

class ConnorsRSI2:
    def __init__(self, rsi_period: int = 2, oversold: int = 10, overbought: int = 90,
                 trend_filter_period: int = 200):
        """
        Args:
            rsi_period: RSI periyodu (Connors klasigi = 2)
            oversold: Asiri satim esigi
            overbought: Asiri alim esigi
            trend_filter_period: Trend filtresi (EMA)
        """
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.trend_filter_period = trend_filter_period

    def _rsi(self, prices: pd.Series, period: int) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"price": prices})
        df["rsi2"] = self._rsi(prices, self.rsi_period)
        df["ema_trend"] = prices.ewm(span=self.trend_filter_period).mean()
        df["trend_up"] = prices > df["ema_trend"]
        df["prev_high"] = prices.shift(1)
        return df

    def generate_signal(self, prices: pd.Series) -> Dict:
        df = self.calculate(prices)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        rsi = latest["rsi2"]
        trend_up = latest["trend_up"]
        price = latest["price"]
        prev_high = latest["prev_high"]

        if pd.isna(rsi):
            return {"signal": "NO_DATA"}

        # Connors kurallari:
        # 1. RSI(2) < 10 + trend up -> al
        # 2. RSI(2) > 90 veya onceki gunun yuksegi kirildi -> sat

        if rsi < self.oversold and trend_up:
            signal = "BUY"
            desc = f"RSI(2)={rsi:.0f} < {self.oversold}, uptrend. Mean reversion long."
        elif rsi > self.overbought:
            signal = "SELL"
            desc = f"RSI(2)={rsi:.0f} > {self.overbought}. Asiri alim, cikis."
        elif price > prev_high and prev["rsi2"] < self.overbought:
            signal = "SELL"
            desc = f"Onceki bar yuksegi kirildi. Hizli cikis."
        elif rsi < self.oversold:
            signal = "OVERSOLD"
            desc = f"RSI(2)={rsi:.0f}. Trend filtreli degil, bekleyin."
        elif rsi > self.overbought - 10:
            signal = "OVERBOUGHT"
            desc = f"RSI(2)={rsi:.0f}. Yakinda cikis dusunulebilir."
        else:
            signal = "NEUTRAL"
            desc = f"RSI(2)={rsi:.0f}. Tarafsiz."

        return {
            "signal": signal,
            "rsi2": round(float(rsi), 1),
            "trend": "UP" if trend_up else "DOWN",
            "price": round(float(price), 2),
            "description": desc
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.generate_signal(prices)


if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(300) * 2))
    print(ConnorsRSI2().run(prices))
