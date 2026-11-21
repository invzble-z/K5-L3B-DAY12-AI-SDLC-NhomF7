"use strict";
/*
 * Bench có render (TICKET-04, phía client, nganhduong123). Bật bằng /?bench=1 (tùy chọn &warmup=3&duration=30).
 * - Bỏ menu/intro, không gửi phím: Út Sen đứng yên ở bến, cảnh do máy chủ dựng (bench_cmd chọn mode + seed 42).
 * - Làm nóng `warmup` giây kể từ khung đầu có snapshot, rồi ghi thời gian từng khung (ms) trong `duration` giây.
 * - Xong thì POST /bench: {frame_ms[], frames, measured_s, warmup_s, first_frame_epoch_ms, width, height, dpr}.
 *   Python (chonoi/bench.py) tính 5 trường chính thức; client chỉ hiện avg_fps để xem nhanh.
 */
(function (CN) {
  const q = new URLSearchParams(location.search);
  const on = q.get("bench") === "1" && !CN.state.mock;
  const num = (k, d) => { const v = parseFloat(q.get(k)); return Number.isFinite(v) && v >= 0 ? v : d; };
  const warm = num("warmup", 3), dur = Math.max(0.5, num("duration", 30));

  const B = (CN.bench = { on, warm, dur, phase: on ? "wait" : "off", frames: [], avgFps: null, sent: null });
  let t0 = 0, m0 = 0, last = 0, firstEpoch = null;

  B.frame = function (hasSnap) {
    if (B.phase === "off" || B.phase === "done") return;
    const now = performance.now();
    if (B.phase === "wait") {
      if (!hasSnap) return;
      B.phase = "warm"; t0 = last = now; firstEpoch = performance.timeOrigin + now;
      return;
    }
    const dt = now - last;
    last = now;
    if (B.phase === "warm") {
      if (now - t0 >= warm * 1000) { B.phase = "measure"; m0 = now; }
      return;
    }
    B.frames.push(Math.round(dt * 1000) / 1000);
    if (now - m0 >= dur * 1000) { B.phase = "done"; send((now - m0) / 1000); }
  };

  async function send(measured_s) {
    B.avgFps = B.frames.length / measured_s;
    const body = {
      frame_ms: B.frames, frames: B.frames.length, measured_s, warmup_s: warm,
      first_frame_epoch_ms: firstEpoch, width: innerWidth, height: innerHeight, dpr: window.devicePixelRatio || 1,
    };
    try {
      const r = await fetch("/bench", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      B.sent = r.ok;
    } catch (e) { B.sent = false; }
  }

  B.draw = function (w) {
    if (!on) return;
    const label = B.phase === "warm" ? "BENCH: làm nóng…" : B.phase === "measure" ? "BENCH: đang đo " + Math.min(dur, (performance.now() - m0) / 1000).toFixed(0) + "/" + dur + " s"
      : B.phase === "done" ? "BENCH xong: " + (B.avgFps || 0).toFixed(1) + " FPS · " + (B.sent ? "đã gửi" : B.sent === false ? "gửi lỗi" : "đang gửi") : "BENCH: chờ máy chủ…";
    CN.text(label, w - 14, 96, { size: 18, align: "right", weight: "700", color: "#ffd166" });
  };
})(window.CN);
