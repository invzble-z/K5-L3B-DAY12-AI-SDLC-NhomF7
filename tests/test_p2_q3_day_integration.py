"""Behavioral integration checks for Q3 inside the Phase 2 DaySim cycle."""

import copy
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session
try:
    from tests.helpers import read_jsonl, run_headless, write_json
except ImportError:
    from helpers import read_jsonl, run_headless, write_json


def state(buttons=None, pressed=None, buy=None):
    buttons = buttons or {}
    pressed = set(pressed or ())
    return InputState((0, 0), buttons, pressed, buy=buy)


class Q3DayIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tuning = copy.deepcopy(load_contract()["tuning"])

    def one_dish_plan(self, dish="ca_loc_nuong_trui"):
        self.tuning["day_plan"] = {
            "1": {"dishes": {dish: 1}, "ingredients": {"ca_loc": 1}}
        }

    def make_session(self, *, scenario=None, seed=17):
        return Session("day", self.tuning, scenario or {}, seed=seed)

    def test_gather_inventory_is_handed_to_quan_once_and_reserved(self):
        self.one_dish_plan()
        self.tuning["quan"]["first_customer_tick"] = 1
        self.tuning["quan"]["customer_interval_s"] = 1 / self.tuning["tick_hz"]
        session = self.make_session(scenario={
            "gather": {"time_left_ticks": 1, "hold": ["ca_loc"], "nodes": [], "random_fish": False},
            "quan": {"time_left_ticks": 10, "random_customers": True},
        })

        transition = session.step(state())
        self.assertEqual([row["name"] for row in transition],
                         ["day_start", "day_plan", "phase_start", "gather_end", "phase_start"])
        self.assertEqual(session.sim.phase, "quan")
        self.assertEqual([(item["kind"], item["fresh"]) for item in session.sim.stock],
                         [("ca_loc", 99.99166666666666)])
        self.assertEqual(session.sim.quan.stock, {"ca_loc": 1})
        self.assertEqual(session.sim.quan.planned_dishes, frozenset({"ca_loc_nuong_trui"}))

        arrival = session.step(state())
        customers = [c for c in session.snapshot()["customers"]]
        self.assertEqual([row["name"] for row in arrival], ["customer_arrived"])
        self.assertEqual(customers[0]["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(customers[0]["table_id"], "T1")
        self.assertEqual(session.sim.quan.stock, {"ca_loc": 1}, "reservation must not debit physical stock")
        self.assertEqual(session.snapshot()["stock"], [], "snapshot stock is available stock after reservation")

    def test_gather_to_day_order_consumes_recipe_exactly_once(self):
        self.one_dish_plan()
        session = self.make_session(scenario={
            "gather": {"time_left_ticks": 1, "hold": ["ca_loc"], "nodes": [], "random_fish": False},
            "quan": {
                "time_left_ticks": 20,
                "player": {"pos": [2, 8]},
                "random_customers": False,
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
            },
        })
        session.step(state())

        events = session.step(state({"interact": True}, {"interact"}))
        self.assertEqual([row["name"] for row in events], ["cook_started"])
        self.assertEqual(session.sim.quan.stock, {})
        self.assertEqual(session.sim.quan._reservation_state["C1"], "consumed")
        self.assertFalse(session.sim.quan._consume_reservation("C1"))
        self.assertEqual(session.sim.quan.stock, {})

    def test_real_day_customer_schedule_uses_first_tick_and_interval_from_tuning(self):
        self.one_dish_plan()
        session = self.make_session(scenario={
            "gather": {"time_left_ticks": 1, "hold": ["ca_loc", "ca_loc"],
                       "nodes": [], "random_fish": False},
            "quan": {"time_left_ticks": 1100, "random_customers": True},
        })
        session.step(state())
        arrival_ticks = []
        arrivals = []
        for tick in range(1, 1021):
            for row in session.step(state()):
                if row["name"] == "customer_arrived":
                    arrival_ticks.append(tick)
                    arrivals.append(row["data"])
        first = self.tuning["quan"]["first_customer_tick"]
        interval = round(self.tuning["quan"]["customer_interval_s"] * self.tuning["tick_hz"])
        self.assertEqual(arrival_ticks, [first, first + interval])
        self.assertEqual([c["order_tick"] for c in session.snapshot()["customers"]], [first, first + interval])
        self.assertEqual([a["table_id"] for a in arrivals], ["T1", "T2"])
        self.assertEqual(len({a["customer_id"] for a in arrivals}), 2)

    def test_customer_leaving_releases_unconsumed_day_reservation_once(self):
        self.one_dish_plan()
        session = self.make_session(scenario={
            "gather": {"time_left_ticks": 1, "hold": ["ca_loc"], "nodes": [], "random_fish": False},
            "quan": {
                "time_left_ticks": 10,
                "random_customers": False,
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                               "patience_ticks_left": 1}],
            },
        })
        session.step(state())
        self.assertEqual(session.sim.quan.stock, {"ca_loc": 1})
        self.assertEqual(session.snapshot()["stock"], [])

        events = session.step(state())
        self.assertEqual([row["name"] for row in events], ["customer_left"])
        self.assertEqual(session.sim.quan.stock, {"ca_loc": 1})
        self.assertEqual([(item["kind"], item["id"]) for item in session.snapshot()["stock"]],
                         [("ca_loc", "I1")])
        freshness_after_departure = session.snapshot()["stock"][0]["fresh"]
        self.assertLess(freshness_after_departure, 99.99166666666666)
        self.assertIsNone(next(t for t in session.snapshot()["tables"] if t["id"] == "T1")["customer_id"])
        for _ in range(9):
            session.step(state())
        self.assertEqual(session.sim.phase, "shop")
        self.assertEqual([(item["kind"], item["id"]) for item in session.snapshot()["stock"]],
                         [("ca_loc", "I1")])
        self.assertLess(session.snapshot()["stock"][0]["fresh"], freshness_after_departure)

    def test_day_plan_payload_and_filter_do_not_mutate_contract_tuning(self):
        self.tuning["day_plan"] = {
            "1": {"dishes": {"ca_loc_nuong_trui": 2, "goi_bong_sung": 3},
                  "ingredients": {"ca_loc": 2, "bong_sung": 6}}
        }
        original_plan = copy.deepcopy(self.tuning["day_plan"])
        session = self.make_session(scenario={
            "gather": {"time_left_ticks": 1, "hold": ["ca_loc"] * 2 + ["bong_sung"] * 6,
                       "nodes": [], "random_fish": False},
            "quan": {"time_left_ticks": 10, "random_customers": False},
        })
        day_start = session.step(state())
        self.assertEqual([row["name"] for row in day_start], ["day_start", "day_plan", "phase_start", "gather_end", "phase_start"])
        self.assertEqual(day_start[1]["data"]["dishes"], original_plan["1"]["dishes"])
        self.assertEqual(session.sim.quan.planned_dishes,
                         frozenset({"ca_loc_nuong_trui", "goi_bong_sung"}))
        self.assertEqual(self.tuning["day_plan"], original_plan)

    def test_empty_day_plan_is_an_empty_quan_filter(self):
        self.tuning["day_plan"] = {"1": {"dishes": {}, "ingredients": {}}}
        session = self.make_session(scenario={
            "gather": {"time_left_ticks": 1, "hold": ["ca_loc"] * 3 + ["bong_sung"] * 6,
                       "nodes": [], "random_fish": False},
            "quan": {"time_left_ticks": 200, "random_customers": True},
        })
        session.step(state())
        self.assertEqual(session.sim.quan.planned_dishes, frozenset())

    def test_empty_day_plan_does_not_spawn_customer_for_unplanned_dish(self):
        self.tuning["day_plan"] = {"1": {"dishes": {}, "ingredients": {}}}
        self.tuning["quan"]["first_customer_tick"] = 1
        self.tuning["quan"]["customer_interval_s"] = 1 / self.tuning["tick_hz"]
        session = self.make_session(scenario={
            "gather": {"time_left_ticks": 1, "hold": ["ca_loc"] * 3 + ["bong_sung"] * 6,
                       "nodes": [], "random_fish": False},
            "quan": {"time_left_ticks": 20, "random_customers": True},
        })
        session.step(state())
        arrivals = session.step(state())
        self.assertFalse(any(row["name"] == "customer_arrived" for row in arrivals))

    def test_day_to_day_rebuild_resets_customer_clock_tables_and_shift_state(self):
        self.one_dish_plan()
        session = self.make_session(scenario={
            "day": {"days": 2},
            "gather": {"time_left_ticks": 1, "hold": ["ca_loc"], "nodes": [], "random_fish": False},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        })
        session.step(state())
        session.step(state())
        shop_rows = session.step(state({"shop_done": True}, {"shop_done"}))
        self.assertEqual([r["name"] for r in shop_rows],
                         ["shop_end", "day_start", "day_plan", "phase_start"])
        self.assertEqual(session.sim.days_completed, 1)
        self.assertEqual(session.sim.day, 2)
        self.assertEqual(session.sim.phase, "gather")

        session.step(state())
        self.assertEqual(session.sim.phase, "quan")
        self.assertEqual(session.sim.phase_tick, 0)
        self.assertEqual(session.sim.quan.elapsed_ticks, 0)
        self.assertEqual(session.sim.quan.customers, [])
        self.assertEqual(session.sim.quan._available_stock(), {"ca_loc": 1})

    def test_manifest_mapping_and_list_plans_are_read_without_mutation(self):
        original = copy.deepcopy(self.tuning["day_plan"])
        for day in range(1, 6):
            session = self.make_session(scenario={
                "day": {"day": day},
                "gather": {"time_left_ticks": 1, "nodes": [], "random_fish": False},
                "quan": {"random_customers": False},
            })
            plan = self.tuning["day_plan"][str(day)]
            self.assertEqual(session.snapshot()["day_plan"]["dishes"], plan["dishes"])
            session.step(state())
            self.assertEqual(session.sim.quan.planned_dishes, frozenset(plan["dishes"]))
        self.assertEqual(self.tuning["day_plan"], original)

        self.tuning["day_plan"] = [
            {"day": 1, "dishes": {"goi_bong_sung": 2}, "ingredients": {"bong_sung": 4}},
            {"day": 2, "dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {"ca_loc": 1}},
        ]
        list_tuning_before = copy.deepcopy(self.tuning["day_plan"])
        session = self.make_session(scenario={"day": {"day": 2}})
        self.assertEqual(session.snapshot()["day_plan"]["dishes"], {"ca_loc_nuong_trui": 1})
        self.assertEqual(self.tuning["day_plan"], list_tuning_before)

    def test_day_level_reputation_is_passed_into_first_quan_shift(self):
        session = self.make_session(scenario={
            "reputation": 4.25,
            "gather": {"time_left_ticks": 1, "nodes": [], "random_fish": False},
            "quan": {"time_left_ticks": 5, "random_customers": False},
        })
        session.step(state())
        self.assertEqual(session.sim.quan.reputation, 4.25)

    def test_day_payment_updates_cumulative_money_and_earned_once(self):
        session = self.make_session(scenario={
            "day": {"days": 1, "money": 10},
            "gather": {"time_left_ticks": 1, "nodes": [], "random_fish": False},
            "quan": {
                "time_left_ticks": 1,
                "random_customers": False,
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                               "state": "eating", "eat_ticks_left": 1}],
            },
        })
        session.step(state())
        paid = session.step(state())
        self.assertEqual([(r["data"]["price"], r["data"]["tip"])
                          for r in paid if r["name"] == "paid"], [(60, 12)])
        self.assertEqual(session.sim.money, 82)
        self.assertEqual(session.sim.earned, 72)
        session.step(state({"shop_done": True}, {"shop_done"}))
        self.assertEqual(session.sim.money, 82)
        self.assertEqual(session.sim.earned, 72)

    def test_reputation_earned_in_quan_survives_into_next_day(self):
        session = self.make_session(scenario={
            "day": {"days": 2},
            "gather": {"time_left_ticks": 1, "nodes": [], "random_fish": False},
            "quan": {
                "time_left_ticks": 1,
                "random_customers": False,
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                               "state": "eating", "eat_ticks_left": 1}],
            },
        })
        session.step(state())
        session.step(state())
        self.assertAlmostEqual(session.sim.reputation, 3.2)
        session.step(state({"shop_done": True}, {"shop_done"}))
        session.step(state())
        self.assertEqual(session.sim.phase, "quan")
        self.assertAlmostEqual(session.sim.quan.reputation, 3.2)

    def test_sim_tick_stays_still_while_paused(self):
        session = self.make_session(scenario={
            "gather": {"time_left_ticks": 10, "nodes": [], "random_fish": False}
        })
        pause_events = session.step(state({"pause": True}, {"pause"}))
        self.assertEqual([r["name"] for r in pause_events],
                         ["day_start", "day_plan", "phase_start", "paused"])
        phase_tick = session.sim.phase_tick
        time_left = session.sim.time_left_ticks
        paused_sim_tick = session.snapshot()["sim_tick"]
        self.assertEqual(session.step(state()), [])
        self.assertEqual(session.tick, 2)
        self.assertEqual(session.sim.phase_tick, phase_tick)
        self.assertEqual(session.sim.time_left_ticks, time_left)
        self.assertEqual(session.snapshot()["sim_tick"], paused_sim_tick)


