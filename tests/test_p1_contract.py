"""Phase 1, contract B/D: validate restaurant fixtures before writing JSONL."""

import os
import unittest

from helpers import Workdir, read_jsonl, run_headless, write_json


class RestaurantFixtureContract(unittest.TestCase):
    def run_fixture(self, directory, customer_fields=None, random_customers=False):
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        customer.update(customer_fields or {})
        scenario = write_json(directory.path("scenario.json"), {"quan": {
            "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
            "random_customers": random_customers,
            "customers": [customer],
        }})
        output = directory.path("output.jsonl")
        code, error = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                   "--scenario", scenario, "--out", output)
        return code, error, output

    def assert_invalid_fixture(self, **kwargs):
        with Workdir() as directory:
            code, error, output = self.run_fixture(directory, **kwargs)
            self.assertEqual(code, 2, error)
            self.assertTrue(error.strip(), "Expected a diagnostic on stderr")
            self.assertFalse(os.path.exists(output), "Invalid fixture created output")

    def test_valid_customer_patience(self):
        with Workdir() as directory:
            code, error, output = self.run_fixture(directory, {"patience_ticks_left": 12})
            self.assertEqual(code, 0, error)
            first = read_jsonl(output)[0]
            self.assertEqual((first["type"], first["tick"]), ("snapshot", 0))
            self.assertEqual(first["customers"][0]["patience_ticks_left"], 12)

    def test_negative_patience(self):
        self.assert_invalid_fixture(customer_fields={"patience_ticks_left": -1})

    def test_unknown_customer_field(self):
        self.assert_invalid_fixture(customer_fields={"patience_ticks": 12})

    def test_random_customers_requires_boolean(self):
        self.assert_invalid_fixture(random_customers="no")
