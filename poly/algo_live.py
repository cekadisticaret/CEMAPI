"""LIVE Squeeze Momentum — sanal ile aynı sinyal/ATR, gerçek Binance Futures.

$30 marj × 10x. Sanal squeeze_momentum defterine dokunmaz.
"""
from __future__ import annotations

import json
import os
import threading
import time
import traceback
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import binance_fapi as fapi
from atr_sistem import ATRP_NO_TRADE, ATR_SL_MULT, atr_last, atrp as _atrp, levels as _atr_levels, sl_clears_liq, trail_stop
import algo_paper as paper

_TZ = ZoneInfo("Europe/Istanbul")
_DIR = os.path.dirname(os.path.abspath(__file__))
_STATE = os.path.join(_DIR, "algo_live_state.json")
AID = "squeeze_momentum"
MARGIN = 30.0
LEV = 10
NOTIONAL = MARGIN * LEV
MAX_POS = 6

_lock = threading.RLock()
_state: dict | None = None
_dual: bool | None = None
_wallet_cache: dict = {"t": 0.0, "row": {}}


def _now() -> datetime:
    return datetime.now(_TZ)


def _ts() -> str:
    return _now().strftime("%m-%d %H:%M")


def _iso() -> str:
    return _now().isoformat(timespec="seconds")


def _blank() -> dict:
    return {
        "id": AID,
        "code": "LIVE",
        "title": "Squeeze Momentum — Binance Futures",
        "active": True,
        "fees": 0.0,
        "positions": [],
        "history": [],
        "error": "",
        "last_signal": "",
        "last_scan": "",
    }


def _load() -> dict:
    global _state
    if _state is not None:
        return _state
    raw: dict = {}
    if os.path.isfile(_STATE):
        try:
            with open(_STATE, encoding="utf-8") as f:
                raw = json.load(f) or {}
        except Exception:
            raw = {}
    b = _blank()
    b["active"] = bool(raw.get("active", True))
    b["fees"] = float(raw.get("fees") or 0)
    b["positions"] = list(raw.get("positions") or [])
    b["history"] = list(raw.get("history") or [])[-400:]
    b["error"] = str(raw.get("error") or "")
    b["last_signal"] = str(raw.get("last_signal") or "")
    b["last_scan"] = str(raw.get("last_scan") or "")
    _state = b
    return _state


def _save() -> None:
    if _state is None:
        return
    tmp = _STATE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_state, f, ensure_ascii=False)
        os.replace(tmp, _STATE)
    except OSError:
        pass


def _qty_fmt(qty: float, step: float) -> str:
    q = paper._round_step(qty, step)
    if q <= 0:
        return "0"
    s = f"{q:.12f}".rstrip("0").rstrip(".")
    return s or "0"


def _is_dual() -> bool:
    global _dual
    if _dual is None:
        try:
            _dual = fapi.dual_side()
        except Exception:
            _dual = False
    return bool(_dual)


def _pos_side(side: str) -> str | None:
    if not _is_dual():
        return None
    return "LONG" if side == "LONG" else "SHORT"


def _order_side(side: str, close: bool) -> str:
    if close:
        return "SELL" if side == "LONG" else "BUY"
    return "BUY" if side == "LONG" else "SELL"


def wallet(force: bool = False) -> dict:
    now = time.time()
    if not force and _wallet_cache["row"] and now - _wallet_cache["t"] < 4:
        return _wallet_cache["row"]
    row = fapi.usdt_wallet()
    _wallet_cache["t"] = now
    _wallet_cache["row"] = row
    return row


def _meta() -> dict | None:
    for m in paper._discover():
        if m["id"] == AID:
            return m
    return None


def _mark_one(p: dict, marks: dict) -> dict:
    info = marks.get(p["symbol"]) or {}
    mark = float(info.get("mark") or info.get("price") or p.get("mark") or p["entry"])
    qty = float(p.get("qty") or 0)
    margin = float(p.get("margin") or MARGIN)
    exit_est = paper._fill_px(p["side"], "close", info) or mark
    gross = paper._pnl(p["side"], float(p["entry"]), mark, qty)
    fee_open = float(p.get("fee_open") or 0)
    fee_close = paper._fee_on(qty, exit_est or mark)
    fund = float(p.get("funding_acc") or 0)
    net = gross - fee_open - fee_close + fund
    pct = (net / margin) * 100 if margin else 0
    out = dict(p)
    out.update({
        "mark": mark,
        "chg": float(info.get("chg") or 0),
        "qty": qty,
        "gross": round(gross, 2),
        "commission": round(fee_open + fee_close, 2),
        "funding": round(fund, 4),
        "net": round(net, 2),
        "pct": round(pct, 2),
        "mins": paper._hold_mins(p),
        "tp_usd": round(paper._pnl(p["side"], float(p["entry"]), float(p.get("tp") or 0), qty), 2),
        "sl_usd": round(paper._pnl(p["side"], float(p["entry"]), float(p.get("sl") or 0), qty), 2),
        "atr": round(float(p.get("atr") or 0), 8),
        "atrp": round(float(p.get("atrp") or 0), 2),
        "trail_on": bool(p.get("trail_on")),
        "tp1_done": bool(p.get("tp1_done")),
        "live": True,
    })
    return out


