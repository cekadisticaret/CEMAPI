"""Dashboard HTML şablonları — CoptC Live Control."""

PAGE = r"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{{ base }}/favicon.ico" type="image/svg+xml">
<link rel="stylesheet" href="{{ base }}/static/coptc.css?v={{ static_ver }}">
<title>{{ app_name }}</title>
</head><body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-icon" id="badge">C</div>
      <div><div class="brand-name">CemAPI</div><div class="brand-sub">Live Control</div></div>
    </div>
    <nav class="nav">
      <a class="nav-item on" href="{{ base }}/">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg>
        Dashboard
      </a>
      <a class="nav-item" href="{{ base }}/islemler">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-6 6"/></svg>
        İşlemler
      </a>
      <a class="nav-item" href="{{ base }}/algoritma-islemler">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        Algoritma İşlemler
      </a>
      <a class="nav-item{% if nav_on=='live' %} on{% endif %}" href="{{ base }}/live">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M5 5a10 10 0 0 1 14 0M3 3a13 13 0 0 1 18 0M8.5 8.5a5 5 0 0 1 7 0"/></svg>
        LIVE
        <span class="nav-live-dot"></span>
      </a>
      <a class="nav-item" href="{{ base }}/grafik-analiz">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19V9M10 19V5M16 19v-7M22 19V3"/></svg>
        Grafik Analiz
      </a>
      <a class="nav-item" href="{{ base }}/ayarlar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        Ayarlar
      </a>
    </nav>
    <div class="sidebar-foot">
      <b>Mirror modu</b>
      Kaynak defterin pozisyonları otomatik kopyalanır. :02:00–:09 arası 4 sn poll.
    </div>
  </aside>

  <div class="main">
    <header class="topbar">
      <div>
        <h1 id="title">…</h1>
        <div class="topbar-sub" id="subtitle"></div>
      </div>
      <div class="search-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3-3"/></svg>
        <input id="qhist" placeholder="İşlem geçmişinde ara…" autocomplete="off">
      </div>
      <div class="topbar-actions">
        <span class="clock" id="clock"></span>
        <span class="pill" id="pill">—</span>
        <button class="btn" id="bsig">Sinyal çek</button>
        <button class="btn primary" id="bref">Yenile</button>
      </div>
      <div class="topbar-mobile">
        <button type="button" class="btn btn-mlive danger" id="mLive">Live kapat</button>
        <button type="button" class="btn" id="mDesk">İşlemler</button>
        <button type="button" class="btn" id="mAlg">Algoritma</button>
        <button type="button" class="btn" id="mGa">Grafik Analiz</button>
        <button type="button" class="btn btn-mset" id="mSet">Ayarlar</button>
      </div>
    </header>

    <div class="content">
      <div class="center-col">
        <div class="note" id="mdlnote" style="display:none"></div>

        <div class="stat-row" id="stats"></div>

        <div class="card card-positions" id="posSection">
          <div class="card-hd">
            <span class="card-title">Açık pozisyonlar <span class="pos-count" id="posCount"></span></span>
            <span class="pos-hd-act">
              <button class="btn danger btn-sm" id="bcloseall" style="display:none">Tümünü kapat</button>
              <span class="status wait" id="posBadge">CANLI</span>
            </span>
          </div>
          <div id="pos"></div>
        </div>

        <div class="cons-strip" id="cons"></div>
        <div class="syms" id="syms">
          {% for i in range(3) %}
          <div class="sym nu"><div class="sym-top"><span class="sym-name">—</span></div>
            <div class="sym-price">…</div><div class="sym-metric">yükleniyor</div>
            <div class="gauge"><i style="left:50%"></i></div></div>
          {% endfor %}
        </div>

        <div class="card card-chart">
          <div class="card-hd"><span class="card-title">Saatlik performans</span><span class="mut" id="hsrc">—</span></div>
          <div class="chart-wrap" id="chart"></div>
        </div>

        <div class="card card-hist">
          <div class="card-hd"><span class="card-title">Son işlemler</span><span class="mut" id="tsrc">—</span></div>
          <div class="table-wrap"><table>
            <thead><tr><th>Sembol</th><th>Platform</th><th>Tahmin</th><th>Gerçek</th><th>Durum</th><th>P&amp;L</th><th>Zaman</th></tr></thead>
            <tbody id="hist"></tbody>
          </table></div>
        </div>
      </div>

      <aside class="right-col">
        <div class="wallet-card">
          <div class="wallet-label">Polymarket</div>
          <div class="wallet-bal" id="wpmbal">—</div>
          <div class="wallet-sub" id="wpmsub">Serbest USDC</div>
          <div class="wallet-src" id="wsrc"></div>
        </div>

        <div class="quick-actions">
          <div class="qa" onclick="location.href=BASE+'/ayarlar'"><div class="qa-icon">⚙</div>Ayarlar</div>
          <div class="qa" id="qaLive"><div class="qa-icon">▶</div><span id="qaLiveTxt">Live</span></div>
          <div class="qa" id="bref2"><div class="qa-icon">↻</div>Yenile</div>
          <div class="qa" id="bsig2"><div class="qa-icon">📡</div>Sinyal</div>
        </div>

        <div class="card card-wl">
          <div class="card-hd"><span class="card-title">Win / Loss</span></div>
          <div class="donut-wrap">
            <div class="donut" id="donut"></div>
          </div>
          <div class="legend" id="legend"></div>
        </div>

        <div class="card card-cron">
          <div class="card-hd"><span class="card-title">Cron zamanları</span></div>
          <div class="timeline-list" id="tl"></div>
        </div>
      </aside>
    </div>
  </div>
</div>

<script>
let BOOK = {{ book|tojson }};
const BASE = {{ base|tojson }};
let LIVE_ON = false;
let HIST = [];
let POS_N = 0;
let CLOSING = false;
const CLOSE_ALL_ENABLED = true;
const CLOSE_ONE_ENABLED = true;
const $ = id => document.getElementById(id);
const money = v => v === null || v === undefined ? '—'
  : (v < 0 ? '-$' : '$') + Math.abs(v).toLocaleString('tr-TR', {minimumFractionDigits:2, maximumFractionDigits:2});
const cls = v => v > 0 ? 'g' : (v < 0 ? 'b' : '');
const fmtSpot = n => n == null ? '—' : '$' + Number(n).toLocaleString('tr-TR', {maximumFractionDigits:2});
const symIcon = s => (s || '?').replace('USDT','').slice(0,3);

function posCard(p){
  const dirTr = p.dir === 'UP' ? 'YÜKSELİR' : 'DÜŞER';
  const win = p.winning;
  const delta = p.spot_diff;
  const deltaTxt = delta == null ? '' :
    `<span class="${delta >= 0 ? 'g' : 'b'}">${delta >= 0 ? '+' : ''}${delta}</span>`;
  const winMark = win == null ? '' : `<span class="${win ? 'g' : 'b'}">${win ? '✓' : '✗'}</span>`;
  const hasPnl = p.close_pnl != null && !p.no_liquidity;
  const pnlCls = cls(p.close_pnl);
  const pnlAmt = hasPnl
    ? (p.close_pnl >= 0 ? '+' : '') + p.close_pnl.toFixed(2) + '$'
    : '—';
  const pnlPct = hasPnl && p.pnl_pct != null
    ? (p.pnl_pct >= 0 ? '+' : '') + p.pnl_pct.toFixed(1) + '%'
    : '';
  const pnlHeroCls = p.no_liquidity ? 'na' : (!hasPnl ? 'flat' : (p.close_pnl > 0 ? 'is-up' : (p.close_pnl < 0 ? 'is-dn' : 'flat')));
  const badge = p.badge ? `<span class="ptag${p.book === BOOK ? ' me' : ''}">${p.badge}</span>` : '';
  const srcTag = p.source ? `<span class="ptag src">${p.source}</span>` : '';
  const dirCls = p.dir === 'UP' ? 'dir-up' : (p.dir === 'DOWN' ? 'dir-dn' : '');
  return `<div class="pcard ${dirCls}"><div class="phead">
      <span class="psym">${p.symbol}${badge}${srcTag}</span>
      <span class="tag ${p.dir === 'UP' ? 'up' : 'dn'}">${dirTr}</span></div>
    <div class="ppx">${fmtSpot(p.spot_now)} ${winMark} ${deltaTxt}</div>
    <div class="pmeta">Giriş $${p.entry ?? '—'} · Slot ${p.slot || '—'}</div>
    <div class="pnl-hero ${pnlHeroCls}">
      <div class="pnl-hero-k">Anlık kâr/zarar</div>
      <div class="pnl-hero-row">
        <span class="pnl-hero-amt ${pnlCls}">${pnlAmt}</span>
        ${pnlPct ? `<span class="pnl-hero-pct ${pnlCls}">${pnlPct}</span>` : ''}
      </div>
      ${p.no_liquidity ? '<div class="pnl-hero-note">Piyasada alıcı yok — satış değeri hesaplanamıyor</div>' : ''}
    </div>
    <div class="pclose"><div><div class="risk-k">Anlık kapatma</div>
      <div class="mut" style="font-size:11px">${p.no_liquidity ? 'alıcı yok' : ('token ' + (p.token_bid ?? '—'))}</div></div>
      <div class="risk-v ${hasPnl ? pnlCls : ''}">${p.no_liquidity ? '—' : money(p.close_val)}</div></div>
    <div class="pfoot">
      <span>Risk <b>${money(p.spent)}</b></span>
      <span>Kazanırsa <b class="g">${money(p.to_win)}</b></span></div>
    ${CLOSE_ONE_ENABLED ? `<button type="button" class="btn danger btn-sm pclose-btn"
      data-symbol="${p.symbol}"
      data-token="${p.token_id || ''}"
      data-source="${p.source_book || ''}"
      data-hour="${p.entry_hour ?? ''}"
      data-pnl="${hasPnl ? p.close_pnl.toFixed(2) : ''}"
      ${(!p.token_id || p.no_liquidity) ? 'disabled' : ''}
      ${p.no_liquidity ? 'title="Piyasada alıcı yok"' : ''}>Manuel kapat</button>` : ''}</div>`;
}

function clock(){
  $('clock').textContent = new Date().toLocaleTimeString('tr-TR', {timeZone:'Europe/Istanbul', hour12:false}) + ' İST';
}
setInterval(clock, 1000); clock();

function renderSyms(rows){
  $('syms').innerHTML = rows.map(s => {
    const d = s.dir === 'UP' ? 'up' : (s.dir === 'DOWN' ? 'dn' : '');
    const card = s.dir === 'UP' ? '' : (s.dir === 'DOWN' ? 'dn' : 'nu');
    const px = s.price ? '$' + Number(s.price).toLocaleString('tr-TR', {maximumFractionDigits:2}) : '—';
    const gp = Math.round((s.gauge ?? .5) * 100);
    return `<div class="sym ${card}"><div class="sym-top">
        <span class="sym-name">${s.name}</span><span class="tag ${d}">${s.dir || 'NÖTR'}</span></div>
      <div class="sym-price">${px}</div>
      <div class="sym-metric">${s.metric_label}</div>
      <div class="sym-val">${s.metric_value}</div>
      <div class="gauge"><i style="left:${Math.min(96, Math.max(4, gp))}%"></i></div>
      <div class="sym-foot">${s.foot || ''}</div></div>`;
  }).join('');
}

function renderChart(hours){
  const maxH = 120;
  $('chart').innerHTML = hours.map(h => {
    const pct = h.wr == null ? 8 : Math.max(12, Math.min(100, h.wr));
    const kind = h.wr == null ? 'empty' : (h.wr >= 55 ? 'hot' : (h.wr <= 45 ? 'cold' : ''));
    const tip = h.wr == null ? `${h.n} işlem yok` : `%${h.wr} · ${h.n} işlem`;
    return `<div class="chart-bar"><div class="bar ${kind}" style="height:${pct * 1.6}px" title="${tip}">
      <span class="tip">${h.wr == null ? '—' : h.wr + '%'}</span></div>
      <span class="lbl">${String(h.h).padStart(2,'0')}</span></div>`;
  }).join('');
}

function renderDonut(w, l){
  const tot = w + l || 1;
  const wp = (w / tot) * 100;
  const lp = (l / tot) * 100;
  const c = 2 * Math.PI * 54;
  const wLen = (wp / 100) * c;
  const lLen = (lp / 100) * c;
  $('donut').innerHTML = `<svg width="140" height="140" viewBox="0 0 120 120">
    <circle cx="60" cy="60" r="54" fill="none" stroke="#2A2D38" stroke-width="14"/>
    <circle cx="60" cy="60" r="54" fill="none" stroke="#C1FF72" stroke-width="14"
      stroke-dasharray="${wLen} ${c}" stroke-linecap="round"/>
    <circle cx="60" cy="60" r="54" fill="none" stroke="#FF4D8D" stroke-width="14"
      stroke-dasharray="${lLen} ${c}" stroke-dashoffset="${-wLen}" stroke-linecap="round"/>
  </svg><div class="donut-center"><div class="big">${tot ? Math.round(wp) : 0}%</div><div class="sm">Win rate</div></div>`;
  $('legend').innerHTML = `
    <div class="legend-item"><span class="legend-dot" style="background:#C1FF72"></span>Kazanç ${w}</div>
    <div class="legend-item"><span class="legend-dot" style="background:#FF4D8D"></span>Kayıp ${l}</div>
    <div class="legend-item"><span class="legend-dot" style="background:#9a9a9a"></span>Toplam ${tot}</div>
    <div class="legend-item"><span class="legend-dot" style="background:#6b6b6b"></span>WR ${tot ? Math.round(wp) : 0}%</div>`;
}

function renderHist(filter=''){
  const q = filter.toLocaleLowerCase('tr');
  const rows = HIST.filter(t => {
    if (!q) return true;
    const hay = `${t.symbol||''} ${t.platform||''}`.toLocaleLowerCase('tr');
    return hay.includes(q);
  });
  $('hist').innerHTML = rows.length ? rows.map(t => `<tr>
      <td><div class="td-sym"><span class="td-icon">${symIcon(t.symbol)}</span>${t.symbol}</div></td>
      <td class="mut">${t.platform || 'Polymarket'}</td>
      <td>${t.pred}</td><td>${t.actual}</td>
      <td><span class="status ${t.win ? 'ok' : 'bad'}">${t.win ? 'Kazanç' : 'Kayıp'}</span></td>
      <td class="${cls(t.pnl)}">${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}$</td>
      <td class="mut">${t.time}</td></tr>`).join('')
    : `<tr><td colspan="7" class="empty">${filter ? 'Eşleşme yok' : 'Henüz kapanmış işlem yok'}</td></tr>`;
}

