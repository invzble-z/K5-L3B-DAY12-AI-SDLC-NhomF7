"use strict";
/*
 * HUD buổi sáng (Ticket-02 §2): Máu, oxy (< 25% đổi màu + nhấp nháy), thời gian (≤ 30 s đổi màu), độ sâu,
 * giỏ theo loại, danh sách cần lấy (đã lấy/cần), hồi bắt, "Thủy quái!" + viền tím, "Hết hơi!". Chữ ≥ 18 px.
 */
(function (CN) {
  const { ctx, text, bar, ui, COLOR, fmtTime } = CN;
  const PURPLE = "#a26bff";

  const counts = (list) => CN.inv.counts(list);
  const isUnder = (snap, p) => (p.at_surface === undefined ? p.pos && p.pos[1] > ((snap.meta || {}).surface_depth ?? 0.5) : !p.at_surface);

  function monsterNear(snap, p) {
    if (!p.pos || p.pos[1] < 10) return false;                       // Cá Sấu chỉ đuổi khi người chơi ở d ≥ 10
    const species = ((snap.meta || {}).monsters || {}).species || {};
    return (snap.monsters || []).some((m) => {
      const r = (species[m.species ?? m.kind] || {}).detect_radius || 10;
      return m.state === "chase" || Math.hypot(m.pos[0] - p.pos[0], m.pos[1] - p.pos[1]) <= r;
    });
  }

  function warnings(w, h, snap, p) {
    const t = CN.now();
    const lowO2 = p.oxygen_max_ticks && isUnder(snap, p) && p.oxygen_ticks < p.oxygen_max_ticks * 0.25;
    if (lowO2) {
      const a = 0.2 + 0.14 * Math.sin(t * 6);
      const g = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.3, w / 2, h / 2, Math.max(w, h) * 0.7);
      g.addColorStop(0, "rgba(239,83,80,0)"); g.addColorStop(1, `rgba(239,83,80,${a.toFixed(3)})`);
      ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    }
    // 3 cảnh báo TICKET-04 (2 cái ở cảnh lặn): chữ + biểu tượng qua ui.alert, viền màn hình chỉ là phụ.
    let ay = 104;
    if (monsterNear(snap, p)) {
      ctx.strokeStyle = PURPLE; ctx.globalAlpha = CN.contrast.on ? 1 : 0.55 + 0.35 * Math.sin(t * 8); ctx.lineWidth = CN.contrast.on ? 14 : 10;
      ctx.strokeRect(5, 5, w - 10, h - 10); ctx.globalAlpha = 1;
      ui.alert(w / 2, ay, "Thủy quái! Tránh xa", CN.contrast.on ? "#bf5af2" : PURPLE, { size: 26 });
      ay += 52;
    }
    if (p.oxygen_max_ticks && isUnder(snap, p)) {
      if (p.oxygen_ticks === 0) ui.alert(w / 2, h / 2 - 80, "Hết hơi! Lên mặt nước!", COLOR.danger, { size: 30 });
      else if (lowO2) ui.alert(w / 2, ay, "Sắp hết hơi! Lên thở", COLOR.danger, { size: 24 });
    }
  }

  function statusPanel(snap, p) {
    ui.panel(10, 8, 430, 74);
    if (p.oxygen_ticks !== undefined && p.oxygen_max_ticks) {
      const f = p.oxygen_ticks / p.oxygen_max_ticks;
      const blink = f < 0.25 && Math.floor(CN.now() * 4) % 2;
      text("O₂", 22, 32, { size: 20, weight: "800", color: COLOR.oxy, base: "middle" });
      bar(58, 20, 200, 26, f, f < 0.25 ? (blink ? "#ff8a80" : COLOR.danger) : COLOR.oxy, Math.ceil(p.oxygen_ticks / 60) + " s");
    }
    if (p.hp !== undefined && p.hp_max) {
      let hs = "";
      for (let i = 0; i < p.hp_max; i++) hs += i < p.hp ? "♥" : "♡";
      text(hs, 270, 33, { size: 26, color: COLOR.hp, base: "middle" });
    }
    if (p.pos) text("Sâu " + Math.max(0, p.pos[1]).toFixed(1) + " m", 22, 64, { size: 18, base: "middle", weight: "600" });
    const cd = p.catch_cd_ticks > 0 ? "Bắt: " + (p.catch_cd_ticks / 60).toFixed(1) + " s" : "Bắt: sẵn sàng";
    text(cd, 160, 64, { size: 18, base: "middle", color: p.catch_cd_ticks > 0 ? COLOR.muted : COLOR.ok });
    if (snap.day !== undefined) text("Ngày " + snap.day, 428, 64, { size: 18, base: "middle", align: "right", color: COLOR.gold, weight: "700" });
  }

  function clock(w, snap) {
    const low = (snap.time_left_ticks || 0) <= 30 * 60;
    ui.panel(w / 2 - 66, 8, 132, 44);
    text("⏱ " + fmtTime(snap.time_left_ticks), w / 2, 31, { size: 24, align: "center", base: "middle", weight: "800", color: low ? COLOR.danger : COLOR.text });
  }

  function minimap(w, snap) {
    const v = CN.lastView;
    if (!v || w < 900) return 8;
    const x = w - 290, y = 8, mw = 280, mh = 56, ix = x + 10, iy = y + 10, iw = mw - 20, ih = mh - 20;
    ui.panel(x, y, mw, mh);
    const mx = (wx) => ix + ((wx - v.X0) / (v.X - v.X0)) * iw, my = (d) => iy + (d / v.D) * ih;
    const mg = ctx.createLinearGradient(0, iy, 0, iy + ih);                // nước phù sa như cảnh chính
    mg.addColorStop(0, "rgba(207,163,106,.8)"); mg.addColorStop(1, "rgba(60,46,28,.85)");
    ctx.fillStyle = mg; ctx.fillRect(ix, iy, iw, ih);
    const dp = v.meta.dock_pos || [2, 0];
    ctx.fillStyle = "#c98f4a"; ctx.fillRect(mx(dp[0]) - 4, iy - 4, 8, 5);
    (snap.nodes || []).forEach((n) => { ctx.fillStyle = n.ready !== false ? CN.kc(n.kind) : "rgba(255,255,255,.3)"; ctx.fillRect(mx(n.pos[0]) - 3, iy, 6, 4); });
    (snap.fish || []).forEach((f) => { ctx.fillStyle = CN.kc(f.kind); ctx.fillRect(mx(f.pos[0]) - 2, my(f.pos[1]) - 2, 4, 4); });
    (snap.monsters || []).forEach((m) => { ctx.fillStyle = PURPLE; ctx.beginPath(); ctx.arc(mx(m.pos[0]), my(m.pos[1]), 4, 0, Math.PI * 2); ctx.fill(); });
    const p = snap.player;
    if (p && p.pos) { ctx.fillStyle = COLOR.player; ctx.beginPath(); ctx.arc(mx(p.pos[0]), my(p.pos[1]), 4, 0, Math.PI * 2); ctx.fill(); }
    ctx.strokeStyle = "rgba(255,255,255,.75)"; ctx.lineWidth = 1;
    const l = Math.max(ix, mx(v.camX)), r = Math.min(ix + iw, mx(v.camX + w / v.s));
    ctx.strokeRect(l, iy - 1, Math.max(4, r - l), ih + 2);
    return y + mh + 8;
  }

  // Danh sách cần lấy theo kế hoạch Ngày (day_plan.ingredients): đã lấy / cần.
  function needList(w, y, snap) {
    const need = (snap.day_plan || {}).ingredients;
    if (!need) return;
    const have = counts(snap.hold), kinds = Object.keys(need);
    const pw = 220, ph = 40 + kinds.length * 32, x = w - pw - 10;
    ui.panel(x, y, pw, ph);
    text("Cần lấy", x + 14, y + 24, { size: 18, weight: "700", color: COLOR.gold });
    kinds.forEach((k, i) => {
      const yy = y + 52 + i * 32, got = have[k] || 0, done = got >= need[k];
      ui.icon(k, x + 28, yy - 6, 26);
      text(CN.kname(k), x + 48, yy, { size: 18, color: done ? COLOR.ok : COLOR.text });
      text(got + "/" + need[k], x + pw - 14, yy, { size: 18, align: "right", weight: "700", color: done ? COLOR.ok : COLOR.text });
    });
  }

  // Giỏ theo loại: icon + số lượng, tổng n/sức chứa; viền vàng ở món nhặt sau cùng (bị rơi trước khi trúng quái).
  // v1.2 (AC-P3-09): mỗi cá thể một ô theo thứ tự nhặt: icon, số độ tươi (floor), thanh màu; < ngưỡng ghi "ươn".
  function freshHold(w, h, snap) {
    const items = snap.hold, cap = snap.hold_capacity, n = items.length, full = n >= cap, below = CN.inv.spoiledBelow(snap);
    const sw = 56, gap = 4, maxSlots = Math.max(1, Math.floor((w - 140) / (sw + gap)));
    const shown = items.slice(-maxSlots), pw = 96 + Math.max(1, shown.length) * (sw + gap), ph = 86, y0 = h - ph - 10;
    ui.panel(10, y0, pw, ph, full ? { stroke: COLOR.danger, lineWidth: 2 } : {});
    text("Giỏ", 24, y0 + 32, { size: 20, weight: "800" });
    text(n + "/" + cap, 24, y0 + 58, { size: 18, weight: "700", color: full ? COLOR.danger : COLOR.muted });
    const spoiled = items.filter((it) => it.fresh < below).length;
    if (spoiled) text(spoiled + " ươn", 24, y0 + 78, { size: 18, weight: "800", color: COLOR.danger });
    shown.forEach((it, i) => {
      const x = 96 + i * (sw + gap), bad = it.fresh < below, col = CN.freshColor(it.fresh, below);
      ui.panel(x, y0 + 6, sw, ph - 12, { fill: bad ? "rgba(239,83,80,.22)" : "rgba(255,255,255,.06)", stroke: bad ? COLOR.danger : COLOR.line, lineWidth: bad ? 2 : 1, r: 8 });
      ctx.globalAlpha = bad ? 0.55 : 1;
      ui.icon(it.kind, x + sw / 2, y0 + 26, 30);
      ctx.globalAlpha = 1;
      text(bad ? "ươn" : String(Math.floor(it.fresh)), x + sw / 2, y0 + 58, { size: 18, align: "center", weight: "800", color: bad ? COLOR.danger : COLOR.text });
      bar(x + 6, y0 + 66, sw - 12, 6, it.fresh / 100, col);
    });
    if (full) text("Giỏ đầy!", 10 + pw + 12, y0 + 44, { size: 20, color: COLOR.danger, weight: "800" });
  }

  function hold(w, h, snap) {
    if (!snap.hold || !snap.hold_capacity) return;
    if (CN.inv.hasFresh(snap.hold)) return freshHold(w, h, snap);
    const cap = snap.hold_capacity, n = snap.hold.length, full = n >= cap, c = counts(snap.hold), kinds = Object.keys(c);
    const pw = Math.max(200, 130 + kinds.length * 86), y0 = h - 74;
    ui.panel(10, y0, pw, 64, full ? { stroke: COLOR.danger, lineWidth: 2 } : {});
    text("Giỏ", 24, y0 + 28, { size: 20, weight: "800" });
    text(n + "/" + cap, 24, y0 + 52, { size: 18, weight: "700", color: full ? COLOR.danger : COLOR.muted });
    const last = snap.hold[n - 1];
    kinds.forEach((k, i) => {
      const x0 = 96 + i * 86;
      if (k === last) { ctx.strokeStyle = COLOR.gold; ctx.lineWidth = 1.5; CN.rrect(x0 - 4, y0 + 8, 80, 48, 8); ctx.stroke(); }
      ui.icon(k, x0 + 20, y0 + 32, 34);
      text("×" + c[k], x0 + 42, y0 + 39, { size: 20, weight: "700" });
    });
    if (full) text("Giỏ đầy!", 10 + pw + 12, y0 + 38, { size: 20, color: COLOR.danger, weight: "800" });
  }

  function returnWarning(w, h, snap) {
    const v = CN.lastView;
    if (!v || snap.finished || (snap.time_left_ticks || 0) > 20 * 60) return;
    const x = v.sx((v.meta.dock_pos || [2, 0])[0]);
    ctx.globalAlpha = 0.6 + 0.4 * Math.sin(CN.now() * 6);
    if (x < 0) text("◀ Về ghe!", 16, h / 2, { size: 22, color: COLOR.gold, weight: "800" });
    else if (x > w) text("Về ghe! ▶", w - 16, h / 2, { size: 22, color: COLOR.gold, weight: "800", align: "right" });
    ctx.globalAlpha = 1;
  }

  CN.hud.gather = function (w, h, snap) {
    const p = snap.player || {};
    warnings(w, h, snap, p);
    statusPanel(snap, p);
    clock(w, snap);
    needList(w, minimap(w, snap), snap);
    hold(w, h, snap);
    returnWarning(w, h, snap);
    text("Esc tạm dừng · H tương phản cao", w - 14, h - 16, { size: 18, align: "right", color: COLOR.muted });
  };
})(window.CN);
