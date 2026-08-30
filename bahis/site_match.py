""" /site/mac — maç detay, tüm pazarlar. Emir yok. """

SITE_MATCH_HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maç detay · MATCHDAY</title>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Oswald:wght@500;700&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#080c14;--card:#101826;--line:rgba(245,197,24,.28);--y:#F5C518;--ink:#111;--txt:#fff;--muted:#9aa3b2}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:Inter,system-ui,sans-serif}
a{color:inherit;text-decoration:none}
__SITE_NAV_CSS__
.wrap{max-width:1100px;margin:0 auto;padding:22px 18px 56px}
.hero{text-align:center;padding:18px 0 10px}
.hero h1{font:italic 800 42px/1 Anton,sans-serif;color:var(--y)}
.vs{display:flex;align-items:center;justify-content:center;gap:22px;margin:16px 0}
.vs img,.fb{width:72px;height:72px;border-radius:50%;background:#fff;object-fit:contain}
.fb{display:grid;place-items:center;font-weight:800;color:#111}
.vs b{display:block;margin-top:6px;font:700 13px Oswald,sans-serif}
.pick{color:var(--y);font:700 16px Oswald,sans-serif;margin:8px 0}
.models{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:16px 0}
.mb{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;text-align:center}
.mb s{display:block;text-decoration:none;color:var(--y);font:700 10px Oswald,sans-serif;letter-spacing:.08em}
.mb b{display:block;font-size:13px;margin-top:4px}
.g{margin:22px 0 8px;font:700 13px Oswald,sans-serif;letter-spacing:.14em;color:var(--y)}
.note{font-size:12px;color:var(--muted);margin-bottom:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
.box{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px}
.box s{display:block;text-decoration:none;color:var(--muted);font-size:10px;font-weight:700}
.box b{display:block;margin-top:4px;font-size:15px}
.box.on{border-color:var(--y);background:#1a1608}
.val{color:#22c55e;font-size:11px;font-weight:800}
.warn{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin:8px 0 18px}
.wb{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}
.wb.bad{border-color:#e11d48;background:#1a0c10}
.wb s{display:block;text-decoration:none;color:var(--y);font:700 11px Oswald,sans-serif;letter-spacing:.08em}
.wb p{margin-top:6px;font-size:12px;color:#c8ced8;line-height:1.45}
@media(max-width:800px){.warn{grid-template-columns:1fr}}
.scores{display:flex;flex-wrap:wrap;gap:6px}
.scores i{font-style:normal;background:var(--card);border:1px solid var(--line);border-radius:99px;padding:4px 10px;font-size:12px;font-weight:800}
.prow{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #1c2430;font-size:13px;font-weight:700}
.prow img{width:28px;height:28px;border-radius:50%}
@media(max-width:800px){.models{grid-template-columns:repeat(2,1fr)}.hero h1{font-size:28px}}
</style>
</head>
<body>
__SITE_NAV__
<div class="wrap">
  <div class="hero">
    <div class="note" id="when">—</div>
    <h1 id="ttl">YÜKLENİYOR</h1>
    <div class="vs" id="vs"></div>
    <div class="pick" id="pick"></div>
    <div class="note" id="note">Pazarlar hesaplanıyor…</div>
  </div>
  <div class="g">MODELLER</div>
  <div class="models" id="models"></div>
  <div class="g">VALUE · KELLY</div>
  <div class="grid" id="value"></div>
  <div class="g">ÖNEMLİ UYARILAR</div>
  <div class="warn" id="warn"></div>
  <div id="mk"></div>
</div>
<script>
window.BAHIS_MID = __MID__;
window.BAHIS_API = __API__;
</script>
<script src="__JS__"></script>
</body>
</html>
"""