function render(d){
  BOOK = d.book; LIVE_ON = d.live_on; HIST = d.history || [];
  $('badge').textContent = (d.badge || 'C').slice(0,2);
  $('title').textContent = d.title || 'Dashboard';
  $('subtitle').textContent = d.subtitle || '';

  $('mdlnote').innerHTML = d.live_on
    ? `Live açık — yön <b>${d.mirror_short || d.mirror_book || '—'}</b> (API 1. sıra) kaynağından kopyalanır.`
    : 'Live kapalı — cron çalışır ama emir gönderilmez.';
  if (d.weekend && d.weekend.enabled && d.weekend.active) {
    $('mdlnote').innerHTML += `<br><span class="b">Hafta sonu duraklama aktif — ${d.weekend.window}</span>`;
  } else if (d.weekend && d.weekend.enabled && d.live_on) {
    $('mdlnote').innerHTML += `<br>Hafta sonu kontrolü açık — ${d.weekend.window}`;
  }
  $('mdlnote').style.display = '';

  const wkPause = d.weekend && d.weekend.active;
  $('pill').textContent = !d.live_on ? 'LIVE KAPALI' : (wkPause ? 'HAFTA SONU' : 'LIVE AÇIK');
  $('pill').className = 'pill' + (d.live_on && !wkPause ? ' on' : '');
  $('qaLiveTxt').textContent = d.live_on ? 'Live ✓' : 'Live ✗';
  $('qaLive').className = 'qa' + (d.live_on ? ' on' : '');
  const mLive = $('mLive');
  if (mLive) {
    mLive.textContent = d.live_on ? 'Live kapat' : 'Live aç';
    mLive.className = 'btn btn-mlive ' + (d.live_on ? 'danger' : 'success');
  }

  const r = d.risk;
  const pnlCls = d.live_pnl > 0 ? ' pos' : (d.live_pnl < 0 ? ' neg' : '');
  const upnlTxt = r.upnl ? ((r.upnl >= 0 ? '+' : '') + money(r.upnl)) : '—';
  const toWinTxt = r.to_win ? money(r.to_win) : '—';
  const closeTxt = r.close_total ? money(r.close_total) : '—';
  $('stats').innerHTML = `
    <div class="stat acc-lime">
      <div class="stat-icon blue">💵</div>
      <div class="stat-label">PM nakit</div>
      <div class="stat-val">${money(d.cash)}</div>
      <div class="stat-foot">${d.cash === null ? 'cüzdan tanımsız' : 'serbest USDC'}</div>
    </div>
    <div class="stat stat-cashout acc-cyan" id="redeemStat" title="Nakde çevir — tıkla">
      <div class="stat-icon blue">↻</div>
      <div class="stat-label">Nakde çevrilecek</div>
      <div class="stat-val" id="redeemVal">${money(d.redeem_pending)}</div>
      <div class="stat-foot" id="redeemFoot">${d.pm_redeem_winners || 0} kazanan · tıkla veya otomatik</div>
    </div>
    <div class="stat acc-pink${d.live_pnl > 0 ? ' hi' : ''}">
      <div class="stat-icon ${d.live_pnl < 0 ? 'red' : 'green'}">📈</div>
      <div class="stat-label">Gerçek P&amp;L</div>
      <div class="stat-val${pnlCls}">${money(d.live_pnl)}</div>
      <div class="stat-foot">${d.live_w}W / ${d.live_l}L · defter ${d.pm_book_pnl >= 0 ? '+' : ''}${money(d.pm_book_pnl)}</div>
    </div>
    <div class="stat stat-risk acc-orange">
      <div class="stat-icon">◎</div>
      <div class="stat-label">Toplam riskteki</div>
      <div class="stat-val">${money(r.total)}</div>
      <div class="risk-grid">
        <div><div class="rk">Kazanılacak</div><div class="rv">${toWinTxt}</div></div>
        <div><div class="rk">Açık</div><div class="rv">${r.open}</div></div>
        <div><div class="rk">Anlık kâr/zarar</div><div class="rv">${upnlTxt}</div></div>
        <div><div class="rk">Anlık kapama</div><div class="rv">${closeTxt}</div></div>
      </div>
    </div>`;

  $('wpmbal').textContent = money(d.cash);
  const srcHint = d.cash_stale || d.cash_source === 'cache' ? ' · son okunan'
    : (d.cash_source === 'chain' ? ' · zincir' : '');
  $('wpmsub').innerHTML = d.equity != null
    ? `<span class="wallet-equity">Anlık toplam ${money(d.equity)}</span> · serbest USDC${srcHint}`
    : (d.cash === null ? 'CLOB yanıt vermedi' : 'Serbest USDC' + srcHint);
  const wc = document.querySelector('.wallet-card');
  const walletTotal = d.equity != null ? d.equity : d.cash;
  if (wc) {
    wc.classList.toggle('ok', walletTotal != null && walletTotal > 1000);
    wc.classList.toggle('warn', walletTotal != null && walletTotal <= 1000);
  }
  $('wsrc').textContent = d.live_on
    ? `${d.mirror_short || d.mirror_book || '—'} aynası · PM emri açık`
    : 'Live kapalı';

  $('pos').innerHTML = d.positions.length
    ? `<div class="pgrid">${d.positions.map(posCard).join('')}</div>`
    : `<div class="empty">${d.live_on ? 'Kaynak açınca :02:00–:09 arası PM emri açılır' : 'Live kapalı'}</div>`;
  const nPos = d.positions.length;
  const closeSum = (d.positions || []).reduce((s, p) => s + (Number(p.close_val) || 0), 0);
  $('posCount').innerHTML = nPos
    ? `(${nPos}) <span class="pos-close-sum">· anlık kapatma ${money(closeSum)}</span>`
    : '';
  $('posSection').classList.toggle('has-pos', nPos > 0);
  $('posBadge').textContent = nPos ? `${nPos} AÇIK` : 'BOŞ';
  $('posBadge').className = 'status ' + (nPos ? 'ok' : 'wait');
  POS_N = nPos;
  if (CLOSE_ALL_ENABLED && !CLOSING){
    const bca = $('bcloseall');
    bca.style.display = nPos ? '' : 'none';
    bca.disabled = false;
    bca.textContent = 'Tümünü kapat';
  } else {
    $('bcloseall').style.display = 'none';
  }

  $('hsrc').textContent = (d.mirror_short || d.badge) + ' · saatlik WR';
  $('tsrc').textContent = (d.mirror_short || d.badge);
  renderChart(d.hours);
  renderDonut(d.live_w || 0, d.live_l || 0);
  renderHist($('qhist').value);

  $('tl').innerHTML = d.timeline.map(t =>
    `<div class="tl-item"><span class="tl-time">${t[0]}</span><span class="tl-text">${t[1]}</span></div>`).join('');
  const rs = $('redeemStat');
  if (rs) rs.onclick = cashOut;
}

async function load(){
  try{
    const r = await fetch(BASE + '/api/overview', {cache:'no-store'});
    if (r.status === 401) return location.href = BASE + '/giris';
    const d = await r.json();
    if (!d || !d.models) throw new Error(d?.error || 'veri alınamadı');
    render(d);
  } catch(e){
    $('mdlnote').innerHTML = `<span class="werr">Veri yüklenemedi: ${e.message}</span>`;
  }
}
let es = null, esBackoff = 1000, esLast = Date.now();
function startStream(){
  try { if (es) es.close(); } catch(e) {}
  es = new EventSource(BASE + '/api/overview/stream');
  es.onopen = () => { esBackoff = 1000; esLast = Date.now(); };
  es.onmessage = ev => {
    esLast = Date.now(); esBackoff = 1000;
    try { const d = JSON.parse(ev.data); if (d && d.models) render(d); } catch(e) {}
  };
  es.onerror = () => {
    // Sunucu yeniden başlarsa tarayıcı bağlantıyı kalıcı kapatır; elle geri bağlan.
    if (es && es.readyState === EventSource.CLOSED){
      setTimeout(startStream, esBackoff);
      esBackoff = Math.min(esBackoff * 2, 30000);
    }
  };
}
setInterval(() => {
  if (Date.now() - esLast > 25000){ esLast = Date.now(); startStream(); }
}, 5000);

function renderCons(d){
  const el = $('cons'); if (!el) return;
  if (!d || !d.ok){ el.innerHTML = ''; return; }
  const coins = (d.coins || []).map(c => {
    const up = c.dir === 'UP';
    return `<span class="cons-chip ${up ? 'up' : 'dn'}"><b>${c.symbol} ${c.label || ''}</b><em>↑${c.up} ↓${c.down}</em><i>%${Math.round(+c.wr || 0)}</i></span>`;
  }).join('');
  const st = d.stats || {};
  const slot = (d.slot_open_tr || '') + (d.books != null ? ` · ${d.books} defter` : '');
  el.innerHTML = `<span class="cons-slot">:${String(d.slot ?? '').padStart(2,'0')} ${slot}</span>${coins}<span class="cons-wr">${st.label || ''}</span>`;
}

async function loadCons(){
  try{
    const r = await fetch(BASE + '/api/consensus', {cache:'no-store'});
    if (r.status === 401) return;
    renderCons(await r.json());
  } catch(e){}
}

async function signals(){
  $('bsig').disabled = true; $('bsig2').style.opacity = '.5';
  try{
    const r = await fetch(BASE + `/api/${BOOK}/signals`);
    renderSyms(await r.json());
  } finally {
    $('bsig').disabled = false; $('bsig2').style.opacity = '1';
  }
}

$('bref').onclick = () => load().then(signals);
$('bref2').onclick = $('bref').onclick;
$('bsig').onclick = signals;
$('bsig2').onclick = signals;
async function toggleLive(){
  const on = !LIVE_ON;
  if (on && !confirm('GERÇEK PARA — bir sonraki slotta PM emri açılacak. Onay?')) return;
  const btn = $('mLive');
  if (btn) btn.disabled = true;
  try {
    await fetch(BASE + '/api/active', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book:BOOK, on})});
    await load();
  } finally {
    if (btn) btn.disabled = false;
  }
}
if ($('mLive')) $('mLive').onclick = toggleLive;
if ($('mSet')) $('mSet').onclick = () => location.href = BASE + '/ayarlar';
if ($('mDesk')) $('mDesk').onclick = () => location.href = BASE + '/islemler';
if ($('mAlg')) $('mAlg').onclick = () => location.href = BASE + '/algoritma-islemler';
if ($('mGa')) $('mGa').onclick = () => location.href = BASE + '/grafik-analiz';
$('qaLive').onclick = toggleLive;
$('qhist').oninput = e => renderHist(e.target.value);

async function cashOut(){
  const foot = $('redeemFoot');
  if (foot) foot.textContent = 'Nakde çevriliyor…';
  try{
    const r = await fetch(BASE + '/api/redeem', {method:'POST'});
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Başarısız');
    await load();
  } catch(e){
    if (foot) foot.innerHTML = `<span class="werr">${e.message}</span>`;
  }
}
const rs0 = $('redeemStat');
if (rs0) rs0.onclick = cashOut;

async function closeOne(btn){
  if (!CLOSE_ONE_ENABLED || CLOSING || btn.disabled) return;
  const sym = btn.dataset.symbol || '?';
  const pnl = btn.dataset.pnl;
  const pnlTxt = pnl ? ((Number(pnl) >= 0 ? '+' : '') + Number(pnl).toFixed(2) + '$') : '—';
  if (!confirm(`${sym} pozisyonu piyasa fiyatından satılacak.\nAnlık kâr/zarar: ${pnlTxt}\nGeri alınamaz — onaylıyor musun?`)) return;
  btn.disabled = true;
  const old = btn.textContent;
  btn.textContent = 'Kapatılıyor…';
  try{
    const r = await fetch(BASE + '/api/close-position', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        token_id: btn.dataset.token,
        source: btn.dataset.source || null,
        hour_tr: btn.dataset.hour === '' ? null : Number(btn.dataset.hour),
      }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Başarısız');
    const net = (d.pnl > 0 ? '+' : '') + money(d.pnl);
    alert(`${sym} kapatıldı · ${net}`);
    await load();
  } catch(e){
    alert(`${sym} kapatılamadı: ` + e.message);
    btn.disabled = false;
    btn.textContent = old;
  }
}

async function closeAll(){
  if (!CLOSE_ALL_ENABLED) return;
  if (CLOSING) return;
  if (!confirm(`${POS_N} açık pozisyonun tamamı piyasa fiyatından satılacak.\nGeri alınamaz — onaylıyor musun?`)) return;
  const b = $('bcloseall');
  CLOSING = true;
  b.disabled = true;
  b.textContent = 'Kapatılıyor…';
  try{
    const r = await fetch(BASE + '/api/close-all', {method:'POST'});
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Başarısız');
    const pnl = (d.pnl > 0 ? '+' : '') + money(d.pnl);
    alert(`${d.closed} pozisyon kapatıldı · ${pnl}` + (d.failed ? `\n${d.failed} pozisyon satılamadı${d.error ? ' — ' + d.error : ' — tekrar dene.'}` : ''));
  } catch(e){
    alert('Kapatma başarısız: ' + e.message);
  } finally {
    CLOSING = false;
    await load();
  }
}
$('bcloseall').onclick = closeAll;

$('posSection').addEventListener('click', e => {
  const btn = e.target.closest('.pclose-btn');
  if (btn) closeOne(btn);
});

