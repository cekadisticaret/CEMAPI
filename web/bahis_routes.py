"""Futbol bahis paketi — /bahis altında sayfa + API. Emir yok."""
from __future__ import annotations

import json
import os
import sys

from flask import Response, jsonify, redirect, request

_WEB = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_WEB)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _rewrite(html: str, prefix: str) -> str:
    from bahis.site_nav import apply_nav

    html = apply_nav(html)
    p = (prefix or "").rstrip("/")
    html = html.replace("/bahis", f"{p}/bahis")
    html = html.replace("/site", f"{p}/bahis/site")
    return html


def _html(body: str) -> Response:
    resp = Response(body, mimetype="text/html; charset=utf-8")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp


def _apply_league() -> None:
    from bahis.leagues_cfg import set_league

    lg = (request.args.get("league") or "").strip()
    if lg:
        set_league(lg)


def _err(exc: Exception, code: int = 500):
    return jsonify({"ok": False, "error": str(exc)}), code


def register_bahis(app, guard, prefix: str, url_fn) -> None:
    @app.route("/bahis/app")
    @guard
    def bahis_app():
        from bahis.engines import list_engines
        from bahis.pages import BAHIS_HTML

        html = BAHIS_HTML.replace("__ENGINES__", json.dumps(list_engines(), ensure_ascii=False))
        html = _rewrite(html, prefix)
        p = (prefix or "").rstrip("/")
        html = html.replace("__SITE_URL__", f"{p}/bahis/site")
        html = html.replace("__HOME_URL__", p or "/")
        return _html(html)

    @app.route("/bahis/kuponlar")
    @guard
    def bahis_kuponlar():
        return redirect(url_fn("/bahis/site/kuponlar"))

    @app.route("/bahis/site")
    @guard
    def bahis_site():
        from bahis.site import BAHIS_SITE_HTML

        return _html(_rewrite(BAHIS_SITE_HTML, prefix))

    @app.route("/bahis/site/kuponlar")
    @guard
    def bahis_site_kuponlar():
        from bahis.site_coupons import SITE_COUPONS_HTML

        return _html(_rewrite(SITE_COUPONS_HTML, prefix))

    @app.route("/bahis/site/biten")
    @guard
    def bahis_site_biten():
        from bahis.site_results import SITE_RESULTS_HTML

        return _html(_rewrite(SITE_RESULTS_HTML, prefix))

    @app.route("/bahis/site/mac/<path:mid>")
    @guard
    def bahis_site_mac(mid: str):
        from bahis.site_match import SITE_MATCH_HTML

        p = (prefix or "").rstrip("/")
        js_path = os.path.join(_WEB, "static", "matchday_detail.js")
        try:
            ver = str(int(os.path.getmtime(js_path)))
        except OSError:
            ver = "1"
        html = _rewrite(SITE_MATCH_HTML, prefix)
        html = html.replace("__MID__", json.dumps(mid))
        html = html.replace("__API__", json.dumps(f"{p}/bahis/site/api/match"))
        html = html.replace("__JS__", f"{p}/static/matchday_detail.js?v={ver}")
        return _html(html)

    @app.route("/bahis/api/summary")
    @app.route("/bahis/site/api/summary")
    @guard
    def bahis_api_summary():
        try:
            _apply_league()
            from bahis.league import summary

            return jsonify(summary())
        except Exception as e:
            return _err(e)

    @app.route("/bahis/api/matches")
    @app.route("/bahis/site/api/matches")
    @guard
    def bahis_api_matches():
        try:
            _apply_league()
            from bahis.league import list_matches

            lim = request.args.get("limit")
            return jsonify(list_matches(
                season=request.args.get("season") or None,
                team=request.args.get("team") or None,
                status=request.args.get("status") or "all",
                limit=int(lim) if lim else None,
            ))
        except Exception as e:
            return _err(e)

    @app.route("/bahis/api/h2h")
    @app.route("/bahis/site/api/h2h")
    @guard
    def bahis_api_h2h():
        try:
            _apply_league()
            from bahis.league import pair_h2h

            a = (request.args.get("a") or "").strip()
            b = (request.args.get("b") or "").strip()
            if not a or not b:
                return jsonify({"ok": False, "error": "takım yok"}), 400
            return jsonify(pair_h2h(a, b))
        except Exception as e:
            return _err(e)

    @app.route("/bahis/api/preds")
    @guard
    def bahis_api_preds():
        try:
            from bahis.engines import run

            lim = request.args.get("limit") or "24"
            try:
                limit = max(1, min(int(lim), 80))
            except ValueError:
                limit = 24
            return jsonify(run(
                engine_id=request.args.get("engine") or None,
                team=request.args.get("team") or None,
                limit=limit,
                league=request.args.get("league") or None,
            ))
        except Exception as e:
            return _err(e)

    @app.route("/bahis/api/players")
    @guard
    def bahis_api_players():
        try:
            _apply_league()
            from bahis import players

            pid = request.args.get("id")
            if pid:
                return jsonify(players.player(int(pid)))
            kind = (request.args.get("kind") or "").strip()
            season = request.args.get("season") or None
            if kind == "summary":
                return jsonify(players.summary(season))
            if kind == "squad":
                return jsonify(players.squad(request.args.get("team") or None))
            if kind == "leaders":
                return jsonify(players.leaders(
                    season,
                    request.args.get("stat") or "goals",
                    int(request.args.get("limit") or 25),
                ))
            lim = request.args.get("limit") or "80"
            try:
                limit = max(1, min(int(lim), 400))
            except ValueError:
                limit = 80
            return jsonify(players.list_players(
                season=season,
                team=request.args.get("team") or None,
                q=request.args.get("q") or None,
                sort=request.args.get("sort") or "goals",
                limit=limit,
            ))
        except Exception as e:
            return _err(e)

    @app.route("/bahis/site/api/coupons")
    @guard
    def bahis_api_coupons():
        try:
            from bahis.coupon_book import listing

            return jsonify(listing(
                league=request.args.get("league") or None,
                tab=request.args.get("tab") or "open",
                limit=int(request.args.get("limit") or 80),
            ))
        except Exception as e:
            return _err(e)

    @app.route("/bahis/site/api/leagues")
    @guard
    def bahis_api_leagues():
        try:
            from bahis.leagues_cfg import list_public

            return jsonify({"ok": True, "leagues": list_public()})
        except Exception as e:
            return _err(e)

    @app.route("/bahis/site/api/finished")
    @guard
    def bahis_api_finished():
        try:
            from bahis.results import finished

            return jsonify(finished(
                limit=int(request.args.get("limit") or 40),
                league=request.args.get("league") or None,
            ))
        except Exception as e:
            return _err(e)

    @app.route("/bahis/api/match")
    @app.route("/bahis/site/api/match")
    @guard
    def bahis_api_match():
        try:
            from bahis.match_intel import detail

            mid = (request.args.get("id") or "").strip()
            if not mid:
                return jsonify({"ok": False, "error": "maç yok"}), 400
            return jsonify(detail(mid))
        except Exception as e:
            return _err(e)
