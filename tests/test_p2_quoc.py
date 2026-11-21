"""Phase 2 customer seam tests with provisional tuning, not official acceptance."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


class Phase2Customers(unittest.TestCase):
    def make_sim(self, menu_filter):
        tuning = copy.deepcopy(load_contract()["tuning"])
        tuning["quan"]["tables"] = [{"id": f"T{i}", "pos": [i, 2]} for i in range(1, 5)]
        tuning["quan"]["stoves"].append({"id": "B2", "pos": [4, 8]})
        scenario = {"stock": {"ca_loc": 10, "bong_sung": 20}}
        return QuanSim(tuning, scenario, Streams(1), IdAllocator(), menu_filter=menu_filter)

    def test_schedule_four_tables_and_plan_filter(self):
        sim = self.make_sim({"goi_bong_sung"})
        player = InputPlayer([])
        arrivals = []
        for tick in range(120 + 900 * 4):
            for name, data in sim.step(player.advance(tick)):
                if name == "customer_arrived":
                    arrivals.append((tick + 1, data["table_id"], data["dish_id"]))
        self.assertEqual(arrivals, [(120 + 900 * i, f"T{i % 4 + 1}", "goi_bong_sung") for i in range(5)])
        self.assertEqual(len(sim.stoves), 2)

    def test_empty_plan_and_invalid_dish(self):
        sim = self.make_sim(set())
        self.assertFalse(sim._can_accept_order())
        player = InputPlayer([])
        events = [event for tick in range(120) for event in sim.step(player.advance(tick))]
        self.assertFalse(any(name == "customer_arrived" for name, _ in events))
        with self.assertRaises(BadInput):
            self.make_sim({"unknown"})
