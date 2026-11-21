"use strict";
/* Thành phần UI dùng chung: khung, vòng tiến độ, icon nguyên liệu/món, bong bóng gợi ý. Icon cá/bông vẽ bằng CN.art (core/art.js); hình khối cũ chỉ còn làm dự phòng cho loài lạ. */
(function (CN) {
  const { ctx, text, COLOR } = CN;

  function fishIcon(color, size, flip) {
    ctx.scale(flip ? -1 : 1, 1);
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.ellipse(0, 0, size * 0.42, size * 0.22, 0, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-size * 0.36, 0); ctx.lineTo(-size * 0.62, -size * 0.2); ctx.lineTo(-size * 0.62, size * 0.2); ctx.closePath(); ctx.fill();
    ctx.fillStyle = "#1b2630"; ctx.beginPath(); ctx.arc(size * 0.24, -size * 0.04, Math.max(1, size * 0.04), 0, Math.PI * 2); ctx.fill();
  }

  function flowerIcon(color, size) {
    ctx.fillStyle = color;
    for (let i = 0; i < 5; i++) {
      const a = (i / 5) * Math.PI * 2 - Math.PI / 2;
      ctx.beginPath(); ctx.arc(Math.cos(a) * size * 0.2, Math.sin(a) * size * 0.2, size * 0.17, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = "#fff4c2"; ctx.beginPath(); ctx.arc(0, 0, size * 0.12, 0, Math.PI * 2); ctx.fill();
  }

  CN.ui = {
    panel(x, y, w, h, o = {}) {
      ctx.fillStyle = o.fill || COLOR.panel; CN.rrect(x, y, w, h, o.r ?? 10); ctx.fill();
      ctx.strokeStyle = o.stroke || COLOR.line; ctx.lineWidth = Math.max(o.lineWidth || 1, CN.contrast.on ? 2 : 0); ctx.stroke();
    },

    // Cảnh báo (TICKET-04): biểu tượng tam giác "!" + chữ trong khung viền màu. Không chỉ dựa vào màu;
    // ở tương phản cao nền đen đặc, chữ trắng, viền dày. (x, y) là tâm.
    alert(x, y, label, color, o = {}) {
      const size = Math.max(18, o.size || 22), hc = CN.contrast.on;
      ctx.font = "800 " + size + "px system-ui, sans-serif";
      const tw = ctx.measureText(label).width, iw = size * 1.1, w = tw + iw + 30, h = size + 16;
      CN.ui.panel(x - w / 2, y - h / 2, w, h, { fill: hc ? "#000" : "rgba(12,16,22,.86)", stroke: color, lineWidth: hc ? 4 : 2, r: h / 2 });
      const ix = x - w / 2 + 12 + iw / 2, s2 = size * 0.5;
      ctx.fillStyle = color; ctx.beginPath();
      ctx.moveTo(ix, y - s2 * 0.95); ctx.lineTo(ix + s2, y + s2 * 0.85); ctx.lineTo(ix - s2, y + s2 * 0.85); ctx.closePath(); ctx.fill();
      text("!", ix, y + s2 * 0.5, { size: 18, align: "center", weight: "900", color: "#000", noOutline: true });
      text(label, ix + iw / 2 + 8, y + 1, { size, base: "middle", weight: "800", color: hc ? "#fff" : color });
      return w;
    },

    // Vòng tiến độ quanh (x, y); frac 1 = đầy.
    ring(x, y, r, frac, color, width = 4) {
      ctx.lineWidth = width;
      ctx.strokeStyle = "rgba(0,0,0,.35)"; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke();
      const f = Math.max(0, Math.min(1, frac));
      if (f > 0) { ctx.strokeStyle = color; ctx.beginPath(); ctx.arc(x, y, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * f); ctx.stroke(); }
    },

    // Màu theo phần còn lại: xanh -> vàng -> đỏ.
    heat(frac) { return frac > 0.5 ? COLOR.ok : frac > 0.25 ? COLOR.gold : COLOR.danger; },

    // Icon nguyên liệu (cá / bông) tâm (x, y), cỡ size px.
    icon(kind, x, y, size, flip = false) {
      ctx.save(); ctx.translate(x, y);
      if (CN.art && CN.art.hasFish(kind)) { ctx.restore(); CN.art.fish(kind, x, y, size * 1.05, flip); return; }
      if (CN.art && CN.KIND_NAME[kind]) { ctx.restore(); CN.art.plant(kind, x, y, size * 0.95); return; }
      if (String(kind).startsWith("ca_")) fishIcon(CN.kc(kind), size, flip); else flowerIcon(CN.kc(kind), size);
      ctx.restore();
    },

    // Icon món: dĩa + nguyên liệu chính.
    dish(dishId, x, y, size) {
      ctx.fillStyle = "#f5f1e8"; ctx.beginPath(); ctx.ellipse(x, y + size * 0.12, size * 0.5, size * 0.26, 0, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = "#c9c2b2"; ctx.lineWidth = 1; ctx.stroke();
      CN.ui.icon(CN.DISH_ICON[dishId] || "ca_linh", x, y, size * 0.8);
    },

    // Bong bóng trắng có đuôi chỉ xuống (x, y = mũi đuôi). Trả về tâm bong bóng.
    bubble(x, y, w, h) {
      const bx = x - w / 2, by = y - h - 8;
      ctx.fillStyle = "#fffdf6"; CN.rrect(bx, by, w, h, 8); ctx.fill();
      ctx.beginPath(); ctx.moveTo(x - 6, by + h - 1); ctx.lineTo(x, y); ctx.lineTo(x + 6, by + h - 1); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = "rgba(0,0,0,.25)"; ctx.lineWidth = 1; CN.rrect(bx, by, w, h, 8); ctx.stroke();
      return [x, by + h / 2];
    },

    // Gợi ý phím (chỉ hiển thị; sim mới quyết định có tác dụng hay không).
    hint(x, y, key, label) {
      ctx.font = "600 18px system-ui, sans-serif";
      const kw = Math.max(24, ctx.measureText(key).width + 10);
      const w = ctx.measureText(label).width + kw + 20;
      const bob = Math.sin(CN.now() * 4) * 2, top = y - 36 + bob;
      CN.ui.panel(x - w / 2, top, w, 32, { r: 16, fill: "rgba(12,20,28,.88)" });
      ctx.fillStyle = COLOR.gold; CN.rrect(x - w / 2 + 5, top + 4, kw, 24, 6); ctx.fill();
      text(key, x - w / 2 + 5 + kw / 2, top + 17, { size: 18, align: "center", base: "middle", color: "#1b1b1b", weight: "700", noOutline: true });
      text(label, x - w / 2 + kw + 12, top + 17, { size: 18, base: "middle", weight: "600" });
    },

    // Tên phím hiển thị trong khung nhỏ (dùng ở menu / Shop / intro).
    key(x, y, key) {
      ctx.font = "700 18px system-ui, sans-serif";
      const kw = Math.max(28, ctx.measureText(key).width + 12);
      ctx.fillStyle = COLOR.gold; CN.rrect(x, y - 13, kw, 26, 6); ctx.fill();
      text(key, x + kw / 2, y + 1, { size: 18, align: "center", base: "middle", color: "#1b1b1b", weight: "700", noOutline: true });
      return kw;
    },
  };
})(window.CN);
