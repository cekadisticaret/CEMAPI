"""LIVE — seçilen sanal algoritmanın kopyası, gerçek Binance Futures.

$50 marj × 15x. Sanal deftere dokunmaz. Varsayılan kaynak: squeeze_momentum.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import binance_fapi as fapi
from atr_sistem import ATRP_NO_TRADE, ATR_SL_MULT, atr_last, atrp as _atrp, levels as _atr_levels, sl_clears_liq, trail_stop
import algo_paper as paper

_AI = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AI"))
if _AI not in sys.path:
    sys.path.insert(0, _AI)
from atr_step_trailing_stop import ATRStepTrailingStop

_TZ = ZoneInfo("Europe/Istanbul")
_DIR = os.path.dirname(os.path.abspath(__file__))
_STATE = os.path.join(_DIR, "algo_live_state.json")
_FOLLOW = os.path.join(_DIR, "algo_live_follow.json")
AID = "squeeze_momentum"
MARGIN = 50.0
LEV = 15
LEV_FALLBACK = 10
BOOST_MARGIN = 60.0
BOOST_LEV = 20
NOTIONAL = MARGIN * LEV
MAX_POS = 6
_lev_ok: dict[str, int] = {}
_iso_ok: set[str] = set()


def _liq_px(side: str, entry: float, lev: int | None = None) -> float:
    lv = int(lev or LEV)
    if lv <= 0:
        lv = LEV
    if side == "LONG":
        return entry * (1.0 - 1.0 / lv + paper.MMR)
    return entry * (1.0 + 1.0 / lv - paper.MMR)


def _ensure_lev(symbol: str, want: int | None = None, *, required: bool = True) -> int:
    """15x mümkünse 15, değilse 10 (daha düşük tavan varsa tavan).

    Kaldıraç Binance'te sembol bazında kalıcı. Bu turda zaten ayarladıysak
    tekrar POST atmıyoruz — açılış yolundan iki gereksiz tur geliş-gidiş düşüyor.
    """
    have = _lev_ok.get(symbol)
    if have and (want is None or int(want) == have):
        return have
    if symbol in _lev_ok and want is None:
        want = _lev_ok[symbol]
    if want is None:
        mx = 0
        try:
            mx = int(fapi.max_leverage(symbol) or 0)
        except Exception:
            mx = 0
        want = LEV
        if mx > 0 and mx < LEV:
            want = LEV_FALLBACK if mx >= LEV_FALLBACK else mx
    try:
        fapi.set_leverage(symbol, want)
        _lev_ok[symbol] = want
        return want
    except RuntimeError as e:
        msg = str(e).lower()
        bad = "leverage" in msg or "-4028" in str(e)
        if bad and want != LEV_FALLBACK:
            fapi.set_leverage(symbol, LEV_FALLBACK)
            _lev_ok[symbol] = LEV_FALLBACK
            return LEV_FALLBACK
        if required:
            raise
        return _lev_ok.get(symbol) or LEV_FALLBACK

_lock = threading.RLock()
# Paper'a yazılacak Binance dolum bilgileri — `_lock` altında toplanır, dışında uygulanır.
_mirror_q: dict[str, dict] = {}
_mirror_q_lock = threading.Lock()
_state: dict | None = None
_dual: bool | None = None
_wallet_cache: dict = {"t": 0.0, "row": {}}
_bn_opens_cache: dict = {"t": 0.0, "row": None}
_ov_snap: tuple[float, dict | None] = (0.0, None)
_live_ov_cache: dict = {"t": 0.0, "data": None}


def _live_ov_refresh() -> None:
    """Arkaplanda her 3 sn'de bir overview hesapla — SSE bloke olmasın."""
    import time as _time
    _time.sleep(1)
    while True:
        try:
            result = overview()
            _live_ov_cache["data"] = result
            _live_ov_cache["t"] = _time.time()
        except Exception:
            traceback.print_exc()
        _time.sleep(3)


def _live_ov_get() -> dict | None:
    """Son hesaplanan overview'i döndür; yoksa bekle."""
    import time as _time
    deadline = _time.time() + 20
    while _time.time() < deadline:
        if _live_ov_cache["data"] is not None:
            return _live_ov_cache["data"]
        _time.sleep(0.2)
    return None


_live_ov_thread: threading.Thread | None = None


def ensure_live_stream_started() -> None:
    global _live_ov_thread
    if _live_ov_thread and _live_ov_thread.is_alive():
        return
    _live_ov_thread = threading.Thread(target=_live_ov_refresh, name="live-ov-bg", daemon=True)
    _live_ov_thread.start()


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
        "skip_src": [],
        "pending_close": [],
        "pending_open": [],
        "follow_aid": AID,
        "follow_since": 0,
        "auto_follow": True,
        "auto_follow_mark": None,
    }


def _read_follow() -> dict:
    if not os.path.isfile(_FOLLOW):
        return {}
    try:
        with open(_FOLLOW, encoding="utf-8") as f:
            d = json.load(f) or {}
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _write_follow(aid: str, since: int = 0, title: str = "") -> None:
    row = {
        "follow_aid": str(aid or "").strip(),
        "follow_since": int(since or 0),
        "title": str(title or ""),
        # Panel otoseçim durumunu kilit almadan bu dosyadan okuyor.
        "auto_follow": bool(_state.get("auto_follow", True)) if _state else True,
    }
    tmp = _FOLLOW + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(row, f, ensure_ascii=False)
        os.replace(tmp, _FOLLOW)
    except OSError:
        pass


def _apply_follow(b: dict) -> dict:
    """Aktif kaynak ayrı dosyada — eski süreç state kaydı 43'e çeviremesin."""
    d = _read_follow()
    aid = str(d.get("follow_aid") or "").strip()
    if not aid:
        return b
    b["follow_aid"] = aid
    try:
        since = int(d.get("follow_since") or 0)
    except (TypeError, ValueError):
        since = 0
    if since:
        b["follow_since"] = since
    if d.get("title"):
        b["title"] = str(d.get("title") or b.get("title") or "")
    return b


