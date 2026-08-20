"""Dashboard HTML şablonları — CoptC Live Control."""

PAGE = r"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{{ base }}/favicon.ico" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{ base }}/static/coptc.css?v={{ static_ver }}">
<title>{{ app_name }}</title>
</head><body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-icon" id="badge">C</div>
      <div><div class="brand-name">CoptC</div><div class="brand-sub">Live Control</div></div>
    </div>
    <nav class="nav">
      <a class="nav-item on" href="{{ base }}/">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg>
        Dashboard
      </a>
      <a class="nav-item" href="{{ base }}/ayarlar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        Ayarlar
      </a>
    </nav>
    <div class="sidebar-foot">
      <b>Mirror modu</b>
      Kaynak defterin pozisyonları otomatik kopyalanır. :02:08–:08 arası 10 sn poll.
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
  const pnlHeroCls = p.no_liquidity ? 'na' : (!hasPnl ? 'flat' : (p.close_pnl > 0 ? 'up' : (p.close_pnl < 0 ? 'dn' : 'flat')));
  const badge = p.badge ? `<span class="ptag${p.book === BOOK ? ' me' : ''}">${p.badge}</span>` : '';
  const srcTag = p.source ? `<span class="ptag src">${p.source}</span>` : '';
  const dirCls = p.dir === 'UP' ? 'up' : (p.dir === 'DOWN' ? 'dn' : '');
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
      <div class="risk-v">${p.no_liquidity ? '—' : money(p.close_val)}</div></div>
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
    <circle cx="60" cy="60" r="54" fill="none" stroke="#1e2230" stroke-width="12"/>
    <circle cx="60" cy="60" r="54" fill="none" stroke="#22c55e" stroke-width="12"
      stroke-dasharray="${wLen} ${c}" stroke-linecap="round"/>
    <circle cx="60" cy="60" r="54" fill="none" stroke="#ef4444" stroke-width="12"
      stroke-dasharray="${lLen} ${c}" stroke-dashoffset="${-wLen}" stroke-linecap="round"/>
  </svg><div class="donut-center"><div class="big">${tot ? Math.round(wp) : 0}%</div><div class="sm">Win rate</div></div>`;
  $('legend').innerHTML = `
    <div class="legend-item"><span class="legend-dot" style="background:#22c55e"></span>Kazanç ${w}</div>
    <div class="legend-item"><span class="legend-dot" style="background:#ef4444"></span>Kayıp ${l}</div>
    <div class="legend-item"><span class="legend-dot" style="background:#3b82f6"></span>Toplam ${tot}</div>
    <div class="legend-item"><span class="legend-dot" style="background:#636b7e"></span>WR ${tot ? Math.round(wp) : 0}%</div>`;
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
    ? `Live açık — yön <b>${d.mirror_short || d.mirror_book || '—'}</b> kaynağından kopyalanır.`
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
    <div class="stat">
      <div class="stat-icon blue">💵</div>
      <div class="stat-label">PM nakit</div>
      <div class="stat-val">${money(d.cash)}</div>
      <div class="stat-foot">${d.cash === null ? 'cüzdan tanımsız' : 'serbest USDC'}</div>
    </div>
    <div class="stat stat-cashout" id="redeemStat" title="Nakde çevir — tıkla">
      <div class="stat-icon blue">↻</div>
      <div class="stat-label">Nakde çevrilecek</div>
      <div class="stat-val" id="redeemVal">${money(d.redeem_pending)}</div>
      <div class="stat-foot" id="redeemFoot">${d.pm_redeem_winners || 0} kazanan · tıkla veya otomatik</div>
    </div>
    <div class="stat">
      <div class="stat-icon ${d.live_pnl < 0 ? 'red' : 'green'}">📈</div>
      <div class="stat-label">Gerçek P&amp;L</div>
      <div class="stat-val${pnlCls}">${money(d.live_pnl)}</div>
      <div class="stat-foot">${d.live_w}W / ${d.live_l}L · defter ${d.pm_book_pnl >= 0 ? '+' : ''}${money(d.pm_book_pnl)}</div>
    </div>
    <div class="stat stat-risk">
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
  $('wpmsub').textContent = d.equity != null
    ? `Anlık toplam ${money(d.equity)} · serbest USDC`
    : (d.cash === null ? 'cüzdan tanımsız' : 'Serbest USDC');
  const wc = document.querySelector('.wallet-card');
  const walletTotal = d.cash != null ? d.cash : d.equity;
  if (wc) {
    wc.classList.toggle('ok', walletTotal != null && walletTotal > 1000);
    wc.classList.toggle('warn', walletTotal != null && walletTotal <= 1000);
  }
  $('wsrc').textContent = d.live_on
    ? `${d.mirror_short || d.mirror_book || '—'} aynası · PM emri açık`
    : 'Live kapalı';

  $('pos').innerHTML = d.positions.length
    ? `<div class="pgrid">${d.positions.map(posCard).join('')}</div>`
    : `<div class="empty">${d.live_on ? 'Kaynak açınca :02:08–:08 arası PM emri açılır' : 'Live kapalı'}</div>`;
  const nPos = d.positions.length;
  $('posCount').textContent = nPos ? `(${nPos})` : '';
  $('posSection').classList.toggle('has-pos', nPos > 0);
  $('posBadge').textContent = nPos ? `${nPos} AÇIK` : 'BOŞ';
  $('posBadge').className = 'status ' + (nPos ? 'ok' : 'wait');
  POS_N = nPos;
  // Tümünü kapat — panelden kapalı (CLOSE_ALL_ENABLED)
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

load().then(signals);
setInterval(load, 30000);
</script></body></html>"""

SETTINGS = r"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{{ base }}/favicon.ico" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{ base }}/static/coptc.css?v={{ static_ver }}">
<title>{{ app_name }} — Ayarlar</title>
</head><body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-icon">C</div>
      <div><div class="brand-name">CoptC</div><div class="brand-sub">Live Control</div></div>
    </div>
    <nav class="nav">
      <a class="nav-item" href="{{ base }}/">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg>
        Dashboard
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
      <span><b>:02:08–:08</b> Live PM aç (10 sn poll)</span>
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
          <div class="amt-src">A2#05 V2</div>
          <div class="form-row amount-row">
            <label>Low (WR &lt; 50%)<input id="alow" type="number" step="0.5" min="1"></label>
            <label>Mid<input id="amid" type="number" step="0.5" min="1"></label>
            <label>High<input id="ahigh" type="number" step="0.5" min="1"></label>
          </div>
          <div class="amt-src">A1</div>
          <div class="form-row amount-row">
            <label>Low (WR &lt; 50%)<input id="a1low" type="number" step="0.5" min="1"></label>
            <label>Mid<input id="a1mid" type="number" step="0.5" min="1"></label>
            <label>High<input id="a1high" type="number" step="0.5" min="1"></label>
          </div>
          <div class="amt-src">C1#01</div>
          <div class="form-row amount-row">
            <label>Low (WR &lt; 50%)<input id="c1low" type="number" step="0.5" min="1"></label>
            <label>Mid<input id="c1mid" type="number" step="0.5" min="1"></label>
            <label>High<input id="c1high" type="number" step="0.5" min="1"></label>
            <button class="btn primary" id="bsave">Kaydet</button>
          </div>
          <div class="cold-cut-row">
            <button class="btn primary" id="bcoldcut">Zayıf saat −30%: —</button>
            <div class="hint" id="coldhint">Geçmişte en düşük WR'li saatlerde giriş tutarı otomatik −30% indirilir.</div>
          </div>
            <div class="hint" id="ahint">Sembol win rate'e göre kademe. A2, A1 ve C1#01 ayrı tutarlar — birlikte seçilince her kaynak kendi kademesini kullanır.</div>
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
          <div class="hint" id="mhint">En fazla 3 algoritma seçilebilir; hepsi aynı anda çalışır.
            Aynı sembolde ikisi de aynı yönü derse her biri için ayrı pozisyon açılır,
            zıt yön derlerse o sembol atlanır. Öncelik win rate'i yüksek olanda.</div>
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
    ? 'Her saat :02:08–:08 arası kaynak 10 sn\'de bir okunur, PM emri açılır.'
    : 'Cron çalışır ama emir gönderilmez.';
  $('blive').textContent = d.live_on ? 'Live kapat' : 'Live aç';
  $('blive').className = 'btn ' + (d.live_on ? 'danger' : 'success');
  const a = d.amounts;
  $('abox').innerHTML = `
    <div class="stat"><div class="stat-label">Win rate</div><div class="stat-val ${a.wr >= 50 ? 'g' : 'b'}">${a.wr == null ? '—' : '%'+a.wr}</div></div>
    <div class="stat"><div class="stat-label">İşlem</div><div class="stat-val">${a.trades}</div></div>
    <div class="stat"><div class="stat-label">Açık</div><div class="stat-val">${a.open}</div></div>`;
  if (document.activeElement.tagName !== 'INPUT'){
    $('alow').value = a.low; $('amid').value = a.mid; $('ahigh').value = a.high;
    const a1 = a.a1 || {};
    if ($('a1low')) { $('a1low').value = a1.low ?? 16; $('a1mid').value = a1.mid ?? 24; $('a1high').value = a1.high ?? 32; }
    const c1 = a.c1 || {};
    if ($('c1low')) { $('c1low').value = c1.low ?? 6; $('c1mid').value = c1.mid ?? 7; $('c1high').value = c1.high ?? 8; }
  }
  renderColdCut(a.cold_hour_cut_enabled);
  drawMirror();
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
        a1_low: +$('a1low').value, a1_mid: +$('a1mid').value, a1_high: +$('a1high').value,
        c1_low: +$('c1low').value, c1_mid: +$('c1mid').value, c1_high: +$('c1high').value,
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

const pick = () => PICK || MIRROR;
const bookName = k => { const b = ROWS.find(x => x.book === k); return b ? b.short : k; };
const sameSet = (a, b) => a.length === b.length && a.every(x => b.includes(x));
const dirty = () => !sameSet(pick(), MIRROR);

function setSaved(list){
  MIRROR = Array.isArray(list) ? list.slice() : (list ? [list] : []);
  if (PICK === null) PICK = MIRROR.slice();
}

function mrow(b){
  const dirs = (b.positions||[]).map(p =>
    `<span class="chip ${p.dir==='UP'?'up':'dn'}">${p.symbol} ${p.dir==='UP'?'↑':'↓'}</span>`).join('');
  const on = pick().includes(b.book);
  const pnlCls = b.pnl == null ? '' : (b.pnl >= 0 ? 'g' : 'b');
  return `<div class="mrow ${on?'on':''}" data-k="${b.book}">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <span class="mtick">${on?'✓':''}</span>
      <span class="nm">${b.short}</span>${on?'<span class="sel">SEÇİLİ</span>':''}
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
  $('mlist').innerHTML = rows.length ? `<div class="mlist">${rows.map(mrow).join('')}</div>` : `<div class="empty">Eşleşen defter yok</div>`;
  document.querySelectorAll('.mrow').forEach(el => el.onclick = () => toggle(el.dataset.k));
  const cur = pick(), chg = dirty();
  $('mcount').textContent = cur.length ? `(${cur.length}/${MIRROR_MAX})` : '';
  $('mnow').innerHTML = cur.length
    ? (chg ? 'Kaydedilmedi: ' : 'Çalışan: ') + `<b>${cur.map(bookName).join(' + ')}</b>`
    : 'Seçim yok';
  $('mnow').className = 'msel-now' + (chg ? ' dirty' : '');
  $('msave').disabled = !chg;
  $('mreset').disabled = !chg;
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
      a1_low: +$('a1low').value, a1_mid: +$('a1mid').value, a1_high: +$('a1high').value,
      c1_low: +$('c1low').value, c1_mid: +$('c1mid').value, c1_high: +$('c1high').value,
      cold_hour_cut_enabled: COLD_CUT_ON,
    })});
  $('ahint').textContent = r.ok ? 'Kaydedildi.' : 'Kaydedilemedi.'; $('bsave').disabled = false; load();
};
$('bcoldcut').onclick = toggleColdCut;