load().then(signals); loadCons(); startStream();
setInterval(loadCons, 60000);
</script></body></html>"""

SETTINGS = r"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{{ base }}/favicon.ico" type="image/svg+xml">
<link rel="stylesheet" href="{{ base }}/static/coptc.css?v={{ static_ver }}">
<title>{{ app_name }} — Ayarlar</title>
</head><body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-icon">C</div>
      <div><div class="brand-name">CemAPI</div><div class="brand-sub">Live Control</div></div>
    </div>
    <nav class="nav">
      <a class="nav-item" href="{{ base }}/">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg>
        Dashboard
      </a>
      <a class="nav-item" href="{{ base }}/islemler">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-6 6"/></svg>
        İşlemler
      </a>
      <a class="nav-item" href="{{ base }}/algoritma-islemler">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        Algoritma İşlemler
      </a>
      <a class="nav-item{% if nav_on=='live' %} on{% endif %}" href="{{ base }}/live">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M5 5a10 10 0 0 1 14 0M3 3a13 13 0 0 1 18 0M8.5 8.5a5 5 0 0 1 7 0"/></svg>
        LIVE
        <span class="nav-live-dot"></span>
      </a>
      <a class="nav-item" href="{{ base }}/grafik-analiz">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19V9M10 19V5M16 19v-7M22 19V3"/></svg>
        Grafik Analiz
      </a>
      <a class="nav-item on" href="{{ base }}/ayarlar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        Ayarlar
      </a>
    </nav>
    <div class="sidebar-foot"><b>Gerçek para</b>Live aç/kapa ve kaynak defter seçimi buradan yapılır.</div>
  </aside>

  <div class="main">
    <header class="topbar">
      <div><h1>Ayarlar</h1><div class="topbar-sub">{{ app_name }}</div></div>
      <div class="topbar-actions">
        <span class="pill" id="pill">—</span>
        <button class="btn" id="bsig">Sinyal çek</button>
        <button class="btn primary" id="bref">Yenile</button>
        <button class="btn primary" id="bweekend">HS otomatik: —</button>
        <button class="btn danger" id="blive">—</button>
      </div>
    </header>

    <div class="cron-strip">
      <span><b>:01</b> Eski slot kapanır</span>
      <span><b>:02:00–:09</b> Live PM aç (4 sn poll)</span>
      <span><b>Cum 22:00 – Pzt 11:00</b> HS otomatik penceresi</span>
    </div>

    <div class="content" style="grid-template-columns:1fr">
      <div class="center-col settings-grid">

        <div class="card">
          <div class="card-hd"><span class="card-title">Gerçek para işlemi</span></div>
          <div class="lvst" id="lvst">—</div>
          <div class="hint" id="lvhint"></div>
        </div>

        <div class="card">
          <div class="card-hd">
            <span class="card-title">Hafta sonu kontrolü</span>
            <span class="status wait" id="wkBadge">—</span>
          </div>
          <div class="lvst" id="wkst">—</div>
          <div class="hint" id="wkhint">Üstteki «HS otomatik» ile aç/kapa — Cum 22:00 – Pazartesi 11:00 İST.</div>
        </div>

        <div class="card">
          <div class="card-hd"><span class="card-title">Giriş tutarları</span></div>
          <div class="stat-row" style="grid-template-columns:repeat(3,1fr)" id="abox"></div>
          <div class="amt-src" id="amtSrc">Seçili kaynak</div>
          <div class="form-row amount-row">
            <label>Low (WR &lt; 50%)<input id="alow" type="number" step="0.5" min="1"></label>
            <label>Mid<input id="amid" type="number" step="0.5" min="1"></label>
            <label>High<input id="ahigh" type="number" step="0.5" min="1"></label>
            <button class="btn primary" id="bsave">Kaydet</button>
          </div>
          <div class="amt-src">Asgari kâr — tüm API algoritmaları</div>
          <div class="form-row amount-row">
            <label>Kâr eşiği (%)<input id="mprofit" type="number" step="1" min="0" max="900"></label>
            <div class="hint" id="mprofithint">—</div>
          </div>
          <div class="cold-cut-row">
            <button class="btn primary" id="bcoldcut">Zayıf saat −30%: —</button>
            <div class="hint" id="coldhint">Geçmişte en düşük WR'li saatlerde giriş tutarı otomatik −30% indirilir.</div>
          </div>
            <div class="hint" id="ahint">API’den seçilen her algoritma bu Low/Mid/High ile açılır.</div>
        </div>

        <div class="card settings-full">
          <div class="card-hd">
            <span class="card-title">Kaynak algoritma <span class="pos-count" id="mcount"></span></span>
            <span class="status wait">API</span>
          </div>
          <div class="mtools">
            <input id="q" placeholder="Defter ara…" autocomplete="off">
            <button class="btn" id="brel">Yenile</button>
          </div>
          <div class="msel-bar">
            <div class="msel-now" id="mnow">—</div>
            <button class="btn" id="mreset" disabled>Geri al</button>
            <button class="btn primary" id="msave" disabled>Kaydet</button>
          </div>
          <div id="mlist"><div class="empty">Kaynak listesi yükleniyor…</div></div>
          <div class="hint" id="mhint">Kaynak, API sıralamasının 1. defteridir — Kaydet gerekmez.
            Sıralama değişince otomatik geçer; açık PM pozisyonlar kapanmaz.</div>
        </div>

        <div class="card settings-full">
          <div class="card-hd"><span class="card-title">Polymarket'ten para çek</span><span class="status bad">GERÇEK PARA</span></div>
          <div class="stat-row" style="grid-template-columns:repeat(3,1fr)" id="wdinfo"></div>
          <div class="form-row" style="grid-template-columns:2fr 1fr 1fr;margin-top:16px">
            <label>Hedef adres<input id="wto" placeholder="0x…" class="mono" autocomplete="off"></label>
            <label>Tutar ($)<input id="wamt" type="number" step="0.01" min="0.01"></label>
            <label>Token<select id="wtok"><option value="PUSD">pUSD</option><option value="USDC.E">USDC.e</option></select></label>
          </div>
          <div class="form-row" style="grid-template-columns:1fr auto">
            <label>Çekim kodu<input id="wcode" type="password" autocomplete="off"></label>
            <button class="btn danger" id="wsend">Parayı çek</button>
          </div>
          <div class="hint" id="wmsg">Geri alınamaz. 5 hatalı kod → 15 dk kilit.</div>
          <div id="wlog"></div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
let BOOK = {{ book|tojson }};
const BASE = {{ base|tojson }};
let LIVE_ON = false, ROWS = [], WEEKEND_ON = false, COLD_CUT_ON = false;
// MIRROR = kayıtlı seçim, PICK = henüz kaydedilmemiş seçim (null = hiç dokunulmadı)
let MIRROR = [], PICK = null;
const MIRROR_MAX = 3;
const $ = id => document.getElementById(id);
const money = v => v === null || v === undefined ? '—'
  : (v < 0 ? '-$' : '$') + Math.abs(v).toLocaleString('tr-TR', {minimumFractionDigits:2, maximumFractionDigits:2});

function renderWeekend(w){
  if (!w) return;
  WEEKEND_ON = !!w.enabled;
  const active = !!w.active;
  $('wkBadge').textContent = !WEEKEND_ON ? 'PASİF' : (active ? 'DURAKLAMA' : 'BEKLEMEDE');
  $('wkBadge').className = 'status ' + (!WEEKEND_ON ? 'wait' : (active ? 'bad' : 'ok'));
  $('wkst').textContent = !WEEKEND_ON
    ? '7/24 mod — hafta sonu kısıtı yok'
    : (active ? 'Şu an kapalı — ' + w.window : 'Zamanlayıcı aktif — ' + w.window);
  $('wkst').className = 'lvst ' + (!WEEKEND_ON ? 'g' : (active ? 'b' : ''));
  $('wkhint').textContent = w.message || w.window || '';
  $('bweekend').textContent = WEEKEND_ON ? 'HS otomatik: AÇIK' : 'HS otomatik: KAPALI';
  $('bweekend').className = 'btn primary' + (WEEKEND_ON ? ' on' : '');
}

async function toggleWeekend(){
  const on = !WEEKEND_ON;
  $('bweekend').disabled = true;
  $('bweekend').textContent = 'Kaydediliyor…';
  try{
    const r = await fetch(BASE + '/api/weekend', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({enabled: on}),
    });
    if (r.status === 401) return location.href = BASE + '/giris';
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Kaydedilemedi');
    renderWeekend(d);
    load();
  } catch(e){
    $('wkhint').innerHTML = `<span class="werr">${e.message}</span>`;
    renderWeekend({enabled: WEEKEND_ON});
  } finally {
    $('bweekend').disabled = false;
  }
}

function render(d){
  BOOK = d.book; LIVE_ON = d.live_on;
  setSaved(d.mirror_books || (d.mirror_book ? [d.mirror_book] : []));
  renderWeekend(d.weekend);
  const wkPause = d.weekend && d.weekend.active;
  $('pill').textContent = !d.live_on ? 'LIVE KAPALI' : (wkPause ? 'HAFTA SONU' : 'LIVE AÇIK');
  $('pill').className = 'pill' + (d.live_on && !wkPause ? ' on' : '');
  const src = d.mirror_short || d.mirror_book || '—';
  $('lvst').textContent = d.live_on ? src + ' kaynağından live AÇIK' : 'Gerçek para işlemi KAPALI';
  $('lvst').className = 'lvst ' + (d.live_on ? 'g' : 'b');
  $('lvhint').textContent = d.live_on
    ? 'Kaynak API 1. sıra — sıralama değişince otomatik geçer. :02:00–:09 arası 4 sn poll.'
    : 'Cron çalışır ama emir gönderilmez.';
  $('blive').textContent = d.live_on ? 'Live kapat' : 'Live aç';
  $('blive').className = 'btn ' + (d.live_on ? 'danger' : 'success');
  const a = d.amounts;
  $('abox').innerHTML = `
    <div class="stat acc-lime${a.wr >= 50 ? ' hi' : ''}"><div class="stat-label">Win rate</div><div class="stat-val ${a.wr >= 50 ? 'g' : 'b'}">${a.wr == null ? '—' : '%'+a.wr}</div></div>
    <div class="stat acc-cyan"><div class="stat-label">İşlem</div><div class="stat-val">${a.trades}</div></div>
    <div class="stat acc-orange"><div class="stat-label">Açık</div><div class="stat-val">${a.open}</div></div>`;
  if (document.activeElement.tagName !== 'INPUT'){
    $('alow').value = a.low; $('amid').value = a.mid; $('ahigh').value = a.high;
    if ($('mprofit')) $('mprofit').value = a.min_profit_pct ?? 60;
  }
  renderProfitHint(a.min_profit_pct, a.min_profit_max_price);
  renderColdCut(a.cold_hour_cut_enabled);
  drawMirror();
}

function renderProfitHint(pct, cap){
  const el = $('mprofithint');
  if (!el) return;
  const p = pct == null ? 60 : pct;
  el.textContent = `Kazanınca kâr, harcanan paranın %${p} altındaysa işlem açılmaz `
    + `— token fiyatı en fazla ${(cap ?? (1/(1+p/100))).toFixed(3)}. `
    + `Her API algoritması için geçerli.`;
}

function renderColdCut(on){
  COLD_CUT_ON = !!on;
  $('bcoldcut').textContent = COLD_CUT_ON ? 'Zayıf saat −30%: AÇIK' : 'Zayıf saat −30%: KAPALI';
  $('bcoldcut').className = 'btn primary' + (COLD_CUT_ON ? ' on' : '');
  $('coldhint').textContent = COLD_CUT_ON
    ? 'Zayıf saatlerde (geçmişte en düşük WR) giriş tutarı otomatik −30% indirilir.'
    : 'Kesinti kapalı — kademe tutarı (Low/Mid/High) olduğu gibi uygulanır.';
}

async function toggleColdCut(){
  const on = !COLD_CUT_ON;
  $('bcoldcut').disabled = true;
  $('bcoldcut').textContent = 'Kaydediliyor…';
  try{
    const r = await fetch(BASE + `/api/${BOOK}/amounts`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        low: +$('alow').value, mid: +$('amid').value, high: +$('ahigh').value,
        cold_hour_cut_enabled: on,
      }),
    });
    if (r.status === 401) return location.href = BASE + '/giris';
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Kaydedilemedi');
    renderColdCut(d.cold_hour_cut_enabled);
    $('ahint').innerHTML = '<span class="wok">Zayıf saat kesintisi güncellendi.</span>';
    load();
  } catch(e){
    $('ahint').innerHTML = `<span class="werr">${e.message}</span>`;
    renderColdCut(COLD_CUT_ON);
  } finally {
    $('bcoldcut').disabled = false;
  }
}

async function load(){
  const r = await fetch(BASE + '/api/overview', {cache:'no-store'});
  if (r.status === 401) return location.href = BASE + '/giris';
  render(await r.json());
}
let es = null, esBackoff = 1000, esLast = Date.now();
function startStream(){
  try { if (es) es.close(); } catch(e) {}
  es = new EventSource(BASE + '/api/overview/stream');
  es.onopen = () => { esBackoff = 1000; esLast = Date.now(); };
  es.onmessage = ev => {
    esLast = Date.now(); esBackoff = 1000;
    try { const d = JSON.parse(ev.data); if (d) render(d); } catch(e) {}
  };
  es.onerror = () => {
    if (es && es.readyState === EventSource.CLOSED){
      setTimeout(startStream, esBackoff);
      esBackoff = Math.min(esBackoff * 2, 30000);
    }
  };
}
setInterval(() => {
  if (Date.now() - esLast > 25000){ esLast = Date.now(); startStream(); }
}, 5000);

const pick = () => PICK || MIRROR;
const bookName = k => { const b = ROWS.find(x => x.book === k); return b ? b.short : k; };
const sameSet = (a, b) => a.length === b.length && a.every(x => b.includes(x));
const dirty = () => !sameSet(pick(), MIRROR);

function setSaved(list){
  MIRROR = Array.isArray(list) ? list.slice() : (list ? [list] : []);
  if (PICK === null) PICK = MIRROR.slice();
}

function mrow(b, i){
  const dirs = (b.positions||[]).map(p =>
    `<span class="chip ${p.dir==='UP'?'up':'dn'}">${p.symbol} ${p.dir==='UP'?'↑':'↓'}</span>`).join('');
  const on = pick().includes(b.book);
  const pnlCls = b.pnl == null ? '' : (b.pnl >= 0 ? 'g' : 'b');
  const mark = i === 0 ? 'API 1' : (on ? 'SEÇİLİ' : '');
  return `<div class="mrow ${on?'on':''}" data-k="${b.book}">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <span class="mtick">${on?'✓':''}</span>
      <span class="mut" style="font-size:11px;min-width:22px">#${i+1}</span>
      <span class="nm">${b.short}</span>${mark?'<span class="sel">'+mark+'</span>':''}
      <span class="mut" style="margin-left:auto;font-size:11px">${b.open?b.open+' açık':'açık yok'}</span></div>
    <div style="display:flex;gap:12px;align-items:baseline">
      <span style="font-size:18px;font-weight:800">${money(b.balance)}</span>
      <span class="${pnlCls}">${b.pnl==null?'—':((b.pnl>=0?'+':'')+b.pnl.toFixed(2))}</span>
      ${b.wr!=null?`<span class="mut" style="font-size:11px">WR %${b.wr}</span>`:''}
    </div>${dirs?`<div style="margin-top:8px">${dirs}</div>`:''}</div>`;
}

function drawMirror(){
  const q = ($('q').value||'').toLocaleLowerCase('tr');
  const rows = ROWS.filter(b => !q || (b.short||'').toLocaleLowerCase('tr').includes(q) || (b.label||'').toLocaleLowerCase('tr').includes(q));
  $('mlist').innerHTML = rows.length ? `<div class="mlist">${rows.map((b,i) => mrow(b, ROWS.indexOf(b))).join('')}</div>` : `<div class="empty">Eşleşen defter yok</div>`;
  document.querySelectorAll('.mrow').forEach(el => el.onclick = () => toggle(el.dataset.k));
  const cur = pick(), chg = dirty();
  $('mcount').textContent = cur.length ? `(${cur.length}/${MIRROR_MAX})` : '';
  $('mnow').innerHTML = cur.length
    ? (chg ? 'Kaydedilmedi: ' : 'Çalışan: ') + `<b>${cur.map(bookName).join(' + ')}</b>`
    : 'Seçim yok';
  $('mnow').className = 'msel-now' + (chg ? ' dirty' : '');
  $('msave').disabled = !chg;
  $('mreset').disabled = !chg;
  if ($('amtSrc')) $('amtSrc').textContent = cur.length
    ? 'Seçili kaynak: ' + cur.map(bookName).join(' + ')
    : 'Seçili kaynak';
}

function toggle(book){
  const cur = pick().slice();
  const i = cur.indexOf(book);
  if (i >= 0){
    if (cur.length === 1){
      $('mhint').innerHTML = '<span class="werr">En az bir algoritma seçili kalmalı.</span>';
      return;
    }
    cur.splice(i, 1);
  } else if (cur.length >= MIRROR_MAX){
    $('mhint').innerHTML = `<span class="werr">En fazla ${MIRROR_MAX} algoritma seçebilirsin — önce birini çıkar.</span>`;
    return;
  } else {
    cur.push(book);
  }
  PICK = cur;
  drawMirror();
}

async function loadMirror(){
  $('brel').disabled = true;
  try{
    const r = await fetch(BASE + '/api/mirror/books', {cache:'no-store'});
    const d = await r.json();
    if (d.error && !(d.books||[]).length){ $('mlist').innerHTML = `<div class="empty werr">${d.error}</div>`; return; }
    ROWS = d.books||[]; setSaved(d.selected); drawMirror();
  } finally { $('brel').disabled = false; }
}

async function saveMirror(){
  const list = pick().slice();
  if (!list.length) return;
  const names = list.map(bookName);
  if (!confirm(`Kaynak algoritmalar:\n\n${names.join('\n')}\n\n`
    + `Bu ${names.length} algoritma aynı anda çalışacak ve her biri kendi `
    + `pozisyonunu açacak. Devam?`)) return;
  $('msave').disabled = true;
  try{
    const r = await fetch(BASE + '/api/mirror/select', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({books: list}),
    });
    if (r.status === 401) return location.href = BASE + '/giris';
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Kaydedilemedi');
    MIRROR = d.selected || list; PICK = MIRROR.slice();
    $('mhint').innerHTML = `<span class="wok">Kaydedildi — ${MIRROR.map(bookName).join(' + ')} birlikte çalışacak.</span>`;
    load();
  } catch(e){
    $('mhint').innerHTML = `<span class="werr">${e.message}</span>`;
  } finally { drawMirror(); }
}

$('q').oninput = drawMirror; $('brel').onclick = loadMirror;
$('msave').onclick = saveMirror;
$('mreset').onclick = () => { PICK = MIRROR.slice(); drawMirror(); };
$('bweekend').onclick = toggleWeekend;
$('blive').onclick = async () => {
  const on = !LIVE_ON;
  if (on && !confirm(`GERÇEK PARA — ${MIRROR.map(bookName).join(' + ')||'kaynak'} bir sonraki slotta PM emri açacak. Onay?`)) return;
  $('blive').disabled = true;
  await fetch(BASE + '/api/active', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book:BOOK, on})});
  $('blive').disabled = false; load();
};
$('bsave').onclick = async () => {
  $('bsave').disabled = true;
  const r = await fetch(BASE + `/api/${BOOK}/amounts`, {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      low: +$('alow').value, mid: +$('amid').value, high: +$('ahigh').value,
      min_profit_pct: +$('mprofit').value,
      cold_hour_cut_enabled: COLD_CUT_ON,
    })});
  $('ahint').textContent = r.ok ? 'Kaydedildi.' : 'Kaydedilemedi.'; $('bsave').disabled = false; load();
};
$('bcoldcut').onclick = toggleColdCut;

function renderWd(w){
  const short = a => a ? a.slice(0,6)+'…'+a.slice(-4) : '—';
  const ok = !w.error && w.builder_ready && w.proxy_match;
  $('wdinfo').innerHTML = `
    <div class="stat acc-lime"><div class="stat-label">Çekilebilir</div><div class="stat-val">${money(w.balance)}</div></div>
    <div class="stat acc-cyan"><div class="stat-label">Cüzdan</div><div class="stat-val" style="font-size:14px">${short(w.funder)}</div></div>
    <div class="stat acc-pink${ok?' hi':''}"><div class="stat-label">Durum</div><div class="stat-val ${ok?'g':'b'}" style="font-size:15px">${ok?'Hazır':'Eksik'}</div></div>`;
  if (w.error) $('wmsg').innerHTML = `<span class="werr">${w.error}</span>`;
  $('wlog').innerHTML = (w.history||[]).map(h =>
    `<div class="pcard" style="margin-top:8px;padding:10px 14px"><span class="mut">${String(h.ts).slice(5,16)}</span>
     <b>${money(h.amount)}</b> → <span class="mono">${short(h.to)}</span></div>`).join('');
}
async function loadWd(){ const r = await fetch(BASE + '/api/withdraw/info'); if (r.ok) renderWd(await r.json()); }
$('wsend').onclick = async () => {
  const to=$('wto').value.trim(), amt=+$('wamt').value, code=$('wcode').value;
  if (!/^0x[0-9a-fA-F]{40}$/.test(to)) return $('wmsg').innerHTML='<span class="werr">Geçersiz adres</span>';
  if (!(amt>0)||!code) return $('wmsg').innerHTML='<span class="werr">Tutar ve kod gerekli</span>';
  if (!confirm(`GERİ ALINAMAZ — ${money(amt)} → ${to.slice(0,10)}…`)) return;
  $('wsend').disabled=true;
  const r=await fetch(BASE + '/api/withdraw/send',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({to,amount:amt,code,token:$('wtok').value})});
  const d=await r.json();
  $('wmsg').innerHTML=r.ok&&!d.error?`<span class="wok">Gönderildi</span>`:`<span class="werr">${d.error||'Hata'}</span>`;
  $('wsend').disabled=false; loadWd();
};
async function signals(){
  $('bsig').disabled = true;
  try{
    const r = await fetch(BASE + `/api/${BOOK}/signals`, {cache:'no-store'});
    if (r.status === 401) return location.href = BASE + '/giris';
    if (!r.ok) throw new Error('Sinyal alınamadı');
    $('lvhint').textContent = 'Sinyaller güncellendi — ' + new Date().toLocaleTimeString('tr-TR');
  } catch(e){
    $('lvhint').innerHTML = `<span class="werr">${e.message}</span>`;
  } finally { $('bsig').disabled = false; }
}
$('bref').onclick = () => load();
$('bsig').onclick = signals;
load(); loadMirror(); loadWd(); startStream(); setInterval(loadMirror, 60000);
</script></body></html>"""

