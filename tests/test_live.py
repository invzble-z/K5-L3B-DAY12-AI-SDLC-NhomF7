"""Test cửa sổ chơi trực tiếp (chonoi.live). Chỉ dành cho starter Python: nhóm đổi ngôn ngữ thì xóa file này."""

import json
import os
import tempfile
import time
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer
from chonoi.runner import Session
from chonoi.inputs import InputState
from chonoi.inventory import read_inventory_for_mode


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read()


def _post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


class LiveServerTest(unittest.TestCase):
    def test_state_input_and_clean_stop(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("gather", tuning, {}, 1), port=0)  # cổng ngẫu nhiên
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            code, body = _get(base + "/state")
            self.assertEqual(code, 200)
            st = json.loads(body)
            self.assertIn("tick", st)
            self.assertEqual(st["mode"], "gather")
            self.assertEqual(st["player"]["pos"], [2, 0])
            self.assertEqual(_post(base + "/input", {"move": [1, 0], "interact": False, "catch": False}), 200)
            self.assertEqual(_post(base + "/input", {"move": [5, 0]}), 400)
            code, html = _get(base + "/")
            self.assertEqual(code, 200)
            self.assertIn(b"<canvas", html)
            deadline = time.time() + 3
            while time.time() < deadline:
                st2 = json.loads(_get(base + "/state")[1])
                if st2["tick"] > st["tick"] + 3 and st2["player"]["pos"][0] > st["player"]["pos"][0]:
                    break
                time.sleep(0.05)
            self.assertGreater(st2["tick"], st["tick"], "mô phỏng phải chạy nền")
            self.assertGreater(st2["player"]["pos"][0], st["player"]["pos"][0], "input phải tác động tới sim")
        finally:
            server.stop()
        self.assertFalse(server.game._thread.is_alive())
        self.assertFalse(server._thread.is_alive())


class LiveInventoryPersistenceTest(unittest.TestCase):
    def test_day_does_not_double_existing_inventory_on_handoff(self):
        tuning = dict(load_contract()["tuning"], contract_version="1.1")
        with tempfile.TemporaryDirectory() as d:
            inventory_path = os.path.join(d, "inventory.json")
            with open(inventory_path, "w", encoding="utf-8") as f:
                json.dump({"items": {"ca_linh": 12, "ca_loc": 2}}, f)
            scenario = {
                "gather": {"hold": [], "random_fish": False, "time_left_ticks": 1},
                "quan": {"random_customers": False},
            }
            game = LiveGame(
                "day",
                tuning,
                scenario,
                1,
                inventory={"ca_linh": 12, "ca_loc": 2},
                inventory_out=inventory_path,
            )
            game._tick_once()
            snapshot = json.loads(game.state_json())
            self.assertEqual(snapshot["phase"], "quan")
            self.assertEqual(snapshot["stock"], {"ca_linh": 12, "ca_loc": 2})
            with open(inventory_path, encoding="utf-8") as f:
                self.assertEqual(
                    json.load(f),
                    {"items": {"ca_linh": 12, "ca_loc": 2}},
                )

    def test_default_inventory_file_is_loaded_by_quan_and_day(self):
        with tempfile.TemporaryDirectory() as d:
            old_cwd = os.getcwd()
            try:
                os.chdir(d)
                with open("inventory.json", "w", encoding="utf-8") as f:
                    json.dump({"items": {"ca_linh": 12, "ca_loc": 2}}, f)
                self.assertEqual(
                    read_inventory_for_mode("quan", None, version="1.1"),
                    {"ca_linh": 12, "ca_loc": 2},
                )
                self.assertEqual(
                    read_inventory_for_mode("day", None, version="1.1"),
                    {"ca_linh": 12, "ca_loc": 2},
                )
            finally:
                os.chdir(old_cwd)

    def test_gather_writes_inventory_immediately(self):
        tuning = dict(load_contract()["tuning"], contract_version="1.1")
        with tempfile.TemporaryDirectory() as d:
            inventory_path = os.path.join(d, "inventory.json")
            with open(inventory_path, "w", encoding="utf-8") as f:
                json.dump({"items": {"ca_loc": 2}}, f)
            scenario = {
                "player": {"pos": [12, 0]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                "random_fish": False,
            }
            game = LiveGame("gather", tuning, scenario, 1, inventory_out=inventory_path)
            game.inputs.set(interact=True)
            game._tick_once()
            with open(inventory_path, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 1, "ca_loc": 2}})

            game.restart()
            game.inputs.set(interact=True)
            game._tick_once()
            with open(inventory_path, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 2, "ca_loc": 2}})

    def test_quan_live_snapshot_uses_inventory(self):
        tuning = dict(load_contract()["tuning"], contract_version="1.1")
        game = LiveGame(
            "quan",
            tuning,
            {},
            1,
            inventory={"ca_linh": 12, "ca_loc": 2},
        )
        snapshot = json.loads(game.state_json())
        self.assertEqual(snapshot["stock"], {"ca_linh": 12, "ca_loc": 2})


class DayFlowTest(unittest.TestCase):
    def test_gather_handoff_to_quan_preserves_caught_items(self):
        tuning = load_contract()["tuning"]
        session = Session(
            "day",
            tuning,
            {
                "gather": {
                    "player": {"pos": [12, 0]},
                    "hold": ["ca_loc"],
                    "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
                    "random_fish": False,
                    "time_left_ticks": 1,
                },
                "quan": {
                    "customers": [{
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "state": "waiting",
                        "patience_ticks_left": 3600,
                        "reserved": ["I1"],
                    }],
                },
            },
            1,
        )

        events = session.step(InputState((0, 0), {}, set()))
        names = [row["name"] for row in events]

        self.assertIn("gather_end", names)
        self.assertIn("phase_start", names)
        snapshot = session.snapshot()
        self.assertEqual(snapshot["mode"], "day")
        self.assertEqual(snapshot["phase"], "quan")
        self.assertEqual([item.kind for item in session.sim.inventory], ["ca_loc"])
        self.assertEqual(snapshot["stock"], [])

        session.sim.quan.pos = [2, 8]
        cook_events = session.step(InputState((0, 0), {"interact": True}, {"interact"}))
        self.assertIn("cook_started", [row["name"] for row in cook_events])

    def test_day_inventory_appears_when_no_customer_reservation(self):
        tuning = load_contract()["tuning"]
        day = Session(
            "day",
            tuning,
            {
                "gather": {
                    "hold": [],
                    "random_fish": False,
                    "time_left_ticks": 1,
                },
                "quan": {"random_customers": False},
            },
            1,
            inventory={"ca_linh": 12, "ca_loc": 2},
        )
        day.step(InputState((0, 0), {}, set()))
        snapshot = day.snapshot()
        self.assertEqual(snapshot["phase"], "quan")
        self.assertEqual([(item["kind"], item["id"]) for item in snapshot["stock"]],
                         [("ca_linh", "I1"), ("ca_linh", "I2"), ("ca_linh", "I3"),
                          ("ca_linh", "I4"), ("ca_linh", "I5"), ("ca_linh", "I6"),
                          ("ca_linh", "I7"), ("ca_linh", "I8"), ("ca_linh", "I9"),
                          ("ca_linh", "I10"), ("ca_linh", "I11"), ("ca_linh", "I12"),
                          ("ca_loc", "I13"), ("ca_loc", "I14")])


if __name__ == "__main__":
    unittest.main()
