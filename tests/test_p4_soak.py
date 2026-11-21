"""Tests for deterministic, actual-DaySim soak execution."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session
from chonoi.soak import _tuning_for_days, main, run_soak


class SoakTests(unittest.TestCase):
    def quick_tuning(self):
        tuning = copy.deepcopy(load_contract()["tuning"])
        tuning["gather"]["duration_s"] = 1
        tuning["quan"]["duration_s"] = 2
        tuning["quan"]["first_customer_tick"] = 10000
        tuning["shop"]["max_ticks"] = 2
        return tuning

    def run_in(self, directory, name, days=1):
        return run_soak(7, days, str(Path(directory) / name), tuning=self.quick_tuning())

    def test_cli_rejects_non_integer_seed_and_invalid_days(self):
        with self.assertRaises(SystemExit) as seed_error:
            main(["--seed", "nope", "--days", "1", "--out", "unused.json"])
        self.assertEqual(seed_error.exception.code, 2)
        with self.assertRaises(SystemExit) as days_error:
            main(["--seed", "1", "--days", "0", "--out", "unused.json"])
        self.assertEqual(days_error.exception.code, 2)

    def test_one_day_uses_real_daysim_and_writes_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            code, result = self.run_in(directory, "one.json")
            written = json.loads((Path(directory) / "one.json").read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(result["days_completed"], 1)
        self.assertEqual(result["crashes"], 0)
        self.assertEqual(result["results"], [{"day": 1, "earned": 0, "reputation": 3.0, "score": 300}])
        self.assertEqual(set(written), {"days", "days_completed", "crashes", "results", "duration_s"})
        self.assertGreaterEqual(written["duration_s"], 0)

    def test_ten_day_replay_matches_gameplay_results(self):
        with tempfile.TemporaryDirectory() as directory:
            code_a, result_a = self.run_in(directory, "a.json", days=10)
            code_b, result_b = self.run_in(directory, "b.json", days=10)
        self.assertEqual(code_a, 0)
        self.assertEqual(code_b, 0)
        self.assertEqual(result_a["days_completed"], 10)
        self.assertEqual(result_a["crashes"], 0)
        for field in ("days", "days_completed", "crashes", "results"):
            self.assertEqual(result_a[field], result_b[field])
        self.assertEqual([row["day"] for row in result_a["results"]], list(range(1, 11)))

    def test_day_plan_event_repeats_d1_to_d5_for_days_six_to_ten(self):
        tuning = self.quick_tuning()
        original = copy.deepcopy(tuning["day_plan"])
        cycle = [original[str(day)] for day in range(1, 6)]
        tuning = _tuning_for_days(tuning, 10)
        session = Session("day", tuning, {
            "day": {"days": 10},
            "gather": {"time_left_ticks": 1, "random_fish": False},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }, seed=7, days=10)
        observed = []
        while not session.done:
            phase = session.sim.phase
            edges = {"interact"} if phase == "gather" else ({"shop_done"} if phase == "shop" else set())
            rows = session.step(InputState((0.0, 0.0), {}, edges))
            observed.extend(row["data"] for row in rows if row["name"] == "day_plan")
        expected = [cycle[index % 5] for index in range(10)]
        self.assertEqual([row["dishes"] for row in observed], [p["dishes"] for p in expected])
        self.assertEqual([row["ingredients"] for row in observed], [p["ingredients"] for p in expected])
        self.assertEqual(tuning["day_plan"]["6"], original["1"])
        self.assertEqual(tuning["day_plan"]["10"], original["5"])

    def test_soak_day_with_real_payment_preserves_money_and_reputation(self):
        tuning = self.quick_tuning()
        tuning["quan"]["reputation_initial"] = 3.0
        scenario = {
            "day": {"days": 1, "money": 10},
            "gather": {"time_left_ticks": 1, "random_fish": False},
            "quan": {
                "time_left_ticks": 1,
                "random_customers": False,
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                               "state": "eating", "eat_ticks_left": 1}],
            },
        }
        observed_rows = []
        original_step = Session.step

        def capture_step(session, inputs):
            rows = original_step(session, inputs)
            observed_rows.extend(rows)
            return rows

        with tempfile.TemporaryDirectory() as directory, \
                patch("chonoi.soak.Session.step", new=capture_step):
            code, result = run_soak(7, 1, str(Path(directory) / "paid.json"),
                                    tuning=tuning, scenario=scenario)
        self.assertEqual(code, 0)
        self.assertEqual([row["name"] for row in observed_rows if row["name"] == "paid"], ["paid"])
        self.assertEqual(result["results"][0]["earned"], 72)
        self.assertEqual(result["results"][0]["reputation"], 3.2)
        self.assertEqual(result["results"][0]["score"], 372)

    def test_runtime_crash_is_counted_and_not_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("chonoi.soak.Session.step", side_effect=RuntimeError("injected runtime failure")):
                code, result = self.run_in(directory, "crash.json")
            saved = json.loads((Path(directory) / "crash.json").read_text(encoding="utf-8"))
        self.assertEqual(code, 1)
        self.assertEqual(result["crashes"], 1)
        self.assertEqual(result["days_completed"], 0)
        self.assertIn("injected runtime failure", saved["diagnostics"][0]["error"])

    def test_output_path_error_returns_nonzero(self):
        code, result = run_soak(7, 1, "missing-parent/soak.json", tuning=self.quick_tuning())
        self.assertEqual(code, 1)
        self.assertEqual(result["days_completed"], 1)
        self.assertEqual(result["crashes"], 0)


if __name__ == "__main__":
    unittest.main()
