"""PO #11: a due arrival with a free table but no cookable dish is dropped."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


class NoDishTests(unittest.TestCase):
    def setUp(self):
        self.tuning = copy.deepcopy(load_contract()["tuning"])
        self.tuning["quan"]["first_customer_tick"] = 2
        self.tuning["quan"]["customer_interval_s"] = 1 / self.tuning["tick_hz"]

    def run_ticks(self, sim, ticks):
        inp = InputPlayer([])
        return [
            (tick + 1, name, data)
            for tick in range(ticks)
            for name, data in sim.step(inp.advance(tick))
        ]

    def sim(self, scenario=None, menu_filter=None):
        return QuanSim(self.tuning, scenario or {}, Streams(17), IdAllocator(), menu_filter=menu_filter)

    def test_free_table_with_empty_stock_emits_one_no_dish_at_each_due_turn(self):
        sim = self.sim({"stock": {}})
        events = self.run_ticks(sim, 5)

        self.assertEqual([(tick, data) for tick, name, data in events if name == "no_dish"],
                         [(2, {}), (3, {}), (4, {}), (5, {})])
        self.assertFalse(any(name == "customer_arrived" for _, name, _ in events))
        self.assertFalse(sim.done)
        self.assertEqual(sim.ids.new("C"), "C1")

    def test_partial_recipe_and_empty_menu_filter_emit_no_dish(self):
        for scenario, menu_filter in (({"stock": {"ca_linh": 2}}, None),
                                      ({"stock": {"ca_loc": 2}}, [])):
            with self.subTest(menu_filter=menu_filter):
                sim = self.sim(scenario, menu_filter)
                events = self.run_ticks(sim, 2)
                self.assertEqual([name for _, name, _ in events if name in ("no_dish", "customer_arrived")],
                                 ["no_dish"])

    def test_empty_filter_blocks_cookable_stock_and_emits_no_dish(self):
        sim = self.sim({"stock": {"ca_loc": 5, "bong_sung": 10}}, menu_filter=[])
        events = self.run_ticks(sim, 2)
        self.assertEqual([name for _, name, _ in events
                          if name in ("no_dish", "customer_arrived")], ["no_dish"])
        self.assertEqual(sim.planned_dishes, frozenset())

    def test_single_and_multiple_filters_are_preserved(self):
        single = self.sim({"stock": {"ca_loc": 5}}, menu_filter=["ca_loc_nuong_trui"])
        multiple = self.sim({"stock": {"ca_loc": 5, "bong_sung": 10}},
                            menu_filter=["ca_loc_nuong_trui", "goi_bong_sung"])
        self.assertEqual(single.planned_dishes, frozenset({"ca_loc_nuong_trui"}))
        self.assertEqual(multiple.planned_dishes,
                         frozenset({"ca_loc_nuong_trui", "goi_bong_sung"}))

    def test_full_tables_drop_due_turn_without_no_dish(self):
        customers = [
            {"id": f"C{i}", "table_id": f"T{i}", "dish_id": "ca_loc_nuong_trui",
             "reserved": {}}
            for i in range(1, 5)
        ]
        sim = self.sim({"stock": {}, "customers": customers})
        events = self.run_ticks(sim, 2)
        self.assertFalse(any(name in ("no_dish", "customer_arrived") for _, name, _ in events))

    def test_arrival_schedule_is_not_backlogged_after_no_dish(self):
        sim = self.sim({"stock": {}})
        before_due = self.run_ticks(sim, 1)
        self.assertEqual(before_due, [])
        self.assertEqual([name for _, name, _ in self.run_ticks(sim, 1)], ["no_dish"])
        sim.stock = {"ca_loc": 1}
        later = self.run_ticks(sim, 1)
        self.assertEqual([name for _, name, _ in later], ["customer_arrived"])
        self.assertEqual(sim.customers[0]["id"], "C1")


if __name__ == "__main__":
    unittest.main()
