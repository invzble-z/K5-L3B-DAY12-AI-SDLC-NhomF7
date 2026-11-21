"use strict";
/* Tiện ích vẽ dùng chung: canvas, bảng màu, tên loài/món, chữ, thanh, khung bo góc, thời gian. */
window.CN = window.CN || { scenes: {}, hud: {}, layout: {} };
(function (CN) {
  const cv = document.getElementById("c");
  const ctx = cv.getContext("2d");
  CN.cv = cv;
  CN.ctx = ctx;

  CN.COLOR = {
    bg: "#10161c", panel: "rgba(12,20,28,.74)", line: "rgba(255,255,255,.18)", text: "#e8eef2", muted: "#9fb3c0",
    gold: "#f2c230", oxy: "#4fc3f7", danger: "#ef5350", hp: "#ff6b81", ok: "#7bc67b", player: "#ff8a3d",
  };
  // Chế độ tương phản cao (TICKET-04): nền khung đen đặc, chữ trắng có viền đen, viền dày, màu bão hòa.
  // Cảnh báo luôn có chữ + biểu tượng nên không chỉ dựa vào màu. Lựa chọn lưu trong localStorage; ?contrast=1|0 ghi đè.
  const BASE_COLOR = { ...CN.COLOR };
  const HC_COLOR = {
    bg: "#000000", panel: "rgba(0,0,0,.94)", line: "#ffffff", text: "#ffffff", muted: "#f2f2f2",
    gold: "#ffd60a", oxy: "#64d2ff", danger: "#ff453a", hp: "#ff6482", ok: "#30d158", player: "#ff9f0a",
  };
  CN.contrast = {
    on: false,
    set(v) {
      this.on = !!v;
      Object.assign(CN.COLOR, this.on ? HC_COLOR : BASE_COLOR);   // sửa tại chỗ: mọi file đã giữ tham chiếu CN.COLOR
      try { localStorage.setItem("cn.contrast", this.on ? "1" : "0"); } catch (e) { /* chế độ riêng tư: bỏ qua */ }
    },
    toggle() { this.set(!this.on); },
  };
  (function initContrast() {
    const q = new URLSearchParams(location.search).get("contrast");
    let saved = null;
    try { saved = localStorage.getItem("cn.contrast"); } catch (e) { /* không đọc được: mặc định tắt */ }
    const v = q === "1" || q === "0" ? q : saved;
    if (v === "1") { CN.contrast.on = true; Object.assign(CN.COLOR, HC_COLOR); }
  })();

  CN.KIND_COLOR = { ca_loc: "#7c9a52", ca_linh: "#d6e6f2", ca_keo: "#d9a066", bong_dien_dien: "#f2c230", bong_sung: "#e8799c", keo_neo: "#8fcf6b" };
  CN.KIND_NAME = { ca_loc: "cá lóc", ca_linh: "cá linh", ca_keo: "cá kèo", bong_dien_dien: "điên điển", bong_sung: "bông súng", keo_neo: "kèo nèo" };
  // Chỉ là chữ hiển thị; công thức, giá, thời gian nấu nằm trong game.contract.json (sim đọc).
  CN.DISH_NAME = {
    ca_loc_nuong_trui: "Cá lóc nướng trui", goi_bong_sung: "Gỏi bông súng", lau_ca_linh_dien_dien: "Lẩu cá linh bông điên điển",
    canh_chua_ca_loc: "Canh chua cá lóc", ca_keo_nuong: "Cá kèo nướng muối ớt", lau_mam: "Lẩu mắm miền Tây",
  };
  CN.DISH_ICON = {
    ca_loc_nuong_trui: "ca_loc", goi_bong_sung: "bong_sung", lau_ca_linh_dien_dien: "ca_linh",
    canh_chua_ca_loc: "bong_dien_dien", ca_keo_nuong: "ca_keo", lau_mam: "keo_neo",
  };
  CN.kc = (k) => CN.KIND_COLOR[k] || "#bbbbbb";
  CN.kname = (k) => CN.KIND_NAME[k] || k;
  CN.dname = (d) => CN.DISH_NAME[d] || d || "?";

  // Đồng hồ chỉ dùng cho hiệu ứng hình (sóng, nhấp nháy); không bao giờ đi vào luật.
  CN.now = () => performance.now() / 1000;

  CN.fit = function () {
    const dpr = window.devicePixelRatio || 1;
    const w = innerWidth, h = innerHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) {
      cv.width = Math.round(w * dpr);
      cv.height = Math.round(h * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return [w, h];
  };

  CN.text = function (s, x, y, o = {}) {
    ctx.font = (o.weight || "") + " " + (o.size || 14) + "px system-ui, sans-serif";
    ctx.fillStyle = o.color || CN.COLOR.text;
    ctx.textAlign = o.align || "left";
    ctx.textBaseline = o.base || "alphabetic";
    if (CN.contrast.on && !o.noOutline) {   // viền đen để chữ nổi trên mọi nền cảnh
      ctx.lineJoin = "round"; ctx.lineWidth = Math.max(3, (o.size || 14) / 6); ctx.strokeStyle = "#000";
      ctx.strokeText(s, x, y);
    }
    ctx.fillText(s, x, y);
  };

  CN.rrect = function (x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  };

  CN.bar = function (x, y, w, h, frac, color, label) {
    frac = Math.max(0, Math.min(1, frac));
    ctx.fillStyle = "rgba(0,0,0,.45)"; CN.rrect(x, y, w, h, h / 2); ctx.fill();
    if (frac > 0) { ctx.fillStyle = color; CN.rrect(x, y, Math.max(h, w * frac), h, h / 2); ctx.fill(); }
    ctx.strokeStyle = "rgba(255,255,255,.45)"; ctx.lineWidth = 1; CN.rrect(x + .5, y + .5, w - 1, h - 1, h / 2); ctx.stroke();
    if (label) CN.text(label, x + w / 2, y + h / 2 + 1, { size: 18, align: "center", base: "middle", weight: "700" });
  };

  CN.fmtTime = function (ticks) {
    const s = Math.ceil((ticks || 0) / 60);
    return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
  };

  // Kho/giỏ theo hai schema (docs/contracts §2): v1.0/v1.1 là mảng tên loài (giỏ) hoặc map loài → số (kho);
  // v1.2 là mảng cá thể {id, kind, fresh}. Client chỉ đọc để vẽ; ngưỡng "ươn" lấy từ tuning.freshness.
  CN.kindOf = (x) => (x && typeof x === "object" ? x.kind : x);
  CN.inv = {
    counts(v) {
      const c = {};
      if (Array.isArray(v)) v.forEach((x) => { const k = CN.kindOf(x); c[k] = (c[k] || 0) + 1; });
      else if (v) for (const k of Object.keys(v)) if (v[k] > 0) c[k] = v[k];
      return c;
    },
    hasFresh: (v) => Array.isArray(v) && v.some((x) => x && typeof x === "object" && typeof x.fresh === "number"),
    spoiledBelow: (snap) => ((snap && snap.freshness) || {}).spoiled_below ?? 30,
  };
  // Màu độ tươi: ươn (< ngưỡng) đỏ, dưới 60 vàng, còn lại xanh. Luôn đi kèm số hoặc chữ "ươn", không chỉ dựa vào màu.
  CN.freshColor = (f, below) => (f < below ? CN.COLOR.danger : f < 60 ? CN.COLOR.gold : CN.COLOR.ok);

  CN.brief = function (d) {
    try { const s = JSON.stringify(d); return s.length > 60 ? s.slice(0, 57) + "…" : s; } catch (e) { return ""; }
  };
})(window.CN);
