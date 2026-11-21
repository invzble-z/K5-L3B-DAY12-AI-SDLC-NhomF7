"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live --mode gather|quan|day [--seed N] [--port 8000] [--days 1-5]

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/index.html` và hai API:
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool}   (trạng thái phím đang giữ)
                    v1.1 (nhóm F7): thêm "pause", "shop_done", "attack", "photo" (bool) và "buy" (chuỗi, một tick)
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)
    GET  /<file>  -> file tĩnh trong chonoi/web/ (js/, mock/, assets/; thêm bởi nhóm F7, xem docs/adr/0001)

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import json
import math
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

from .contract import load_contract
from .errors import BadInput
from .inputs import LiveInputs
from .inventory import merge_items, read_inventory_for_mode, read_inventory_or_empty, write_inventory
from .runner import Session
from .scenario import load_scenario

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
MAX_BENCH_BODY = 1 << 20   # POST /bench: ~1800 thời gian khung cho 30 s, vượt xa 4 KB của /input
MAX_BENCH_FRAMES = 100000
RECENT_EVENTS = 40
# Nhóm F7: client tách thành nhiều file (js/, mock/, assets/) nên máy chủ phục vụ file tĩnh theo đuôi này.
STATIC_TYPES = {
    ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
    ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".webp": "image/webp",
    ".wav": "audio/wav", ".mp3": "audio/mpeg", ".ogg": "audio/ogg",
}
# Nhóm F7 (Test Contract v1.1): nút boolean mới + lệnh `buy` (chuỗi, chỉ có tác dụng ở một tick).
LIVE_BUTTONS = ("interact", "catch", "pause", "shop_done", "attack", "photo")
MAX_BUY_LEN = 64


class _LiveInputsV11(LiveInputs):
    """LiveInputs + nút v1.1 + `buy`. Sim chưa dùng nút nào thì bỏ qua (chỉ đọc `pressed(...)`)."""

    def __init__(self):
        super().__init__(LIVE_BUTTONS)
        self._buy = None

    def set(self, move=None, buy=None, **buttons):
        super().set(move, **buttons)
        if buy is not None:
            self._buy = buy

    def advance(self):
        state = super().advance()
        state.buy, self._buy = self._buy, None
        return state


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, days=None):
        self._args = (mode, tuning, scenario, seed, inventory, days)
        self.mode = mode
        self.tuning = tuning
        self.inventory_out = inventory_out
        self._lock = threading.Lock()
        self._stop = threading.Event()
        # Bench có render (TICKET-04): client ?bench=1 gửi thời gian khung về đây; chonoi/bench.py đọc qua
        # `bench_event`/`bench_result` (cùng tiến trình) hoặc GET /bench. Không ảnh hưởng mô phỏng.
        self.bench_event = threading.Event()
        self.bench_result = None
        self._thread = None
        self._reset()

    def _reset(self):
        self.inventory_base = (read_inventory_or_empty(
            self.inventory_out, version=self.tuning.get("contract_version"))
                               if self.mode in ("gather", "day") and self.inventory_out else {})
        self.session = Session(*self._args)
        self.inputs = _LiveInputsV11()
        self.events = []
        self._saved = False
        self.error = None
        # Nhóm F7: chạy riêng gather/quan thì sim không có pause (headless v1.0), nên bản chơi tự giữ cờ
        # tạm dừng: không bước sim, tick/timer đứng yên, bỏ qua cạnh hành động (docs/contracts §4, clarify #3).
        self.live_paused = False

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    self.session.sim.done = True
                    self.session.sim.reason = "error"
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if s.done:
            return
        inp = self.inputs.advance()
        if self.mode != "day" and inp.pressed("pause"):   # mode day: DaySim tự xử lý pause
            self.live_paused = not self.live_paused
            self.events.append({"type": "event", "tick": s.tick, "phase": s.sim.phase,
                                "name": "paused" if self.live_paused else "resumed", "data": {}})
        if self.live_paused:
            return
        for row in s.step(inp):
            self.events.append(row)
        del self.events[:-RECENT_EVENTS]
        if self.mode in ("gather", "day") and self.inventory_out:
            inventory_events = {"gather", "fish_caught", "faint", "gather_end"}
            if any(row["name"] in inventory_events for row in self.events[-RECENT_EVENTS:]
                   if row["tick"] == s.tick):
                items = (s.sim.inventory_items() if self.mode == "day"
                         else merge_items(self.inventory_base, s.sim.inventory_items()))
                write_inventory(self.inventory_out, items)
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out:
                try:
                    s.write_inventory_if_done(self.inventory_out, self.inventory_base)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            # meta theo pha hiện tại (day đổi gather -> quan -> shop); menu để client hiện tên món / tiến độ nấu
            snap["meta"] = self.tuning.get(snap.get("phase") or self.mode, self.tuning.get(self.mode, {}))
            snap["menu"] = self.tuning.get("menu", {})
            if "freshness" in self.tuning:   # v1.2: ngưỡng "ươn" cho HUD độ tươi
                snap["freshness"] = self.tuning["freshness"]
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            if self.live_paused:
                snap["state"] = "paused"
            # Chỉ để hiển thị (không vào JSONL): tiền của ca đang chạy và số Ngày đã xong cho HUD/Tổng kết.
            sim = self.session.sim
            quan = sim if self.mode == "quan" else getattr(sim, "quan", None)
            if quan is not None and "shift_earned" not in snap:
                snap["shift_earned"] = getattr(quan, "shift_earned", None)
            if self.mode == "day" and "days_completed" not in snap:
                snap["days_completed"] = getattr(sim, "days_completed", 0)
                snap["max_days"] = getattr(sim, "max_days", None)
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in LIVE_BUTTONS:
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        buy = body.get("buy")
        if buy is not None and (not isinstance(buy, str) or not buy or len(buy) > MAX_BUY_LEN):
            raise ValueError("buy phải là chuỗi khác rỗng")
        with self._lock:
            self.inputs.set(move, buy=buy, **buttons)

    def set_bench(self, body: dict):
        frames = body.get("frame_ms")
        if (not isinstance(frames, list) or not 0 < len(frames) <= MAX_BENCH_FRAMES or
                not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x > 0 for x in frames)):
            raise ValueError("frame_ms phải là mảng số dương, khác rỗng")
        out = {"frame_ms": [float(x) for x in frames]}
        for k in ("measured_s", "warmup_s", "first_frame_epoch_ms", "width", "height", "dpr"):
            v = body.get(k)
            if v is not None and (not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0):
                raise ValueError(f"{k} phải là số ≥ 0")
            out[k] = v
        if not out.get("measured_s"):
            raise ValueError("measured_s phải > 0")
        out["frames"] = len(out["frame_ms"])
        with self._lock:
            self.bench_result = out
        self.bench_event.set()

    def bench_json(self) -> bytes:
        with self._lock:
            r = self.bench_result
        return json.dumps({"ready": r is not None, "result": r}, separators=(",", ":")).encode("utf-8")

    def restart(self):
        with self._lock:
            self._reset()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            self._send(200, self.game.state_json())
        elif path == "/bench":
            self._send(200, self.game.bench_json())
        elif path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu index.html"}')
        else:
            self._send_static(path)

    def _send_static(self, path):
        """File tĩnh của client (js/, mock/, assets/...) trong WEB_DIR; chặn thoát ra ngoài thư mục."""
        root = os.path.realpath(WEB_DIR)
        full = os.path.realpath(os.path.join(root, unquote(path).lstrip("/")))
        ctype = STATIC_TYPES.get(os.path.splitext(full)[1].lower())
        if ctype is None or os.path.commonpath([root, full]) != root or not os.path.isfile(full):
            self._send(404, b'{"error":"khong co"}')
            return
        try:
            with open(full, "rb") as f:
                self._send(200, f.read(), ctype)
        except OSError:
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > (MAX_BENCH_BODY if path == "/bench" else MAX_BODY):
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path == "/input":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_input(body)
            elif path == "/restart":
                self.game.restart()
            elif path == "/bench":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_bench(body)
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (starter).")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--inventory", help="nạp kho cho quan hoặc day")
    p.add_argument("--inventory-out", dest="inventory_out",
                   help="chỉ với gather: ghi kho ngay khi khởi động, hái/bắt và kết thúc buổi")
    p.add_argument("--days", type=int, default=None,
                   help="chỉ với day: số Ngày 1–5 (mặc định 5 ở bản chơi để đi hết D1–D5 rồi Tổng kết)")
    a = p.parse_args(argv)
    try:
        if a.days is not None and a.mode != "day":
            raise BadInput("--days chỉ dùng với day")
        if a.days is not None and not 1 <= a.days <= 5:
            raise BadInput("--days phải là số nguyên 1–5")
        days = (a.days or 5) if a.mode == "day" else None
        if a.inventory and a.mode not in ("quan", "day"):
            raise BadInput("--inventory chỉ dùng với quan hoặc day")
        if a.inventory_out and a.mode not in ("gather", "day"):
            raise BadInput("--inventory-out chỉ dùng với gather hoặc day")
        tuning = load_contract()["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning)
        has_scenario_stock = (
            "stock" in scenario
            if a.mode == "quan"
            else a.mode == "day" and "stock" in scenario.get("quan", {})
        )
        if a.inventory is not None:
            inventory = read_inventory_for_mode(a.mode, a.inventory)
            if has_scenario_stock:
                raise BadInput("vừa có quan.stock vừa có --inventory")
        elif has_scenario_stock:
            inventory = None
        else:
            inventory = read_inventory_for_mode(a.mode, None)
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out, days=days)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
