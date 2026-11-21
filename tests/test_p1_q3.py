"""Q3 Phase 1 outcome tests.

Oracles marked PROPOSED here follow the feature's Q3↔Q4 proposal; they are not
official PRD acceptance claims until D-01..D-09 are resolved from the source.
"""

import contextlib
import copy
import io
import json
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.headless import main as headless_main
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.scenario import load_scenario


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "tests", "fixtures", "p1", "q3")


def _contract():
    return load_contract()


def _fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


def _step(session, count=1):
    player = InputPlayer([])
    rows = []
    for _ in range(count):
        rows.extend(session.step(player.advance(session.tick)))
    return rows


class Q3HydrationTests(unittest.TestCase):
    def test_tc_q3_001_tick_zero_hydrates_customer_and_table_mapping(self):
        """A valid fixture is normalized before the first snapshot."""
        contract = _contract()
        scenario = load_scenario(
            os.path.join(FIXTURES, "waiting-expiry.json"), "quan", contract["tuning"]
        )
        session = Session("quan", contract["tuning"], scenario, seed=7)

        snapshot = session.snapshot()
        self.assertEqual(session.tick, 0)
        self.assertEqual(snapshot["customers"][0]["id"], "C2")
        self.assertEqual(snapshot["customers"][0]["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(snapshot["customers"][0]["patience_ticks_left"], 2)
        self.assertEqual(snapshot["customers"][0]["reserved"], ["I1"])
        self.assertEqual(snapshot["tables"][0]["customer_id"], "C2")
        self.assertNotIn("ca_loc", session.sim._available_stock())

    def test_tc_q3_002_existing_customer_ids_are_reserved_before_allocation(self):
        """Numeric ID ordering and allocator state include loaded customers."""
        contract = _contract()
        tuning = copy.deepcopy(contract["tuning"])
        tuning["quan"]["tables"].append({"id": "T2", "pos": [12, 2]})
        scenario = {
            "customers": [
                {"id": "C10", "table_id": "T2", "dish_id": "ca_loc_nuong_trui",
                 "state": "waiting", "patience_ticks_left": 5, "reserved": {}},
                {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                 "state": "waiting", "patience_ticks_left": 5, "reserved": {}},
            ],
            "stock": {"ca_loc": 2},
            "random_customers": False,
        }
        session = Session("quan", tuning, scenario, seed=3)

        self.assertEqual([c["id"] for c in session.snapshot()["customers"]], ["C2", "C10"])
        self.assertEqual(session.sim.ids.new("C"), "C11")

    def test_tc_q3_003_sessions_do_not_mutate_reused_scenario_or_menu(self):
        """Nested reservation data is session-owned; restart can reuse input objects."""
        contract = _contract()
        tuning = contract["tuning"]
        original_reserved = {"ca_loc": 1}
        scenario = {
            "stock": {"ca_loc": 1},
            "customers": [{"id": "C4", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                           "state": "waiting", "patience_ticks_left": 1,
                           "reserved": original_reserved}],
        }
        recipe_before = copy.deepcopy(tuning["menu"]["ca_loc_nuong_trui"]["recipe"])

        first = Session("quan", tuning, scenario, seed=12)
        first.sim._release_reservation("C4")
        second = Session("quan", tuning, scenario, seed=12)

        self.assertEqual(scenario["customers"][0]["reserved"], {"ca_loc": 1})
        self.assertEqual(tuning["menu"]["ca_loc_nuong_trui"]["recipe"], recipe_before)
        self.assertIsNot(first.sim.customers[0]["reserved"], original_reserved)
        self.assertEqual(second.sim._available_stock(), {})

    def test_tc_q3_001_missing_reserved_is_inferred_as_a_copy_of_menu_recipe(self):
        contract = _contract()
        tuning = contract["tuning"]
        scenario = {
            "stock": {"ca_loc": 1},
            "customers": [{"id": "C3", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                           "state": "waiting", "patience_ticks_left": 8}],
        }

        session = Session("quan", tuning, scenario, seed=4)

        self.assertEqual(session.snapshot()["customers"][0]["reserved"], {"ca_loc": 1})
        self.assertNotIn("reserved", scenario["customers"][0])
        self.assertEqual(tuning["menu"]["ca_loc_nuong_trui"]["recipe"], {"ca_loc": 1})

    def test_tc_q3_004_ordered_customer_without_reserved_does_not_reserve_again(self):
        """[PROPOSED] Local ordered state means ingredients were consumed before hydration."""
        contract = _contract()
        scenario = {
            "stock": {"ca_loc": 1},
            "customers": [{"id": "C5", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                           "state": "ordered", "patience_ticks_left": 8}],
        }

        session = Session("quan", contract["tuning"], scenario, seed=6)

        self.assertEqual(session.sim.customers[0]["reserved"], {})
        self.assertEqual(session.sim._reservation_state["C5"], "consumed")
        self.assertEqual(session.sim._available_stock(), {"ca_loc": 1})
        self.assertEqual(session.sim.stock, {"ca_loc": 1})

    def test_tc_q3_004_q4_handoff_fixtures_hydrate_coherently(self):
        """[PROPOSED] Local waiting/cooking/eating fixture states hydrate coherently."""
        contract = _contract()

        waiting_scenario = load_scenario(
            os.path.join(FIXTURES, "reserved-before-cook.json"), "quan", contract["tuning"]
        )
        waiting = Session("quan", contract["tuning"], waiting_scenario, seed=6).sim
        self.assertEqual(waiting.customers[0]["reserved"], ["I1"])
        self.assertEqual(waiting._reservation_state["C2"], "reserved")
        self.assertNotIn("ca_loc", waiting._available_stock())

        ordered_scenario = load_scenario(
            os.path.join(FIXTURES, "ordered-during-cook.json"), "quan", contract["tuning"]
        )
        ordered = Session("quan", contract["tuning"], ordered_scenario, seed=6).sim
        self.assertEqual(ordered.customers[0]["state"], "ordered")
        self.assertEqual(ordered.customers[0]["reserved"], {})
        self.assertEqual(ordered._reservation_state["C2"], "consumed")
        self.assertEqual(ordered.stoves[0]["state"], "cooking")
        self.assertEqual(ordered._available_stock(), {"ca_loc": 1})

        eating_scenario = load_scenario(
            os.path.join(FIXTURES, "eating-before-paid.json"), "quan", contract["tuning"]
        )
        eating = Session("quan", contract["tuning"], eating_scenario, seed=6).sim
        self.assertEqual(eating.customers[0]["state"], "eating")
        self.assertEqual(eating.customers[0]["reserved"], {})
        self.assertEqual(eating.customers[0]["eat_ticks_left"], 12)
        self.assertEqual(eating._reservation_state["C2"], "consumed")
        self.assertTrue(eating._has_active_work())

    def test_tc_q3_020_invalid_overreservation_is_rejected_before_output(self):
        """The headless entry point returns the input error code without a partial JSONL."""
        contract = _contract()
        with self.assertRaises(BadInput):
            load_scenario(os.path.join(FIXTURES, "invalid-overreserved.json"), "quan", contract["tuning"])
        with tempfile.TemporaryDirectory() as temp_dir:
            out = os.path.join(temp_dir, "invalid.jsonl")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = headless_main([
                    "--mode", "quan", "--seed", "1", "--ticks", "0", "--out", out,
                    "--scenario", os.path.join(FIXTURES, "invalid-overreserved.json"),
                ])
            self.assertEqual(code, 2, stderr.getvalue())
            self.assertFalse(os.path.exists(out))

    def test_tc_q3_021_partial_recipe_reservation_is_rejected_before_output(self):
        """A valid but incomplete reservation fails during hydration before JSONL creation."""
        scenario_path = os.path.join(FIXTURES, "invalid-partial-recipe.json")
        contract = _contract()
        with self.assertRaises(BadInput):
            load_scenario(scenario_path, "quan", contract["tuning"])

        with tempfile.TemporaryDirectory() as temp_dir:
            out = os.path.join(temp_dir, "invalid.jsonl")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = headless_main([
                    "--mode", "quan", "--seed", "1", "--ticks", "0", "--out", out,
                    "--scenario", scenario_path,
                ])
            self.assertEqual(code, 2, stderr.getvalue())
            self.assertFalse(os.path.exists(out))

    def test_tc_q3_021_invalid_random_customers_type_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            scenario_path = os.path.join(temp_dir, "bad-random-customers.json")
            out = os.path.join(temp_dir, "invalid.jsonl")
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump({"quan": {"random_customers": "false"}}, f)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = headless_main([
                    "--mode", "quan", "--seed", "1", "--ticks", "0", "--out", out,
                    "--scenario", scenario_path,
                ])
            self.assertEqual(code, 2, stderr.getvalue())
            self.assertFalse(os.path.exists(out))


class Q3ArrivalTests(unittest.TestCase):
    def test_tc_q3_005_first_due_arrival_uses_elapsed_simulation_tick(self):
        """[PROPOSED] Arrival at first_customer_tick is emitted on that step."""
        contract = _contract()
        tuning = copy.deepcopy(contract["tuning"])
        tuning["quan"]["first_customer_tick"] = 2
        tuning["quan"]["customer_interval_s"] = 1 / 60
        scenario = {"stock": {"ca_loc": 1}, "random_customers": True, "time_left_ticks": 3}
        session = Session("quan", tuning, scenario, seed=7)

        before = _step(session)
        self.assertEqual(session.tick, 1)
        self.assertEqual(session.sim.elapsed_ticks, 1)
        self.assertEqual(session.sim.customers, [])
        self.assertEqual(before, [])

        due = _step(session)
        self.assertEqual(session.tick, 2)
        self.assertEqual(session.sim.elapsed_ticks, 2)
        self.assertEqual(len(session.sim.customers), 1)
        self.assertEqual(session.sim.customers[0]["table_id"], "T1")
        self.assertIn(session.sim.customers[0]["dish_id"], tuning["menu"])
        self.assertTrue(any(name == "customer_arrived" for name, _data in
                            ((row["name"], row["data"]) for row in due)))

    def test_tc_q3_007_disabling_arrivals_does_not_disable_fixture_patience(self):
        contract = _contract()
        tuning = copy.deepcopy(contract["tuning"])
        tuning["quan"]["first_customer_tick"] = 1
        scenario = _fixture("waiting-expiry.json")["quan"]
        scenario["random_customers"] = False
        session = Session("quan", tuning, scenario, seed=1)

        rows = _step(session)

        self.assertEqual(len(session.sim.customers), 1)
        self.assertEqual(session.sim.customers[0]["patience_ticks_left"], 1)
        self.assertFalse(any(row["name"] == "customer_arrived" for row in rows))

    def test_tc_q3_006_second_arrival_obeys_interval_across_two_tuned_tables(self):
        """[PROPOSED] Scheduled arrivals use the configured interval and next free table."""
        contract = _contract()
        tuning = copy.deepcopy(contract["tuning"])
        tuning["quan"]["tables"].append({"id": "T2", "pos": [12, 2]})
        tuning["quan"]["first_customer_tick"] = 1
        tuning["quan"]["customer_interval_s"] = 2 / tuning["tick_hz"]
        session = Session("quan", tuning, {"stock": {"ca_loc": 2}}, seed=10)

        _step(session)
        self.assertEqual([c["table_id"] for c in session.sim.customers], ["T1"])
        _step(session)
        self.assertEqual(len(session.sim.customers), 1)
        _step(session)

        self.assertEqual([c["table_id"] for c in session.sim.customers], ["T1", "T2"])
        self.assertEqual([c["id"] for c in session.sim.customers], ["C1", "C2"])
        self.assertEqual(session.sim._available_stock(), {})

    def test_tc_q3_005_new_customer_keeps_full_patience_on_arrival_tick(self):
        """[PROPOSED] A customer spawned after countdown starts at its full configured patience."""
        contract = _contract()
        tuning = copy.deepcopy(contract["tuning"])
        tuning["quan"]["first_customer_tick"] = 1
        tuning["quan"]["customer_interval_s"] = 1 / tuning["tick_hz"]
        tuning["quan"]["patience_s"] = 5 / tuning["tick_hz"]
        session = Session("quan", tuning, {"stock": {"ca_loc": 1}}, seed=10)

        _step(session)

        self.assertEqual(session.sim.customers[0]["patience_ticks_left"], 5)

    def test_tc_q3_017_expiry_before_serve_interaction_is_provisional(self):
        """[PROPOSED] Current step order expires waiting customers before serve interaction."""
        contract = _contract()
        scenario = {
            "player": {"pos": [9, 2]},
            "stock": {},
            "hand": "ca_loc_nuong_trui",
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                           "state": "ordered", "patience_ticks_left": 1, "reserved": {}}],
        }
        session = Session("quan", contract["tuning"], scenario, seed=1)
        inp = InputPlayer([{"tick": 0, "interact": True}]).advance(0)

        rows = session.step(inp)

        names = [row["name"] for row in rows]
        self.assertEqual(names.count("customer_left"), 1)
        self.assertEqual(names.count("served"), 0)
        self.assertEqual(session.sim.hand, "ca_loc_nuong_trui")

    def test_tc_q3_019_expiry_on_last_time_tick_emits_left_and_end_once(self):
        """[PROPOSED] Final-tick timeout and patience expiry each notify once on that tick."""
        contract = _contract()
        scenario = _fixture("waiting-expiry.json")["quan"]
        scenario["time_left_ticks"] = 1
        scenario["customers"][0]["patience_ticks_left"] = 1
        session = Session("quan", contract["tuning"], scenario, seed=1)

        rows = _step(session)

        self.assertEqual([row["name"] for row in rows].count("customer_left"), 1)
        self.assertEqual([row["name"] for row in rows].count("quan_end"), 1)
        self.assertEqual({row["tick"] for row in rows}, {1})
        self.assertTrue(session.done)

    def test_tc_q3_008_spawn_requires_the_full_recipe_in_available_stock(self):
        """A partial multi-ingredient recipe cannot be selected or reserved."""
        contract = _contract()
        tuning = copy.deepcopy(contract["tuning"])
        tuning["quan"]["first_customer_tick"] = 1
        tuning["quan"]["customer_interval_s"] = 1 / 60
        scenario = {
            "stock": {"ca_linh": 3},
            "random_customers": True,
        }
        session = Session("quan", tuning, scenario, seed=2)

        _step(session)

        self.assertEqual(len(session.sim.customers), 0)
        self.assertEqual(session.sim._available_stock(), {"ca_linh": 3})

    def test_tc_q3_009_consuming_an_unrelated_rng_stream_does_not_change_customer(self):
        """Named Streams keep unrelated random draws from shifting Q3 selection."""
        contract = _contract()
        tuning = copy.deepcopy(contract["tuning"])
        tuning["quan"]["first_customer_tick"] = 1
        tuning["quan"]["customer_interval_s"] = 1 / 60
        scenario = {"stock": {"ca_loc": 1, "bong_sung": 2}, "random_customers": True}

        def arrive(consume_other):
            streams = Streams(99)
            if consume_other:
                for _ in range(25):
                    streams.get("unrelated_test_stream").random()
            session = Session("quan", tuning, scenario, seed=99)
            session.sim.rng = streams
            _step(session)
            return session.snapshot()

        self.assertEqual(arrive(False), arrive(True))

    def test_tc_q3_010_same_seed_and_inputs_replay_the_same_session_rows(self):
        contract = _contract()
        tuning = copy.deepcopy(contract["tuning"])
        tuning["quan"]["first_customer_tick"] = 1
        tuning["quan"]["customer_interval_s"] = 1 / 60
        scenario = {"stock": {"ca_loc": 1, "bong_sung": 2}, "random_customers": True}

        def replay():
            session = Session("quan", tuning, scenario, seed=31)
            rows = [session.snapshot()]
            rows.extend(_step(session, 3))
            rows.append(session.snapshot())
            return json.dumps(rows, sort_keys=True, separators=(",", ":"))

        self.assertEqual(replay(), replay())


