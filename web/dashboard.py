#!/usr/bin/env python3
"""CoptC Live Control — API mirror dashboard.

    python3 web/dashboard.py            # 0.0.0.0:5060
    COPTC_PASSWORD=... python3 web/dashboard.py

`Live aç` gerçek para harcatır; `COPTC_PASSWORD` tanımlıysa oturum açmadan
hiçbir uç noktaya erişilemez.
"""
from __future__ import annotations

import os
import secrets
import sys
from functools import wraps

from flask import Flask, jsonify, redirect, render_template_string, request, send_from_directory, session

_DIR = os.path.dirname(os.path.abspath(__file__))
_STATIC = os.path.join(_DIR, "static")
sys.path.insert(0, _DIR)

import api  # noqa: E402
import ui_templates  # noqa: E402

app = Flask(__name__)
# .env'de anahtar tanımlı ama boşsa getenv boş string döner; `or` ile yakala,
# yoksa Flask "no secret key" diye oturumu tamamen reddediyor.
app.secret_key = os.getenv("COPTC_SECRET") or secrets.token_hex(16)
PASSWORD = (os.getenv("COPTC_PASSWORD") or "").strip()
PORT = int(os.getenv("COPTC_PORT") or 5060)
APP_NAME = "CoptC Live Control"


def static_ver() -> str:
    """CSS/şablon değişince tarayıcı eski dosyayı tutmasın."""
    mt = 0.0
    for path in (
        os.path.join(_DIR, "ui_templates.py"),
        os.path.join(_STATIC, "coptc.css"),
        os.path.join(_DIR, "dashboard.py"),
    ):
        try:
            mt = max(mt, os.path.getmtime(path))
        except OSError:
            pass
    return str(int(mt)) if mt else "0"


def _tpl(name: str) -> str:
    """ui_templates.py değişince restart gerekmeden yeni HTML."""
    import importlib
    importlib.reload(ui_templates)
    return getattr(ui_templates, name)


def _render(name: str, **ctx):
    ctx.setdefault("app_name", APP_NAME)
    ctx.setdefault("static_ver", static_ver())
    return render_template_string(_tpl(name), **ctx)


@app.after_request
def _no_cache(resp):
    """Panel canlı veri gösterir — tarayıcı eski sayfayı/veriyi tutmasın."""
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp


def guard(fn):
    @wraps(fn)
    def inner(*a, **kw):
        if PASSWORD and not session.get("ok"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "yetkisiz"}), 401
            return redirect("/giris")
        return fn(*a, **kw)
    return inner


# ── sayfa şablonları → ui_templates.py ───────────────────────────


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(_STATIC, "favicon.svg", mimetype="image/svg+xml")


@app.route("/giris", methods=["GET", "POST"])
def login():
    if not PASSWORD:
        return redirect("/")
    err = False
    if request.method == "POST":
        if secrets.compare_digest(request.form.get("p", ""), PASSWORD):
            session["ok"] = True
            return redirect("/")
        err = True
    return render_template_string(_tpl("LOGIN"), err=err, app_name=APP_NAME, static_ver=static_ver())


@app.route("/")
@guard
def index():
    return _render("PAGE", book=api.active_book())


@app.route("/ayarlar")
@guard
def settings_page():
    return _render("SETTINGS", book=api.active_book())


@app.route("/api/mirror/books")
@guard
def api_mirror_books():
    return jsonify(api.mirror_books())


@app.route("/api/mirror/select", methods=["POST"])
@guard
def api_mirror_select():
    """Çoklu seçim: {"books": [...]}. Tekil {"book": "..."} da kabul edilir."""
    d = request.get_json(silent=True) or {}
    raw = d.get("books")
    if not isinstance(raw, list):
        raw = [d.get("book")]
    books = [str(b or "").strip() for b in raw]
    books = [b for b in books if b]
    if not books:
        return jsonify({"error": "defter belirtilmedi"}), 400
    if len(books) > api.MIRROR_BOOKS_MAX:
        return jsonify({"error": f"en fazla {api.MIRROR_BOOKS_MAX} algoritma seçilebilir"}), 400
    known = {b.get("book") for b in (api.mirror_books().get("books") or [])}
    unknown = [b for b in books if known and b not in known]
    if unknown:
        return jsonify({"error": f"bilinmeyen defter: {', '.join(unknown)}"}), 404
    return jsonify({"selected": api.set_mirror_book_list(books)})


