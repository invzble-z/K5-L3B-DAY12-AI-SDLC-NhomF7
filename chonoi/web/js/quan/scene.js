"use strict";
/*
 * Cảnh buổi tối (quan): quán trên nhà bè nhìn từ trên xuống, x sang phải, z lên (bắc) (PRD-0 §3).
 * Sông đêm, sàn ván, đèn dây vàng, đèn lồng, khói bếp; 2 bếp cà ràng B1/B2, 4 bàn với ghế nhựa đỏ,
 * khách có bong bóng order + thanh kiên nhẫn, Út Sen bưng món.
 * Chỉ vẽ. Tên trường của khách theo docs/contracts/ (đang giả định: table_id, dish_id, state, patience_ticks_left).
 * Gợi ý "E Nấu / Bưng / Dọn món" chỉ để hiển thị; sim chọn đối tượng tương tác thật.
 * Chi tiết trang trí lấy từ CN.art.hash (cố định), không đụng Streams của mô phỏng.
 */
(function (CN) {
  const { ctx, text, ui, COLOR, art } = CN;
  const { hash: H, strHash, TAU } = art;
  CN.layout.quan = { top: 70, bottom: 84 };
  const KITCHEN = { x1: 7, z0: 6.8 };  // góc bếp (trên-trái) chỉ để tô nền; không phải tường chặn

  const dishOf = (c) => c.dish_id || c.dish || (c.order && c.order.dish_id) || null;
  const patienceLeft = (c) => (c.patience_ticks_left !== undefined ? c.patience_ticks_left : c.patience_ticks);

  function view(w, h, snap) {
    const meta = snap.meta || {};
    const b = meta.bounds || { x: [0, 16], z: [0, 10] };
    const X = b.x[1], Z = b.z[1];
    const { top, bottom } = CN.layout.quan;
    const s = Math.max(10, Math.min((w - 40) / X, (h - top - bottom) / Z));
    const ox = (w - s * X) / 2, oy = top;
    return { meta, X, Z, s, w, h, sx: (x) => ox + x * s, sy: (z) => oy + (Z - z) * s };
  }

  // ---------------- sông đêm quanh nhà bè ----------------
  function drawRiver(v) {
    const { w, h, s } = v, t = CN.now();
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, "#0b1726"); g.addColorStop(1, "#13293a");
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    // gợn sóng dài trôi ngang
    ctx.strokeStyle = "rgba(140,180,210,.12)"; ctx.lineWidth = 1.5; ctx.beginPath();
    for (let i = 0; i < 26; i++) {
      const y = H(i) * h, len = (40 + H(i + 40) * 90), x = ((H(i + 80) * (w + 200) + t * (8 + H(i + 9) * 10)) % (w + 200)) - 100;
      ctx.moveTo(x, y); ctx.quadraticCurveTo(x + len / 2, y - 3, x + len, y);
    }
    ctx.stroke();
    // ánh trăng vỡ trên mặt nước (bên phải)
    const mx = w - Math.max(60, (w - v.X * s) / 4);
    for (let i = 0; i < 14; i++) {
      const y = 90 + i * 34 + Math.sin(t * 1.3 + i) * 3, ww = (26 - i * 1.2) * (0.7 + 0.3 * Math.sin(t * 2 + i * 1.7));
      ctx.fillStyle = `rgba(230,236,255,${(0.32 - i * 0.018).toFixed(3)})`;
      ctx.fillRect(mx - ww / 2 + Math.sin(t + i) * 4, y, ww, 2.5);
    }
    // hoa đăng trôi chậm ở hai bên
    for (let i = 0; i < 6; i++) {
      const side = i % 2 ? w - 40 - H(i) * 60 : 30 + H(i) * 60;
      const y = ((H(i + 20) * h + t * (6 + H(i + 30) * 6)) % (h + 60)) - 30;
      art.glow(side, y, 26, "rgba(255,180,90,.45)");
      ctx.fillStyle = "#e8604c"; ctx.beginPath();
      for (let k = 0; k < 6; k++) { const a = (k / 6) * TAU + t * 0.2; ctx.ellipse(side + Math.cos(a) * 6, y + Math.sin(a) * 6, 5, 3, a, 0, TAU); }
      ctx.fill();
      ctx.fillStyle = "#ffe9a8"; ctx.beginPath(); ctx.arc(side, y, 3, 0, TAU); ctx.fill();
    }
  }

  // ---------------- sàn nhà bè (vẽ sẵn vào canvas phụ, chỉ vẽ lại khi đổi cỡ) ----------------
  let floorCv = null, floorKey = "";
  function rr(g, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
  }

  function paintFloor(g, v) {
    const { X, Z, s } = v, x0 = v.sx(0), y0 = v.sy(Z), W = X * s, Hh = Z * s;
    // phao gỗ / thùng phuy bên dưới sàn
    g.fillStyle = "#2a1d13"; rr(g, x0 - 0.45 * s, y0 - 0.45 * s, W + 0.9 * s, Hh + 0.9 * s, 0.3 * s); g.fill();
    g.fillStyle = "#3b2a1c";
    for (let i = 0; i < X; i += 2) { rr(g, v.sx(i) + 0.1 * s, y0 - 0.4 * s, 1.8 * s, 0.35 * s, 0.15 * s); g.fill(); rr(g, v.sx(i) + 0.1 * s, y0 + Hh + 0.05 * s, 1.8 * s, 0.35 * s, 0.15 * s); g.fill(); }
    // ván sàn chạy ngang
    const tones = ["#a77748", "#b28150", "#9b6d41", "#ad7c4c"];
    const rows = Math.round(Z * 2);
    for (let r = 0; r < rows; r++) {
      const y = y0 + (r * Hh) / rows, hh = Hh / rows;
      g.fillStyle = tones[Math.floor(H(r * 5) * tones.length)]; g.fillRect(x0, y, W, hh);
      g.fillStyle = "rgba(60,35,15,.35)"; g.fillRect(x0, y + hh - 1.5, W, 1.5);                      // khe ván
      let jx = H(r * 7) * 3;                                                                       // mối nối đầu ván
      while (jx < X) {
        const px = v.sx(jx);
        g.fillStyle = "rgba(60,35,15,.45)"; g.fillRect(px, y, 1.5, hh);
        g.fillStyle = "rgba(40,25,10,.6)"; g.fillRect(px - 5, y + hh * 0.3, 2, 2); g.fillRect(px + 4, y + hh * 0.3, 2, 2);
        jx += 2.5 + H(r * 13 + Math.floor(jx)) * 3;
      }
      g.strokeStyle = "rgba(255,230,190,.06)"; g.lineWidth = 1;                                     // vân gỗ
      g.beginPath(); for (let k = 0; k < 3; k++) { const yy = y + hh * (0.25 + k * 0.25); g.moveTo(x0, yy); g.bezierCurveTo(x0 + W * 0.3, yy + 2, x0 + W * 0.6, yy - 2, x0 + W, yy + 1); } g.stroke();
    }
    // góc bếp lát gạch tàu
    const kx1 = v.sx(KITCHEN.x1), ky1 = v.sy(KITCHEN.z0), tile = 0.5 * s;
    for (let yy = y0, j = 0; yy < ky1 - 0.5; yy += tile, j++) {
      for (let xx = x0, i = 0; xx < kx1 - 0.5; xx += tile, i++) {
        g.fillStyle = (i + j) % 2 ? "#b4613f" : "#a5563a";
        g.fillRect(xx, yy, Math.min(tile, kx1 - xx), Math.min(tile, ky1 - yy));
      }
    }
    g.strokeStyle = "rgba(255,225,190,.18)"; g.lineWidth = 1; g.beginPath();
    for (let xx = x0; xx <= kx1; xx += tile) { g.moveTo(xx, y0); g.lineTo(xx, ky1); }
    for (let yy = y0; yy <= ky1; yy += tile) { g.moveTo(x0, yy); g.lineTo(kx1, yy); }
    g.stroke();
    g.fillStyle = "#6b4a2b"; g.fillRect(x0, ky1 - 3, kx1 - x0, 6); g.fillRect(kx1 - 3, y0, 6, ky1 - y0);  // nẹp gỗ ranh giới bếp
    // quầy bếp sát tường trên: hũ mắm, thớt, rổ rau
    g.fillStyle = "#5a3d24"; g.fillRect(x0 + 0.2 * s, y0 + 0.08 * s, kx1 - x0 - 0.4 * s, 0.42 * s);
    for (let i = 0; i < 4; i++) {
      const jx = x0 + (0.7 + i * 0.45) * s, jy = y0 + 0.29 * s;
      g.fillStyle = "#4a3326"; g.beginPath(); g.arc(jx, jy, 0.17 * s, 0, TAU); g.fill();
      g.fillStyle = "#7a5a40"; g.beginPath(); g.arc(jx, jy, 0.1 * s, 0, TAU); g.fill();
    }
    g.fillStyle = "#c9a26b"; rr(g, x0 + 3.2 * s, y0 + 0.13 * s, 0.9 * s, 0.32 * s, 4); g.fill();          // thớt
    g.fillStyle = "#cfd6dc"; g.fillRect(x0 + 3.35 * s, y0 + 0.24 * s, 0.45 * s, 0.07 * s);
    g.fillStyle = "#8a6a3a"; g.beginPath(); g.arc(x0 + 6.2 * s, y0 + 0.29 * s, 0.22 * s, 0, TAU); g.fill();  // rổ rau
    for (let i = 0; i < 7; i++) { g.fillStyle = i % 2 ? "#6fae4a" : "#4f8f3c"; g.beginPath(); g.arc(x0 + 6.2 * s + Math.cos(i) * 0.1 * s, y0 + 0.29 * s + Math.sin(i * 2) * 0.1 * s, 0.07 * s, 0, TAU); g.fill(); }
    // lan can quanh bè, chừa lối lên ở giữa cạnh dưới
    const gate0 = v.sx(X / 2 - 1.2), gate1 = v.sx(X / 2 + 1.2);
    g.strokeStyle = "#6e4c2f"; g.lineWidth = 5; g.lineCap = "round"; g.beginPath();
    g.moveTo(gate0, y0 + Hh); g.lineTo(x0, y0 + Hh); g.lineTo(x0, y0); g.lineTo(x0 + W, y0); g.lineTo(x0 + W, y0 + Hh); g.lineTo(gate1, y0 + Hh);
    g.stroke(); g.lineCap = "butt";
    g.fillStyle = "#4a3220";
    for (const [px, py] of postsOf(v)) { g.beginPath(); g.arc(px, py, 0.13 * s, 0, TAU); g.fill(); }
    // cầu ván ra lối vào
    g.fillStyle = "#8d6a45"; g.fillRect(gate0 + 0.3 * s, y0 + Hh, gate1 - gate0 - 0.6 * s, 0.9 * s);
    g.strokeStyle = "rgba(50,30,15,.5)"; g.lineWidth = 1; g.beginPath();
    for (let i = 1; i < 5; i++) { const yy = y0 + Hh + i * 0.18 * s; g.moveTo(gate0 + 0.3 * s, yy); g.lineTo(gate1 - 0.3 * s, yy); }
    g.stroke();
    // phủ màu đêm: sàn tối lại để quầng đèn nổi lên
    g.fillStyle = "rgba(18,22,55,.3)"; g.fillRect(x0 - 0.5 * s, y0 - 0.5 * s, W + s, Hh + 1.5 * s);
  }

  function postsOf(v) {
    const pts = [], { X, Z } = v;
    for (let x = 0; x <= X; x += 2) { pts.push([v.sx(x), v.sy(Z)]); if (Math.abs(x - X / 2) > 1.2) pts.push([v.sx(x), v.sy(0)]); }
    for (let z = 2; z < Z; z += 2) { pts.push([v.sx(0), v.sy(z)]); pts.push([v.sx(X), v.sy(z)]); }
    return pts;
  }

  function drawFloor(v) {
    const dpr = window.devicePixelRatio || 1, key = [v.w, v.h, v.s, v.X, v.Z, dpr].join();
    if (key !== floorKey) {
      floorKey = key;
      floorCv = document.createElement("canvas");
      floorCv.width = Math.round(v.w * dpr); floorCv.height = Math.round(v.h * dpr);
      const g = floorCv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0);
      paintFloor(g, v);
    }
    ctx.drawImage(floorCv, 0, 0, v.w, v.h);
  }

  // ---------------- ánh đèn: đèn dây vàng, đèn lồng, quầng sáng trên sàn ----------------
  function wire(x0, y0, x1, y1, sag, n, seed, t) {
    ctx.strokeStyle = "rgba(30,20,10,.75)"; ctx.lineWidth = 1.2;
    const mx = (x0 + x1) / 2, my = (y0 + y1) / 2 + sag;
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo(mx, my, x1, y1); ctx.stroke();
    for (let i = 1; i < n; i++) {
      const f = i / n, bx = (1 - f) * (1 - f) * x0 + 2 * (1 - f) * f * mx + f * f * x1, by = (1 - f) * (1 - f) * y0 + 2 * (1 - f) * f * my + f * f * y1;
      const tw = 0.75 + 0.25 * Math.sin(t * 2.2 + (seed + i) * 1.7);
      art.glow(bx, by, 16 * tw, "rgba(255,214,120,.7)");
      ctx.fillStyle = `rgba(255,236,170,${tw.toFixed(2)})`; ctx.beginPath(); ctx.arc(bx, by, 3, 0, TAU); ctx.fill();
    }
  }

  function drawLights(v, layer) {
    const { X, Z, s } = v, t = CN.now();
    if (layer === "pools") {
      // quầng sáng ấm trên sàn (vẽ dưới đồ vật)
      art.glow(v.sx(3.5), v.sy(8.2), 4.2 * s, "rgba(255,150,70,.22)");
      for (const [x, z] of [[11, 4], [9, 2], [13, 6], [5, 3], [14, 9], [9, 8.5]]) art.glow(v.sx(x), v.sy(z), 3.2 * s, "rgba(255,200,120,.2)");
      return;
    }
    // dây đèn theo lan can + hai dây vắt qua khu bàn
    const posts = [[0, Z], [4, Z], [8, Z], [12, Z], [X, Z], [X, Z * 0.5], [X, 0], [0, 0], [0, Z * 0.5]];
    const seq = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [8, 0], [7, 8]];
    seq.forEach(([a, b], i) => {
      const [ax, az] = posts[a], [bx, bz] = posts[b];
      wire(v.sx(ax), v.sy(az), v.sx(bx), v.sy(bz), 0.35 * s, 5, i * 7, t);
    });
    wire(v.sx(KITCHEN.x1 + 0.5), v.sy(Z), v.sx(X), v.sy(0.8), 0.6 * s, 9, 60, t);
    wire(v.sx(X), v.sy(Z), v.sx(KITCHEN.x1 + 0.5), v.sy(0.8), 0.6 * s, 9, 90, t);
    // đèn lồng đỏ ở bốn góc
    [[0, Z], [X, Z], [0, 0], [X, 0]].forEach(([x, z], i) => {
      const px = v.sx(x), py = v.sy(z), sw = Math.sin(t * 1.5 + i) * 2;
      art.glow(px + sw, py, 1.6 * s, "rgba(255,110,60,.5)");
      ctx.fillStyle = "#c8322a"; ctx.beginPath(); ctx.ellipse(px + sw, py, 0.3 * s, 0.26 * s, 0, 0, TAU); ctx.fill();
      ctx.strokeStyle = "#f2c230"; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(px + sw, py, 0.3 * s, 0.26 * s, 0, 0, TAU); ctx.moveTo(px + sw, py - 0.26 * s); ctx.lineTo(px + sw, py + 0.26 * s); ctx.stroke();
    });
    // biển quán
    const bx = v.sx(X - 4), by = v.sy(Z) - 4;
    ctx.fillStyle = "#3b2414"; CN.rrect(bx - 118, by - 15, 236, 30, 6); ctx.fill();
    ctx.strokeStyle = "#f2c230"; ctx.lineWidth = 2; ctx.stroke();
    text("QUÁN ĂN CHỢ NỔI", bx, by + 1, { size: 18, align: "center", base: "middle", color: "#ffe39a", weight: "800" });
  }

  // ---------------- bếp cà ràng ----------------
  function drawSmoke(x, y, s, t, n, white, seed) {
    for (let i = 0; i < n; i++) {
      const a = (t * 0.45 + i / n + seed) % 1;
      const px = x + Math.sin(t * 1.1 + i * 2 + seed * 9) * 0.3 * s + a * 0.5 * s, py = y - a * 1.7 * s;
      const r = (0.12 + a * 0.32) * s, al = (white ? 0.3 : 0.2) * (1 - a);
      ctx.fillStyle = white ? `rgba(245,245,240,${al.toFixed(3)})` : `rgba(170,170,180,${al.toFixed(3)})`;
      ctx.beginPath(); ctx.arc(px, py, r, 0, TAU); ctx.fill();
    }
  }

  function drawStoves(v, snap) {
    const { s } = v, t = CN.now(), menu = snap.menu || {};
    (snap.stoves || []).forEach((st, si) => {
      const x = v.sx(st.pos[0]), y = v.sy(st.pos[1]);
      const flick = 0.8 + 0.2 * Math.sin(t * 13 + si * 3) * Math.sin(t * 7.3 + si);
      ctx.fillStyle = "rgba(0,0,0,.25)"; ctx.beginPath(); ctx.ellipse(x + 3, y + 5, 0.95 * s, 0.9 * s, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = "#9a4f2c"; ctx.beginPath(); ctx.arc(x, y, 0.9 * s, 0, TAU); ctx.fill();           // thân cà ràng đất nung
      ctx.strokeStyle = "#6e3519"; ctx.lineWidth = 3; ctx.stroke();
      ctx.fillStyle = "#b9663b"; ctx.beginPath(); ctx.arc(x, y, 0.72 * s, 0, TAU); ctx.fill();
      ctx.fillStyle = "#2a1610"; ctx.beginPath(); ctx.arc(x, y, 0.58 * s, 0, TAU); ctx.fill();          // lòng bếp
      art.glow(x, y, 1.1 * s * flick, "rgba(255,120,40,.75)");
      ctx.fillStyle = "#ff8a3d";
      for (let i = 0; i < 6; i++) { const a = (i / 6) * TAU + si; ctx.globalAlpha = 0.6 + 0.4 * Math.sin(t * 9 + i); ctx.beginPath(); ctx.arc(x + Math.cos(a) * 0.28 * s, y + Math.sin(a) * 0.28 * s, 0.09 * s, 0, TAU); ctx.fill(); }
      ctx.globalAlpha = 1;
      if (st.state !== "idle") {                                                                        // nồi đất trên bếp
        ctx.fillStyle = "#3a2c24"; ctx.beginPath(); ctx.arc(x, y, 0.56 * s, 0, TAU); ctx.fill();
        ctx.strokeStyle = "#5c4636"; ctx.lineWidth = 3; ctx.stroke();
        const kind = CN.DISH_ICON[st.dish] || "ca_linh";
        ctx.fillStyle = st.state === "ready" ? "#d9a35a" : "#b8743a"; ctx.beginPath(); ctx.arc(x, y, 0.44 * s, 0, TAU); ctx.fill();  // nước dùng
        ui.icon(kind, x, y, 0.55 * s);
        if (st.state === "cooking") {
          ctx.fillStyle = "rgba(255,240,210,.7)";
          for (let i = 0; i < 4; i++) { const a = (t * 1.7 + i / 4) % 1; ctx.beginPath(); ctx.arc(x + Math.cos(i * 2.1) * 0.25 * s, y + Math.sin(i * 1.7) * 0.22 * s, 0.05 * s + a * 0.05 * s, 0, TAU); ctx.fill(); }
        }
      }
      drawSmoke(x, y - 0.4 * s, s, t, st.state === "idle" ? 3 : 6, st.state !== "idle", si * 0.37);
      // bảng tên bếp
      ui.panel(x - 22, y + 0.95 * s, 44, 26, { r: 6, fill: "rgba(40,22,10,.85)", stroke: "rgba(242,194,48,.6)" });
      text(st.id || "B" + (si + 1), x, y + 0.95 * s + 14, { size: 18, align: "center", base: "middle", color: "#ffe39a", weight: "800" });
      if (st.state === "cooking") {
        const total = ((menu[st.dish] || {}).cook_s || 0) * 60;
        if (total > 0 && st.cook_ticks_left !== undefined) ui.ring(x, y, 1.02 * s, 1 - st.cook_ticks_left / total, "#ffb347", 6);
        if (st.cook_ticks_left !== undefined) {
          const label = Math.ceil(st.cook_ticks_left / 60) + " s";
          ui.panel(x + 0.95 * s, y - 15, 54, 30, { r: 15, fill: "rgba(255,248,230,.92)", stroke: "rgba(80,50,20,.4)" });
          text(label, x + 0.95 * s + 27, y + 1, { size: 18, align: "center", base: "middle", color: "#5a3010", weight: "800" });
        }
      } else if (st.state === "ready") {
        ui.ring(x, y, 1.02 * s, 1, COLOR.ok, 6);
        ui.dish(st.dish, x, y - 0.1 * s, 0.85 * s);
        const [bx, by] = ui.bubble(x, y - 1.0 * s, 86, 34);
        text("Chín!", bx, by + 1, { size: 18, align: "center", base: "middle", color: "#2f6b2f", weight: "800", noOutline: true });
      }
    });
  }

  // ---------------- bàn, ghế nhựa đỏ, khách ----------------
  const SHIRTS = ["#3f7cc4", "#d0774a", "#6aa35a", "#a0558f", "#e0b94a", "#4aa3a0", "#c94f5d"];

  function stool(x, y, s) {
    ctx.fillStyle = "#b72f2f"; CN.rrect(x - 0.32 * s, y - 0.32 * s, 0.64 * s, 0.64 * s, 0.14 * s); ctx.fill();
    ctx.fillStyle = "#dd4a42"; CN.rrect(x - 0.25 * s, y - 0.25 * s, 0.5 * s, 0.5 * s, 0.1 * s); ctx.fill();
    ctx.fillStyle = "#8c1f22"; ctx.fillRect(x - 0.12 * s, y - 0.03 * s, 0.24 * s, 0.06 * s);
  }

  function customer(x, y, s, c, t) {
    const hsh = strHash(c.id || c.table_id || "c"), shirt = SHIRTS[Math.floor(hsh * SHIRTS.length)];
    const eating = c.state === "eating";
    ctx.fillStyle = "rgba(0,0,0,.25)"; ctx.beginPath(); ctx.ellipse(x + 2, y + 4, 0.5 * s, 0.42 * s, 0, 0, TAU); ctx.fill();
    // tay với về phía bàn (bên phải)
    const chew = eating ? Math.sin(t * 8) * 0.06 * s : 0;
    ctx.strokeStyle = shirt; ctx.lineWidth = 0.17 * s; ctx.lineCap = "round"; ctx.beginPath();
    ctx.moveTo(x, y - 0.3 * s); ctx.lineTo(x + 0.5 * s + chew, y - 0.22 * s);
    ctx.moveTo(x, y + 0.3 * s); ctx.lineTo(x + 0.5 * s - chew, y + 0.22 * s); ctx.stroke();
    ctx.fillStyle = "#e9b88f"; ctx.beginPath(); ctx.arc(x + 0.55 * s + chew, y - 0.22 * s, 0.08 * s, 0, TAU); ctx.arc(x + 0.55 * s - chew, y + 0.22 * s, 0.08 * s, 0, TAU); ctx.fill();
    ctx.lineCap = "butt";
    ctx.fillStyle = shirt; ctx.beginPath(); ctx.ellipse(x, y, 0.3 * s, 0.44 * s, 0, 0, TAU); ctx.fill();   // vai
    if (hsh < 0.4) {                                                                                    // nón lá
      ctx.fillStyle = "#e6cf93"; ctx.beginPath(); ctx.arc(x + 0.05 * s, y, 0.38 * s, 0, TAU); ctx.fill();
      ctx.strokeStyle = "rgba(140,110,50,.6)"; ctx.lineWidth = 1;
      for (const r of [0.28, 0.18, 0.08]) { ctx.beginPath(); ctx.arc(x + 0.05 * s, y, r * s, 0, TAU); ctx.stroke(); }
    } else {
      ctx.fillStyle = "#e9b88f"; ctx.beginPath(); ctx.arc(x + 0.06 * s, y, 0.24 * s, 0, TAU); ctx.fill();
      ctx.fillStyle = hsh > 0.8 ? "#5a4636" : "#1c1618"; ctx.beginPath(); ctx.arc(x + 0.02 * s, y, 0.24 * s, Math.PI * 0.4, Math.PI * 1.6); ctx.fill();
    }
  }

  function patienceBar(cx, y, wd, frac, t) {
    const col = frac < 0.25 ? (Math.floor(t * 4) % 2 ? "#ff8a80" : COLOR.danger) : frac < 0.5 ? COLOR.gold : COLOR.ok;
    ctx.fillStyle = "rgba(0,0,0,.2)"; CN.rrect(cx - wd / 2, y, wd, 8, 4); ctx.fill();
    if (frac > 0) { ctx.fillStyle = col; CN.rrect(cx - wd / 2, y, Math.max(8, wd * Math.min(1, frac)), 8, 4); ctx.fill(); }
  }

  function drawTables(v, snap) {
    const { meta, s } = v, t = CN.now();
    const patMax = (meta.patience_s || 60) * 60;
    const alerts = [];   // nhãn "Sắp giận!" vẽ sau cùng để bàn/biển số vẽ sau không đè lên
    const byTable = {};
    (snap.customers || []).forEach((c) => { if (c.table_id) byTable[c.table_id] = c; });
    (snap.tables || []).forEach((tb, ti) => {
      const x = v.sx(tb.pos[0]), y = v.sy(tb.pos[1]);
      const c = byTable[tb.id];
      stool(x + 1.2 * s, y, s);
      if (!c) stool(x - 1.2 * s, y, s);
      // mặt bàn gỗ tròn
      ctx.fillStyle = "rgba(0,0,0,.28)"; ctx.beginPath(); ctx.arc(x + 4, y + 6, 0.88 * s, 0, TAU); ctx.fill();
      ctx.fillStyle = "#7b4a26"; ctx.beginPath(); ctx.arc(x, y, 0.88 * s, 0, TAU); ctx.fill();
      ctx.fillStyle = "#94603a"; ctx.beginPath(); ctx.arc(x, y, 0.78 * s, 0, TAU); ctx.fill();
      ctx.strokeStyle = "rgba(60,30,10,.3)"; ctx.lineWidth = 1;
      for (const r of [0.6, 0.42, 0.24]) { ctx.beginPath(); ctx.arc(x, y, r * s, 0.3 * ti, 0.3 * ti + 5); ctx.stroke(); }
      // ống đũa, chén nước mắm, đèn dầu nhỏ
      ctx.fillStyle = "#d9c08a"; ctx.beginPath(); ctx.arc(x + 0.35 * s, y - 0.4 * s, 0.11 * s, 0, TAU); ctx.fill();
      ctx.fillStyle = "#3a2010"; for (let i = 0; i < 4; i++) ctx.fillRect(x + 0.3 * s + (i % 2) * 0.06 * s, y - 0.45 * s + (i >> 1) * 0.06 * s, 2, 2);
      ctx.fillStyle = "#f5f1e8"; ctx.beginPath(); ctx.arc(x + 0.4 * s, y + 0.38 * s, 0.1 * s, 0, TAU); ctx.fill();
      ctx.fillStyle = "#c46a2a"; ctx.beginPath(); ctx.arc(x + 0.4 * s, y + 0.38 * s, 0.06 * s, 0, TAU); ctx.fill();
      const fl = 0.85 + 0.15 * Math.sin(t * 11 + ti * 2);
      art.glow(x - 0.05 * s, y - 0.05 * s, 1.0 * s * fl, "rgba(255,200,110,.5)");
      ctx.fillStyle = "#ffe08a"; ctx.beginPath(); ctx.arc(x - 0.05 * s, y - 0.05 * s, 0.07 * s, 0, TAU); ctx.fill();
      // bảng số bàn
      ui.panel(x - 22, y + 0.95 * s, 44, 26, { r: 6, fill: "rgba(40,22,10,.85)", stroke: "rgba(242,194,48,.6)" });
      text(tb.id, x, y + 0.95 * s + 14, { size: 18, align: "center", base: "middle", color: "#ffe39a", weight: "800" });
      if (!c) return;
      const cx = x - 1.2 * s;
      stool(cx, y, s);
      customer(cx, y, s, c, t);
      if (c.state === "eating") {                                                                       // tô món trên bàn + hơi nóng
        ui.dish(dishOf(c), x - 0.3 * s, y + 0.05 * s, 0.7 * s);
        drawSmoke(x - 0.3 * s, y - 0.1 * s, s * 0.6, t, 3, true, ti * 0.3);
        const [bx, by] = ui.bubble(x, y - 1 * s, 96, 34);
        text("Đang ăn", bx, by + 1, { size: 18, align: "center", base: "middle", color: "#2f6b2f", weight: "700", noOutline: true });
        return;
      }
      const [bx, by] = ui.bubble(x, y - 1 * s, 76, 62);                                                 // bong bóng order + kiên nhẫn
      ui.dish(dishOf(c), bx, by - 7, 36);
      const left = patienceLeft(c);
      if (left !== undefined) patienceBar(bx, by + 17, 60, left / patMax, t);
      if (left !== undefined && left / patMax < 0.25) alerts.push([bx, by - 52]);   // TICKET-04
    });
    alerts.forEach(([ax, ay]) => ui.alert(ax, ay, "Sắp giận!", COLOR.danger, { size: 18 }));
  }

  // ---------------- Út Sen (nhìn từ trên): khăn rằn quấn đầu, áo bà ba, bưng món ----------------
  let lastPos = null, faceA = -Math.PI / 2;
  function drawPlayer(v, snap) {
    const p = snap.player;
    if (!p || !p.pos) return null;
    const { s } = v, x = v.sx(p.pos[0]), y = v.sy(p.pos[1]), t = CN.now();
    let moving = false;
    if (lastPos) {
      const dx = p.pos[0] - lastPos[0], dz = p.pos[1] - lastPos[1];
      if (Math.hypot(dx, dz) > 1e-3) { faceA = Math.atan2(-dz, dx); moving = true; }
    }
    lastPos = p.pos.slice();
    if (v.meta.interact_radius) {
      ctx.strokeStyle = "rgba(255,236,170,.4)"; ctx.lineWidth = 1; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.arc(x, y, v.meta.interact_radius * s, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
    }
    art.glow(x, y, 1.3 * s, "rgba(255,220,160,.25)");
    ctx.fillStyle = "rgba(0,0,0,.3)"; ctx.beginPath(); ctx.ellipse(x + 3, y + 5, 0.5 * s, 0.45 * s, 0, 0, TAU); ctx.fill();
    ctx.save(); ctx.translate(x, y); ctx.rotate(faceA);
    const step = moving ? Math.sin(t * 12) * 0.12 * s : 0;
    ctx.fillStyle = "#1f1f26";                                                                          // chân bước
    ctx.beginPath(); ctx.ellipse(step, -0.2 * s, 0.16 * s, 0.1 * s, 0, 0, TAU); ctx.ellipse(-step, 0.2 * s, 0.16 * s, 0.1 * s, 0, 0, TAU); ctx.fill();
    ctx.strokeStyle = "#f3e7cf"; ctx.lineWidth = 0.17 * s; ctx.lineCap = "round"; ctx.beginPath();     // tay đưa ra trước
    const reach = snap.hand ? 0.55 : 0.25;
    ctx.moveTo(0, -0.34 * s); ctx.lineTo(reach * s, -0.22 * s); ctx.moveTo(0, 0.34 * s); ctx.lineTo(reach * s, 0.22 * s); ctx.stroke(); ctx.lineCap = "butt";
    ctx.fillStyle = "#f3e7cf"; ctx.beginPath(); ctx.ellipse(0, 0, 0.3 * s, 0.46 * s, 0, 0, TAU); ctx.fill();   // áo bà ba
    ctx.strokeStyle = "#5a3b22"; ctx.lineWidth = 1.2; ctx.stroke();
    // đầu quấn khăn rằn (ca rô đen trắng, cắt theo hình tròn)
    ctx.fillStyle = "#1c1618"; ctx.beginPath(); ctx.arc(0.02 * s, 0, 0.22 * s, 0, TAU); ctx.fill();   // tóc
    ctx.save(); ctx.beginPath(); ctx.arc(0.04 * s, 0, 0.19 * s, 0, TAU); ctx.clip();
    ctx.fillStyle = "#1d1d22"; ctx.fillRect(-0.3 * s, -0.3 * s, 0.6 * s, 0.6 * s);
    ctx.fillStyle = "#f2efe6"; const c = 0.075 * s;
    for (let i = 0; i < 6; i++) for (let j = 0; j < 6; j++) if ((i + j) % 2 === 0) ctx.fillRect(-0.3 * s + i * c, -0.3 * s + j * c, c, c);
    ctx.restore();
    art.khanRan(-0.14 * s, 0, -0.42 * s, Math.sin(t * 6) * 0.06 * s, Math.max(3, 0.1 * s));                  // đuôi khăn
    ctx.restore();
    if (snap.hand) {
      const hx = x + Math.cos(faceA) * 0.62 * s, hy = y + Math.sin(faceA) * 0.62 * s;
      ui.dish(typeof snap.hand === "string" ? snap.hand : snap.hand.dish_id, hx, hy, 0.85 * s);
      drawSmoke(hx, hy - 0.1 * s, s * 0.5, t, 3, true, 0.5);
    }
    return [x, y];
  }

  function drawHint(v, snap) {
    const p = snap.player, r = v.meta.interact_radius || 1.5;
    if (!p || !p.pos || snap.finished) return;
    const near = (e) => Math.hypot(e.pos[0] - p.pos[0], e.pos[1] - p.pos[1]);
    const byTable = {};
    (snap.customers || []).forEach((c) => { if (c.table_id) byTable[c.table_id] = c; });
    const cands = [];
    (snap.stoves || []).forEach((st) => {
      if (near(st) > r) return;
      // bếp sát tường trên: gợi ý vẽ BÊN DƯỚI bếp để không đè bong bóng "Chín!" và thanh HUD
      if (st.state === "ready" && !snap.hand) cands.push([near(st), 0, st, "Bưng", -2.3]);
      else if (st.state === "idle" && !snap.hand) cands.push([near(st), 0, st, "Nấu", -2.3]);
    });
    (snap.tables || []).forEach((tb) => {
      const c = byTable[tb.id];
      if (near(tb) <= r && c && c.state !== "eating" && snap.hand) cands.push([near(tb), 1, tb, "Dọn món", 2.4]);
    });
    cands.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    if (cands.length) { const [, , e, label, up] = cands[0]; ui.hint(v.sx(e.pos[0]), v.sy(e.pos[1]) - up * v.s, "E", label); }
  }

  function vignette(v) {
    const { w, h } = v;
    const g = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.35, w / 2, h / 2, Math.max(w, h) * 0.75);
    g.addColorStop(0, "rgba(5,10,25,0)"); g.addColorStop(1, "rgba(5,10,25,.55)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
  }

  CN.scenes.quan = {
    draw(w, h, snap) {
      const v = view(w, h, snap);
      CN.lastView = v;
      drawRiver(v);
      drawFloor(v);
      drawLights(v, "pools");
      drawLights(v, "strings");     // vẽ trước đồ vật để bong bóng order luôn đọc rõ
      drawStoves(v, snap);
      drawTables(v, snap);
      const at = drawPlayer(v, snap);
      vignette(v);
      drawHint(v, snap);
      CN.fx.anchor = at ? { x: at[0], y: at[1] - v.s } : null;
    },
  };
})(window.CN);