TRADES = r"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{{ base }}/favicon.ico" type="image/svg+xml">
<link rel="stylesheet" href="{{ base }}/static/coptc.css?v={{ static_ver }}">
<title>{{ app_name }} — İşlemler</title>
</head><body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-icon">C</div>
      <div><div class="brand-name">CemAPI</div><div class="brand-sub">Live Control</div></div>
    </div>
    <nav class="nav">
      <a class="nav-item" href="{{ base }}/">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg>
        Dashboard
      </a>
      <a class="nav-item on" href="{{ base }}/islemler">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-6 6"/></svg>
        İşlemler
      </a>
      <a class="nav-item" href="{{ base }}/algoritma-islemler">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        Algoritma İşlemler
      </a>
      <a class="nav-item{% if nav_on=='live' %} on{% endif %}" href="{{ base }}/live">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M5 5a10 10 0 0 1 14 0M3 3a13 13 0 0 1 18 0M8.5 8.5a5 5 0 0 1 7 0"/></svg>
        LIVE
        <span class="nav-live-dot"></span>
      </a>
      <a class="nav-item" href="{{ base }}/grafik-analiz">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19V9M10 19V5M16 19v-7M22 19V3"/></svg>
        Grafik Analiz
      </a>
      <a class="nav-item" href="{{ base }}/ayarlar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        Ayarlar
      </a>
    </nav>
    <div class="sidebar-foot">
      <b>CLOB kotasyon</b>
      to win ve gerçek risk Gamma mid değil — anlık ask yürüyüşü.
    </div>
  </aside>

  <div class="main desk-page">
    <header class="topbar">
      <div>
        <h1>İşlemler</h1>
        <div class="topbar-sub">BTC · ETH · SOL — Polymarket anlık</div>
      </div>
      <div class="topbar-actions">
        <span class="clock" id="clock">—</span>
        <span class="pill" id="bal">—</span>
      </div>
      <div class="topbar-mobile">
        <button type="button" class="btn" id="mDash">Dashboard</button>
        <button type="button" class="btn btn-mset" id="mSet">Ayarlar</button>
      </div>
    </header>

    <div class="desk">
      <aside class="desk-left">
        <div class="desk-tabs" id="tabs"></div>

        <div class="desk-sec">
          <div class="desk-sec-hd">Aktif market</div>
          <div id="mkts"></div>
        </div>

        <div class="desk-sec">
          <div class="desk-sec-hd">Yeni işlem</div>
          <div class="desk-px">
            <div><span>Başlangıç</span><b id="pxOpen">—</b></div>
            <div><span>Anlık</span><b id="pxLast">—</b></div>
            <div class="desk-dx" id="pxDiff">—</div>
          </div>
          <div class="desk-slot" id="slotLine">—</div>
          <div class="desk-dirs">
            <button type="button" class="desk-dir up on" id="bUp">Yükselir</button>
            <button type="button" class="desk-dir dn" id="bDn">Düşer</button>
          </div>
          <label class="desk-amt">Tutar ($)
            <input id="amt" type="number" min="1" max="500" step="1" value="7">
          </label>
          <button type="button" class="desk-go" id="bOpen">İşlem Aç</button>
          <div class="desk-quote" id="qline">CLOB kotasyonu bekleniyor…</div>
        </div>

        <div class="desk-sec">
          <div class="desk-sec-hd">Açık pozisyonlar</div>
          <div id="dpos" class="desk-pos-list"><div class="empty">Bu ekrandan açık işlem yok</div></div>
        </div>
      </aside>

      <section class="desk-right">
        <div class="cons-strip" id="cons"></div>
        <div class="desk-chart-bar">
          <div class="desk-iv" id="ivs"></div>
          <div class="desk-sigs" id="sigs"></div>
          <div class="desk-chart-meta">
            <span id="refLbl">Ref —</span>
            <span id="nowLbl">—</span>
          </div>
        </div>
        <canvas class="desk-chart" id="deskChart"></canvas>
      </section>
    </div>
  </div>
</div>

<script>
const BASE = {{ base|tojson }};
const $ = id => document.getElementById(id);
const PERIODS = [[5,'5 Dakika'],[15,'15 Dakika'],[60,'1 Saat']];
const IVS = ['1m','5m','15m','1h'];
let period = 60, symbol = 'SOLUSDT', dir = 'UP', interval = '1m';
let snap = null, quote = null, bars = [], overlay = null, busy = false, qBusy = false;

function money(n, d=2){
  if (n == null || Number.isNaN(+n)) return '—';
  const x = +n;
  return (x < 0 ? '-$' : '$') + Math.abs(x).toFixed(d);
}
function fmtPx(n){
  if (n == null) return '—';
  const x = +n;
  return x >= 100 ? x.toFixed(2) : x >= 10 ? x.toFixed(3) : x.toFixed(4);
}
function leftTxt(sec){
  sec = Math.max(0, sec|0);
  const m = Math.floor(sec/60), s = sec % 60;
  return m + ':' + String(s).padStart(2,'0');
}

function drawTabs(){
  $('tabs').innerHTML = PERIODS.map(([p,l]) =>
    `<button type="button" class="desk-tab${p===period?' on':''}" data-p="${p}">${l}</button>`
  ).join('');
  $('tabs').onclick = e => {
    const b = e.target.closest('[data-p]');
    if (!b) return;
    period = +b.dataset.p;
    interval = period === 60 ? '1m' : (period === 15 ? '1m' : '1m');
    drawTabs(); loadSnap(); loadQuote(); loadBars();
  };
  $('ivs').innerHTML = IVS.map(iv =>
    `<button type="button" class="desk-ivb${iv===interval?' on':''}" data-iv="${iv}">${iv}</button>`
  ).join('');
  $('ivs').onclick = e => {
    const b = e.target.closest('[data-iv]');
    if (!b) return;
    interval = b.dataset.iv;
    drawTabs(); loadBars();
  };
}

function mktOf(sym){
  return (snap && snap.markets || []).find(m => m.symbol === sym) || null;
}

function drawMkts(){
  const rows = (snap && snap.markets) || [];
  $('mkts').innerHTML = rows.map(m => {
    const on = m.symbol === symbol ? ' on' : '';
    const st = m.ok ? '<em class="g">Açık</em>' : '<em class="b">Kapalı</em>';
    const up = m.up_cent != null ? `UP ${m.up_cent}¢` : 'UP —';
    const dn = m.down_cent != null ? `DOWN ${m.down_cent}¢` : 'DOWN —';
    const title = m.title || (m.short + ' Up or Down');
    return `<button type="button" class="desk-mkt${on}" data-s="${m.symbol}">
      <div class="desk-mkt-top"><b>${m.short}</b>${st}</div>
      <div class="desk-mkt-sub">${title}</div>
      <div class="desk-mkt-odds"><span class="up">${up}</span><span class="dn">${dn}</span></div>
    </button>`;
  }).join('') || '<div class="empty">Market yükleniyor…</div>';
  $('mkts').onclick = e => {
    const b = e.target.closest('[data-s]');
    if (!b) return;
    symbol = b.dataset.s;
    drawMkts(); fillSpot(); loadQuote(); loadBars();
  };
}

function fillSpot(){
  const m = mktOf(symbol);
  const slot = snap ? snap.slot_tr : '—';
  const left = snap ? leftTxt(snap.left_sec) : '—';
  const pl = period === 60 ? '1saat' : (period + 'dk');
  $('slotLine').textContent = `${slot} İST · ${pl} · kalan ${left}`;
  if (!m){ $('pxOpen').textContent='—'; $('pxLast').textContent='—'; $('pxDiff').textContent='—'; $('refLbl').textContent='Ref —'; return; }
  $('pxOpen').textContent = m.spot_open != null ? money(m.spot_open) : '—';
  $('pxLast').textContent = m.spot != null ? money(m.spot) : '—';
  const d = m.spot_diff;
  const el = $('pxDiff');
  if (d == null){ el.textContent='—'; el.className='desk-dx'; }
  else {
    el.textContent = (d>=0?'+':'') + money(d);
    el.className = 'desk-dx ' + (d>=0?'g':'b');
  }
  $('refLbl').textContent = m.spot_open != null ? `Ref ${fmtPx(m.spot_open)}` : 'Ref —';
}

