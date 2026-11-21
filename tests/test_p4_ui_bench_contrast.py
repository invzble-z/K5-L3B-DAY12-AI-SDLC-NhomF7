"""Phase 4, phía client (nganhduong123): bench có render `?bench=1` và 3 cảnh báo + chế độ tương phản cao.

- POST /bench nhận thời gian khung (body lớn hơn /input), kiểm kiểu, GET /bench trả lại; bench_event báo cho bench.py.
- index.html nạp core/bench.js; client có đủ 3 cảnh báo có chữ, phím H bật/tắt và lưu lựa chọn an toàn.
"""

import json
import os
import re
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import WEB_DIR, LiveGame, LiveServer


def _req(url, obj=None, raw=None):
    data = raw if raw is not None else (json.dumps(obj).encode() if obj is not None else None)
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read()
        e.close()
        return e.code, json.loads(body or b"{}")
    except (ConnectionResetError, ConnectionAbortedError):
        return 400, {"error": "body sai"}


def _read(rel):
    with open(os.path.join(WEB_DIR, rel), encoding="utf-8") as f:
        return f.read()


class BenchEndpointTest(unittest.TestCase):
    def setUp(self):
        self.game = LiveGame("gather", load_contract()["tuning"], {}, 42)
        self.server = LiveServer(self.game, port=0)
        self.server.start()
        self.base = f"http://127.0.0.1:{self.server.port}"

    def tearDown(self):
        self.server.stop()

    def test_not_ready_before_post(self):
        code, body = _req(self.base + "/bench")
        self.assertEqual(code, 200)
        self.assertEqual(body, {"ready": False, "result": None})
        self.assertFalse(self.game.bench_event.is_set())

    def test_full_30s_payload_accepted(self):
        frames = [16.667] * 1800 + [33.4] * 18            # 30 s @ 60 FPS, vài khung chậm
        payload = {"frame_ms": frames, "frames": len(frames), "measured_s": 30.01, "warmup_s": 3,
                   "first_frame_epoch_ms": 1.79e12, "width": 1280, "height": 720, "dpr": 1}
        self.assertGreater(len(json.dumps(payload)), 4096)  # lớn hơn giới hạn của /input
        code, _ = _req(self.base + "/bench", payload)
        self.assertEqual(code, 200)
        self.assertTrue(self.game.bench_event.wait(1))
        code, body = _req(self.base + "/bench")
        self.assertTrue(body["ready"])
        self.assertEqual(body["result"]["frames"], len(frames))
        self.assertEqual(body["result"]["width"], 1280)
        self.assertAlmostEqual(body["result"]["measured_s"], 30.01)

    def test_invalid_payloads_rejected(self):
        for bad in ({"frame_ms": [], "measured_s": 1}, {"frame_ms": [16, -1], "measured_s": 1},
                    {"frame_ms": [16, True], "measured_s": 1}, {"frame_ms": [16]},
                    {"frame_ms": [16], "measured_s": 1, "width": "1280"}, {"frame_ms": "16", "measured_s": 1}):
            code, _ = _req(self.base + "/bench", bad)
            self.assertEqual(code, 400, bad)
        code, _ = _req(self.base + "/bench", raw=b"[1,2]")
        self.assertEqual(code, 400)
        self.assertFalse(self.game.bench_event.is_set())

    def test_input_body_limit_unchanged(self):
        code, _ = _req(self.base + "/input", raw=b'{"move":[0,0]' + b" " * 5000 + b"}")
        self.assertEqual(code, 400)


class ClientStaticTest(unittest.TestCase):
    def test_index_loads_bench_before_main(self):
        srcs = re.findall(r'<script src="([^"]+)"', _read("../web/index.html"))
        self.assertIn("js/core/bench.js", srcs)
        self.assertLess(srcs.index("js/core/net.js"), srcs.index("js/core/bench.js"))
        self.assertLess(srcs.index("js/core/bench.js"), srcs.index("js/main.js"))
        bench = _read("js/core/bench.js")
        for word in ("frame_ms", "measured_s", "first_frame_epoch_ms", '"/bench"', "warmup", "duration"):
            self.assertIn(word, bench)

    def test_three_alerts_have_text(self):
        gather, quan_hud, quan_scene = _read("js/gather/hud.js"), _read("js/quan/hud.js"), _read("js/quan/scene.js")
        self.assertIn("Thủy quái!", gather)
        self.assertIn("Hết hơi!", gather)
        self.assertIn("Sắp hết hơi!", gather)
        self.assertIn("Khách sắp giận", quan_hud)
        self.assertIn("Sắp giận!", quan_scene)
        for src in (gather, quan_hud, quan_scene):
            self.assertIn("ui.alert(", src)

    def test_contrast_toggle_and_safe_storage(self):
        draw, inp = _read("js/core/draw.js"), _read("js/core/input.js")
        self.assertIn("CN.contrast", draw)
        self.assertRegex(draw, r"try \{ localStorage\.setItem")
        self.assertRegex(draw, r"try \{ saved = localStorage\.getItem")
        self.assertIn('k === "h"', inp)
        self.assertIn("Tương phản cao", _read("js/shared/screens.js"))


if __name__ == "__main__":
    unittest.main()
