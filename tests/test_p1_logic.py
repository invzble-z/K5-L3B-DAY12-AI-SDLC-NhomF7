import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from chonoi.sim.quan import QuanSim


class GatherLogic(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_empty_oxygen_chokes_and_faints(self):
        scenario = {"player": {"pos": [20, 10], "oxygen_ticks": 0, "hp": 1},
                    "hold": ["ca_loc"], "random_fish": False}
        sim = GatherSim(self.tuning, scenario, Streams(1), IdAllocator())
        sim.zero_oxy_ticks = self.tuning["gather"]["choke_interval_ticks"] - 1
        events = sim.step(LiveInputs().advance())
        names = [name for name, _ in events]
        self.assertIn("choke", names)
        self.assertIn("faint", names)
        self.assertIn("gather_end", names)
        self.assertEqual(sim.hp, 0)
        self.assertEqual(sim.hold, [])

    def test_harvest_lifo_and_hold_full(self):
        scenario = {"player": {"pos": [12, 0]}, "hold": ["ca_loc"] * 11,
                    "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                    "random_fish": False}
        sim = GatherSim(self.tuning, scenario, Streams(1), IdAllocator())
        inp = LiveInputs()
        inp.set(interact=True)
        events = sim.step(inp.advance())
        names = [name for name, _ in events]
        self.assertIn("gather", names)
        self.assertIn("hold_full", names)
        self.assertEqual(sim.hold[-1].kind, "bong_sung")
        self.assertEqual(len(sim.hold), 12)


class QuanLogic(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_reserved_customer_cooks_serves_and_pays(self):
        dish = "goi_bong_sung"
        recipe = self.tuning["menu"][dish]["recipe"]
        scenario = {"stock": {"bong_sung": 2},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish,
                                   "state": "waiting", "patience_ticks_left": 3600,
                                   "reserved": dict(recipe)}]}
        sim = QuanSim(self.tuning, scenario, Streams(1), IdAllocator())
        sim.pos = [2, 8]
        inp = LiveInputs()
        inp.set(interact=True)
        events = sim.step(inp.advance())
        names = [name for name, _ in events]
        self.assertIn("cook_started", names)

        for _ in range(self.tuning["menu"][dish]["cook_s"] * 60):
            sim.step(LiveInputs().advance())
        self.assertEqual(sim.stoves[0]["state"], "ready")
        sim.pos = [2, 8]
        inp = LiveInputs()
        inp.set(interact=True)
        self.assertIsNotNone(sim._nearest_interaction())
        self.assertIsNone(sim.hand)
        events = sim.step(inp.advance())
        self.assertIn("dish_picked", [name for name, _ in events])

        sim.pos = [9, 2]
        inp = LiveInputs()
        inp.set(interact=True)
        events = sim.step(inp.advance())
        names = [name for name, _ in events]
        self.assertIn("served", names)

        for _ in range(self.tuning["quan"]["eat_s"] * 60):
            sim.step(LiveInputs().advance())
        self.assertGreater(sim.earned, 0)
        self.assertGreaterEqual(sim.money, self.tuning["menu"][dish]["price"])

    def test_customer_leaves_and_reputation_drops(self):
        dish = "goi_bong_sung"
        scenario = {"stock": {"bong_sung": 2},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish,
                                   "state": "waiting", "patience_ticks_left": 1,
                                   "reserved": dict(self.tuning["menu"][dish]["recipe"])}]}
        sim = QuanSim(self.tuning, scenario, Streams(1), IdAllocator())
        events = sim.step(LiveInputs().advance())
        names = [name for name, _ in events]
        self.assertIn("customer_left", names)
        self.assertEqual(sim.reputation,
                         self.tuning["quan"]["reputation_initial"] +
                         self.tuning["quan"]["left_reputation_delta"])


if __name__ == "__main__":
    unittest.main()