function drawQuote(){
  const el = $('qline');
  if (!quote){ el.className='desk-quote'; el.textContent='CLOB kotasyonu bekleniyor…'; return; }
  if (!quote.ok){ el.className='desk-quote bad'; el.textContent = quote.error || 'kotasyon yok'; return; }
  const net = +quote.net, win = +quote.to_win, risk = +quote.spent, px = +quote.price;
  el.className = 'desk-quote ok';
  el.innerHTML = `<b class="${net>=0?'g':'b'}">${net>=0?'+':''}${money(net)}</b>
    🏆 ${money(win)} to win · gerçek risk ~${money(risk)}
    <span class="mut">@ ${px.toFixed(2)}</span>`;
}

function drawPos(){
  const rows = (snap && snap.positions) || [];
  if (!rows.length){ $('dpos').innerHTML = '<div class="empty">Bu ekrandan açık işlem yok</div>'; return; }
  $('dpos').innerHTML = rows.map(p => {
    const pnl = p.close_pnl;
    const pc = pnl == null ? '' : (pnl>=0?' g':' b');
    const pv = pnl == null ? '—' : ((pnl>=0?'+':'')+money(pnl));
    return `<div class="desk-pos">
      <div><b>${p.short} ${p.dir}</b> <span class="mut">${p.slot_tr||''}</span></div>
      <div class="mut">${money(p.pm_spent)} → ${(+p.pm_size||0).toFixed(2)} sh @ ${(+p.pm_entry_price||0).toFixed(2)}</div>
      <div class="desk-pos-row"><span class="${pc}">${pv}</span>
        <button type="button" class="btn danger btn-sm" data-id="${p.id}">Kapat</button></div>
    </div>`;
  }).join('');
  $('dpos').onclick = e => {
    const b = e.target.closest('[data-id]');
    if (b) closePos(b.dataset.id);
  };
}

function setDir(d){
  dir = d;
  $('bUp').classList.toggle('on', d==='UP');
  $('bDn').classList.toggle('on', d==='DOWN');
  loadQuote();
}

async function loadSnap(){
  try{
    const r = await fetch(BASE + '/api/desk/snapshot?period=' + period, {cache:'no-store'});
    if (r.status === 401) return location.href = BASE + '/giris';
    if (!r.ok) throw new Error('snapshot');
    snap = await r.json();
    if (snap.now_tr) $('clock').textContent = snap.now_tr;
    if (snap.balance != null) $('bal').textContent = money(snap.balance);
    drawMkts(); fillSpot(); drawPos(); drawChart();
  } catch(e){}
}
let es = null, esBackoff = 1000, esLast = Date.now();
function startSnapStream(){
  try { if (es) es.close(); } catch(e) {}
  es = new EventSource(BASE + '/api/desk/snapshot/stream');
  es.onopen = () => { esBackoff = 1000; esLast = Date.now(); };
  es.onmessage = ev => {
    esLast = Date.now(); esBackoff = 1000;
    try {
      const d = JSON.parse(ev.data);
      if (!d || d.ok === false) return;
      snap = d;
      if (snap.now_tr) $('clock').textContent = snap.now_tr;
      if (snap.balance != null) $('bal').textContent = money(snap.balance);
      drawMkts(); fillSpot(); drawPos(); drawChart();
    } catch(e) {}
  };
  es.onerror = () => {
    setTimeout(loadSnap, 3000);
    if (es && es.readyState === EventSource.CLOSED){
      setTimeout(startSnapStream, esBackoff);
      esBackoff = Math.min(esBackoff * 2, 30000);
    }
  };
}
setInterval(() => {
  if (Date.now() - esLast > 25000){ esLast = Date.now(); startSnapStream(); }
}, 5000);

async function loadQuote(){
  const amt = +$('amt').value;
  if (!(amt >= 1)) { quote = {ok:false, error:'tutar $1+'}; drawQuote(); return; }
  if (qBusy) return;
  qBusy = true;
  try{
    const u = BASE + `/api/desk/quote?symbol=${symbol}&period=${period}&dir=${dir}&amount=${amt}`;
    const r = await fetch(u, {cache:'no-store'});
    quote = await r.json();
    drawQuote();
  } catch(e){
    quote = {ok:false, error:'kotasyon alınamadı'};
    drawQuote();
  } finally { qBusy = false; }
}

async function loadBars(){
  try{
    const r = await fetch(BASE + `/api/desk/klines?symbol=${symbol}&interval=${interval}`, {cache:'no-store'});
    const d = await r.json();
    bars = d.bars || [];
    overlay = d.overlay || null;
    drawSigs();
    drawChart();
  } catch(e){ bars = []; }
}

async function openTrade(){
  if (busy) return;
  const amt = +$('amt').value;
  if (!(amt >= 1 && amt <= 500)) return;
  if (!quote || !quote.ok){ $('qline').className='desk-quote bad'; $('qline').textContent='Önce canlı kotasyon gelsin'; return; }
  const msg = `GERÇEK PARA — ${symbol.replace('USDT','')} ${dir} $${amt.toFixed(0)}\n`
    + `${money(quote.to_win)} to win · gerçek risk ~${money(quote.spent)} @ ${(+quote.price).toFixed(2)}`;
  if (!confirm(msg)) return;
  busy = true; $('bOpen').disabled = true; $('bOpen').textContent = 'Gönderiliyor…';
  try{
    const r = await fetch(BASE + '/api/desk/open', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({symbol, period, dir, amount: amt}),
    });
    const d = await r.json();
    if (!r.ok || !d.ok) throw new Error(d.error || 'emir başarısız');
    await loadSnap();
  } catch(e){
    $('qline').className='desk-quote bad';
    $('qline').textContent = e.message;
  } finally {
    busy = false; $('bOpen').disabled = false; $('bOpen').textContent = 'İşlem Aç';
  }
}

async function closePos(id){
  if (busy) return;
  if (!confirm('Bu işlemi CLOB bid yürüyüşüyle sat? (yalnızca bu ekranın payı)')) return;
  busy = true;
  try{
    const r = await fetch(BASE + '/api/desk/close', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({id}),
    });
    const d = await r.json();
    if (!r.ok || !d.ok) throw new Error(d.error || 'kapanmadı');
    if (d.settled){
      const p = d.pnl == null ? '' : ((d.pnl >= 0 ? '+' : '') + Number(d.pnl).toFixed(2) + '$');
      alert('Slot bitmişti, satış yok — sonuç yazıldı ' + p);
    }
    await loadSnap();
  } catch(e){
    alert(e.message);
  } finally { busy = false; }
}

function renderCons(d){
  const el = $('cons'); if (!el) return;
  if (!d || !d.ok){ el.innerHTML = ''; return; }
  const coins = (d.coins || []).map(c => {
    const up = c.dir === 'UP';
    return `<span class="cons-chip ${up ? 'up' : 'dn'}"><b>${c.symbol} ${c.label || ''}</b><em>↑${c.up} ↓${c.down}</em><i>%${Math.round(+c.wr || 0)}</i></span>`;
  }).join('');
  const st = d.stats || {};
  const slot = (d.slot_open_tr || '') + (d.books != null ? ` · ${d.books} defter` : '');
  el.innerHTML = `<span class="cons-slot">:${String(d.slot ?? '').padStart(2,'0')} ${slot}</span>${coins}<span class="cons-wr">${st.label || ''}</span>`;
}

async function loadCons(){
  try{
    const r = await fetch(BASE + '/api/consensus', {cache:'no-store'});
    if (r.status === 401) return;
    renderCons(await r.json());
  } catch(e){}
}

function fmtSd(n){
  if (n == null) return '—';
  const x = +n;
  if (x >= 1000) return '$' + x.toFixed(1);
  if (x >= 100) return '$' + x.toFixed(2);
  return '$' + x.toFixed(3);
}

function drawSigs(){
  const el = $('sigs');
  if (!el) return;
  const ov = overlay;
  if (!ov || !ov.ok){ el.innerHTML = ''; return; }
  const sc = ov.mum_skor|0;
  const s = ov.support != null ? 'S ' + fmtSd(ov.support) : '';
  const d = ov.resistance != null ? 'D ' + fmtSd(ov.resistance) : '';
  el.innerHTML = `<span class="desk-mum">Mum skor ${sc} · ${[s,d].filter(Boolean).join(' · ')}</span>`;
}

function drawChart(){
  const c = $('deskChart');
  if (!c) return;
  const dpr = window.devicePixelRatio || 1;
  const w = c.clientWidth, h = c.clientHeight;
  if (w < 40 || h < 40) return;
  c.style.width = w + 'px';
  c.style.height = h + 'px';
  c.width = Math.floor(w * dpr); c.height = Math.floor(h * dpr);
  const ctx = c.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.clearRect(0,0,w,h);
  ctx.fillStyle = '#0F111A';
  ctx.fillRect(0,0,w,h);
  if (!bars.length){
    ctx.fillStyle = '#636b7e';
    ctx.font = '13px Inter,sans-serif';
    ctx.fillText('grafik yükleniyor…', 16, 28);
    return;
  }
  const padL = 8, padR = 78, padT = 12, volH = Math.floor(h * 0.18);
  const ch = h - volH - 28 - padT;
  const n = bars.length;
  const mid = bars[n-1].c;
  const lvPrices = [];
  if (overlay && overlay.ok){
    if (overlay.support != null && Math.abs(overlay.support - mid) / mid < 0.025) lvPrices.push(overlay.support);
    if (overlay.resistance != null && Math.abs(overlay.resistance - mid) / mid < 0.025) lvPrices.push(overlay.resistance);
  }
  const hi = Math.max(...bars.map(b => b.h), ...lvPrices);
  const lo = Math.min(...bars.map(b => b.l), ...lvPrices);
  const span = Math.max(1e-8, hi - lo);
  const m = mktOf(symbol);
  const ref = m && m.spot_open;
  const yOf = v => padT + (1 - (v - lo) / span) * ch;
  const bw = Math.max(2, (w - padL - padR) / n - 1.4);
  ctx.strokeStyle = 'rgba(255,255,255,.05)';
  ctx.lineWidth = 1;
  for (let i = 0; i < 5; i++){
    const y = padT + ch * i / 4;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(w-padR, y); ctx.stroke();
  }
  const last = bars[n-1].c;
  const tags = [];
  const addLine = (px, col) => {
    if (px == null || px < lo || px > hi) return null;
    const y = yOf(px);
    ctx.setLineDash([]);
    ctx.strokeStyle = col;
    ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(w-padR, y); ctx.stroke();
    return y;
  };
  if (overlay && overlay.ok){
    const yr = addLine(overlay.resistance, '#f472b6');
    if (yr != null) tags.push({y: yr, bg:'#f472b6', fg:'#2a0a18', title:'Direnç', px: overlay.resistance});
    const ys = addLine(overlay.support, '#4ade80');
    if (ys != null) tags.push({y: ys, bg:'#4ade80', fg:'#052e16', title:'Destek', px: overlay.support});
  }
  if (ref != null && ref >= lo && ref <= hi){
    const y = addLine(ref, '#f59e0b');
    if (y != null) tags.push({y, bg:'#f59e0b', fg:'#1c1004', title:'Ref', px: ref});
  }
  tags.push({y: yOf(last), bg:'#C1FF72', fg:'#11140C', title:'', px: last, last: true});
  tags.sort((a,b) => a.y - b.y);
  const gap = 36;
  for (let i = 1; i < tags.length; i++){
    if (tags[i].y - tags[i-1].y < gap) tags[i].y = tags[i-1].y + gap;
  }
  for (let i = tags.length - 2; i >= 0; i--){
    if (tags[i+1].y - tags[i].y < gap) tags[i].y = tags[i+1].y - gap;
  }
  const vmax = Math.max(1, ...bars.map(b => b.v));
  bars.forEach((b, i) => {
    const x = padL + i * (w - padL - padR) / n;
    const up = b.c >= b.o;
    const col = up ? '#22c55e' : '#ef4444';
    ctx.strokeStyle = col; ctx.fillStyle = col;
    ctx.beginPath();
    ctx.moveTo(x + bw/2, yOf(b.h)); ctx.lineTo(x + bw/2, yOf(b.l)); ctx.stroke();
    const y1 = yOf(Math.max(b.o, b.c)), y2 = yOf(Math.min(b.o, b.c));
    ctx.fillRect(x, y1, bw, Math.max(1, y2-y1));
    const vh = (b.v / vmax) * volH;
    ctx.globalAlpha = .55;
    ctx.fillRect(x, h - 10 - vh, bw, vh);
    ctx.globalAlpha = 1;
  });
  tags.forEach(t => {
    const th = t.last ? 20 : 34;
    ctx.fillStyle = t.bg;
    ctx.fillRect(w-padR+2, t.y - th/2, padR-4, th);
    ctx.fillStyle = t.fg;
    if (t.last){
      ctx.font = '700 11px Inter,sans-serif';
      ctx.fillText(fmtPx(t.px), w-padR+8, t.y + 4);
    } else {
      ctx.font = '700 9px Inter,sans-serif';
      ctx.fillText(t.title, w-padR+8, t.y - 3);
      ctx.font = '700 11px Inter,sans-serif';
      ctx.fillText(fmtPx(t.px), w-padR+8, t.y + 12);
    }
  });
  $('nowLbl').textContent = fmtPx(last);
}

