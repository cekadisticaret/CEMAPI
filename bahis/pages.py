"""BAHİS — Green Betting tahta. POLY/KRİPTO şeridi yok."""

BAHIS_HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Green Betting</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%2300ff88'/></svg>">
<style>
:root{
  --bg:#101318; --card:#171c22; --card2:#1c2229; --line:#2a3038;
  --txt:#fff; --muted:#8b9590; --g:#00ff88; --g2:#00df81;
  --ink:#08140c; --pur:#7c5cff; --pur2:#5a3fd6;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--txt);font-family:Manrope,system-ui,sans-serif}
body{display:flex;overflow:hidden}
.rail{
  width:68px;background:#0c0f13;border-right:1px solid var(--line);
  display:flex;flex-direction:column;align-items:center;gap:8px;
  padding:16px 0;flex-shrink:0;z-index:30;
}
.logo-dot{
  width:40px;height:40px;border-radius:12px;background:var(--g);color:var(--ink);
  font-weight:800;display:grid;place-items:center;box-shadow:0 0 20px rgba(0,255,136,.4);margin-bottom:6px;
}
.ric{
  width:42px;height:42px;border:0;border-radius:12px;background:transparent;color:#5d6662;cursor:pointer;
  display:grid;place-items:center;
}
.ric.on{background:var(--g);color:var(--ink);box-shadow:0 0 14px rgba(0,255,136,.3)}
.ric svg{width:19px;height:19px}
.stage{flex:1;min-width:0;display:flex;flex-direction:column;height:100vh}
.top{
  height:60px;display:flex;align-items:center;gap:14px;padding:0 20px;
  background:rgba(12,15,19,.94);border-bottom:1px solid var(--line);
  flex-shrink:0;z-index:20;
}
.word{font-weight:800;letter-spacing:.08em;font-size:13px;white-space:nowrap}
.word i{font-style:normal;color:var(--g)}
.tabs{display:flex;background:#15191e;border-radius:999px;padding:3px}
.tab{border:0;background:transparent;color:#6e7773;font:800 10px/1 Manrope,sans-serif;letter-spacing:.08em;padding:8px 12px;border-radius:999px;cursor:pointer;text-decoration:none}
a.tab{display:inline-flex;align-items:center}
.tab.on{background:var(--g);color:var(--ink)}
.search{
  flex:1;max-width:280px;height:36px;border-radius:999px;border:1px solid var(--line);
  background:#15191e;color:#fff;padding:0 14px;font:600 12px Manrope,sans-serif;
}
.search::placeholder{color:#6e7773}
.clock{font-size:11px;font-weight:700;color:var(--muted);white-space:nowrap}
.home{font:800 11px Manrope,sans-serif;color:var(--ink);background:var(--g);text-decoration:none;padding:7px 12px;border-radius:999px}
.board{
  flex:1;min-height:0;display:grid;
  grid-template-columns:240px minmax(0,1fr) 280px;
  gap:12px;padding:12px 14px 14px;
}
.col{min-height:0;overflow:auto;display:flex;flex-direction:column;gap:10px}
.box{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px}
.sec{font-size:10px;font-weight:800;letter-spacing:.12em;color:var(--muted);margin-bottom:8px}
.live-mini{display:flex;align-items:center;gap:8px;padding:10px;border-radius:14px;background:#14191e;border:1px solid #2a3a32;cursor:pointer}
.live-mini .lp{background:var(--g);color:var(--ink);font:800 9px Manrope,sans-serif;letter-spacing:.1em;padding:3px 7px;border-radius:999px}
.live-mini b{font-size:13px}
.wrow{
  display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid #242a2e;
  cursor:pointer;font-size:12px;font-weight:700;
}
.wrow:hover{color:var(--g)}
.wrow .od{margin-left:auto;color:var(--g);font-variant-numeric:tabular-nums}
.crest,.crest.fb{
  width:28px;height:28px;border-radius:50%;object-fit:contain;background:#fff;border:2px solid #2a3036;flex-shrink:0;
}
.crest.fb{display:grid;place-items:center;font-size:8px;font-weight:800;color:#fff}
.lgbar,.mbar,.tbar{display:flex;gap:6px;flex-wrap:wrap}
.chip{
  border:1px solid var(--line);background:#15191e;color:#c5cdc8;border-radius:999px;
  padding:6px 10px;font:800 10px/1 Manrope,sans-serif;letter-spacing:.05em;cursor:pointer
}
.chip.on{background:var(--g);color:var(--ink);border-color:var(--g)}
.chip.pur.on{background:var(--pur);border-color:var(--pur);color:#fff}
.gridm{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.card{
  background:var(--card2);border:1px solid var(--line);border-radius:16px;padding:12px 12px 10px;
  cursor:pointer;position:relative;
}
.card:hover{border-color:#3a4540}
.card .when{font-size:10px;color:var(--muted);font-weight:700;margin-bottom:8px}
.card .vs{display:grid;grid-template-columns:1fr auto 1fr;gap:6px;align-items:center;margin-bottom:10px}
.card .side{text-align:center}
.card .nm{font-weight:800;font-size:12px;margin-top:4px}
.card .score{font-size:20px;font-weight:800;letter-spacing:1px}
.odds{display:grid;gap:6px}
.odds.n3{grid-template-columns:1fr 1fr 1fr}
.odds.n2{grid-template-columns:1fr 1fr}
.ob{
  background:#101417;border:1.5px solid #2a3036;border-radius:10px;padding:7px 4px;
  text-align:center;cursor:pointer;color:#fff;font:inherit;
}
.ob:hover,.ob.on{border-color:var(--g);background:rgba(0,255,136,.1)}
.ob s{display:block;text-decoration:none;color:var(--muted);font-size:9px;font-weight:700}
.ob b{display:block;margin-top:2px;font-size:14px}
.tip{
  margin:0 0 8px;padding:5px 8px;border-radius:8px;
  background:rgba(0,255,136,.1);border:1px solid rgba(0,255,136,.3);
  color:var(--g);font-size:10px;font-weight:800;text-align:center;
}
.src{position:absolute;top:8px;right:10px;font-size:9px;color:#6e7773;font-weight:700}
.kasa{background:linear-gradient(160deg,#1a2420,#171c22);border-color:#2a3a32}
.kasa .bal{font-size:26px;font-weight:800;letter-spacing:-.5px}
.kasa .sub{font-size:10px;color:var(--muted);margin-top:2px}
.slip-leg{padding:8px 0;border-bottom:1px solid #242a2e;font-size:12px}
.slip-leg b{color:var(--g)}
.pbet{
  display:block;text-align:center;text-decoration:none;width:100%;margin-top:10px;
  border:0;border-radius:999px;padding:12px;background:var(--g);color:var(--ink);
  font:800 12px Manrope,sans-serif;letter-spacing:.08em;cursor:pointer;
}
.pbet.ghost{background:#15191e;color:#9aa39e;border:1px solid var(--line)}
.note{font-size:10px;color:var(--muted);line-height:1.4}
.mk .g{font-size:10px;font-weight:800;letter-spacing:.08em;color:#6e7773;margin:10px 0 5px;text-transform:uppercase}
.mk .chip2{display:flex;justify-content:space-between;gap:8px;font-size:11px;font-weight:700;padding:3px 0;border-bottom:1px solid #1e2428}
.mk .chip2 b{color:var(--g);font-variant-numeric:tabular-nums}
.ov{position:fixed;inset:0;background:rgba(0,0,0,.62);z-index:50;display:none;align-items:center;justify-content:center;padding:20px}
.ov.on{display:flex}
.ovc{width:min(780px,100%);max-height:92vh;overflow:auto;background:#161b1f;border:1px solid var(--line);border-radius:20px;padding:18px}
#pane-p,#pane-t{display:none;overflow:auto;padding:4px 2px 20px}
.ptabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.ptab{border:0;background:#15191e;color:#6e7773;font:800 10px/1 Manrope,sans-serif;letter-spacing:.08em;padding:8px 12px;border-radius:999px;cursor:pointer;text-decoration:none}
.ptab.on{background:var(--g);color:var(--ink)}
.tnote{color:var(--muted);font-size:12px;margin:0 0 10px}
.tgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.tcard{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px;cursor:pointer}
.tcard .when{font-size:11px;color:var(--muted);font-weight:700;margin-bottom:8px}
.tcard .vs{display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:center;margin-bottom:10px;text-align:center}
.tcard .nm{font-weight:800;font-size:12px;margin-top:4px}
.tpick{margin:0 0 10px;padding:7px 8px;border-radius:10px;text-align:center;background:rgba(0,255,136,.1);border:1px solid rgba(0,255,136,.3);color:var(--g);font-weight:800;font-size:12px}
.tpick small{display:block;color:#8b9590;font-size:10px;margin-top:3px}
.tmk{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px}
.tmk .box{background:#101417;border:1px solid #2a3036;border-radius:10px;padding:7px 8px}
.tmk .box s{display:block;text-decoration:none;color:var(--muted);font-size:10px;font-weight:700}
.tsc{display:flex;flex-wrap:wrap;gap:5px}
.tsc i{font-style:normal;background:#101417;border:1px solid #2a3036;border-radius:999px;padding:3px 7px;font-size:10px;font-weight:800}
.tsc i em{font-style:normal;color:var(--g);margin-left:3px}
.vbadge{display:inline-block;margin-left:6px;background:var(--g);color:var(--ink);font-size:9px;font-weight:800;padding:2px 6px;border-radius:999px}
.erow{display:grid;grid-template-columns:90px 50px 54px 64px 1fr;gap:6px;align-items:center;padding:6px 0;border-bottom:1px solid #242a2e;font-size:11px;font-weight:700}
.erow .ok{color:var(--g)} .erow .no{color:#8b9590}
.pbar{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
.pbar select,.pbar input{background:#15191e;border:1px solid var(--line);color:#fff;border-radius:10px;padding:7px 9px;font:700 12px Manrope,sans-serif}
.pchip{border:1px solid var(--line);background:#15191e;color:#9aa39e;border-radius:999px;padding:5px 9px;font:800 10px Manrope,sans-serif;cursor:pointer}
.pchip.on{border-color:var(--g);color:var(--ink);background:var(--g)}
.plead{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:12px}
.pcard{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px}
.pcard .h{font-size:10px;letter-spacing:.1em;color:var(--muted);font-weight:800;margin-bottom:6px}
.prow{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #242a2e;cursor:pointer;font-size:12px;font-weight:700}
.prow img,.pface{width:26px;height:26px;border-radius:50%;object-fit:cover;background:#222}
.pface{display:grid;place-items:center;font-size:9px;font-weight:800}
.pval{margin-left:auto;color:var(--g);font-weight:800}
.ptable{width:100%;border-collapse:collapse;font-size:12px}
.ptable th{text-align:left;font-size:10px;letter-spacing:.08em;color:var(--muted);padding:6px 4px;cursor:pointer}
.ptable td{padding:6px 4px;border-top:1px solid #242a2e}
.psquad{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:12px}
.tstr{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.tstr .chip{cursor:default}
.empty{color:var(--muted);font-size:12px;padding:16px 4px}
#pane-k{display:none;overflow:auto;padding:4px 2px 24px;flex:1;min-height:0}
.khead{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.klist{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.kslip{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px}
.kslip.won{border-color:#22c55e}
.kslip.lost{border-color:#ef4444}
.kslip.win{border-color:#22c55e;background:rgba(34,197,94,.08)}
.kslip.live{border-color:#f5c518}
.kslip .kh{display:flex;align-items:center;gap:8px;margin-bottom:8px;font-size:12px;font-weight:800}
.kslip .badge{margin-left:auto;border-radius:99px;padding:3px 8px;font-size:10px}
.kslip .badge.wait{background:#1a1608;color:#f5c518}
.kslip .badge.ok{background:#12351f;color:#22c55e}
.kslip .badge.no{background:#3a1218;color:#ef4444}
.kleg{display:grid;grid-template-columns:1fr 56px;gap:8px;align-items:center;padding:7px 0;border-bottom:1px solid #242a2e}
.kleg .nm{font-size:12px;font-weight:800}
.kleg .mk{font-size:10px;color:var(--muted);font-weight:700}
.kleg .od{text-align:center;background:var(--g);color:var(--ink);border-radius:10px;font-weight:800;padding:8px 4px}
.kfoot{display:flex;justify-content:space-between;margin-top:8px;font-size:11px;font-weight:700;color:var(--muted)}
.kfoot b{color:var(--g);font-size:16px}
@media(max-width:1180px){
  .board{grid-template-columns:1fr}
  .rail{display:none}
  .gridm,.tgrid,.plead,.psquad,.klist{grid-template-columns:1fr}
  .search{display:none}
}
</style>
</head>
<body data-world="bahis">
<aside class="rail">
  <div class="logo-dot">GB</div>
  <button class="ric on" type="button" data-go="k" title="Kuponlar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 4h12v16H6z"/><path d="M9 8h6M9 12h6M9 16h4"/></svg></button>
  <button class="ric" type="button" data-go="m" title="Maçlar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 3a15 15 0 010 18M12 3a15 15 0 000 18M3 12h18"/></svg></button>
  <button class="ric" type="button" data-go="res" title="Sonuçlar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6h16M4 12h10M4 18h16"/></svg></button>
  <button class="ric" type="button" data-go="cr" title="Korner"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 20V8a4 4 0 014-4h12"/><circle cx="8" cy="16" r="3"/></svg></button>
  <button class="ric" type="button" data-go="t" title="Motorlar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 19V5M4 19l7-7 4 4 5-6"/></svg></button>
  <button class="ric" type="button" data-go="p" title="Oyuncular"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="8" r="3"/><path d="M5 20c1.5-4 12.5-4 14 0"/></svg></button>
</aside>
<div class="stage">
  <header class="top">
    <div class="word">GREEN <i>BETTING</i></div>
    <div class="tabs">
      <button class="tab on" type="button" data-go="k">KUPONLAR</button>
      <button class="tab" type="button" data-go="m">MAÇLAR</button>
      <button class="tab" type="button" data-go="res">SONUÇLAR</button>
      <a class="tab" id="nav-site" href="__SITE_URL__" target="_top">SITE</a>
    </div>
    <input class="search" id="q" type="search" placeholder="Takım ara…">
    <div class="clock" id="clock"></div>
    <a class="home" href="__HOME_URL__" target="_top">CemAPI</a>
  </header>

  <div class="board" id="pane-m" style="display:none">
    <aside class="col">
      <div class="box" id="feat"></div>
      <div class="box">
        <div class="sec">SIRADAKİ · 1X2</div>
        <div id="winners"></div>
      </div>
      <div class="box">
        <div class="sec">SON SONUÇLAR</div>
        <div id="latest"></div>
      </div>
    </aside>

    <main class="col">
      <div class="lgbar" id="lgbar"></div>
      <div class="mbar" id="mbar">
        <button class="chip on" type="button" data-mk="1x2">1X2</button>
        <button class="chip" type="button" data-mk="ou">2.5</button>
        <button class="chip" type="button" data-mk="kg">KG</button>
        <button class="chip" type="button" data-mk="dc">ÇİFTE</button>
        <button class="chip" type="button" data-mk="ah">H-1</button>
        <button class="chip" type="button" data-mk="cr">KORNER</button>
      </div>
      <div class="tbar" id="whenbar">
        <button class="chip pur on" type="button" data-when="next">YAKIN</button>
        <button class="chip pur" type="button" data-when="today">BUGÜN</button>
        <button class="chip pur" type="button" data-when="played">SONUÇLAR</button>
      </div>
      <div class="gridm" id="gridm"></div>
    </main>

    <aside class="col">
      <div class="box kasa" id="kasa">
        <div class="sec">SANAL KASA</div>
        <div class="note">yükleniyor…</div>
      </div>
      <div class="box" id="slipbox">
        <div class="sec">KUPON · KÂĞIT</div>
        <div id="slip"><div class="note">Orana tıkla · emir yok</div></div>
        <div class="note" id="slip-tot"></div>
        <button class="pbet ghost" type="button" id="slip-clear">TEMİZLE</button>
      </div>
      <div class="box">
        <div class="sec">SİSTEM KUPONU</div>
        <div id="opens"></div>
        <button class="pbet" type="button" data-go="k">KUPONLARI AÇ</button>
      </div>
    </aside>
  </div>

  <div id="pane-k" style="display:block">
    <div class="khead">
      <div class="word">KUPONLAR</div>
      <button class="chip on" type="button" data-ktab="open">AÇIK</button>
      <button class="chip" type="button" data-ktab="done">BİTMİŞ</button>
      <span class="note" id="kmeta">sistemin ürettiği kâğıt kupon · emir yok</span>
    </div>
    <div class="klist" id="klist"><div class="empty">yükleniyor…</div></div>
  </div>

  <div id="pane-p">
    <div class="pbar">
      <select id="psea"></select>
      <input id="pq" type="search" placeholder="oyuncu / takım">
      <button class="pchip on" type="button" data-stat="goals">GOL</button>
      <button class="pchip" type="button" data-stat="assists">ASİST</button>
      <button class="pchip" type="button" data-stat="ga">G+A</button>
      <button class="pchip" type="button" data-stat="xg">xG</button>
      <button class="pchip" type="button" data-stat="rating">PUAN</button>
      <button class="pchip" type="button" data-stat="yellow">SARI</button>
      <button class="pchip" type="button" data-stat="minutes">DK</button>
    </div>
    <div class="plead" id="plead"></div>
    <div class="box" style="overflow:auto">
      <div class="sec" id="pttl">OYUNCU TABLOSU</div>
      <table class="ptable" id="ptable"></table>
    </div>
    <div class="psquad" id="psquad"></div>
  </div>

  <div id="pane-t">
    <div class="ptabs" id="ptabs"></div>
    <p class="tnote" id="tmeta">Motor</p>
    <div class="tstr" id="tstr"></div>
    <div class="tgrid" id="tgrid"></div>
  </div>
</div>
<div class="ov" id="ov" onclick="if(event.target===this)this.className='ov'"></div>
<script type="application/json" id="engines-json">__ENGINES__</script>
<script>
const $ = id => document.getElementById(id);
const ENGINES = (()=>{ try{ return JSON.parse(($('engines-json').textContent||'[]').trim()); }catch(e){ return []; } })();
let SUM=null, TEAM='', PLAY=null, PSTAT='goals', PSEA='', PRED=null;
let ENGINE=(ENGINES[0]&&ENGINES[0].id)||'';
let LEAGUE = new URLSearchParams(location.search).get('league') || 'tr';
let MARKET='1x2', WHEN='next', ROWS=[], CORNER={}, SLIP=[];
let Q='', KTAB='open';

function withLg(url){
  const join = url.includes('?') ? '&' : '?';
  return url + join + 'league=' + encodeURIComponent(LEAGUE);
}
function esc(s){return String(s||'').replace(/[&<>"]/g,c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));}
function crest(t, cls){
  if(t&&t.crest) return `<img class="${cls||'crest'}" src="${esc(t.crest)}" alt="">`;
  return `<div class="crest fb" style="background:${t&&t.color||'#333'}">${esc((t&&t.short)||'?')}</div>`;
}
function fmt(v){ return v==null||v===''?'—':Number(v).toFixed(2); }
function pct(p){ return Math.round(Number(p||0)*100); }
function srcLab(s){ return s==='pinnacle'?'Pinnacle':(s==='fd'?'FD':'oran yok'); }

function tick(){
  const d=new Date();
  const z=d.toLocaleTimeString('tr-TR',{hour:'2-digit',minute:'2-digit',timeZone:'Europe/Istanbul'});
  if($('clock')) $('clock').textContent = z+' TR';
}
tick(); setInterval(tick, 15000);

function paintLeagues(list){
  $('lgbar').innerHTML = (list||[]).map(x=>
    `<button class="chip${x.id===LEAGUE?' on':''}" type="button" data-id="${esc(x.id)}">${esc(x.flag)} ${esc(x.short)}</button>`
  ).join('');
}

function picks(m){
  const o=m.odds||{}, cr=CORNER[m.id]||{};
  if(MARKET==='ou'){
    const u=o.ou25||{};
    return [{k:'U25',s:'Alt 2.5',v:u.under},{k:'O25',s:'Üst 2.5',v:u.over}];
  }
  if(MARKET==='kg'){
    const b=o.btts||{};
    return [{k:'YY',s:'KG Var',v:b.yes},{k:'YN',s:'KG Yok',v:b.no}];
  }
  if(MARKET==='dc'){
    const d=o.dc||{};
    return [{k:'1X',s:'1X',v:d['1X']},{k:'12',s:'12',v:d['12']},{k:'X2',s:'X2',v:d.X2}];
  }
  if(MARKET==='ah'){
    const a=o.ah_m1||{};
    return [{k:'AH1',s:'Ev −1',v:a.home||a['1']},{k:'AHX',s:'X −1',v:a.draw||a.X},{k:'AH2',s:'Dep +1',v:a.away||a['2']}];
  }
  if(MARKET==='cr'){
    const book=cr.odds||{};
    const ou=(cr.overUnder||{})['9.5']||{};
    return [
      {k:'CU',s:'Korner A 9.5',v:book.under,p:ou.under},
      {k:'CO',s:'Korner Ü 9.5',v:book.over,p:ou.over}
    ];
  }
  return [{k:'H',s:'1',v:o.home},{k:'D',s:'X',v:o.draw},{k:'A',s:'2',v:o.away}];
}
function oddsHtml(m){
  const arr=picks(m);
  const n=arr.length===2?'n2':'n3';
  const tip=(m.tip&&m.tip.pick)||'';
  return `<div class="odds ${n}">${arr.map(x=>{
    const on=(MARKET==='1x2'&&((x.k==='H'&&tip==='H')||(x.k==='D'&&tip==='D')||(x.k==='A'&&tip==='A')))?' on':'';
    const extra=x.v==null&&x.p!=null?`%${pct(x.p)}`:fmt(x.v);
    return `<button class="ob${on}" type="button" data-id="${esc(m.id||'')}" data-k="${x.k}" data-s="${esc(x.s)}" data-v="${x.v==null?'':x.v}"><s>${esc(x.s)}</s><b>${extra}</b></button>`;
  }).join('')}</div>`;
}
function cardHtml(m){
  const played=!!m.played;
  const mid=played?`<div class="score">${m.hg} : ${m.ag}</div>`:`<div class="score">VS</div>`;
  const tip=(!played&&m.tip)?`<div class="tip">${esc(m.tip.text)} · %${m.tip.pct}</div>`:'';
  const cr=CORNER[m.id];
  const extra=(MARKET==='cr'&&cr&&cr.expectedCorners)?`<div class="note" style="margin:0 0 6px;text-align:center">λ ${cr.expectedCorners.total} korner</div>`:'';
  return `<article class="card" data-id="${esc(m.id||'')}">
    <span class="src">${esc(srcLab(m.odds_src))}</span>
    <div class="when">${esc(m.when||'')}${m.week?' · H'+m.week:''}</div>
    <div class="vs">
      <div class="side">${crest(m.home)}<div class="nm">${esc(m.home.short||m.home.name)}</div></div>
      ${mid}
      <div class="side">${crest(m.away)}<div class="nm">${esc(m.away.short||m.away.name)}</div></div>
    </div>
    ${tip}${extra}
    ${played?'':oddsHtml(m)}
  </article>`;
}
function filterRows(rows){
  const q=(Q||'').toLowerCase();
  return (rows||[]).filter(m=>{
    if(!q) return true;
    const hay=((m.home&&m.home.name)||'')+' '+((m.away&&m.away.name)||'')+' '+((m.home&&m.home.short)||'')+' '+((m.away&&m.away.short)||'');
    return hay.toLowerCase().includes(q);
  });
}
function paintGrid(){
  const rows=filterRows(ROWS);
  $('gridm').innerHTML = rows.slice(0,18).map(cardHtml).join('') || '<div class="empty">Maç yok</div>';
}
function paintFeat(m){
  const box=$('feat');
  if(!m){ box.innerHTML='<div class="sec">CANLI / SIRADAKİ</div><div class="note">Maç yok</div>'; return; }
  const sc=m.played?`${m.hg} - ${m.ag}`:'VS';
  box.innerHTML = `<div class="sec">${m.played?'SON MAÇ':'SIRADAKİ'}</div>
    <div class="live-mini" data-id="${esc(m.id||'')}">
      ${crest(m.home)}
      <div><div class="lp">${m.played?'MS':'YAKIN'}</div><b>${esc(m.home.short)} ${sc} ${esc(m.away.short)}</b>
      <div class="note">${esc(m.when||'')}</div></div>
    </div>`;
}
function paintWinners(rows){
  $('winners').innerHTML = (rows||[]).slice(0,8).map(m=>{
    const o=m.odds||{};
    const best=[['1',o.home],['X',o.draw],['2',o.away]].filter(x=>x[1]).sort((a,b)=>a[1]-b[1])[0];
    return `<div class="wrow" data-id="${esc(m.id||'')}"><div>${esc(m.home.short)} — ${esc(m.away.short)}</div>
      <span class="od">${best?best[0]+' '+fmt(best[1]):'—'}</span></div>`;
  }).join('') || '<div class="note">fikstür yok</div>';
}
function paintLatest(){
  $('latest').innerHTML = (SUM.latest||[]).map(m=>`
    <div class="wrow" data-id="${esc(m.id||'')}">${crest(m.home)}
      <div>${esc(m.home.short)} ${m.hg}–${m.ag} ${esc(m.away.short)}</div></div>`).join('') || '<div class="note">sonuç yok</div>';
}

function paintSlip(){
  if(!SLIP.length){ $('slip').innerHTML='<div class="note">Orana tıkla · emir yok</div>'; $('slip-tot').textContent=''; return; }
  let prod=1;
  $('slip').innerHTML = SLIP.map((x,i)=>{
    const o=Number(x.v)||1; prod*=o;
    return `<div class="slip-leg">${esc(x.h)} — ${esc(x.a)}<br><b>${esc(x.s)} ${fmt(x.v)}</b>
      <span class="note" style="cursor:pointer" onclick="dropSlip(${i})">sil</span></div>`;
  }).join('');
  $('slip-tot').textContent = SLIP.length+' ayak · birleşik '+prod.toFixed(2)+' · kâğıt';
}
function dropSlip(i){ SLIP.splice(i,1); paintSlip(); }
function addSlip(m, btn){
  const v=btn.dataset.v; if(!v) return;
  const id=btn.dataset.id;
  SLIP=SLIP.filter(x=>x.id!==id);
  SLIP.push({id,h:m.home.short,a:m.away.short,s:btn.dataset.s,v:Number(v),k:btn.dataset.k});
  paintSlip();
}

function paintKasa(d){
  const s=(d&&d.stats)||{};
  if($('kasa')) $('kasa').innerHTML = `<div class="sec">SANAL KASA</div>
    <div class="bal">${(s.balance??'—')} ₺</div>
    <div class="sub">nakit · açık ${s.open||0} kupon · kilitli ${s.locked||0}</div>
    <div class="note" style="margin-top:8px">özkaynak ${s.equity??'—'} · PnL ${s.pnl??0} · ROI ${s.roi==null?'—':s.roi+'%'}</div>`;
}
function paintOpens(d){
  const c=((d&&d.coupons)||[])[0];
  if(!$('opens')) return;
  if(!c){ $('opens').innerHTML='<div class="note">açık kupon yok</div>'; return; }
  $('opens').innerHTML = (c.legs||[]).map(l=>`
    <div class="slip-leg">${esc(l.home_short||l.home)} — ${esc(l.away_short||l.away)}<br>
    <b>${esc(l.label||l.sel)} ${Number(l.odds||0).toFixed(2)}</b></div>`).join('')
    + `<div class="note" style="margin-top:6px">${esc(c.league_short||c.league||'')} · ${ (c.legs||[]).length} ayak · ${Number(c.odds_product||0).toFixed(2)}</div>`;
}
function paintBook(d){
  const st=(d&&d.stats)||{};
  if($('kmeta')) $('kmeta').textContent = `açık ${st.open||0} · kasa ${(st.balance??'—')} ₺ · Pinnacle · emir yok`;
  const rows=(d&&d.coupons)||[];
  if(!$('klist')) return;
  $('klist').innerHTML = rows.map(c=>{
    const stt=c.tone||c.status||'open';
    const badge=stt==='won'?'<span class="badge ok">KAZANDI</span>':stt==='lost'?'<span class="badge no">KAYBETTİ</span>':stt==='win'?'<span class="badge ok">TUTUYOR</span>':stt==='live'?'<span class="badge wait">CANLI</span>':'<span class="badge wait">AÇIK</span>';
    const legs=(c.legs||[]).map(l=>{
      const sc=(l.hg!=null&&l.ag!=null)?` ${l.hg}–${l.ag}`:'';
      const when=l.live?(l.minute||'CANLI'):(l.when_tr||l.when||'');
      return `<div class="kleg">
      <div><div class="nm">${esc(l.home)} — ${esc(l.away)}${sc?` · ${esc(sc.trim())}`:''}</div>
      <div class="mk">${esc(l.market_label||'')} · ${esc(l.label||l.sel)} · ${esc(when)}</div></div>
      <div class="od">${Number(l.odds||0).toFixed(2)}</div></div>`;
    }).join('');
    return `<article class="kslip ${esc(stt)}">
      <div class="kh">${esc(c.league_short||c.league||'')} · ${esc(c.day||'')}${badge}</div>
      ${legs}
      <div class="kfoot"><span>${c.stake||200} ₺ yatırım</span><b>${Number(c.odds_product||0).toFixed(2)}</b></div>
    </article>`;
  }).join('') || `<div class="empty">${KTAB==='done'?'Bitmiş kupon yok.':'Açık kupon yok.'}</div>`;
}

async function loadCoupons(){
  try{
    const d=await (await fetch('/site/api/coupons?tab=open&league=all&limit=20',{cache:'no-store'})).json();
    paintKasa(d);
    paintOpens(d);
  }catch(e){ if($('kasa')) $('kasa').innerHTML='<div class="sec">SANAL KASA</div><div class="note">yüklenemedi</div>'; }
}
async function loadBook(){
  try{
    const d=await (await fetch('/site/api/coupons?tab='+encodeURIComponent(KTAB)+'&league=all&limit=40',{cache:'no-store'})).json();
    paintBook(d);
    paintKasa(d);
    if(KTAB==='open') paintOpens(d);
  }catch(e){ if($('klist')) $('klist').innerHTML='<div class="empty">kupon yüklenemedi</div>'; }
}

async function loadCorners(){
  try{
    const d=await (await fetch(withLg('/bahis/api/preds?engine=corners&limit=24'),{cache:'no-store'})).json();
    CORNER={};
    (d.preds||[]).forEach(m=>{ if(m.id) CORNER[m.id]=m; });
  }catch(e){ CORNER={}; }
}

async function loadRows(){
  if(WHEN==='played'){
    ROWS = await (await fetch(withLg('/bahis/api/matches?status=played&limit=30'),{cache:'no-store'})).json();
  } else if(WHEN==='today'){
    ROWS = (SUM&&SUM.today)||[];
  } else {
    ROWS = await (await fetch(withLg('/bahis/api/matches?status=upcoming&limit=18'),{cache:'no-store'})).json();
  }
  if(MARKET==='cr') await loadCorners();
  paintGrid();
}

async function loadSum(){
  SUM = await (await fetch(withLg('/bahis/api/summary'),{cache:'no-store'})).json();
  paintLeagues(SUM.leagues||[]);
  const feat=(SUM.today&&SUM.today[0])||(SUM.next&&SUM.next[0]);
  paintFeat(feat);
  paintWinners(SUM.next||[]);
  paintLatest();
  await loadRows();
}

function showPane(which){
  const map={k:'k',p:'p',t:'t'};
  const pane=map[which]||'m';
  $('pane-m').style.display = pane==='m'?'grid':'none';
  $('pane-k').style.display = pane==='k'?'block':'none';
  $('pane-p').style.display = pane==='p'?'block':'none';
  $('pane-t').style.display = pane==='t'?'block':'none';
  document.querySelectorAll('.ric').forEach(x=>x.classList.toggle('on', x.dataset.go===which));
  document.querySelectorAll('.top .tab[data-go]').forEach(x=>{
    const tab = which==='res' ? 'res' : (which==='k'?'k':'m');
    x.classList.toggle('on', x.dataset.go===tab);
  });
  if(which==='k') loadBook();
  if(which==='live'){ WHEN='today'; syncWhen(); if(!SUM) loadSum(); else loadRows(); }
  if(which==='res'){ WHEN='played'; syncWhen(); if(!SUM) loadSum(); else loadRows(); }
  if(which==='m' || which==='cr'){
    WHEN='next';
    if(which==='cr') MARKET='cr';
    syncMk(); syncWhen();
    if(!SUM) loadSum(); else loadRows();
  }
  if(which==='p'){ if(!PLAY) loadPlaySum(); else loadPlayers(); }
  if(which==='t') loadPreds();
}
function syncMk(){ document.querySelectorAll('#mbar .chip').forEach(x=>x.classList.toggle('on', x.dataset.mk===MARKET)); }
function syncWhen(){ document.querySelectorAll('#whenbar .chip').forEach(x=>x.classList.toggle('on', x.dataset.when===WHEN)); }

function mkPct(p){ return Math.round(Number(p||0)*100); }
function mkChip(k,v){ return `<div class="chip2"><span>${esc(k)}</span><b>%${v}</b></div>`; }
function paintMarkets(d){
  const ov=$('ov');
  if(!d||!d.ok){ ov.innerHTML='<div class="ovc"><div class="note">Pazar yok</div></div>'; return; }
  const m=d.match||{}, mk=d.markets||{};
  const h=(m.home&&m.home.short)||'EV', a=(m.away&&m.away.short)||'DEP';
  const ou=mk.ou||{}, dc=mk.doubleChance||{}, o=m.odds||{};
  const cb=mk.cornersBucket||{}, co=mk.cornerOu||{};
  const scores=(mk.correctScore||[]).slice(0,8).map(s=>`${s.score} %${s.pct}`).join(' · ');
  ov.className='ov on';
  ov.innerHTML=`<div class="ovc mk">
    <div class="sec">MAÇ · ${esc(srcLab(d.odds_src||m.odds_src))}</div>
    <b style="font-size:18px">${esc(m.home&&m.home.name||'')} — ${esc(m.away&&m.away.name||'')}</b>
    <div class="note" style="margin:4px 0 10px">${esc(m.when||'')}</div>
    <div class="odds n3" style="margin-bottom:10px">
      <div class="ob"><s>1</s><b>${fmt(o.home)}</b></div>
      <div class="ob"><s>X</s><b>${fmt(o.draw)}</b></div>
      <div class="ob"><s>2</s><b>${fmt(o.away)}</b></div>
    </div>
    <div class="g">Model · 1X2</div>
    ${mkChip('1 '+h, mkPct((mk.result||{})['1']))}${mkChip('X', mkPct((mk.result||{}).X))}${mkChip('2 '+a, mkPct((mk.result||{})['2']))}
    <div class="g">Çifte · KG · 2.5</div>
    ${mkChip('1X', mkPct(dc['1X']))}${mkChip('12', mkPct(dc['12']))}${mkChip('X2', mkPct(dc.X2))}
    ${mkChip('KG var', mkPct((mk.btts||{}).yes))}${mkChip('KG yok', mkPct((mk.btts||{}).no))}
    ${['1.5','2.5','3.5'].map(l=>mkChip(l+' A/Ü', mkPct((ou[l]||{}).under)+' / %'+mkPct((ou[l]||{}).over))).join('')}
    <div class="g">Korner</div>
    ${mkChip('0–8', mkPct(cb.le8))}${mkChip('9–11', mkPct(cb['9_11']))}${mkChip('12+', mkPct(cb.ge12))}
    ${Object.entries(co).map(([l,v])=>mkChip(l+' A/Ü', mkPct(v.under)+' / %'+mkPct(v.over))).join('')}
    <div class="g">Doğru skor</div>
    <div class="note">${esc(scores)||'—'}</div>
    <a class="pbet" href="/site/mac/${encodeURIComponent(m.id||'')}">TAM DETAY</a>
    <button class="pbet ghost" type="button" onclick="document.getElementById('ov').className='ov'">KAPAT</button>
  </div>`;
}
async function openMatch(id){
  if(!id) return;
  $('ov').className='ov on';
  $('ov').innerHTML='<div class="ovc"><div class="note">Pazarlar…</div></div>';
  try{
    const d=await (await fetch(withLg('/bahis/api/match?id='+encodeURIComponent(id)),{cache:'no-store'})).json();
    paintMarkets(d);
  }catch(e){ $('ov').innerHTML='<div class="ovc"><div class="note">yüklenemedi</div></div>'; }
}

function face(p){
  const letter=esc((p.name||'?')[0]);
  if(!p.photo) return `<div class="pface">${letter}</div>`;
  return `<img src="${esc(p.photo)}" alt="">`;
}
function paintLeaders(leaders){
  const keys=[['goals','GOL'],['assists','ASİST'],['xg','xG'],['rating','PUAN']];
  $('plead').innerHTML = keys.map(([k,h])=>{
    const rows=(leaders&&leaders[k])||[];
    return `<div class="pcard"><div class="h">${h}</div>${rows.slice(0,6).map((p,i)=>`
      <div class="prow" onclick="openPlayer(${p.id})"><span style="width:14px;color:#6e7773">${i+1}</span>${face(p)}
        <div>${esc(p.name)}<div class="note">${esc(p.team_short||'')}</div></div>
        <div class="pval">${p.value??'—'}</div></div>`).join('')||'<div class="note">veri yok</div>'}</div>`;
  }).join('');
}
function paintPTable(rows, sort){
  const cols=[['name','Oyuncu'],['team_short','Takım'],['matches','M'],['goals','G'],['assists','A'],['xg','xG'],['rating','Puan']];
  const th=cols.map(([k,l])=>`<th data-s="${k}">${l}</th>`).join('');
  const st=p=>p.stats||{};
  const cell=(p,k)=>{
    if(k==='name') return `<td style="display:flex;align-items:center;gap:8px">${face(p)}${esc(p.name)}</td>`;
    if(k==='team_short') return `<td>${esc(p.team_short||'')}</td>`;
    if(k==='matches') return `<td>${p[k]??'—'}</td>`;
    return `<td>${st(p)[k]==null?'—':st(p)[k]}</td>`;
  };
  $('ptable').innerHTML=`<thead><tr>${th}</tr></thead><tbody>${(rows||[]).map(p=>`
    <tr onclick="openPlayer(${p.id})">${cols.map(([k])=>cell(p,k)).join('')}</tr>`).join('')}</tbody>`;
  $('ptable').querySelectorAll('th').forEach(th=>{ th.onclick=e=>{ e.stopPropagation(); loadPlayers(th.dataset.s); }; });
}
async function loadPlayers(sort){
  if(sort && !['name','team_short'].includes(sort)) PSTAT=sort;
  document.querySelectorAll('#pane-p .pchip').forEach(x=>x.classList.toggle('on', x.dataset.stat===PSTAT));
  const qs=new URLSearchParams({sort:PSTAT, limit:'80'});
  if(PSEA) qs.set('season', PSEA);
  if(TEAM) qs.set('team', TEAM);
  const q=($('pq').value||'').trim(); if(q) qs.set('q', q);
  const [d,sum]=await Promise.all([
    (await fetch(withLg('/bahis/api/players?'+qs),{cache:'no-store'})).json(),
    (await fetch(withLg('/bahis/api/players?kind=summary'+(PSEA?'&season='+encodeURIComponent(PSEA):'')),{cache:'no-store'})).json(),
  ]);
  if(sum&&sum.ok) paintLeaders(sum.leaders);
  $('pttl').textContent=`${(d.season&&d.season.label)||''} · ${d.count||0} · ${PSTAT}`;
  paintPTable(d.players||[], PSTAT);
}
async function loadPlaySum(){
  PLAY=await (await fetch(withLg('/bahis/api/players?kind=summary'),{cache:'no-store'})).json();
  if(!PLAY||!PLAY.ok) return;
  PSEA=(PLAY.season&&PLAY.season.id)||'';
  $('psea').innerHTML=(PLAY.seasons||[]).map(s=>`<option value="${s.id}">${esc(s.label)}</option>`).join('');
  $('psea').value=PSEA;
  paintLeaders(PLAY.leaders);
  loadPlayers(PSTAT);
}
async function openPlayer(id){
  const d=await (await fetch(withLg('/bahis/api/players?id='+id),{cache:'no-store'})).json();
  if(!d.ok) return;
  const c=d.career||{};
  $('ov').className='ov on';
  $('ov').innerHTML=`<div class="ovc">
    <b style="font-size:20px">${esc(d.name)}</b>
    <div class="odds n3" style="margin:10px 0">
      <div class="ob"><s>Maç</s><b>${c.matches||0}</b></div>
      <div class="ob"><s>Gol</s><b>${c.goals||0}</b></div>
      <div class="ob"><s>Asist</s><b>${c.assists||0}</b></div>
    </div>
    ${(d.seasons||[]).map(s=>`<div class="wrow"><div>${esc(s.label)} · ${esc(s.team_short||'')}</div>
      <span class="od">${(s.stats&&s.stats.goals)||0}G</span></div>`).join('')}
    <button class="pbet" type="button" onclick="document.getElementById('ov').className='ov'">KAPAT</button>
  </div>`;
}

function vsHead(m, left, right){
  return `<div class="when">${esc(m.when||'')}${m.week?' · H'+m.week:''}</div>
    <div class="vs">
      <div>${crest(m.home)}<div class="nm">${esc(m.home.name)}</div><div class="note">${left||''}</div></div>
      <div class="score">VS</div>
      <div>${crest(m.away)}<div class="nm">${esc(m.away.name)}</div><div class="note">${right||''}</div></div>
    </div>`;
}
function bars(m){
  const r=m.matchResult||{};
  return `<div class="odds n3">
    <div class="ob${m.pick==='1'?' on':''}"><s>1</s><b>%${pct(r['1'])}</b></div>
    <div class="ob${m.pick==='X'?' on':''}"><s>X</s><b>%${pct(r.X)}</b></div>
    <div class="ob${m.pick==='2'?' on':''}"><s>2</s><b>%${pct(r['2'])}</b></div>
  </div>`;
}
function paintDixonCard(m, label){
  const ou=(m.overUnder&&m.overUnder['2.5'])||{};
  const scores=(m.correctScoreTop5||[]).slice(0,5).map(s=>`<i>${esc(s.score)}<em>%${s.pct}</em></i>`).join('');
  return `<div class="tcard" data-id="${esc(m.id||'')}">${vsHead(m, m.xg?('xG '+m.xg.home):'', m.xg?('xG '+m.xg.away):'')}
    <div class="tpick">${esc(m.text)} · %${m.pct}<small>${esc(label)}</small></div>${bars(m)}
    <div class="tmk">
      <div class="box"><s>2.5 A/Ü</s><b>%${pct(ou.under)} / %${pct(ou.over)}</b></div>
      <div class="box"><s>KG</s><b>%${pct(m.bttsYes)} / %${pct(m.bttsNo)}</b></div>
    </div><div class="tsc">${scores}</div></div>`;
}
function paintEloCard(m){
  const e=m.elo||{};
  return `<div class="tcard" data-id="${esc(m.id||'')}">${vsHead(m,'','')}
    <div class="tpick">${esc(m.text)} · %${m.pct}<small>ELO ${e.home??'—'} / ${e.away??'—'}</small></div>${bars(m)}</div>`;
}
function paintBankCard(m){
  const ok=m.stake&&m.stake.should_bet;
  const rows=(m.evals||[]).map(e=>`<div class="erow"><div>${esc(e.label||e.selection)}</div>
    <div>${e.odds==null?'—':Number(e.odds).toFixed(2)}</div><div>%${pct(e.model_prob)}</div>
    <div class="${e.edge>=0.04?'ok':'no'}">${e.edge>=0?'+':''}${(e.edge*100).toFixed(1)}p</div>
    <div class="${e.should_bet?'ok':'no'}">${e.should_bet?('AL '+e.stake):('PAS')}</div></div>`).join('');
  return `<div class="tcard" data-id="${esc(m.id||'')}">${vsHead(m,'','')}
    <div class="tpick">${esc(m.text)}${ok?'<span class="vbadge">AL</span>':''}</div>${rows||'<div class="note">oran yok</div>'}</div>`;
}
function paintCouponHead(c){
  if(!c) return '<div class="tcard"><div class="tpick">Kupon yok<small>emir yok</small></div></div>';
  const legs=(c.legs||[]).map(l=>`<div class="erow"><div>${esc(l.label)}</div><div>${Number(l.odds).toFixed(2)}</div>
    <div>%${pct(l.model_p)}</div><div class="ok">+${((l.edge_fair||0)*100).toFixed(1)}p</div>
    <div>${esc(l.home)} — ${esc(l.away)}</div></div>`).join('');
  return `<div class="tcard"><div class="tpick">birleşik ${c.odds_product} · %${pct(c.p_joint)}
    ${c.should?`<span class="vbadge">${c.stake}</span>`:''}</div>${legs}</div>`;
}
function paintCornerCard(m){
  const ou=(m.overUnder||{})['9.5']||{};
  const x=m.expectedCorners||{};
  return `<div class="tcard" data-id="${esc(m.id||'')}">${vsHead(m,'λ '+ (x.home||''),'λ '+(x.away||''))}
    <div class="tpick">${esc(m.pick)} · %${m.pct}<small>toplam ${x.total||'—'} korner</small></div>
    <div class="tmk"><div class="box"><s>9.5 A/Ü</s><b>%${pct(ou.under)} / %${pct(ou.over)}</b></div>
    <div class="box"><s>kota</s><b>${m.odds&&m.odds.over?fmt(m.odds.over)+' / '+fmt(m.odds.under):'yok'}</b></div></div></div>`;
}
function paintBackCard(m){
  const s=m.stats||{};
  return `<div class="tcard"><div class="when">walk-forward</div>
    <div class="tpick">${esc(m.text)}</div>
    <div class="tmk"><div class="box"><s>Brier</s><b>${s.brier??'—'}</b></div>
    <div class="box"><s>ROI</s><b>${s.value_roi==null?'—':s.value_roi}</b></div></div></div>`;
}
function paintPreds(d){
  PRED=d;
  if(!d||!d.ok){ $('tmeta').textContent='Tahmin yok'; $('tgrid').innerHTML=''; return; }
  const name=d.label||d.model||'Tahmin';
  const kind=d.engine||d.model||'';
  $('tmeta').textContent=`${name} · ${d.note||''} · ${d.n||0}`;
  if(kind==='coupon'){
    const cl=d.clv||{};
    $('tstr').innerHTML=`<span class="chip">${(d.coupon&&d.coupon.n)||0} ayak</span><span class="chip">${d.candidates_n||0} value</span>`+(cl.n?`<span class="chip">CLV ${cl.beat_pct}%</span>`:'');
  } else if(kind==='bankroll'&&d.bankroll){
    const b=d.bankroll;
    $('tstr').innerHTML=`<span class="chip">kasa ${b.current_bankroll}</span><span class="chip">${d.taken_n||0} AL</span>`;
  } else {
    $('tstr').innerHTML=(d.strengths||[]).slice(0,10).map(t=>`<span class="chip">${esc(t.short)} ${t.attack}</span>`).join('');
  }
  const paint = kind==='elo'?paintEloCard:kind==='backtest'?paintBackCard:kind==='corners'?paintCornerCard:(kind==='bankroll'||kind==='coupon')?paintBankCard:paintDixonCard;
  const head=kind==='coupon'?paintCouponHead(d.coupon):'';
  $('tgrid').innerHTML=head+((d.preds||[]).map(m=>paint(m,name)).join('')||(kind==='coupon'?'':'<div class="empty">Maç yok</div>'));
}
async function loadPreds(){
  if(!ENGINE){ $('tmeta').textContent='Motor yok'; return; }
  $('tmeta').textContent=ENGINE.toUpperCase()+'…';
  $('tgrid').innerHTML='';
  const d=await (await fetch(withLg('/bahis/api/preds?limit=24&engine='+encodeURIComponent(ENGINE)),{cache:'no-store'})).json();
  paintPreds(d);
}
(function mountEngines(){
  $('ptabs').innerHTML = ENGINES.map(e=>`<button class="ptab${e.id===ENGINE?' on':''}" type="button" data-engine="${esc(e.id)}">${esc(e.label)}</button>`).join('');
})();

document.addEventListener('click', e=>{
  const kt=e.target.closest('[data-ktab]');
  if(kt){
    KTAB=kt.dataset.ktab||'open';
    document.querySelectorAll('[data-ktab]').forEach(x=>x.classList.toggle('on', x===kt));
    loadBook();
    return;
  }
  const go=e.target.closest('[data-go]');
  if(go && !go.closest('#mbar,#whenbar,#lgbar')){ showPane(go.dataset.go); return; }
  const lg=e.target.closest('#lgbar .chip');
  if(lg){
    LEAGUE=lg.dataset.id||'tr'; TEAM=''; PLAY=null;
    const u=new URL(location.href); u.searchParams.set('league', LEAGUE); history.replaceState(null,'',u);
    loadSum(); loadCoupons();
    if($('pane-t').style.display==='block') loadPreds();
    return;
  }
  const mk=e.target.closest('#mbar .chip');
  if(mk){ MARKET=mk.dataset.mk; syncMk(); loadRows(); return; }
  const wh=e.target.closest('#whenbar .chip');
  if(wh){ WHEN=wh.dataset.when; syncWhen(); loadRows(); return; }
  const ob=e.target.closest('.ob[data-id]');
  if(ob){
    const m=ROWS.find(x=>x.id===ob.dataset.id)||(SUM.next||[]).find(x=>x.id===ob.dataset.id);
    if(m) addSlip(m, ob);
    e.stopPropagation();
    return;
  }
  const row=e.target.closest('[data-id]');
  if(row && (row.classList.contains('card')||row.classList.contains('wrow')||row.classList.contains('live-mini')||row.classList.contains('tcard'))){
    openMatch(row.dataset.id);
  }
});
$('ptabs').addEventListener('click', e=>{
  const b=e.target.closest('.ptab'); if(!b) return;
  document.querySelectorAll('#ptabs .ptab').forEach(x=>x.classList.toggle('on', x===b));
  ENGINE=b.dataset.engine; loadPreds();
});
$('q').addEventListener('input', ()=>{ Q=$('q').value||''; paintGrid(); });
$('slip-clear').onclick=()=>{ SLIP=[]; paintSlip(); };
$('psea').addEventListener('change', ()=>{ PSEA=$('psea').value; loadPlayers(); });
$('pq').addEventListener('input', ()=>{ clearTimeout($('pq')._t); $('pq')._t=setTimeout(()=>loadPlayers(), 220); });
document.querySelector('#pane-p .pbar').addEventListener('click', e=>{
  const b=e.target.closest('.pchip'); if(!b) return; loadPlayers(b.dataset.stat);
});
(function(){
  const a=document.getElementById('nav-site');
  if(!a) return;
  a.addEventListener('click', e=>{
    e.preventDefault();
    const url=a.getAttribute('href')||'';
    try{ window.top.location.href=url; }catch(err){ location.href=url; }
  });
})();
loadBook();
loadCoupons();
setInterval(()=>{ if($('pane-k').style.display!=='none') loadBook(); }, 30000);
</script>
</body>
</html>
"""
