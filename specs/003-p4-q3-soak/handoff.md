# Handoff — AC-P4-03

Implementation: `chonoi/soak.py`; tests: `tests/test_p4_soak.py`; fresh production-tuning proof: [`soak-q3-run1.json`](../../docs/proof/phase-4/soak-q3-run1.json), [`soak-q3-run2.json`](../../docs/proof/phase-4/soak-q3-run2.json), [focused test output](../../docs/proof/phase-4/q3-focused-tests.txt).

Both runs use seed 7, complete 10/10 days with zero crashes and exit 0; gameplay fields match. The fast-dock bot leaves QuanSim uncontrolled and does not gather, so `earned=0` is observed behavior. This proves lifecycle stability under this policy, not economy balance or player strategy quality.

QA/Integrator should review the run files and branch diff. Benchmark, UI warnings, packaging and release remain owned outside this soak task; no external review approval is claimed.
