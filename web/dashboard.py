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

from flask import Flask, jsonify, redirect, render_template_string, request, send_file, send_from_directory, session

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
ALG_API_TOKEN = (os.getenv("ALG_API_TOKEN") or "").strip()
PORT = int(os.getenv("COPTC_PORT") or 5060)
APP_NAME = "CemAPI Live Control"
URL_PREFIX = (os.getenv("COPTC_URL_PREFIX") or "").strip().rstrip("/")
if URL_PREFIX and not URL_PREFIX.startswith("/"):
    URL_PREFIX = "/" + URL_PREFIX


class _PrefixMiddleware:
    """nginx /admin/ altında — PATH_INFO önekini soy, oturum çerezi doğru kalsın."""

    def __init__(self, wsgi_app, prefix: str):
        self.wsgi_app = wsgi_app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        environ["SCRIPT_NAME"] = self.prefix
        path = environ.get("PATH_INFO") or "/"
        if path == self.prefix:
            environ["PATH_INFO"] = "/"
        elif path.startswith(self.prefix + "/"):
            environ["PATH_INFO"] = path[len(self.prefix):] or "/"
        scheme = environ.get("HTTP_X_FORWARDED_PROTO")
        if scheme:
            environ["wsgi.url_scheme"] = scheme
        return self.wsgi_app(environ, start_response)


if URL_PREFIX:
    app.wsgi_app = _PrefixMiddleware(app.wsgi_app, URL_PREFIX)
    app.config["SESSION_COOKIE_PATH"] = URL_PREFIX + "/"
    app.config["APPLICATION_ROOT"] = URL_PREFIX


def _url(path: str) -> str:
    return f"{URL_PREFIX}{path}" if URL_PREFIX else path


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
    ctx.setdefault("base", URL_PREFIX)
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
            return redirect(_url("/giris"))
        return fn(*a, **kw)
    return inner


def _algo_token() -> str:
    auth = (request.headers.get("Authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return (
        (request.headers.get("X-Algo-Token") or "").strip()
        or (request.args.get("token") or "").strip()
    )


def _algo_public_ok() -> bool:
    if not ALG_API_TOKEN:
        return False
    got = _algo_token()
    if not got or len(got) != len(ALG_API_TOKEN):
        return False
    return secrets.compare_digest(got, ALG_API_TOKEN)


# ── sayfa şablonları → ui_templates.py ───────────────────────────


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(_STATIC, "favicon.svg", mimetype="image/svg+xml")


@app.route("/giris", methods=["GET", "POST"])
def login():
    if not PASSWORD:
        return redirect(_url("/"))
    err = False
    if request.method == "POST":
        if secrets.compare_digest(request.form.get("p", ""), PASSWORD):
            session["ok"] = True
            return redirect(_url("/"))
        err = True
    return render_template_string(
        _tpl("LOGIN"), err=err, app_name=APP_NAME, static_ver=static_ver(), base=URL_PREFIX,
    )


def _json_login():
    if not PASSWORD:
        session["ok"] = True
        return jsonify({"ok": True})
    d = request.get_json(silent=True) or {}
    p = str(d.get("password") or "")
    if secrets.compare_digest(p, PASSWORD):
        session["ok"] = True
        session.permanent = True
        return jsonify({"ok": True})
    return jsonify({"error": "yanlış parola"}), 401


@app.route("/api/login", methods=["POST"])
def api_login():
    """Mobil uygulama — JSON parola, oturum çerezi döner."""
    return _json_login()


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("ok", None)
    return jsonify({"ok": True})


@app.route("/api/mobile/login", methods=["POST"])
def api_mobile_login():
    return _json_login()


@app.route("/api/mobile/logout", methods=["POST"])
def api_mobile_logout():
    session.pop("ok", None)
    return jsonify({"ok": True})


@app.route("/api/mobile/home")
@guard
def api_mobile_home():
    return jsonify(api.mobile_home())


@app.route("/api/mobile/live", methods=["POST"])
@guard
def api_mobile_live():
    d = request.get_json(silent=True) or {}
    if "on" not in d:
        return jsonify({"error": "on alanı gerekli"}), 400
    return jsonify(api.mobile_set_live(bool(d.get("on"))))


@app.route("/api/mobile/settings")
@guard
def api_mobile_settings():
    return jsonify(api.mobile_settings())


@app.route("/api/mobile/settings/amounts", methods=["POST"])
@guard
def api_mobile_settings_amounts():
    d = request.get_json(silent=True) or {}
    try:
        vals = [round(float(d[k]), 2) for k in ("low", "mid", "high")]
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "low/mid/high sayı olmalı"}), 400
    if not all(1.0 <= v <= 500.0 for v in vals):
        return jsonify({"error": "kademe $1–$500 aralığında olmalı"}), 400
    return jsonify(api.mobile_save_amounts(*vals))


