# Tasks — Q3 Phase 3

- [x] Read Phase 3 ownership, freshness tuning and shared inventory contract.
- [x] Add tests for freshness, threshold, ID selection, atomicity, retry/failure and idempotent consume/release.
- [x] Implement exact Quan stock decay and `spoiled` events.
- [x] Implement freshest-first physical ID reservation and safe single retry after spoilage.
- [x] Preserve v1.1 count inventory path when explicitly selected.
- [x] Integrate contract v1.3 root version through gather → physical inventory file → Quan; validate physical scenario/inventory and Day handoff.
- [ ] Integrator/PO approve the `unfulfillable` event payload (clarify #16).
- [ ] QA/Integrator review the full integrated v1.3 evidence and confirm UI/client compatibility.

Evidence: [v1.3 focused/regression tests](../../docs/proof/phase-4/q3-focused-tests.txt), [Day headless](../../docs/proof/phase-4/day-headless-run.txt), [full suite](../../docs/proof/phase-4/q3-full-regression.txt).