class Q3ReservationTests(unittest.TestCase):
    def test_tc_q3_011_reservation_is_atomic_and_competes_for_one_recipe(self):
        """[PROPOSED] One dish's whole recipe is reserved or none of it is."""
        contract = _contract()
        tuning = copy.deepcopy(contract["tuning"])
        tuning["quan"]["tables"].append({"id": "T2", "pos": [12, 2]})
        scenario = {"stock": {"ca_loc": 1, "ca_linh": 3}, "random_customers": False}
        session = Session("quan", tuning, scenario, seed=5)
        partial = {"id": "C0", "table_id": "T2", "dish_id": "lau_ca_linh_dien_dien",
                   "state": "waiting", "reserved": {}}
        first = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                 "state": "waiting", "reserved": {}}
        second = {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui",
                  "state": "waiting", "reserved": {}}

        before = session.sim._available_stock()
        self.assertFalse(session.sim._reserve_for_customer(partial))
        self.assertEqual(partial["reserved"], {})
        self.assertEqual(session.sim._available_stock(), before)
        self.assertTrue(session.sim._reserve_for_customer(first))
        session.sim.customers.append(first)
        self.assertFalse(session.sim._reserve_for_customer(second))
        self.assertEqual(first["reserved"], {"ca_loc": 1})
        self.assertEqual(second["reserved"], {})
        self.assertEqual(session.sim._available_stock(), {"ca_linh": 3})

    def test_tc_q3_012_release_and_consume_are_idempotent_without_refund(self):
        """[PROPOSED] A release frees availability; consume debits stock at most once."""
        contract = _contract()
        session = Session("quan", contract["tuning"], {"stock": {"ca_loc": 1}}, seed=8)
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting", "reserved": {}}

        self.assertTrue(session.sim._reserve_for_customer(customer))
        session.sim.customers.append(customer)
        self.assertEqual(session.sim._release_reservation("C1"), {"ca_loc": 1})
        self.assertEqual(session.sim._release_reservation("C1"), {})
        self.assertEqual(session.sim.stock, {"ca_loc": 1})

        customer2 = {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                     "state": "waiting", "reserved": {}}
        self.assertTrue(session.sim._reserve_for_customer(customer2))
        session.sim.customers = [customer2]
        self.assertTrue(session.sim._consume_reservation("C2"))
        self.assertFalse(session.sim._consume_reservation("C2"))
        self.assertEqual(session.sim.stock, {})
        self.assertEqual(session.sim._release_reservation("C2"), {})


