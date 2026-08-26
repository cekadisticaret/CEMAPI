"""
h1_professional_combo.py
H1 Profesyonel Kombinasyon: EMA + RSI + MACD + ATR multi-sinyal.
"""
import pandas as pd
import numpy as np
from typing import Dict

class H1ProfessionalCombo:
    def __init__(self):
        pass

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"high": high, "low": low, "close": close})

        # EMA 21/55
        df["ema21"] = close.ewm(span=21).mean()
        df["ema55"] = close.ewm(span=55).mean()

        # RSI 14
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        rs = gain.rolling(14).mean() / loss.rolling(14).mean()
        df["rsi"] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # ATR 14
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr"] = tr.rolling(14).mean()

        return df

    def generate_signal(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        df = self.calculate(high, low, close)
        latest = df.iloc[-1]

        score = 0
        reasons = []

        # EMA
        if latest["ema21"] > latest["ema55"]:
            score += 1
            reasons.append("EMA21>EMA55")
        else:
            score -= 1
            reasons.append("EMA21<EMA55")

        # RSI
        if 40 < latest["rsi"] < 60:
            score += 0
            reasons.append("RSI neutral")
        elif latest["rsi"] > 60:
            score += 1
            reasons.append("RSI>60")
        else:
            score -= 1
            reasons.append("RSI<40")

        # MACD
        if latest["macd"] > latest["macd_signal"] and latest["macd_hist"] > 0:
            score += 1
            reasons.append("MACD bullish")
        elif latest["macd"] < latest["macd_signal"]:
            score -= 1
            reasons.append("MACD bearish")

        # ATR (volatilite uygun mu?)
        atr_pct = latest["atr"] / latest["close"]
        if 0.005 < atr_pct < 0.03:
            score += 0.5
            reasons.append("ATR normal")

        if score >= 2:
            signal = "BUY"
        elif score <= -2:
            signal = "SELL"
        else:
            signal = "NEUTRAL"

        return {
            "signal": signal,
            "score": round(score, 1),
            "rsi": round(float(latest["rsi"]), 1),
            "macd_hist": round(float(latest["macd_hist"]), 4),
            "ema_diff": f"{(latest['ema21']/latest['ema55']-1):.2%}",
            "atr_pct": f"{atr_pct:.2%}",
            "reasons": reasons
        }

    def run(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        return self.generate_signal(high, low, close)

if __name__ == "__main__":
    np.random.seed(42)
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2))
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    print(H1ProfessionalCombo().run(high, low, close))
