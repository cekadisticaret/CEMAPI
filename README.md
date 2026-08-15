# CoptC Live Control

Kaynak API (bursaapp mirror) üzerinden Polymarket gerçek para işlemleri.

| Bileşen | Dosya |
|---|---|
| Cron | `runner.py` |
| Live mirror | `poly/coptc_live.py` → `poly/coptc_live_core.py` |
| API istemcisi | `poly/coptc_mirror.py` |
| PM emirleri | `poly/pm_trader_helpers.py` |
| Ayarlar | `poly/coptc_control.json` |
| Tutarlar | `poly/coptc_settings.json` |
| Dashboard | `web/dashboard.py` |

Cron: `:02` kapat · `:05` bekle · `:06` API mirror · `:12` settle

Dashboard: `python3 web/dashboard.py` → port 8080
