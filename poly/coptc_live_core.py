#!/usr/bin/env python3
"""CoptC Live Control — gerçek PM çekirdeği (API mirror)."""
from __future__ import annotations

import asyncio
import contextlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from coptc_pm_common import fetch_klines, sym_short, tg_send, try_pm_open

_sym_short = sym_short
_fetch_klines = fetch_klines
from pm_trader_helpers import (
    HOURLY_MIN_NET_PROFIT_RATIO,
    pm_fetch_resolution,
    pm_get_balance,
    pm_live_amount_range_str,
    pm_live_wr_amount,
    pm_realized_pnl,
    pm_sanal_slot_candle,
    pm_tg_stake,
    resolve_open_slot_gates,
    resolve_slot_trade_amount,
    skip_if_weekend_pause,
    slot_amount_log,
)
from coptc_guard import can_open_trade, is_dashboard_live_open

_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
if os.path.exists(_ENV_FILE):
    with open(_ENV_FILE) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

_TZ_TR = ZoneInfo("Europe/Istanbul")
_DIR = os.path.dirname(os.path.abspath(__file__))


@dataclass(frozen=True)
class LiveSpec:
    label: str
    amount_system: str  # coptc_settings.json anahtarı (coptc_live_amount_*)
    env_flag: str       # COPTC_LIVE_ENABLED
    default_amount: float = 5.0
    book_tag: str = "coptc_live"
    algo_name: str = "API Mirror"
    min_profit_ratio: float | None = None
    mirror_book: str | None = None


def book_tag(spec: LiveSpec) -> str:
    return spec.book_tag


def _paths(spec: LiveSpec) -> tuple[str, str, str]:
    tag = book_tag(spec)
    return (
        os.path.join(_DIR, f"{tag}_state.json"),
        os.path.join(_DIR, f"{tag}_history.json"),
        os.path.join(_DIR, f"{tag}_polyhata.json"),
    )


def _pm_enabled(spec: LiveSpec) -> bool:
    """Dashboard Live anahtarı tek otorite; .env bayrağı yedek (geriye uyumluluk)."""
    if is_dashboard_live_open(spec.label):
        return True
    return os.getenv(spec.env_flag, "false").lower() in ("1", "true", "yes")


def is_live_active(spec: LiveSpec) -> bool:
    if not _pm_enabled(spec):
        return False
    return can_open_trade(spec.label, lambda t: tg_send(spec.label, t))


def _sanal_state_path(_spec: LiveSpec) -> str:
    return os.path.join(_DIR, "coptc_live_state.json")


def _live_has_sanal_pos(live_state: dict, sanal_pos: dict) -> bool:
    sym = sanal_pos.get("symbol")
    slug = sanal_pos.get("pm_slug")
    hour = sanal_pos.get("entry_hour_tr")
    for p in live_state.get("open_positions") or []:
        if p.get("symbol") != sym:
            continue
        if slug and p.get("pm_slug") == slug:
            return True
        if hour is not None and p.get("entry_hour_tr") == hour:
            return True
    return False


def _read_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _atomic_write(path: str, data) -> None:
    """Yarım yazılmış dosya = kayıp pozisyon = mükerrer emir; önce yedekle, sonra takas et."""
    if os.path.exists(path):
        with contextlib.suppress(OSError):
            shutil.copyfile(path, f"{path}.bak")
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_state(spec: LiveSpec) -> dict:
    """Bozuk state'i boş saymak açık pozisyonları görünmez yapar ve aynı slota
    ikinci emir girilmesine yol açar — yedeğe düş, o da yoksa hata ver."""
    sp, _, _ = _paths(spec)
    if not os.path.exists(sp):
        return {"balance": 0.0, "open_positions": [], "total_pnl": 0.0}
    try:
        return _read_json(sp)
    except Exception as e:
        bak = f"{sp}.bak"
        if os.path.exists(bak):
            try:
                st = _read_json(bak)
                print(f"[{spec.label}] state bozuk, yedekten okundu: {e}", file=sys.stderr)
                return st
            except Exception:
                pass
        raise RuntimeError(f"state okunamadı ve yedek yok ({sp}): {e}") from e


def save_state(spec: LiveSpec, state: dict) -> None:
    sp, _, _ = _paths(spec)
    _atomic_write(sp, state)


def load_history(spec: LiveSpec) -> list:
    _, hp, _ = _paths(spec)
    if os.path.exists(hp):
        try:
            return _read_json(hp)
        except Exception:
            bak = f"{hp}.bak"
            if os.path.exists(bak):
                with contextlib.suppress(Exception):
                    return _read_json(bak)
    return []


def save_history(spec: LiveSpec, history: list) -> None:
    _, hp, _ = _paths(spec)
    _atomic_write(hp, history)


def _wr(wins: int, total: int) -> str:
    return f"%{wins / total * 100:.0f} ({wins}/{total})" if total else "veri yok"


def get_symbol_stats(history: list, symbol: str) -> tuple[int, int]:
    trades = [t for t in history if t.get("symbol") == symbol]
    return sum(1 for t in trades if t.get("win")), len(trades)


def get_stats(history: list, symbol: str, hour_tr: int) -> tuple[int, int]:
    trades = [
        t for t in history
        if t.get("symbol") == symbol and t.get("entry_hour_tr") == hour_tr
    ]
    return sum(1 for t in trades if t.get("win")), len(trades)


def _amount_system_for(spec: LiveSpec, source: str | None = None) -> str:
    # Tek kademe — API'den hangi kaynak seçilirse aynı Low/Mid/High.
    return spec.amount_system


def _trade_amount(
    spec: LiveSpec, history: list, symbol: str, source: str | None = None,
) -> float:
    return pm_live_wr_amount(
        _amount_system_for(spec, source), history, symbol, get_symbol_stats,
    )


def _pm_bal_line() -> str:
    bal = pm_get_balance()
    return f"💰 PM Bakiye: ${bal:.2f}" if bal >= 0 else "💰 PM Bakiye: ?"


