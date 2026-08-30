"""Korner toplamı — Poisson attack/defense, dixon_coles.py ile aynı mimari.

Bağımsız Poisson (rho düzeltmesi yok): korner sayıları gol gibi düşük
sayılarda kritik bağımlılık göstermiyor, ortalama 5-6/takım seviyesinde.
Ham veri: league.py maç kayıtlarındaki hc/ac (ev/deplasman korner).
Piyasa oran kaynağı henüz yok → value/coupon'a bağlanmadı, sadece
tahmin çıktısı üretir (bkz. modül sonundaki not). Emir yok.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from bahis.dixon_coles import _GUN, _pct, _round_p, _time_weight, _when, poisson_pmf
from bahis.league import all_matches, team_info

TR = ZoneInfo("Europe/Istanbul")
HALF_LIFE_DAYS = 180
MAX_ITER = 300
HOME_ADV = 0.12          # korner'de ev avantajı gollerden daha zayıf
MAX_CORNERS = 20
UPCOMING_DAYS = 21
UPCOMING_LIMIT = 24
LINES = (7.5, 8.5, 9.5, 10.5, 11.5)


class CornerModel:
    """dixon_coles.DixonColesModel'in korner karşılığı — rho'suz Poisson."""

    def __init__(self, matches: list[dict], half_life_days: float = HALF_LIFE_DAYS, max_iter: int = MAX_ITER):
        self.matches = matches
        self.half_life_days = half_life_days
        self.max_iter = max_iter
        teams: set[str] = set()
        for m in matches:
            teams.add(m["home"])
            teams.add(m["away"])
        self.teams = list(teams)
        self.params: dict[str, dict[str, float]] = {}
        self.home_adv = HOME_ADV
        self.avg_corners = 5.0

    def fit(self) -> dict[str, dict[str, float]]:
        teams = self.teams
        if not teams:
            self.params = {}
            return self.params
        att = {t: 1.0 for t in teams}
        deff = {t: 1.0 for t in teams}
        n = max(len(self.matches), 1)
        avg = sum(m["homeCorners"] + m["awayCorners"] for m in self.matches) / (n * 2) or 5.0
        ref = datetime.now(TR)
        exp_h = math.exp(self.home_adv)

        for _ in range(self.max_iter):
            att_num = {t: 0.0 for t in teams}
            att_den = {t: 0.0 for t in teams}
            def_num = {t: 0.0 for t in teams}
            def_den = {t: 0.0 for t in teams}
            for m in self.matches:
                w = _time_weight(m["date"], ref, self.half_life_days)
                att_num[m["home"]] += w * m["homeCorners"]
                att_den[m["home"]] += w * (deff[m["away"]] * exp_h * avg)
                def_num[m["away"]] += w * m["homeCorners"]
                def_den[m["away"]] += w * (att[m["home"]] * exp_h * avg)
                att_num[m["away"]] += w * m["awayCorners"]
                att_den[m["away"]] += w * (deff[m["home"]] * avg)
                def_num[m["home"]] += w * m["awayCorners"]
                def_den[m["home"]] += w * (att[m["away"]] * avg)
            for t in teams:
                if att_den[t] > 0:
                    att[t] = att_num[t] / att_den[t]
                if def_den[t] > 0:
                    deff[t] = def_num[t] / def_den[t]
            mean_att = sum(att.values()) / len(teams)
            mean_def = sum(deff.values()) / len(teams)
            for t in teams:
                att[t] /= mean_att
                deff[t] /= mean_def

        # Az maçlı takım 1.0'a doğru çek (dixon_coles.py'deki aynı mantık)
        seen = {t: 0 for t in teams}
        for m in self.matches:
            seen[m["home"]] += 1
            seen[m["away"]] += 1
        for t in teams:
            k = seen[t]
            if k < 10:
                w = k / 10
                att[t] = w * att[t] + (1 - w)
                deff[t] = w * deff[t] + (1 - w)
        mean_att = sum(att.values()) / len(teams)
        mean_def = sum(deff.values()) / len(teams)
        for t in teams:
            att[t] /= mean_att
            deff[t] /= mean_def

        self.params = {t: {"attack": att[t], "defense": deff[t]} for t in teams}
        self.avg_corners = avg
        return self.params

    def _strength(self, key: str) -> dict[str, float]:
        return self.params.get(key) or {"attack": 1.0, "defense": 1.0}

    def expected_corners(self, home: str, away: str) -> dict[str, float]:
        h, a = self._strength(home), self._strength(away)
        lam = h["attack"] * a["defense"] * math.exp(self.home_adv) * self.avg_corners
        mu = a["attack"] * h["defense"] * self.avg_corners
        return {"lambda": lam, "mu": mu}

    def markets(self, home: str, away: str, *, lam: float | None = None, mu: float | None = None) -> dict:
        if lam is None or mu is None:
            xg = self.expected_corners(home, away)
            lam, mu = xg["lambda"], xg["mu"]
        # Bağımsız Poisson: P(toplam=k) = konvolüsyon
        p_home = [poisson_pmf(lam, x) for x in range(MAX_CORNERS + 1)]
        p_away = [poisson_pmf(mu, y) for y in range(MAX_CORNERS + 1)]
        tot_dist = [0.0] * (2 * MAX_CORNERS + 1)
        for x, px in enumerate(p_home):
            for y, py in enumerate(p_away):
                tot_dist[x + y] += px * py
        total_p = sum(tot_dist) or 1.0
        tot_dist = [p / total_p for p in tot_dist]
        over_under = {}
        for line in LINES:
            under = sum(tot_dist[: int(math.floor(line)) + 1])
            over_under[str(line)] = {"under": round(under, 4), "over": round(1 - under, 4)}
        exp_total = sum(k * p for k, p in enumerate(tot_dist))
        return {
            "expectedCorners": {"lambda": lam, "mu": mu, "total": round(exp_total, 2)},
            "overUnder": over_under,
            "totalDist": tot_dist,
        }


def _train_rows() -> list[dict]:
    rows = []
    for m in all_matches():
        if not m.get("played"):
            continue
        hc, ac = m.get("hc"), m.get("ac")
        if hc is None or ac is None:
            continue
        ko = m.get("kickoff")
        try:
            dt = datetime.fromisoformat((ko or "").replace("Z", "+00:00"))
            dt = dt.replace(tzinfo=TR) if dt.tzinfo is None else dt.astimezone(TR)
        except ValueError:
            dt = datetime(2016, 1, 1, tzinfo=TR)
        rows.append({
            "home": m["home"]["key"],
            "away": m["away"]["key"],
            "homeCorners": int(hc),
            "awayCorners": int(ac),
            "date": dt,
        })
    return rows


@lru_cache(maxsize=8)
def _fitted_for(league: str) -> CornerModel:
    from bahis.leagues_cfg import set_league
    set_league(league)
    model = CornerModel(_train_rows())
    model.fit()
    return model


def _fitted() -> CornerModel:
    from bahis.leagues_cfg import current_league
    return _fitted_for(current_league())


def _closest_line(book_line: float) -> str | None:
    key = min(LINES, key=lambda l: abs(l - book_line), default=None)
    return str(key) if key is not None and abs(key - book_line) < 0.01 else str(book_line)


def _value_pack(mk: dict, book: dict | None) -> list[dict]:
    """Piyasa korner O/U oranı varsa (bkz. corner_odds.py) fair kenar hesapla."""
    if not book or not book.get("over") or not book.get("under"):
        return []
    from bahis.value import MIN_EDGE, de_vig, implied_raw
    line_key = _closest_line(float(book.get("line") or 9.5))
    model_ou = mk["overUnder"].get(line_key)
    if not model_ou:
        return []
    fair = de_vig({"over": book["over"], "under": book["under"]})
    if not fair:
        return []
    out = []
    for sel, field in (("over", "over"), ("under", "under")):
        o = book.get(field)
        model_p = model_ou.get(sel)
        fair_p = fair["fair"].get(sel)
        if not o or model_p is None or fair_p is None:
            continue
        edge = model_p - fair_p
        if edge >= MIN_EDGE:
            out.append({"pick": sel, "odds": round(float(o), 2), "edge": round(edge, 4),
                        "line": line_key, "implied": round(implied_raw(o) or 0, 4)})
    return out


def _card(m: dict, mk: dict) -> dict:
    hi, ai = m["home"], m["away"]
    xg = mk["expectedCorners"]
    ou = mk["overUnder"]
    line = "9.5"
    pick_over = ou.get(line, {}).get("over", 0) >= 0.5
    from bahis.corner_odds import for_match as corner_book
    book = corner_book(m)
    value = _value_pack(mk, book)
    return {
        "id": m["id"],
        "week": m.get("week"),
        "kickoff": m.get("kickoff"),
        "when": _when(m.get("kickoff")),
        "venue": m.get("venue"),
        "home": hi,
        "away": ai,
        "expectedCorners": {
            "home": round(xg["lambda"], 2),
            "away": round(xg["mu"], 2),
            "total": xg["total"],
        },
        "overUnder": ou,
        "odds": book,
        "odds_src": "pinnacle" if book else None,
        "pick": f"{line} {'Üst' if pick_over else 'Alt'}",
        "pct": _pct(ou.get(line, {}).get("over" if pick_over else "under", 0.5)),
        "value": value,
    }


def upcoming_preds(team: str | None = None, limit: int = UPCOMING_LIMIT) -> dict:
    now = datetime.now(TR)
    until = now + timedelta(days=UPCOMING_DAYS)
    now_s, until_s = now.isoformat(), until.isoformat()
    model = _fitted()
    rows = []
    for m in all_matches():
        if m.get("played"):
            continue
        ko = m.get("kickoff") or ""
        if ko < now_s[:10] or ko > until_s:
            continue
        if team and team not in (m["home"]["key"], m["away"]["key"]):
            continue
        mk = model.markets(m["home"]["key"], m["away"]["key"])
        rows.append(_card(m, mk))
        if len(rows) >= limit:
            break
    used = {r["home"]["key"] for r in rows} | {r["away"]["key"] for r in rows}
    strengths = [
        {"key": k, **team_info(k), "attack": _round_p(v["attack"]), "defense": _round_p(v["defense"])}
        for k, v in sorted(model.params.items(), key=lambda kv: kv[1]["attack"], reverse=True)
        if k in used
    ]
    return {
        "ok": True,
        "model": "corners",
        "note": f"{len(model.matches)} maç · {HALF_LIFE_DAYS}g · bağımsız Poisson (rho yok) · "
                f"Pinnacle korner O/U — endpoint doğrulanmadı, bkz. corner_odds.py",
        "matches_used": len(model.matches),
        "horizon_days": UPCOMING_DAYS,
        "updated": now.isoformat(timespec="seconds"),
        "n": len(rows),
        "preds": rows,
        "strengths": strengths,
    }
