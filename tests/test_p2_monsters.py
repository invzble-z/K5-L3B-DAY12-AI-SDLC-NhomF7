import copy
import json
import tempfile
import unittest
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.scenario import load_scenario
from chonoi.sim.day import DaySim
from chonoi.sim.gather import GatherSim


def idle_input():
    return InputState((0, 0), {}, set())


class MonsterBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.tuning = copy.deepcopy(load_contract()["tuning"])

    def gather(self, scenario=None, day=1):
        if day == 1:
            return GatherSim(self.tuning, scenario or {}, Streams(1), IdAllocator())
        return GatherSim(self.tuning, scenario or {}, Streams(1), IdAllocator(), day=day)

    def test_default_monsters_follow_day_schedule(self):
        day_one = self.gather()
        day_three = self.gather(day=3)

        self.assertEqual([m["id"] for m in day_one.snapshot()["monsters"]], ["M1"])
        self.assertEqual([m["id"] for m in day_three.snapshot()["monsters"]], ["M1", "M2"])
        self.assertEqual(day_one.snapshot()["monsters"][0]["pos"], [60.0, 24.0])
        self.assertEqual(day_three.snapshot()["monsters"][1]["pos"], [85.0, 18.0])
        day_three_sim = DaySim(self.tuning, {"day": {"day": 3}}, Streams(1), IdAllocator())
        self.assertEqual([m["id"] for m in day_three_sim.snapshot()["monsters"]], ["M1", "M2"])

    def test_patrol_moves_at_configured_speed(self):
        sim = self.gather({"player": {"pos": [2, 0]}})

        for _ in range(60):
            sim.step(idle_input())

        monster = sim.snapshot()["monsters"][0]
        self.assertEqual(monster["state"], "patrol")
        self.assertAlmostEqual(monster["pos"][0], 61.0, places=5)
        for _ in range(180):
            sim.step(idle_input())
        self.assertEqual(sim.snapshot()["monsters"][0]["pos"], [64.0, 24.0])
        self.assertEqual(sim.snapshot()["monsters"][0]["waypoint_index"], 0)
        sim.step(idle_input())
        self.assertLess(sim.snapshot()["monsters"][0]["pos"][0], 64.0)

    def test_contact_drops_newest_half_and_starts_recoil(self):
        sim = self.gather({
            "player": {"pos": [60, 24]},
            "hold": ["ca_loc", "ca_keo", "bong_sung", "ca_linh", "bong_sung"],
        })

        events = sim.step(idle_input())
        hit = next(data for name, data in events if name == "monster_hit")

        self.assertEqual(hit["monster_id"], "M1")
        self.assertEqual([item["kind"] for item in hit["lost"]], ["bong_sung", "ca_linh"])
        self.assertEqual(sim.hp, 2)
        self.assertEqual(sim.invuln_ticks, 90)
        self.assertEqual([item.kind for item in sim.hold], ["ca_loc", "ca_keo", "bong_sung"])
        self.assertEqual(sim.snapshot()["monsters"][0]["state"], "recoil")
        self.assertEqual(sim.snapshot()["monsters"][0]["recoil_ticks"], 60)

        old_x = sim.snapshot()["monsters"][0]["pos"][0]
        sim.step(idle_input())
        new_x = sim.snapshot()["monsters"][0]["pos"][0]
        self.assertAlmostEqual(new_x - old_x, 2 / 60, places=5)

    def test_only_nearest_monster_hits_and_ties_use_id_order(self):
        sim = self.gather(
            {
                "player": {"pos": [60, 24]},
                "monsters": [
                    {"id": "M10", "species": "ca_sau", "pos": [60, 24],
                     "waypoints": [[60, 24], [64, 24]]},
                    {"id": "M2", "species": "ca_sau", "pos": [60, 24],
                     "waypoints": [[60, 24], [64, 24]]},
                ],
            },
            day=3,
        )

        events = sim.step(idle_input())
        hits = [data for name, data in events if name == "monster_hit"]

        self.assertEqual([hit["monster_id"] for hit in hits], ["M2"])
        self.assertEqual(sim.snapshot()["monsters"][0]["state"], "recoil")
        self.assertEqual(sim.snapshot()["monsters"][1]["state"], "chase")

    def test_chase_exits_outside_radius_and_below_species_depth(self):
        sim = self.gather({"player": {"pos": [60, 24], "invuln_ticks": 90}})
        sim.step(idle_input())
        self.assertEqual(sim.snapshot()["monsters"][0]["state"], "chase")

        sim.pos = [80, 24]
        sim.step(idle_input())
        self.assertEqual(sim.snapshot()["monsters"][0]["state"], "patrol")

    def test_detects_at_radius_and_chases_at_configured_speed(self):
        sim = self.gather({
            "player": {"pos": [60, 24], "invuln_ticks": 90},
            "monsters": [{
                "id": "M1", "species": "ca_sau", "pos": [70, 24],
                "waypoints": [[70, 24], [74, 24]],
            }],
        })

        sim.step(idle_input())

        monster = sim.snapshot()["monsters"][0]
        self.assertEqual(monster["state"], "chase")
        self.assertAlmostEqual(monster["pos"][0], 69.95, places=5)

        sim.pos = [60, 9.9]
        sim.step(idle_input())
        self.assertEqual(sim.snapshot()["monsters"][0]["state"], "patrol")

    def test_invulnerability_prevents_hits_and_recoil_for_90_ticks(self):
        sim = self.gather({"player": {"pos": [60, 24]}})
        first_events = sim.step(idle_input())
        self.assertEqual(sum(name == "monster_hit" for name, _ in first_events), 1)

        later_events = []
        for _ in range(90):
            later_events.extend(sim.step(idle_input()))

        self.assertFalse(any(name == "monster_hit" for name, _ in later_events))
        self.assertEqual(sim.invuln_ticks, 0)
        self.assertEqual(sim.snapshot()["monsters"][0]["state"], "chase")
        next_events = sim.step(idle_input())
        self.assertEqual(sum(name == "monster_hit" for name, _ in next_events), 1)

    def test_recoil_is_clamped_at_map_boundary(self):
        sim = self.gather({
            "player": {"pos": [1, 10]},
            "monsters": [{
                "id": "M1", "species": "ca_sau", "pos": [0.01, 10],
                "waypoints": [[0.01, 10], [4, 10]],
            }],
        })

        sim.step(idle_input())
        sim.step(idle_input())
        sim.step(idle_input())

        self.assertEqual(sim.snapshot()["monsters"][0]["pos"][0], 0)

    def test_scenario_monsters_are_validated_against_species_depth(self):
        scenario = {
            "gather": {
                "monsters": [{
                    "id": "M9", "species": "ca_sau", "pos": [30, 12],
                    "waypoints": [[30, 12], [34, 12]],
                }],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scenario.json"
            path.write_text(json.dumps(scenario), encoding="utf-8")
            loaded = load_scenario(path, "gather", self.tuning)
            self.assertEqual(loaded["monsters"], scenario["gather"]["monsters"])

            scenario["gather"]["monsters"][0]["pos"][1] = 9
            path.write_text(json.dumps(scenario), encoding="utf-8")
            with self.assertRaises(BadInput):
                load_scenario(path, "gather", self.tuning)

    def test_faint_hands_empty_stock_to_evening_quan(self):
        scenario = {
            "day": {"days": 1},
            "gather": {
                "player": {"pos": [60, 24], "hp": 1},
                "hold": ["ca_loc", "ca_keo", "bong_sung", "ca_linh"],
            },
        }
        sim = DaySim(self.tuning, scenario, Streams(1), IdAllocator())

        events = sim.step(idle_input())

        faint = next(data for name, data, *_ in events if name == "faint")
        gather_end = next(data for name, data, *_ in events if name == "gather_end")
        self.assertEqual(faint["cause"], "monster")
        self.assertEqual(gather_end["inventory"], {"items": []})
        self.assertEqual(sim.phase, "quan")
        self.assertEqual(sim.stock, [])


if __name__ == "__main__":
    unittest.main()
