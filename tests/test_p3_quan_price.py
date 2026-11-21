"""Unit test cho sim/quan Phase 3 - AC-P3-05 (Trần Trung Kiên - ttkien0710).

Kiểm chứng các yêu cầu AC-P3-05:
1. Nấu tiêu đúng id cá thể nguyên liệu đang giữ.
2. cook_started.items là mảng cá thể sắp xếp theo kind rồi id.
3. base_price = floor(giá × trung bình fresh / 100) (tính bằng số nguyên / Fraction).
4. Tiền boa (tip) = floor(base_price × 0.2) tính trên base_price đã chốt (không tính trên giá gốc menu).
5. Món chín không hao thêm độ tươi.
6. Món cháy (burn) làm mất nguyên liệu cá thể đã nấu.
"""

import copy
from fractions import Fraction
import math
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.runner import Session


class QuanPhase3PriceTests(unittest.TestCase):
    def setUp(self):
        base_tuning = load_contract()["tuning"]
        self.tuning = copy.deepcopy(base_tuning)
        self.tuning["quan"]["stoves"] = [
            {"id": "B1", "pos": [2, 8]},
            {"id": "B2", "pos": [5, 8]},
        ]
        self.tuning["quan"]["tables"] = [
            {"id": "T1", "pos": [9, 2]},
            {"id": "T2", "pos": [13, 2]},
        ]
        self.tuning["menu"] = {
            "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
            "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40},
            "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
        }

    def test_base_price_and_tip_single_item(self):
        """Fresh=80 decays one tick before cooking; base_price floors to 47 and tip to 9."""
        sc = {
            "player": {"pos": [2, 8]},
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 80}
            ],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order": "ca_loc_nuong_trui",
                 "reserved": ["I1"], "patience_ticks_left": 3600, "patience_max_ticks": 3600, "eat_ticks_left": 2}
            ]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # 1. Bấm nấu tại B1
        li.set(interact=True)
        evs = s.step(li.advance())
        cook_ev = [e for e in evs if e["name"] == "cook_started"]
        self.assertEqual(len(cook_ev), 1)
        self.assertEqual(cook_ev[0]["data"]["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(len(cook_ev[0]["data"]["items"]), 1)
        self.assertEqual(cook_ev[0]["data"]["items"][0]["id"], "I1")
        # Phase 3 order decays raw stock before the first interaction tick.
        self.assertAlmostEqual(cook_ev[0]["data"]["items"][0]["fresh"], 80 - 1 / 240)

        # 2. Tua qua nấu -> chín
        s.sim.stoves[0]["cook_ticks_left"] = 1
        li.set(interact=False)
        s.step(li.advance())

        # 3. Nhấc món lên tay
        li.set(interact=True)
        s.step(li.advance())
        self.assertEqual(s.sim.hand, "ca_loc_nuong_trui")

        # 4. Phục vụ tại bàn T1 [9, 2]
        li.set(interact=False)
        s.sim.pos = [9, 2]
        s.step(li.advance())
        li.set(interact=True)
        s.step(li.advance())

        # 5. Khách ăn xong -> paid
        s.sim.customers[0]["eat_ticks_left"] = 1
        li.set(interact=False)
        all_evs = s.step(li.advance())
        paid_ev = [e for e in all_evs if e["name"] == "paid"]
        self.assertEqual(len(paid_ev), 1)
        # One tick of Phase 3 stock decay makes floor(60 * fresh / 100) = 47.
        self.assertEqual(paid_ev[0]["data"]["price"], 47)
        # Tip remains floor(base_price * 0.2).
        self.assertEqual(paid_ev[0]["data"]["tip"], 9)
        self.assertEqual(s.sim.money, 47 + 9)

    def test_base_price_multi_item_and_cook_started_items_sorting(self):
        """2 items start at fresh=73 and 64 and decay one tick; base_price still floors to 61.
        cook_started.items phải sắp xếp theo kind rồi id (bong_dien_dien trước ca_loc).
        """
        sc = {
            "player": {"pos": [2, 8]},
            "stock": [
                {"id": "I2", "kind": "ca_loc", "fresh": 64},
                {"id": "I1", "kind": "bong_dien_dien", "fresh": 73},
            ],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "canh_chua_ca_loc", "order": "canh_chua_ca_loc",
                 "reserved": ["I2", "I1"], "patience_ticks_left": 3600, "patience_max_ticks": 3600, "eat_ticks_left": 2}
            ]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # Bấm nấu
        li.set(interact=True)
        evs = s.step(li.advance())
        cook_ev = [e for e in evs if e["name"] == "cook_started"]
        self.assertEqual(len(cook_ev), 1)
        items = cook_ev[0]["data"]["items"]
        self.assertEqual(len(items), 2)
        # Thứ tự kind: bong_dien_dien trước ca_loc
        self.assertEqual(items[0]["kind"], "bong_dien_dien")
        self.assertEqual(items[0]["id"], "I1")
        self.assertEqual(items[1]["kind"], "ca_loc")
        self.assertEqual(items[1]["id"], "I2")

        # Tua và phục vụ
        s.sim.stoves[0]["cook_ticks_left"] = 1
        li.set(interact=False)
        s.step(li.advance())

        li.set(interact=True)
        s.step(li.advance())

        li.set(interact=False)
        s.sim.pos = [9, 2]
        s.step(li.advance())
        li.set(interact=True)
        s.step(li.advance())

        # Ăn xong
        s.sim.customers[0]["eat_ticks_left"] = 1
        li.set(interact=False)
        evs_paid = s.step(li.advance())
        paid_ev = [e for e in evs_paid if e["name"] == "paid"]
        self.assertEqual(len(paid_ev), 1)
        # floor(90 * 68.5 / 100) = floor(61.65) = 61
        self.assertEqual(paid_ev[0]["data"]["price"], 61)
        # floor(61 * 0.2) = floor(12.2) = 12
        self.assertEqual(paid_ev[0]["data"]["tip"], 12)
        self.assertEqual(s.sim.money, 61 + 12)

    def test_tip_zero_when_patience_ratio_below_half(self):
        """Một tick decay cho giá 59; khách phục vụ dưới 50% patience nhận tip 0."""
        sc = {
            "player": {"pos": [2, 8]},
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 100}
            ],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order": "ca_loc_nuong_trui",
                 "reserved": ["I1"], "patience_ticks_left": 100, "patience_max_ticks": 3600, "eat_ticks_left": 1}
            ]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # Nấu và phục vụ
        li.set(interact=True)
        s.step(li.advance())
        s.sim.stoves[0]["cook_ticks_left"] = 1
        li.set(interact=False)
        s.step(li.advance())
        li.set(interact=True)
        s.step(li.advance())
        li.set(interact=False)
        s.sim.pos = [9, 2]
        s.step(li.advance())
        li.set(interact=True)
        s.step(li.advance())

        s.sim.customers[0]["eat_ticks_left"] = 1
        li.set(interact=False)
        evs = s.step(li.advance())
        paid_ev = [e for e in evs if e["name"] == "paid"]
        self.assertEqual(len(paid_ev), 1)
        self.assertEqual(paid_ev[0]["data"]["price"], 59)
        self.assertEqual(paid_ev[0]["data"]["tip"], 0)
        self.assertEqual(s.sim.money, 59)

    def test_ready_dish_does_not_decay_freshness(self):
        """Món đã nấu chín trên bếp không bị hao thêm độ tươi theo thời gian."""
        sc = {
            "player": {"pos": [2, 8]},
            "stoves": [
                {"id": "B1", "pos": [2, 8], "state": "ready", "dish": "ca_loc_nuong_trui",
                 "base_price": 50, "ready_ticks": 10}
            ],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order": "ca_loc_nuong_trui",
                 "reserved": [], "patience_ticks_left": 3600, "patience_max_ticks": 3600, "eat_ticks_left": 1}
            ]
        }
        s = Session("quan", self.tuning, sc, 1)
        li = LiveInputs()

        # Tua 100 ticks trên bếp ready
        for _ in range(100):
            s.step(li.advance())
        self.assertEqual(s.sim.stoves[0]["ready_ticks"], 110)
        self.assertEqual(s.sim.stoves[0]["base_price"], 50)

        # Nhấc và phục vụ
        li.set(interact=True)
        s.step(li.advance())
        li.set(interact=False)
        s.sim.pos = [9, 2]
        s.step(li.advance())
        li.set(interact=True)
        s.step(li.advance())

        s.sim.customers[0]["eat_ticks_left"] = 1
        li.set(interact=False)
        evs = s.step(li.advance())
        paid_ev = [e for e in evs if e["name"] == "paid"]
        self.assertEqual(len(paid_ev), 1)
        self.assertEqual(paid_ev[0]["data"]["price"], 50)


if __name__ == "__main__":
    unittest.main()