def _resolve_pm(pos: dict, *, now_hour: int):
    """PM sonuç — slot bitmişse gevşek eşik, o da yoksa Binance mum yedeği.

    Gamma bazen saat bitince uzun süre mid-price (örn. 0.75) tutuyor;
    closed=False iken 0.99 eşiği hiç geçmiyor. Slot bitmişse:
      1) 0.90 eşiği
      2) Binance 1h slot mumu (sanal settle ile aynı) — defteri kilitlemez
    """
    slug = pos.get("pm_slug")
    if not slug:
        return None
    res = pm_fetch_resolution(slug)
    if res is not None:
        return res
    entry_h = pos.get("entry_hour_tr")
    slot_ended = entry_h is not None and int(entry_h) != int(now_hour)
    if not slot_ended:
        return None
    res = pm_fetch_resolution(slug, min_decisive=0.90)
    if res is not None:
        return res
    candle = pm_sanal_slot_candle(pos.get("symbol") or "", pos.get("entry_time_tr") or "")
    if not candle:
        return None
    hour_open, hour_close = candle
    up_won = hour_close >= hour_open
    print(
        f"[A2 live] {pos.get('symbol')} PM kesin değil → Binance yedek "
        f"{'UP' if up_won else 'DOWN'} ({hour_open:.2f}→{hour_close:.2f})"
    )
    return {
        "up_won": up_won,
        "closed": False,
        "up_price": 1.0 if up_won else 0.0,
        "down_price": 0.0 if up_won else 1.0,
        "title": "binance_fallback",
        "source": "binance_slot",
    }


async def run_close(spec: LiveSpec) -> None:
    now_tr = datetime.now(timezone.utc).astimezone(_TZ_TR)
    if skip_if_weekend_pause(spec.label, "close", now_tr):
        return
    reconcile_external_closes(spec)
    state = load_state(spec)
    history = load_history(spec)
    if not state["open_positions"]:
        print(f"[{spec.label} close] açık pozisyon yok")
        return

    lines = []
    pending = []
    tur_pnl = 0.0
    failed = []
    for pos in list(state["open_positions"]):
        sym = pos["symbol"]
        klines = await _fetch_klines(sym, "1h", 2)
        if not klines:
            failed.append(pos)
            pending.append(f"{_sym_short(sym)} (kline yok)")
            continue
        current_price = klines[-1]["close"]
        entry = pos["entry_price"]
        pred = pos["predicted_dir"]
        amount = pos.get("amount", spec.default_amount)
        has_pm = bool(pos.get("pm_slug") and pos.get("pm_order_id"))
        if has_pm:
            res = _resolve_pm(pos, now_hour=now_tr.hour)
            if res is None:
                failed.append(pos)
                pending.append(
                    f"{_sym_short(sym)} h={pos.get('entry_hour_tr')} "
                    f"(PM sonuç henüz kesin değil)"
                )
                continue
            token_dir = pos.get("pm_token_dir") or pred
            win = (token_dir == "UP" and res["up_won"]) or (token_dir == "DOWN" and not res["up_won"])
            actual = "UP" if res["up_won"] else "DOWN"
            pnl = pm_realized_pnl(pos, win)
            settle_src = res.get("source") or "pm"
        else:
            actual = "UP" if current_price >= entry else "DOWN"
            win = pred == actual
            pm_spent = float(pos.get("pm_spent") or amount)
            pm_size = float(pos.get("pm_size") or 0)
            pnl = round(pm_size - pm_spent, 2) if win and pm_size else round(-pm_spent, 2)
            settle_src = "no_pm"
        tur_pnl += pnl
        state["total_pnl"] = round(state.get("total_pnl", 0.0) + pnl, 2)
        history.append({
            "symbol": sym,
            "predicted_dir": pred,
            "actual_dir": actual,
            "win": win,
            "entry_price": entry,
            "exit_price": current_price,
            "entry_time_tr": pos["entry_time_tr"],
            "entry_hour_tr": pos.get("entry_hour_tr"),
            "entry_dow": pos.get("entry_dow"),
            "amount": amount,
            "pnl": pnl,
            "pm_live": True,
            "exit_time_tr": now_tr.isoformat(),
            "pm_spent": pos.get("pm_spent"),
            "pm_size": pos.get("pm_size"),
            "pm_slug": pos.get("pm_slug"),
            "algo_name": pos.get("algo_name", spec.algo_name),
            "algo_num": 0,
            "settle_source": settle_src if has_pm else "no_pm",
            "source_position_id": pos.get("source_position_id"),
            "mirrored_from_source": pos.get("mirrored_from_source"),
        })
        name = _sym_short(sym)
        lines.append(f"{'✅' if win else '❌'} {name}  {pred}  net {'+' if pnl >= 0 else ''}{pnl:.2f}$")

    state["open_positions"] = failed
    save_state(spec, state)
    save_history(spec, history)
    if pending:
        print(f"[{spec.label} close] {len(pending)} pozisyon bekliyor: {', '.join(pending)}")
    if not lines:
        return
    print(f"[{spec.label} close] {len(lines)} pozisyon kapatıldı")
    closed = len(history)
    wins = sum(1 for t in history if t["win"])
    genel = f"%{wins / closed * 100:.0f}" if closed else "—"
    sep = "━" * 26
    tg_send(
        spec.label,
        f"{sep}\n🏁 <b>{spec.label} — Sonuçlar</b>  🔴 GERÇEK PM\n"
        + "\n".join(lines)
        + f"\nBu tur: {'+' if tur_pnl >= 0 else ''}{tur_pnl:.2f}$  |  {_pm_bal_line()}\n"
        f"Genel: {genel} ({closed} işlem)\n{sep}",
    )
    try:
        from pm_trader_helpers import pm_cash_out_pending
        open_ids = {
            str(p["pm_token_id"]) for p in state.get("open_positions") or []
            if p.get("pm_token_id")
        }
        pm_cash_out_pending(label=spec.label, open_token_ids=open_ids, wait=True)
    except Exception as e:
        print(f"[{spec.label} close] cash-out: {e}", file=sys.stderr)