@app.route("/")
@guard
def index():
    return _render("PAGE", book=api.active_book())


@app.route("/ayarlar")
@guard
def settings_page():
    return _render("SETTINGS", book=api.active_book())


@app.route("/islemler")
@guard
def trades_page():
    return _render("TRADES", book=api.active_book())


@app.route("/grafik-analiz")
@guard
def chart_analiz_page():
    return _render("ANALIZ", book=api.active_book())


@app.route("/algoritma-islemler")
@guard
def algo_list_page():
    return _render("ALGOS", book=api.active_book())


@app.route("/algoritma/<aid>")
@guard
def algo_detail_page(aid: str):
    return _render("ALGO_ONE", book=api.active_book(), aid=aid)


@app.route("/indir")
@guard
def download_zip():
    path = os.getenv("COPTC_ZIP") or "/root/projects/CoptC-20260819.zip"
    if not os.path.isfile(path):
        return "zip yok", 404
    return send_file(path, as_attachment=True, download_name="CoptC.zip")


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
    return redirect(_url("/"))


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


@app.route("/api/close-position", methods=["POST"])
@guard
def api_close_position():
    d = request.get_json(silent=True) or {}
    token_id = str(d.get("token_id") or "").strip()
    source = str(d.get("source") or "").strip() or None
    hour_tr = d.get("hour_tr")
    if hour_tr is not None:
        try:
            hour_tr = int(hour_tr)
        except (TypeError, ValueError):
            hour_tr = None
    res, status = api.manual_close_position(token_id, source=source, hour_tr=hour_tr)
    return jsonify(res), status


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


@app.route("/api/desk/snapshot")
@guard
def api_desk_snapshot():
    try:
        period = int(request.args.get("period") or 60)
    except (TypeError, ValueError):
        period = 60
    return jsonify(api.desk_snapshot(period))


@app.route("/api/desk/quote")
@guard
def api_desk_quote():
    try:
        period = int(request.args.get("period") or 60)
        amount = float(request.args.get("amount") or 7)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "tutar/periyot sayı olmalı"})
    return jsonify(api.desk_quote(
        str(request.args.get("symbol") or ""),
        period,
        str(request.args.get("dir") or "UP"),
        amount,
    ))


@app.route("/api/consensus")
@guard
def api_consensus():
    return jsonify(api.desk_consensus())


@app.route("/api/desk/futures")
@guard
def api_desk_futures():
    return jsonify(api.desk_futures())


@app.route("/api/desk/mvrvz")
@guard
def api_desk_mvrvz():
    return jsonify(api.desk_mvrvz(str(request.args.get("symbol") or "BTCUSDT")))


@app.route("/api/desk/confluence")
@guard
def api_desk_confluence():
    return jsonify(api.desk_confluence(str(request.args.get("symbol") or "BTCUSDT")))


@app.route("/api/desk/klines")
@guard
def api_desk_klines():
    ov = str(request.args.get("overlay") or "1").lower() not in ("0", "false", "no")
    return jsonify(api.desk_klines(
        str(request.args.get("symbol") or "BTCUSDT"),
        str(request.args.get("interval") or "1m"),
        overlay=ov,
    ))


@app.route("/api/desk/open", methods=["POST"])
@guard
def api_desk_open():
    d = request.get_json(silent=True) or {}
    try:
        amount = float(d.get("amount") or 0)
        period = int(d.get("period") or 60)
    except (TypeError, ValueError):
        return jsonify({"error": "tutar/periyot sayı olmalı"}), 400
    res, status = api.desk_open(
        str(d.get("symbol") or ""), period,
        str(d.get("dir") or ""), amount,
    )
    return jsonify(res), status


