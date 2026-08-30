"""MATCHDAY üst menü — tüm /site sayfalarında aynı."""

SITE_NAV_CSS = """
.nav{position:sticky;top:0;z-index:40;background:rgba(8,12,20,.94);border-bottom:1px solid rgba(255,255,255,.06);display:flex;align-items:center;gap:22px;padding:14px 28px;backdrop-filter:blur(12px)}
.logo{display:flex;align-items:center;gap:10px;font:700 15px/1 Oswald,sans-serif;letter-spacing:.12em;color:#fff}
.logo i{width:38px;height:38px;border-radius:10px;background:var(--y,#F5C518);color:var(--ink,#111);display:grid;place-items:center;font-style:normal;font-size:18px;margin-right:0}
.links{display:flex;gap:22px;margin-left:18px;flex-wrap:wrap}
.links a{font:600 13px/1 Oswald,sans-serif;letter-spacing:.1em;color:#c5c9d1}
.links a:hover{color:var(--y,#F5C518)}
.sp{flex:1}
.cta{background:var(--y,#F5C518);color:var(--ink,#111);border:0;border-radius:6px;padding:10px 18px;font:800 12px/1 Oswald,sans-serif;letter-spacing:.1em}
.cta.gb{background:#171b1f;color:#c1ff72;margin-right:8px}
@media(max-width:800px){.nav{padding:12px 14px;gap:12px;flex-wrap:wrap}.links{margin-left:0;gap:14px}}
"""

SITE_NAV = """
<header class="nav">
  <a class="logo" href="/site"><i>⚽</i> MATCHDAY</a>
  <nav class="links">
    <a href="/site">MAÇLAR</a>
    <a href="/site/kuponlar">KUPONLAR</a>
    <a href="/site/biten">BİTMİŞ</a>
  </nav>
  <div class="sp"></div>
  <a class="cta gb" href="/bahis">GB</a>
  <a class="cta" href="/site/kuponlar">KUPONLAR</a>
</header>
"""


def apply_nav(html: str) -> str:
    return html.replace("__SITE_NAV_CSS__", SITE_NAV_CSS).replace("__SITE_NAV__", SITE_NAV)
