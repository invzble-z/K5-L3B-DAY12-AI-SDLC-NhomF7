"""Q3 Phase 3 stock freshness, physical ID reservation and spoil recovery."""

import copy
from fractions import Fraction
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


class QuanFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.tuning = copy.deepcopy(load_contract()["tuning"])
        self.tuning["quan"]["first_customer_tick"] = 10000
        self.tuning["menu"] = {
            "dish_one": {"recipe": {"ca_loc": 1}, "cook_s": 1, "price": 60},
            "dish_two": {"recipe": {"ca_loc": 1, "bong_sung": 2}, "cook_s": 1, "price": 90},
        }

    def sim(self, stock, customers=None):
        scenario = {"stock": stock, "random_customers": False, "customers": customers or []}
        return QuanSim(self.tuning, scenario, Streams(7), IdAllocator())

    def tick(self, sim, n=1):
        player = InputPlayer([])
        events = []
        for index in range(n):
            events.extend(sim.step(player.advance(index)))
        return events

    def test_freshness_uses_exact_quan_decay_and_is_clamped_at_zero(self):
        sim = self.sim([{"id": "I1", "kind": "ca_loc", "fresh": 100},
                        {"id": "I2", "kind": "ca_loc", "fresh": 0.001}])
        self.tick(sim, 60)
        self.assertEqual(sim.items[0].fresh, Fraction(9975, 100))
        self.assertEqual(sim.items[1].fresh, 0)

    def test_reservation_picks_freshest_then_smallest_numeric_id(self):
        sim = self.sim([
            {"id": "I10", "kind": "ca_loc", "fresh": 80},
            {"id": "I2", "kind": "ca_loc", "fresh": 80},
            {"id": "I1", "kind": "ca_loc", "fresh": 75},
        ])
        customer = {"id": "C1", "dish_id": "dish_one", "reserved": []}
        self.assertTrue(sim._reserve_for_customer(customer))
        sim.customers.append(customer)
        self.assertEqual(customer["reserved"], ["I2"])
        self.assertEqual(sim._available_stock(), {"ca_loc": 2})

    def test_multikind_reservation_is_atomic_and_never_overlaps_ids(self):
        sim = self.sim([
            {"id": "I1", "kind": "ca_loc", "fresh": 90},
            {"id": "I2", "kind": "bong_sung", "fresh": 90},
            {"id": "I3", "kind": "bong_sung", "fresh": 80},
        ])
        first = {"id": "C1", "dish_id": "dish_two", "reserved": []}
        second = {"id": "C2", "dish_id": "dish_two", "reserved": []}
        self.assertTrue(sim._reserve_for_customer(first))
        sim.customers.append(first)
        self.assertFalse(sim._reserve_for_customer(second))
        self.assertEqual(first["reserved"], ["I1", "I2", "I3"])
        self.assertEqual(second["reserved"], [])
        self.assertEqual(sim._available_stock(), {})

    def test_missing_one_ingredient_never_reserves_a_partial_recipe(self):
        sim = self.sim([{"id": "I1", "kind": "ca_loc", "fresh": 90},
                        {"id": "I2", "kind": "bong_sung", "fresh": 90}])
        customer = {"id": "C1", "dish_id": "dish_two", "reserved": []}
        self.assertFalse(sim._reserve_for_customer(customer))
        self.assertEqual(customer["reserved"], [])
        self.assertEqual(sim._available_stock(), {"bong_sung": 1, "ca_loc": 1})

    def test_spoiled_event_crosses_threshold_once_in_stable_id_order(self):
        sim = self.sim([
            {"id": "I10", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_loc", "fresh": 30},
            {"id": "I3", "kind": "bong_sung", "fresh": 29.999},
        ])
        events = self.tick(sim, 3)
        spoiled = [data for name, data in events if name == "spoiled"]
        self.assertEqual(spoiled, [
            {"item_id": "I2", "kind": "ca_loc", "location": "stock"},
            {"item_id": "I10", "kind": "ca_loc", "location": "stock"},
        ])

    def test_spoiled_reserved_item_releases_then_re_reserves_once(self):
        sim = self.sim([
            {"id": "I1", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_loc", "fresh": 60},
        ], [{"id": "C1", "table_id": "T1", "dish_id": "dish_one",
             "reserved": ["I1"], "patience_ticks_left": 100}])
        events = self.tick(sim)
        self.assertEqual([name for name, _ in events], ["spoiled"])
        self.assertEqual(sim.customers[0]["reserved"], ["I2"])
        self.assertNotIn("order_status", sim.customers[0])
        self.assertEqual(sim._available_stock(), {})

    def test_failed_spoil_recovery_marks_order_unfulfillable_once_without_stock_loss(self):
        sim = self.sim([{"id": "I1", "kind": "ca_loc", "fresh": 30}],
                       [{"id": "C1", "table_id": "T1", "dish_id": "dish_one",
                         "reserved": ["I1"], "patience_ticks_left": 100}])
        events = self.tick(sim, 3)
        self.assertEqual([name for name, _ in events], ["spoiled", "unfulfillable"])
        self.assertEqual(sim.customers[0]["order_status"], "unfulfillable")
        self.assertEqual(sim.customers[0]["reserved"], [])
        self.assertEqual([item.id for item in sim.items], ["I1"])
        self.assertEqual(sim._available_stock(), {})

    def test_consume_and_release_are_idempotent_for_physical_ids(self):
        sim = self.sim([{"id": "I1", "kind": "ca_loc", "fresh": 90}], [
            {"id": "C1", "table_id": "T1", "dish_id": "dish_one", "reserved": ["I1"]}
        ])
        self.assertTrue(sim._consume_reservation("C1"))
        self.assertFalse(sim._consume_reservation("C1"))
        self.assertEqual(sim.items, [])
        self.assertEqual(sim.customers[0]["consumed_items"][0]["id"], "I1")
        self.assertEqual(sim._release_reservation("C1"), {})

        waiting = self.sim([{"id": "I2", "kind": "ca_loc", "fresh": 90}], [
            {"id": "C2", "table_id": "T1", "dish_id": "dish_one", "reserved": ["I2"]}
        ])
        self.assertEqual(waiting._release_reservation("C2"), ["I2"])
        self.assertEqual(waiting._release_reservation("C2"), {})
        self.assertEqual(waiting._available_stock(), {"ca_loc": 1})

    def test_same_seed_and_stock_replay_identically(self):
        tuning = copy.deepcopy(self.tuning)
        tuning["quan"]["first_customer_tick"] = 2
        tuning["quan"]["customer_interval_s"] = 1 / tuning["tick_hz"]
        stock = [{"id": f"I{i}", "kind": "ca_loc", "fresh": 100} for i in range(1, 9)]

        def replay():
            sim = QuanSim(tuning, {"stock": copy.deepcopy(stock)}, Streams(71), IdAllocator())
            player = InputPlayer([])
            return [event for index in range(100)
                    for event in sim.step(player.advance(index))], sim.snapshot()

        self.assertEqual(replay(), replay())

    def test_duplicate_reserved_item_ids_are_rejected(self):
        with self.assertRaises(BadInput):
            self.sim([{"id": "I1", "kind": "ca_loc", "fresh": 100}], [
                {"id": "C1", "table_id": "T1", "dish_id": "dish_one", "reserved": ["I1"]},
                {"id": "C2", "table_id": "T2", "dish_id": "dish_one", "reserved": ["I1"]},
            ])


if __name__ == "__main__":
    unittest.main()
