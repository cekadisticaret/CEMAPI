"""
trading_orchestrator.py
===============================================================================
Kripto Trading Algoritma Birleştirici (Orchestrator)
===============================================================================
53 bağımsiz algoritmayi calistirir, kategorilere gore agirliklandirir,
final consensus sinyali uretir ve risk yonetimi uygular.

Kullanim:
    from trading_orchestrator import TradingEngine

    engine = TradingEngine()
    result = engine.run_full_analysis(
        prices=price_series,
        high=high_series,
        low=low_series,
        close=close_series,
        volume=volume_series,
        oi=oi_series,
        open_prices=open_series
    )
    print(result["final_signal"])
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import importlib
import sys
import os

_ALG_DIR = os.path.dirname(os.path.abspath(__file__))
if _ALG_DIR not in sys.path:
    sys.path.insert(0, _ALG_DIR)

_SKIP_MODULES = {
    "mvrv_zscore", "sopr_indicator", "funding_arbitrage",
    "oi_liquidation_analyzer", "oi_divergence", "pairs_trading",
    "multi_timeframe", "fear_greed_index", "lstm_predictor",
    "random_forest_predictor", "grid_bot", "hmm_regime_detector",
}

# ===============================================================================
# 1. SINYAL SOZLUGU
# ===============================================================================

SIGNAL_MAP = {
    "STRONG_BUY": 1.0, "BUY": 0.8, "BOUNCE_SUPPORT": 0.8,
    "BREAKOUT_UP": 0.9, "BULLISH": 0.6, "HOLD_LONG": 0.4,
    "BULLISH_DIVERGENCE": 0.85, "BULLISH_OI_DIV": 0.7,
    "BULLISH_HIST_DIV": 0.85, "ACCUMULATION": 0.9,
    "CAPITULATION_BUY": 0.9, "OVERSOLD": 0.7, "GOLDEN_ZONE": 0.8,
    "SWEEP_LOW": 0.85, "SQUEEZE_END": 0.5, "TRENDING": 0.3,
    "SETUP_LONG": 0.5, "LONG_SPREAD": 0.6, "ABOVE_POC": 0.4,
    "ABOVE_VALUE": 0.3, "STRONG_TREND_UP": 0.8, "WEAK_UP": 0.3,
    "EXTREME_FEAR": 0.9, "FEAR": 0.5, "SAR_BULLISH": 0.6,
    "TK_CROSS_BULLISH": 0.7, "UP": 0.3, "TREND": 0.4,
    "RANGE": 0.0, "VOLATILE": -0.1,

    "STRONG_SELL": -1.0, "SELL": -0.8, "REJECT_RESISTANCE": -0.8,
    "BREAKOUT_DOWN": -0.9, "BEARISH": -0.6, "HOLD_SHORT": -0.4,
    "BEARISH_DIVERGENCE": -0.85, "BEARISH_OI_DIV": -0.7,
    "BEARISH_HIST_DIV": -0.85, "OVERVALUED": -0.7,
    "PROFIT_TAKING": -0.6, "OVERBOUGHT": -0.7,
    "SWEEP_HIGH": -0.85, "SQUEEZE_START": -0.2,
    "MEAN_REVERTING": -0.3, "SETUP_SHORT": -0.5,
    "SHORT_SPREAD": -0.6, "BELOW_POC": -0.4,
    "BELOW_VALUE": -0.3, "STRONG_TREND_DOWN": -0.8,
    "WEAK_DOWN": -0.3, "EXTREME_GREED": -0.9,
    "GREED": -0.5, "SAR_BEARISH": -0.6,
    "TK_CROSS_BEARISH": -0.7, "DOWN": -0.3,
    "NO_TREND": 0.0, "RANDOM_WALK": 0.0,

    "NEUTRAL": 0.0, "HOLD": 0.0, "NO_DATA": 0.0,
    "NO_TRADE": 0.0, "NO_SQUEEZE": 0.0, "SQUEEZE": 0.0,
    "NO_SWEEP": 0.0, "N/A": 0.0, "EXIT": 0.0,
    "IN_RANGE": 0.0, "SQUEEZE_ON": 0.0, "LIQUIDATION_RISK": -0.3,
    "CONFIRMED_UP": 0.3, "CAUTION": -0.2, "EXTREME_RISK": -0.9,
    "382_ZONE": 0.0, "NEAR_HIGH": -0.2, "NEAR_LOW": 0.2,
}

# ===============================================================================
# 2. ALGORITMA KAYIT DEFTERI
# ===============================================================================

@dataclass
class AlgorithmMeta:
    name: str
    module: str
    category: str
    weight: float
    needs_ohlc: bool = False
    needs_volume: bool = False
    needs_oi: bool = False
    needs_open: bool = False
    needs_two_series: bool = False

ALGORITHMS = [
    AlgorithmMeta("MVRV_ZScore", "mvrv_zscore", "onchain", 0.08),
    AlgorithmMeta("SOPR", "sopr_indicator", "onchain", 0.07),

    AlgorithmMeta("OI_Liquidation", "oi_liquidation_analyzer", "market_structure", 0.05),
    AlgorithmMeta("OI_Divergence", "oi_divergence", "market_structure", 0.03),
    AlgorithmMeta("Fear_Greed", "fear_greed_index", "sentiment", 0.02),

    AlgorithmMeta("EMA_Cross", "ema_crossover", "trend", 0.025),
    AlgorithmMeta("TEMA_Cross", "tema_crossover", "trend", 0.025),
    AlgorithmMeta("Triple_EMA", "triple_ema", "trend", 0.025),
    AlgorithmMeta("Hull_MA", "hull_ma", "trend", 0.025),
    AlgorithmMeta("Supertrend", "supertrend", "trend", 0.025, needs_ohlc=True),
    AlgorithmMeta("Supertrend_v2", "supertrend_v2", "trend", 0.025, needs_ohlc=True),
    AlgorithmMeta("Parabolic_SAR_ADX", "parabolic_sar_adx", "trend", 0.025, needs_ohlc=True),
    AlgorithmMeta("ADX_Regime", "adx_regime", "trend", 0.025, needs_ohlc=True),
    AlgorithmMeta("Ichimoku", "ichimoku_cloud", "trend", 0.025, needs_ohlc=True),
    AlgorithmMeta("Ichimoku_v2", "ichimoku_cloud_v2", "trend", 0.025, needs_ohlc=True),
    AlgorithmMeta("Heikin_Ashi", "heikin_ashi", "trend", 0.02, needs_ohlc=True, needs_open=True),
    AlgorithmMeta("KAMA", "kama_indicator", "trend", 0.025),
    AlgorithmMeta("ATR_Breakout", "atr_breakout", "trend", 0.02, needs_ohlc=True),
    AlgorithmMeta("Donchian", "donchian_channel", "trend", 0.02, needs_ohlc=True),

    AlgorithmMeta("MACD_Div", "macd_divergence", "momentum", 0.02),
    AlgorithmMeta("MACD_Hist_Div", "macd_histogram_divergence", "momentum", 0.02),
    AlgorithmMeta("RSI_Div", "rsi_divergence", "momentum", 0.02),
    AlgorithmMeta("RSI_Div_Strict", "rsi_divergence_strict", "momentum", 0.02),
    AlgorithmMeta("StochRSI", "stochastic_rsi", "momentum", 0.015),
    AlgorithmMeta("StochRSI_KD", "stoch_rsi_kd", "momentum", 0.015),
    AlgorithmMeta("StochRSI_14_KD", "stochastic_rsi_14_kd", "momentum", 0.015),
    AlgorithmMeta("Schaff_TC", "schaff_trend_cycle", "momentum", 0.015),
    AlgorithmMeta("Williams_R", "williams_r", "momentum", 0.015, needs_ohlc=True),
    AlgorithmMeta("CCI", "cci", "momentum", 0.015, needs_ohlc=True),
    AlgorithmMeta("MFI", "money_flow_index", "momentum", 0.015, needs_ohlc=True, needs_volume=True),
    AlgorithmMeta("Bollinger", "bollinger_bands", "momentum", 0.015),
    AlgorithmMeta("Bollinger_Squeeze", "bollinger_squeeze", "momentum", 0.01),
    AlgorithmMeta("Keltner", "keltner_channel", "momentum", 0.01, needs_ohlc=True),
    AlgorithmMeta("Squeeze_Momentum", "squeeze_momentum", "momentum", 0.015, needs_ohlc=True),
    AlgorithmMeta("H1_Combo", "h1_professional_combo", "momentum", 0.02, needs_ohlc=True),

    AlgorithmMeta("OBV", "obv", "volume", 0.025, needs_volume=True),
    AlgorithmMeta("VWAP", "vwap", "volume", 0.025, needs_volume=True),
    AlgorithmMeta("VWAP_VP", "vwap_volume_profile", "volume", 0.025, needs_volume=True),
    AlgorithmMeta("Volume_Profile", "volume_profile", "volume", 0.025, needs_volume=True),
    AlgorithmMeta("Liquidity_Sweep", "liquidity_sweep_proxy", "volume", 0.02, needs_ohlc=True),

    AlgorithmMeta("MeanRev_ZScore", "mean_reversion_zscore", "mean_reversion", 0.03),
    AlgorithmMeta("Hurst_Proxy", "hurst_proxy", "mean_reversion", 0.02),
    AlgorithmMeta("Range_SR", "range_trading_sr", "mean_reversion", 0.02, needs_ohlc=True),
    AlgorithmMeta("Fibonacci", "fibonacci_retracement", "mean_reversion", 0.01, needs_ohlc=True),

    AlgorithmMeta("HMM_Regime", "hmm_regime_detector", "ml_stat", 0.025),
    AlgorithmMeta("Markov_Chain", "markov_chain", "ml_stat", 0.015),
    AlgorithmMeta("Random_Forest", "random_forest_predictor", "ml_stat", 0.02),
    AlgorithmMeta("LSTM", "lstm_predictor", "ml_stat", 0.02),
    AlgorithmMeta("Pairs_Trading", "pairs_trading", "ml_stat", 0.02, needs_two_series=True),

    AlgorithmMeta("Funding_Arb", "funding_arbitrage", "delta_neutral", 0.03),
    AlgorithmMeta("Chandelier_Exit", "chandelier_exit", "risk", 0.03, needs_ohlc=True),
    AlgorithmMeta("Grid_Bot", "grid_bot", "delta_neutral", 0.03),
    AlgorithmMeta("Multi_TF", "multi_timeframe", "risk", 0.02),
]

CATEGORY_CAPS = {
    "onchain": 0.15, "market_structure": 0.10, "sentiment": 0.05,
    "trend": 0.25, "momentum": 0.20, "volume": 0.12,
    "mean_reversion": 0.08, "ml_stat": 0.10, "delta_neutral": 0.05, "risk": 0.05,
}


# ===============================================================================
# 3. ALGORITMA YUKLEYICI
# ===============================================================================

class AlgorithmLoader:
    _cache = {}

    @classmethod
    def load(cls, meta: AlgorithmMeta):
        if meta.name in cls._cache:
            return cls._cache[meta.name]

        try:
            module = importlib.import_module(meta.module)
            special_names = {
                "mvrv_zscore": "MVRVZScore", "sopr_indicator": "SOPRIndicator",
                "oi_liquidation_analyzer": "OILiquidationAnalyzer",
                "fear_greed_index": "FearGreedIndex", "ema_crossover": "EMACrossover",
                "macd_divergence": "MACDDivergence", "rsi_divergence": "RSIDivergence",
                "stochastic_rsi": "StochasticRSI", "bollinger_bands": "BollingerBands",
                "volume_profile": "VolumeProfile", "mean_reversion_zscore": "MeanReversionZScore",
                "pairs_trading": "PairsTrading", "grid_bot": "GridBot",
                "lstm_predictor": "LSTMPredictor", "multi_timeframe": "MultiTimeframe",
                "atr_breakout": "ATRBreakout", "heikin_ashi": "HeikinAshi",
                "tema_crossover": "TEMACrossover", "adx_regime": "ADXRegime",
                "oi_divergence": "OIDivergence", "parabolic_sar_adx": "ParabolicSARADX",
                "macd_histogram_divergence": "MACDHistogramDivergence",
                "stoch_rsi_kd": "StochRSIKD", "triple_ema": "TripleEMA",
                "hull_ma": "HullMA", "keltner_channel": "KeltnerChannel",
                "donchian_channel": "DonchianChannel", "vwap_volume_profile": "VWAPVolumeProfile",
                "money_flow_index": "MoneyFlowIndex", "random_forest_predictor": "RandomForestPredictor",
                "markov_chain": "MarkovChain", "supertrend_v2": "SuperTrendV2",
                "ichimoku_cloud_v2": "IchimokuCloudV2", "rsi_divergence_strict": "RSIDivergenceStrict",
                "h1_professional_combo": "H1ProfessionalCombo", "liquidity_sweep_proxy": "LiquiditySweepProxy",
                "schaff_trend_cycle": "SchaffTrendCycle", "hurst_proxy": "HurstProxy",
                "williams_r": "WilliamsR", "squeeze_momentum": "SqueezeMomentum",
                "fibonacci_retracement": "FibonacciRetracement", "range_trading_sr": "RangeTradingSR",
                "cci": "CCIIndicator", "stochastic_rsi_14_kd": "StochasticRSI14KD",
                "bollinger_squeeze": "BollingerSqueeze", "supertrend": "Supertrend",
                "ichimoku_cloud": "IchimokuCloud", "vwap": "VWAPIndicator",
                "obv": "OBVIndicator", "kama_indicator": "KAMAIndicator",
                "chandelier_exit": "ChandelierExit", "hmm_regime_detector": "HMMRegimeDetector",
                "funding_arbitrage": "FundingArbitrage",
            }
            class_name = special_names.get(meta.module, "".join([p.capitalize() for p in meta.module.split("_")]))
            cls_obj = getattr(module, class_name)
            instance = cls_obj()
            cls._cache[meta.name] = instance
            return instance
        except Exception as e:
            print(f"[!] {meta.name} yuklenemedi: {e}")
            cls._cache[meta.name] = None
            return None

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()


# ===============================================================================
# 4. SINYAL CIKARICI
# ===============================================================================

class SignalExtractor:
    @staticmethod
    def extract(alg: AlgorithmMeta, data: Dict[str, Any]) -> Dict:
        instance = AlgorithmLoader.load(alg)
        if instance is None:
            return {"signal": "NO_DATA", "score": 0.0, "error": "LOAD_FAILED"}

        try:
            if alg.needs_two_series:
                if "series2" in data:
                    result = instance.run(data["prices"], data["series2"])
                else:
                    return {"signal": "NO_DATA", "score": 0.0, "error": "NEEDS_SERIES2"}
            elif alg.needs_ohlc and alg.needs_open:
                result = instance.run(data["open_prices"], data["high"], data["low"], data["close"])
            elif alg.needs_ohlc and alg.needs_volume:
                result = instance.run(data["high"], data["low"], data["close"], data["volume"])
            elif alg.needs_ohlc:
                result = instance.run(data["high"], data["low"], data["close"])
            elif alg.needs_volume:
                ts = data.get("timestamps")
                if ts is not None:
                    result = instance.run(data["prices"], data["volume"], ts)
                else:
                    result = instance.run(data["prices"], data["volume"])
            elif alg.name == "Fear_Greed":
                result = instance.run()
            elif alg.name == "Funding_Arb":
                result = instance.run()
            elif alg.name == "Grid_Bot":
                result = instance.run(data["close"].iloc[-1], data["close"])
            elif alg.name == "Multi_TF":
                result = instance.run(data.get("tf_signals", {}))
            else:
                result = instance.run(data["prices"])

            raw_signal = result.get("signal", "NEUTRAL")
            score = SIGNAL_MAP.get(raw_signal, 0.0)

            return {
                "signal": raw_signal, "score": score, "raw": result,
                "category": alg.category, "weight": alg.weight, "name": alg.name
            }
        except Exception as e:
            return {"signal": "ERROR", "score": 0.0, "error": str(e), "name": alg.name}


# ===============================================================================
# 5. AGIRLIKLI KONSENSUS MOTORU
# ===============================================================================

class ConsensusEngine:
    def __init__(self, category_caps: Dict[str, float] = None):
        self.caps = category_caps or CATEGORY_CAPS

    def calculate(self, signals: List[Dict]) -> Dict:
        if not signals:
            return {"score": 0.0, "direction": "NEUTRAL", "confidence": 0.0}

        category_scores = defaultdict(list)
        category_weights = defaultdict(list)

        for sig in signals:
            cat = sig.get("category", "unknown")
            category_scores[cat].append(sig["score"])
            category_weights[cat].append(sig.get("weight", 0.01))

        category_contrib = {}
        for cat, scores in category_scores.items():
            weights = category_weights[cat]
            weighted_avg = np.average(scores, weights=weights)
            cap = self.caps.get(cat, 0.1)
            category_contrib[cat] = np.clip(weighted_avg, -cap, cap)

        total_score = sum(category_contrib.values())
        max_possible = sum(self.caps.get(cat, 0.1) for cat in category_contrib) or sum(self.caps.values())
        normalized = np.clip(total_score / max_possible, -1.0, 1.0)

        non_neutral = [s for s in signals if abs(s["score"]) > 0.1]
        if non_neutral:
            agreement = len([s for s in non_neutral if s["score"] * normalized > 0]) / len(non_neutral)
            confidence = agreement * min(len(non_neutral) / 10, 1.0)
        else:
            confidence = 0.0

        if normalized > 0.5:
            direction = "STRONG_BUY"
        elif normalized > 0.2:
            direction = "BUY"
        elif normalized < -0.5:
            direction = "STRONG_SELL"
        elif normalized < -0.2:
            direction = "SELL"
        else:
            direction = "NEUTRAL"

        return {
            "score": round(float(normalized), 4),
            "direction": direction,
            "confidence": round(float(confidence), 2),
            "category_breakdown": {k: round(float(v), 4) for k, v in category_contrib.items()},
            "active_signals": len(non_neutral),
            "total_signals": len(signals)
        }


# ===============================================================================
# 6. RISK YONETIMI
# ===============================================================================

class RiskManager:
    def __init__(self, max_risk_pct: float = 0.02, kelly_fraction: float = 0.25):
        self.max_risk_pct = max_risk_pct
        self.kelly_fraction = kelly_fraction

    def calculate_stop(self, high: pd.Series, low: pd.Series, close: pd.Series, position: str = "LONG") -> Dict:
        try:
            from chandelier_exit import ChandelierExit
            ce = ChandelierExit(atr_period=22, multiplier=3.0)
            result = ce.run(high, low, close, position=position)
            return {
                "stop_price": result.get("long_exit" if position == "LONG" else "short_exit"),
                "signal": result.get("signal"),
                "risk_reward": result.get("risk_reward_suggestion")
            }
        except Exception:
            tr1 = high - low
            tr2 = (high - close.shift(1)).abs()
            tr3 = (low - close.shift(1)).abs()
            atr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean().iloc[-1]
            stop = close.iloc[-1] - 2.5 * atr if position == "LONG" else close.iloc[-1] + 2.5 * atr
            return {"stop_price": round(float(stop), 2), "signal": "FALLBACK_STOP"}

    def position_size(self, capital: float, entry: float, stop: float, confidence: float) -> Dict:
        risk_per_trade = self.max_risk_pct * capital
        price_risk = abs(entry - stop) / entry
        if price_risk == 0:
            return {"size": 0, "risk_pct": 0}
        base_size = risk_per_trade / price_risk
        confidence_multiplier = 0.5 + (confidence * 0.5)
        final_size = min(base_size * confidence_multiplier, capital * self.kelly_fraction)
        return {
            "position_size_usd": round(final_size, 2),
            "position_size_pct": f"{final_size/capital:.2%}",
            "risk_amount": round(risk_per_trade, 2),
            "risk_pct": f"{self.max_risk_pct:.2%}",
            "confidence_adjusted": round(confidence_multiplier, 2)
        }


# ===============================================================================
# 7. ANA MOTOR
# ===============================================================================

class TradingEngine:
    def __init__(self, capital: float = 10000.0, category_caps: Dict = None):
        self.capital = capital
        self.consensus = ConsensusEngine(category_caps)
        self.risk = RiskManager()
        self.results_cache = {}

    def run_full_analysis(self, 
                          prices: pd.Series,
                          high: Optional[pd.Series] = None,
                          low: Optional[pd.Series] = None,
                          close: Optional[pd.Series] = None,
                          open_prices: Optional[pd.Series] = None,
                          volume: Optional[pd.Series] = None,
                          oi: Optional[pd.Series] = None,
                          timestamps: Optional[pd.DatetimeIndex] = None,
                          series2: Optional[pd.Series] = None,
                          tf_signals: Optional[Dict] = None,
                          verbose: bool = True) -> Dict:

        if close is None:
            close = prices
        if high is None:
            high = close * (1 + close * 0.00005)
        if low is None:
            low = close * (1 - close * 0.00005)
        if open_prices is None:
            open_prices = close.shift(1).fillna(close.iloc[0])
        if volume is None:
            volume = pd.Series(np.random.randint(1000, 10000, len(close)), index=close.index)
        if oi is None:
            oi = pd.Series(1000000, index=close.index)

        data = {
            "prices": prices, "high": high, "low": low, "close": close,
            "open_prices": open_prices, "volume": volume, "oi": oi,
            "timestamps": timestamps, "series2": series2, "tf_signals": tf_signals or {}
        }

        signals = []
        errors = []

        for meta in ALGORITHMS:
            if meta.module in _SKIP_MODULES or meta.needs_two_series:
                continue
            try:
                sig = SignalExtractor.extract(meta, data)
                if sig.get("signal") not in ("NO_DATA", "ERROR"):
                    signals.append(sig)
                    if verbose:
                        print(f"  [OK] {meta.name:25s} -> {sig['signal']:20s} (score: {sig['score']:+.2f})")
            except Exception as e:
                errors.append({"algo": meta.name, "error": str(e)})
                if verbose:
                    print(f"  [ERR] {meta.name:25s} -> {str(e)[:40]}")

        consensus = self.consensus.calculate(signals)
        position = "LONG" if consensus["score"] > 0 else "SHORT" if consensus["score"] < 0 else "NONE"

        stop_data = {}
        sizing = {}
        if position != "NONE":
            stop_data = self.risk.calculate_stop(high, low, close, position)
            entry = float(close.iloc[-1])
            stop_price = stop_data.get("stop_price", entry * 0.95 if position == "LONG" else entry * 1.05)
            if isinstance(stop_price, (int, float)):
                sizing = self.risk.position_size(self.capital, entry, stop_price, consensus["confidence"])

        regime = "UNKNOWN"
        if verbose:
            try:
                from hmm_regime_detector import HMMRegimeDetector
                hmm = HMMRegimeDetector()
                regime_result = hmm.run(prices)
                regime = regime_result.get("current_regime", "UNKNOWN")
            except Exception:
                pass

        report = {
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "price": round(float(close.iloc[-1]), 2),
            "regime": regime,
            "consensus": consensus,
            "recommendation": {
                "action": consensus["direction"],
                "position": position,
                "confidence": f"{consensus['confidence']:.0%}",
                "score": consensus["score"]
            },
            "risk_management": {
                "stop_loss": stop_data.get("stop_price"),
                "risk_reward": stop_data.get("risk_reward"),
                "position_sizing": sizing
            },
            "signal_breakdown": {
                "bullish": len([s for s in signals if s["score"] > 0.3]),
                "bearish": len([s for s in signals if s["score"] < -0.3]),
                "neutral": len([s for s in signals if abs(s["score"]) <= 0.3]),
                "total": len(signals)
            },
            "category_scores": consensus.get("category_breakdown", {}),
            "all_signals": [{"name": s["name"], "signal": s["signal"], "score": s["score"]} for s in signals],
            "errors": errors
        }

        self.results_cache = report
        return report

    def run(self, prices, high=None, low=None, close=None, volume=None, open_p=None):
        """algo_paper uyumu — BUY/SELL/HOLD."""
        px = close if close is not None else prices
        ts = None
        try:
            ts = pd.date_range(end=pd.Timestamp.utcnow(), periods=len(px), freq="15min")
        except Exception:
            ts = None
        result = self.run_full_analysis(
            prices=prices,
            high=high,
            low=low,
            close=px,
            open_prices=open_p,
            volume=volume,
            timestamps=ts,
            verbose=False,
        )
        cons = result.get("consensus") or {}
        direction = str(cons.get("direction") or "NEUTRAL")
        score = cons.get("score")
        conf = cons.get("confidence")
        trend = float((cons.get("category_breakdown") or {}).get("trend") or 0)
        if direction in ("BUY", "STRONG_BUY") or (
            isinstance(score, (int, float)) and ((score > 0.12) or (trend >= 0.15 and score > 0))
        ):
            sig = "BUY"
        elif direction in ("SELL", "STRONG_SELL") or (
            isinstance(score, (int, float)) and ((score < -0.12) or (trend <= -0.15 and score < 0))
        ):
            sig = "SELL"
        else:
            sig = "HOLD"
        return {
            "signal": sig,
            "description": f"{direction} skor {score:+.2f} conf {conf}",
            "direction": direction,
            "score": score,
            "confidence": conf,
        }

    def quick_signal(self, prices: pd.Series, close: pd.Series = None) -> str:
        result = self.run_full_analysis(prices, close=close or prices, verbose=False)
        return result["consensus"]["direction"]

    def get_cached(self) -> Dict:
        return self.results_cache


# ===============================================================================
# 8. DEMO
# ===============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Kripto Trading Orchestrator v1.0 - 53 Algoritma Birlestirici")
    print("=" * 70)

    np.random.seed(42)
    n = 200
    returns = np.random.normal(0.001, 0.02, n)
    close = pd.Series(100 * np.exp(np.cumsum(returns)))
    high = close * (1 + np.abs(np.random.randn(n)) * 0.01)
    low = close * (1 - np.abs(np.random.randn(n)) * 0.01)
    open_p = close.shift(1).fillna(close.iloc[0])
    volume = pd.Series(np.random.randint(1000, 10000, n), index=close.index)

    engine = TradingEngine(capital=10000)
    print("\nAlgoritmalar calistiriliyor...\n")
    report = engine.run_full_analysis(prices=close, high=high, low=low, close=close, open_prices=open_p, volume=volume)

    print("\n" + "=" * 70)
    print("FINAL RAPOR")
    print("=" * 70)
    print(f"Zaman:          {report['timestamp']}")
    print(f"Fiyat:          {report['price']}")
    print(f"Regim:          {report['regime']}")
    print(f"Sinyal:         {report['recommendation']['action']}")
    print(f"Skor:           {report['recommendation']['score']:+.3f}")
    print(f"Confidence:     {report['recommendation']['confidence']}")
    print(f"Aktif Sinyal:   {report['signal_breakdown']['bullish']} bullish / "
          f"{report['signal_breakdown']['bearish']} bearish / "
          f"{report['signal_breakdown']['neutral']} neutral")

    if report['risk_management']['stop_loss']:
        print(f"Stop Loss:      {report['risk_management']['stop_loss']}")
    if report['risk_management']['position_sizing']:
        sizing = report['risk_management']['position_sizing']
        print(f"Pozisyon:       ${sizing['position_size_usd']} ({sizing['position_size_pct']})")

    print("\nKategori Skorlari:")
    for cat, score in report['category_scores'].items():
        bar = "#" * int(abs(score) * 20)
        print(f"   {cat:20s}: {score:+.3f} {bar}")

    if report['errors']:
        print(f"\n{len(report['errors'])} algoritma hata verdi.")