def run_manual_close(
    spec: LiveSpec,
    symbols: list[str] | None = None,
    *,
    token_id: str | None = None,
    source: str | None = None,
    hour_tr: int | None = None,
) -> dict:
    """Açık live pozisyonları piyasa fiyatından sat — sonucu beklemeden kapat."""
    import pm_trader_helpers as pmh
    from pm_trader_helpers import pm_sell_position

    pmh.PM_DRY_RUN = False   # bu defterdeki pozisyonlar zaten gerçek PM

    now_tr = datetime.now(timezone.utc).astimezone(_TZ_TR)
    state = load_state(spec)
    history = load_history(spec)
    opens = state.get("open_positions") or []
    if not opens:
        print(f"[{spec.label} manuel] açık pozisyon yok")
        return {"closed": 0, "failed": 0, "pnl": 0.0}

    want = {s.upper() for s in symbols} if symbols else None
    targeted = bool(token_id)
    kalan, lines = [], []
    closed = failed = 0
    tur_pnl = 0.0

    for pos in opens:
        sym = pos.get("symbol") or ""
        tid = pos.get("pm_token_id")
        if not _manual_close_match(
            pos, symbols=want, token_id=token_id, source=source, hour_tr=hour_tr,
        ):
            kalan.append(pos)
            continue

        sell_size = None
        if targeted:
            sz = float(pos.get("pm_size") or 0)
            if sz >= 0.01:
                sell_size = sz

        held = -1.0
        if tid:
            try:
                held = pmh.pm_conditional_shares(str(tid))
            except Exception:
                held = -1.0
        if tid and held >= 0 and held < 0.5:
            fill = pmh.pm_recent_sell(str(tid))
            res = {
                "order_id": "external",
                "size": float(fill["size"]) if fill else 0.0,
                "price": float(fill["price"]) if fill else 0.0,
                "proceeds": float(fill["proceeds"]) if fill else 0.0,
                "external": True,
            }
        else:
            res = pm_sell_position(str(tid), sell_size, label=spec.label, attempts=5)
        if not res:
            failed += 1
            kalan.append(pos)
            print(f"[{spec.label} manuel] {_sym_short(sym)} satılamadı", file=sys.stderr)
            continue

        leftover = res.get("remaining")
        if leftover is None and tid:
            try:
                leftover = pmh.pm_conditional_shares(str(tid))
            except Exception:
                leftover = -1.0
        if leftover is not None and leftover >= 0.5:
            old_sz = float(pos.get("pm_size") or 0)
            old_spent = float(pos.get("pm_spent") or pos.get("amount") or 0)
            pos["pm_size"] = leftover
            if old_sz > 0:
                pos["pm_spent"] = round(old_spent * leftover / old_sz, 2)
            kalan.append(pos)
            failed += 1
            print(
                f"[{spec.label} manuel] {_sym_short(sym)} kısmi satış — "
                f"{leftover:g} share duruyor, defterde kaldı",
                file=sys.stderr,
            )
            continue

        spent = float(pos.get("pm_spent") or pos.get("amount") or 0)
        proceeds = float(res["proceeds"])
        pnl = round(proceeds - spent, 2)
        tur_pnl += pnl
        closed += 1
        state["total_pnl"] = round(state.get("total_pnl", 0.0) + pnl, 2)
        history.append({
            "symbol": sym,
            "predicted_dir": pos.get("predicted_dir"),
            "actual_dir": "MANUEL",
            "win": pnl > 0,
            "entry_price": pos.get("entry_price"),
            "entry_time_tr": pos.get("entry_time_tr"),
            "entry_hour_tr": pos.get("entry_hour_tr"),
            "entry_dow": pos.get("entry_dow"),
            "amount": pos.get("amount"),
            "pnl": pnl,
            "pm_live": True,
            "manual_close": True,
            "exit_time_tr": now_tr.isoformat(),
            "pm_spent": spent,
            "pm_size": pos.get("pm_size"),
            "pm_exit_price": res["price"],
            "pm_proceeds": proceeds,
            "pm_slug": pos.get("pm_slug"),
            "algo_name": pos.get("algo_name", spec.algo_name),
            "algo_num": 0,
            "settle_source": "pm_external_close" if res.get("external") else "manual_sell",
            "source_position_id": pos.get("source_position_id"),
            "mirrored_from_source": pos.get("mirrored_from_source"),
        })
        lines.append(
            f"{'✅' if pnl >= 0 else '❌'} {_sym_short(sym)}  {res['size']} share "
            f"@ {res['price']:.2f} → ${proceeds:.2f}  ({'+' if pnl >= 0 else ''}{pnl:.2f}$)"
        )
        print(f"[{spec.label} manuel] {_sym_short(sym)} kapatıldı: {pnl:+.2f}$")

    state["open_positions"] = kalan
    save_state(spec, state)
    save_history(spec, history)

    if lines:
        sep = "━" * 26
        tg_send(
            spec.label,
            f"{sep}\n✋ <b>{spec.label} — Manuel Kapatma</b>  🔴 GERÇEK PM\n"
            + "\n".join(lines)
            + f"\nBu tur: {'+' if tur_pnl >= 0 else ''}{tur_pnl:.2f}$  |  {_pm_bal_line()}\n{sep}",
        )
    out = {"closed": closed, "failed": failed, "pnl": round(tur_pnl, 2)}
    if failed:
        still = next(
            (
                p for p in kalan
                if targeted and _manual_close_match(
                    p, symbols=want, token_id=token_id, source=source, hour_tr=hour_tr,
                )
            ),
            None,
        )
        if still and still.get("pm_size"):
            left = still["pm_size"]
            out["remaining"] = left
            out["error"] = f"Kısmi satış — {left:g} share kaldı. Bir kez daha Manuel kapat."
        else:
            out["error"] = pmh.pm_last_order_error()
    elif targeted and closed == 0:
        out["error"] = "Pozisyon bulunamadı"
    return out


def _source_id_in_history(history: list, source_id: str) -> bool:
    """Gerçek kapanış var mı — 0$ hayalet reconcile tekrar açmayı engellemesin."""
    sid = str(source_id or "")
    if not sid:
        return False
    for t in reversed(history[-300:]):
        if str(t.get("source_position_id") or "") != sid:
            continue
        if _is_ghost_external_close(t):
            continue
        return True
    return False


def _is_ghost_external_close(t: dict) -> bool:
    if t.get("settle_source") != "pm_external_close":
        return False
    try:
        return float(t.get("pm_proceeds") or 0) <= 0.01
    except (TypeError, ValueError):
        return True


def _pos_age_sec(pos: dict) -> float | None:
    raw = pos.get("entry_time_tr") or ""
    if not raw:
        return None
    try:
        ts = datetime.fromisoformat(str(raw))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=_TZ_TR)
        now = datetime.now(timezone.utc).astimezone(_TZ_TR)
        return max(0.0, (now - ts).total_seconds())
    except Exception:
        return None


