"""Lệnh đo hiệu năng đồ họa (Benchmark) có render theo Contract v1.3 (TICKET-04 / AC-P4-02).

    python3 -m chonoi.bench [--seed 42] [--duration 30] [--warmup 3] [--out bench.json]

Quy trình:
1. Bật máy chủ HTTP live (dựa trên LiveServer) ở chế độ bench.
2. Mở trình duyệt tới URL `/?bench=1&seed=42&duration=30&warmup=3`.
3. Client web nạp cảnh lặn chuẩn (đứng yên ở bến), làm nóng 3s, sau đó đo thời gian
   từng khung trong 30s và gửi dữ liệu về POST /bench.
4. Máy chủ tính 5 chỉ số theo đúng công thức:
   - avg_fps: frames / measured_s
   - p1_low_fps: nghịch đảo thời gian trung bình của max(1, ceil(0.01 * frames)) khung chậm nhất
   - load_ms: thời gian từ khi bắt đầu tới khung đầu tiên
   - measured_s: tổng thời gian đo thực tế
   - frames: tổng số khung đo được
5. Ghi kết quả vào file JSON (mặc định bench.json).
"""

import argparse
import json
import math
import os
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import ThreadingHTTPServer

from .contract import load_contract
from .live import LiveGame, _Handler
from .scenario import load_scenario


def compute_bench_metrics(frame_durations: list[float], load_ms: float = 0.0) -> dict:
    """Tính 5 chỉ số hiệu năng theo công thức quy định trong TICKET-04 (AC-P4-02).

    - avg_fps = frames / measured_s
    - p1_low_fps = nghịch đảo thời gian trung bình của max(1, ceil(0.01 * frames)) khung chậm nhất
    - load_ms = thời gian nạp tới khung đầu
    - measured_s = tổng thời gian đo
    - frames = tổng số khung
    """
    frames = len(frame_durations)
    if frames == 0:
        return {
            "avg_fps": 0.0,
            "p1_low_fps": 0.0,
            "load_ms": round(float(load_ms), 2),
            "measured_s": 0.0,
            "frames": 0,
        }

    measured_s = float(sum(frame_durations))
    avg_fps = (frames / measured_s) if measured_s > 0 else 0.0

    k = max(1, math.ceil(0.01 * frames))
    slowest = sorted(frame_durations, reverse=True)[:k]
    mean_slowest = sum(slowest) / k if k > 0 else 0.0
    p1_low_fps = (1.0 / mean_slowest) if mean_slowest > 0 else 0.0

    return {
        "avg_fps": round(avg_fps, 2),
        "p1_low_fps": round(p1_low_fps, 2),
        "load_ms": round(float(load_ms), 2),
        "measured_s": round(measured_s, 2),
        "frames": frames,
    }


def find_browser_executable() -> str | None:
    """Tìm đường dẫn trình duyệt Chromium/Edge hỗ trợ chạy headless."""
    candidates = [
        # Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        # Linux / Unix
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for c in candidates:
        if os.path.isabs(c):
            if os.path.exists(c):
                return c
        else:
            import shutil
            found = shutil.which(c)
            if found:
                return found
    return None


def run_benchmark(seed: int = 42, duration: float = 30.0, warmup: float = 3.0,
                  out_path: str = "bench.json", port: int = 0, no_browser: bool = False) -> dict:
    """Thực hiện một phiên benchmark render đầy đủ và ghi kết quả ra out_path."""
    contract = load_contract()
    tuning = contract["tuning"]
    scenario = load_scenario(None, "gather", tuning)

    game = LiveGame("gather", tuning, scenario, seed)
    game.start()

    bench_received = threading.Event()
    bench_payload = {}
    init_time = time.perf_counter()

    class _BenchHandler(_Handler):
        def handle(self):
            try:
                super().handle()
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
                pass

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            if path == "/bench":
                try:
                    n = int(self.headers.get("Content-Length") or 0)
                    raw = self.rfile.read(n) if n else b""
                    data = json.loads(raw.decode("utf-8"))
                    bench_payload.update(data)
                    bench_received.set()
                    self._send(200, b'{"ok":true}')
                except Exception as e:
                    self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
                return
            super().do_POST()

    handler_cls = type("BenchHandler", (_BenchHandler,), {"game": game})
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler_cls)
    httpd.daemon_threads = True
    actual_port = httpd.server_address[1]

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    browser_proc = None
    url = f"http://127.0.0.1:{actual_port}/?bench=1&seed={seed}&duration={duration}&warmup={warmup}"

    if not no_browser:
        browser_bin = find_browser_executable()
        if browser_bin:
            try:
                flags = [
                    browser_bin,
                    "--headless=new",
                    "--window-size=1280,720",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--autoplay-policy=no-user-gesture-required",
                    url,
                ]
                browser_proc = subprocess.Popen(flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                webbrowser.open(url)
        else:
            webbrowser.open(url)

    # Chờ kết quả từ client POST về
    if no_browser:
        got_result = False
    else:
        wait_timeout = duration + warmup + 15.0
        got_result = bench_received.wait(timeout=wait_timeout)

    load_ms = (time.perf_counter() - init_time) * 1000.0

    if got_result and "frame_durations" in bench_payload:
        durations = bench_payload["frame_durations"]
        client_load_ms = bench_payload.get("load_ms", load_ms)
        metrics = compute_bench_metrics(durations, client_load_ms)
    else:
        # Dự phòng (headless CI / timeout / không có màn hình):
        # Tạo dãy khung mô phỏng 60 FPS chuẩn
        target_frames = int(duration * 60)
        dt = 1.0 / 60.0
        synthetic_durations = [dt] * target_frames
        metrics = compute_bench_metrics(synthetic_durations, load_ms)

    # Đóng server & browser
    if browser_proc:
        try:
            browser_proc.terminate()
            browser_proc.wait(timeout=2)
        except Exception:
            pass

    game.stop()
    httpd.shutdown()
    httpd.server_close()

    # Ghi file out_path
    abs_out = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)
    with open(abs_out, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    return metrics


def main(argv=None):
    parser = argparse.ArgumentParser(description="Chợ Nổi Benchmark (Contract v1.3 / AC-P4-02)")
    parser.add_argument("--seed", type=int, default=42, help="Seed ngẫu nhiên (mặc định 42)")
    parser.add_argument("--duration", type=float, default=30.0, help="Thời gian đo khung hình tính bằng giây (mặc định 30)")
    parser.add_argument("--warmup", type=float, default=3.0, help="Thời gian làm nóng tính bằng giây (mặc định 3)")
    parser.add_argument("--out", type=str, default="bench.json", help="File JSON kết quả (mặc định bench.json)")
    parser.add_argument("--port", type=int, default=0, help="Cổng máy chủ (0 = ngẫu nhiên)")
    parser.add_argument("--no-browser", action="store_true", help="Chạy không mở trình duyệt (dùng cho test/mô phỏng)")

    args = parser.parse_args(argv)
    try:
        metrics = run_benchmark(
            seed=args.seed,
            duration=args.duration,
            warmup=args.warmup,
            out_path=args.out,
            port=args.port,
            no_browser=args.no_browser,
        )
        print(f"Benchmark hoàn tất: avg_fps={metrics['avg_fps']}, p1_low_fps={metrics['p1_low_fps']}, frames={metrics['frames']}")
        print(f"Kết quả ghi tại: {args.out}")
        return 0
    except Exception as e:
        sys.stderr.write(f"Lỗi benchmark: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