@app.route("/<book>")
@guard
def page(book: str):
    """Eski defter linkleri — tek sayfaya yönlendir."""
    return redirect("/")


@app.route("/api/active", methods=["POST"])
@guard
def api_active():
    d = request.get_json(silent=True) or {}
    book = str(d.get("book") or "")
    if book not in api.BOOKS:
        return jsonify({"error": "bilinmeyen model"}), 404
    return jsonify(api.set_active(book, bool(d.get("on"))))


@app.route("/api/weekend", methods=["POST"])
@guard
def api_weekend():
    d = request.get_json(silent=True) or {}
    enabled = d.get("enabled")
    if enabled is None:
        enabled = not api.weekend_info().get("enabled")
    return jsonify(api.set_weekend_pause(bool(enabled)))


@app.route("/api/redeem", methods=["POST"])
@guard
def api_redeem():
    return jsonify(api.cash_out_now())


@app.route("/api/close-all", methods=["POST"])
@guard
def api_close_all():
    res, status = api.manual_close_all()
    return jsonify(res), status


@app.route("/api/overview")
@guard
def api_overview_active():
    """Aktif model — sayfa hangi HTML'den açılırsa açılsın tek doğru kaynak."""
    return jsonify(api.overview(api.active_book()))


@app.route("/api/<book>/overview")
@guard
def api_overview(book: str):
    if book not in api.BOOKS:
        return jsonify({"error": "bilinmeyen defter"}), 404
    return jsonify(api.overview(book))


@app.route("/api/<book>/signals")
@guard
def api_signals(book: str):
    if book not in api.BOOKS:
        return jsonify({"error": "bilinmeyen defter"}), 404
    return jsonify(api.live_signals(book))


@app.route("/api/<book>/live", methods=["POST"])
@guard
def api_live(book: str):
    if book not in api.BOOKS:
        return jsonify({"error": "bilinmeyen defter"}), 404
    want = bool((request.get_json(silent=True) or {}).get("open"))
    return jsonify({"live_open": api.set_live(book, want)})


@app.route("/api/withdraw/info")
@guard
def api_withdraw_info():
    info = api.withdraw_info()
    info["history"] = api.withdraw_history()
    return jsonify(info)


@app.route("/api/withdraw/send", methods=["POST"])
@guard
def api_withdraw_send():
    # Parola korumasız panelde gerçek para gönderimi açılmaz.
    if not PASSWORD:
        return jsonify({"error": "Panel parolasız — çekim kapalı. .env'e COPTC_PASSWORD ekle."}), 403
    d = request.get_json(silent=True) or {}
    res, status = api.withdraw_send(
        to=str(d.get("to") or ""), amount=d.get("amount"),
        code=str(d.get("code") or ""), token=str(d.get("token") or "PUSD"),
    )
    return jsonify(res), status


@app.route("/api/<book>/amounts", methods=["POST"])
@guard
def api_amounts(book: str):
    if book not in api.BOOKS:
        return jsonify({"error": "bilinmeyen defter"}), 404
    d = request.get_json(silent=True) or {}
    try:
        vals = [round(float(d[k]), 2) for k in ("low", "mid", "high")]
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "low/mid/high sayı olmalı"}), 400
    if not all(1.0 <= v <= 500.0 for v in vals):
        return jsonify({"error": "kademe $1–$500 aralığında olmalı"}), 400
    cold = d.get("cold_hour_cut_enabled")
    cold_opt = bool(cold) if cold is not None else None
    return jsonify(api.save_amounts(book, *vals, cold_hour_cut_enabled=cold_opt))


if __name__ == "__main__":
    if not PASSWORD:
        print("UYARI: COPTC_PASSWORD tanımsız — panel korumasız, Live düğmesi herkese açık.")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
