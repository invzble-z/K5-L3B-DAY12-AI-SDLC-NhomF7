import json
import math
import unittest
from pathlib import Path

from chonoi.inputs import InputState
from chonoi.runner import Session


class FishMotionTest(unittest.TestCase):
    def session(self, seed=1, **scenario):
        path = Path(__file__).resolve().parents[1] / "game.contract.json"
        tuning = json.loads(path.read_text(encoding="utf-8"))["tuning"]
        tuning["gather"]["fish_yield"]["ca_keo"] = 2
        tuning["gather"]["nodes"].extend([
            {"id": "N5", "kind": "keo_neo", "pos": [76, 0]},
            {"id": "N6", "kind": "keo_neo", "pos": [90, 0]},
        ])
        tuning["gather"].update(
            fish_motion={"speed": 3, "turn_every_ticks": 3,
                         "max_turn_deg": 25, "min_depth": 1},
            fish_initial=[{"id": "F10", "kind": "ca_loc", "pos": [100, 5],
                           "heading_deg": 0}],
            fish_spawn_schedule=[
                {"tick": 2, "kind": "ca_linh", "pos": [20, 8], "heading_deg": 0},
                {"tick": 2, "kind": "ca_loc", "pos": [40, 16], "heading_deg": 180},
            ],
        )
        return Session("gather", tuning, scenario, seed)

    def advance(self, session):
        session.step(InputState((0, 0), {}, set()))
        return session.snapshot()["fish"]

    def ticket_session(self, **scenario):
        path = Path(__file__).resolve().parents[1] / "game.contract.json"
        tuning = json.loads(path.read_text(encoding="utf-8"))["tuning"]
        gather = tuning["gather"]
        gather.pop("fish_motion")
        gather.update(
            fish_initial=8, fish_speed=1.5, fish_turn_ticks=120, fish_max=12,
            fish_spawn_ticks=360, fish_spawn_clearance=1,
            fish_x=[10, 20, 30, 40, 50, 60, 70, 80], fish_depths=[5],
            fish_spawn_x=[20, 40, 60, 80], fish_spawn_depths=[25],
            fish_weights={"ca_linh": 40, "ca_loc": 30, "ca_keo": 30},
        )
        return Session("gather", tuning, scenario, seed=1)

    def test_ticket_schedule_emits_spawn_events_and_caps_population(self):
        session = self.ticket_session()
        initial = session.snapshot()["fish"]
        self.assertEqual(len(initial), 8)
        self.assertEqual([fish["age_ticks"] for fish in initial], [0] * 8)
        spawns = []
        for _ in range(360 * 5):
            events = session.step(InputState((0, 0), {}, set()))
            spawns.extend(event for event in events if event["name"] == "fish_spawned")
            for event in events:
                if event["name"] == "fish_spawned":
                    fish = session.snapshot()["fish"]
                    spawned = fish[-1]
                    self.assertEqual(spawned["age_ticks"], 0)
                    self.assertEqual(event["data"], {key: spawned[key] for key in ("id", "kind", "pos")})
                    self.assertTrue(all(math.dist(spawned["pos"], school["pos"]) > 1
                                        for school in fish[:-1]))
        self.assertEqual([event["tick"] for event in spawns], [360, 720, 1080, 1440])
        self.assertEqual([event["data"]["id"] for event in spawns], ["F9", "F10", "F11", "F12"])
        self.assertEqual(len(session.snapshot()["fish"]), 12)

    def test_ticket_random_fish_false_preserves_static_fixture(self):
        session = self.ticket_session(random_fish=False, fish=[
            {"id": "F20", "kind": "ca_keo", "pos": [25, 10]},
        ])
        for _ in range(360):
            fish = self.advance(session)
        self.assertEqual([(school["id"], school["pos"]) for school in fish], [("F20", [25, 10])])

    def test_default_contract_fish_swim_at_configured_speed(self):
        path = Path(__file__).resolve().parents[1] / "game.contract.json"
        tuning = json.loads(path.read_text(encoding="utf-8"))["tuning"]
        motion = tuning["gather"]["fish_motion"]
        self.assertEqual(motion["speed"], 1.5)

        session = Session("gather", tuning, {"random_fish": True}, seed=1)
        initial = {fish["id"]: fish["pos"][0] for fish in session.snapshot()["fish"]}
        for _ in range(60):
            session.step(InputState((0, 0), {}, set()))
        moved = {fish["id"]: fish["pos"][0] for fish in session.snapshot()["fish"]}

        for fish_id, initial_x in initial.items():
            self.assertAlmostEqual(moved[fish_id], initial_x + motion["speed"], places=5)

    def test_boundary_and_spawn_ticks(self):
        session = self.session()
        fish = self.advance(session)
        self.assertEqual([school["id"] for school in fish], ["F10"])
        self.assertEqual(fish[0]["pos"], [100, 5])
        self.assertEqual(fish[0]["heading_deg"], 180)

        fish = self.advance(session)
        self.assertEqual([school["id"] for school in fish], ["F10", "F11", "F12"])
        self.assertLess(fish[0]["pos"][0], 100)
        self.assertEqual(fish[1]["pos"], [20, 8])
        self.assertEqual(len(self.advance(session)), 3)

    def test_turns_are_repeatable_and_seeded(self):
        first, repeat, other = self.session(), self.session(), self.session(seed=2)
        for _ in range(2):
            self.assertEqual(self.advance(first), self.advance(repeat))
            self.advance(other)
        turned = self.advance(first)
        self.assertEqual(turned, self.advance(repeat))
        self.assertNotEqual(turned, self.advance(other))
        self.assertNotEqual(turned[0]["heading_deg"], 180)

    def test_scenario_overrides_suppress_scheduled_spawns(self):
        for scenario in ({"fish": []}, {"random_fish": False}):
            with self.subTest(scenario=scenario):
                session = self.session(**scenario)
                self.advance(session)
                self.assertEqual(self.advance(session), [])

    def test_new_ingredients_enter_inventory_with_updated_tuning(self):
        fishing = self.session(
            player={"pos": [25, 10]},
            fish=[{"id": "F1", "kind": "ca_keo", "pos": [25, 10]}],
        )
        fishing.step(InputState((0, 0), {}, {"catch"}))
        self.assertEqual(fishing.sim.inventory_items(), {"ca_keo": 2})

        for node_x in (76, 90):
            with self.subTest(node_x=node_x):
                harvesting = self.session(player={"pos": [node_x, 0]})
                harvesting.step(InputState((0, 0), {}, {"interact"}))
                self.assertEqual(harvesting.sim.inventory_items(), {"keo_neo": 1})
