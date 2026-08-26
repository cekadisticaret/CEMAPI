"""
multi_timeframe.py
Multi-Timeframe Analiz: Birden fazla zaman diliminde sinyal birleştirme.
"""
import pandas as pd
import numpy as np
from typing import Dict, List

class MultiTimeframe:
    def __init__(self, timeframes: List[str] = None):
        self.timeframes = timeframes or ["15m", "1h", "4h", "1d"]

    def aggregate_signal(self, signals: Dict[str, str]) -> Dict:
        """Farklı TF'lerden gelen sinyalleri birleştirir."""
        score = 0
        weights = {"15m": 0.1, "1h": 0.2, "4h": 0.3, "1d": 0.4}

        for tf, sig in signals.items():
            w = weights.get(tf, 0.25)
            if "BUY" in sig or "LONG" in sig:
                score += w
            elif "SELL" in sig or "SHORT" in sig:
                score -= w

        if score >= 0.6:
            signal = "STRONG_BUY"
        elif score >= 0.3:
            signal = "BUY"
        elif score <= -0.6:
            signal = "STRONG_SELL"
        elif score <= -0.3:
            signal = "SELL"
        else:
            signal = "NEUTRAL"

        return {
            "signal": signal,
            "consensus_score": round(score, 3),
            "timeframe_signals": signals,
            "description": f"Multi-TF consensus: {score:.2f}"
        }

    def run(self, signals: Dict[str, str]) -> Dict:
        return self.aggregate_signal(signals)

if __name__ == "__main__":
    signals = {
        "15m": "BUY",
        "1h": "BUY",
        "4h": "NEUTRAL",
        "1d": "BUY"
    }
    print(MultiTimeframe().run(signals))