function renderWd(w){
  const short = a => a ? a.slice(0,6)+'…'+a.slice(-4) : '—';
  const ok = !w.error && w.builder_ready && w.proxy_match;
  $('wdinfo').innerHTML = `
    <div class="stat"><div class="stat-label">Çekilebilir</div><div class="stat-val">${money(w.balance)}</div></div>
    <div class="stat"><div class="stat-label">Cüzdan</div><div class="stat-val" style="font-size:14px">${short(w.funder)}</div></div>
    <div class="stat"><div class="stat-label">Durum</div><div class="stat-val ${ok?'g':'b'}" style="font-size:15px">${ok?'Hazır':'Eksik'}</div></div>`;
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
load(); loadMirror(); loadWd(); setInterval(loadMirror, 60000); setInterval(load, 30000);
</script></body></html>"""

LOGIN = r"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{{ base }}/favicon.ico" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{ base }}/static/coptc.css?v={{ static_ver }}">
<title>{{ app_name }}</title></head>
<body class="login-page">
<form class="login-box" method="post">
  <div class="brand"><div class="brand-icon">C</div><div><div class="brand-name">CoptC</div><div class="brand-sub">Live Control</div></div></div>
  <div class="mut" style="text-align:center;margin-bottom:8px">Panele giriş yap</div>
  <input type="password" name="p" placeholder="Parola" autofocus>
  <button type="submit">Giriş</button>
  {% if err %}<div class="werr" style="text-align:center;margin-top:8px">Hatalı parola</div>{% endif %}
</form></body></html>"""