def _load() -> dict:
    global _state
    if _state is not None:
        _apply_follow(_state)
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
    b["skip_src"] = list(raw.get("skip_src") or [])
    b["pending_close"] = list(raw.get("pending_close") or [])
    b["pending_open"] = list(raw.get("pending_open") or [])
    b["follow_aid"] = str(raw.get("follow_aid") or AID).strip() or AID
    b["auto_follow"] = bool(raw.get("auto_follow", True))
    try:
        mark = raw.get("auto_follow_mark")
        b["auto_follow_mark"] = None if mark is None else int(mark)
    except (TypeError, ValueError):
        b["auto_follow_mark"] = None
    try:
        b["follow_since"] = int(raw.get("follow_since") or 0)
    except (TypeError, ValueError):
        b["follow_since"] = 0
    _apply_follow(b)
    if not _read_follow().get("follow_aid"):
        _write_follow(b["follow_aid"], int(b.get("follow_since") or 0), str(b.get("title") or ""))
    _state = b
    return _state


def _save() -> None:
    if _state is None:
        return
    _apply_follow(_state)
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


def auto_follow_on() -> bool:
    """Otoseçim açık mı — kilitsiz okuma (panel her saniye soruyor)."""
    d = _read_follow()
    if "auto_follow" in d:
        return bool(d.get("auto_follow"))
    return True


def follow_aid() -> str:
    aid = str(_read_follow().get("follow_aid") or "").strip()
    if aid:
        return aid
    with _lock:
        aid = str(_load().get("follow_aid") or AID).strip()
    return aid or AID


def has_src(src_id: str) -> bool:
    """Kilitsiz okuma: paper bunu kendi kilidini tutarken çağırıyor; `_lock`
    beklersek iki kilit birbirini kilitler (deadlock). Bayat okumak zararsız."""
    sid = str(src_id or "")
    if not sid:
        return False
    for _ in range(3):
        try:
            poss = list(_load().get("positions") or [])
            return any(str(p.get("src_id") or "") == sid for p in poss)
        except RuntimeError:
            time.sleep(0.01)
    return False


def set_follow(aid: str) -> dict | None:
    """LIVE bundan sonra bu sanal defteri kopyalar. Açık LIVE pozisyon kapanmaz."""
    key = str(aid or "").strip()
    if not key:
        return None
    st = paper._load()
    books = st.get("algos") or {}
    src = books.get(key)
    if not src:
        src = next((row for row in books.values() if paper._match_aid(row, key)), None)
    if not src:
        return None
    nid = str(src.get("id") or "")
    title = f"{src.get('code') or nid} — sanal kopya"
    with _lock:
        b = _load()
        # Elle seçim açık bir tercihtir; otoseçim açık kalsaydı bunu 10 işlem
        # sonra geri alırdı. Panel butonu tekrar açana kadar seçim sabit.
        b["auto_follow"] = False
        b["auto_follow_mark"] = None
        if str(b.get("follow_aid") or "") != nid:
            b["follow_aid"] = nid
            b["follow_since"] = int(time.time() * 1000)
            b["title"] = title
            # Yeni defterin şu an açık pozisyonlarını kopyalamıyoruz —
            # sadece bundan sonra açtıkları. Toplu kopya girişi zarar ettiriyor.
            _skip_open_paper(b, list(src.get("positions") or []))
        _write_follow(nid, int(b.get("follow_since") or 0), str(b.get("title") or title))
        _save()
    return overview()


def _meta() -> dict | None:
    want = follow_aid()
    for m in paper._discover():
        if m["id"] == want:
            return m
    return None


# Yeni açılan pozisyonu "Binance'te yok" diye silmeden önce beklenecek süre.
# `_bn_opens` önbelleği 5 sn + dolumun yansıma gecikmesi için bolca pay.
_FLAT_GRACE_MS = 30_000

_warn_last: dict[str, float] = {}


def _warn_throttled(tag: str, err: object, every: float = 30.0) -> None:
    """Binance kesintisi sessiz kalmasın; log'u da boğmasın."""
    now = time.time()
    if now - _warn_last.get(tag, 0.0) < every:
        return
    _warn_last[tag] = now
    print(f"[algo_live] {tag} başarısız: {str(err)[:160]}", file=sys.stderr, flush=True)


def _bn_opens() -> dict[str, dict] | None:
    """None = okunamadı (pozisyonları silme). {} = gerçekten açık yok."""
    now = time.time()
    if _bn_opens_cache["row"] is not None and now - _bn_opens_cache["t"] < 5:
        return _bn_opens_cache["row"]
    try:
        rows = fapi.position_risk()
    except Exception as e:
        _warn_throttled("position_risk", e)
        return None
    if not isinstance(rows, list):
        _warn_throttled("position_risk", f"beklenmeyen yanıt: {type(rows).__name__}")
        return None
    out: dict[str, dict] = {}
    for r in rows or []:
        try:
            amt = float(r.get("positionAmt") or 0)
        except (TypeError, ValueError):
            continue
        if amt == 0:
            continue
        sym = str(r.get("symbol") or "")
        if not sym:
            continue
        out[sym] = r
    _bn_opens_cache["t"] = now
    _bn_opens_cache["row"] = out
    return out


def _adopt_from_risk(r: dict) -> dict:
    amt = float(r.get("positionAmt") or 0)
    side = "LONG" if amt > 0 else "SHORT"
    entry = float(r.get("entryPrice") or 0)
    qty = abs(amt)
    mark = float(r.get("markPrice") or entry)
    lev = int(float(r.get("leverage") or LEV) or LEV)
    iso = float(r.get("isolatedMargin") or 0)
    return {
        "id": "bn-" + uuid.uuid4().hex[:10],
        "symbol": str(r.get("symbol") or ""),
        "base": str(r.get("symbol") or "").replace("USDT", ""),
        "side": side,
        "entry": entry,
        "mark": mark,
        "qty": qty,
        "qty_orig": qty,
        "margin": iso if iso > 0 else MARGIN,
        "lev": lev,
        "atr": 0.0,
        "atrp": 0.0,
        "r_dist": 0.0,
        "sl": 0.0,
        "tp1": 0.0,
        "tp": 0.0,
        "tp2": 0.0,
        "liq": _liq_px(side, entry) if entry else 0.0,
        "peak": mark,
        "trough": mark,
        "trail_on": False,
        "tp1_done": False,
        "fee_open": paper._fee_on(qty, entry),
        "funding_acc": 0.0,
        "opened": _ts(),
        "opened_iso": _iso(),
        "opened_ms": int(time.time() * 1000),
        "fill": "binance",
        "live": True,
        "order_id": "",
        "src_id": "",
        "unreal_bn": float(r.get("unRealizedProfit") or 0),
    }


