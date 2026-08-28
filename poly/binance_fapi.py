"""Binance USDT-M Futures imzalı REST — anahtarlar sadece env'den."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

_BASE = "https://fapi.binance.com"
_HDR_UA = {"User-Agent": "CEMAPI-LIVE"}


def configured() -> bool:
    return bool(key() and secret())


def enabled() -> bool:
    return configured() and (os.getenv("BINANCE_FAPI_LIVE") or "1").strip() not in ("0", "false", "off")


def key() -> str:
    return (os.getenv("BINANCE_FAPI_KEY") or "").strip()


def secret() -> str:
    return (os.getenv("BINANCE_FAPI_SECRET") or "").strip()


def _public(path: str, params: dict | None = None, timeout: int = 5):
    q = urllib.parse.urlencode(params or {})
    url = f"{_BASE}{path}" + (f"?{q}" if q else "")
    req = urllib.request.Request(url, headers=_HDR_UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _signed(method: str, path: str, params: dict | None = None, timeout: int = 8):
    if not configured():
        raise RuntimeError("Binance Futures anahtarı yok")
    p = dict(params or {})
    p["timestamp"] = int(time.time() * 1000)
    p["recvWindow"] = 10000
    query = urllib.parse.urlencode(p)
    sig = hmac.new(secret().encode(), query.encode(), hashlib.sha256).hexdigest()
    url = f"{_BASE}{path}?{query}&signature={sig}"
    headers = {**_HDR_UA, "X-MBX-APIKEY": key()}
    data = b"" if method == "POST" else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body)
        except Exception:
            err = {"msg": body[:200], "code": e.code}
        raise RuntimeError(str(err.get("msg") or body)[:180]) from None


def ping() -> bool:
    _public("/fapi/v1/ping")
    return True


def server_time() -> int:
    return int(_public("/fapi/v1/time").get("serverTime") or 0)


def account() -> dict:
    return _signed("GET", "/fapi/v2/account")


def balances() -> list:
    return _signed("GET", "/fapi/v2/balance")


def position_risk(symbol: str | None = None) -> list:
    p = {"symbol": symbol} if symbol else None
    return _signed("GET", "/fapi/v2/positionRisk", p)


def dual_side() -> bool:
    r = _signed("GET", "/fapi/v1/positionSide/dual")
    return bool(r.get("dualSidePosition"))


def set_leverage(symbol: str, lev: int) -> dict:
    return _signed("POST", "/fapi/v1/leverage", {"symbol": symbol, "leverage": int(lev)})


def max_leverage(symbol: str) -> int:
    """Sembolün izin verdiği en yüksek kaldıraç. Okunamazsa 0."""
    try:
        rows = _signed("GET", "/fapi/v1/leverageBracket", {"symbol": symbol})
    except Exception:
        return 0
    if isinstance(rows, dict):
        brackets = rows.get("brackets") or []
    elif isinstance(rows, list) and rows:
        brackets = (rows[0] or {}).get("brackets") or []
    else:
        brackets = []
    best = 0
    for b in brackets:
        try:
            best = max(best, int(b.get("initialLeverage") or 0))
        except (TypeError, ValueError):
            pass
    return best


def set_isolated(symbol: str) -> None:
    try:
        _signed("POST", "/fapi/v1/marginType", {"symbol": symbol, "marginType": "ISOLATED"})
    except RuntimeError as e:
        if "No need to change" in str(e) or "-4046" in str(e):
            return
        raise


def _fmt_px(px: float) -> str:
    s = f"{float(px):.12f}".rstrip("0").rstrip(".")
    return s or "0"


def get_order(symbol: str, order_id: str | int) -> dict:
    return _signed("GET", "/fapi/v1/order", {"symbol": symbol, "orderId": int(order_id)})


def cancel_order(symbol: str, order_id: str | int) -> dict:
    """Önce algo STOP, olmazsa klasik emir."""
    try:
        return _signed("DELETE", "/fapi/v1/algoOrder", {"symbol": symbol, "algoId": int(order_id)})
    except Exception:
        return _signed("DELETE", "/fapi/v1/order", {"symbol": symbol, "orderId": int(order_id)})


def stop_market_close(
    symbol: str,
    side: str,
    stop_price: float,
    *,
    client_order_id: str = "",
    working_type: str = "MARK_PRICE",
    position_side: str | None = None,
) -> dict:
    """STOP_MARKET + closePosition — Algo Order API (2025 sonrası zorunlu)."""
    p = {
        "algoType": "CONDITIONAL",
        "symbol": symbol,
        "side": side,
        "type": "STOP_MARKET",
        "triggerPrice": _fmt_px(stop_price),
        "closePosition": "true",
        "workingType": working_type,
    }
    if client_order_id:
        p["clientAlgoId"] = client_order_id[:32]
    if position_side:
        p["positionSide"] = position_side
    return _signed("POST", "/fapi/v1/algoOrder", p)


def user_trades(symbol: str, limit: int = 50) -> list:
    return _signed("GET", "/fapi/v1/userTrades", {"symbol": symbol, "limit": int(limit)})


def market_order(symbol: str, side: str, qty: str, reduce_only: bool = False, position_side: str | None = None) -> dict:
    p = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": qty,
        "newOrderRespType": "RESULT",
    }
    if position_side:
        p["positionSide"] = position_side
    elif reduce_only:
        p["reduceOnly"] = "true"
    return _signed("POST", "/fapi/v1/order", p)


def usdt_wallet() -> dict:
    """available / wallet / unreal — USDT futures."""
    out = {
        "ok": False,
        "wallet": 0.0,
        "available": 0.0,
        "unreal": 0.0,
        "error": "",
    }
    if not configured():
        out["error"] = "anahtar yok"
        return out
    try:
        rows = balances()
    except Exception as e:
        out["error"] = str(e)[:160]
        return out
    for r in rows or []:
        if str(r.get("asset") or "") != "USDT":
            continue
        out["ok"] = True
        out["wallet"] = float(r.get("balance") or 0)
        out["available"] = float(r.get("availableBalance") or 0)
        out["unreal"] = float(r.get("crossUnPnl") or 0)
        return out
    out["error"] = "USDT bakiyesi yok"
    return out
