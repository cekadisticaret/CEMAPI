"""
lstm_predictor.py
Basit LSTM Fiyat Tahmini. (TensorFlow gerektirir, mock versiyon da sunulur.)
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional

class LSTMPredictor:
    def __init__(self, lookback: int = 60, forecast: int = 5):
        self.lookback = lookback
        self.forecast = forecast
        self.model = None

    def _create_sequences(self, data: np.ndarray):
        X, y = [], []
        for i in range(len(data) - self.lookback - self.forecast + 1):
            X.append(data[i:i+self.lookback])
            y.append(data[i+self.lookback:i+self.lookback+self.forecast])
        return np.array(X), np.array(y)

    def train(self, prices: pd.Series) -> "LSTMPredictor":
        try:
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense

            data = prices.values.reshape(-1, 1)
            # Normalize
            self.mean = data.mean()
            self.std = data.std()
            norm_data = (data - self.mean) / self.std

            X, y = self._create_sequences(norm_data.flatten())
            X = X.reshape((X.shape[0], X.shape[1], 1))

            self.model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(self.lookback, 1)),
                LSTM(50),
                Dense(self.forecast)
            ])
            self.model.compile(optimizer="adam", loss="mse")
            self.model.fit(X, y, epochs=10, batch_size=32, verbose=0)

        except ImportError:
            print("TensorFlow yüklü değil. Mock tahmin kullanılıyor.")
            self.model = "mock"

        return self

    def predict(self, prices: pd.Series) -> Dict:
        if self.model is None:
            self.train(prices)

        last_sequence = prices.iloc[-self.lookback:].values.reshape(-1, 1)

        if self.model == "mock":
            # Basit lineer trend extrapolation
            returns = np.diff(last_sequence.flatten())
            avg_return = np.mean(returns[-10:])
            predictions = [last_sequence[-1][0] + avg_return * (i+1) for i in range(self.forecast)]
        else:
            norm_seq = (last_sequence - self.mean) / self.std
            X = norm_seq.reshape(1, self.lookback, 1)
            pred = self.model.predict(X, verbose=0)
            predictions = (pred[0] * self.std + self.mean).tolist()

        current = prices.iloc[-1]
        predicted_change = (predictions[-1] - current) / current

        if predicted_change > 0.02:
            signal = "BUY"
        elif predicted_change < -0.02:
            signal = "SELL"
        else:
            signal = "NEUTRAL"

        return {
            "signal": signal,
            "current_price": round(float(current), 2),
            "predicted_prices": [round(float(p), 2) for p in predictions],
            "predicted_change": f"{predicted_change:.2%}",
            "model": "LSTM" if self.model != "mock" else "Mock_Linear"
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.predict(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(200) * 2))
    print(LSTMPredictor().run(prices))
