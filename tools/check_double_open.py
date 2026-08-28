"""Çift açılma izini düzeltme tarihine göre ayırır.

`_FLAT_GRACE_MS` koruması 28-08 19:41'de (yerel) yayına girdi. Soru şu: o andan
sonra hâlâ hayali `binance_flat` ya da 2x büyüklükte kayıt oluşuyor mu?
"""
from __future__ import annotations

import json
from pathlib import Path

STATE = Path(__file__).resolve().parent.parent / "poly" / "algo_live_state.json"
FIX = "08-28 19:41"
BEKLENEN = (600.0, 750.0, 900.0)


def implied(h: dict) -> float | None:
    entry = float(h.get("entry") or 0)
    exit_px = float(h.get("exit") or 0)
    gross = float(h.get("gross") or 0)
    if entry <= 0 or exit_px <= 0 or gross == 0:
        return None
    move = (exit_px - entry) / entry
    if str(h.get("side") or "") == "SHORT":
        move = -move
    if abs(move) < 1e-6:
        return None
    return gross / move


def kat(h: dict) -> float | None:
    n = implied(h)
    if n is None:
        return None
    return n / min(BEKLENEN, key=lambda b: abs(n / b - 1))


def main() -> None:
    book = json.loads(STATE.read_text())
    hist = book.get("history") or []
    print(f"düzeltme çizgisi: {FIX} (yerel)\n")

    for label, rows in (
        ("DÜZELTMEDEN ÖNCE", [h for h in hist if str(h.get("t") or "") < FIX]),
        ("DÜZELTMEDEN SONRA", [h for h in hist if str(h.get("t") or "") >= FIX]),
    ):
        flats = [h for h in rows if str(h.get("reason")) == "binance_flat"]
        genc = [h for h in flats if int(h.get("mins") or 0) <= 1]
        dbl = [h for h in rows if (kat(h) or 0) > 1.6]
        print(f"=== {label} — {len(rows)} kayıt ===")
        print(f"    binance_flat            : {len(flats)}")
        print(f"    bunlardan 0-1 dk yaşinda: {len(genc)}   <- hayali flat izi")
        print(f"    2x büyüklükte kayıt     : {len(dbl)}   <- çift açılma izi")
        for h in dbl:
            print(f"        {h.get('t')}  {h.get('symbol')}  {h.get('reason')}  net {h.get('net')}  ({kat(h):.2f}x)")
        print()

    son = [str(h.get("t")) for h in hist if h.get("t")]
    print(f"en yeni kayıt: {max(son) if son else '-'}")
    print("\naçık pozisyonların büyüklüğü:")
    for p in book.get("positions") or []:
        n = float(p.get("qty") or 0) * float(p.get("entry") or 0)
        k = n / min(BEKLENEN, key=lambda b: abs(n / b - 1))
        print(f"    {str(p.get('base')):<7} notional {n:>8.1f}  {k:.2f}x  açılış {p.get('opened')}")


if __name__ == "__main__":
    main()
