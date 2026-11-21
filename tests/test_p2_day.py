"""Test Lát 4a — Phase 2: Vòng ngày (--mode day, D1..D5, đổi pha, Shop, nâng cấp, pause).

Chạy: python -m unittest tests.test_p2_day -v
"""

import json
import os
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer, InputState, load_frames
from chonoi.runner import Session
try:
    from tests.helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json
except ImportError:
    from helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json


class DaySimTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()
        self.tuning = self.contract["tuning"]

    def test_day_start_and_phase_transitions(self):
        """Kiểm tra chuỗi đổi pha: gather -> quan -> shop -> ngày kế tiếp."""
        scenario = {
            "day": {"days": 2},
            "gather": {
                "player": {"pos": [12, 0]},
                "hold": ["ca_loc"],
                "nodes": [],
                "fish": [],
                "random_fish": False,
                "time_left_ticks": 2,
            },
            "quan": {
                "customers": [],
                "random_customers": False,
                "time_left_ticks": 2,
            },
        }
        sess = Session("day", self.tuning, scenario, seed=1, days=2)
        snap0 = sess.snapshot()
        self.assertEqual(snap0["day"], 1)
        self.assertEqual(snap0["phase"], "gather")
        self.assertEqual(snap0["state"], "running")
        self.assertIn("dishes", snap0["day_plan"])

        # Tick 1: Gather chạy (còn 1 tick)
        ev1 = sess.step(InputState((0, 0), {}, set()))
        names1 = [r["name"] for r in ev1]
        self.assertIn("day_start", names1)
        self.assertIn("day_plan", names1)
        self.assertIn("phase_start", names1)

        # Tick 2: Gather hết giờ -> chuyển sang quan
        ev2 = sess.step(InputState((0, 0), {}, set()))
        names2 = [r["name"] for r in ev2]
        self.assertIn("gather_end", names2)
        self.assertIn("phase_start", names2)
        self.assertEqual(sess.sim.phase, "quan")
        self.assertEqual([item.kind for item in sess.sim.inventory], ["ca_loc"])

        # Tick 3: Quán chạy (còn 1 tick)
        sess.step(InputState((0, 0), {}, set()))

        # Tick 4: Quán hết giờ -> chuyển sang shop
        ev4 = sess.step(InputState((0, 0), {}, set()))
        names4 = [r["name"] for r in ev4]
        self.assertIn("quan_end", names4)
        self.assertIn("phase_start", names4)
        self.assertEqual(sess.sim.phase, "shop")

        # Tick 5: Trong shop, bấm shop_done -> hết ngày 1, sang ngày 2
        ev5 = sess.step(InputState((0, 0), {"shop_done": True}, {"shop_done"}))
        names5 = [r["name"] for r in ev5]
        self.assertIn("shop_end", names5)
        self.assertIn("day_start", names5)
        self.assertIn("day_plan", names5)
        self.assertIn("phase_start", names5)
        self.assertEqual(sess.sim.day, 2)
        self.assertEqual(sess.sim.days_completed, 1)
        self.assertEqual(sess.sim.phase, "gather")

    def test_shop_purchases_and_next_day_active_upgrades(self):
        """Mua nâng cấp ở Shop: trừ tiền, tăng cấp, và chỉ có hiệu lực ở Ngày tiếp theo."""
        scenario = {
            "day": {
                "days": 2,
                "money": 300,  # Có 300 xu (đủ mua oxy cấp 1 giá 200)
                "upgrades": {},
                "active_upgrades": {},
            },
            "gather": {"time_left_ticks": 1, "random_fish": False, "nodes": []},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        sess = Session("day", self.tuning, scenario, seed=1)

        # Qua gather và quan đến shop
        sess.step(InputState((0, 0), {}, set()))  # gather ends -> quan
        sess.step(InputState((0, 0), {}, set()))  # quan ends -> shop
        self.assertEqual(sess.sim.phase, "shop")
        self.assertEqual(sess.sim.money, 300)

        # Mua oxygen cấp 1 (giá 200)
        ev_buy = sess.step(InputState((0, 0), {}, set(), buy="oxygen"))
        bought_events = [r for r in ev_buy if r["name"] == "bought"]
        self.assertEqual(len(bought_events), 1)
        self.assertEqual(bought_events[0]["data"]["upgrade"], "oxygen")
        self.assertEqual(bought_events[0]["data"]["level"], 1)
        self.assertEqual(bought_events[0]["data"]["price"], 200)
        self.assertEqual(sess.sim.money, 100)
        self.assertEqual(sess.sim.upgrades["oxygen"], 1)
        # Tại ngày 1, active_upgrades vẫn chưa có
        self.assertNotIn("oxygen", sess.sim.active_upgrades)

        # Mua tiếp oxy cấp 2 (giá 400) nhưng chỉ còn 100 xu -> buy_failed (funds)
        ev_funds = sess.step(InputState((0, 0), {}, set(), buy="oxygen"))
        failed_funds = [r for r in ev_funds if r["name"] == "buy_failed"]
        self.assertEqual(len(failed_funds), 1)
        self.assertEqual(failed_funds[0]["data"]["reason"], "funds")

        # Mua nâng cấp lạ -> buy_failed (unknown)
        ev_bad = sess.step(InputState((0, 0), {}, set(), buy="jetpack"))
        failed_events = [r for r in ev_bad if r["name"] == "buy_failed"]
        self.assertEqual(failed_events[0]["data"]["reason"], "unknown")

        # Đóng shop -> sang Ngày 2
        ev_done = sess.step(InputState((0, 0), {"shop_done": True}, {"shop_done"}))
        self.assertEqual(sess.sim.day, 2)
        # Nâng cấp đã trở thành active_upgrades tại Ngày 2
        self.assertEqual(sess.sim.active_upgrades.get("oxygen"), 1)
        # GatherSim ngày 2 có oxygen_max_s được nâng cấp
        oxy_up_info = next(u for u in self.tuning["shop"]["upgrades"]["oxygen"] if u["level"] == 1)
        expected_oxy_ticks = int(round(oxy_up_info["oxygen_max_s"] * self.tuning["tick_hz"]))
        self.assertEqual(sess.sim.sub_sim.oxygen_max, expected_oxy_ticks)

    def test_pause_and_resume_freezes_simulation(self):
        """Bấm pause tạm dừng vòng chơi; bấm pause lần nữa thì tiếp tục."""
        scenario = {
            "gather": {"time_left_ticks": 100, "random_fish": False, "nodes": []},
        }
        sess = Session("day", self.tuning, scenario, seed=1)
        self.assertEqual(sess.snapshot()["state"], "running")

        # Bấm pause
        ev_pause = sess.step(InputState((0, 0), {"pause": True}, {"pause"}))
        self.assertIn("paused", [r["name"] for r in ev_pause])
        self.assertEqual(sess.sim.state, "paused")
        self.assertEqual(sess.snapshot()["state"], "paused")

        time_before = sess.sim.time_left_ticks
        # Tick khi đang pause -> thời gian không giảm
        sess.step(InputState((0, 0), {}, set()))
        self.assertEqual(sess.sim.time_left_ticks, time_before)

        # Bấm pause lần nữa -> resume
        ev_resume = sess.step(InputState((0, 0), {"pause": True}, {"pause"}))
        self.assertIn("resumed", [r["name"] for r in ev_resume])
        self.assertEqual(sess.sim.state, "running")
        self.assertEqual(sess.snapshot()["state"], "running")

    def test_day_completion_stops_at_max_days(self):
        """Chạy đủ số ngày đặt ra sẽ kết thúc với reason 'days_complete'."""
        scenario = {
            "day": {"days": 1},
            "gather": {"time_left_ticks": 1, "random_fish": False, "nodes": []},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        sess = Session("day", self.tuning, scenario, seed=1, days=1)
        sess.step(InputState((0, 0), {}, set()))  # gather -> quan
        sess.step(InputState((0, 0), {}, set()))  # quan -> shop
        # Bấm shop_done kết thúc ngày 1
        sess.step(InputState((0, 0), {"shop_done": True}, {"shop_done"}))
        self.assertTrue(sess.done)
        self.assertEqual(sess.sim.reason, "days_complete")
        self.assertEqual(sess.sim.days_completed, 1)
        end = sess.end_row()
        self.assertEqual(end["state"], "finished")
        self.assertEqual(end["reason"], "days_complete")
        self.assertEqual(end["days_completed"], 1)


class DayHeadlessCLITests(unittest.TestCase):
    def test_headless_day_run_produces_valid_jsonl(self):
        with Workdir() as w:
            out = w.path("day_run.jsonl")
            sc = write_json(w.path("sc.json"), {
                "day": {"days": 1},
                "gather": {"time_left_ticks": 2, "random_fish": False, "nodes": []},
                "quan": {"time_left_ticks": 2, "random_customers": False},
            })
            inp = write_json(w.path("in.json"), frames({"tick": 4, "shop_done": True}))
            code, err = run_headless("--mode", "day", "--days", "1", "--seed", "1",
                                     "--ticks", "10", "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(rows[0]["type"], "snapshot")
            self.assertEqual(rows[0]["mode"], "day")
            self.assertIn("day_plan", rows[0])
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["days_completed"], 1)

    def test_headless_day_validation_exit_2(self):
        with Workdir() as w:
            out = w.path("out.jsonl")
            # --days 0 phải báo mã 2
            code, _ = run_headless("--mode", "day", "--days", "0", "--seed", "1", "--ticks", "5", "--out", out)
            self.assertEqual(code, 2)
            # --days dùng với mode gather phải báo mã 2
            code, _ = run_headless("--mode", "gather", "--days", "1", "--seed", "1", "--ticks", "5", "--out", out)
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