def recover_ghost_closes(spec: LiveSpec) -> int:
    """Satışsız reconcile ile düşen, zincirde hâlâ duran pozisyonu deftere geri yaz."""
    import pm_trader_helpers as pmh

    history = load_history(spec)
    state = load_state(spec)
    opens = list(state.get("open_positions") or [])
    open_sids = {str(p.get("source_position_id") or "") for p in opens}
    open_tids = {str(p.get("pm_token_id") or "") for p in opens if p.get("pm_token_id")}
    restored = 0
    keep_hist: list[dict] = []
    for t in history:
        if not _is_ghost_external_close(t):
            keep_hist.append(t)
            continue
        sid = str(t.get("source_position_id") or "")
        tid = str(t.get("pm_token_id") or "")
        if sid and sid in open_sids:
            keep_hist.append(t)
            continue
        if not tid and t.get("pm_slug"):
            hit = pmh.pm_live_position_by_slug(str(t["pm_slug"]))
            if hit:
                tid = str(hit["token_id"])
                t["pm_token_id"] = tid
        held = -1.0
        if tid:
            try:
                held = pmh.pm_conditional_shares(tid, refresh=True)
            except Exception:
                held = -1.0
            if held < 0.5:
                hit = pmh.pm_live_position_by_slug(str(t.get("pm_slug") or ""))
                if hit and str(hit["token_id"]) == tid:
                    held = float(hit["size"])
        if held < 0.5:
            keep_hist.append(t)
            continue
        if tid and tid in open_tids:
            continue
        pos = {
            "symbol": t.get("symbol"),
            "predicted_dir": t.get("predicted_dir"),
            "entry_price": t.get("entry_price"),
            "entry_time_tr": t.get("entry_time_tr"),
            "entry_hour_tr": t.get("entry_hour_tr"),
            "entry_dow": t.get("entry_dow"),
            "amount": t.get("amount"),
            "algo_name": t.get("algo_name"),
            "mirrored_from_source": t.get("mirrored_from_source"),
            "source_position_id": t.get("source_position_id"),
            "pm_slug": t.get("pm_slug"),
            "pm_token_id": tid,
            "pm_token_dir": t.get("predicted_dir"),
            "pm_size": held,
            "pm_entry_price": t.get("pm_entry_price") or t.get("source_price_now"),
            "pm_spent": t.get("pm_spent") or t.get("amount") or 0,
            "pm_live": True,
        }
        opens.append(pos)
        open_sids.add(sid)
        open_tids.add(tid)
        try:
            state["total_pnl"] = round(
                float(state.get("total_pnl") or 0) - float(t.get("pnl") or 0), 2
            )
        except (TypeError, ValueError):
            pass
        restored += 1
        print(f"[{spec.label} reconcile] {_sym_short(t.get('symbol') or '')} "
              f"hayalet kapanış geri alındı ({held:g} share)")
    if not restored:
        return 0
    state["open_positions"] = opens
    save_state(spec, state)
    save_history(spec, keep_hist)
    return restored


def reconcile_external_closes(spec: LiveSpec) -> dict:
    """Defterde açık, zincirde share yok ve gerçek SELL varsa satılmış say.

    Yeni alınan share CLOB'da birkaç saniye 0 görünebilir — satış teyidi
    yoksa defterden düşme. Hayalet kapanışı geri al.
    """
    import time
    import pm_trader_helpers as pmh

    recover_ghost_closes(spec)

    state = load_state(spec)
    opens = list(state.get("open_positions") or [])
    if not opens:
        return {"closed": 0, "pnl": 0.0}

    history = load_history(spec)
    now_tr = datetime.now(timezone.utc).astimezone(_TZ_TR)
    kalan: list[dict] = []
    lines: list[str] = []
    closed = 0
    tur_pnl = 0.0

    for pos in opens:
        tid = pos.get("pm_token_id")
        if not tid:
            kalan.append(pos)
            continue
        age = _pos_age_sec(pos)
        if age is not None and age < 120:
            kalan.append(pos)
            continue
        try:
            held = pmh.pm_conditional_shares(str(tid), refresh=True)
        except Exception:
            kalan.append(pos)
            continue
        if held < 0:
            kalan.append(pos)
            continue
        if 0 <= held < 0.5:
            time.sleep(1.2)
            try:
                held = pmh.pm_conditional_shares(str(tid), refresh=True)
            except Exception:
                held = -1.0
        if held < 0 or held >= 0.5:
            kalan.append(pos)
            continue

        fill = pmh.pm_recent_sell(str(tid))
        if not fill:
            print(
                f"[{spec.label} reconcile] {_sym_short(pos.get('symbol') or '')} "
                f"share 0 ama SELL yok — defterde kaldı",
                file=sys.stderr,
            )
            kalan.append(pos)
            continue

        spent = float(pos.get("pm_spent") or pos.get("amount") or 0)
        proceeds = float(fill["proceeds"])
        price = float(fill["price"])
        size = float(fill["size"])
        pnl = round(proceeds - spent, 2)
        tur_pnl += pnl
        closed += 1
        state["total_pnl"] = round(state.get("total_pnl", 0.0) + pnl, 2)
        history.append({
            "symbol": pos.get("symbol"),
            "predicted_dir": pos.get("predicted_dir"),
            "actual_dir": "MANUEL",
            "win": pnl > 0,
            "entry_price": pos.get("entry_price"),
            "entry_time_tr": pos.get("entry_time_tr"),
            "entry_hour_tr": pos.get("entry_hour_tr"),
            "entry_dow": pos.get("entry_dow"),
            "amount": pos.get("amount"),
            "pnl": pnl,
            "pm_live": True,
            "manual_close": True,
            "exit_time_tr": now_tr.isoformat(),
            "pm_spent": spent,
            "pm_size": size,
            "pm_exit_price": price,
            "pm_proceeds": proceeds,
            "pm_slug": pos.get("pm_slug"),
            "pm_token_id": tid,
            "algo_name": pos.get("algo_name", spec.algo_name),
            "algo_num": 0,
            "settle_source": "pm_external_close",
            "source_position_id": pos.get("source_position_id"),
            "mirrored_from_source": pos.get("mirrored_from_source"),
        })
        sym = pos.get("symbol") or ""
        lines.append(
            f"{'✅' if pnl >= 0 else '❌'} {_sym_short(sym)}  {size:g} share "
            f"@ {price:.2f} → ${proceeds:.2f}  ({'+' if pnl >= 0 else ''}{pnl:.2f}$)"
        )
        print(f"[{spec.label} reconcile] {_sym_short(sym)} PM'de satılmış — "
              f"defterden düşüldü {pnl:+.2f}$")

    if not closed:
        return {"closed": 0, "pnl": 0.0}

    state["open_positions"] = kalan
    save_state(spec, state)
    save_history(spec, history)
    if lines:
        sep = "━" * 26
        tg_send(
            spec.label,
            f"{sep}\n✋ <b>{spec.label} — PM'de kapanmış</b>  🔴 GERÇEK PM\n"
            + "\n".join(lines)
            + f"\nBu tur: {'+' if tur_pnl >= 0 else ''}{tur_pnl:.2f}$  |  {_pm_bal_line()}\n{sep}",
        )
    return {"closed": closed, "pnl": round(tur_pnl, 2)}


