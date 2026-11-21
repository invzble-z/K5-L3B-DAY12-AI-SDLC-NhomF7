"use strict";
/*
 * Shop cuối Ngày (phase "shop"): thẻ nâng cấp đọc từ meta.upgrades (= tuning.shop.upgrades), cấp đã mua (upgrades)
 * và cấp đang áp dụng (active_upgrades). Phím 1..n gửi `buy`, Enter gửi `shop_done`. Sim quyết định mua được hay không.
 */
(function (CN) {
  const { ctx, text, ui, COLOR, fmtTime } = CN;
  const INFO = {
    oxygen: { name: "Bình oxy", effect: (l) => l.oxygen_max_s + " s oxy" },
    hp: { name: "Áo phao", effect: (l) => l.hp_max + " Máu" },
    weapon: { name: "Lao xua", effect: (l) => "bán kính " + l.weapon_radius + " m, choáng " + l.stun_s + " s" },
    net: { name: "Vợt hút cá", effect: (l) => l.catch_radius + " m, " + l.max_schools + " đàn/lần" },
  };

  CN.shop = {
    // thứ tự thẻ = thứ tự phím 1..n
    ids(snap) { return Object.keys(((snap && snap.meta) || {}).upgrades || {}); },
  };

  CN.scenes.shop = {
    draw(w, h, snap) {
      ctx.fillStyle = "#2a1d14"; ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = "rgba(255,210,150,.05)";
      for (let x = 0; x < w; x += 48) ctx.fillRect(x, 0, 2, h);
      const pw = Math.min(980, w - 40), x0 = (w - pw) / 2;
      text("Shop nâng cấp" + (snap.day !== undefined ? " — cuối Ngày " + snap.day : ""), w / 2, 60, { size: 30, align: "center", weight: "800", color: COLOR.gold });
      text("Tiền: " + (snap.money ?? 0) + "k", x0, 106, { size: 22, weight: "700" });
      text("Tự đóng sau " + fmtTime(snap.time_left_ticks), x0 + pw, 106, { size: 18, align: "right", color: COLOR.muted });

      const upgrades = (snap.meta || {}).upgrades || {}, ids = CN.shop.ids(snap);
      const bought = snap.upgrades || {}, active = snap.active_upgrades || {};
      const gap = 18, cw = Math.min(300, (pw - gap * (ids.length - 1)) / Math.max(1, ids.length)), ch = 230;
      const cx0 = (w - (cw * ids.length + gap * (ids.length - 1))) / 2, cy = 136;
      ids.forEach((id, i) => {
        const levels = upgrades[id] || [], info = INFO[id] || { name: id, effect: () => "" };
        const cur = bought[id] || 0, next = levels.find((l) => l.level === cur + 1);
        const x = cx0 + i * (cw + gap);
        const afford = next && (snap.money ?? 0) >= next.price;
        ui.panel(x, cy, cw, ch, { fill: "rgba(255,248,235,.08)", stroke: afford ? COLOR.gold : COLOR.line, lineWidth: afford ? 2 : 1 });
        text(info.name, x + 18, cy + 38, { size: 22, weight: "800" });
        text("Cấp " + cur + "/" + levels.length, x + cw - 18, cy + 38, { size: 18, align: "right", color: COLOR.muted });
        if ((active[id] || 0) < cur) text("Có hiệu lực từ Ngày sau", x + 18, cy + 70, { size: 18, color: COLOR.oxy });
        if (next) {
          text("Lên cấp " + next.level + ": " + info.effect(next), x + 18, cy + 108, { size: 18 });
          text(next.price + "k", x + 18, cy + 150, { size: 26, weight: "800", color: afford ? COLOR.gold : COLOR.muted });
          const kw = ui.key(x + 18, cy + 196, String(i + 1));
          text(afford ? "Mua" : "Chưa đủ tiền", x + 26 + kw, cy + 197, { size: 18, base: "middle", color: afford ? COLOR.text : COLOR.muted });
        } else {
          text("Đã tối đa", x + 18, cy + 150, { size: 22, weight: "700", color: COLOR.ok });
        }
      });
      if (!ids.length) text("(chưa có dữ liệu shop.upgrades trong game.contract.json)", w / 2, cy + 100, { size: 18, align: "center", color: COLOR.muted });

      const stock = CN.inv.counts(snap.stock), left = Object.keys(stock);
      const sy = cy + ch + 50;
      text("Kho dư (bỏ sau Shop):", x0, sy, { size: 18, color: COLOR.muted });
      left.forEach((k, i) => { ui.icon(k, x0 + 220 + i * 80, sy - 6, 28); text("×" + stock[k], x0 + 240 + i * 80, sy, { size: 18, weight: "700" }); });
      if (!left.length) text("không còn", x0 + 220, sy, { size: 18, color: COLOR.muted });
      const kw = ui.key(w / 2 - 150, h - 44, "Enter");
      text("Đóng Shop, sang Ngày mới", w / 2 - 140 + kw, h - 43, { size: 18, base: "middle" });
      CN.fx.anchor = { x: w / 2, y: cy + ch + 36 };
    },
  };
  CN.hud.shop = () => {};
})(window.CN);
