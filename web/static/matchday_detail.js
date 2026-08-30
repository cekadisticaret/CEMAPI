(function () {
  const $ = (id) => document.getElementById(id);
  const MID = String(window.BAHIS_MID || "").trim()
    || decodeURIComponent((location.pathname.split("/mac/")[1] || "").replace(/\/$/, ""));

  function esc(s) {
    return String(s || "").replace(/[&<>"]/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;",
    }[c]));
  }
  function pct(p) { return Math.round(Number(p || 0) * 100); }
  function crest(t) {
    if (t && t.crest) return `<img src="${esc(t.crest)}" alt="">`;
    return `<div class="fb">${esc((t && t.short) || "?")}</div>`;
  }
  function box(k, v, on) {
    return `<div class="box${on ? " on" : ""}"><s>${esc(k)}</s><b>${v}</b></div>`;
  }
  function sec(title, html, note) {
    return `<div class="g">${esc(title)}</div>${note ? `<div class="note">${esc(note)}</div>` : ""}${html}`;
  }
  function grid(items) { return `<div class="grid">${items.join("")}</div>`; }
  function maxKey(o) {
    let k = null, m = -1;
    for (const [a, b] of Object.entries(o || {})) {
      if (Number(b) > m) { m = Number(b); k = a; }
    }
    return k;
  }
  function nest(o, ...ks) {
    let x = o;
    for (const k of ks) {
      if (x == null) return {};
      x = x[k];
    }
    return x == null ? {} : x;
  }
  function apiUrl(mid) {
    if (window.BAHIS_API) return String(window.BAHIS_API) + "?id=" + encodeURIComponent(mid);
    return new URL("../api/match?id=" + encodeURIComponent(mid), location.href).href;
  }

  async function load() {
    if ($("ttl")) $("ttl").textContent = "YÜKLENİYOR";
    if ($("note")) $("note").textContent = MID ? "Pazarlar hesaplanıyor…" : "maç id yok";
    if (!MID) {
      if ($("ttl")) $("ttl").textContent = "Maç yok";
      return;
    }
    let d;
    try {
      const r = await fetch(apiUrl(MID), { cache: "no-store" });
      d = await r.json();
    } catch (e) {
      if ($("ttl")) $("ttl").textContent = "YÜKLENEMEDİ";
      if ($("note")) $("note").textContent = "API cevap vermedi. Sayfayı yenile.";
      return;
    }
    if (!d || !d.ok) {
      if ($("ttl")) $("ttl").textContent = "Maç yok";
      if ($("note")) $("note").textContent = (d && d.error) || "";
      return;
    }
    paint(d);
  }

  function paint(d) {
    const m = d.match || {};
    const mk = d.markets || {};
    const md = d.models || {};
    const xg = d.xg || {};
    document.title = `${(m.home || {}).short || "?"} vs ${(m.away || {}).short || "?"} · MATCHDAY`;
    $("when").textContent = `${m.when || ""} ${m.venue ? "· " + m.venue : ""} ${m.week ? "· H" + m.week : ""}`;
    $("ttl").textContent = "IT'S MATCHDAY";
    $("vs").innerHTML = `<div>${crest(m.home)}<b>${esc((m.home || {}).name)}</b></div><div class="pick">VS</div><div>${crest(m.away)}<b>${esc((m.away || {}).name)}</b></div>`;
    $("pick").textContent = `${d.text || ""} · %${d.pct || 0}`;
    const g = d.grade || {};
    if (g.played && g.hit != null) {
      $("pick").textContent += g.hit ? ` · TUTTU ${g.hg}–${g.ag}` : ` · TUTMADI ${g.hg}–${g.ag}`;
    } else if (g.played) {
      $("pick").textContent += ` · skor ${g.hg}–${g.ag} · maç öncesi kilit yok`;
    }
    $("note").textContent = d.note || "";
    const row = (name, o) => box(name, `1 ${pct((o || {})["1"])} · X ${pct((o || {}).X)} · 2 ${pct((o || {})["2"])}`, false);
    const cx = d.context || {};
    const shapeH = cx.shape_h || {}, shapeA = cx.shape_a || {};
    $("models").innerHTML = [
      row("POISSON", md.poisson), row("ELO", md.elo), row("XG", md.xg),
      row("ENSEMBLE", md.ensemble), row("MONTE CARLO", md.monteCarlo),
      box("λ / μ · DC+ELO", `${xg.home || "—"} / ${xg.away || "—"}`),
    ].join("");
    const ctxHtml = sec("VERİ KATMANI", grid([
      box("Dinlenme ev", cx.rest_h == null ? "—" : cx.rest_h + " gün"),
      box("Dinlenme dep", cx.rest_a == null ? "—" : cx.rest_a + " gün"),
      box("xG ev / 5s", shapeH.xg == null ? "—" : shapeH.xg),
      box("xG dep / 5s", shapeA.xg == null ? "—" : shapeA.xg),
      box("Şut ev", shapeH.shots == null ? "—" : shapeH.shots),
      box("Şut dep", shapeA.shots == null ? "—" : shapeA.shots),
      box("Korner ev", shapeH.corners == null ? "—" : shapeH.corners),
      box("Korner dep", shapeA.corners == null ? "—" : shapeA.corners),
      box("Kart ev", shapeH.cards == null ? "—" : shapeH.cards),
      box("Kart dep", shapeA.cards == null ? "—" : shapeA.cards),
      box("Sakat ev", String((cx.injuries && cx.injuries.n_h) || 0)),
      box("Sakat dep", String((cx.injuries && cx.injuries.n_a) || 0)),
    ]), (cx.notes || []).join(" · ") || "5 sezon şekil · ELO λ · Fotmob kadro");
    const ov = d.overround;
    const vextra = ov
      ? [box("overround", "%" + ov.pct + " · toplam %" + (ov.sum * 100).toFixed(1)), box("¼ Kelly", "tavan %3 · tam kasa yok")]
      : [box("¼ Kelly", "tavan %3 · tam kasa yok")];
    $("value").innerHTML = (d.value || []).map((v) => {
      const e = (v.edgeFair != null ? v.edgeFair : v.edge) || 0;
      return box(
        v.sel + " @ " + v.odds,
        v.isValue ? `VALUE +${(e * 100).toFixed(1)}p fair · ${v.stake}` : `pas · fair ${(e * 100).toFixed(1)}p`,
        v.isValue
      );
    }).concat(vextra).join("") || box("oran", "yok");
    $("warn").innerHTML = (d.warnings || []).map((w) =>
      `<div class="wb${w.ok ? "" : " bad"}"><s>${esc(w.title)}</s><p>${esc(w.text)}</p></div>`
    ).join("");
    const r = mk.result || {}, dc = mk.doubleChance || {}, ah01 = mk.ah01 || {}, ah10 = mk.ah10 || {};
    const top = maxKey(r);
    const parts = [ctxHtml];
    parts.push(sec("SONUÇ · 1X2", grid([
      box("1", "%" + pct(r["1"]), top === "1"), box("X", "%" + pct(r.X), top === "X"), box("2", "%" + pct(r["2"]), top === "2"),
      box("1X", "%" + pct(dc["1X"])), box("12", "%" + pct(dc["12"])), box("X2", "%" + pct(dc.X2)),
    ]), "90 dk kim kazanır · çifte şans"));
    parts.push(sec("HANDİKAP", grid([
      box("0:1 ev −1 · 1", "%" + pct(ah01["1"])), box("0:1 X", "%" + pct(ah01.X)), box("0:1 2", "%" + pct(ah01["2"])),
      box("1:0 dep −1 · 1", "%" + pct(ah10["1"])), box("1:0 X", "%" + pct(ah10.X)), box("1:0 2", "%" + pct(ah10["2"])),
    ]), "0:1 / 1:0 avans"));
    parts.push(sec("DOĞRU SKOR", `<div class="scores">${(mk.correctScore || []).map((s) =>
      `<i>${esc(s.score)} <em style="color:var(--y);font-style:normal">%${s.pct}</em></i>`).join("")}</div>`));
    const mg = mk.margin || {}, qf = mk.qualify || {};
    parts.push(sec("FARK", grid([
      box((m.home || {}).short + " 1 fark", "%" + pct(mg.h1)), box((m.home || {}).short + " 2+", "%" + pct(mg.h2p)),
      box((m.away || {}).short + " 1 fark", "%" + pct(mg.a1)), box((m.away || {}).short + " 2+", "%" + pct(mg.a2p)),
      box((m.home || {}).short + " tur", "%" + pct(qf.home)), box((m.away || {}).short + " tur", "%" + pct(qf.away)),
    ]), "Tur: kupa varsayımı · 90 dk 1 vs 2"));
    const ou = mk.ou || {}, btts = mk.btts || {}, oe = mk.oddEven || {};
    parts.push(sec("KAÇ GOL", grid([
      ...["0.5", "1.5", "2.5", "3.5", "4.5", "5.5"].map((l) =>
        box(l + " alt/üst", `%${pct(nest(ou, l).under)} / %${pct(nest(ou, l).over)}`)),
      box("KG var", "%" + pct(btts.yes)), box("KG yok", "%" + pct(btts.no)),
      box("tek", "%" + pct(oe.odd)), box("çift", "%" + pct(oe.even)),
    ])));
    const ms = mk.ms25 || {}, kg = mk.kg25 || {};
    parts.push(sec("MS + 2.5  ·  KG + 2.5", grid([
      box("1 ve üst", "%" + pct(ms["1_over"])), box("1 ve alt", "%" + pct(ms["1_under"])),
      box("X ve üst", "%" + pct(ms.X_over)), box("X ve alt", "%" + pct(ms.X_under)),
      box("2 ve üst", "%" + pct(ms["2_over"])), box("2 ve alt", "%" + pct(ms["2_under"])),
      box("KG+üst", "%" + pct(kg.yes_over)), box("KG+alt", "%" + pct(kg.yes_under)),
      box("KG yok+üst", "%" + pct(kg.no_over)), box("KG yok+alt", "%" + pct(kg.no_under)),
    ])));
    const hou = mk.homeOu || {}, aou = mk.awayOu || {};
    parts.push(sec("EV / DEP ALT-ÜST", grid([
      ...["0.5", "1.5", "2.5"].map((l) => box("Ev " + l + " A/Ü", `%${pct(nest(hou, l).under)} / %${pct(nest(hou, l).over)}`)),
      ...["0.5", "1.5", "2.5"].map((l) => box("Dep " + l + " A/Ü", `%${pct(nest(aou, l).under)} / %${pct(nest(aou, l).over)}`)),
    ])));
    const fg = mk.firstGoal || {};
    parts.push(sec("İLK GOL · ARALIK", grid([
      box("İlk gol ev", "%" + pct(fg.home)), box("İlk gol dep", "%" + pct(fg.away)), box("Golsüz", "%" + pct(fg.none)),
      ...(mk.goalWindows || []).map((w) => box(w.k + "' gol olur", "%" + w.pct)),
    ]), "Poisson bekleme · dakika verisi yok"));
    const iy = mk.iyMs || {}, sh2 = mk.sh || {}, ht = mk.ht || {}, hm = mk.halfMore || {}, htOu = mk.htOu15 || {};
    parts.push(sec("DEVRE", grid([
      box("İY 1", "%" + pct(ht["1"])), box("İY X", "%" + pct(ht.X)), box("İY 2", "%" + pct(ht["2"])),
      box("2Y 1", "%" + pct(sh2["1"])), box("2Y X", "%" + pct(sh2.X)), box("2Y 2", "%" + pct(sh2["2"])),
      box("İY 1.5 alt/üst", `%${pct(htOu.under)} / %${pct(htOu.over)}`),
      box("İY KG", "%" + pct(mk.htBtts)),
      box("1. yarı daha çok", "%" + pct(hm.first)), box("2. yarı daha çok", "%" + pct(hm.second)), box("eşit", "%" + pct(hm.eq)),
      ...Object.entries(iy).map(([k, v]) => box("İY/MS " + k, "%" + pct(v))),
    ])));
    parts.push(sec("İY SKOR", `<div class="scores">${(mk.htScores || []).map((s) =>
      `<i>${esc(s.score)} <em style="color:var(--y);font-style:normal">%${s.pct}</em></i>`).join("")}</div>`));
    const cb = mk.cornersBucket || {}, cm = mk.cornerMore || {}, fc = mk.firstCorner || {};
    const hcou = nest(mk.homeCornerOu, "8.5"), acou = nest(mk.awayCornerOu, "8.5");
    parts.push(sec("KORNER", grid([
      box("0–8", "%" + pct(cb.le8)), box("9–11", "%" + pct(cb["9_11"])), box("12+", "%" + pct(cb.ge12)),
      ...Object.entries(mk.cornerOu || {}).map(([l, v]) => box(l + " A/Ü", `%${pct(v.under)} / %${pct(v.over)}`)),
      ...Object.entries(mk.htCornerOu || {}).map(([l, v]) => box("İY " + l + " A/Ü", `%${pct(v.under)} / %${pct(v.over)}`)),
      box("daha çok ev", "%" + pct(cm.home)), box("daha çok dep", "%" + pct(cm.away)),
      box("ilk korner ev", "%" + pct(fc.home)), box("ilk korner dep", "%" + pct(fc.away)),
      box("ev 8.5 A/Ü", `%${pct(hcou.under)} / %${pct(hcou.over)}`),
      box("dep 8.5 A/Ü", `%${pct(acou.under)} / %${pct(acou.over)}`),
    ]), "Son 10 maç HC/AC Poisson + 6k sim"));
    const cmo = mk.cardMore || {};
    parts.push(sec("KART", grid([
      box("kırmızı olur", "%" + pct(mk.redYes)),
      ...Object.entries(mk.cardOu || {}).map(([l, v]) => box("puan " + l + " A/Ü", `%${pct(v.under)} / %${pct(v.over)}`)),
      box("daha çok ev", "%" + pct(cmo.home)), box("daha çok dep", "%" + pct(cmo.away)), box("eşit", "%" + pct(cmo.eq)),
      ...["1.5", "2.5"].map((l) => box("ev " + l + " A/Ü", `%${pct(nest(mk.homeCardOu, l).under)} / %${pct(nest(mk.homeCardOu, l).over)}`)),
      ...["1.5", "2.5"].map((l) => box("dep " + l + " A/Ü", `%${pct(nest(mk.awayCardOu, l).under)} / %${pct(nest(mk.awayCardOu, l).over)}`)),
    ]), "sarı 1 · kırmızı 2"));
    const sc = d.scorers || {};
    const col = (arr, t) => (arr || []).map((p) =>
      `<div class="prow">${p.photo ? `<img src="${esc(p.photo)}">` : ""}<div>${esc(p.name)}<div class="note">${esc(t)} · herhangi %${pct(p.anyGoal)} · ilk %${pct(p.firstGoal)} · son %${pct(p.lastGoal)} · sıradaki %${pct(p.nextGoal)} · ${(p.stats && p.stats.goals) || 0}G · ${(p.stats && p.stats.xg) || 0} xG${p.yellow ? " · " + p.yellow + "S" : ""}${p.pen ? " · pen " + p.pen : ""}${p.red ? " · " + p.red + "K" : ""}</div></div></div>`
    ).join("");
    parts.push(sec("OYUNCU", `<div class="grid" style="grid-template-columns:1fr 1fr"><div>${col(sc.a, (m.home || {}).short)}</div><div>${col(sc.b, (m.away || {}).short)}</div></div>`, "İlk / son / herhangi / sıradaki gol — xG payı · Fotmob"));
    const lv = mk.live || {}, tm = lv.tenMin || {}, ex = lv.extra || {}, exo = ex.ou || {};
    parts.push(sec("CANLI / DİĞER", grid([
      box("maç başladı", lv.started ? "evet" : "hayır"),
      box("kalanını kim", lv.remainWinner
        ? (`1 ${pct(lv.remainWinner["1"])} · X ${pct(lv.remainWinner.X)} · 2 ${pct(lv.remainWinner["2"])}`)
        : "maç öncesi kapalı"),
      box("10 dk gol", "%" + pct(tm.goal)),
      box("10 dk korner", "%" + pct(tm.corner)),
      box("10 dk kart", "%" + pct(tm.card)),
      box("uzatma olur", "%" + pct(ex.yes)),
      box("uzatma yok", "%" + pct(ex.no)),
      ...["0.5", "1.5", "2.5"].map((l) => box("uzatma " + l + " A/Ü", `%${pct(nest(exo, l).under)} / %${pct(nest(exo, l).over)}`)),
    ]), "Kalan-kazanan maç başladıysa. Uzatma/tur kupa varsayımı (90 X → 30 dk)."));
    $("mk").innerHTML = parts.join("");
  }

  load().catch((e) => {
    if ($("ttl")) $("ttl").textContent = "HATA";
    if ($("note")) $("note").textContent = String((e && e.message) || e);
  });
})();
