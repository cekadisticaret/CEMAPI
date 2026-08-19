#!/usr/bin/env python3
"""CoptC Live Control — API mirror tek giriş noktası.

Live AÇIK: :02:08–:08:00 arası 10 sn'de bir kaynak API → PM mirror.
A2#05 / V2 :02 açar; A1 (analiz1) :05 açar — poll ikisini de kapsar.
Live KAPALI: işlem açılmaz.

Modlar
    close       :01   live kapat + redeem
    open        :02   live-open ile aynı
    live-open   :02   :02:08…:08:00 API poll + mirror
    settle      :12   live kapanış tekrarı
    status             live defter özeti
"""
from __future__ import annotations

import contextlib
import fcntl
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_DIR = os.path.dirname(os.path.abspath(__file__))
_POLY = os.path.join(_DIR, "poly")
_ENV = os.path.join(_DIR, ".env")
_TZ = ZoneInfo("Europe/Istanbul")
_LOCK = os.path.join(_POLY, ".coptc_open.lock")
_LIVE_SCRIPT = "coptc_live.py"
_LIVE_GROUP = "coptc_live"
_MIRROR_TICK_TIMEOUT = 170


def _load_env() -> None:
    if not os.path.exists(_ENV):
        return
    with open(_ENV, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def _live_open() -> bool:
    sys.path.insert(0, _POLY)
    from coptc_guard import is_group_paused
    return not is_group_paused(_LIVE_GROUP)


def _mirror_mode() -> bool:
    sys.path.insert(0, _POLY)
    try:
        import coptc_mirror
        return coptc_mirror.enabled()
    except Exception:
        return False


def _run(script: str, *args: str, timeout: int = 600) -> int:
    cmd = [sys.executable, os.path.join(_POLY, script), *args]
    try:
        r = subprocess.run(cmd, cwd=_POLY, timeout=timeout)
        return r.returncode
    except subprocess.TimeoutExpired:
        print(f"[CoptC] {script} {' '.join(args)} — zaman aşımı ({timeout}s)")
        return 1
    except Exception as e:
        print(f"[CoptC] {script} {' '.join(args)} — hata: {e}")
        return 1


class _GateBusy(RuntimeError):
    """Başka bir açılış turu sürüyor."""


@contextlib.contextmanager
def _open_gate(wait: int = 0):
    """Kilit alınamazsa tur iptal — kilitsiz devam iki paralel tur demek,
    ikisi de aynı state'i okuyup aynı sembole emir girer."""
    f = open(_LOCK, "w")
    got = False
    try:
        deadline = time.monotonic() + wait
        while True:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                got = True
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    break
                time.sleep(1)
        if not got:
            raise _GateBusy
        yield
    finally:
        if got:
            with contextlib.suppress(Exception):
                fcntl.flock(f, fcntl.LOCK_UN)
        f.close()


def _stamp(mode: str) -> None:
    print(f"\n[CoptC {mode}] {datetime.now(_TZ):%Y-%m-%d %H:%M:%S} İST", flush=True)


def _mirror_poll_window(now_tr: datetime | None = None) -> tuple[datetime, datetime]:
    """Bu saatin mirror poll penceresi: :02:08 … :08:00.

    A2#05/V2 :02 açar; analiz1 (A1) :05 açar. Eski tavan :05:00 A1'i
    tam açıldığı anda kesiyordu.
    """
    now_tr = now_tr or datetime.now(_TZ)
    base = now_tr.replace(minute=0, second=0, microsecond=0)
    return base.replace(minute=2, second=8), base.replace(minute=8, second=0)


def _wait_until(target: datetime) -> None:
    while True:
        now_tr = datetime.now(_TZ)
        if now_tr >= target:
            return
        time.sleep(min(1.0, (target - now_tr).total_seconds()))


def _redeem(label: str) -> None:
    try:
        sys.path.insert(0, _POLY)
        import json
        from pm_trader_helpers import pm_cash_out_pending
        sp = os.path.join(_POLY, "coptc_live_state.json")
        open_ids: set[str] = set()
        if os.path.exists(sp):
            st = json.load(open(sp, encoding="utf-8"))
            open_ids = {
                str(p["pm_token_id"]) for p in st.get("open_positions") or []
                if p.get("pm_token_id")
            }
        pm_cash_out_pending(label=label, open_token_ids=open_ids, wait=True)
    except Exception as e:
        print(f"[CoptC] redeem: {e}", flush=True)


def run_close() -> None:
    _stamp("close")
    _run(_LIVE_SCRIPT, "close")
    _redeem("CoptC")


def run_open() -> None:
    run_live_open()


def run_live_open() -> None:
    _stamp("live-open")
    if not _live_open():
        print("[CoptC] live kapalı — mirror poll atlandı")
        return
    if not _mirror_mode():
        print("[CoptC] MIRROR_API_TOKEN yok — mirror açılamaz", flush=True)
        return

    start, end = _mirror_poll_window()
    now_tr = datetime.now(_TZ)
    if now_tr < start:
        print(f"[CoptC] mirror poll — {start:%H:%M:%S}'e kadar bekleniyor", flush=True)
        _wait_until(start)
    elif now_tr >= end:
        print(f"[CoptC] mirror poll penceresi kapalı ({start:%H:%M}–{end:%H:%M})", flush=True)
        return

    try:
        with _open_gate(wait=45):
            poll_at = max(start, datetime.now(_TZ))
            n = 0
            print(
                f"[CoptC] mirror poll başladı — {start:%H:%M:%S}…{end:%H:%M:%S}, 10 sn aralık",
                flush=True,
            )
            while poll_at <= end:
                if poll_at > datetime.now(_TZ):
                    _wait_until(poll_at)
                if datetime.now(_TZ) > end:
                    break
                n += 1
                tick = datetime.now(_TZ)
                print(f"[CoptC] mirror poll #{n} @ {tick:%H:%M:%S}", flush=True)
                # Emir yeniden denemeleri ~95 sn sürebiliyor; kısa timeout turu
                # state yazılmadan öldürür ve sonraki tur aynı emri tekrar girer.
                _run(_LIVE_SCRIPT, "mirror", timeout=_MIRROR_TICK_TIMEOUT)
                # Tur uzun sürdüyse kaçan slotları atla — yoksa aralıksız ateşler.
                poll_at += timedelta(seconds=10)
                now_tr = datetime.now(_TZ)
                while poll_at <= now_tr:
                    poll_at += timedelta(seconds=10)
            print(f"[CoptC] mirror poll bitti — {n} tur", flush=True)
    except _GateBusy:
        print("[CoptC] başka bir açılış turu sürüyor — bu tur atlandı", flush=True)


def run_settle() -> None:
    _stamp("settle")
    _run(_LIVE_SCRIPT, "close")
    _redeem("CoptC-settle")


def run_cash_out() -> None:
    _stamp("cash-out")
    _redeem("CoptC-cash-out")


def run_status() -> None:
    import json

    _stamp("status")
    sp = os.path.join(_POLY, "coptc_live_state.json")
    hp = os.path.join(_POLY, "coptc_live_history.json")
    st = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
    hist = json.load(open(hp, encoding="utf-8")) if os.path.exists(hp) else []
    wins = sum(1 for t in hist if t.get("win"))
    wr = f"%{wins / len(hist) * 100:.1f}" if hist else "—"
    print(f"  CoptC Live       bakiye ${st.get('balance', 0):>8.2f} · "
          f"açık {len(st.get('open_positions') or []):>2} · "
          f"{len(hist):>3} işlem · WR {wr}")
    print(f"  CoptC Live       gerçek PM: {'AÇIK' if _live_open() else 'KAPALI'}")
    print(f"  Mirror API       {'AÇIK' if _mirror_mode() else 'KAPALI'}")


MODES = {
    "close": run_close,
    "open": run_open,
    "live-open": run_live_open,
    "settle": run_settle,
    "cash-out": run_cash_out,
    "redeem": run_cash_out,
    "status": run_status,
}

if __name__ == "__main__":
    _load_env()
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    fn = MODES.get(mode)
    if not fn:
        print(f"Geçersiz mod: {mode}\nKullanım: runner.py [{' | '.join(MODES)}]")
        sys.exit(2)
    fn()
