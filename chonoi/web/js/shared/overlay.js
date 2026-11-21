"use strict";
/* Lớp phủ chung: nhãn MOCK, mất kết nối, lỗi luật, nhật ký sự kiện (phím `), thẻ hết buổi khi chạy riêng gather/quan. */
(function (CN) {
  const { ctx, text, ui, COLOR, kname, brief } = CN;
  const REASON = { docked: "Đã về ghe", time: "Hết giờ", fainted: "Ngất — mất cả giỏ", error: "Luật báo lỗi" };

  function eventLog(w, h, snap) {
    const ev = (snap.events || []).slice(-8);
    ui.panel(w - 560, h - 120 - ev.length * 22, 550, ev.length * 22 + 16, { fill: "rgba(0,0,0,.6)" });
    ev.forEach((e, i) => text(`t${e.tick} ${e.phase || ""} ${e.name} ${brief(e.data)}`, w - 550, h - 100 - (ev.length - 1 - i) * 22,
      { size: 14, color: "rgba(232,238,242,.85)" }));   // công cụ debug cho nhóm, không phải HUD người chơi
  }

  function finishedCard(w, h, snap) {
    if (snap.day !== undefined || !snap.finished) return;   // chế độ day: Summary ở screens.js
    ctx.fillStyle = "rgba(8,12,18,.6)"; ctx.fillRect(0, 0, w, h);
    const cw = 520, ch = 260, x = (w - cw) / 2, y = (h - ch) / 2;
    ui.panel(x, y, cw, ch, { fill: "rgba(20,28,36,.96)", r: 14 });
    const gather = (snap.phase || snap.mode) === "gather";
    text(gather ? "Buổi sáng kết thúc" : "Đóng quán", x + cw / 2, y + 52, { size: 30, align: "center", weight: "800", color: COLOR.gold });
    text(REASON[snap.reason] || snap.reason || "", x + cw / 2, y + 90, { size: 20, align: "center" });
    if (gather) {
      const items = Object.entries(CN.inv.counts(snap.hold));
      text("Mang về quán:", x + 40, y + 136, { size: 18, color: COLOR.muted });
      if (!items.length) text("(không có gì)", x + 180, y + 136, { size: 18, color: COLOR.muted });
      items.forEach(([k, n], i) => { ui.icon(k, x + 196 + i * 80, y + 130, 28); text("×" + n, x + 214 + i * 80, y + 137, { size: 18, weight: "700" }); });
    } else {
      const st = CN.screens.stats;
      text("Thu " + (snap.earned ?? 0) + "k · uy tín " + (snap.reputation ?? 0).toFixed(1) + " · điểm " + (snap.score ?? 0), x + cw / 2, y + 136, { size: 20, align: "center" });
      text("Phục vụ " + st.served + " khách · " + st.left + " khách bỏ đi", x + cw / 2, y + 172, { size: 18, align: "center", color: COLOR.muted });
    }
    text("R chơi lại · M về menu", x + cw / 2, y + ch - 24, { size: 18, align: "center", color: COLOR.muted });
  }

  CN.overlay = {
    draw(w, h, snap) {
      const st = CN.state;
      if (CN.debug) eventLog(w, h, snap);
      finishedCard(w, h, snap);
      if (st.mock) text("MOCK: mock/" + st.mock + ".json · P bật/tắt tạm dừng · R đọc lại", w - 14, h - 44, { size: 18, align: "right", color: "#ffd166" });
      if (st.offline) text(st.mock ? "Không đọc được file mock (xem console)" : "Mất kết nối tới máy chủ (đã tắt chưa?)", w / 2, 130, { align: "center", color: "#ff8a80", size: 20 });
      if (snap.error) text("Luật của nhóm báo lỗi — xem terminal. R để chơi lại.", w / 2, 160, { align: "center", color: "#ff8a80", size: 20 });
    },
  };
})(window.CN);
