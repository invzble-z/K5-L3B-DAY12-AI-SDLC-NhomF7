"""Independent customer integration tests; fixture data is not v1.1 acceptance."""
import copy
import json
from pathlib import Path
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


class CustomersPhase2(unittest.TestCase):
    def setUp(self):
        self.tuning = copy.deepcopy(load_contract()["tuning"])
        fixture = json.loads((Path(__file__).parent / "fixtures/p2/q3/tuning.json").read_text(encoding="utf-8"))
        self.tuning["quan"]["tables"] = fixture["tables"]
        self.tuning["quan"]["stoves"].append({"id": "B2", "pos": [5, 8]})
        self.fixture_dishes = set(fixture["extra_menu"])
        self.tuning["menu"].update(fixture["extra_menu"])

    def sim(self, scenario=None, menu_filter=None, seed=1):
        return QuanSim(self.tuning, scenario or {}, Streams(seed), IdAllocator(), menu_filter=menu_filter)

    def run_steps(self, sim, count):
        player = InputPlayer([])
        return [(tick + 1, name, data) for tick in range(count)
                for name, data in sim.step(player.advance(tick))]

    def test_six_dishes_independent_and_full_recipe(self):
        before = copy.deepcopy(self.tuning)
        for dish, entry in self.tuning["menu"].items():
            sim = self.sim({"stock": dict(entry["recipe"])}, [dish])
            events = self.run_steps(sim, 120)
            self.assertEqual([d["dish_id"] for _, n, d in events if n == "customer_arrived"], [dish])
            self.assertEqual(sim.customers[0]["reserved"], entry["recipe"])
        self.assertEqual(len(set(self.tuning["menu"]) - self.fixture_dishes), 6)
        self.assertEqual(self.tuning, before)

    def test_plan_filters_before_recipe_and_rng(self):
        sim = self.sim({"stock": {"ca_loc": 1, "bong_sung": 2}}, ["fixture_a", "goi_bong_sung"])
        events = self.run_steps(sim, 120)
        self.assertIn(next(d["dish_id"] for _, n, d in events if n == "customer_arrived"), {"fixture_a", "goi_bong_sung"})
        sim = self.sim({"stock": {"ca_loc": 5}}, ["fixture_a"])
        self.assertFalse(any(n == "customer_arrived" for _, n, _ in self.run_steps(sim, 120)))

    def test_full_tables_no_duplicates_and_no_queue(self):
        customers = [{"id": f"C{i}", "table_id": f"T{i}", "dish_id": "ca_loc_nuong_trui", "reserved": {"ca_loc": 1}} for i in range(1, 5)]
        sim = self.sim({"stock": {"ca_loc": 5}, "customers": customers})
        self.assertFalse(any(n == "customer_arrived" for _, n, _ in self.run_steps(sim, 121)))
        self.assertEqual(len({c["table_id"] for c in sim.customers}), 4)

    def test_random_disabled_and_order_tick_snapshot(self):
        sim = self.sim({"stock": {"ca_loc": 2}, "random_customers": False,
                        "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 7}]})
        self.assertEqual(sim.snapshot()["customers"][0]["order_tick"], 7)
        self.assertFalse(any(n == "customer_arrived" for _, n, _ in self.run_steps(sim, 121)))
        with self.assertRaises(BadInput):
            self.sim({"stock": {"ca_loc": 1}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": -1}]})

    def test_seed_replay_and_no_filter(self):
        scenario = {"stock": {"ca_loc": 10, "bong_sung": 10, "ca_linh": 10, "bong_dien_dien": 10}}
        a, b = self.sim(scenario), self.sim(scenario)
        self.assertEqual(self.run_steps(a, 1920), self.run_steps(b, 1920))
        self.assertEqual(a.snapshot(), b.snapshot())

    def test_payment_and_departure_release_tables(self):
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "eat_ticks_left": 1}
        sim = self.sim({"customers": [customer], "random_customers": False})
        self.assertEqual([n for _, n, _ in self.run_steps(sim, 2)], ["paid"])
        self.assertIsNone(sim.snapshot()["tables"][0]["customer_id"])
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 1}
        sim = self.sim({"stock": {"ca_loc": 1}, "customers": [customer], "random_customers": False})
        self.assertEqual([n for _, n, _ in self.run_steps(sim, 2)], ["customer_left"])
        self.assertEqual(sim._available_stock(), {"ca_loc": 1})
        self.assertIsNone(sim.snapshot()["tables"][0]["customer_id"])

    def test_two_stoves_do_not_consume_same_order(self):
        sim = self.sim({"player": {"pos": [2, 8]}, "stock": {"ca_loc": 1},
                        "random_customers": False, "customers": [{"id": "C1", "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui", "order_tick": 5}]})
        self.assertEqual([n for n, _ in sim._interact()], ["cook_started"])
        sim.pos = [5, 8]
        self.assertEqual(sim._interact(), [])
        self.assertEqual(sim.stock.get("ca_loc", 0), 0)
        self.assertEqual(sim.stoves[1]["state"], "idle")

    def test_q4_f1_orphan_dish_reproduced(self):
        sim = self.sim({"player": {"pos": [2, 8]}, "stock": {"ca_loc": 1},
                        "random_customers": False, "customers": [{"id": "C1", "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 2}]})
        self.assertEqual([n for n, _ in sim._interact()], ["cook_started"])
        self.run_steps(sim, 2)
        self.assertEqual(sim.customers, [])
        sim.stoves[0]["cook_ticks_left"] = 1
        self.run_steps(sim, 1)
        self.assertEqual([n for n, _ in sim._interact()], ["dish_picked"])
        self.assertEqual(sim.hand, "ca_loc_nuong_trui")

    def test_each_new_shift_restarts_arrival_clock_and_copies_inventory(self):
        stock = {"ca_loc": 2}
        def new_shift():
            return QuanSim(self.tuning, {}, Streams(1), IdAllocator(), inventory=stock,
                           menu_filter=["ca_loc_nuong_trui"])
        first, second = new_shift(), new_shift()
        for sim in (first, second):
            events = self.run_steps(sim, 120)
            self.assertEqual([t for t, name, _ in events if name == "customer_arrived"], [120])
            self.assertEqual(sim.snapshot()["customers"][0]["order_tick"], 120)
            self.assertEqual(sim.snapshot()["stock"], {"ca_loc": 1})
        self.assertEqual(stock, {"ca_loc": 2})

    def test_two_distinct_orders_consumed_once(self):
        sim = self.sim({"player": {"pos": [2, 8]}, "stock": {"ca_loc": 2}, "random_customers": False,
                        "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"},
                                      {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui"}]})
        self.assertEqual([n for n, _ in sim._interact()], ["cook_started"])
        sim.pos = [5, 8]
        self.assertEqual([n for n, _ in sim._interact()], ["cook_started"])
        self.assertEqual(sim.stock.get("ca_loc", 0), 0)
        self.assertEqual([c["state"] for c in sim.customers], ["ordered", "ordered"])
        self.assertFalse(sim._consume_reservation("C1"))
        self.assertEqual(sim._release_reservation("C1"), {})