class Q3PatienceTests(unittest.TestCase):
    def test_tc_q3_015_waiting_expiry_notifies_and_removes_once(self):
        """[PROPOSED] Waiting patience reaches zero, notifies once, and releases once."""
        contract = _contract()
        scenario = _fixture("waiting-expiry.json")["quan"]
        session = Session("quan", contract["tuning"], scenario, seed=1)

        first = _step(session)
        self.assertEqual(len(session.sim.customers), 1)
        self.assertEqual(session.sim.customers[0]["patience_ticks_left"], 1)
        self.assertFalse(any(row["name"] == "customer_left" for row in first))

        expired = _step(session)
        self.assertEqual(session.sim.customers, [])
        self.assertEqual([row["name"] for row in expired].count("customer_left"), 1)
        self.assertEqual(session.sim.stock, {"ca_loc": 1})
        self.assertEqual(session.snapshot()["tables"][0]["customer_id"], None)

        after = _step(session)
        self.assertEqual([row["name"] for row in after].count("customer_left"), 0)

    def test_tc_q3_015_eating_customer_is_not_waiting_timeout_target(self):
        contract = _contract()
        tuning = contract["tuning"]
        scenario = {
            "stock": {},
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                           "state": "eating", "patience_ticks_left": 0,
                           "eat_ticks_left": 3, "reserved": {}}],
        }
        session = Session("quan", tuning, scenario, seed=1)

        rows = _step(session)

        self.assertEqual(len(session.sim.customers), 1)
        self.assertEqual(session.sim.customers[0]["state"], "eating")
        self.assertFalse(any(row["name"] == "customer_left" for row in rows))