$('bUp').onclick = () => setDir('UP');
$('bDn').onclick = () => setDir('DOWN');
$('bOpen').onclick = openTrade;
$('amt').oninput = () => { quote = null; drawQuote(); loadQuote(); };
$('mDash').onclick = () => location.href = BASE + '/';
$('mSet').onclick = () => location.href = BASE + '/ayarlar';
window.addEventListener('resize', drawChart);
drawTabs();
loadSnap(); loadQuote(); loadBars(); loadCons(); startSnapStream();
setInterval(loadQuote, 1000);
setInterval(loadBars, 10000);
setInterval(loadCons, 60000);
</script></body></html>"""

ANALIZ = r"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{{ base }}/favicon.ico" type="image/svg+xml">
<link rel="stylesheet" href="{{ base }}/static/coptc.css?v={{ static_ver }}">
<title>{{ app_name }} — Grafik Analiz</title>
</head><body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-icon">C</div>
      <div><div class="brand-name">CemAPI</div><div class="brand-sub">Live Control</div></div>
    </div>
    <nav class="nav">
      <a class="nav-item" href="{{ base }}/">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg>
        Dashboard
      </a>
      <a class="nav-item" href="{{ base }}/islemler">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-6 6"/></svg>
        İşlemler
      </a>
      <a class="nav-item" href="{{ base }}/algoritma-islemler">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        Algoritma İşlemler
      </a>
      <a class="nav-item{% if nav_on=='live' %} on{% endif %}" href="{{ base }}/live">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M5 5a10 10 0 0 1 14 0M3 3a13 13 0 0 1 18 0M8.5 8.5a5 5 0 0 1 7 0"/></svg>
        LIVE
        <span class="nav-live-dot"></span>
      </a>
      <a class="nav-item on" href="{{ base }}/grafik-analiz">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19V9M10 19V5M16 19v-7M22 19V3"/></svg>
        Grafik Analiz
      </a>
      <a class="nav-item" href="{{ base }}/ayarlar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        Ayarlar
      </a>
    </nav>
    <div class="sidebar-foot"><b>1H Confluence</b>4H trend · CVD · OI · ATR kapısı — emir yok.</div>
  </aside>
  <div class="main desk-page">
    <header class="topbar">
      <div><h1>Grafik Analiz <span class="ga-sym" id="gaSym">BTC</span></h1></div>
      <div class="topbar-actions">
        <div class="desk-iv" id="ivs"></div>
        <span class="ga-sig" id="gaSig"></span>
        <span class="clock" id="clock">—</span>
      </div>
      <div class="topbar-mobile">
        <button type="button" class="btn" id="mDash">Dashboard</button>
        <button type="button" class="btn" id="mDesk">İşlemler</button>
      </div>
    </header>
    <div class="ga">
      <div class="ga-chart">
        <div class="ga-conf" id="gaConf"></div>
        <canvas class="desk-chart" id="deskChart"></canvas>
        <div class="ga-osc-wrap">
          <div class="ga-osc-bar">
            <b>MVRVZ-Risk</b>
            <span id="mvrvzLbl">—</span>
          </div>
          <canvas class="ga-osc" id="mvrvzChart"></canvas>
        </div>
      </div>
      <aside class="ga-coins">
        <div class="ga-coins-head">
          <input id="qcoin" type="search" placeholder="Ara…" autocomplete="off">
          <span class="ga-coins-n" id="coinN"></span>
        </div>
        <div class="ga-coin-list" id="coins">yükleniyor…</div>
      </aside>
    </div>
  </div>
</div>
<script>
const BASE = {{ base|tojson }};
const $ = id => document.getElementById(id);
const PINS = [['BTCUSDT','BTC'],['ETHUSDT','ETH'],['SOLUSDT','SOL']];
const IVS = ['1m','5m','15m','1h'];
let symbol = 'BTCUSDT', interval = '1h', bars = [], coins = [], mvrvz = null, conf = null;

function fmtPx(n){
  if (n == null) return '—';
  const x = +n;
  return x >= 1000 ? x.toFixed(1) : x >= 100 ? x.toFixed(2) : x >= 1 ? x.toFixed(3) : x.toFixed(6);
}

function baseOf(sym){
  const hit = coins.find(c => c.symbol === sym);
  if (hit) return hit.base;
  const pin = PINS.find(([s]) => s === sym);
  return pin ? pin[1] : String(sym || '').replace(/USDT$/, '');
}

function syncTitle(){
  const el = $('gaSym');
  if (el) el.textContent = baseOf(symbol);
}

function setSymbol(s){
  if (!s || s === symbol) { syncTitle(); drawCoins(); return; }
  symbol = s;
  syncTitle(); drawCoins(); loadBars(); loadMvrvz(); loadConf();
}

function drawTabs(){
  $('ivs').innerHTML = IVS.map(iv =>
    `<button type="button" class="desk-ivb${iv===interval?' on':''}" data-iv="${iv}">${iv}</button>`).join('');
  $('ivs').onclick = e => {
    const b = e.target.closest('[data-iv]'); if (!b) return;
    interval = b.dataset.iv; drawTabs(); loadBars();
  };
}

function drawCoins(){
  const q = (($('qcoin') && $('qcoin').value) || '').trim().toLowerCase();
  let rows = coins;
  if (q) rows = coins.filter(c =>
    (c.base || '').toLowerCase().includes(q) || (c.symbol || '').toLowerCase().includes(q));
  if ($('coinN')) $('coinN').textContent = rows.length ? rows.length + ' çift' : '';
  if (!rows.length){
    $('coins').innerHTML = '<span style="color:#636b7e;font-size:12px;padding:8px">eşleşme yok</span>';
    return;
  }
  $('coins').innerHTML = rows.map(c => {
    const chg = +c.chg || 0;
    const cls = chg > 0 ? 'up' : chg < 0 ? 'dn' : '';
    const txt = (chg > 0 ? '+' : '') + chg.toFixed(2) + '%';
    return `<button type="button" class="ga-coin${c.symbol===symbol?' on':''}" data-s="${c.symbol}">
      <b>${c.base}</b>
      <span class="px">${fmtPx(c.price)}</span>
      <span class="chg ${cls}">${txt}</span>
    </button>`;
  }).join('');
}

async function loadCoins(){
  try{
    const r = await fetch(BASE + '/api/desk/futures', {cache:'no-store'});
    if (r.status === 401) return location.href = BASE + '/giris';
    const d = await r.json();
    coins = d.symbols || [];
    if (!coins.length){
      coins = PINS.map(([s,l]) => ({symbol:s, base:l, price:0, chg:0}));
    }
    drawCoins(); syncTitle();
  } catch(e){
    coins = PINS.map(([s,l]) => ({symbol:s, base:l, price:0, chg:0}));
    drawCoins(); syncTitle();
  }
}

async function loadBars(){
  try{
    const r = await fetch(BASE + `/api/desk/klines?symbol=${symbol}&interval=${interval}&overlay=0`, {cache:'no-store'});
    if (r.status === 401) return location.href = BASE + '/giris';
    const d = await r.json();
    bars = d.bars || [];
    $('clock').textContent = new Date().toLocaleString('tr-TR');
    drawChart();
  } catch(e){}
}

async function loadMvrvz(){
  try{
    const r = await fetch(BASE + `/api/desk/mvrvz?symbol=${symbol}`, {cache:'no-store'});
    if (r.status === 401) return location.href = BASE + '/giris';
    mvrvz = await r.json();
    const el = $('mvrvzLbl');
    if (el){
      if (!mvrvz || !mvrvz.ok){ el.textContent = 'veri yok'; el.className = ''; }
      else {
        const v = (+mvrvz.risk).toFixed(2);
        const cls = mvrvz.al ? 'al' : mvrvz.sat ? 'sat' : (mvrvz.risk >= 0.70 ? 'hi' : mvrvz.risk <= 0.20 ? 'lo' : '');
        const tag = mvrvz.al ? ' · AL' : mvrvz.sat ? ' · SAT' : '';
        el.className = cls;
        el.textContent = `${v}${tag}  Z ${(+mvrvz.z).toFixed(2)}`;
      }
    }
    drawOsc();
  } catch(e){}
}

function clsDir(v){
  if (v === 'YUKARI') return 'up';
  if (v === 'AŞAĞI') return 'dn';
  if (v === 'AÇIK') return 'ok';
  if (v === 'KAPALI') return 'off';
  return '';
}

function drawConfPanel(){
  const el = $('gaConf');
  if (!el) return;
  if (!conf || !conf.ok){
    el.innerHTML = '<table><tr><th>Bileşen</th><th>Durum</th></tr><tr><td colspan="2">yükleniyor…</td></tr></table>';
    return;
  }
  const vol = conf.vol_ok ? 'AÇIK' : 'KAPALI';
  const cvdL = (conf.cvd === 'n/a') ? 'CVD Bias (n/a)' : 'CVD Bias';
  const oiL = (conf.oi === 'n/a') ? 'OI Rejimi (n/a)' : 'OI Rejimi';
  el.innerHTML = `<table>
    <tr><th>Bileşen</th><th>Durum</th></tr>
    <tr><td>HTF Trend</td><td class="${clsDir(conf.htf)}">${conf.htf}</td></tr>
    <tr><td>${cvdL}</td><td class="${clsDir(conf.cvd)}">${conf.cvd}</td></tr>
    <tr><td>${oiL}</td><td class="${clsDir(conf.oi)}">${conf.oi}</td></tr>
    <tr><td>Vol. Filtresi</td><td class="${clsDir(vol)}">${vol}</td></tr>
    <tr><td>Skor (Bull/Bear)</td><td>${conf.bull_score} / ${conf.bear_score}</td></tr>
  </table>`;
  const sg = $('gaSig');
  if (sg){
    if (conf.long){ sg.textContent = 'YUKARI'; sg.className = 'ga-sig up'; }
    else if (conf.short){ sg.textContent = 'AŞAĞI'; sg.className = 'ga-sig dn'; }
    else { sg.textContent = ''; sg.className = 'ga-sig'; }
  }
}

function confAt(t){
  const rows = (conf && conf.bars) || [];
  if (!rows.length) return null;
  const hour = t - (t % 3600000);
  let hit = null;
  for (let i = 0; i < rows.length; i++){
    if (rows[i].t <= hour) hit = rows[i];
    else break;
  }
  return hit;
}

async function loadConf(){
  try{
    const r = await fetch(BASE + `/api/desk/confluence?symbol=${symbol}`, {cache:'no-store'});
    if (r.status === 401) return location.href = BASE + '/giris';
    conf = await r.json();
    drawConfPanel();
    drawChart();
  } catch(e){}
}

function drawOsc(){
  const c = $('mvrvzChart'); if (!c) return;
  const dpr = window.devicePixelRatio || 1;
  const w = c.clientWidth, h = c.clientHeight;
  if (w < 40 || h < 30) return;
  c.style.width = w + 'px'; c.style.height = h + 'px';
  c.width = Math.floor(w * dpr); c.height = Math.floor(h * dpr);
  const ctx = c.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.fillStyle = '#0F111A'; ctx.fillRect(0,0,w,h);
  const rows = (mvrvz && mvrvz.bars) || [];
  if (!rows.length){
    ctx.fillStyle = '#636b7e'; ctx.font = '12px Inter,sans-serif';
    ctx.fillText('MVRVZ yükleniyor…', 12, 22);
    return;
  }
  const padL = 8, padR = 48, padT = 8, padB = 14;
  const cw = w - padL - padR, ch = h - padT - padB;
  const yOf = v => padT + (1 - v) * ch;
  const xOf = i => padL + i * cw / Math.max(1, rows.length - 1);
  ctx.fillStyle = 'rgba(239,68,68,.10)';
  ctx.fillRect(padL, yOf(1), cw, yOf(0.70) - yOf(1));
  ctx.fillStyle = 'rgba(34,197,94,.10)';
  ctx.fillRect(padL, yOf(0.20), cw, yOf(0) - yOf(0.20));
  const lines = [[1,'#ef444466'],[0.70,'#f59e0b88'],[0.50,'#ffffff22'],[0.20,'#22c55e88'],[0,'#22c55e66']];
  ctx.font = '10px Inter,sans-serif';
  lines.forEach(([v, col]) => {
    const y = yOf(v);
    ctx.strokeStyle = col; ctx.setLineDash(v === 0.50 ? [2,3] : (v === 0.70 || v === 0.20 ? [4,3] : []));
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(w - padR, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#8b93a7';
    ctx.fillText(v.toFixed(2), w - padR + 6, y + 3);
  });
  ctx.lineWidth = 1.2; ctx.strokeStyle = 'rgba(234,179,8,.75)';
  ctx.beginPath();
  rows.forEach((b, i) => { const x = xOf(i), y = yOf(b.signal); i ? ctx.lineTo(x,y) : ctx.moveTo(x,y); });
  ctx.stroke();
  ctx.lineWidth = 2;
  for (let i = 1; i < rows.length; i++){
    const a = rows[i-1], b = rows[i];
    const risk = b.risk;
    ctx.strokeStyle = risk > 0.70 ? '#ef4444' : risk < 0.20 ? '#22c55e' : (risk > b.signal ? '#22d3ee' : '#f59e0b');
    ctx.beginPath(); ctx.moveTo(xOf(i-1), yOf(a.risk)); ctx.lineTo(xOf(i), yOf(b.risk)); ctx.stroke();
  }
  rows.forEach((b, i) => {
    if (!b.al && !b.sat) return;
    const x = xOf(i);
    ctx.beginPath();
    if (b.al){
      ctx.fillStyle = '#22c55e';
      ctx.moveTo(x, h - 3); ctx.lineTo(x - 5, h - 12); ctx.lineTo(x + 5, h - 12);
    } else {
      ctx.fillStyle = '#ef4444';
      ctx.moveTo(x, padT + 2); ctx.lineTo(x - 5, padT + 11); ctx.lineTo(x + 5, padT + 11);
    }
    ctx.closePath(); ctx.fill();
  });
  const last = rows[rows.length - 1];
  const ly = yOf(last.risk);
  ctx.fillStyle = last.risk > 0.70 ? '#FF4D8D' : last.risk < 0.20 ? '#C1FF72' : '#FFB347';
  ctx.fillRect(w - padR + 2, ly - 8, padR - 4, 16);
  ctx.fillStyle = '#fff'; ctx.font = '700 10px Inter,sans-serif';
  ctx.fillText((+last.risk).toFixed(2), w - padR + 6, ly + 3);
}

function drawChart(){
  const c = $('deskChart'); if (!c) return;
  const dpr = window.devicePixelRatio || 1;
  const w = c.clientWidth, h = c.clientHeight;
  if (w < 40 || h < 40) return;
  c.style.width = w + 'px'; c.style.height = h + 'px';
  c.width = Math.floor(w * dpr); c.height = Math.floor(h * dpr);
  const ctx = c.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.fillStyle = '#0F111A'; ctx.fillRect(0,0,w,h);
  if (!bars.length){ ctx.fillStyle='#636b7e'; ctx.font='13px Inter,sans-serif'; ctx.fillText('grafik yükleniyor…',16,28); return; }
  const padL = 8, padR = 62, padT = 12, volH = Math.floor(h * 0.16);
  const ch = h - volH - 28 - padT;
  const n = bars.length, last = bars[n-1].c;
  let hi = Math.max(...bars.map(b => b.h));
  let lo = Math.min(...bars.map(b => b.l));
  bars.forEach(b => {
    const cf = confAt(b.t);
    if (!cf) return;
    if (cf.ema_fast != null){ hi = Math.max(hi, cf.ema_fast); lo = Math.min(lo, cf.ema_fast); }
    if (cf.ema_slow != null){ hi = Math.max(hi, cf.ema_slow); lo = Math.min(lo, cf.ema_slow); }
  });
  const span = Math.max(1e-8, hi - lo);
  const yOf = v => padT + (1 - (v - lo) / span) * ch;
  const bw = Math.max(2, (w - padL - padR) / n - 1.4);
  const step = (w - padL - padR) / n;
  ctx.strokeStyle = 'rgba(255,255,255,.05)';
  for (let i = 0; i < 5; i++){ const y = padT + ch * i / 4; ctx.beginPath(); ctx.moveTo(padL,y); ctx.lineTo(w-padR,y); ctx.stroke(); }
  bars.forEach((b, i) => {
    const cf = confAt(b.t);
    if (!cf) return;
    const x = padL + i * step;
    if (cf.long){ ctx.fillStyle = 'rgba(34,197,94,.12)'; ctx.fillRect(x, padT, step, ch); }
    else if (cf.short){ ctx.fillStyle = 'rgba(239,68,68,.12)'; ctx.fillRect(x, padT, step, ch); }
  });
  const vmax = Math.max(1, ...bars.map(b => b.v));
  bars.forEach((b, i) => {
    const x = padL + i * step;
    const col = b.c >= b.o ? '#22c55e' : '#ef4444';
    ctx.strokeStyle = col; ctx.fillStyle = col;
    ctx.beginPath(); ctx.moveTo(x+bw/2, yOf(b.h)); ctx.lineTo(x+bw/2, yOf(b.l)); ctx.stroke();
    const y1 = yOf(Math.max(b.o,b.c)), y2 = yOf(Math.min(b.o,b.c));
    ctx.fillRect(x, y1, bw, Math.max(1, y2-y1));
    ctx.globalAlpha = .55; ctx.fillRect(x, h-10-(b.v/vmax)*volH, bw, (b.v/vmax)*volH); ctx.globalAlpha = 1;
  });
  function lineOf(key, col){
    ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.beginPath();
    let started = false;
    bars.forEach((b, i) => {
      const cf = confAt(b.t);
      const v = cf && cf[key];
      if (v == null){ started = false; return; }
      const x = padL + i * step + bw / 2, y = yOf(v);
      if (!started){ ctx.moveTo(x, y); started = true; }
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
  lineOf('ema_fast', '#14b8a6');
  lineOf('ema_slow', '#f59e0b');
  bars.forEach((b, i) => {
    const cf = confAt(b.t);
    if (!cf) return;
    const prevT = i ? bars[i-1].t : -1;
    const hour = b.t - (b.t % 3600000);
    const prevH = prevT >= 0 ? prevT - (prevT % 3600000) : -1;
    if (hour === prevH) return;
    const x = padL + i * step + bw / 2;
    if (cf.long_new){
      ctx.fillStyle = '#22c55e';
      ctx.beginPath();
      ctx.moveTo(x, yOf(b.l) + 12);
      ctx.lineTo(x - 6, yOf(b.l) + 22);
      ctx.lineTo(x + 6, yOf(b.l) + 22);
      ctx.closePath(); ctx.fill();
    }
    if (cf.short_new){
      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.moveTo(x, yOf(b.h) - 12);
      ctx.lineTo(x - 6, yOf(b.h) - 22);
      ctx.lineTo(x + 6, yOf(b.h) - 22);
      ctx.closePath(); ctx.fill();
    }
  });
  const y = yOf(last);
  ctx.fillStyle = '#C1FF72';
  ctx.fillRect(w-padR+2, y-9, padR-4, 18);
  ctx.fillStyle = '#11140C'; ctx.font = '700 11px Inter,sans-serif';
  ctx.fillText(fmtPx(last), w-padR+8, y+4);
}

$('mDash').onclick = () => location.href = BASE + '/';
$('mDesk').onclick = () => location.href = BASE + '/islemler';
$('coins').onclick = e => {
  const b = e.target.closest('[data-s]'); if (!b) return;
  setSymbol(b.dataset.s);
};
$('qcoin').oninput = drawCoins;
window.addEventListener('resize', () => { drawChart(); drawOsc(); });
drawTabs(); loadCoins(); loadBars(); loadMvrvz(); loadConf();
setInterval(loadBars, 10000);
setInterval(loadCoins, 60000);
setInterval(loadMvrvz, 60000);
setInterval(loadConf, 20000);
</script></body></html>"""