def _sync_binance(b: dict, bn: dict | None = None) -> None:
    """Ekran = Binance gerçeği. State'te olmayan açıklar alınır, Binance'te kapananlar düşer."""
    if bn is None:
        bn = _bn_opens()
    if bn is None:
        return
    # Anlık görüntü, pozisyon açılmadan önce alınmış olabilir (önbellek 5 sn) ya da
    # Binance dolumu henüz yansıtmamış olabilir. O pozisyonu "kapanmış" sayıp silersek
    # bir sonraki tur onu yeniden açar -> Binance'te çift pozisyon. Bu yüzden taze
    # pozisyonlara dokunmuyoruz.
    snap_ms = int(_bn_opens_cache.get("t", 0.0) * 1000)
    now_ms = int(time.time() * 1000)
    kept = []
    have = set()
    for p in b.get("positions") or []:
        sym = str(p.get("symbol") or "")
        if sym not in bn:
            opened_ms = int(p.get("opened_ms") or 0)
            too_new = opened_ms and (
                opened_ms >= snap_ms - _FLAT_GRACE_MS
                or now_ms - opened_ms < _FLAT_GRACE_MS
            )
            if too_new:
                kept.append(p)
                have.add(sym)
                continue
            # Genç bir pozisyonu kapanmış saymak, çift açılmanın başlangıcıydı:
            # defterden silinir, sonraki tur yeniden açar. Koruma tuttuğu için
            # buraya artık düşmemeli; düşerse sessiz kalmasın.
            age_s = (now_ms - opened_ms) / 1000.0 if opened_ms else -1
            if age_s < 0 or age_s < 300:
                print(
                    f"[algo_live] DİKKAT {sym}: Binance anlık görüntüsünde yok,"
                    f" pozisyon yaşı {age_s:.0f} sn (opened_ms={opened_ms or 'YOK'}),"
                    f" görüntü yaşı {(now_ms - snap_ms) / 1000.0:.1f} sn"
                    " — kapanmış sayılıyor, çift açılma riski",
                    file=sys.stderr, flush=True,
                )
            exit_px = float(p.get("mark") or p.get("entry") or 0)
            qty = float(p.get("qty") or 0)
            entry = float(p.get("entry") or 0)
            side = str(p.get("side") or "")
            fee_open = float(p.get("fee_open") or 0)
            fee_close = paper._fee_on(qty, exit_px) if qty and exit_px else 0.0
            gross = paper._pnl(side, entry, exit_px, qty) if qty and entry and exit_px else 0.0
            if p.get("unreal_bn") not in (None, ""):
                try:
                    gross = float(p.get("unreal_bn"))
                except (TypeError, ValueError):
                    pass
            rec = {
                "id": p.get("id"),
                "t": _ts(),
                "iso": _iso(),
                "symbol": sym,
                "base": p.get("base"),
                "side": side,
                "entry": entry,
                "exit": exit_px,
                "reason": (
                    f"STOP{int(p.get('trail_step') or 0)}"
                    if p.get("trail_order_id") or p.get("trail_step")
                    else "binance_flat"
                ),
                "gross": round(gross, 2),
                "commission": round(fee_open + fee_close, 2),
                "funding": 0.0,
                "net": round(gross - fee_open - fee_close, 2),
                "opened": p.get("opened") or "",
                "closed": _ts(),
                "mins": paper._hold_mins(p),
                "live": True,
            }
            hist = b.setdefault("history", [])
            hist.append(rec)
            if len(hist) > 400:
                del hist[:-400]
            continue
        r = bn[sym]
        amt = abs(float(r.get("positionAmt") or 0))
        if amt > 0:
            _apply_bn_row(p, r)
            _queue_mirror_fill(p)
        kept.append(p)
        have.add(sym)
    follow = str(b.get("follow_aid") or AID)
    src_book = (paper._load().get("algos") or {}).get(follow) or {}
    by_sym = {str(p.get("symbol") or ""): p for p in src_book.get("positions") or []}
    blocked = _pending_syms(b)
    for sym, r in bn.items():
        if sym in have or sym in blocked:
            continue
        row = _adopt_from_risk(r)
        src = by_sym.get(sym)
        if src:
            row["src_id"] = str(src.get("id") or "")
            row["src_aid"] = follow
            _copy_paper_atr(row, src)
        kept.append(row)
    b["positions"] = kept


def _apply_bn_row(p: dict, r: dict) -> None:
    """LIVE satırı = Binance: giriş, mark, adet, PnL. Kâğıt fiyatı ezilmez."""
    amt = abs(float(r.get("positionAmt") or 0))
    if amt <= 0:
        return
    p["qty"] = amt
    mark = float(r.get("markPrice") or p.get("mark") or 0)
    if mark > 0:
        p["mark"] = mark
    ep = float(r.get("entryPrice") or 0)
    if ep > 0:
        p["entry"] = ep
    p["unreal_bn"] = float(r.get("unRealizedProfit") or 0)
    try:
        lev = int(float(r.get("leverage") or 0) or 0)
    except (TypeError, ValueError):
        lev = 0
    if lev:
        p["lev"] = lev
    iso = float(r.get("isolatedMargin") or 0)
    if iso > 0:
        p["margin"] = iso
    p["fill"] = "binance"


def _queue_mirror_fill(lp: dict) -> None:
    """`_sync_binance` `_lock` altında çalışıyor; paper kilidini burada isteyemeyiz.
    İşi kuyruğa al, `_flush_mirror_fills()` kilit bırakıldıktan sonra uygular."""
    sid = str(lp.get("src_id") or "")
    entry = float(lp.get("entry") or 0)
    if not sid or entry <= 0:
        return
    with _mirror_q_lock:
        _mirror_q[sid] = {
            "src_id": sid,
            "src_aid": str(lp.get("src_aid") or ""),
            "entry": entry,
            "mark": float(lp.get("mark") or 0),
        }


def _flush_mirror_fills() -> None:
    """Sadece `_lock` bırakıldıktan sonra çağır."""
    with _mirror_q_lock:
        jobs = list(_mirror_q.values())
        _mirror_q.clear()
    for job in jobs:
        try:
            _mirror_fill_to_paper(job)
        except Exception:
            traceback.print_exc()


def _mirror_fill_to_paper(lp: dict) -> None:
    """Kaynak sanal pozisyon Binance giriş/mark'ına uysun — aynı fiyat, aynı yön."""
    sid = str(lp.get("src_id") or "")
    if not sid:
        return
    entry = float(lp.get("entry") or 0)
    mark = float(lp.get("mark") or 0)
    if entry <= 0:
        return
    try:
        with paper._lock:
            st = paper._load()
            books = st.get("algos") or {}
            aid = str(lp.get("src_aid") or "")
            src = books.get(aid) if aid else None
            if not src:
                src = next(
                    (
                        row for row in books.values()
                        if any(str(p.get("id") or "") == sid for p in row.get("positions") or [])
                    ),
                    None,
                )
            if not src:
                return
            for p in src.get("positions") or []:
                if str(p.get("id") or "") != sid:
                    continue
                p["entry"] = entry
                if mark > 0:
                    p["mark"] = mark
                p["fill"] = "binance"
                break
            paper._save()
    except Exception:
        pass


