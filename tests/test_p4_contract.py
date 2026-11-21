"""Unit test cho AC-P4-01 (Khai báo Contract v1.3: bench_cmd và soak_cmd).

Chạy: python -m unittest tests.test_p4_contract -v
"""

import unittest

from chonoi.contract import DEFAULT_PATH, load_contract, validate_contract
from chonoi.errors import BadInput


class ContractPhase4Tests(unittest.TestCase):
    def test_contract_v13_root_fields(self):
        c = load_contract()
        self.assertEqual(c.get("contract_version"), "1.3")
        self.assertEqual(c.get("bench_cmd"), "python3 -m chonoi.bench")
        self.assertEqual(c.get("soak_cmd"), "python3 -m chonoi.soak")
        self.assertEqual(c.get("build_cmd"), "true")
        self.assertIn("python3 -m chonoi.live", c.get("run_cmd", ""))
        self.assertEqual(c.get("headless_cmd"), "python3 -m chonoi.headless")

    def test_validate_contract_rejects_missing_bench_or_soak(self):
        c = load_contract()
        c_bad_bench = dict(c)
        c_bad_bench["bench_cmd"] = ""
        with self.assertRaises(BadInput):
            validate_contract(c_bad_bench)

        c_bad_soak = dict(c)
        c_bad_soak["soak_cmd"] = None
        with self.assertRaises(BadInput):
            validate_contract(c_bad_soak)


if __name__ == "__main__":
    unittest.main()
