"""
atr_step_trailing_stop.py
===========================================================================
ATR bazli kademeli KAR STOPU (profit-lock trailing stop) - Binance USDM Futures

LIVE baglanti (CEMAPI): zarar SL (1.5xATR) yerinde kalir. Bu katman yalnizca
trail acikken (1R sonra) ve aday stop girisin guvenli tarafundayken
STOP_MARKET yazar. python-binance zorunlu degil — place_fn / cancel_fn yeter.
===========================================================================
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Literal, Optional

logger = logging.getLogger("step_trailing_stop")

PlaceFn = Callable[..., dict]
CancelFn = Callable[[str, Any], Any]
RoundFn = Callable[[float], float]


class ATRStepTrailingStop:
    def __init__(
        self,
        symbol: str,
        side: Literal["LONG", "SHORT"],
        entry_price: float,
        quantity: float = 0.0,
        activation_atr_mult: float = 0.5,
        trail_atr_mult: float = 1.0,
        min_step_atr_mult: float = 0.25,
        client_id_prefix: str = "STOP",
        working_type: str = "MARK_PRICE",
        client: Any = None,
        place_fn: PlaceFn | None = None,
        cancel_fn: CancelFn | None = None,
        round_fn: RoundFn | None = None,
        position_side: str | None = None,
    ):
        self.client = client
        self.place_fn = place_fn
        self.cancel_fn = cancel_fn
        self.round_fn = round_fn
        self.position_side = position_side
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.quantity = quantity

        self.activation_atr_mult = activation_atr_mult
        self.trail_atr_mult = trail_atr_mult
        self.min_step_atr_mult = min_step_atr_mult
        self.client_id_prefix = client_id_prefix
        self.working_type = working_type

        self.active = False
        self.step = 0
        self.high_water = entry_price
        self.current_stop_price: Optional[float] = None
        self.current_order_id: Optional[int] = None
        self.current_client_order_id: Optional[str] = None

    def on_price_update(self, price: float, atr: float) -> Optional[dict]:
        """Yeni fiyat + ATR. Yeni stop konursa dict, yoksa None."""
        if atr is None or atr <= 0 or price is None or price <= 0:
            return None

        is_long = self.side == "LONG"

        if is_long:
            self.high_water = max(self.high_water, price)
        else:
            self.high_water = min(self.high_water, price)

        profit_dist = (
            (self.high_water - self.entry_price)
            if is_long
            else (self.entry_price - self.high_water)
        )
        if not self.active:
            if profit_dist < self.activation_atr_mult * atr:
                return None
            self.active = True
            logger.info(f"{self.symbol} kar stopu aktive oldu (kar={profit_dist:.4f})")

        candidate_stop = (
            self.high_water - self.trail_atr_mult * atr
            if is_long
            else self.high_water + self.trail_atr_mult * atr
        )
        if is_long:
            candidate_stop = max(candidate_stop, self.entry_price)
        else:
            candidate_stop = min(candidate_stop, self.entry_price)
        if self.round_fn:
            candidate_stop = float(self.round_fn(candidate_stop))
            if is_long:
                candidate_stop = max(candidate_stop, self.entry_price)
            else:
                candidate_stop = min(candidate_stop, self.entry_price)

        if self.current_stop_price is not None:
            improved = (
                candidate_stop > self.current_stop_price
                if is_long
                else candidate_stop < self.current_stop_price
            )
            if not improved:
                return None
            if abs(candidate_stop - self.current_stop_price) < self.min_step_atr_mult * atr:
                return None

        return self._update_stop_order(candidate_stop)

    def _place(self, close_side: str, stop_price: float, client_order_id: str) -> dict:
        if self.place_fn:
            return self.place_fn(
                self.symbol,
                close_side,
                stop_price,
                client_order_id,
                self.working_type,
                self.position_side,
            )
        if self.client is not None:
            from binance.enums import FUTURE_ORDER_TYPE_STOP_MARKET
            kw = dict(
                symbol=self.symbol,
                side=close_side,
                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                stopPrice=stop_price,
                closePosition=True,
                newClientOrderId=client_order_id,
                workingType=self.working_type,
            )
            if self.position_side:
                kw["positionSide"] = self.position_side
            return self.client.futures_create_order(**kw)
        raise RuntimeError("place_fn veya client yok")

    def _cancel(self, order_id: Any) -> None:
        if self.cancel_fn:
            self.cancel_fn(self.symbol, order_id)
            return
        if self.client is not None:
            self.client.futures_cancel_order(symbol=self.symbol, orderId=order_id)
            return
        raise RuntimeError("cancel_fn veya client yok")

    def _update_stop_order(self, new_stop_price: float) -> dict:
        if self.current_order_id is not None:
            try:
                self._cancel(self.current_order_id)
            except Exception as e:
                logger.warning(f"{self.symbol} eski stop emri iptal edilemedi: {e}")

        close_side = "SELL" if self.side == "LONG" else "BUY"
        nxt = self.step + 1
        label = f"{self.client_id_prefix}{nxt}"
        client_order_id = f"{label}-{self.symbol[:12]}-{int(time.time()) % 100000000}"

        order = self._place(close_side, new_stop_price, client_order_id)
        oid = order.get("algoId") or order.get("orderId")
        self.step = nxt
        self.current_stop_price = new_stop_price
        self.current_order_id = int(oid) if oid not in (None, "") else None
        self.current_client_order_id = client_order_id

        logger.info(
            f"{self.symbol} {label} guncellendi: stop={new_stop_price:.4f} "
            f"(zirve={self.high_water:.4f})"
        )

        return {
            "label": label,
            "step": self.step,
            "stop_price": new_stop_price,
            "high_water": self.high_water,
            "order_id": self.current_order_id,
            "client_order_id": client_order_id,
        }

    def on_stop_filled(self, fill_price: float) -> str:
        label = f"{self.client_id_prefix}{self.step}"
        note = f"{label}'de stoploss oldu (fiyat={fill_price:.4f})"
        logger.info(note)
        self.active = False
        self.current_order_id = None
        self.current_client_order_id = None
        return note

    def cancel(self):
        if self.current_order_id is not None:
            try:
                self._cancel(self.current_order_id)
            except Exception as e:
                logger.warning(f"{self.symbol} stop emri iptalinde hata: {e}")
            finally:
                self.current_order_id = None
                self.current_client_order_id = None