def _manual_close_match(
    pos: dict,
    *,
    symbols: set[str] | None,
    token_id: str | None,
    source: str | None,
    hour_tr: int | None,
) -> bool:
    tid = pos.get("pm_token_id")
    if not tid:
        return False
    if token_id and str(tid) != str(token_id):
        return False
    # Karttaki token yeterli; source/saat uyuşmazsa aynı token atlanmasın
    if not token_id:
        if source and str(pos.get("mirrored_from_source") or "") != str(source):
            return False
        if hour_tr is not None and pos.get("entry_hour_tr") != hour_tr:
            return False
    if symbols:
        sym = pos.get("symbol") or ""
        if sym.upper() not in symbols and _sym_short(sym).upper() not in symbols:
            return False
    return True


async def mirror_open_from_sanal(
    spec: LiveSpec,
    sanal_pos: dict,
    *,
    entry_price: float,
    now_tr: datetime | None = None,
) -> tuple[dict | None, str | None]:
    """Sanal pozisyon → gerçek PM (aynı sembol, yön, slot)."""
    if not is_live_active(spec):
        return None, "inactive"

    sym = sanal_pos.get("symbol") or ""
    direction = (sanal_pos.get("predicted_dir") or sanal_pos.get("pm_token_dir") or "").upper()
    if not sym or direction not in ("UP", "DOWN"):
        return None, "bad_pos"
    if entry_price <= 0:
        return None, "bad_entry"

    if now_tr is None:
        now_tr = datetime.now(timezone.utc).astimezone(_TZ_TR)
    now = datetime.now(timezone.utc)

    state = load_state(spec)
    if _live_has_sanal_pos(state, sanal_pos):
        return None, "exists"

    history = load_history(spec)
    hour_tr = int(sanal_pos.get("entry_hour_tr", now_tr.hour))
    dow = int(sanal_pos.get("entry_dow", now_tr.weekday()))
    is_weekend = bool(sanal_pos.get("entry_is_weekend", dow >= 5))

    base = _trade_amount(spec, history, sym)
    amount, hot_boost, cold_cut = resolve_slot_trade_amount(base, hour_tr, history)
    slot_amount_log(spec.label, hour_tr, base, amount, hot_boost, cold_cut)
    _, _, hata = _paths(spec)

    pos, err = try_pm_open(
        state,
        label=spec.label,
        hata_file=hata,
        sym=sym,
        direction=direction,
        entry_price=entry_price,
        hour_tr=hour_tr,
        dow=dow,
        is_weekend=is_weekend,
        now_tr=now_tr,
        now=now,
        extra={
            "algo_name": spec.algo_name,
            "algo_num": 0,
            "algo_signal": direction,
            "hot_hour_boost": hot_boost,
            "cold_hour_cut": cold_cut,
            "mirrored_from_sanal": True,
            "sanal_pm_slug": sanal_pos.get("pm_slug"),
        },
        amount=amount,
        pm_live=True,
        min_profit_ratio=spec.min_profit_ratio,
    )
    if pos:
        save_state(spec, state)
        name = _sym_short(sym)
        print(
            f"[{spec.label} mirror] {name} {direction} ${amount:.2f} "
            f"(kaynak API aynası)"
        )
    return pos, err


async def sync_open_from_sanal_state(spec: LiveSpec) -> list[tuple[str, str, float, dict]]:
    """Sanal defterdeki tüm açık pozisyonları live'a yansıt."""
    if not is_live_active(spec):
        print(f"[{spec.label} sync] live kapalı — atlandı")
        return []

    spath = _sanal_state_path(spec)
    if not os.path.exists(spath):
        return []
    try:
        with open(spath, encoding="utf-8") as f:
            sanal_state = json.load(f)
    except Exception:
        return []

    now_tr = datetime.now(timezone.utc).astimezone(_TZ_TR)
    opened: list[tuple[str, str, float, dict]] = []
    for sanal_pos in sanal_state.get("open_positions") or []:
        entry_price = float(sanal_pos.get("entry_price") or 0)
        if entry_price <= 0:
            continue
        pos, err = await mirror_open_from_sanal(
            spec, sanal_pos, entry_price=entry_price, now_tr=now_tr,
        )
        if pos:
            sym = sanal_pos["symbol"]
            direction = (sanal_pos.get("predicted_dir") or "").upper()
            opened.append((sym, direction, entry_price, pos))
        elif err and err not in ("exists", "inactive"):
            print(f"[{spec.label} sync] {sanal_pos.get('symbol')} — {err}")
    return opened


def _load_signal_module(spec: LiveSpec):
    if not spec.signal_module:
        return None
    import importlib
    return importlib.import_module(spec.signal_module)


def _open_for_symbol_slot(state: dict, sym: str, hour_tr: int) -> dict | None:
    """Aynı sembol+saat — kaynak fark etmez. Zıt yön hedge yasak."""
    for p in state.get("open_positions") or []:
        if p.get("symbol") == sym and p.get("entry_hour_tr") == hour_tr:
            return p
    return None


def _live_has_symbol_slot(state: dict, sym: str, hour_tr: int,
                          *, source: str | None = None) -> bool:
    """Bu sembol+saat zaten açık mı.

    source verilirse yalnızca o kaynak; verilmezse herhangi bir kaynak yeter
    (aynı saatte SOL UP + SOL DOWN hedge açılmasın).
    """
    for p in state.get("open_positions") or []:
        if p.get("symbol") != sym or p.get("entry_hour_tr") != hour_tr:
            continue
        if source is None or str(p.get("mirrored_from_source") or "") == str(source):
            return True
    return False


def _has_token_position(state: dict, token_id: str,
                        *, source: str | None = None) -> bool:
    for p in state.get("open_positions") or []:
        if str(p.get("pm_token_id") or "") != str(token_id):
            continue
        if source is None or str(p.get("mirrored_from_source") or "") == str(source):
            return True
    return False


def _recorded_shares(state: dict, token_id: str) -> float:
    """Defterde bu token için kayıtlı toplam share (tüm kaynaklar)."""
    total = 0.0
    for p in state.get("open_positions") or []:
        if str(p.get("pm_token_id") or "") == str(token_id):
            try:
                total += float(p.get("pm_size") or 0)
            except (TypeError, ValueError):
                pass
    return total


def _unrecorded_on_chain(pmh, state: dict, token_id: str) -> bool:
    """Zincirde defterin bilmediği share var mı.

    Emir gidip defter yazılamadan süreç ölmüşse (subprocess timeout) aynı
    tokena ikinci emir gitmemeli. Ama birden fazla algoritma aynı tokenı
    kasıtlı olarak üst üste alabildiği için mutlak bakiyeye bakılamaz;
    zincirdeki share defterde yazan toplamı aşıyorsa kayıt dışı emir var
    demektir. Okunamazsa engelleme (False).
    """
    try:
        held = pmh.pm_conditional_shares(token_id)
    except Exception:
        return False
    return held >= _recorded_shares(state, token_id) + 0.5