_ALG_NAV = r"""      <a class="nav-item" href="{{ base }}/">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg>
        Dashboard
      </a>
      <a class="nav-item" href="{{ base }}/islemler">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-6 6"/></svg>
        İşlemler
      </a>
      <a class="nav-item{% if nav_on!='live' %} on{% endif %}" href="{{ base }}/algoritma-islemler">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        Algoritma İşlemler
      </a>
      <a class="nav-item{% if nav_on=='live' %} on{% endif %}" href="{{ base }}/live">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M5 5a10 10 0 0 1 14 0M3 3a13 13 0 0 1 18 0M8.5 8.5a5 5 0 0 1 7 0"/></svg>
        LIVE
        <span class="nav-live-dot"></span>
      </a>
      <a class="nav-item" href="{{ base }}/grafik-analiz">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19V9M10 19V5M16 19v-7M22 19V3"/></svg>
        Grafik Analiz
      </a>
      <a class="nav-item" href="{{ base }}/ayarlar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        Ayarlar
      </a>"""

ALGOS = r"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{{ base }}/favicon.ico" type="image/svg+xml">
<link rel="stylesheet" href="{{ base }}/static/coptc.css?v={{ static_ver }}">
<title>{{ app_name }} — Algoritma İşlemler</title>
</head><body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-icon">C</div>
      <div><div class="brand-name">CemAPI</div><div class="brand-sub">Live Control</div></div>
    </div>
    <nav class="nav">""" + _ALG_NAV + r"""
    </nav>
    <div class="sidebar-foot"><b>Sanal Binance</b>$1000 bakiye · $100×10x · max 6 — gerçek emir yok.</div>
  </aside>
  <div class="main alg-page">
    <header class="topbar">
      <div>
        <h1>Algoritma İşlemler</h1>
        <div class="topbar-sub" id="sub">sanal Binance yükleniyor…</div>
      </div>
      <div class="topbar-actions">
        <span class="alg-topstat" id="topstat">—</span>
        <button type="button" class="btn auto-btn" id="autoBtn" title="Açıkken en çok kazanan defter otomatik seçilir">Otoseçim —</button>
        <span class="clock" id="clock">—</span>
      </div>
      <div class="topbar-mobile">
        <button type="button" class="btn" id="mDash">Dashboard</button>
        <button type="button" class="btn" id="mDesk">İşlemler</button>
      </div>
    </header>
    <div class="alg-wrap">
      <div class="alg-grid" id="grid"></div>
      <aside class="alg-side">
        <div class="alg-side-hd alg-side-hd-row">
          <span id="loseHd">EN ÇOK ZARAR EDEN</span>
          <button type="button" class="btn btn-sm" id="pnlBtn">Kâr</button>
        </div>
        <div class="alg-pend" id="losers"></div>
        <div class="alg-side-hd" id="pendHd">İŞLEM BEKLEYEN</div>
        <div class="alg-pend" id="pend"></div>
      </aside>
    </div>
  </div>
