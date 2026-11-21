# Handoff — Q3 Phase 3

Quoosc implements restaurant freshness/reservations in `chonoi/sim/quan.py` and the integrated inventory path through contract v1.3. Proof includes [focused Q3/v1.3 tests](../../docs/proof/phase-4/q3-focused-tests.txt), [Day headless/replay](../../docs/proof/phase-4/day-headless-run.txt), and [full suite](../../docs/proof/phase-4/q3-full-regression.txt).

The shared root manifest is v1.3. The tests verify physical inventory parsing and scenario reservation validation, gather → inventory file → Quan ID/freshness continuity, and Day handoff. Legacy count inventory remains covered only with explicit v1.1 tuning.

Integrator/PO: approve the proposed `unfulfillable` payload in clarify #16 before declaring the event contract complete. QA/Integrator: review v1.3 UI/client compatibility and the integrated branch evidence. No reviewer approval is claimed here.