@app.route("/api/desk/close", methods=["POST"])
@guard
def api_desk_close():
    d = request.get_json(silent=True) or {}
    res, status = api.desk_close(str(d.get("id") or ""))
    return jsonify(res), status


@app.route("/api/v1/algos", methods=["GET", "OPTIONS"])
def api_v1_algos():
    """Liste sayfasıyla aynı veri — oturum yok, ALG_API_TOKEN gerekir."""
    if request.method == "OPTIONS":
        resp = app.make_response(("", 204))
    elif not ALG_API_TOKEN:
        resp = jsonify({"error": "ALG_API_TOKEN tanımsız"})
        resp.status_code = 503
    elif not _algo_public_ok():
        resp = jsonify({"error": "yetkisiz"})
        resp.status_code = 401
    else:
        resp = jsonify(api.algo_public_list())
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Authorization, X-Algo-Token"
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return resp


@app.route("/api/algo/overview")
@guard
def api_algo_overview():
    return jsonify(api.algo_overview())


@app.route("/api/algo/<aid>")
@guard
def api_algo_detail(aid: str):
    row = api.algo_detail(aid)
    if not row:
        return jsonify({"error": "algoritma yok"}), 404
    return jsonify(row)


@app.route("/api/algo/<aid>/toggle", methods=["POST"])
@guard
def api_algo_toggle(aid: str):
    row = api.algo_toggle(aid)
    if not row:
        return jsonify({"error": "algoritma yok"}), 404
    return jsonify(row)


@app.route("/api/algo/<aid>/close", methods=["POST"])
@guard
def api_algo_close(aid: str):
    d = request.get_json(silent=True) or {}
    res, status = api.algo_close(aid, str(d.get("id") or ""))
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
    a1_vals = None
    if all(k in d for k in ("a1_low", "a1_mid", "a1_high")):
        try:
            a1_vals = [round(float(d[k]), 2) for k in ("a1_low", "a1_mid", "a1_high")]
        except (TypeError, ValueError):
            return jsonify({"error": "A1 low/mid/high sayı olmalı"}), 400
        if not all(1.0 <= v <= 500.0 for v in a1_vals):
            return jsonify({"error": "A1 kademe $1–$500 aralığında olmalı"}), 400
    c1_vals = None
    if all(k in d for k in ("c1_low", "c1_mid", "c1_high")):
        try:
            c1_vals = [round(float(d[k]), 2) for k in ("c1_low", "c1_mid", "c1_high")]
        except (TypeError, ValueError):
            return jsonify({"error": "C1#01 low/mid/high sayı olmalı"}), 400
        if not all(1.0 <= v <= 500.0 for v in c1_vals):
            return jsonify({"error": "C1#01 kademe $1–$500 aralığında olmalı"}), 400
    cold = d.get("cold_hour_cut_enabled")
    cold_opt = bool(cold) if cold is not None else None
    profit = d.get("min_profit_pct")
    if profit is not None:
        try:
            profit = round(float(profit), 1)
        except (TypeError, ValueError):
            return jsonify({"error": "asgari kâr yüzdesi sayı olmalı"}), 400
        if not 0.0 <= profit <= 900.0:
            return jsonify({"error": "asgari kâr %0–%900 aralığında olmalı"}), 400
    return jsonify(api.save_amounts(
        book, *vals,
        min_profit_pct=profit,
        a1_low=a1_vals[0] if a1_vals else None,
        a1_mid=a1_vals[1] if a1_vals else None,
        a1_high=a1_vals[2] if a1_vals else None,
        c1_low=c1_vals[0] if c1_vals else None,
        c1_mid=c1_vals[1] if c1_vals else None,
        c1_high=c1_vals[2] if c1_vals else None,
        cold_hour_cut_enabled=cold_opt,
    ))


def _start_algo_loop():
    try:
        p = os.path.join(_DIR, "..", "poly")
        if p not in sys.path:
            sys.path.insert(0, p)
        import algo_paper
        algo_paper.ensure_started()
    except Exception as exc:
        print("algo_paper:", exc)


_start_algo_loop()


if __name__ == "__main__":
    if not PASSWORD:
        print("UYARI: COPTC_PASSWORD tanımsız — panel korumasız, Live düğmesi herkese açık.")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