def overview() -> dict:
    with _lock:
        b = _load()
        marks = paper._marks()
        poss = [_mark_one(p, marks) for p in b.get("positions") or []]
        hist = list(b.get("history") or [])[-80:][::-1]
        wins = sum(1 for h in hist if float(h.get("net") or 0) > 0)
        realized = sum(float(h.get("net") or 0) for h in hist)
        w = wallet()
        equity = float(w.get("wallet") or 0) + float(w.get("unreal") or 0)
        return {
            "id": AID,
            "code": "LIVE",
            "title": b.get("title") or "Squeeze Momentum",
            "auto": True,
            "active": bool(b.get("active")),
            "live": True,
            "error": b.get("error") or w.get("error") or "",
            "connected": bool(w.get("ok")),
            "wallet": round(float(w.get("wallet") or 0), 2),
            "available": round(float(w.get("available") or 0), 2),
            "wallet_unreal": round(float(w.get("unreal") or 0), 2),
            "cash_free": round(float(w.get("available") or 0), 2),
            "equity": round(equity, 2),
            "net_pnl": round(realized + sum(p["net"] for p in poss), 2),
            "unreal": round(sum(p["net"] for p in poss), 2),
            "fees": round(float(b.get("fees") or 0), 2),
            "open_n": len(poss),
            "wins": wins,
            "trades": len(b.get("history") or []),
            "win_pct": round(100.0 * wins / len(hist), 1) if hist else 0.0,
            "realized": round(realized, 2),
            "positions": poss,
            "history": hist,
            "last_signal": b.get("last_signal") or "",
            "last_scan": b.get("last_scan") or "",
            "margin": MARGIN,
            "lev": LEV,
        }


def toggle() -> dict:
    with _lock:
        b = _load()
        b["active"] = not b.get("active")
        _save()
    return overview()


def _place(symbol: str, side: str, qty: float, step: float, close: bool = False) -> dict:
    fapi.set_isolated(symbol)
    fapi.set_leverage(symbol, LEV)
    q = _qty_fmt(qty, step)
    if float(q) <= 0:
        raise RuntimeError("miktar 0")
    return fapi.market_order(
        symbol,
        _order_side(side, close),
        q,
        reduce_only=close and not _is_dual(),
        position_side=_pos_side(side),
    )


def _fill_px_qty(order: dict, fallback_px: float, fallback_qty: float, symbol: str = "") -> tuple[float, float]:
    px = float(order.get("avgPrice") or 0)
    qty = float(order.get("executedQty") or 0)
    oid = order.get("orderId")
    if (px <= 0 or qty <= 0) and oid and symbol:
        try:
            nxt = fapi.get_order(symbol, oid)
            px = px or float(nxt.get("avgPrice") or 0)
            qty = qty or float(nxt.get("executedQty") or 0)
        except Exception:
            pass
    if px <= 0:
        px = fallback_px
    if qty <= 0:
        qty = fallback_qty
    return px, qty


def _hist_rec(p: dict, exit_px: float, qty: float, reason: str, fee_close: float, partial: bool = False) -> dict:
    gross = paper._pnl(p["side"], float(p["entry"]), exit_px, qty)
    fee_open = float(p.get("fee_open") or 0)
    frac = qty / float(p.get("qty") or qty or 1)
    fee_open_part = fee_open * (frac if partial else 1.0)
    fund = float(p.get("funding_acc") or 0) * (frac if partial else 1.0)
    net = gross - fee_open_part - fee_close + fund
    return {
        "id": p["id"] + ("a" if partial else ""),
        "t": _ts(),
        "iso": _iso(),
        "symbol": p["symbol"],
        "base": p["base"],
        "side": p["side"],
        "entry": p["entry"],
        "exit": exit_px,
        "reason": reason,
        "gross": round(gross, 2),
        "commission": round(fee_open_part + fee_close, 2),
        "funding": round(fund, 4),
        "net": round(net, 2),
        "opened": str(p.get("opened") or ""),
        "opened_iso": str(p.get("opened_iso") or ""),
        "closed": _ts(),
        "closed_iso": _iso(),
        "mins": paper._hold_mins(p),
        "partial": partial,
        "live": True,
    }


