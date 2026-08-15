"""Kaynak sunucunun (bursaapp / A2#05) açık pozisyonlarını okuyan mirror istemcisi.

Bu modül fikir üretmez. Hangi pozisyonun kopyalanacağına, hangi fiyat aralığında
girileceğine kaynak karar verir; burada yalnızca kararı okuyup uygularız. Eşikleri
değiştirmek gerekirse yer kaynak sunucunun .env'i, bu dosya değil.

Kaynağın gönderdiği karar alanları:
    positions[].copyable         kopyalanacak mı (tek doğruluk kaynağı)
    positions[].block_reason     kopyalanmıyorsa makine okunur kod
    positions[].block_detail     insan okunur gerekçe (log'a bu yazılır)
    positions[].entry_price_min  emir anındaki fiyat tabanı
    positions[].entry_price_max  emir anındaki fiyat tavanı
    positions[].min_stake_usd    borsa minimumunu şişirmeden girilebilecek en az tutar
    positions[].position_id      mükerrer kontrolü için sabit kimlik
    policy.max_spend_ratio       niyet edilen tutarın kaç katına kadar harcanabilir

Karar alanı gelmezse pozisyon atlanır: kaynak susuyorsa ayna kendi kararını
üretmez, işlem açmaz.

Ayarlar (.env):
    MIRROR_API_TOKEN  zorunlu — X-Mirror-Token başlığı
    MIRROR_API_URL    varsayılan https://bursaapp.com/poly/api/mirror
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, time
from zoneinfo import ZoneInfo

_DEFAULT_URL = "https://bursaapp.com/poly/api/mirror"
_TZ_TR = ZoneInfo("Europe/Istanbul")


def api_url() -> str:
    return (os.getenv("MIRROR_API_URL") or _DEFAULT_URL).rstrip("/")


def api_token() -> str:
    return (os.getenv("MIRROR_API_TOKEN") or "").strip()


def enabled() -> bool:
    return bool(api_token()) and (os.getenv("MIRROR_MODE") or "on").lower() in ("1", "true", "on", "yes")


def _get(path: str, *, timeout: int = 20) -> dict:
    token = api_token()
    if not token:
        raise RuntimeError("MIRROR_API_TOKEN tanımsız")
    req = urllib.request.Request(
        f"{api_url()}{path}",
        headers={"X-Mirror-Token": token, "Accept": "application/json",
                 "User-Agent": "CoptC Live Control-mirror"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:200]
        raise RuntimeError(f"mirror API {e.code}: {body}") from e


def book_list() -> list[dict]:
    return _get("").get("books") or []


def fetch_book(book: str, *, timeout: int = 20) -> dict:
    return _get(f"/{book}?filter=current_slot", timeout=timeout)


def active_slot(data: dict) -> dict:
    return data.get("active_slot") or {}


def slot_prediction_label(data: dict, hour_tr: int | None = None) -> str:
    slot = active_slot(data)
    if slot.get("prediction_tr"):
        return str(slot["prediction_tr"])
    if slot.get("slot_tr"):
        return str(slot["slot_tr"])
    if hour_tr is not None:
        return f"{hour_tr:02d}:00-{(hour_tr + 1) % 24:02d}:00"
    ah = slot.get("entry_hour_tr")
    if ah is not None:
        return f"{int(ah):02d}:00-{(int(ah) + 1) % 24:02d}:00"
    return "—"


def _parse_hm(value: str) -> tuple[int, int] | None:
    try:
        h, m = str(value).strip().split(":", 1)
        return int(h), int(m)
    except Exception:
        return None


def _slot_window_ok(slot: dict, now_tr: datetime) -> tuple[bool, str]:
    """API active_slot — status + slot_open_tr…slot_close_tr penceresi."""
    status = str(slot.get("status") or "").lower()
    if status and status != "active":
        return False, f"slot durumu '{status}' (active değil)"

    slot_date = slot.get("slot_date_tr")
    open_hm = _parse_hm(slot.get("slot_open_tr") or "")
    close_hm = _parse_hm(slot.get("slot_close_tr") or "")
    if not (slot_date and open_hm and close_hm):
        return True, ""

    try:
        day = datetime.strptime(str(slot_date), "%Y-%m-%d").date()
        start = datetime.combine(day, time(open_hm[0], open_hm[1]), tzinfo=_TZ_TR)
        end = datetime.combine(day, time(close_hm[0], close_hm[1]), tzinfo=_TZ_TR)
        if now_tr < start:
            return False, f"henüz açılmadı (pencere {slot.get('slot_open_tr')})"
        if now_tr > end:
            return False, f"slot kapandı (pencere {slot.get('slot_close_tr')})"
    except Exception:
        return True, ""
    return True, ""


def _slot_hour_ok(data: dict, expected_hour_tr: int | None) -> tuple[bool, str]:
    if expected_hour_tr is None:
        return True, ""

    slot = active_slot(data)
    if slot:
        ah = slot.get("entry_hour_tr")
        if ah is not None and int(ah) != int(expected_hour_tr):
            return False, (
                f"slot uyumsuz: kaynak {slot_prediction_label(data)}, "
                f"hedef {expected_hour_tr:02d}:00-{(expected_hour_tr + 1) % 24:02d}:00"
            )
        return True, ""

    # eski API yedeği
    slot_h = data.get("slot_hour_tr")
    if slot_h is not None and int(slot_h) != int(expected_hour_tr):
        return False, (
            f"slot uyumsuz: kaynak {int(slot_h):02d}:00-{(int(slot_h) + 1) % 24:02d}:00, "
            f"hedef {expected_hour_tr:02d}:00-{(expected_hour_tr + 1) % 24:02d}:00"
        )
    return True, ""


def policy(data: dict) -> dict:
    return data.get("policy") or {}


def order_guards(pos: dict, amount: float, data: dict | None = None) -> dict | None:
    """pm_place_order'a verilecek fiyat/harcama sınırları — hepsi kaynaktan.

    Kaynak sınırları göndermiyorsa None döner ve emir açılmaz; ayna eksik
    sınırın yerine varsayılan uydurmaz.
    """
    pol = policy(data or {})
    hi = pos.get("entry_price_max", pol.get("entry_price_max"))
    lo = pos.get("entry_price_min", pol.get("entry_price_min"))
    ratio = pol.get("max_spend_ratio")
    if hi is None or ratio is None:
        return None
    return {
        "min_price": float(lo or 0),
        "max_price": float(hi),
        "max_spend": round(float(amount) * float(ratio), 2),
    }


def _positions_from_data(
    data: dict,
    *,
    expected_hour_tr: int | None = None,
    now_tr: datetime | None = None,
) -> tuple[list[dict], list[str]]:
    """Kaynağın copyable=true dediği pozisyonlar + atlama gerekçeleri.

    Buradaki tek yerel kontrol, kaynağın konuştuğu slot ile bizim cron saatimizin
    aynı saat olması: işlemin iyi/kötü olduğuna dair değil, iki makinenin aynı
    saatten bahsettiğine dair bir bütünlük kontrolü.
    """
    if not data.get("ok"):
        raise RuntimeError(f"mirror API ok=false: {str(data)[:160]}")

    skipped: list[str] = []
    now_tr = now_tr or datetime.now(_TZ_TR)
    slot = active_slot(data)

    ok, note = _slot_hour_ok(data, expected_hour_tr)
    if not ok:
        skipped.append(note)
        return [], skipped

    if slot:
        ok, note = _slot_window_ok(slot, now_tr)
        if not ok:
            skipped.append(note)
            return [], skipped

    rows: list[dict] = []
    for p in data.get("positions") or []:
        sym = p.get("symbol_raw") or p.get("symbol") or "?"
        if "copyable" not in p:
            skipped.append(
                f"{sym}: kaynak karar alanı (copyable) göndermiyor — "
                "eski API sürümü, kopyalanmadı"
            )
            continue
        if not p.get("copyable"):
            skipped.append(
                f"{sym}: {p.get('block_detail') or p.get('block_reason') or 'kaynak kapattı'}"
            )
            continue
        rows.append(p)

    count = data.get("count")
    got = len(data.get("positions") or [])
    if count is not None and int(count) != got:
        skipped.append(f"uyarı: API count={count} ama {got} pozisyon geldi (kısmi veri?)")
    return rows, skipped


def open_positions(
    book: str,
    *,
    expected_hour_tr: int | None = None,
    now_tr: datetime | None = None,
) -> tuple[list[dict], list[str]]:
    """(kopyalanabilir pozisyonlar, atlama notları).

    expected_hour_tr: cron saati (13 → prediction 13:00-14:00).
    now_tr: slot_open_tr…slot_close_tr penceresi kontrolü için.
    """
    return _positions_from_data(
        fetch_book(book), expected_hour_tr=expected_hour_tr, now_tr=now_tr,
    )


def open_positions_with_meta(
    book: str,
    *,
    expected_hour_tr: int | None = None,
    now_tr: datetime | None = None,
) -> tuple[list[dict], list[str], dict]:
    """open_positions + ham API meta (active_slot, filter)."""
    data = fetch_book(book)
    rows, skipped = _positions_from_data(
        data,
        expected_hour_tr=expected_hour_tr,
        now_tr=now_tr,
    )
    return rows, skipped, data
