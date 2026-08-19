#!/usr/bin/env python3
"""CoptC Live Control — gerçek Polymarket · kaynak API aynası.

Yön yerelde hesaplanmaz; dashboard'da seçilen kaynak defterin (bursaapp mirror API)
o saat slotundaki pozisyonları birebir kopyalanır.

Cron: close :01 · mirror poll :02:08…:08 · settle :12
"""
from __future__ import annotations

from coptc_live_core import LiveSpec, main

SPEC = LiveSpec(
    label="CoptC Live",
    amount_system="coptc_live",
    env_flag="COPTC_LIVE_ENABLED",
    default_amount=5.0,
    book_tag="coptc_live",
    min_profit_ratio=None,
)

if __name__ == "__main__":
    main(SPEC)
