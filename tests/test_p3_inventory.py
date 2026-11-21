"""Unit test cho AC-P3-01 (Adapter kho cá thể v1.2, Item, và bắt lỗi schema).

Chạy: python -m unittest tests.test_p3_inventory -v
"""

from fractions import Fraction
import json
import os
import unittest

from chonoi.errors import BadInput
from chonoi.inventory import (
    Item,
    hold_to_items,
    merge_items,
    read_inventory,
    read_inventory_or_empty,
    write_inventory,
)
try:
    from tests.helpers import Workdir, read_jsonl, run_headless, write_json
except ImportError:
    from helpers import Workdir, read_jsonl, run_headless, write_json


class InventoryPhase3Tests(unittest.TestCase):
    def test_item_class_initialization_and_access(self):
        item = Item("I1", "ca_linh", 97.5)
        self.assertEqual(item.id, "I1")
        self.assertEqual(item.kind, "ca_linh")
        self.assertEqual(item.fresh, Fraction(195, 2))
        self.assertEqual(item["id"], "I1")
        self.assertEqual(item["kind"], "ca_linh")
        self.assertEqual(item["fresh"], 97.5)
        self.assertEqual(item.snapshot(), {"id": "I1", "kind": "ca_linh", "fresh": 97.5})

    def test_item_rejects_invalid_values(self):
        # id rỗng
        with self.assertRaises(BadInput):
            Item("", "ca_linh", 100)
        # kind lạ
        with self.assertRaises(BadInput):
            Item("I1", "ca_map", 100)
        # fresh ngoài [0, 100]
        with self.assertRaises(BadInput):
            Item("I1", "ca_linh", -1)
        with self.assertRaises(BadInput):
            Item("I1", "ca_linh", 100.1)
        # fresh boolean
        with self.assertRaises(BadInput):
            Item("I1", "ca_linh", True)

    def test_read_inventory_v12_rejects_count_inventory(self):
        """Kho đếm khi đọc với version 1.2 phải báo BadInput."""
        with Workdir() as w:
            path = write_json(w.path("inv.json"), {"items": {"ca_loc": 2}})
            with self.assertRaises(BadInput):
                read_inventory(path, version="1.2")

    def test_read_inventory_v10_rejects_individual_inventory(self):
        """Kho cá thể khi đọc với version 1.1 phải báo BadInput."""
        with Workdir() as w:
            path = write_json(w.path("inv.json"), {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]})
            with self.assertRaises(BadInput):
                read_inventory(path, version="1.1")

    def test_read_inventory_v12_validation(self):
        with Workdir() as w:
            # id trùng
            p1 = write_json(w.path("dup.json"), {
                "items": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 100},
                    {"id": "I1", "kind": "ca_linh", "fresh": 90},
                ]
            })
            with self.assertRaises(BadInput):
                read_inventory(p1, version="1.2")

            # kind lạ
            p2 = write_json(w.path("unk.json"), {
                "items": [{"id": "I1", "kind": "tom_hum", "fresh": 100}]
            })
            with self.assertRaises(BadInput):
                read_inventory(p2, version="1.2")

            # fresh ngoài [0, 100]
            p3 = write_json(w.path("fresh_neg.json"), {
                "items": [{"id": "I1", "kind": "ca_loc", "fresh": -5}]
            })
            with self.assertRaises(BadInput):
                read_inventory(p3, version="1.2")

            p4 = write_json(w.path("fresh_hi.json"), {
                "items": [{"id": "I1", "kind": "ca_loc", "fresh": 105}]
            })
            with self.assertRaises(BadInput):
                read_inventory(p4, version="1.2")

            # sai schema (thừa trường)
            p5 = write_json(w.path("extra.json"), {
                "items": [{"id": "I1", "kind": "ca_loc", "fresh": 100, "extra": True}]
            })
            with self.assertRaises(BadInput):
                read_inventory(p5, version="1.2")

    def test_write_and_read_v12_roundtrip_preserves_threshold_30(self):
        """Ghi rồi đọc lại giữ đúng giá trị ở ngưỡng 30 và sắp theo id."""
        with Workdir() as w:
            p = w.path("inv.json")
            items = [
                Item("I10", "ca_linh", 30),
                Item("I2", "keo_neo", 30.0),
                Item("I3", "ca_keo", 97.5),
            ]
            write_inventory(p, items, version="1.2")
            loaded = read_inventory(p, version="1.2")
            self.assertEqual(len(loaded), 3)
            # Sắp theo id: I2, I3, I10
            self.assertEqual([it.id for it in loaded], ["I2", "I3", "I10"])
            self.assertEqual(loaded[0].fresh, Fraction(30))
            self.assertEqual(loaded[1].fresh, Fraction(195, 2))
            self.assertEqual(loaded[2].fresh, Fraction(30))

    def test_merge_items_with_individual_items(self):
        i1 = [Item("I10", "ca_linh", 80), Item("I2", "ca_loc", 90)]
        i2 = [Item("I1", "keo_neo", 100)]
        merged = merge_items(i1, i2)
        self.assertEqual([it.id for it in merged], ["I1", "I2", "I10"])

    def test_day_handoff_individual_items_and_id_continuity(self):
        """AC-P3-08: Bàn giao kho cá thể giữa các ngày và IdAllocator không đụng độ."""
        from chonoi.contract import load_contract
        from chonoi.inputs import InputState
        from chonoi.runner import Session

        contract = load_contract()
        tuning = dict(contract["tuning"])

        scenario = {
            "day": {"days": 2},
            "gather": {
                "player": {"pos": [12, 0]},
                "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                "nodes": [],
                "fish": [],
                "random_fish": False,
                "time_left_ticks": 1,
            },
            "quan": {
                "customers": [],
                "random_customers": False,
                "time_left_ticks": 1,
            },
        }

        sess = Session("day", tuning, scenario, seed=1, days=2)
        # Bắt đầu Day 1
        snap0 = sess.snapshot()
        self.assertEqual(snap0["day"], 1)
        self.assertEqual(snap0["phase"], "gather")

        # Step tick 0 -> kết thúc gather, chuyển sang quan
        evs0 = sess.step(InputState((0, 0), {}, set()))
        self.assertEqual(sess.sim.phase, "quan")
        # Kho ở quan nhận bàn giao cá thể
        self.assertTrue(any(it["id"] == "I1" for it in sess.sim.inventory_items()))

        # Step tick 1 -> kết thúc quan, chuyển sang shop
        evs1 = sess.step(InputState((0, 0), {}, set()))
        self.assertEqual(sess.sim.phase, "shop")

        # Rút ngắn shop để sang Day 2
        sess.sim.shop_time_left_ticks = 1
        evs2 = sess.step(InputState((0, 0), {}, set()))
        self.assertEqual(sess.sim.day, 2)
        self.assertEqual(sess.sim.phase, "gather")

        # Kiểm tra IdAllocator cấp id mới không đụng độ I1 (xuyên ngày)
        new_id = sess.sim.ids.new("I")
        self.assertNotEqual(new_id, "I1")
        self.assertEqual(new_id, "I2")

        # Item còn lại được chuyển sang Gather ngày kế tiếp đúng một lần.
        self.assertEqual([item["id"] for item in sess.sim.gather.inventory_items()], ["I1"])
        self.assertEqual(sess.sim.stock, [])

    def test_day_headless_smoke_two_days(self):
        """AC-P3-08: Headless --mode day --days 2 --ticks 600 chạy trơn tru."""
        with Workdir() as w:
            out_file = w.path("day_smoke.jsonl")
            code, err = run_headless("--mode", "day", "--days", "2", "--seed", "1", "--ticks", "600", "--out", out_file)
            self.assertEqual(code, 0, f"Headless thất bại: {err}")
            self.assertTrue(os.path.exists(out_file))
            rows = read_jsonl(out_file)
            self.assertTrue(len(rows) > 0)
            self.assertEqual(rows[0]["type"], "snapshot")
            self.assertEqual(rows[0]["mode"], "day")
            self.assertEqual(rows[-1]["type"], "end")


if __name__ == "__main__":
    unittest.main()
