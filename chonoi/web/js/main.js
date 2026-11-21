"use strict";
/*
 * Vòng vẽ: sự kiện mới -> màn hình (menu/intro) -> cảnh theo pha (gather/quan/shop) -> HUD -> chữ nổi -> lớp phủ.
 * Thêm pha mới = đăng ký CN.scenes[pha] và CN.hud[pha] trong file riêng, thêm <script> vào index.html.
 */
(function (CN) {
  const { ctx, text, COLOR } = CN;

  function frame() {
    requestAnimationFrame(frame);  // đặt trước để lỗi vẽ không làm dừng vòng lặp
    const [w, h] = CN.fit();
    ctx.fillStyle = COLOR.bg; ctx.fillRect(0, 0, w, h);
    const { snap, offline, mock } = CN.state;
    CN.bench.frame(!!snap);   // ?bench=1: đo thời gian khung (core/bench.js), không làm gì khi tắt
    if (!snap) {
      const msg = offline ? (mock ? "Không đọc được file mock…" : "Không kết nối được máy chủ…") : "Đang tải…";
      text(msg, w / 2, h / 2, { align: "center", size: 20 });
      return;
    }
    const fresh = CN.events.ingest(snap);
    if (CN.events.restarted) CN.camera.reset();
    CN.screens.update(snap, fresh);
    if (CN.screens.mode !== "play") { CN.screens.drawFull(w, h); return; }

    CN.fx.ingest(fresh);
    const phase = CN.scenes[snap.phase] ? snap.phase : CN.scenes[snap.mode] ? snap.mode : "gather";
    const [dx, dy] = CN.fx.shake();
    ctx.save(); ctx.translate(dx, dy);
    CN.scenes[phase].draw(w, h, snap);
    ctx.restore();
    (CN.hud[phase] || (() => {}))(w, h, snap);
    CN.fx.draw();
    CN.overlay.draw(w, h, snap);
    CN.screens.drawOverlay(w, h, snap);
    CN.bench.draw(w);
  }
  requestAnimationFrame(frame);
})(window.CN);
