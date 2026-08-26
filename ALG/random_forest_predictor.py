"""
random_forest_predictor.py
Random Forest Classifier: Teknik göstergelerden fiyat yönü tahmini.
"""
import pandas as pd
import numpy as np
from typing import Dict

class RandomForestPredictor:
    def __init__(self, lookback: int = 20, n_estimators: int = 100):
        self.lookback = lookback
        self.n_estimators = n_estimators
        self.model = None

    def _engineer_features(self, prices: pd.Series) -> pd.DataFrame:
        """Teknik göstergelerden feature seti oluşturur."""
        df = pd.DataFrame({"price": prices})
        df["returns"] = prices.pct_change()
        df["sma_10"] = prices.rolling(10).mean()
        df["sma_30"] = prices.rolling(30).mean()
        df["rsi"] = self._rsi(prices, 14)
        df["volatility"] = df["returns"].rolling(20).std()
        df["momentum"] = prices.diff(5)
        df["ema_12"] = prices.ewm(span=12).mean()
        df["ema_26"] = prices.ewm(span=26).mean()
        df["macd"] = df["ema_12"] - df["ema_26"]

        # Target: sonraki 5 periyotta yükselirse 1, düşerse 0
        df["target"] = np.where(prices.shift(-5) > prices, 1, 0)
        return df.dropna()

    def _rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def train(self, prices: pd.Series) -> "RandomForestPredictor":
        try:
            from sklearn.ensemble import RandomForestClassifier
            df = self._engineer_features(prices)

            features = ["returns", "volatility", "momentum", "rsi", "macd"]
            X = df[features].values
            y = df["target"].values

            self.model = RandomForestClassifier(n_estimators=self.n_estimators, random_state=42)
            self.model.fit(X, y)
            self.features = features
        except ImportError:
            print("scikit-learn yüklü değil. Mock model kullanılıyor.")
            self.model = "mock"
        return self

    def predict(self, prices: pd.Series) -> Dict:
        if self.model is None:
            self.train(prices)

        df = self._engineer_features(prices)
        latest = df.iloc[-1]

        if self.model == "mock":
            prob = 0.5 + (latest["momentum"] / prices.iloc[-1]) * 10
            prob = max(0, min(1, prob))
            pred = 1 if prob > 0.5 else 0
        else:
            X = latest[self.features].values.reshape(1, -1)
            pred = self.model.predict(X)[0]
            prob = self.model.predict_proba(X)[0][pred]

        signal = "BUY" if pred == 1 else "SELL"

        return {
            "signal": signal,
            "confidence": f"{prob:.1%}",
            "price": round(float(prices.iloc[-1]), 2),
            "model": "RandomForest" if self.model != "mock" else "Mock"
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.predict(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(200) * 2))
    print(RandomForestPredictor().run(prices))
