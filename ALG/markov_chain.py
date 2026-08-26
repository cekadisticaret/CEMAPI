"""
markov_chain.py
Markov Zinciri: Fiyat hareket durumları arasındaki geçiş olasılıkları.
"""
import pandas as pd
import numpy as np
from typing import Dict
from collections import defaultdict

class MarkovChain:
    def __init__(self, n_states: int = 3, lookback: int = 100):
        self.n_states = n_states
        self.lookback = lookback
        self.transition_matrix = None
        self.states = ["DOWN", "SIDE", "UP"]

    def _discretize(self, returns: pd.Series) -> pd.Series:
        """Getiriyi durumlara ayırır."""
        std = returns.std()
        conditions = [
            returns < -0.5 * std,
            (returns >= -0.5 * std) & (returns <= 0.5 * std),
            returns > 0.5 * std
        ]
        return pd.Series(np.select(conditions, [0, 1, 2], default=1), index=returns.index)

    def fit(self, prices: pd.Series) -> "MarkovChain":
        returns = prices.pct_change().dropna()
        states = self._discretize(returns.iloc[-self.lookback:])

        # Geçiş matrisi
        trans = defaultdict(lambda: defaultdict(int))
        for i in range(len(states) - 1):
            trans[states.iloc[i]][states.iloc[i+1]] += 1

        # Normalize
        matrix = np.zeros((self.n_states, self.n_states))
        for i in range(self.n_states):
            total = sum(trans[i].values())
            if total > 0:
                for j in range(self.n_states):
                    matrix[i][j] = trans[i][j] / total

        self.transition_matrix = matrix
        return self

    def predict(self, prices: pd.Series) -> Dict:
        if self.transition_matrix is None:
            self.fit(prices)

        returns = prices.pct_change().dropna()
        current_state = int(self._discretize(returns).iloc[-1])

        probs = self.transition_matrix[current_state]
        next_state = np.argmax(probs)

        state_names = {0: "DOWN", 1: "SIDE", 2: "UP"}

        return {
            "signal": "BUY" if next_state == 2 else "SELL" if next_state == 0 else "NEUTRAL",
            "current_state": state_names[current_state],
            "predicted_state": state_names[next_state],
            "probabilities": {
                "DOWN": f"{probs[0]:.1%}",
                "SIDE": f"{probs[1]:.1%}",
                "UP": f"{probs[2]:.1%}"
            },
            "transition_matrix": self.transition_matrix.tolist()
        }

    def run(self, prices: pd.Series) -> Dict:
        return self.predict(prices)

if __name__ == "__main__":
    np.random.seed(42)
    prices = pd.Series(100 + np.cumsum(np.random.randn(200) * 2))
    print(MarkovChain().run(prices))
