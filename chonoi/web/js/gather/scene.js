"use strict";
/*
 * Cảnh buổi sáng (gather): mặt cắt sông nhìn ngang, camera bám theo Út Sen (PRD-0 §3).
 * Trời hồng buổi sớm, bờ xa có nhà sàn, dừa nước; nước phù sa đậm dần theo độ sâu (nông / giữa / sâu).
 * Chỉ vẽ. Gợi ý phím ("E Hái", "Space Bắt") chỉ để HIỂN THỊ theo snapshot; sim mới quyết định có tác dụng.
 * Mọi chi tiết trang trí lấy từ CN.art.hash (cố định), không đụng Streams của mô phỏng.
 */
(function (CN) {
  const { ctx, text, ui, COLOR, art } = CN;
  const { hash: H, TAU } = art;
  const SKY = 6;                       // khoảng trời phía trên mặt nước (đơn vị thế giới)
  const PURPLE = "#a26bff";
  const PS = 1.6;                      // phóng to Út Sen cho dễ nhìn (chỉ hình, không đổi vị trí/bán kính trong sim)
  CN.layout.gather = { top: 64, bottom: 76 };
  const bubbles = [];                  // bọt khí: thuần hình ảnh
  let lastBubble = 0;

  function view(w, h, snap) {
    const meta = snap.meta || {};
    const b = meta.bounds || { x: [0, 100], d: [0, 30] };
    const X0 = b.x[0], X = b.x[1], D = b.d[1];
    const { top, bottom } = CN.layout.gather;
    const s = Math.max(4, (h - top - bottom) / (D + SKY));
    const p = (snap.player && snap.player.pos) || [X0, 0];
    const camX = CN.camera.follow(p[0], w / s, X0 - 4, X + 4);
    const oy = top + SKY * s;
    return { meta, X0, X, D, s, camX, oy, top, w, h, sx: (x) => (x - camX) * s, sy: (d) => oy + d * s };
  }

  // nhiễu mượt 1 chiều từ hàm băm (đường chân trời, bờ đáy)
  function noise(u, salt) {
    const i = Math.floor(u), f = u - i, k = f * f * (3 - 2 * f);
    return H(i * 31 + salt) * (1 - k) + H((i + 1) * 31 + salt) * k;
  }

  // Lặp các vật trang trí cách đều `gap` trên lớp parallax `par`; fn(screenX, k).
  function eachDeco(v, par, gap, margin, fn) {
    const u0 = v.camX * par, k0 = Math.floor((u0 - margin) / gap), k1 = Math.ceil((u0 + v.w / v.s + margin) / gap);
    for (let k = k0; k <= k1; k++) fn((k * gap + H(k * 7 + gap) * gap * 0.5 - u0) * v.s, k);
  }

  // ---------------- trời buổi sớm và bờ sông ----------------
  function drawSky(v) {
    const { w, oy, s } = v, t = CN.now();
    const g = ctx.createLinearGradient(0, 0, 0, oy);
    g.addColorStop(0, "#d98fa4"); g.addColorStop(0.45, "#f3b8a2"); g.addColorStop(0.8, "#fbd9b4"); g.addColorStop(1, "#fde9cc");
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, oy);
    // mặt trời mới mọc
    const sunX = w * 0.72 - v.camX * s * 0.02, sunY = oy - 1.2 * s;
    art.glow(sunX, sunY, 9 * s, "rgba(255,196,150,.6)");
    ctx.fillStyle = "#fff3da"; ctx.beginPath(); ctx.arc(sunX, sunY, 1.3 * s, 0, TAU); ctx.fill();
    // mây hồng trôi chậm
    for (let i = 0; i < 5; i++) {
      const span = w * 1.4, x = ((H(i) * span + t * (4 + H(i + 9) * 6) - v.camX * s * 0.05) % span + span) % span - w * 0.2;
      const y = oy * (0.18 + H(i + 3) * 0.32), r = (1.2 + H(i + 5)) * s;
      ctx.fillStyle = "rgba(255,232,226,.55)";
      ctx.beginPath(); ctx.ellipse(x, y, r * 2.4, r * 0.5, 0, 0, TAU); ctx.ellipse(x + r, y - r * 0.3, r * 1.3, r * 0.55, 0, 0, TAU); ctx.ellipse(x - r * 1.1, y - r * 0.15, r, r * 0.4, 0, 0, TAU); ctx.fill();
    }
    // rặng cây xa (mờ tím hồng)
    ctx.fillStyle = "rgba(170,120,135,.55)"; ctx.beginPath(); ctx.moveTo(0, oy);
    for (let x = 0; x <= w + 8; x += 8) { const u = x / s + v.camX * 0.12; ctx.lineTo(x, oy - (0.9 + 1.6 * noise(u / 2.5, 3)) * s); }
    ctx.lineTo(w, oy); ctx.fill();
    // nhà sàn bờ xa
    eachDeco(v, 0.32, 15, 6, (x, k) => {
      if (H(k * 13 + 1) < 0.25) drawBoat(x + 2 * s, oy, s * 0.7, "rgba(110,80,70,.75)");
      else drawStiltHouse(x, oy, s, k);
    });
    // dừa nước bờ gần
    eachDeco(v, 0.6, 6, 5, (x, k) => { if (H(k * 5 + 2) > 0.3) drawNipa(x, oy + 0.2 * s, s, k); });
  }

  function drawStiltHouse(x, base, s, k) {
    const wd = (3.4 + H(k) * 1.4) * s, legs = 0.9 * s, wall = (1.3 + H(k + 1) * 0.4) * s;
    ctx.fillStyle = "rgba(92,66,52,.8)";
    for (let i = 0; i < 4; i++) ctx.fillRect(x + (i / 3) * (wd - 0.15 * s), base - legs, 0.13 * s, legs + 0.3 * s);   // cột sàn
    ctx.fillRect(x - 0.2 * s, base - legs - 0.15 * s, wd + 0.4 * s, 0.18 * s);                                     // sàn
    ctx.fillStyle = "rgba(150,108,80,.85)"; ctx.fillRect(x, base - legs - wall, wd, wall);                          // vách gỗ
    ctx.fillStyle = "rgba(110,78,58,.5)";
    for (let i = 1; i < 6; i++) ctx.fillRect(x + (i / 6) * wd, base - legs - wall, 1, wall);
    ctx.fillStyle = "rgba(255,214,140,.9)"; ctx.fillRect(x + wd * 0.58, base - legs - wall * 0.7, wd * 0.18, wall * 0.38); // cửa sổ có đèn
    ctx.fillStyle = H(k + 2) < 0.5 ? "rgba(122,86,60,.95)" : "rgba(150,140,135,.95)";                                // mái lá / mái tôn
    ctx.beginPath(); ctx.moveTo(x - 0.5 * s, base - legs - wall); ctx.lineTo(x + wd * 0.5, base - legs - wall - 1.3 * s); ctx.lineTo(x + wd + 0.5 * s, base - legs - wall); ctx.closePath(); ctx.fill();
  }

  // ghe nhìn ngang: thân cong, mũi vểnh, mui cong
  function drawBoat(x, base, s, color) {
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.moveTo(x - 2.4 * s, base - 0.9 * s);
    ctx.quadraticCurveTo(x - 1.8 * s, base + 0.3 * s, x, base + 0.3 * s);
    ctx.quadraticCurveTo(x + 1.8 * s, base + 0.3 * s, x + 2.6 * s, base - 1 * s);
    ctx.lineTo(x + 2.1 * s, base - 0.45 * s); ctx.lineTo(x - 2 * s, base - 0.45 * s); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.ellipse(x - 0.1 * s, base - 0.45 * s, 1.1 * s, 0.75 * s, 0, Math.PI, 0); ctx.fill();
  }

  function drawNipa(x, base, s, k) {
    const n = 6 + Math.floor(H(k + 3) * 3), t = CN.now();
    ctx.strokeStyle = "rgba(58,98,52,.9)"; ctx.lineCap = "round";
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const a = -Math.PI / 2 + (i / (n - 1) - 0.5) * 2.1 + Math.sin(t * 0.8 + k + i) * 0.03;
      const len = (2.2 + H(k * 9 + i) * 1.4) * s;
      const tx = x + Math.cos(a) * len, ty = base + Math.sin(a) * len * 0.9 + len * 0.25;
      const cx = x + Math.cos(a) * len * 0.5, cy = base + Math.sin(a) * len * 0.75;
      ctx.moveTo(x, base); ctx.quadraticCurveTo(cx, cy, tx, ty);
      for (let j = 2; j <= 8; j++) {                                   // lá chét rủ xuống hai bên sống lá
        const f = j / 9, px = (1 - f) * (1 - f) * x + 2 * (1 - f) * f * cx + f * f * tx, py = (1 - f) * (1 - f) * base + 2 * (1 - f) * f * cy + f * f * ty;
        const ll = (1 - f * 0.6) * 0.55 * s;
        ctx.moveTo(px, py); ctx.lineTo(px - ll * 0.6, py + ll);
        ctx.moveTo(px, py); ctx.lineTo(px + ll * 0.6, py + ll);
      }
    }
    ctx.lineWidth = Math.max(1, 0.09 * s); ctx.stroke(); ctx.lineCap = "butt";
  }

  // ---------------- nước phù sa ----------------
  function drawWater(v) {
    const { w, oy, s, D } = v, t = CN.now();
    const bed = v.sy(D);
    const g = ctx.createLinearGradient(0, oy, 0, bed);
    g.addColorStop(0, "#cfa36a"); g.addColorStop(Math.min(1, 9 / D), "#a77c46"); g.addColorStop(Math.min(1, 20 / D), "#5e4a2b"); g.addColorStop(1, "#1d1a12");
    ctx.fillStyle = g; ctx.fillRect(0, oy, w, bed - oy);
    // ánh trời hồng phản chiếu dưới mặt nước
    const r = ctx.createLinearGradient(0, oy, 0, oy + 2 * s);
    r.addColorStop(0, "rgba(255,190,170,.45)"); r.addColorStop(1, "rgba(255,190,170,0)");
    ctx.fillStyle = r; ctx.fillRect(0, oy, w, 2 * s);
    // tia nắng xiên
    ctx.fillStyle = "rgba(255,226,170,.07)";
    for (let k = 0; k < 5; k++) {
      const x = (((k * 21 - v.camX * 0.3) * s) % (w + 300) + w + 300) % (w + 300) - 150 + Math.sin(t * 0.4 + k) * 10;
      ctx.beginPath(); ctx.moveTo(x, oy); ctx.lineTo(x + 2.5 * s, oy); ctx.lineTo(x + 10 * s, oy + 16 * s); ctx.lineTo(x + 5.5 * s, oy + 16 * s); ctx.fill();
    }
    // hạt phù sa lơ lửng
    ctx.fillStyle = "rgba(255,238,205,.22)"; ctx.beginPath();
    const span = v.X - v.X0 + 8;
    for (let i = 0; i < 160; i++) {
      const wx = v.X0 - 4 + H(i) * span + Math.sin(t * 0.3 + i) * 0.5, d = 0.6 + H(i + 500) * (D - 1) + Math.sin(t * 0.5 + i * 1.7) * 0.3;
      const x = v.sx(wx); if (x < -5 || x > w + 5) continue;
      const rr = (0.05 + H(i + 900) * 0.08) * s;
      ctx.moveTo(x + rr, v.sy(d)); ctx.arc(x, v.sy(d), rr, 0, TAU);
    }
    ctx.fill();
    // đáy bùn gợn, sỏi, rong
    ctx.fillStyle = "#3a2c1c"; ctx.beginPath(); ctx.moveTo(0, v.h);
    for (let x = 0; x <= w + 10; x += 10) ctx.lineTo(x, bed - noise((x / s + v.camX) / 3, 11) * 0.8 * s);
    ctx.lineTo(w, v.h); ctx.fill();
    const k0 = Math.floor(v.camX / 1.7) - 1, k1 = k0 + Math.ceil(w / s / 1.7) + 2;
    for (let k = k0; k <= k1; k++) {
      if (H(k + 77) < 0.5) continue;
      const x = v.sx(k * 1.7 + H(k) * 1.2);
      ctx.fillStyle = H(k + 3) < 0.5 ? "#5b4a36" : "#6d6150";
      ctx.beginPath(); ctx.ellipse(x, bed - 0.1 * s, (0.2 + H(k + 4) * 0.25) * s, 0.15 * s, 0, 0, TAU); ctx.fill();
    }
    // rong / cỏ nước: lá thuôn đung đưa, hai tông màu
    const r0 = Math.floor(v.camX / 1.6) - 1, r1 = r0 + Math.ceil(w / s / 1.6) + 2;
    for (const tone of [0, 1]) {
      ctx.fillStyle = tone ? "rgba(120,140,60,.85)" : "rgba(70,92,40,.9)"; ctx.beginPath();
      for (let k = r0; k <= r1; k++) {
        if ((H(k * 11) < 0.5) !== !!tone) continue;
        const x = v.sx(k * 1.6 + H(k * 3) * 1.2), hgt = (0.9 + H(k * 5) * 2.4) * s, wb = (0.12 + H(k * 2) * 0.1) * s;
        const sway = Math.sin(t * 1.4 + k) * 0.5 * s, lean = (H(k * 9) - 0.5) * s;
        ctx.moveTo(x - wb, bed); ctx.quadraticCurveTo(x - wb + sway * 0.5 + lean, bed - hgt * 0.55, x + sway + lean, bed - hgt);
        ctx.quadraticCurveTo(x + wb + sway * 0.5 + lean, bed - hgt * 0.5, x + wb, bed);
      }
      ctx.fill();
    }
    // mặt nước gợn
    ctx.strokeStyle = "rgba(255,244,230,.9)"; ctx.lineWidth = 2; ctx.beginPath();
    for (let x = 0; x <= w; x += 8) {
      const y = oy + Math.sin((x + v.camX * s) * 0.04 + t * 2) * 1.5;
      if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
    // ngoài biên: tối lại
    ctx.fillStyle = "rgba(20,10,0,.35)";
    const l = v.sx(v.X0), rr = v.sx(v.X);
    if (l > 0) ctx.fillRect(0, oy, l, bed - oy);
    if (rr < w) ctx.fillRect(rr, oy, w - rr, bed - oy);
    // vùng độ sâu theo ticket: nông d < 10, giữa 10 ≤ d < 20, sâu d ≥ 20
    ctx.setLineDash([10, 8]); ctx.strokeStyle = "rgba(255,240,220,.2)"; ctx.lineWidth = 1;
    for (const d of [10, 20]) if (d < D) { ctx.beginPath(); ctx.moveTo(0, v.sy(d)); ctx.lineTo(w, v.sy(d)); ctx.stroke(); }
    ctx.setLineDash([]);
    [["Nông", 0, 10], ["Giữa", 10, 20], ["Sâu", 20, D]].forEach(([name, a, b]) => {
      if (a < D) text(name, 12, v.sy((a + Math.min(b, D)) / 2) + 6, { size: 18, color: "rgba(255,240,220,.4)", weight: "600" });
    });
  }

  // ---------------- bến ----------------
  function drawDock(v) {
    const { meta, s, oy } = v;
    const dp = meta.dock_pos || [2, 0], dr = meta.dock_radius || 3;
    const x = v.sx(dp[0]), t = CN.now();
    const deck = oy - 0.9 * s;
    // cầu tàu bên trái
    ctx.fillStyle = "#5a3e26";
    for (let i = 0; i < 4; i++) { const px = x - 4.2 * s + i * 1.2 * s; ctx.fillRect(px, deck, 0.22 * s, 3.4 * s); }
    ctx.fillStyle = "rgba(40,25,10,.35)"; ctx.fillRect(x - 4.4 * s, oy, 4 * s, 2.6 * s);                         // bóng cột dưới nước
    ctx.fillStyle = "#9b7148"; ctx.fillRect(x - 4.5 * s, deck - 0.25 * s, 3.8 * s, 0.3 * s);
    ctx.fillStyle = "rgba(60,40,20,.5)";
    for (let i = 0; i < 8; i++) ctx.fillRect(x - 4.5 * s + i * 0.48 * s, deck - 0.25 * s, 1, 0.3 * s);
    // biển "Bến"
    ctx.fillStyle = "#5a3e26"; ctx.fillRect(x - 3.9 * s, deck - 2.2 * s, 0.15 * s, 2 * s);
    ctx.fillStyle = "#e9cf9a"; CN.rrect(x - 4.6 * s, deck - 2.9 * s, 2.4 * s, 1 * s, 4); ctx.fill();
    ctx.strokeStyle = "#6b4a2b"; ctx.lineWidth = 2; ctx.stroke();
    text("Bến", x - 3.4 * s, deck - 2.4 * s, { size: 18, align: "center", base: "middle", color: "#5a2e14", weight: "800" });
    // ghe của Út Sen
    const bob = Math.sin(t * 1.6) * 0.08 * s;
    ctx.save(); ctx.translate(0, bob);
    drawBoat(x + 0.6 * s, oy, s, "#5b3a22");
    ctx.fillStyle = "#b5402f"; ctx.fillRect(x - 1.5 * s, oy - 0.62 * s, 4.1 * s, 0.14 * s);                       // sọc sơn mạn ghe
    ctx.fillStyle = "#d8b27a";                                                                                  // mui ghe
    ctx.beginPath(); ctx.ellipse(x + 0.5 * s, oy - 0.5 * s, 1.1 * s, 0.8 * s, 0, Math.PI, 0); ctx.fill();
    ctx.strokeStyle = "rgba(110,80,40,.6)"; ctx.lineWidth = 1;
    for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.moveTo(x + 0.5 * s + i * 0.4 * s, oy - 0.5 * s); ctx.lineTo(x + 0.5 * s + i * 0.3 * s, oy - 0.5 * s - Math.sqrt(1 - (i * 0.36) ** 2) * 0.78 * s); ctx.stroke(); }
    // mắt ghe ở mũi
    ctx.fillStyle = "#f4efe2"; ctx.beginPath(); ctx.ellipse(x + 2.45 * s, oy - 0.62 * s, 0.24 * s, 0.14 * s, -0.2, 0, TAU); ctx.fill();
    ctx.fillStyle = "#c0392b"; ctx.beginPath(); ctx.arc(x + 2.5 * s, oy - 0.62 * s, 0.1 * s, 0, TAU); ctx.fill();
    ctx.fillStyle = "#111"; ctx.beginPath(); ctx.arc(x + 2.52 * s, oy - 0.62 * s, 0.05 * s, 0, TAU); ctx.fill();
    // đèn treo đầu mui
    ctx.strokeStyle = "#3b2a1a"; ctx.beginPath(); ctx.moveTo(x - 0.5 * s, oy - 0.9 * s); ctx.lineTo(x - 0.5 * s, oy - 1.6 * s); ctx.stroke();
    art.glow(x - 0.5 * s, oy - 0.75 * s, 1.1 * s, "rgba(255,200,110,.6)");
    ctx.fillStyle = "#e0533a"; CN.rrect(x - 0.65 * s, oy - 0.95 * s, 0.3 * s, 0.36 * s, 3); ctx.fill();
    ctx.restore();
    ctx.strokeStyle = "rgba(255,236,170,.55)"; ctx.lineWidth = 1; ctx.setLineDash([5, 4]);
    ctx.beginPath(); ctx.arc(x, v.sy(dp[1]), dr * s, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
  }

  // ---------------- nút hái: bông súng, điên điển, kèo nèo ----------------
  function lilyPad(x, y, rx, col) {
    ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(x, y, rx, rx * 0.22, 0, 0.2, TAU - 0.2); ctx.lineTo(x, y); ctx.fill();
  }

  function drawNodes(v, nodes) {
    const { s } = v, t = CN.now();
    (nodes || []).forEach((n, i) => {
      const x = v.sx(n.pos[0]), y = v.sy(n.pos[1]);
      if (x < -4 * s || x > v.w + 4 * s) return;
      const ready = n.ready !== false;
      const sway = Math.sin(t * 1.2 + i) * 0.05;
      if (ready) art.glow(x, y - 0.8 * s, 2.2 * s, "rgba(255,240,170,.35)");
      ctx.save(); ctx.globalAlpha = ready ? 1 : 0.6;
      if (n.kind === "bong_sung") {
        ctx.strokeStyle = "rgba(70,105,50,.7)"; ctx.lineWidth = Math.max(1, 0.08 * s); ctx.beginPath();
        for (const dx of [-0.6, 0.1, 0.7]) { ctx.moveTo(x + dx * s, y); ctx.quadraticCurveTo(x + (dx + 0.6) * s, y + 1.5 * s, x + dx * 0.5 * s, y + 3 * s); }
        ctx.stroke();
        lilyPad(x - 0.7 * s, y + 0.05 * s, 0.85 * s, "#3f7f3c"); lilyPad(x + 0.8 * s, y + 0.08 * s, 0.7 * s, "#4b8d44");
        if (ready) {
          ctx.strokeStyle = "#4d7a3a"; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y - 0.5 * s); ctx.stroke();
          ctx.save(); ctx.translate(x, y - 0.75 * s); ctx.rotate(sway); art.plant("bong_sung", 0, 0, 1.5 * s, { open: 0.5 }); ctx.restore();
        } else {
          ctx.fillStyle = "#b85a8c"; ctx.beginPath(); ctx.ellipse(x, y - 0.35 * s, 0.16 * s, 0.32 * s, sway, 0, TAU); ctx.fill();   // nụ khép
        }
      } else if (n.kind === "bong_dien_dien") {
        ctx.strokeStyle = "#6b5032"; ctx.lineWidth = Math.max(1.5, 0.14 * s); ctx.lineCap = "round"; ctx.beginPath();
        ctx.moveTo(x, y + 1.6 * s); ctx.lineTo(x, y - 1.4 * s);
        ctx.moveTo(x, y - 0.6 * s); ctx.lineTo(x - 1 * s, y - 1.5 * s);
        ctx.moveTo(x, y - 0.9 * s); ctx.lineTo(x + 1.1 * s, y - 1.7 * s);
        ctx.stroke(); ctx.lineCap = "butt";
        ctx.fillStyle = "#6f9e47";                                                                               // lá kép lông chim
        for (const [bx, by, ex, ey] of [[x, y - 0.6 * s, x - 1 * s, y - 1.5 * s], [x, y - 0.9 * s, x + 1.1 * s, y - 1.7 * s], [x, y - 0.4 * s, x, y - 1.6 * s]]) {
          for (let j = 1; j <= 5; j++) {
            const f = j / 6, px = bx + (ex - bx) * f, py = by + (ey - by) * f;
            ctx.beginPath(); ctx.ellipse(px - 0.16 * s, py, 0.14 * s, 0.06 * s, 0.3, 0, TAU); ctx.ellipse(px + 0.16 * s, py, 0.14 * s, 0.06 * s, -0.3, 0, TAU); ctx.fill();
          }
        }
        if (ready) { art.plant("bong_dien_dien", x - 0.9 * s, y - 1.2 * s, 1 * s); art.plant("bong_dien_dien", x + 1 * s, y - 1.4 * s, 1 * s); art.plant("bong_dien_dien", x + 0.1 * s, y - 1.7 * s, 0.9 * s); }
      } else if (n.kind === "keo_neo") {
        ctx.save(); ctx.translate(x, y - 0.6 * s); ctx.rotate(sway);
        art.plant("keo_neo", 0, 0, (ready ? 1.6 : 1.1) * s);
        ctx.restore();
        lilyPad(x, y + 0.05 * s, 0.6 * s, "#3d6e35");
      } else {
        lilyPad(x, y, 1.1 * s, "#3f8f4a");
        if (ready) ui.icon(n.kind, x, y - 0.45 * s, 1.3 * s);
      }
      ctx.restore();
      if (!ready && n.regrow_ticks) {
        const ty = y - 2.2 * s;
        ui.panel(x - 26, ty - 14, 52, 26, { r: 13, fill: "rgba(255,248,230,.85)", stroke: "rgba(80,60,30,.4)" });
        text(Math.ceil(n.regrow_ticks / 60) + "s", x, ty, { size: 18, align: "center", base: "middle", color: "#4a3418", weight: "700" });
      }
    });
  }

  // ---------------- cá ----------------
  const FISH_LEN = { ca_linh: 2.0, ca_loc: 3.6, ca_keo: 2.6 };   // dài hơn bán kính bắt một chút cho dễ nhìn; chỉ là hình
  function drawFish(v, fish) {
    const { s } = v, t = CN.now();
    (fish || []).forEach((f, i) => {
      const x = v.sx(f.pos[0]), y = v.sy(f.pos[1]) + Math.sin(t * 2 + i) * 0.12 * s;  // nhấp nhô: chỉ hình ảnh
      if (x < -4 * s || x > v.w + 4 * s) return;
      const a = ((f.heading_deg || 0) * Math.PI) / 180, flip = Math.cos(a) < 0;
      let rot = flip ? Math.PI - a : a;
      rot = Math.atan2(Math.sin(rot), Math.cos(rot));
      rot = Math.max(-0.5, Math.min(0.5, rot)) + Math.sin(t * 7 + i) * 0.05;
      const L = (FISH_LEN[f.kind] || 2.2) * s;
      if (f.kind === "ca_linh") {                                       // cá linh đi đàn: hai con nhỏ bơi kèm (chỉ hình ảnh)
        for (const [ox, oy, k] of [[-0.9, -0.55, 0.75], [-1.1, 0.5, 0.7]]) {
          art.fish("ca_linh", x + (flip ? -ox : ox) * L * 0.8, y + oy * L * 0.6 + Math.sin(t * 3 + i + ox) * 0.1 * s, L * k, flip, rot);
        }
      }
      art.fish(f.kind, x, y, L, flip, rot);
    });
  }

  // ---------------- Cá Sấu Năm Chèo (và loài quái của mở rộng) ----------------
  const lastX = {}, facing = {};
  function monsterNear(v, m, p) {
    if (!p || !p.pos || p.pos[1] < 10) return false;                // Cá Sấu chỉ đuổi khi người chơi ở d ≥ 10
    const r = (((v.meta.monsters || {}).species || {})[m.species ?? m.kind] || {}).detect_radius || 10;
    return m.state === "chase" || Math.hypot(m.pos[0] - p.pos[0], m.pos[1] - p.pos[1]) <= r;
  }

  function crocPath(s, sway, jaw) {
    ctx.beginPath();
    ctx.moveTo(-3.2 * s, sway);                                         // chóp đuôi
    ctx.quadraticCurveTo(-2.2 * s, sway * 0.6 - 0.25 * s, -1.2 * s, -0.42 * s);
    ctx.quadraticCurveTo(0, -0.62 * s, 1.1 * s, -0.36 * s);
    ctx.lineTo(1.5 * s, -0.42 * s);                                     // gò mắt
    ctx.lineTo(2.9 * s, -0.16 * s);                                     // mõm trên
    ctx.lineTo(2.9 * s, -0.02 * s);
    ctx.lineTo(1.4 * s, 0.02 * s);
    ctx.lineTo(2.8 * s, 0.1 * s + jaw);                                  // hàm dưới
    ctx.lineTo(2.7 * s, 0.22 * s + jaw);
    ctx.lineTo(1.1 * s, 0.36 * s);
    ctx.quadraticCurveTo(0, 0.6 * s, -1.2 * s, 0.38 * s);
    ctx.quadraticCurveTo(-2.2 * s, sway * 0.6 + 0.2 * s, -3.2 * s, sway);
    ctx.closePath();
  }

  function drawMonsters(v, monsters, player) {
    const { s } = v, t = CN.now();
    (monsters || []).forEach((m) => {
      const x = v.sx(m.pos[0]), y = v.sy(m.pos[1]);
      if (lastX[m.id] !== undefined && Math.abs(m.pos[0] - lastX[m.id]) > 1e-4) facing[m.id] = m.pos[0] > lastX[m.id] ? 1 : -1;
      lastX[m.id] = m.pos[0];
      if (x < -5 * s || x > v.w + 5 * s) return;
      const chase = m.state === "chase", near = monsterNear(v, m, player);
      ctx.save(); ctx.translate(x, y); ctx.scale(facing[m.id] || 1, 1);
      ctx.globalAlpha = m.state === "recoil" ? 0.55 : 1;
      const sway = Math.sin(t * (chase ? 9 : 4)) * 0.35 * s;
      if ((m.species ?? m.kind) === "ran") {                                           // rắn (mở rộng): thân uốn sóng
        ctx.strokeStyle = near ? PURPLE : "#6b5a2a"; ctx.lineWidth = 0.5 * s + (near ? 3 : 0); ctx.lineCap = "round";
        ctx.beginPath(); for (let i = 0; i <= 12; i++) { const u = -2.5 * s + i * 0.4 * s, yy = Math.sin(t * 6 + i * 0.8) * 0.3 * s; if (i) ctx.lineTo(u, yy); else ctx.moveTo(u, yy); } ctx.stroke();
        ctx.strokeStyle = "#8a7436"; ctx.lineWidth = 0.42 * s; ctx.stroke(); ctx.lineCap = "butt";
      } else {
        ctx.scale(1.45, 1.6);                                           // Cá Sấu to hơn cá thường (chỉ hình)
        const jaw = chase ? (0.25 + Math.sin(t * 10) * 0.12) * s : 0;
        // chân chèo
        ctx.fillStyle = "#3f5230";
        for (const [lx, ph] of [[0.7, 0], [-0.9, Math.PI]]) {
          ctx.save(); ctx.translate(lx * s, 0.35 * s); ctx.rotate(0.5 + Math.sin(t * (chase ? 10 : 5) + ph) * 0.5);
          ctx.fillRect(-0.1 * s, 0, 0.22 * s, 0.6 * s); ctx.restore();
        }
        if (near) { art.glow(0, 0, 3.6 * s, "rgba(162,107,255,.4)"); }
        const g = ctx.createLinearGradient(0, -0.6 * s, 0, 0.6 * s);
        g.addColorStop(0, "#3d5230"); g.addColorStop(0.55, "#5f7440"); g.addColorStop(1, "#b9b27a");
        crocPath(s, sway, jaw);
        ctx.fillStyle = g; ctx.fill();
        if (near) { ctx.strokeStyle = PURPLE; ctx.lineWidth = 1.6; ctx.stroke(); }
        if (chase) {                                                    // răng
          ctx.fillStyle = "#fffbe8";
          for (let i = 0; i < 5; i++) { const tx = 1.6 * s + i * 0.25 * s; ctx.beginPath(); ctx.moveTo(tx, -0.02 * s); ctx.lineTo(tx + 0.08 * s, 0.12 * s); ctx.lineTo(tx + 0.16 * s, -0.02 * s); ctx.fill(); }
        }
        ctx.fillStyle = "#2f3f24";                                      // vảy gai lưng
        for (let i = 0; i < 8; i++) { const u = -2.6 * s + i * 0.45 * s, top = i < 3 ? -0.3 * s + sway * (0.6 - i * 0.2) * 0.5 : -0.48 * s; ctx.beginPath(); ctx.moveTo(u - 0.14 * s, top + 0.06 * s); ctx.lineTo(u, top - 0.16 * s); ctx.lineTo(u + 0.14 * s, top + 0.06 * s); ctx.fill(); }
        ctx.fillStyle = chase ? "#ff3b3b" : "#f2e14b";
        ctx.beginPath(); ctx.arc(1.4 * s, -0.36 * s, 0.13 * s, 0, TAU); ctx.fill();
        ctx.fillStyle = "#111"; ctx.fillRect(1.38 * s, -0.46 * s, 0.05 * s, 0.2 * s);
      }
      ctx.restore();
      if (near) {
        ctx.font = "800 20px system-ui, sans-serif"; ctx.textAlign = "center"; ctx.lineWidth = 4; ctx.strokeStyle = "rgba(20,8,40,.85)";
        ctx.strokeText("Thủy quái!", x, y - 1.6 * s);
        text("Thủy quái!", x, y - 1.6 * s, { size: 20, align: "center", color: "#d9c2ff", weight: "800" });
      } else if (chase) text("!", x, y - 0.9 * s, { size: 24, align: "center", color: COLOR.danger, weight: "800" });
      if (m.state === "stunned") text("✦ ✦", x, y - 0.9 * s, { size: 18, align: "center", color: COLOR.gold });
    });
  }

  // ---------------- Út Sen: áo bà ba, khăn rằn, kính lặn, giỏ lưới ----------------
  function drawPlayer(v, snap) {
    const p = snap.player;
    if (!p || !p.pos) return null;
    const { s } = v, t = CN.now();
    const x = v.sx(p.pos[0]), y = v.sy(p.pos[1]);
    const under = p.at_surface === undefined ? p.pos[1] > (v.meta.surface_depth ?? 0.5) : !p.at_surface;
    if (under && t - lastBubble > 0.35) { bubbles.push({ x: p.pos[0], d: p.pos[1], born: t }); lastBubble = t; }
    ctx.strokeStyle = "rgba(255,250,240,.75)"; ctx.lineWidth = 1; ctx.beginPath();
    for (let i = bubbles.length - 1; i >= 0; i--) {
      const b = bubbles[i], age = t - b.born, d = b.d - 0.5 - age * 2.2;
      if (d < 0 || age > 4) { bubbles.splice(i, 1); continue; }
      const bx = v.sx(b.x + Math.sin(age * 3) * 0.2), by = v.sy(d), br = (0.12 + (i % 3) * 0.05) * s;
      ctx.moveTo(bx + br, by); ctx.arc(bx, by, br, 0, TAU);
    }
    ctx.stroke();
    if (p.invuln_ticks > 0 && Math.floor((snap.tick || 0) / 5) % 2) return [x, y];  // nhấp nháy khi vừa mất Máu

    const a = ((p.heading_deg || 0) * Math.PI) / 180;
    const moving = p.vel ? Math.hypot(p.vel[0], p.vel[1]) > 0.05 : true;
    // hướng mặt: theo heading; trên mặt nước giữ hướng ngang gần nhất
    const flip = Math.cos(a) < 0;
    let rot = under ? (flip ? Math.PI - a : a) : -Math.PI / 2 + 0.25;
    if (under) rot = Math.atan2(Math.sin(rot), Math.cos(rot));
    const kick = Math.sin(t * (moving ? 9 : 3)) * (moving ? 0.35 : 0.15);

    art.glow(x, y, 2.6 * s, "rgba(255,236,200,.28)");
    ctx.save(); ctx.translate(x, y); ctx.scale(PS, PS); if (flip) ctx.scale(-1, 1); ctx.rotate(rot);
    ctx.lineCap = "round";
    // khăn rằn bay phía sau
    const tail = Math.sin(t * 5) * 0.15 * s;
    art.khanRan(0.55 * s, -0.12 * s, -0.5 * s, -0.42 * s + tail, Math.max(3, 0.2 * s));
    // chân (quần đen) đạp nước
    ctx.strokeStyle = "#1f1f26"; ctx.lineWidth = 0.3 * s; ctx.beginPath();
    ctx.moveTo(-0.45 * s, -0.05 * s); ctx.lineTo(-1.2 * s, -0.05 * s + kick * s);
    ctx.moveTo(-0.45 * s, 0.08 * s); ctx.lineTo(-1.2 * s, 0.08 * s - kick * s); ctx.stroke();
    ctx.strokeStyle = "#e9b88f"; ctx.lineWidth = 0.22 * s; ctx.beginPath();
    ctx.moveTo(-1.2 * s, -0.05 * s + kick * s); ctx.lineTo(-1.45 * s, -0.08 * s + kick * 1.3 * s);
    ctx.moveTo(-1.2 * s, 0.08 * s - kick * s); ctx.lineTo(-1.45 * s, 0.05 * s - kick * 1.3 * s); ctx.stroke();
    // giỏ lưới trên lưng: đầy dần theo giỏ
    const cap = snap.hold_capacity || 12, held = snap.hold || [];
    const fill = Math.min(1, (snap.hold_count ?? held.length) / cap);
    ctx.fillStyle = "rgba(120,90,50,.35)"; CN.rrect(-0.55 * s, -0.78 * s, 0.85 * s, 0.5 * s, 0.12 * s); ctx.fill();
    held.slice(0, 6).forEach((k, i) => {
      ctx.fillStyle = CN.kc(CN.kindOf(k));
      ctx.beginPath(); ctx.arc(-0.42 * s + (i % 3) * 0.28 * s, -0.4 * s - Math.floor(i / 3) * 0.17 * s * fill * 2, 0.1 * s, 0, TAU); ctx.fill();
    });
    ctx.strokeStyle = "#a07a45"; ctx.lineWidth = 1; ctx.beginPath();
    for (let i = 0; i <= 4; i++) { const u = -0.55 * s + i * 0.21 * s; ctx.moveTo(u, -0.78 * s); ctx.lineTo(u, -0.28 * s); }
    for (let j = 0; j <= 2; j++) { const vv = -0.78 * s + j * 0.25 * s; ctx.moveTo(-0.55 * s, vv); ctx.lineTo(0.3 * s, vv); }
    ctx.stroke();
    ctx.lineWidth = 2; CN.rrect(-0.55 * s, -0.78 * s, 0.85 * s, 0.5 * s, 0.12 * s); ctx.stroke();
    // thân: áo bà ba màu kem, hàng nút, viền tay
    ctx.fillStyle = "#f3e7cf"; ctx.beginPath(); ctx.ellipse(0, 0, 0.62 * s, 0.3 * s, 0, 0, TAU); ctx.fill();
    ctx.strokeStyle = "#5a3b22"; ctx.lineWidth = 1; ctx.stroke();
    ctx.fillStyle = "#8a5a3a"; for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.arc(0.3 * s - i * 0.25 * s, 0.18 * s, 0.04 * s, 0, TAU); ctx.fill(); }
    // tay sải
    const stroke = Math.sin(t * (moving ? 6 : 2));
    ctx.strokeStyle = "#f3e7cf"; ctx.lineWidth = 0.2 * s; ctx.beginPath();
    ctx.moveTo(0.35 * s, 0.05 * s); ctx.lineTo(0.75 * s + stroke * 0.25 * s, 0.32 * s + stroke * 0.1 * s); ctx.stroke();
    ctx.strokeStyle = "#e9b88f"; ctx.lineWidth = 0.16 * s; ctx.beginPath();
    ctx.moveTo(0.75 * s + stroke * 0.25 * s, 0.32 * s + stroke * 0.1 * s); ctx.lineTo(0.98 * s + stroke * 0.3 * s, 0.34 * s + stroke * 0.12 * s); ctx.stroke();
    // đầu: tóc đen, kính lặn
    const hx = 0.88 * s;
    ctx.fillStyle = "#e9b88f"; ctx.beginPath(); ctx.arc(hx, 0, 0.3 * s, 0, TAU); ctx.fill();
    ctx.fillStyle = "#1a1416"; ctx.beginPath(); ctx.arc(hx - 0.04 * s, -0.04 * s, 0.31 * s, Math.PI * 0.55, Math.PI * 1.85); ctx.fill();
    ctx.beginPath(); ctx.ellipse(hx - 0.42 * s, -0.12 * s + tail * 0.4, 0.2 * s, 0.11 * s, 0.2, 0, TAU); ctx.fill();   // búi tóc
    ctx.strokeStyle = "#2a3b4c"; ctx.lineWidth = 0.07 * s; ctx.beginPath(); ctx.arc(hx, 0, 0.3 * s, -0.7, 0.5); ctx.stroke(); // quai kính
    ctx.fillStyle = "#7fd7ee"; CN.rrect(hx + 0.12 * s, -0.03 * s, 0.24 * s, 0.2 * s, 0.06 * s); ctx.fill();
    ctx.strokeStyle = "#24435a"; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,.75)"; ctx.fillRect(hx + 0.16 * s, 0, 0.06 * s, 0.06 * s);
    ctx.lineCap = "butt";
    ctx.restore();
    if (!under) {                                                        // vòng sóng quanh người khi nổi
      ctx.strokeStyle = "rgba(255,250,240,.7)"; ctx.lineWidth = 1.5;
      const r = (0.8 + (t * 0.8 % 1) * 0.8) * s;
      ctx.globalAlpha = 1 - (t * 0.8 % 1); ctx.beginPath(); ctx.ellipse(x, v.oy, r, r * 0.18, 0, 0, TAU); ctx.stroke(); ctx.globalAlpha = 1;
    }
    return [x, y - 0.3 * s];
  }

  function nearest(list, pos, r, ok) {
    let best = null, bd = r;
    (list || []).forEach((e) => {
      if (!ok(e)) return;
      const d = Math.hypot(e.pos[0] - pos[0], e.pos[1] - pos[1]);
      if (d <= bd) { bd = d; best = e; }
    });
    return best;
  }

  function drawHints(v, snap) {
    const p = snap.player;
    if (!p || !p.pos || snap.finished) return;
    const { meta, s } = v;
    const under = p.at_surface === undefined ? p.pos[1] > (meta.surface_depth ?? 0.5) : !p.at_surface;
    const dp = meta.dock_pos || [2, 0];
    if (Math.hypot(p.pos[0] - dp[0], p.pos[1] - dp[1]) <= (meta.dock_radius || 3)) {
      ui.hint(v.sx(dp[0]), v.sy(-1.8), "E", "Về ghe"); return;
    }
    if (!under) {
      const n = nearest(snap.nodes, p.pos, meta.interact_radius || 2, (n) => n.ready !== false);
      if (n) ui.hint(v.sx(n.pos[0]), v.sy(n.pos[1]) - 2.2 * s, "E", "Hái");
    } else if (!(p.catch_cd_ticks > 0)) {
      const f = nearest(snap.fish, p.pos, meta.catch_radius || 2, () => true);
      if (f) ui.hint(v.sx(f.pos[0]), v.sy(f.pos[1]) - 1.2 * s, "Space", "Bắt");
    }
  }

  CN.scenes.gather = {
    draw(w, h, snap) {
      const v = view(w, h, snap);
      CN.lastView = v;
      drawSky(v);
      drawWater(v);
      drawDock(v);
      drawNodes(v, snap.nodes);
      drawFish(v, snap.fish);
      drawMonsters(v, snap.monsters, snap.player);
      const at = drawPlayer(v, snap);
      drawHints(v, snap);
      CN.fx.anchor = at ? { x: at[0], y: at[1] - 1.4 * v.s } : null;
      ctx.fillStyle = COLOR.bg; // trả màu mặc định cho HUD
    },
  };
})(window.CN);