def _mark_one(p: dict, marks: dict) -> dict:
    info = marks.get(p["symbol"]) or {}
    # Fiyat önce canlı akıştan (bookTicker) alınır: `position_risk` çağrısı
    # takılırsa `p["mark"]` donup kalıyor, ekrandaki "Anlık" değeri de donuyordu.
    # `marks` ayrı bir uçtan beslendiği için bağımsız olarak tazelenmeye devam eder.
    live_px = float(info.get("mark") or info.get("price") or 0)
    mark = live_px or float(p.get("mark") or 0) or float(p.get("entry") or 0)
    qty = float(p.get("qty") or 0)
    margin = float(p.get("margin") or MARGIN)
    exit_est = mark or paper._fill_px(p["side"], "close", info)
    entry = float(p.get("entry") or 0)
    gross = paper._pnl(p["side"], entry, mark, qty)
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
        "trail_log": list(p.get("trail_log") or []),
        "trail_step": int(p.get("trail_step") or 0),
        "trail_stop_px": float(p.get("trail_stop_px") or 0),
        "trail_err": str(p.get("trail_err") or ""),
        "tp1_done": bool(p.get("tp1_done")),
        "r_dist": round(float(p.get("r_dist") or 0), 8),
        "live": True,
    })
    return out


def _copy_paper_atr(lp: dict, src: dict) -> None:
    if not src:
        return
    lp["atr"] = float(src.get("atr") or 0)
    lp["atrp"] = float(src.get("atrp") or 0)
    lp["sl"] = float(src.get("sl") or 0)
    lp["tp1"] = float(src.get("tp1") or 0)
    lp["tp"] = float(src.get("tp") or src.get("tp2") or 0)
    lp["tp2"] = float(src.get("tp2") or src.get("tp") or 0)
    lp["r_dist"] = float(src.get("r_dist") or 0)
    lp["trail_on"] = bool(src.get("trail_on"))
    if src.get("tp1_done"):
        lp["tp1_done"] = True


def _trail_place(symbol, close_side, stop_price, cid, working_type, position_side):
    return fapi.stop_market_close(
        symbol,
        close_side,
        stop_price,
        client_order_id=cid,
        working_type=working_type,
        position_side=position_side,
    )


def _trail_cancel(symbol, order_id) -> None:
    fapi.cancel_order(symbol, order_id)


def _cancel_step_trail(p: dict) -> None:
    oid = p.get("trail_order_id")
    if not oid:
        p["trail_order_id"] = None
        p["trail_cid"] = None
        return
    try:
        _trail_cancel(str(p.get("symbol") or ""), oid)
    except Exception:
        pass
    p["trail_order_id"] = None
    p["trail_cid"] = None


def _step_trailer(lp: dict) -> ATRStepTrailingStop:
    filt = paper._filters().get(lp["symbol"]) or {}
    tick = float(filt.get("tick") or 0)
    t = ATRStepTrailingStop(
        symbol=str(lp["symbol"]),
        side=str(lp["side"]),
        entry_price=float(lp["entry"]),
        quantity=float(lp.get("qty") or 0),
        activation_atr_mult=0.5,
        trail_atr_mult=1.0,
        min_step_atr_mult=0.25,
        place_fn=_trail_place,
        cancel_fn=_trail_cancel,
        round_fn=(lambda px, tk=tick: paper._round_tick(px, tk)) if tick else None,
        position_side=_pos_side(str(lp["side"])),
    )
    t.active = bool(lp.get("trail_on"))
    t.step = int(lp.get("trail_step") or 0)
    entry = float(lp.get("entry") or 0)
    if lp["side"] == "LONG":
        t.high_water = float(lp.get("peak") or entry)
    else:
        t.high_water = float(lp.get("trough") or entry)
    if lp.get("trail_stop_px"):
        t.current_stop_price = float(lp["trail_stop_px"])
    if lp.get("trail_order_id"):
        try:
            t.current_order_id = int(lp["trail_order_id"])
        except (TypeError, ValueError):
            t.current_order_id = None
    t.current_client_order_id = lp.get("trail_cid") or None
    return t


def _maybe_stop_close(b: dict, lp: dict, marks: dict) -> bool:
    """Son fiyat / bid-ask stopu deldiyse Binance'te kapat. Paper kapanmasını bekleme."""
    info = marks.get(str(lp.get("symbol") or "")) or {}
    last = float(info.get("price") or info.get("mark") or 0)
    if last > 0:
        lp["mark"] = last
    mk = float(lp.get("mark") or info.get("mark") or last)
    px = paper._px_for_stop(lp, info, mk)
    why = paper._hit_exit(lp, px)
    if not why:
        return False
    _flush_symbol(b, str(lp.get("symbol") or ""), why, str(lp.get("src_id") or ""))
    return True


def _sync_step_trail(lp: dict) -> None:
    """Zarar SL durur. 0.5×ATR kârda girise kilit, sonra 1×ATR trail → Binance STOP."""
    mark = float(lp.get("mark") or 0)
    atr = float(lp.get("atr") or 0)
    entry = float(lp.get("entry") or 0)
    if mark <= 0 or atr <= 0 or entry <= 0:
        return
    if lp["side"] == "LONG":
        lp["peak"] = max(float(lp.get("peak") or entry), mark)
        profit = float(lp["peak"]) - entry
    else:
        lp["trough"] = min(float(lp.get("trough") or entry), mark)
        profit = entry - float(lp["trough"])
    if profit >= atr * 0.5:
        lp["trail_on"] = True
        from atr_sistem import lock_stop
        ext = float(lp["peak"] if lp["side"] == "LONG" else lp["trough"])
        locked = lock_stop(str(lp["side"]), entry, ext, atr)
        # Peak kârın %85'ini koru
        qty = float(lp.get("qty") or 0)
        if qty > 0 and profit * qty >= 5.0:
            if lp["side"] == "LONG":
                pct_sl = entry + (ext - entry) * 0.85
                locked = max(locked, pct_sl)
            else:
                pct_sl = entry - (entry - ext) * 0.85
                locked = min(locked, pct_sl)
        if lp["side"] == "LONG":
            lp["sl"] = max(float(lp.get("sl") or 0), locked)
        else:
            sl0 = float(lp.get("sl") or 0)
            lp["sl"] = min(sl0, locked) if sl0 else locked
    if not lp.get("trail_on"):
        return
    t = _step_trailer(lp)
    try:
        t.on_price_update(mark, atr)
        lp["trail_err"] = ""
    except Exception as e:
        lp["trail_err"] = str(e)[:120]
        return
    lp["trail_step"] = t.step
    lp["trail_stop_px"] = t.current_stop_price
    lp["trail_order_id"] = t.current_order_id
    lp["trail_cid"] = t.current_client_order_id
    if lp["side"] == "LONG":
        lp["peak"] = t.high_water
    else:
        lp["trough"] = t.high_water
    paper._note_lock(lp)


