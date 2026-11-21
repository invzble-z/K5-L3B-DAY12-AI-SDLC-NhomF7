"""Phase 3, HUD độ tươi (AC-P3-09, nganhduong123).

- Mock v1.2 (`day-gather-v12`, `day-quan-v12`) đúng schema kho cá thể và có cả hàng tươi lẫn hàng ươn.
- Bản chơi live với tuning v1.2 đưa mảng cá thể `{id, kind, fresh}` và ngưỡng `freshness` tới client.
- Client đọc được cả hai schema kho (mảng tên loài / map đếm và mảng cá thể).
"""

import copy
import json
import os
import time
import unittest
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import WEB_DIR, LiveGame, LiveServer

FRESHNESS = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}


def _mock(name):
    with open(os.path.join(WEB_DIR, "mock", name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def _read(rel):
    with open(os.path.join(WEB_DIR, rel), encoding="utf-8") as f:
        return f.read()


class MockV12Test(unittest.TestCase):
    def _check_items(self, items, below):
        self.assertTrue(items)
        ids = [it["id"] for it in items]
        self.assertEqual(len(ids), len(set(ids)))
        for it in items:
            self.assertEqual(set(it), {"id", "kind", "fresh"})
            self.assertTrue(0 <= it["fresh"] <= 100, it)
        self.assertTrue(any(it["fresh"] < below for it in items), "cần ít nhất một hàng ươn để thử HUD")
        self.assertTrue(any(it["fresh"] >= below for it in items))

    def test_gather_mock_hold_is_individual(self):
        snap = _mock("day-gather-v12")
        self._check_items(snap["hold"], snap["freshness"]["spoiled_below"])
        self.assertEqual(snap["hold_count"], len(snap["hold"]))
        self.assertLessEqual(len(snap["hold"]), snap["hold_capacity"])
        self.assertIn("spoiled", [e["name"] for e in snap["events"]])

    def test_quan_mock_stock_is_individual(self):
        snap = _mock("day-quan-v12")
        self._check_items(snap["stock"], snap["freshness"]["spoiled_below"])


class ClientReadsBothSchemasTest(unittest.TestCase):
    def test_hud_uses_shared_inventory_helpers(self):
        self.assertIn("CN.inv", _read("js/core/draw.js"))
        for rel in ("js/gather/hud.js", "js/quan/hud.js", "js/shared/overlay.js", "js/shop/scene.js", "js/shared/screens.js"):
            self.assertIn("CN.inv.", _read(rel), rel)
        self.assertIn("ươn", _read("js/gather/hud.js"))
        self.assertIn("ươn", _read("js/quan/hud.js"))


class LiveV12Test(unittest.TestCase):
    def test_live_gather_v12_sends_individual_hold_and_threshold(self):
        tuning = copy.deepcopy(load_contract()["tuning"])
        tuning["contract_version"] = "1.2"
        tuning["freshness"] = dict(FRESHNESS)
        scenario = {"random_fish": False, "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30},
                                                   {"id": "I2", "kind": "bong_sung", "fresh": 90}]}
        server = LiveServer(LiveGame("gather", tuning, scenario, 1), port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            end = time.monotonic() + 5
            while True:
                with urllib.request.urlopen(base + "/state", timeout=5) as r:
                    snap = json.loads(r.read())
                if snap["tick"] > 2 or time.monotonic() > end:
                    break
                time.sleep(0.05)
            self.assertEqual(snap["freshness"]["spoiled_below"], 30)
            self.assertEqual([it["id"] for it in snap["hold"]], ["I1", "I2"])
            self.assertLess(snap["hold"][0]["fresh"], 30)
            spoiled = [e for e in snap["events"] if e["name"] == "spoiled"]
            self.assertEqual([e["data"]["item_id"] for e in spoiled], ["I1"])
        finally:
            server.stop()

    def test_live_counted_hold_stays_kind_list(self):
        # Explicit v1.1 keeps the legacy counted-hold contract after root manifest v1.3.
        tuning = copy.deepcopy(load_contract()["tuning"])
        tuning["contract_version"] = "1.1"
        server = LiveServer(LiveGame("gather", tuning, {"hold": ["ca_linh", "bong_sung"]}, 1), port=0)
        server.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{server.port}/state", timeout=5) as r:
                snap = json.loads(r.read())
            self.assertEqual(snap["hold"], ["ca_linh", "bong_sung"])
            self.assertEqual("freshness" in snap, "freshness" in tuning)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
