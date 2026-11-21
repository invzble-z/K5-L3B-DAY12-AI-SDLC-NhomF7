"""Regression for PO #13: reuse a cooked dish after its original customer leaves."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session


class OrphanDishReuseTests(unittest.TestCase):
    def test_cooked_dish_serves_matching_waiter_and_releases_their_item_ids(self):
        tuning = copy.deepcopy(load_contract()["tuning"])
        tuning["quan"]["tip_min_patience_ratio"] = 0.1
        scenario = {
            "random_customers": False,
            "time_left_ticks": 1000,
            "player": {"pos": [2, 8]},
            "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
            "stoves": [{"id": "B1", "state": "cooking", "dish": "ca_loc_nuong_trui",
                        "cook_ticks_left": 2}],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                 "state": "ordered", "patience_ticks_left": 1, "reserved": []},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui",
                 "state": "waiting", "patience_ticks_left": 200,
                 "reserved": ["I1"], "eat_ticks_left": 1},
            ],
        }
        session = Session("quan", tuning, scenario, seed=3)
        sim = session.sim

        left = session.step(InputState((0, 0), {}, set()))
        ready = session.step(InputState((0, 0), {}, set()))
        self.assertIn("customer_left", [row["name"] for row in left])
        self.assertIn("dish_ready", [row["name"] for row in ready])
        self.assertEqual(sim.items[0].id, "I1")

        b1 = next(stove for stove in sim.stoves if stove["id"] == "B1")
        sim.pos = list(b1["pos"])
        picked = session.step(InputState((0, 0), {"interact": True}, {"interact"}))
        self.assertIn("dish_picked", [row["name"] for row in picked])
        sim.pos = list(next(table["pos"] for table in sim.tables if table["id"] == "T2"))
        served = session.step(InputState((0, 0), {"interact": True}, {"interact"}))
        self.assertEqual([row["data"]["customer_id"] for row in served if row["name"] == "served"], ["C2"])
        self.assertEqual(sim.customers[0]["state"], "eating")
        self.assertEqual(sim._reservation_state["C2"], "released")
        self.assertEqual(sim.customers[0]["reserved"], [])
        self.assertEqual([item.id for item in sim.items], ["I1"])
        self.assertEqual(sim._reserved_item_ids(), set())

        paid = []
        for _ in range(int(round(tuning["quan"]["eat_s"] * tuning["tick_hz"])) + 2):
            paid.extend(row for row in session.step(InputState((0, 0), {}, set()))
                        if row["name"] == "paid")
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0]["data"]["customer_id"], "C2")
        self.assertEqual(sim.money, paid[0]["data"]["price"] + paid[0]["data"]["tip"])
        self.assertEqual([item.id for item in sim.items], ["I1"])
        self.assertFalse(any(row["name"] == "served" for row in
                             session.step(InputState((0, 0), {"interact": True}, {"interact"}))))


if __name__ == "__main__":
    unittest.main()