def overview_fast() -> dict:
    """Ekran için: cache, yoksa yerel defter. Binance beklemez."""
    if _live_ov_cache.get("data"):
        return _live_ov_cache["data"]
    if _ov_snap[1] is not None:
        return _ov_snap[1]
    try:
        return _overview_from_local()
    except Exception:
        traceback.print_exc()
        return {"ok": True, "id": AID, "code": "LIVE", "title": "LIVE",
                "positions": [], "history": [], "wallet": 0, "available": 0,
                "unreal": 0, "connected": False, "active": True, "trades": 0,
                "wins": 0, "win_pct": 0, "realized": 0, "fees": 0, "error": ""}


def _overview_from_local() -> dict:
    """Ekran defteri okur. `_lock` emir gönderirken saniyelerce meşgul olabilir;
    bekleyip donmak yerine 0.5s dene, olmazsa kilitsiz oku (bayat veri > boş ekran)."""
    marks = paper._px_cache[1] or {}
    w = _wallet_cache.get("row") or {}
    got = _lock.acquire(timeout=0.5)
    try:
        b = dict(_load())
    finally:
        if got:
            _lock.release()
    return _overview_row(b, marks, w)


def _overview_row(b: dict, marks: dict, w: dict) -> dict:
    follow = str(b.get("follow_aid") or AID)
    src_book = (paper._load().get("algos") or {}).get(follow) or {}
    poss = [_mark_one(p, marks) for p in b.get("positions") or []]
    hist = list(b.get("history") or [])[-80:][::-1]
    wins = sum(1 for h in hist if float(h.get("net") or 0) > 0)
    realized = sum(float(h.get("net") or 0) for h in hist)
    equity = float(w.get("wallet") or 0) + float(w.get("unreal") or 0)
    return {
        "ok": True,
        "id": AID,
        "code": "LIVE",
        "title": b.get("title") or src_book.get("title") or "LIVE",
        "follow_aid": follow,
        "follow_code": src_book.get("code") or follow,
        "follow_title": src_book.get("title") or "",
        "auto_follow": bool(b.get("auto_follow", True)),
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
        "boost_margin": BOOST_MARGIN,
        "boost_lev": BOOST_LEV,
        "boost_wr": paper._BOOST_WR,
    }


def overview() -> dict:
    global _ov_snap
    now = time.time()
    if _ov_snap[1] is not None and now - _ov_snap[0] < 2.0:
        return _ov_snap[1]
    bn = _bn_opens()
    marks = paper._marks()
    w = wallet()
    with _lock:
        b = _load()
        try:
            _sync_binance(b, bn)
            follow = str(b.get("follow_aid") or AID)
            src_book = (paper._load().get("algos") or {}).get(follow) or {}
            by_id = {str(p.get("id")): p for p in src_book.get("positions") or []}
            by_sym = {str(p.get("symbol")): p for p in src_book.get("positions") or []}
            for lp in b.get("positions") or []:
                if not _belongs_to_follow(lp, follow):
                    continue
                src = by_id.get(str(lp.get("src_id") or "")) or by_sym.get(str(lp.get("symbol") or ""))
                if src:
                    lp["src_id"] = src.get("id")
                    lp["src_aid"] = follow
                    _copy_paper_atr(lp, src)
                    _maybe_stop_close(b, lp, marks)
            _save()
        except Exception:
            traceback.print_exc()
        row = _overview_row(b, marks, w)
    _flush_mirror_fills()
    _ov_snap = (now, row)
    _live_ov_cache["data"] = row
    _live_ov_cache["t"] = now
    return row


def toggle() -> dict:
    with _lock:
        b = _load()
        b["active"] = not b.get("active")
        _save()
    return overview()


def _ensure_isolated(symbol: str) -> None:
    """Marj tipi de sembol bazında kalıcı — her emirde tekrar göndermeye gerek yok."""
    if symbol in _iso_ok:
        return
    fapi.set_isolated(symbol)
    _iso_ok.add(symbol)


def _place(symbol: str, side: str, qty: float, step: float, close: bool = False, lev: int | None = None) -> dict:
    _ensure_isolated(symbol)
    _ensure_lev(symbol, lev, required=not close)
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
    if not partial:
        _cancel_step_trail(p)
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


