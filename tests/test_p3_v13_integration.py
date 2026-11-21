"""End-to-end checks for root contract v1.3 using the v1.2 physical-item schema."""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputState
from chonoi.inventory import read_inventory
from chonoi.runner import Session
from chonoi.scenario import load_scenario
from tests.helpers import Workdir, events, frames, read_jsonl, run_headless, write_json


class ContractV13InventoryTests(unittest.TestCase):
    def test_root_version_is_propagated_and_gather_to_file_to_quan_keeps_id_fresh(self):
        contract = load_contract()
        self.assertEqual(contract["contract_version"], "1.3")
        self.assertEqual(contract["tuning"]["contract_version"], "1.3")
        with Workdir() as work:
            gather_scenario = write_json(work.path("gather.json"), {
                "gather": {
                    "player": {"pos": [2, 0]},
                    "hold": [{"id": "I9", "kind": "ca_loc", "fresh": 99}],
                    "nodes": [], "random_fish": False,
                }
            })
            gather_inputs = write_json(work.path("gather-inputs.json"), frames({"tick": 0, "interact": True}))
            inventory_path = work.path("inventory.json")
            code, error = run_headless("--mode", "gather", "--seed", "9", "--ticks", "1",
                                       "--scenario", gather_scenario, "--inputs", gather_inputs,
                                       "--inventory-out", inventory_path, "--out", work.path("gather.jsonl"))
            self.assertEqual(code, 0, error)
            inventory = read_inventory(inventory_path)
            self.assertEqual([(item.id, item.kind) for item in inventory], [("I9", "ca_loc")])
            self.assertLess(inventory[0].fresh, 99)

            quan_scenario = write_json(work.path("quan.json"), {"quan": {
                "player": {"pos": [2, 8]}, "random_customers": False,
                "time_left_ticks": 10,
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
            }})
            quan_inputs = write_json(work.path("quan-inputs.json"), frames({"tick": 0, "interact": True}))
            quan_out = work.path("quan.jsonl")
            code, error = run_headless("--mode", "quan", "--seed", "9", "--ticks", "1",
                                       "--scenario", quan_scenario, "--inputs", quan_inputs,
                                       "--inventory", inventory_path, "--out", quan_out)
            self.assertEqual(code, 0, error)
            rows = read_jsonl(quan_out)
            cook = events(rows, "cook_started")
            self.assertEqual(cook[0]["data"]["items"][0]["id"], "I9")
            self.assertLess(cook[0]["data"]["items"][0]["fresh"], float(inventory[0].fresh))

    def test_v13_rejects_count_files_and_count_scenario_stock(self):
        contract = load_contract()
        with Workdir() as work:
            count_inventory = write_json(work.path("counts.json"), {"items": {"ca_loc": 1}})
            with self.assertRaises(BadInput):
                read_inventory(count_inventory)
            out = work.path("invalid.jsonl")
            code, error = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                       "--inventory", count_inventory, "--out", out)
            self.assertEqual(code, 2, error)
            self.assertFalse(__import__("os").path.exists(out))
            count_scenario = write_json(work.path("count-scenario.json"), {
                "quan": {"stock": {"ca_loc": 1}, "random_customers": False}
            })
            with self.assertRaises(BadInput):
                load_scenario(count_scenario, "quan", contract["tuning"])

    def test_v13_scenario_checks_unique_reservation_ids_and_accepts_null_hand(self):
        tuning = load_contract()["tuning"]
        with Workdir() as work:
            valid = write_json(work.path("valid.json"), {"quan": {
                "hand": None,
                "stock": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 100},
                    {"id": "I2", "kind": "ca_loc", "fresh": 90},
                ],
                "random_customers": False,
                "customers": [
                    {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
                    {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I2"]},
                ],
            }})
            loaded = load_scenario(valid, "quan", tuning)
            self.assertIsNone(loaded["hand"])
            duplicate = write_json(work.path("duplicate.json"), {"quan": {
                "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                "random_customers": False,
                "customers": [
                    {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
                    {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
                ],
            }})
            with self.assertRaises(BadInput):
                load_scenario(duplicate, "quan", tuning)

    def test_day_pause_freezes_physical_freshness_and_ticks(self):
        tuning = load_contract()["tuning"]
        session = Session("day", tuning, {
            "day": {"days": 1},
            "stock": [{"id": "I4", "kind": "ca_loc", "fresh": 80}],
            "gather": {"time_left_ticks": 10, "random_fish": False},
            "quan": {"random_customers": False},
        }, seed=4)
        start_fresh = float(session.sim.gather.hold[0].fresh)
        pause = InputState((0, 0), {"pause": True}, {"pause"})
        session.step(pause)
        paused_sim_tick = session.snapshot()["sim_tick"]
        session.step(InputState((0, 0), {}, set()))
        self.assertEqual(session.snapshot()["sim_tick"], paused_sim_tick)
        self.assertEqual(float(session.sim.gather.hold[0].fresh), start_fresh)
        self.assertEqual(session.tick, 2)
        session.step(pause)
        self.assertLess(float(session.sim.gather.hold[0].fresh), start_fresh)


if __name__ == "__main__":
    unittest.main()