class Q3EndConditionTests(unittest.TestCase):
    def test_tc_q3_018_no_dish_queries_preserve_active_work(self):
        """[PROPOSED] No order is possible when idle, but active work prevents idle status."""
        contract = _contract()
        tuning = contract["tuning"]
        idle = Session("quan", tuning, {"stock": {}}, seed=2).sim
        self.assertFalse(idle._can_accept_order())
        self.assertFalse(idle._has_active_work())

        scenarios = {
            "reserved stock": {
                "stock": {"ca_loc": 1},
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                               "state": "waiting", "patience_ticks_left": 5,
                               "reserved": {"ca_loc": 1}}],
            },
            "cooking stove": {
                "stock": {},
                "stoves": [{"id": "B1", "state": "cooking", "dish": "ca_loc_nuong_trui",
                            "cook_ticks_left": 5}],
            },
            "hand": {"stock": {}, "hand": "ca_loc_nuong_trui"},
            "eating customer": {
                "stock": {},
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                               "state": "eating", "patience_ticks_left": 0, "eat_ticks_left": 5,
                               "reserved": {}}],
            },
        }
        for label, scenario in scenarios.items():
            with self.subTest(active_work=label):
                sim = Session("quan", tuning, scenario, seed=2).sim
                self.assertFalse(sim._can_accept_order())
                self.assertTrue(sim._has_active_work())


if __name__ == "__main__":
    unittest.main()