def _open_pos(b: dict, symbol: str, side: str, marks: dict, df=None, src_id: str = "", src: dict | None = None) -> dict | None:
    if paper._blocked(symbol):
        return None
    if not b.get("active"):
        return None
    if not fapi.enabled():
        return None
    if len(b.get("positions") or []) >= MAX_POS:
        return None
    if any(p["symbol"] == symbol for p in b.get("positions") or []):
        return None
    if src_id and src_id in (b.get("skip_src") or []):
        return None
    info = marks.get(symbol) or {}
    filt = paper._filters().get(symbol) or {}
    tick = float(filt.get("tick") or 0)
    step = float(filt.get("step") or 0.001)
    px = paper._round_tick(paper._fill_px(side, "open", info), tick)
    if px <= 0:
        return None
    boost = paper.live_boost(symbol)
    margin = BOOST_MARGIN if boost else MARGIN
    want_lev = BOOST_LEV if boost else LEV
    try:
        mx = int(fapi.max_leverage(symbol) or 0)
    except Exception:
        mx = 0
    if mx > 0:
        want_lev = min(want_lev, mx)
    try:
        lev = _ensure_lev(symbol, want_lev)
    except Exception as e:
        b["error"] = str(e)[:160]
        return None
    notional = margin * lev
    r_dist = 0.0
    if src:
        atr = float(src.get("atr") or 0)
        ap = float(src.get("atrp") or 0)
        sl = float(src.get("sl") or 0)
        tp1 = float(src.get("tp1") or 0)
        tp2 = float(src.get("tp") or src.get("tp2") or 0)
        r_dist = float(src.get("r_dist") or 0)
        liq = paper._round_tick(_liq_px(side, px, lev), tick)
    else:
        if df is None:
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
        r_dist = float(lv["r_dist"])
        liq = paper._round_tick(_liq_px(side, px, lev), tick)
        if not sl_clears_liq(side, px, sl, liq):
            return None
    qty = paper._round_step(notional / px, step)
    if qty <= 0 or qty * px < float(filt.get("min_notional") or 5):
        return None
    # force=True her açılışta ekstra bir imzalı çağrı demekti; 4 sn'lik önbellek
    # bu güvenlik kontrolü için yeterli. Marj gerçekten yetmezse Binance reddediyor.
    w = wallet()
    if not w.get("ok") or float(w.get("available") or 0) < margin * 1.05:
        b["error"] = "USDT yetersiz"
        return None
    t_order = time.time()
    try:
        order = _place(symbol, side, qty, step, close=False, lev=lev)
    except Exception as e:
        b["error"] = str(e)[:160]
        return None
    if src_id:
        src_ms = int((src or {}).get("opened_ms") or 0)
        lag = (time.time() * 1000 - src_ms) / 1000.0 if src_ms else -1
        print(
            f"[algo_live] {symbol} açıldı — emir {(time.time() - t_order) * 1000:.0f} ms,"
            f" sanaldan bu yana {lag:.2f} sn",
            file=sys.stderr, flush=True,
        )
    # Önbellekteki anlık görüntü bu emri bilmiyor; bir sonraki senkron taze çekmeli.
    _bn_opens_cache["t"] = 0.0
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
        "margin": margin,
        "lev": lev,
        "atr": atr,
        "atrp": round(ap, 2),
        "r_dist": r_dist,
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
        "src_id": src_id or str((src or {}).get("id") or ""),
        "src_aid": str(b.get("follow_aid") or follow_aid()) if (src_id or src) else "",
    }
    b["fees"] = round(float(b.get("fees") or 0) + fee, 2)
    b.setdefault("positions", []).append(pos)
    b["error"] = ""
    return pos


def follow_open(paper_pos: dict, marks: dict, df=None) -> dict | None:
    """Sanal yeni işlem açınca LIVE'da da aç. Defter kopyalamaz."""
    if not paper_pos:
        return None
    with _lock:
        b = _load()
        pid = str(paper_pos.get("id") or "")
        pos = _open_pos(
            b,
            str(paper_pos.get("symbol") or ""),
            str(paper_pos.get("side") or ""),
            marks,
            df,
            src_id=pid,
            src=paper_pos,
        )
        pending = b.setdefault("pending_open", [])
        if pos is None and pid and b.get("active"):
            if pid not in pending:
                pending.append(pid)
            if len(pending) > 20:
                del pending[:-20]
        elif pos is not None and pid in pending:
            pending.remove(pid)
        _save()
        return pos


def queue_close(symbol: str, reason: str = "paper_close", src_id: str = "", partial: bool = False) -> None:
    """Sanal kapanışı hemen kuyruğa yaz — emir başarısız olsa da taramada tekrarlanır."""
    with _lock:
        b = _load()
        _queue_close(b, symbol, reason, src_id, partial)
        _save()


def follow_close(symbol: str, reason: str, partial: bool = False, src_id: str = "") -> None:
    """Kaynak sanal defter kapatınca LIVE'ı da kapat. State'te yoksa Binance'ten düzler."""
    with _lock:
        b = _load()
        _queue_close(b, symbol, reason, src_id, partial)
        _flush_symbol(b, str(symbol or ""), reason, src_id, partial)
        _save()


def _queue_close(b: dict, symbol: str, reason: str, src_id: str = "", partial: bool = False) -> None:
    sym = str(symbol or "").strip()
    if not sym:
        return
    pend = b.setdefault("pending_close", [])
    for row in pend:
        if str(row.get("symbol") or "") == sym and bool(row.get("partial")) == bool(partial):
            if src_id and not row.get("src_id"):
                row["src_id"] = src_id
            if reason:
                row["reason"] = reason
            return
    pend.append({
        "symbol": sym,
        "reason": reason or "paper_close",
        "src_id": str(src_id or ""),
        "partial": bool(partial),
        "t": _iso(),
    })
    if len(pend) > 40:
        del pend[:-40]


def _pending_syms(b: dict) -> set[str]:
    return {str(x.get("symbol") or "") for x in (b.get("pending_close") or []) if x.get("symbol")}


def _drop_pending(b: dict, symbol: str, partial: bool | None = None) -> None:
    pend = b.get("pending_close") or []
    if partial is None:
        b["pending_close"] = [x for x in pend if str(x.get("symbol") or "") != symbol]
        return
    b["pending_close"] = [
        x for x in pend
        if not (str(x.get("symbol") or "") == symbol and bool(x.get("partial")) == bool(partial))
    ]


def _bn_amt(symbol: str) -> float | None:
    try:
        rows = fapi.position_risk(symbol)
    except Exception:
        return None
    if not isinstance(rows, list):
        return None
    tot = 0.0
    for r in rows or []:
        if str(r.get("symbol") or "") != symbol:
            continue
        try:
            tot += float(r.get("positionAmt") or 0)
        except (TypeError, ValueError):
            continue
    return tot


def _flatten_exchange(symbol: str, side: str | None = None) -> dict | None:
    """State'te yoksa bile Binance açıkını market ile kapat."""
    amt = _bn_amt(symbol)
    if amt is None:
        raise RuntimeError(f"{symbol} Binance okunamadı")
    if amt == 0:
        return None
    sd = side or ("LONG" if amt > 0 else "SHORT")
    qty = abs(amt)
    filt = paper._filters().get(symbol) or {}
    step = float(filt.get("step") or 0.001)
    return _place(symbol, sd, qty, step, close=True)


