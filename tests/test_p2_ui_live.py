"""Lát 4b (nganhduong123): bản chơi live cho menu/intro/pause/HUD/Shop theo TICKET-02 §2.

- Chạy riêng gather/quan: nút pause của bản chơi giữ tick và timer đứng yên (intro, menu Tạm dừng).
- Mode day: chơi được nhiều Ngày (--days), snapshot có shift_earned / days_completed cho HUD và Tổng kết.
- Không đổi headless: các trường thêm chỉ nằm trong GET /state.
"""

import copy
import json
import time
import unittest
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer, main as live_main


def _get(base):
    with urllib.request.urlopen(base + "/state", timeout=5) as r:
        return json.loads(r.read())


def _post(base, obj):
    req = urllib.request.Request(base + "/input", data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status


def _tap(base, button):
    _post(base, {button: True})
    _post(base, {button: False})


def _wait(base, cond, timeout=10.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        st = _get(base)
        if cond(st):
            return st
        time.sleep(0.03)
    raise AssertionError("hết giờ chờ điều kiện")


def _short_tuning():
    t = copy.deepcopy(load_contract()["tuning"])
    t["gather"]["duration_s"] = 1
    t["quan"]["duration_s"] = 1
    t["shop"]["max_ticks"] = 60
    return t


class _Server:
    def __init__(self, *args, **kw):
        self.server = LiveServer(LiveGame(*args, **kw), port=0)

    def __enter__(self):
        self.server.start()
        return f"http://127.0.0.1:{self.server.port}"

    def __exit__(self, *exc):
        self.server.stop()


class StandalonePauseTest(unittest.TestCase):
    def _check_pause(self, mode, inventory=None):
        with _Server(mode, load_contract()["tuning"], {}, 1, inventory) as base:
            _wait(base, lambda s: s["tick"] > 2)
            _tap(base, "pause")
            a = _wait(base, lambda s: s["state"] == "paused")
            time.sleep(0.3)
            b = _get(base)
            self.assertEqual(b["state"], "paused")
            self.assertEqual(a["tick"], b["tick"])
            self.assertEqual(a["time_left_ticks"], b["time_left_ticks"])
            self.assertIn("paused", [e["name"] for e in b["events"]])
            _tap(base, "pause")
            c = _wait(base, lambda s: s["tick"] > b["tick"])
            self.assertEqual(c["state"], "playing")
            self.assertLess(c["time_left_ticks"], b["time_left_ticks"])

    def test_gather_pause_freezes_tick_and_timer(self):
        self._check_pause("gather")

    def test_quan_pause_freezes_tick_and_timer(self):
        self._check_pause("quan", {})

    def test_actions_ignored_while_paused(self):
        with _Server("gather", load_contract()["tuning"], {}, 1) as base:
            _tap(base, "pause")
            a = _wait(base, lambda s: s["state"] == "paused")
            _post(base, {"move": [0, 1]})
            time.sleep(0.3)
            b = _get(base)
            self.assertEqual(a["player"]["pos"], b["player"]["pos"])
            _post(base, {"move": [0, 0]})

    def test_restart_clears_pause(self):
        with _Server("gather", load_contract()["tuning"], {}, 1) as base:
            _tap(base, "pause")
            _wait(base, lambda s: s["state"] == "paused")
            urllib.request.urlopen(urllib.request.Request(base + "/restart", data=b"", method="POST"), timeout=5).read()
            _wait(base, lambda s: s["state"] == "playing" and s["tick"] > 0)


class DayLiveTest(unittest.TestCase):
    def test_two_days_then_summary_fields(self):
        with _Server("day", _short_tuning(), {}, 1, {}, days=2) as base:
            st = _wait(base, lambda s: s["tick"] > 0)
            self.assertEqual(st["max_days"], 2)
            self.assertEqual(st["days_completed"], 0)
            names = [e["name"] for e in st["events"]]
            self.assertEqual(names[:3], ["day_start", "day_plan", "phase_start"])
            q = _wait(base, lambda s: s["phase"] == "quan")
            self.assertIn("shift_earned", q)
            self.assertEqual(q["shift_earned"], 0)
            _wait(base, lambda s: s["phase"] == "shop")
            _tap(base, "shop_done")
            d2 = _wait(base, lambda s: s.get("day") == 2)
            self.assertEqual(d2["days_completed"], 1)
            _wait(base, lambda s: s["phase"] == "shop" and s["day"] == 2)
            _tap(base, "shop_done")
            end = _wait(base, lambda s: s["finished"])
            self.assertEqual(end["reason"], "days_complete")
            self.assertEqual(end["days_completed"], 2)

    def test_day_pause_handled_by_sim_not_live(self):
        with _Server("day", load_contract()["tuning"], {}, 1, {}) as base:
            _wait(base, lambda s: s["tick"] > 2)
            _tap(base, "pause")
            a = _wait(base, lambda s: s["state"] == "paused")
            time.sleep(0.2)
            b = _get(base)
            self.assertEqual(a["time_left_ticks"], b["time_left_ticks"])
            self.assertEqual([e["name"] for e in b["events"]].count("paused"), 1)

    def test_shop_meta_has_upgrades(self):
        with _Server("day", _short_tuning(), {}, 1, {}) as base:
            st = _wait(base, lambda s: s["phase"] == "shop")
            self.assertIn("oxygen", st["meta"]["upgrades"])
            self.assertIn("hp", st["meta"]["upgrades"])


class LiveCliTest(unittest.TestCase):
    def test_days_flag_validation(self):
        self.assertEqual(live_main(["--mode", "gather", "--days", "2", "--port", "0"]), 2)
        self.assertEqual(live_main(["--mode", "day", "--days", "6", "--port", "0"]), 2)
        self.assertEqual(live_main(["--mode", "day", "--days", "0", "--port", "0"]), 2)


if __name__ == "__main__":
    unittest.main()
