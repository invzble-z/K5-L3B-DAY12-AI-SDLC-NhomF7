"use strict";
/* HUD buổi tối (Ticket-02 §2): đồng hồ ca, tiền ca, uy tín, món đang cầm, kho khả dụng. Món + kiên nhẫn từng bàn và bếp vẽ trong cảnh. */
(function (CN) {
  const { ctx, text, ui, COLOR, fmtTime, dname } = CN;

  function stars(rep) {
    let s = "";
    for (let i = 1; i <= 5; i++) s += rep >= i ? "★" : "☆";
    return s;
  }

  CN.hud.quan = function (w, h, snap) {
    const low = (snap.time_left_ticks || 0) <= 30 * 60;
    ui.panel(10, 8, 560, 52);
    text("⏱ " + fmtTime(snap.time_left_ticks), 24, 35, { size: 24, base: "middle", weight: "800", color: low ? COLOR.danger : COLOR.text });
    const shift = snap.shift_earned ?? snap.money ?? 0;
    text("Tiền ca " + shift + "k", 150, 35, { size: 20, base: "middle", weight: "700", color: COLOR.gold });
    const rep = snap.reputation ?? 0;
    text(stars(rep) + " " + rep.toFixed(1), 320, 35, { size: 20, base: "middle", color: COLOR.gold });
    // Chế độ day: điểm/tiền tổng chỉ cộng khi đóng ca (DaySim), nên trong ca chỉ hiện tiền ca để khỏi hiểu nhầm.
    if (snap.day === undefined) text("Điểm " + (snap.score ?? 0), 556, 35, { size: 18, base: "middle", align: "right" });
    else text("Ví " + (snap.money ?? 0) + "k", 556, 35, { size: 18, base: "middle", align: "right", color: COLOR.muted });
    if (snap.day !== undefined) { ui.panel(w - 130, 8, 120, 52); text("Ngày " + snap.day, w - 70, 35, { size: 20, align: "center", base: "middle", weight: "800", color: COLOR.gold }); }

    // kho khả dụng (v1.2: mảng cá thể có fresh → thêm thanh độ tươi từng cá thể + số "ươn", AC-P3-09)
    const fresh = CN.inv.hasFresh(snap.stock), below = CN.inv.spoiledBelow(snap);
    const stock = CN.inv.counts(snap.stock), kinds = Object.keys(stock);
    const cw = fresh ? 112 : 84, ph = fresh ? 86 : 66;
    const pw = Math.max(220, 90 + kinds.length * cw), y0 = h - ph - 10;
    ui.panel(10, y0, pw, ph);
    text("Kho", 24, y0 + 40, { size: 20, weight: "800" });
    if (!kinds.length) text("(trống)", 80, y0 + 40, { size: 18, color: COLOR.muted });
    kinds.forEach((k, i) => {
      const x0 = 80 + i * cw;
      CN.ui.icon(k, x0 + 18, y0 + 33, 32);
      text("×" + stock[k], x0 + 38, y0 + 40, { size: 20, weight: "700" });
      if (!fresh) return;
      const items = snap.stock.filter((it) => it.kind === k).sort((a, b) => b.fresh - a.fresh);
      const bw = Math.max(3, Math.min(10, (cw - 16) / items.length - 2));
      items.forEach((it, j) => {
        const bh = 14 * Math.max(0.08, it.fresh / 100);
        ctx.fillStyle = "rgba(0,0,0,.4)"; ctx.fillRect(x0 + j * (bw + 2), y0 + 50, bw, 14);
        ctx.fillStyle = CN.freshColor(it.fresh, below); ctx.fillRect(x0 + j * (bw + 2), y0 + 64 - bh, bw, bh);
      });
      const bad = items.filter((it) => it.fresh < below).length;
      if (bad) text(bad + " ươn", x0, y0 + 82, { size: 18, weight: "800", color: COLOR.danger });
    });

    // món đang cầm
    const hx = 10 + pw + 12;
    ui.panel(hx, y0, 280, 66);
    text("Tay", hx + 14, y0 + 40, { size: 20, weight: "800" });
    if (snap.hand) {
      const id = typeof snap.hand === "string" ? snap.hand : snap.hand.dish_id;
      ui.dish(id, hx + 82, y0 + 32, 40);
      text(dname(id), hx + 110, y0 + 40, { size: 18, weight: "600" });
    } else text("(trống)", hx + 66, y0 + 40, { size: 18, color: COLOR.muted });

    // Cảnh báo khách sắp giận (kiên nhẫn < 25%, TICKET-04): banner đếm số bàn, nhãn từng bàn vẽ trong cảnh.
    const patMax = (((snap.meta || {}).patience_s) || 60) * 60;
    const angry = (snap.customers || []).filter((c) => (c.state === "waiting" || c.state === "ordered") &&
      (c.patience_ticks_left ?? c.patience_ticks ?? patMax) / patMax < 0.25).map((c) => c.table_id).sort();
    if (angry.length) ui.alert(w / 2, 92, "Khách sắp giận: " + angry.join(", "), COLOR.danger, { size: 22 });

    text("Esc tạm dừng · H tương phản cao", w - 14, h - 16, { size: 18, align: "right", color: COLOR.muted });
  };
})(window.CN);