def _flush_symbol(b: dict, symbol: str, reason: str, src_id: str = "", partial: bool = False) -> None:
    if not symbol:
        return
    hit = next((p for p in b.get("positions") or [] if p.get("symbol") == symbol), None)
    if not hit and src_id:
        hit = next((p for p in b.get("positions") or [] if str(p.get("src_id") or "") == src_id), None)
    try:
        if hit:
            if partial:
                if hit.get("tp1_done"):
                    _drop_pending(b, symbol, True)
                    return
                _close_qty(b, hit, float(hit.get("qty") or 0) * 0.5, reason, partial=True)
            else:
                _close_qty(b, hit, float(hit.get("qty") or 0), reason, partial=False)
        elif not partial:
            _flatten_exchange(symbol)
    except Exception as e:
        msg = str(e)
        flat = any(k in msg.lower() for k in ("reduceonly", "position", "-2022", "-2019", "insufficient"))
        if not flat:
            b["error"] = msg[:160]
            return
    left = _bn_amt(symbol)
    if left is None:
        return
    if abs(left) < 1e-12:
        _drop_pending(b, symbol, None if not partial else True)
        if not partial:
            b["positions"] = [p for p in (b.get("positions") or []) if p.get("symbol") != symbol]


def _flush_pending(b: dict) -> None:
    for row in list(b.get("pending_close") or []):
        _flush_symbol(
            b,
            str(row.get("symbol") or ""),
            str(row.get("reason") or "paper_close"),
            str(row.get("src_id") or ""),
            bool(row.get("partial")),
        )


def _paper_source() -> dict:
    st = paper._load()
    return (st.get("algos") or {}).get(follow_aid()) or {}


# --- Otomatik takip: sıralamanın tepesindeki sanal defteri izle ---
# Takip edilen defter bu kadar işlem daha kapatınca sıralamaya yeniden bak.
AUTO_FOLLOW_EVERY_TRADES = 10
# Aday defter en az bu kadar kapanmış işlem göstermeli — tek şanslı işlemle
# tepeye çıkan yeni defter canlı parayı almasın.
AUTO_FOLLOW_MIN_TRADES = 10


def _auto_follow_step() -> None:
    """Gerekiyorsa takip edilen defteri sıralama liderine geçirir.

    `on_scan` içinde `_lock` alınmadan çağrılır. Ölçüt sayfanın sıralamasıyla
    aynı: `paper.overview()` defterleri özkaynağa göre sıralı döndürüyor, yani
    "en başta olan" ile "otomatik seçilen" hep aynı defter oluyor.
    """
    try:
        with _lock:
            b = _load()
            if not b.get("auto_follow", True):
                return
            mark = b.get("auto_follow_mark")
        follow = follow_aid()
        books = paper._load().get("algos") or {}
        cur = books.get(follow)
        trades = len((cur or {}).get("history") or [])
        if cur is None or mark is None:
            # İlk açılış ya da takip edilen defter kaybolmuş: beklemeden lidere geç.
            mark = -AUTO_FOLLOW_EVERY_TRADES
        elif int(mark) > trades:
            with _lock:
                _load()["auto_follow_mark"] = trades
                _save()
            return
        if trades - int(mark) < AUTO_FOLLOW_EVERY_TRADES:
            return

        cards = [
            c for c in (paper.overview().get("algos") or [])
            if int(c.get("trades") or 0) >= AUTO_FOLLOW_MIN_TRADES
        ]
        best = cards[0] if cards else None
        nid = str((best or {}).get("id") or "")
        with _lock:
            b = _load()
            b["auto_follow_mark"] = trades
            if not nid or nid == follow:
                _save()
                return
            src = books.get(nid) or {}
            code = str(best.get("code") or nid)
            b["follow_aid"] = nid
            b["follow_since"] = int(time.time() * 1000)
            b["title"] = f"{code} — sanal kopya"
            b["auto_follow_mark"] = len(src.get("history") or [])
            # Yeni defterin şu an açık pozisyonlarını kopyalamıyoruz.
            _skip_open_paper(b, list(src.get("positions") or []))
            _write_follow(nid, int(b["follow_since"]), str(b["title"]))
            _save()
        print(
            f"[algo_live] otomatik takip değişti: {follow} -> {code}"
            f" (özkaynak lideri, {best.get('trades')} işlem,"
            f" net {best.get('net_pnl')} $)",
            file=sys.stderr, flush=True,
        )
    except Exception:
        traceback.print_exc()


def set_auto_follow(on: bool) -> dict:
    """Otoseçimi aç/kapat. Kapalıyken takip o an seçili defterde kalır."""
    with _lock:
        b = _load()
        b["auto_follow"] = bool(on)
        # Açıkken hemen değerlendirsin; kapalıyken sayaç anlamsız.
        b["auto_follow_mark"] = None
        _write_follow(
            str(b.get("follow_aid") or ""),
            int(b.get("follow_since") or 0),
            str(b.get("title") or ""),
        )
        _save()
    return {"ok": True, "auto_follow": bool(on), "follow_aid": follow_aid()}


def _orphan_index(b: dict, follow: str) -> dict:
    """Takip edilenden farklı deftere ait live pozisyonların kaynaklarını bul.

    Sadece gerçekten sahipsiz pozisyon varsa tüm defterleri tarar; normal
    durumda (herkes takip edilen defterden) boş sözlük döner.
    """
    aids = {
        str(p.get("src_aid") or "")
        for p in b.get("positions") or []
        if str(p.get("src_aid") or "") and str(p.get("src_aid") or "") != follow
    }
    if not aids:
        return {}
    out: dict = {}
    books = (paper._load().get("algos") or {})
    for aid in aids:
        for p in (books.get(aid) or {}).get("positions") or []:
            if p.get("id"):
                out[str(p["id"])] = p
    return out


def _belongs_to_follow(lp: dict, follow: str) -> bool:
    src_aid = str(lp.get("src_aid") or "")
    if not src_aid:
        return True
    return src_aid == follow


def _skip_open_paper(b: dict, paper_pos: list) -> None:
    """Şu an açık sanalları kopyalama — sadece bundan sonra açılanlar."""
    skip = b.setdefault("skip_src", [])
    for p in paper_pos:
        pid = str(p.get("id") or "")
        if pid and pid not in skip:
            skip.append(pid)
    if len(skip) > 80:
        del skip[:-80]