def _close_qty(b: dict, p: dict, qty: float, reason: str, partial: bool = False) -> dict | None:
    filt = paper._filters().get(p["symbol"]) or {}
    step = float(filt.get("step") or 0.001)
    order = _place(p["symbol"], p["side"], qty, step, close=True)
    px, filled = _fill_px_qty(
        order, float(p.get("mark") or p["entry"]), qty, symbol=p["symbol"],
    )
    fee_close = paper._fee_on(filled, px)
    rec = _hist_rec(p, px, filled, reason, fee_close, partial=partial)
    b["fees"] = round(float(b.get("fees") or 0) + fee_close, 2)
    hist = b.setdefault("history", [])
    hist.append(rec)
    if len(hist) > 400:
        del hist[:-400]
    if partial:
        p["qty"] = max(0.0, float(p["qty"]) - filled)
        p["fee_open"] = float(p.get("fee_open") or 0) * (p["qty"] / (p["qty"] + filled) if (p["qty"] + filled) else 0)
        p["tp1_done"] = True
        p["margin"] = MARGIN * 0.5
    else:
        b["positions"] = [x for x in b.get("positions") or [] if x["id"] != p["id"]]
    return rec


def close_pos(pos_id: str, reason: str = "manuel") -> tuple[dict, int]:
    with _lock:
        b = _load()
        hit = next((p for p in b.get("positions") or [] if p["id"] == pos_id), None)
        if not hit:
            return {"error": "pozisyon yok"}, 404
        try:
            rec = _close_qty(b, hit, float(hit.get("qty") or 0), reason, partial=False)
        except Exception as e:
            b["error"] = str(e)[:160]
            _save()
            return {"error": str(e)[:160]}, 400
        _save()
        return {"ok": True, "closed": rec, "book": overview()}, 200


def _open_pos(b: dict, symbol: str, side: str, marks: dict, df) -> dict | None:
    if not b.get("active"):
        return None
    if not fapi.enabled():
        return None
    if len(b.get("positions") or []) >= MAX_POS:
        return None
    if any(p["symbol"] == symbol for p in b.get("positions") or []):
        return None
    info = marks.get(symbol) or {}
    filt = paper._filters().get(symbol) or {}
    tick = float(filt.get("tick") or 0)
    step = float(filt.get("step") or 0.001)
    px = paper._round_tick(paper._fill_px(side, "open", info), tick)
    if px <= 0 or df is None:
        return None
    atr = atr_last(df)
    if atr <= 0:
        return None
    ap = _atrp(atr, px)
    if ap >= ATRP_NO_TRADE:
        return None
    lv = _atr_levels(side, px, atr)
    sl = paper._round_tick(lv["sl"], tick)
    tp1 = paper._round_tick(lv["tp1"], tick)
    tp2 = paper._round_tick(lv["tp2"], tick)
    liq = paper._round_tick(paper._liq_price(side, px), tick)
    if not sl_clears_liq(side, px, sl, liq):
        return None
    qty = paper._round_step(NOTIONAL / px, step)
    if qty <= 0 or qty * px < float(filt.get("min_notional") or 5):
        return None
    w = wallet(force=True)
    if not w.get("ok") or float(w.get("available") or 0) < MARGIN * 1.05:
        b["error"] = "USDT yetersiz"
        return None
    try:
        order = _place(symbol, side, qty, step, close=False)
    except Exception as e:
        b["error"] = str(e)[:160]
        return None
    fill_px, fill_qty = _fill_px_qty(order, px, qty)
    fee = paper._fee_on(fill_qty, fill_px)
    pos = {
        "id": uuid.uuid4().hex[:12],
        "symbol": symbol,
        "base": symbol.replace("USDT", ""),
        "side": side,
        "entry": fill_px,
        "mark": fill_px,
        "qty": fill_qty,
        "qty_orig": fill_qty,
        "margin": MARGIN,
        "lev": LEV,
        "atr": atr,
        "atrp": round(ap, 2),
        "r_dist": lv["r_dist"],
        "sl": sl,
        "tp1": tp1,
        "tp": tp2,
        "tp2": tp2,
        "liq": liq,
        "peak": fill_px,
        "trough": fill_px,
        "trail_on": False,
        "tp1_done": False,
        "fee_open": fee,
        "funding_acc": 0.0,
        "opened": _ts(),
        "opened_iso": _iso(),
        "opened_ms": int(time.time() * 1000),
        "fill": "binance",
        "live": True,
        "order_id": str(order.get("orderId") or ""),
    }
    b["fees"] = round(float(b.get("fees") or 0) + fee, 2)
    b.setdefault("positions", []).append(pos)
    b["error"] = ""
    return pos


