"""Sanal defterlerin nakdini geçmişten yeniden hesaplar.

Neden: kısmi kâr-al (TP1) sonrası tam kapanış marjın tamamını nakde geri
ekliyordu; marjın yarısı kısmi kapanışta zaten dönmüştü. Her kısmi kapanış
deftere ~yarım marj kadar hayali para yazdı ve "en çok kazanan" sıralamasını
bozdu. Kod düzeltildi; bu betik geçmişe işlemiş sapmayı temizler.

Doğru nakit = START_CASH + (kapanan işlemlerin net toplamı) - (açık marjlar)

Servis DURDURULMUŞ haldeyken çalıştırılmalı, yoksa süreç üzerine yazar.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "poly" / "algo_paper_state.json"
SRC = ROOT / "poly" / "algo_paper.py"


def _const(name: str) -> float:
    m = re.search(rf"^{name}\s*=\s*([0-9.]+)", SRC.read_text(), re.M)
    if not m:
        raise SystemExit(f"{name} bulunamadı: {SRC}")
    return float(m.group(1))


def main() -> int:
    margin = _const("MARGIN")
    start_cash = _const("START_CASH")
    state = json.loads(STATE.read_text())
    books = state.get("algos") or {}

    backup = STATE.with_suffix(f".json.bak.{int(time.time())}")
    shutil.copy2(STATE, backup)
    print(f"yedek: {backup.name}")
    print(f"MARGIN={margin:.0f}  START_CASH={start_cash:.0f}\n")

    fixed = []
    for book in books.values():
        history = book.get("history") or []
        if len(history) >= 400:
            print(f"UYARI {book.get('code')}: geçmiş 400'de kırpılmış, atlanıyor")
            continue
        realized = sum(float(h.get("net") or 0) for h in history)
        locked = sum(float(p.get("margin") or margin) for p in book.get("positions") or [])
        want = round(start_cash + realized - locked, 2)
        have = float(book.get("cash") or 0)
        if abs(want - have) > 0.01:
            fixed.append((str(book.get("code")), have, want))
            book["cash"] = want
        book["fees"] = round(sum(float(h.get("commission") or 0) for h in history), 2)

    fixed.sort(key=lambda r: r[2] - r[1])
    if fixed:
        print(f"{'kod':<9}{'eski':>11}{'düzeltilmiş':>13}{'fark':>11}")
        for code, have, want in fixed:
            print(f"{code:<9}{have:>11.2f}{want:>13.2f}{want - have:>+11.2f}")
    STATE.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")))
    print(f"\ndüzeltilen defter: {len(fixed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