def mirror_book_keys(spec: LiveSpec) -> list[str]:
    """API 1. sıradaki kaynak — senkron olmazsa kayıtlı / spec defteri."""
    try:
        from coptc_guard import sync_mirror_api_top
        picked = sync_mirror_api_top()
        if picked:
            return picked
    except Exception:
        pass
    return [spec.mirror_book or "a2_05"]


def _order_books_by_wr(books: list[str]) -> list[str]:
    """Önceliği win rate belirler — çakışmada önce yüksek WR'li işlenir,
    bakiye biterse elenen düşük WR'li olur. WR okunamazsa seçim sırası kalır.
    """
    if len(books) < 2:
        return books
    try:
        import coptc_mirror as ms
        wr = {b.get("book"): b.get("wr") for b in ms.book_list() if b.get("book")}
    except Exception:
        return books
    return sorted(books, key=lambda b: (wr.get(b) is None, -(wr.get(b) or 0.0)))


def run_open_mirror(spec: LiveSpec, *, dry: bool = False) -> None:
    """Kaynak sunucudaki defteri birebir kopyala — yön yerelde hesaplanmaz.

    dry=True: emir gönderilmez, state yazılmaz — sadece ne yapılacağı basılır.
    """
    import coptc_mirror as ms
    import pm_trader_helpers as pmh

    now_tr = datetime.now(timezone.utc).astimezone(_TZ_TR)
    if skip_if_weekend_pause(spec.label, "open", now_tr):
        return
    if not is_live_active(spec):
        print(f"[{spec.label} mirror] live kapalı — atlandı")
        return
    if not ms.enabled():
        print(f"[{spec.label} mirror] MIRROR_API_TOKEN yok — atlandı")
        return

    books = _order_books_by_wr(mirror_book_keys(spec))
    hour_tr = ms.current_slot_hour(now_tr)

    # Önce tüm kaynaklar okunur; emir göndermeden önce sembol bazında
    # çelişki var mı bakılacak.
    by_symbol: dict[str, list[tuple[str, dict, dict]]] = {}
    for book in books:
        try:
            remote, skipped, meta = ms.open_positions_with_meta(
                book, expected_hour_tr=hour_tr, now_tr=now_tr,
            )
        except Exception as e:
            print(f"[{spec.label} mirror] {book} okunamadı: {e}", file=sys.stderr)
            continue
        slot = ms.active_slot(meta)
        pred = ms.slot_prediction_label(meta, hour_tr)
        window = slot.get("slot_tr") or f"{slot.get('slot_open_tr', '?')}-{slot.get('slot_close_tr', '?')}"
        print(
            f"[{spec.label} mirror] {now_tr:%H:%M} · tahmin {pred} · pencere {window} · kaynak {book}",
            flush=True,
        )
        if slot.get("status") and str(slot["status"]).lower() != "active":
            print(f"[{spec.label} mirror] {book} slot durumu: {slot.get('status')}", flush=True)
        for note in skipped:
            print(f"[{spec.label} mirror] {book} atlandı — {note}")
        for p in remote:
            sym = p.get("symbol_raw") or f"{p.get('symbol')}USDT"
            if str(p.get("dir") or "").upper() not in ("UP", "DOWN"):
                continue
            # Pozisyonun kendi slot bilgisi boşsa defterin aktif slotundan
            # tamamla — aşağıda hangi kaynağa ait olduğu karışmasın.
            p["slot_tr"] = p.get("slot_tr") or slot.get("slot_tr")
            p["prediction_tr"] = p.get("prediction_tr") or slot.get("prediction_tr")
            by_symbol.setdefault(sym, []).append((book, p, meta))

    local_dirs: dict[str, set[str]] = {}
    local_state = load_state(spec)
    for lp in local_state.get("open_positions") or []:
        if lp.get("entry_hour_tr") != hour_tr:
            continue
        lsym = lp.get("symbol") or ""
        ld = str(lp.get("predicted_dir") or lp.get("pm_token_dir") or "").upper()
        if not lsym or ld not in ("UP", "DOWN"):
            continue
        local_dirs.setdefault(lsym, set()).add(ld)

    if not by_symbol:
        print(f"[{spec.label} mirror] kaynaklarda kopyalanacak pozisyon yok")
        return

    # Zıt yön = çelişkili sinyal; o sembolde hiçbir kaynak açılmaz.
    rank = {b: i for i, b in enumerate(books)}
    plan: list[tuple[str, str, dict, dict]] = []
    for sym, entries in by_symbol.items():
        dirs = {str(p.get("dir")).upper() for _, p, _ in entries}
        dirs |= local_dirs.get(sym, set())
        if len(dirs) > 1:
            detail = ", ".join(f"{b}:{str(p.get('dir')).upper()}" for b, p, _ in entries)
            if local_dirs.get(sym):
                detail += f", açık:{'/'.join(sorted(local_dirs[sym]))}"
            print(f"[{spec.label} mirror] {_sym_short(sym)} — kaynaklar çelişiyor "
                  f"({detail}), atlandı")
            continue
        plan.extend((sym, book, p, meta) for book, p, meta in entries)
    if not plan:
        print(f"[{spec.label} mirror] {now_tr:%H:%M} — çelişki sonrası açılacak sembol kalmadı")
        return
    # Yüksek WR'li kaynak önce sıraya girsin — bakiye biterse o değil diğeri elensin.
    plan.sort(key=lambda t: rank.get(t[1], len(books)))

    reconcile_external_closes(spec)
    history = load_history(spec)
    state = load_state(spec)
    _, _, hata = _paths(spec)
    pmh.PM_DRY_RUN = False
    min_profit = pmh.load_min_profit_pct()
    profit_cap = pmh.max_price_for_profit_pct(min_profit) if min_profit > 0 else None

    opened: list[tuple[str, str, float, dict]] = []
    for sym, book, p, meta in plan:
        direction = str(p.get("dir") or "").upper()
        existing = _open_for_symbol_slot(state, sym, hour_tr)
        if existing:
            ex_src = existing.get("mirrored_from_source") or "?"
            ex_dir = existing.get("predicted_dir") or existing.get("pm_token_dir") or "?"
            if str(ex_src) != str(book) or str(ex_dir).upper() != direction:
                print(
                    f"[{spec.label} mirror] {_sym_short(sym)} zaten açık "
                    f"({ex_src} {ex_dir}) — {book} {direction} açılmadı",
                    flush=True,
                )
            continue
        sid = p.get("position_id")
        if sid and _source_id_in_history(history, sid):
            print(f"[{spec.label} mirror] {_sym_short(sym)} — bu kaynak id bu slotta "
                  "zaten kapanmış, tekrar açılmadı")
            continue

        base = _trade_amount(spec, history, sym, source=book)
        _sk, amount, hot_boost, cold_cut, gate_note = resolve_open_slot_gates(
            history, hour_tr, base
        )
        if _sk:
            print(f"[{spec.label} mirror] {_sym_short(sym)} — slot kapısı")
            continue
        slot_amount_log(spec.label, hour_tr, base, amount, hot_boost, cold_cut)

        token_id = str(p["pm_token_id"])
        if _has_token_position(state, token_id, source=book):
            continue
        if not dry and _unrecorded_on_chain(pmh, state, token_id):
            print(f"[{spec.label} mirror] {_sym_short(sym)} — zincirde deftere "
                  f"yazılmamış pozisyon var, atlandı")
            continue
        guards = ms.order_guards(p, amount, meta)
        if guards is None:
            print(f"[{spec.label} mirror] {_sym_short(sym)} — kaynak fiyat sınırı "
                  "göndermedi, emir açılmadı", file=sys.stderr)
            continue
        # Borsa 5 share minimumu: bahsimiz kaynağın verdiği alt sınırın altındaysa
        # maliyet niyeti aşacak ve emir zaten max_spend'e takılacak.
        min_stake = p.get("min_stake_usd")
        if min_stake and amount < float(min_stake):
            print(f"[{spec.label} mirror] {_sym_short(sym)} — bahis ${amount:.2f} < "
                  f"kaynağın alt sınırı ${float(min_stake):.2f}, emir açılmadı")
            continue
        # Kaynağın tavanı ile asgari kâr tavanının sıkı olanı geçerli.
        if profit_cap is not None:
            guards["max_price"] = min(float(guards["max_price"]), profit_cap)
        if dry:
            print(f"[{spec.label} mirror·DRY] {book} · {_sym_short(sym)} {direction} "
                  f"${amount:.2f} token {token_id[:12]}… kaynak {p.get('pm_entry_price')} "
                  f"şimdi {p.get('pm_price_now')} — emir GÖNDERİLMEDİ")
            continue
        order = pmh.pm_place_order(
            token_id, amount, str(p.get("pm_tick_size") or "0.01"),
            bool(p.get("pm_neg_risk")), label=spec.label, hata_file=hata,
            min_profit_pct=min_profit or None,
            **guards,
        )
        if not order:
            reason = getattr(pmh, "_PM_LAST_ORDER_ERROR", None)
            print(f"[{spec.label} mirror] {_sym_short(sym)} — açılmadı"
                  + (f": {reason}" if reason else " (order başarısız)"), file=sys.stderr)
            continue

        entry_price = float(p.get("spot_entry") or 0)
        pos = {
            "symbol": sym,
            "predicted_dir": direction,
            "entry_price": entry_price,
            "entry_time_tr": now_tr.isoformat(),
            "entry_hour_tr": hour_tr,
            "entry_dow": now_tr.weekday(),
            "entry_is_weekend": now_tr.weekday() >= 5,
            "amount": amount,
            "algo_name": p.get("algo_name") or spec.algo_name,
            "algo_num": 0,
            "algo_signal": direction,
            "hot_hour_boost": hot_boost,
            "cold_hour_cut": cold_cut,
            "mirrored_from_source": book,
            "source_position_id": p.get("position_id"),
            "prediction_tr": p.get("prediction_tr"),
            "slot_tr": p.get("slot_tr"),
            "source_entry_price": p.get("pm_entry_price"),
            "source_price_now": p.get("pm_price_now"),
            "pm_slug": p.get("pm_slug"),
            "pm_title": p.get("pm_title", ""),
            "pm_token_id": token_id,
            "pm_token_dir": direction,
            "pm_size": order["size"],
            "pm_entry_price": order["price"],
            "pm_order_id": order["order_id"],
            "pm_spent": order["spent"],
            "pm_live": True,
        }
        state["open_positions"].append(pos)
        # Para harcandı — tur burada kesilse bile kayıt kalsın, yoksa sonraki
        # poll turu aynı sembolü ikinci kez açar.
        save_state(spec, state)
        opened.append((sym, direction, entry_price, pos))
        print(f"[{spec.label} mirror] {book} · {_sym_short(sym)} {direction} ${amount:.2f} "
              f"← kaynak {p.get('pm_entry_price')} / bizim {order['price']}")

    if not opened:
        print(f"[{spec.label} mirror] {now_tr:%H:%M} — açılan yok")
        return

    save_state(spec, state)
    sep = "━" * 26
    lines = []
    for sym, direction, entry_price, pos in opened:
        dir_icon = "📈" if direction == "UP" else "📉"
        pm_line = pm_tg_stake(pos) or f"💵 ${pos.get('amount', spec.default_amount):.0f}"
        src = pos.get("mirrored_from_source") or "?"
        lines.append(
            f"{dir_icon} <b>{_sym_short(sym)}</b>  {direction}  🪞 {src}\n   {pm_line}"
        )
    books_txt = ", ".join(books)
    tg_send(
        spec.label,
        f"{sep}\n🪞 <b>{spec.label} — {now_tr:%H:%M} MIRROR</b>  🔴 GERÇEK PM\n"
        + "\n".join(lines)
        + f"\n(kaynak defter: {books_txt})\n{sep}\n{_pm_bal_line()}\n{sep}",
    )
    print(f"[{spec.label} mirror] {len(opened)} açıldı (kaynak {books_txt})")