def on_scan(frames: dict, marks: dict) -> None:
    if not fapi.configured():
        with _lock:
            b = _load()
            b["error"] = "Binance anahtarı yok"
            b["last_scan"] = _iso()
            _save()
        return
    with _lock:
        b = _load()
        for p in list(b.get("positions") or []):
            info = marks.get(p["symbol"]) or {}
            mk = float(info.get("mark") or info.get("price") or 0)
            if mk <= 0:
                continue
            paper._refresh_trail(p, mk, frames.get(p["symbol"]))
            why = paper._hit_exit(p, mk)
            try:
                if why == "take_profit_1":
                    _close_qty(b, p, float(p.get("qty") or 0) * 0.5, why, partial=True)
                elif why:
                    _close_qty(b, p, float(p.get("qty") or 0), why, partial=False)
            except Exception as e:
                b["error"] = str(e)[:160]
        _save()

    meta = _meta()
    if not meta:
        return
    book = {"id": AID, "file": meta["file"], "class_name": meta["class_name"]}
    err, hits, last = paper._eval_hits(book, frames, marks)
    with _lock:
        b = _load()
        b["last_signal"] = last
        b["last_scan"] = _iso()
        if err:
            b["error"] = err
            _save()
            return
        if not b.get("active"):
            _save()
            return
        held = {p["symbol"] for p in b.get("positions") or []}
        for _qv, sym, side, _desc, _chg in hits:
            if sym in held or len(held) >= MAX_POS:
                continue
            if _open_pos(b, sym, side, marks, frames.get(sym)):
                held.add(sym)
        _save()


def _iso_ms(s: str) -> int:
    try:
        return int(datetime.fromisoformat(s).timestamp() * 1000)
    except Exception:
        return 0


def _trades_vwap(rows: list) -> tuple[float, float, float, float]:
    notional = 0.0
    qty = 0.0
    fee = 0.0
    rpnl = 0.0
    for t in rows:
        q = float(t.get("qty") or 0)
        px = float(t.get("price") or 0)
        notional += q * px
        qty += q
        fee += abs(float(t.get("commission") or 0))
        rpnl += float(t.get("realizedPnl") or 0)
    return (notional / qty if qty else 0.0), qty, fee, rpnl


def repair_history() -> list[dict]:
    """exit=entry yazılmış kapanışları Binance dolumundan düzelt."""
    fixed = []
    with _lock:
        b = _load()
        for h in b.get("history") or []:
            entry = float(h.get("entry") or 0)
            exit_px = float(h.get("exit") or 0)
            if entry <= 0 or abs(exit_px - entry) > max(entry * 1e-8, 1e-12):
                continue
            sym = str(h.get("symbol") or "")
            if not sym:
                continue
            try:
                trades = fapi.user_trades(sym, 80)
            except Exception:
                continue
            t0 = _iso_ms(str(h.get("opened_iso") or "")) - 15_000
            t1 = _iso_ms(str(h.get("closed_iso") or h.get("iso") or "")) + 15_000
            if t1 <= t0:
                continue
            side = str(h.get("side") or "")
            open_side = "SELL" if side == "SHORT" else "BUY"
            close_side = "BUY" if side == "SHORT" else "SELL"
            opens = [t for t in trades if str(t.get("side")) == open_side and t0 <= int(t.get("time") or 0) <= t1]
            closes = [t for t in trades if str(t.get("side")) == close_side and t0 <= int(t.get("time") or 0) <= t1]
            if not opens or not closes:
                continue
            e_px, _, fee_o, _ = _trades_vwap(opens)
            x_px, qty, fee_c, rpnl = _trades_vwap(closes)
            if e_px <= 0 or x_px <= 0:
                continue
            fee = fee_o + fee_c
            gross = paper._pnl(side, e_px, x_px, qty)
            if abs(rpnl) > 0:
                gross = rpnl
            h["entry"] = e_px
            h["exit"] = x_px
            h["gross"] = round(gross, 2)
            h["commission"] = round(fee, 2)
            h["net"] = round(gross - fee, 2)
            fixed.append({"symbol": sym, "entry": e_px, "exit": x_px, "net": h["net"]})
        _save()
    return fixed


def status() -> dict:
    w = wallet(force=True)
    return {
        "ok": bool(w.get("ok")),
        "configured": fapi.configured(),
        "enabled": fapi.enabled(),
        "wallet": w,
    }