def on_scan(frames: dict, marks: dict) -> None:
    """Sinyal üretmez. Yeni sanal işlem = follow_open. Açık defteri kopyalamaz."""
    if not fapi.configured():
        with _lock:
            b = _load()
            b["error"] = "Binance anahtarı yok"
            b["last_scan"] = _iso()
            _save()
        return
    # Karar kilit ALINMADAN önce: sanal defteri okumak `paper._lock` istiyor,
    # `_lock` tutarken beklemek iki kilidi karşılıklı bloklar.
    _auto_follow_step()
    follow = follow_aid()
    src_book = _paper_source()
    paper_pos = list(src_book.get("positions") or [])
    by_id = {str(p.get("id")): p for p in paper_pos}
    by_sym = {str(p.get("symbol")): p for p in paper_pos}
    with _lock:
        b = _load()
        b["title"] = f"{src_book.get('code') or follow} — sanal kopya"
        b["last_signal"] = str(src_book.get("last_signal") or "")
        b["last_scan"] = _iso()
        try:
            _sync_binance(b)
        except Exception as e:
            b["error"] = str(e)[:160]
        _flush_pending(b)
        want_close = _pending_syms(b)
        orphan_by_id = _orphan_index(b, follow)
        for lp in list(b.get("positions") or []):
            if _belongs_to_follow(lp, follow):
                src = by_id.get(str(lp.get("src_id") or ""))
                if not src:
                    src = by_sym.get(str(lp.get("symbol") or ""))
                    if src:
                        lp["src_id"] = src.get("id")
                        lp["src_aid"] = follow
            else:
                # Takip başka deftere geçti; bu pozisyon eskisinden kaldı.
                # Kendi kaynak defterine göre stop'u ve kapanışı yönetilmeye
                # devam etsin — yoksa sahipsiz kalıp açıkta unutuluyor.
                # Sembol eşlemesi yok: başka defterin aynı coinine yapışmasın.
                src = orphan_by_id.get(str(lp.get("src_id") or ""))
            if src and str(lp.get("symbol") or "") not in want_close:
                _copy_paper_atr(lp, src)
                info = marks.get(str(lp.get("symbol") or "")) or {}
                last = float(info.get("price") or info.get("mark") or 0)
                if last > 0:
                    lp["mark"] = last
                _sync_step_trail(lp)
                if _maybe_stop_close(b, lp, marks):
                    continue
                continue
            _queue_close(b, str(lp.get("symbol") or ""), "paper_close", str(lp.get("src_id") or ""))
            _flush_symbol(b, str(lp.get("symbol") or ""), "paper_close", str(lp.get("src_id") or ""))
        _mirror_opens(b, paper_pos, marks, frames)
        _save()
    _flush_mirror_fills()


def _mirror_opens(b: dict, paper_pos: list, marks: dict, frames: dict | None = None) -> None:
    """Sanal açıksa LIVE aç. Sorgulama, skip yok."""
    if not b.get("active"):
        return
    frames = frames or {}
    blocked = _pending_syms(b)
    live_src = {str(p.get("src_id") or "") for p in b.get("positions") or []}
    live_sym = {str(p.get("symbol") or "") for p in b.get("positions") or []}
    paper_ids = {str(p.get("id") or "") for p in paper_pos if p.get("id")}
    skip = set(b.get("skip_src") or [])
    pending = b.setdefault("pending_open", [])
    for p in paper_pos:
        pid = str(p.get("id") or "")
        sym = str(p.get("symbol") or "")
        if not pid or not sym:
            continue
        if pid in skip:
            if pid in pending:
                pending.remove(pid)
            continue
        if pid in live_src or sym in live_sym or sym in blocked:
            if pid in pending:
                pending.remove(pid)
            continue
        got = _open_pos(
            b, sym, str(p.get("side") or ""), marks, frames.get(sym),
            src_id=pid, src=p,
        )
        if got:
            live_src.add(pid)
            live_sym.add(sym)
            if pid in pending:
                pending.remove(pid)
        elif pid not in pending:
            pending.append(pid)
    b["pending_open"] = [pid for pid in pending if pid in paper_ids]


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
    """Sahte 0 PnL / exit=entry kayıtlarını Binance dolumundan düzelt."""
    fixed = []
    with _lock:
        b = _load()
        for h in b.get("history") or []:
            entry = float(h.get("entry") or 0)
            exit_px = float(h.get("exit") or 0)
            net = float(h.get("net") or 0)
            reason = str(h.get("reason") or "")
            same_px = entry > 0 and abs(exit_px - entry) <= max(entry * 1e-8, 1e-12)
            zero_flat = reason == "binance_flat" and abs(net) < 1e-9
            if not same_px and not zero_flat:
                continue
            sym = str(h.get("symbol") or "")
            if not sym:
                continue
            try:
                trades = fapi.user_trades(sym, 80)
            except Exception:
                trades = []
            t1 = _iso_ms(str(h.get("closed_iso") or h.get("iso") or "")) or int(time.time() * 1000)
            t0 = _iso_ms(str(h.get("opened_iso") or ""))
            if t0 <= 0:
                t0 = t1 - 8 * 3600 * 1000
            t0 -= 15_000
            t1 += 15_000
            side = str(h.get("side") or "")
            open_side = "SELL" if side == "SHORT" else "BUY"
            close_side = "BUY" if side == "SHORT" else "SELL"
            window = [t for t in trades if t0 <= int(t.get("time") or 0) <= t1]
            opens = [t for t in window if str(t.get("side")) == open_side]
            closes = [t for t in window if str(t.get("side")) == close_side]
            if not closes:
                closes = [t for t in trades if str(t.get("side")) == close_side and abs(float(t.get("realizedPnl") or 0)) > 0][-8:]
            if not opens:
                opens = [t for t in trades if str(t.get("side")) == open_side][:8]
            if closes:
                e_px, _, fee_o, _ = _trades_vwap(opens) if opens else (entry, 0.0, 0.0, 0.0)
                x_px, qty, fee_c, rpnl = _trades_vwap(closes)
                if e_px <= 0:
                    e_px = entry
                if x_px <= 0:
                    x_px = exit_px
                fee = fee_o + fee_c
                gross = rpnl if abs(rpnl) > 0 else paper._pnl(side, e_px, x_px, qty)
                h["entry"] = e_px
                h["exit"] = x_px
                h["gross"] = round(gross, 2)
                h["commission"] = round(fee, 2)
                h["net"] = round(gross - fee, 2)
                if h.get("reason") == "binance_flat":
                    h["reason"] = "kapanış"
                fixed.append({"symbol": sym, "net": h["net"]})
                continue
            qty = float(h.get("qty") or 0)
            if qty <= 0 or entry <= 0 or exit_px <= 0:
                continue
            fee = paper._fee_on(qty, entry) + paper._fee_on(qty, exit_px)
            gross = paper._pnl(side, entry, exit_px, qty)
            h["gross"] = round(gross, 2)
            h["commission"] = round(fee, 2)
            h["net"] = round(gross - fee, 2)
            if h.get("reason") == "binance_flat":
                h["reason"] = "kapanış"
            fixed.append({"symbol": sym, "net": h["net"]})
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