class Q3DayHeadlessIntegrationTests(unittest.TestCase):
    def run_day(self, root, days, presses):
        scenario = {
            "day": {"days": days},
            "gather": {"time_left_ticks": 1, "nodes": [], "random_fish": False},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        frames = []
        for tick in presses:
            frames.extend(({"tick": tick, "shop_done": True},
                           {"tick": tick + 1, "shop_done": False}))
        sc_path = os.path.join(root, "scenario.json")
        input_path = os.path.join(root, "inputs.json")
        out_path = os.path.join(root, "day.jsonl")
        write_json(sc_path, scenario)
        write_json(input_path, {"frames": frames})
        code, stderr = run_headless("--mode", "day", "--days", str(days), "--seed", "17",
                                    "--ticks", "20", "--snapshot-every", "1",
                                    "--scenario", sc_path, "--inputs", input_path, "--out", out_path)
        self.assertEqual(code, 0, stderr)
        rows = read_jsonl(out_path)
        return rows, out_path

    def test_headless_day_one_reaches_end(self):
        with tempfile.TemporaryDirectory() as root:
            rows, _ = self.run_day(root, 1, [2])
        events = [row["name"] for row in rows if row["type"] == "event"]
        self.assertEqual(events, ["day_start", "day_plan", "phase_start", "gather_end",
                                  "phase_start", "quan_end", "phase_start", "shop_end"])
        self.assertEqual(rows[-1]["reason"], "days_complete")
        self.assertEqual(rows[-1]["days_completed"], 1)

    def test_headless_day_three_replay_is_deterministic(self):
        with tempfile.TemporaryDirectory() as root:
            first, first_path = self.run_day(root, 3, [2, 5, 8])
            with open(first_path, "rb") as f:
                first_bytes = f.read()
            second, second_path = self.run_day(root, 3, [2, 5, 8])
            with open(second_path, "rb") as f:
                second_bytes = f.read()
        self.assertEqual(first_bytes, second_bytes)
        day_starts = [r for r in first if r["type"] == "event" and r["name"] == "day_start"]
        self.assertEqual([r["day"] for r in day_starts], [1, 2, 3])
        self.assertEqual(first[-1]["reason"], "days_complete")
        self.assertEqual(first[-1]["days_completed"], 3)


if __name__ == "__main__":
    unittest.main()