async def run_open_direct(spec: LiveSpec) -> None:
    """Live açıkken sanal yok — motor sinyalini doğrudan PM'e gönder."""
    mod = _load_signal_module(spec)
    if mod is None:
        print(f"[{spec.label} direct] signal_module yok — mirror'a düş")
        await run_open(spec)
        return

    now_tr = datetime.now(timezone.utc).astimezone(_TZ_TR)
    if skip_if_weekend_pause(spec.label, "open", now_tr):
        return
    if not is_live_active(spec):
        print(f"[{spec.label} direct] live kapalı — atlandı")
        return

    hour_tr = now_tr.hour
    dow = now_tr.weekday()
    is_weekend = dow >= 5
    now = datetime.now(timezone.utc)
    saat = now_tr.strftime("%H:%M")
    history = load_history(spec)
    state = load_state(spec)

    cold_skip, _, _, _, cold_note = resolve_open_slot_gates(history, hour_tr, 0)
    if cold_skip:
        print(f"[{spec.label} direct] {saat} — {cold_note} · işlem yok")
        return

    symbols = getattr(mod, "SYMBOLS", [])
    resolve = getattr(mod, "resolve_live_signal", None)
    if not symbols or resolve is None:
        print(f"[{spec.label} direct] {spec.signal_module} eksik SYMBOLS/resolve")
        return

    _, _, hata = _paths(spec)
    opened: list[tuple[str, str, float, dict]] = []

    for sym in symbols:
        direction, price, algo_name = await resolve(sym)
        if direction is None:
            continue
        if _live_has_symbol_slot(state, sym, hour_tr):
            continue
        try:
            klines = await _fetch_klines(sym, "1h", 3)
            entry_price = klines[-2]["close"] if klines and len(klines) >= 2 else price
        except Exception:
            entry_price = price
        if not entry_price or float(entry_price) <= 0:
            continue

        base = _trade_amount(spec, history, sym)
        _sk, amount, hot_boost, cold_cut, gate_note = resolve_open_slot_gates(
            history, hour_tr, base
        )
        if _sk:
            print(f"[{spec.label} direct] {sym} — slot kapısı")
            continue
        if gate_note and hot_boost:
            print(f"[{spec.label} direct] 🔥 {gate_note}")
        else:
            slot_amount_log(spec.label, hour_tr, base, amount, hot_boost, cold_cut)

        pos, err = try_pm_open(
            state,
            label=spec.label,
            hata_file=hata,
            sym=sym,
            direction=direction,
            entry_price=float(entry_price),
            hour_tr=hour_tr,
            dow=dow,
            is_weekend=is_weekend,
            now_tr=now_tr,
            now=now,
            extra={
                "algo_name": algo_name or spec.algo_name,
                "algo_num": 0,
                "algo_signal": direction,
                "hot_hour_boost": hot_boost,
                "cold_hour_cut": cold_cut,
                "direct_signal": True,
            },
            amount=amount,
            pm_live=True,
            min_profit_ratio=spec.min_profit_ratio,
        )
        if pos:
            opened.append((sym, direction, float(entry_price), pos))
            print(f"[{spec.label} direct] {_sym_short(sym)} {direction} ${amount:.2f}")
        elif err and err not in ("exists",):
            print(f"[{spec.label} direct] {_sym_short(sym)} — {err}")

    if opened:
        save_state(spec, state)

    if not opened:
        print(f"[{spec.label} direct] {saat} — açılan yok")
        return

    next_h = f"{(hour_tr + 1) % 24:02d}:00"
    lines = []
    for sym, direction, entry_price, pos in opened:
        name = _sym_short(sym)
        dir_icon = "📈" if direction == "UP" else "📉"
        hw, ht = get_stats(history, sym, hour_tr)
        sw, st = get_symbol_stats(history, sym)
        pm_line = pm_tg_stake(pos) or f"💵 ${pos.get('amount', spec.default_amount):.0f}"
        lines.append(
            f"{dir_icon} <b>{name}</b>  {direction}  📊 {spec.algo_name}  giriş:{entry_price:.2f}\n"
            f"   {pm_line}\n   🕐 {_wr(hw, ht)}  |  genel: {_wr(sw, st)}"
        )
    sep = "━" * 26
    tg_send(
        spec.label,
        f"{sep}\n🆕 <b>{spec.label} — {saat}-{next_h}</b>  🔴 GERÇEK PM (doğrudan)\n"
        f"{pm_live_amount_range_str(spec.amount_system)}\n"
        + "\n".join(lines)
        + f"\n{sep}\n{_pm_bal_line()}\n{sep}",
    )
    print(f"[{spec.label} direct] {len(opened)} açıldı")


