"""Açık kupon ayakları için Fotmob canlı skor. Emir yok."""
from __future__ import annotations

import time
from typing import Any

from bahis.fetch_leagues import fetch_fotmob_payload
from bahis.league import all_matches, team_key
from bahis.leagues_cfg import get as get_league, set_league

TTL = 40
_CACHE: dict[str, Any] = {"ts": 0.0, "by_mid": {}}


def _parse(m: dict) -> dict | None:
    st = m.get("status") or {}
    if st.get("cancelled") or st.get("awarded"):
        return None
    hg = ag = None
    hs = st.get("scoreStr") or ""
    if isinstance(hs, str) and "-" in hs:
        a, b = hs.split("-", 1)
        try:
            hg, ag = int(a.strip()), int(b.strip())
        except ValueError:
            hg = ag = None
    if hg is None:
        h, a = (m.get("home") or {}).get("score"), (m.get("away") or {}).get("score")
        if h is not None and a is not None:
            try:
                hg, ag = int(h), int(a)
            except (TypeError, ValueError):
                hg = ag = None
    started = bool(st.get("started") or st.get("liveTime") or st.get("finished"))
    finished = bool(st.get("finished"))
    if hg is None and not started:
        return None
    minute = ""
    lt = st.get("liveTime") or st.get("reason") or {}
    if isinstance(lt, dict):
        minute = str(lt.get("short") or lt.get("long") or "")
    elif isinstance(lt, str):
        minute = lt
    if finished:
        minute = "MS"
    elif started and not minute:
        minute = "CANLI"
    return {
        "hg": 0 if hg is None else hg,
        "ag": 0 if ag is None else ag,
        "started": started or finished,
        "finished": finished,
        "minute": minute,
        "fotmob_id": str(m.get("id") or ""),
    }


def _index(lid: str) -> dict[str, str]:
    set_league(lid)
    out: dict[str, str] = {}
    for m in all_matches():
        mid = m.get("id") or ""
        fid = m.get("fotmob_id")
        if fid:
            out[str(fid)] = mid
        hk = (m.get("home") or {}).get("key")
        ak = (m.get("away") or {}).get("key")
        ko = (m.get("kickoff") or "")[:10]
        if hk and ak and ko:
            out[f"{hk}|{ak}|{ko}"] = mid
    return out


def _pull_league(lid: str) -> dict[str, dict]:
    lg = get_league(lid)
    data, err = fetch_fotmob_payload(lg)
    if err or not data:
        return {}
    matches = (
        ((data.get("fixtures") or {}).get("allMatches"))
        or ((data.get("overview") or {}).get("matches") or {}).get("allMatches")
        or []
    )
    idx = _index(lid)
    out: dict[str, dict] = {}
    for m in matches:
        rec = _parse(m)
        if not rec or not rec.get("started"):
            continue
        mid = idx.get(rec["fotmob_id"])
        if not mid:
            hk = team_key((m.get("home") or {}).get("name") or "")
            ak = team_key((m.get("away") or {}).get("name") or "")
            utc = str((m.get("status") or {}).get("utcTime") or "")[:10]
            mid = idx.get(f"{hk}|{ak}|{utc}")
        if mid:
            rec["id"] = mid
            out[mid] = rec
    return out


def for_leagues(lids: list[str]) -> dict[str, dict]:
    now = time.time()
    if now - float(_CACHE.get("ts") or 0) < TTL and _CACHE.get("by_mid"):
        return _CACHE["by_mid"]
    by: dict[str, dict] = {}
    for lid in lids:
        try:
            by.update(_pull_league(lid))
        except Exception:
            continue
    _CACHE["ts"] = now
    _CACHE["by_mid"] = by
    return by
