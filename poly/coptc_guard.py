"""CoptC Live Control — dashboard live anahtarı ve açılış engeli."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta

_DIR = os.path.dirname(os.path.abspath(__file__))
_CONTROL_FILE = os.path.join(_DIR, "coptc_control.json")
_LEGACY_CONTROL = os.path.join(_DIR, "pm_system_control.json")
_GROUP = "coptc_live"
_LABEL = "CoptC Live"
_TZ_TR = timezone(timedelta(hours=3))
WEEKEND_RESUME_HOUR = 11  # Cum 22:00 – Pzt 11:00 İST

MIRROR_BOOKS_KEY = "coptc_mirror_books"
MIRROR_BOOK_KEY = "coptc_mirror_book"
MIRROR_BOOK_DEFAULT = "a2_05"
MIRROR_BOOKS_MAX = 3


def _load_control() -> dict:
    defaults = {
        "coptc_live_paused": True,
        "coptc_active_book": "live",
        "coptc_live_on": False,
        "coptc_mirror_book": "a2_05",
        "coptc_weekend_pause_enabled": False,
        "updated_at_tr": "",
        "updated_by": "",
    }
    path = _CONTROL_FILE if os.path.exists(_CONTROL_FILE) else _LEGACY_CONTROL
    if not os.path.exists(path):
        return defaults
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Eski b1_05 anahtarları → coptc_live
            if "coptc_live_paused" not in data and "b1_05_live_paused" in data:
                data["coptc_live_paused"] = data["b1_05_live_paused"]
            if data.get("coptc_active_book") == "b1_05":
                data["coptc_active_book"] = "live"
            defaults.update(data)
    except Exception:
        pass
    return defaults


def _save_control(data: dict) -> None:
    with open(_CONTROL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_group_paused(group: str) -> bool:
    if group != _GROUP:
        return True
    return bool(_load_control().get("coptc_live_paused", True))


def is_dashboard_live_open(label: str) -> bool:
    if (label or "").strip().lower() not in (_LABEL.lower(), "coptc live control"):
        return False
    return not is_group_paused(_GROUP)


def can_open_trade(label: str, tg_send=None) -> bool:
    if not is_dashboard_live_open(label):
        print(f"[CoptC] {label} — live kapalı", file=__import__("sys").stderr)
        return False
    return True


def is_weekend_pause_enabled() -> bool:
    return bool(_load_control().get("coptc_weekend_pause_enabled", False))


def set_weekend_pause_enabled(enabled: bool, *, source: str = "") -> dict:
    data = _load_control()
    data["coptc_weekend_pause_enabled"] = bool(enabled)
    data["updated_at_tr"] = datetime.now(_TZ_TR).isoformat()
    data["updated_by"] = source or "coptc"
    _save_control(data)
    return data


def in_weekend_window(now_tr: datetime | None = None) -> bool:
    """Cuma 22:00 – Pazartesi 11:00 İST arası mı?"""
    if now_tr is None:
        now_tr = datetime.now(_TZ_TR)
    elif now_tr.tzinfo is None:
        now_tr = now_tr.replace(tzinfo=_TZ_TR)
    else:
        now_tr = now_tr.astimezone(_TZ_TR)
    dow = now_tr.weekday()
    h = now_tr.hour
    if dow == 4 and h >= 22:
        return True
    if dow in (5, 6):
        return True
    if dow == 0 and h < WEEKEND_RESUME_HOUR:
        return True
    return False


def weekend_status(now_tr: datetime | None = None) -> dict:
    if now_tr is None:
        now_tr = datetime.now(_TZ_TR)
    elif now_tr.tzinfo is None:
        now_tr = now_tr.replace(tzinfo=_TZ_TR)
    else:
        now_tr = now_tr.astimezone(_TZ_TR)
    enabled = is_weekend_pause_enabled()
    in_win = in_weekend_window(now_tr)
    active = enabled and in_win
    window = f"Cum 22:00 – Pzt {WEEKEND_RESUME_HOUR:02d}:00 İST"
    if not enabled:
        msg = "Kapalı — live açıkken hafta sonu dahil sürekli çalışır."
    elif in_win:
        msg = (
            f"Aktif pencere — Pazartesi {WEEKEND_RESUME_HOUR:02d}:00'a kadar "
            "yeni emir açılmaz (live açık olsa bile)."
        )
    else:
        msg = (
            f"Açık — Cuma 22:00'da otomatik durur, "
            f"Pazartesi {WEEKEND_RESUME_HOUR:02d}:00'da kendiliğinden devam eder."
        )
    return {
        "enabled": enabled,
        "active": active,
        "in_window": in_win,
        "window": window,
        "message": msg,
    }


def effective_live_on(now_tr: datetime | None = None) -> bool:
    """Manuel live + hafta sonu penceresi birleşik durum."""
    if is_group_paused(_GROUP):
        return False
    st = weekend_status(now_tr)
    return not st["active"]


def is_live_pm_label(label: str) -> bool:
    return is_dashboard_live_open(label)


def skip_algo_islemler_open_deferred(label: str, now_tr) -> bool:
    return False


def set_group_paused(group: str, paused: bool, *, source: str = "") -> dict:
    if group != _GROUP:
        return _load_control()
    data = _load_control()
    data["coptc_live_paused"] = bool(paused)
    data["coptc_live_on"] = not bool(paused)
    data["updated_at_tr"] = datetime.now(_TZ_TR).isoformat()
    data["updated_by"] = source or "coptc"
    _save_control(data)
    return data


def patch_control(**fields) -> dict:
    """Tek dosya: coptc_control.json — panel ve cron aynı kaynağı okur."""
    data = _load_control()
    data.update(fields)
    data["updated_at_tr"] = datetime.now(_TZ_TR).isoformat()
    if "updated_by" not in fields:
        data["updated_by"] = "coptc"
    _save_control(data)
    return data


def _clean_books(raw) -> list[str]:
    out: list[str] = []
    for b in raw or []:
        b = str(b or "").strip()
        if b and b not in out:
            out.append(b)
    return out[:MIRROR_BOOKS_MAX]


def mirror_books_selected(control: dict | None = None) -> list[str]:
    """Seçili kaynak defterler.

    Tek defter tutan eski kayıtlar (coptc_mirror_book) da listeye çevrilir,
    böylece liste anahtarı hiç yazılmamış kurulumlar kırılmaz.
    """
    data = control if control is not None else _load_control()
    raw = data.get(MIRROR_BOOKS_KEY)
    out = _clean_books(raw if isinstance(raw, list) else [])
    if out:
        return out
    one = str(data.get(MIRROR_BOOK_KEY) or "").strip()
    return [one] if one else [MIRROR_BOOK_DEFAULT]


def set_mirror_books(books, *, source: str = "") -> list[str]:
    """Seçimi yaz. Tekil anahtar da ilk defterle güncellenir — hâlâ onu okuyan
    bir yer kalırsa boşa düşmesin."""
    clean = _clean_books(books) or [MIRROR_BOOK_DEFAULT]
    patch_control(**{
        MIRROR_BOOKS_KEY: clean,
        MIRROR_BOOK_KEY: clean[0],
        "updated_by": source or "coptc",
    })
    return clean


def get_coptc_control() -> dict:
    return _load_control()


# geriye uyumluluk
get_pm_system_control = get_coptc_control