async def run_open(spec: LiveSpec) -> None:
    """Live open — sanal defterle senkron (bağımsız sinyal yok)."""
    now_tr = datetime.now(timezone.utc).astimezone(_TZ_TR)
    if skip_if_weekend_pause(spec.label, "open", now_tr):
        return
    if not _pm_enabled(spec):
        print(f"[{spec.label} open] dashboard kapalı ({spec.amount_system}) — atlandı")
        return

    saat = now_tr.strftime("%H:%M")
    hour_tr = now_tr.hour
    history = load_history(spec)
    opened = await sync_open_from_sanal_state(spec)

    if not opened:
        sanal_n = 0
        spath = _sanal_state_path(spec)
        if os.path.exists(spath):
            try:
                with open(spath, encoding="utf-8") as f:
                    sanal_n = len(json.load(f).get("open_positions") or [])
            except Exception:
                pass
        print(
            f"[{spec.label} open] {saat} — live açılan yok"
            + (f" (sanal {sanal_n} açık)" if sanal_n else "")
        )
        return

    next_h = f"{(hour_tr + 1) % 24:02d}:00"
    lines = []
    for sym, direction, entry_price, pos in opened:
        name = _sym_short(sym)
        dir_icon = "📈" if direction == "UP" else "📉"
        hw, ht = get_stats(history, sym, hour_tr)
        sw, st = get_symbol_stats(history, sym)
        pm_line = pm_tg_stake(pos) or f"💵 ${pos.get('amount', spec.default_amount):.0f}"
        lines.append(
            f"{dir_icon} <b>{name}</b>  {direction}  📊 {spec.algo_name}  giriş:{entry_price:.2f}\n"
            f"   {pm_line}\n   🕐 {_wr(hw, ht)}  |  genel: {_wr(sw, st)}"
        )
    sep = "━" * 26
    tg_send(
        spec.label,
        f"{sep}\n🆕 <b>{spec.label} — {saat}-{next_h}</b>  🔴 GERÇEK PM  "
        f"{pm_live_amount_range_str(spec.amount_system)}\n"
        + "\n".join(lines)
        + f"\n(kaynak API aynası)\n"
        + f"{sep}\n{_pm_bal_line()}\n{sep}",
    )
    print(f"[{spec.label} open] {len(opened)} açıldı (sanal sync)")


def main(spec: LiveSpec) -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "mirror"
    if mode == "close":
        asyncio.run(run_close(spec))
    elif mode == "manual-close":
        run_manual_close(spec, sys.argv[2:] or None)
    elif mode == "mirror":
        run_open_mirror(spec, dry="--dry" in sys.argv[2:])
    else:
        print(f"[{spec.label}] yalnızca close | mirror | manual-close — '{mode}' yok (yerel algo kaldırıldı)",
              file=sys.stderr)
        sys.exit(2)
