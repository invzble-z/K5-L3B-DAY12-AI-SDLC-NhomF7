import json
import unittest
from fractions import Fraction
from pathlib import Path

from chonoi.inputs import InputState
from chonoi.runner import Session


class GatherFreshnessTest(unittest.TestCase):
    def session(self, **scenario):
        contract = Path(__file__).resolve().parents[1] / "game.contract.json"
        tuning = json.loads(contract.read_text(encoding="utf-8"))["tuning"]
        tuning["contract_version"] = "1.2"
        tuning["freshness"] = {
            "initial": 100, "gather_decay_per_s": 0.5,
            "quan_decay_per_s": 0.25, "spoiled_below": 30,
        }
        return Session("gather", tuning, {"random_fish": False, **scenario}, seed=1)

    def step(self, session, *buttons):
        return session.step(InputState((0, 0), {}, set(buttons)))

    def test_spoils_once_in_id_order_and_clamps_at_zero(self):
        session = self.session(hold=[
            {"id": "I10", "kind": "ca_linh", "fresh": 30},
            {"id": "I2", "kind": "keo_neo", "fresh": 30},
            {"id": "I3", "kind": "ca_keo", "fresh": 0.005},
        ])
        events = self.step(session)
        self.assertEqual([event["name"] for event in events], ["spoiled", "spoiled"])
        self.assertEqual([event["data"] for event in events], [
            {"item_id": "I2", "kind": "keo_neo", "location": "hold"},
            {"item_id": "I10", "kind": "ca_linh", "location": "hold"},
        ])
        self.assertEqual(self.step(session), [])
        hold = session.snapshot()["hold"]
        self.assertEqual([item["id"] for item in hold], ["I10", "I2", "I3"])
        self.assertAlmostEqual(hold[0]["fresh"], float(Fraction(30) - Fraction(1, 60)))
        self.assertEqual(hold[2]["fresh"], 0)

    def test_catch_assigns_ids_and_dock_exports_sorted_items(self):
        session = self.session(
            player={"pos": [40, 5]},
            hold=[{"id": "I8", "kind": "keo_neo", "fresh": 30}],
            fish=[{"id": "F1", "kind": "ca_linh", "pos": [40, 5]}],
        )
        events = self.step(session, "catch")
        self.assertEqual([event["name"] for event in events], ["spoiled", "fish_caught"])
        hold = session.snapshot()["hold"]
        self.assertEqual([item["id"] for item in hold], ["I8", "I9", "I10", "I11"])
        self.assertEqual([item["fresh"] for item in hold[1:]], [100, 100, 100])

        session.sim.pos = list(session.sim.t["dock_pos"])
        events = self.step(session, "interact")
        inventory = next(event["data"]["inventory"] for event in events
                         if event["name"] == "gather_end")
        self.assertEqual(inventory, {"items": session.snapshot()["hold"]})
        self.assertAlmostEqual(inventory["items"][1]["fresh"], float(Fraction(100) - Fraction(1, 120)))

    def test_harvest_starts_fresh(self):
        session = self.session(player={"pos": [76, 0]})
        self.step(session, "interact")
        self.assertEqual(session.snapshot()["hold"], [{"id": "I1", "kind": "keo_neo", "fresh": 100}])