</div>
<script>
const BASE = {{ base|tojson }};
const BOOT = {{ boot|tojson }};
const $ = id => document.getElementById(id);
const money = (n, s=true) => {
  const v = Number(n||0);
  const t = (v<0?'-':'') + '$' + Math.abs(v).toFixed(2);
  return s ? `<span class="${v>0?'up':v<0?'dn':''}">${v>0?'+':''}${t.replace('-','')}</span>` : t;
};
const signed = n => {
  const v = Number(n||0);
  const t = (v>0?'+':'') + v.toFixed(2);
  return `<span class="${v>0?'up':v<0?'dn':''}">${t}</span>`;
};
function tick(){ $('clock').textContent = new Date().toLocaleTimeString('tr-TR'); }
let showWin = false;
const lastPnl = {losers: [], winners: []};
function paintPnl(){
  const rows = showWin ? lastPnl.winners : lastPnl.losers;
  const hd = $('loseHd');
  const btn = $('pnlBtn');
  if (hd) hd.textContent = (showWin ? 'EN ÇOK KÂR EDEN' : 'EN ÇOK ZARAR EDEN') + ' — ' + rows.length + ' COİN';
  if (btn) btn.textContent = showWin ? 'Zarar' : 'Kâr';
  const box = $('losers');
  if (!box) return;
  const empty = showWin ? 'Kâr eden coin yok' : 'Zarar eden coin yok';
  box.innerHTML = rows.map(c => `<div class="alg-pend-row">
    <b>${c.base}</b>
    <span class="mut">${c.trades||0} işlem · WR ${(c.win_pct||0).toFixed(0)}%</span>
    <span class="alg-dir ${c.net>=0?'up':'dn'}">${signed(c.net)}</span>
  </div>`).join('') || `<div class="mut" style="padding:10px">${empty}</div>`;
}
function bestWrId(rows){
  const ok = (rows||[]).filter(a => (a.trades||0) > 0);
  if (!ok.length) return '';
  ok.sort((a,b) => (b.win_pct||0)-(a.win_pct||0) || (b.trades||0)-(a.trades||0));
  return ok[0].id;
}
function wrRing(pct){
  const r=20, c=2*Math.PI*r, p=Math.max(0,Math.min(100,Number(pct)||0));
  const dash=(p/100)*c;
  return `<svg class="alg-ring" viewBox="0 0 48 48" aria-hidden="true">
    <circle cx="24" cy="24" r="${r}" fill="none" stroke="currentColor" stroke-width="5" opacity=".18"/>
    <circle cx="24" cy="24" r="${r}" fill="none" stroke="currentColor" stroke-width="5"
      stroke-linecap="round" stroke-dasharray="${dash} ${c}" transform="rotate(-90 24 24)"/>
  </svg>`;
}
function card(a, best, i, liveOn){
  const acc = ['lime','cyan','pink','orange'][i%4];
  const wrn = (a.trades||0) ? Number(a.win_pct||0) : 0;
  const wr = (a.trades||0) ? wrn.toFixed(1)+'%' : '—';
  const chips = (a.positions||[]).map(p =>
    `<span class="alg-chip ${p.side==='LONG'?'up':'dn'}">${p.base} ${p.side}</span>`
  ).join('') || '<span class="alg-chip muted">açık yok</span>';
  return `<div class="alg-card acc-${acc}${best?' wr-best':''}${liveOn?' live-src':''}" data-href="${BASE}/algoritma/${encodeURIComponent(a.id)}">
    <div class="alg-card-top">
      <div>
        <div class="alg-kicker">ALGORİTMA</div>
        <div class="alg-name">${a.code}</div>
        <div class="alg-sub">${a.title} · ${a.trades||0} işlem</div>
      </div>
      <div class="alg-ring-box">
        ${wrRing(wrn)}
        <b>${(a.trades||0)?Math.round(wrn):'–'}</b>
      </div>
    </div>
    <div class="alg-hero">
      <span>Bakiye</span>
      <strong>$${a.equity.toFixed(2)}</strong>
    </div>
    <div class="alg-bar"><i style="width:${Math.min(100,wrn)}%"></i></div>
    <div class="alg-metrics">
      <div class="m-pnl"><em>Net P&L</em><b>${signed(a.net_pnl)}</b></div>
      <div class="m-now"><em>Anlık</em><b>${signed(a.unreal)}</b></div>
      <div><em>WR</em><b class="alg-wr">${wr}</b></div>
    </div>
    <div class="alg-card-foot">
      <span class="alg-tag ${a.active?'on':''}">${a.active?'AÇIK':'OFF'}</span>
      <button type="button" class="alg-live-btn${liveOn?' on':''}" data-aid="${a.id}" data-code="${a.code}">${liveOn?'LIVE aktif':'Aktif et'}</button>
      ${chips}
    </div>
  </div>`;
}
function paint(d){
  if (!d || !d.ok) return;
  try {
  $('sub').textContent = d.subtitle || '';
  $('topstat').innerHTML = `Net P&L ${signed(d.net_pnl)} · kom. ${signed(-Math.abs(d.fees||0))} · Açık: ${d.open_n||0}`;
  const rows = (d.algos||[]).slice().sort((a,b)=> (b.equity||0)-(a.equity||0));
  const top = bestWrId(rows);
  const follow = d.live_follow || '';
  paintAuto(d.live_auto !== false, rows, follow);
  $('grid').innerHTML = rows.map((a,i) => card(a, a.id===top, i, a.id===follow)).join('') || '<div class="mut">ALG klasörü boş</div>';
  lastPnl.losers = d.losers||[];
  lastPnl.winners = d.winners||[];
  paintPnl();
  const pend = d.pending||[];
  $('pendHd').textContent = 'İŞLEM BEKLEYEN — ' + pend.length + ' SİNYAL — ' + (d.coin_n||0) + ' COİN (Grafik Analiz)';
  $('pend').innerHTML = pend.map(p => `<div class="alg-pend-row">
    <b>${p.base}</b>
    <span class="mut">${p.note||''}</span>
    <span class="alg-dir ${p.side==='LONG'?'up':'dn'}">${p.side==='LONG'?'çıkar':'düşer'}</span>
  </div>`).join('') || '<div class="mut" style="padding:10px">Tarama bekleniyor…</div>';
  } catch (e) {}
}
let busy = false;
let poller = 0;
async function load(){
  if (busy) return;
  busy = true;
  try {
  const r = await fetch(BASE + '/api/algo/overview', {cache:'no-store', signal: AbortSignal.timeout(8000)});
  if (r.status === 401) return location.href = BASE + '/giris';
  if (!r.ok) return;
  paint(await r.json());
  } catch (e) {}
  finally { busy = false; }
}
let es = null, esBackoff = 1000, esLast = Date.now();
function startStream(){
  try { if (es) es.close(); } catch (e) {}
  es = new EventSource(BASE + '/api/algo/overview/stream');
  es.onopen = () => {
    esBackoff = 1000; esLast = Date.now();
    if (poller) { clearInterval(poller); poller = 0; }
  };
  es.onmessage = ev => {
    esLast = Date.now(); esBackoff = 1000;
    if (poller) { clearInterval(poller); poller = 0; }
    try { paint(JSON.parse(ev.data)); } catch (e) {}
  };
  es.onerror = () => {
    if (!poller) poller = setInterval(load, 8000);
    if (es && es.readyState === EventSource.CLOSED){
      setTimeout(startStream, esBackoff);
      esBackoff = Math.min(esBackoff * 2, 30000);
    }
  };
}
setInterval(() => {
  if (Date.now() - esLast > 25000){ esLast = Date.now(); startStream(); }
}, 5000);
$('grid').onclick = e => {
  const btn = e.target.closest('.alg-live-btn');
  if (btn) { e.preventDefault(); e.stopPropagation(); setLiveFollow(btn); return; }
  const cardEl = e.target.closest('.alg-card[data-href]');
  if (cardEl) location.href = cardEl.dataset.href;
};
let autoOn = true;
function paintAuto(on, rows, follow){
  autoOn = !!on;
  const b = $('autoBtn');
  if (!b) return;
  const cur = (rows||[]).find(a => a.id === follow);
  const ad = cur ? cur.code : '—';
  b.textContent = 'Otoseçim: ' + (on ? 'AÇIK' : 'KAPALI');
  b.classList.toggle('on', on);
  b.title = on
    ? 'En çok kazanan defter otomatik seçiliyor. Kapatırsan ' + ad + ' üzerinde sabit kalır.'
    : ad + ' üzerinde sabit. Aç = en çok kazanana otomatik geç.';
}
$('autoBtn').onclick = async () => {
  const next = !autoOn;
  const msg = next
    ? 'Otoseçim açılacak: LIVE en çok kazanan sanal defteri kendisi seçecek ve o defter 10 işlem kapattıkça sıralamaya yeniden bakacak.\n\nAçık LIVE pozisyonlar kapanmaz.'
    : 'Otoseçim kapanacak: LIVE şu an seçili olan algoritmada sabit kalacak.';
  if (!confirm(msg)) return;
  const r = await fetch(BASE + '/api/live/auto-follow', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({on: next}),
  });
  if (r.status === 401) return location.href = BASE + '/giris';
  if (!r.ok) { alert('Otoseçim değiştirilemedi'); return; }
  autoOn = next;
  load();
};
async function setLiveFollow(btn){
  if (btn.classList.contains('on')) return;
  const code = btn.dataset.code || btn.dataset.aid;
  if (!confirm(`LIVE bundan sonra ${code} sanal defterini kopyalayacak.\n\nAçık LIVE pozisyonlar kapanmaz. Yeni açılışlar bu algoritmadan gider.\n\nElle seçim otoseçimi kapatır — seçimin sabit kalır.`)) return;
  const r = await fetch(BASE + '/api/algo/' + encodeURIComponent(btn.dataset.aid) + '/live-follow', {method:'POST'});
  if (r.status === 401) return location.href = BASE + '/giris';
  if (!r.ok) { alert('Aktif edilemedi'); return; }
  load();
}
$('mDash').onclick = () => location.href = BASE + '/';
$('mDesk').onclick = () => location.href = BASE + '/islemler';
$('pnlBtn').onclick = () => { showWin = !showWin; paintPnl(); };
tick(); if (BOOT && BOOT.ok) paint(BOOT); load(); startStream();
setInterval(tick, 1000);
</script></body></html>"""

ALGO_ONE = r"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{{ base }}/favicon.ico" type="image/svg+xml">
<link rel="stylesheet" href="{{ base }}/static/coptc.css?v={{ static_ver }}">
<title>{{ app_name }} — Algoritma</title>
</head><body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-icon">C</div>
      <div><div class="brand-name">CemAPI</div><div class="brand-sub">Live Control</div></div>
    </div>
    <nav class="nav">""" + _ALG_NAV + r"""
    </nav>
    <div class="sidebar-foot">{% if live_mode %}<b>Gerçek Binance</b>$50 × 15x · kâr WR≥60 → $60 × 20x.{% else %}<b>Sanal Binance</b>Pozisyon $100 × 10x. Kapat = kâğıt kapanış.{% endif %}</div>
  </aside>
  <div class="main alg-page">
    <header class="topbar">
      <div>
        <h1 id="ttl">…</h1>
        <div class="topbar-sub" id="sub">—</div>
      </div>
      <div class="topbar-actions">
        {% if live_mode %}<div class="live-bal" id="liveBal"><em>BINANCE USDT</em><b id="liveUsdt">—</b><span id="liveAvail" class="mut"></span></div>{% endif %}
        <span class="alg-topstat" id="topstat">—</span>
        <a class="btn" href="{{ base }}/algoritma-islemler">Liste</a>
        <button class="btn" id="btog">—</button>
      </div>
    </header>
    <div class="live-strip" id="liveStrip" hidden>
      <div><em>Cüzdan</em><b id="lsWallet">—</b></div>
      <div><em>Serbest</em><b id="lsAvail">—</b></div>
      <div><em>Anlık</em><b id="lsUnreal">—</b></div>
      <div><em>Kilitli</em><b id="lsLock">—</b></div>
    </div>
    <div class="alg-detail">
      <div class="alg-sec-hd">AÇIK POZİSYONLAR</div>
      <div class="ap-grid" id="opens"></div>
      <div class="alg-sum" id="sumbar">—</div>
      <div class="alg-sec-hd" id="hhd">GEÇMİŞ İŞLEMLER</div>
      <div class="ap-hist" id="hist"></div>
    </div>
  </div>
</div>
<script>
const BASE = {{ base|tojson }};
const AID = {{ aid|tojson }};
const LIVE = {{ live_mode|tojson }};
const BOOT = {{ boot|tojson }};
const API = LIVE ? (BASE + '/api/algo/live') : (BASE + '/api/algo/' + encodeURIComponent(AID));
const $ = id => document.getElementById(id);
const signed = n => {
  const v = Number(n||0);
  const sign = v>0?'+':v<0?'−':'';
  return `<span class="${v>0?'up':v<0?'dn':''}">${sign}$${Math.abs(v).toFixed(2)}</span>`;
};
function posMove(p){
  const e = Number(p.entry), m = Number(p.mark);
  if (!e) return 0;
  let r = (m - e) / e * 100;
  if (p.side === 'SHORT') r = -r;
  return r;
}
function lockNote(p){
  const rows = Array.isArray(p.trail_log) ? p.trail_log : [];
  const usd = n => {
    const v = Math.round(Number(n||0));
    return (v>=0?'+':'') + v + ' dolar';
  };
  if (rows.length) {
    return rows.map((x,i) => `${i+1}. Stoploss çalıştı ${usd(x.usd)}`).join('<br>');
  }
  const lock = Number(p.sl_usd||0);
  if (p.trail_on && lock>0) return '1. Stoploss çalıştı ' + usd(lock);
  return 'Stoploss henüz çalışmadı';
}
function posCard(p){
  const net = Number(p.net||0);
  const mv = posMove(p);
  const tag = net>0?'KÂR':net<0?'ZARAR':'NÖTR';
  const dirCls = p.side === 'LONG' ? 'dir-up' : (p.side === 'SHORT' ? 'dir-dn' : '');
  const atrNote = lockNote(p);
  return `<div class="ap-card ${dirCls} ${net>0?'is-win':net<0?'is-lose':''}">
    <div class="ap-hd">
      <div><b>${p.base}</b> <span class="alg-dir ${p.side==='LONG'?'up':'dn'}">${p.side}</span></div>
      <button class="btn danger ap-x" data-id="${p.id}">kapat</button>
    </div>
    <div class="ap-px">$${Number(p.mark).toPrecision(6)} <span class="${mv>=0?'up':'dn'}">poz. ${mv>=0?'+':''}${mv.toFixed(2)}%</span> <span class="mut">24s ${Number(p.chg)>=0?'+':''}${Number(p.chg).toFixed(2)}%</span></div>
    <div class="mut">Giriş $${Number(p.entry).toPrecision(6)} · Açılış ${p.opened||'—'} · ${p.mins!=null?p.mins+' dk açık':''}</div>
    <div class="ap-net ${net>0?'win':net<0?'lose':'flat'}">
      <span>${tag}</span>
      <strong>${signed(net)}</strong>
    </div>
    <div class="ap-atr ${p.trail_on?'on':''}">${atrNote}</div>
    <div class="ap-mini">Brüt ${signed(p.gross)} · Komisyon −$${Number(p.commission).toFixed(2)} · Funding ${signed(p.funding||0)} · Net ${signed(p.net)} · marj ${p.pct>=0?'+':''}${Number(p.pct).toFixed(1)}%</div>
    <div class="ap-mini">${LIVE?'Gerçek Binance':'Sanal'} · ${p.mins!=null?p.mins+' dk':''}</div>
  </div>`;
}
function holdTxt(m){
  const n = Number(m||0);
  if (n < 1) return '<1 dk';
  if (n < 60) return n + ' dk';
  const h = Math.floor(n/60), d = n%60;
  return h + 's ' + d + 'dk';
}
function row(h){
  const gir = h.opened || '—';
  const cik = h.closed || h.t || '—';
  return `<div class="ap-row">
    <span class="mut">${cik}</span>
    <b>${h.base}</b>
    <span class="alg-dir ${h.side==='LONG'?'up':'dn'}">${h.side}</span>
    <span class="mut">Giriş ${gir} → Çıkış ${cik} · ${holdTxt(h.mins)} aktif · $${Number(h.entry).toPrecision(6)} → $${Number(h.exit).toPrecision(6)} — ${h.reason} — Kom: $${Number(h.commission).toFixed(2)}${h.funding? ' · fund '+Number(h.funding).toFixed(4):''}</span>
    <strong class="ap-pnl">${signed(h.net)}</strong>
  </div>`;
}
let busy = false;
let painted = false;
function paint(a) {
  if (!a) return;
  try {
  $('ttl').textContent = LIVE ? 'LIVE' : a.code;
  const src = LIVE ? ((a.follow_code || a.title || '') + ' kopyası') : a.title;
  const m = Number(a.margin || (LIVE ? 50 : 100));
  const lv = Number(a.lev || (LIVE ? 15 : 10));
  const sz = LIVE
    ? `$${m.toFixed(0)}×${lv}x · kâr WR≥${Number(a.boost_wr||60)} → $${Number(a.boost_margin||60)}×${Number(a.boost_lev||20)}x`
    : `$${m.toFixed(0)}x${lv}`;
  $('sub').textContent = `${src} — Win % ${a.win_pct} — ${a.trades} işlem — ${sz} — max: 6${a.error?' — '+a.error:''}`;
  if (LIVE && $('liveUsdt')) {
    $('liveUsdt').textContent = '$' + Number(a.wallet||0).toFixed(2);
    $('liveAvail').textContent = 'serbest $' + Number(a.available||0).toFixed(2);
    $('liveBal').classList.toggle('off', !a.connected);
  }
  if ($('liveStrip')) {
    $('liveStrip').hidden = false;
    const wallet = LIVE ? Number(a.wallet||0) : Number(a.equity||0);
    const avail = LIVE ? Number(a.available||0) : Number(a.cash_free||0);
    const unreal = Number(a.unreal||0);
    $('lsWallet').textContent = '$' + wallet.toFixed(2);
    $('lsAvail').textContent = '$' + avail.toFixed(2);
    $('lsUnreal').innerHTML = signed(unreal);
    const lock = LIVE
      ? Math.max(0, wallet - avail)
      : Math.max(0, wallet - avail - unreal);
    $('lsLock').textContent = '$' + lock.toFixed(2);
  }
  $('topstat').innerHTML = LIVE
    ? `Cüzdan: ${Number(a.wallet||0).toFixed(2)} | Anlık: ${signed(a.unreal)} | ${a.connected?'bağlı':'kopuk'}`
    : `Bakiye: ${a.equity.toFixed(2)} | Net PNL: ${signed(a.net_pnl)} | Anlık Net: ${signed(a.unreal)} | Kom: −$${a.fees.toFixed(2)}`;
  $('btog').textContent = a.active ? 'Durdur' : 'Başlat';
  const opens = a.positions||[];
  $('opens').innerHTML = opens.map(posCard).join('') || '<div class="mut">Açık pozisyon yok — tarama 15m sinyal bekliyor.</div>';
  $('sumbar').textContent = `${a.code} — ${a.trades} işlem — ${a.wins} kazanç — Kâr toplam: ${(a.realized>=0?'+':'')+a.realized.toFixed(2)}`;
  $('hhd').textContent = `GEÇMİŞ İŞLEMLER — ${a.code} (${a.trades} TOPLAM)`;
  $('hist').innerHTML = (a.history||[]).map(row).join('') || '<div class="mut">Henüz kapanmış işlem yok.</div>';
  document.querySelectorAll('.ap-x').forEach(btn => {
    btn.onclick = async ev => {
      ev.preventDefault();
      btn.disabled = true;
      await fetch(API + '/close', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({id: btn.dataset.id})
      });
      load();
    };
  });
  painted = true;
  } catch (e) {}
}
async function load(){
  if (busy) return;
  busy = true;
  try {
    const r = await fetch(API, {cache:'no-store', signal: AbortSignal.timeout(8000)});
    if (r.status === 401) return location.href = BASE + '/giris';
    if (!r.ok) return;
    paint(await r.json());
  } catch (e) {}
  finally { busy = false; }
}
$('btog').onclick = async () => {
  await fetch(API + '/toggle', {method:'POST'});
  load();
};
if (BOOT && BOOT.ok !== false && (BOOT.positions || BOOT.code)) paint(BOOT);
load();
setInterval(() => { if (!painted) load(); }, 2500);
const streamUrl = LIVE
  ? (BASE + '/api/algo/live/stream')
  : (BASE + '/api/algo/' + encodeURIComponent(AID) + '/stream');
let es = null, esBackoff = 1000, esPoller = 0, esLast = Date.now();
const esPollOn = () => { if (!esPoller) esPoller = setInterval(load, 5000); };
const esPollOff = () => { if (esPoller) { clearInterval(esPoller); esPoller = 0; } };
function startStream(){
  try { if (es) es.close(); } catch (e) {}
  es = new EventSource(streamUrl);
  es.onopen = () => { esBackoff = 1000; esLast = Date.now(); esPollOff(); };
  es.onmessage = ev => {
    esLast = Date.now(); esBackoff = 1000; esPollOff();
    try {
      const a = JSON.parse(ev.data);
      if (a && a.ok !== false) paint(a);
    } catch (e) {}
  };
  es.onerror = () => {
    // Sunucu yeniden başlarsa vekil bir an 502 döner; tarayıcı bunu ölümcül sayıp
    // bağlantıyı kapatır ve kendiliğinden geri dönmez. Yoklamaya geç, sonra tekrar bağlan.
    esPollOn();
    if (es && es.readyState === EventSource.CLOSED){
      setTimeout(startStream, esBackoff);
      esBackoff = Math.min(esBackoff * 2, 30000);
    }
  };
}
// Bağlantı açık görünüp veri akmıyorsa (takılı vekil) zorla yenile.
setInterval(() => {
  if (Date.now() - esLast > 25000){ esLast = Date.now(); esPollOn(); startStream(); }
}, 5000);
startStream();
</script></body></html>"""

LOGIN = r"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{{ base }}/favicon.ico" type="image/svg+xml">
<link rel="stylesheet" href="{{ base }}/static/coptc.css?v={{ static_ver }}">
<title>{{ app_name }}</title></head>
<body class="login-page">
<form class="login-box" method="post">
  <div class="brand"><div class="brand-icon">C</div><div><div class="brand-name">CemAPI</div><div class="brand-sub">Live Control</div></div></div>
  <div class="mut" style="text-align:center;margin-bottom:8px">Panele giriş yap</div>
  <input type="password" name="p" placeholder="Parola" autofocus>
  <button type="submit">Giriş</button>
  {% if err %}<div class="werr" style="text-align:center;margin-top:8px">Hatalı parola</div>{% endif %}
</form></body></html>"""
