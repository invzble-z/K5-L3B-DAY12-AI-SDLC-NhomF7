# Test plan — Q3 Phase 3 freshness

Run `python -m unittest tests.test_p3_q3_freshness tests.test_p3_quan_price -v`.

Coverage: exact 0.25-per-second decay at 60 Hz, clamp at zero, freshness threshold and one-shot event, stable ID order, freshest-first ties, complete multi-kind recipes, no partial reservation, no shared IDs, release/replacement, failed replacement, one consume/release, and deterministic replay. Then run Phase 1 Q3, Phase 2 customer/Day integration, Phase 3 inventory/gather/price, Phase 4 soak, and the full unittest suite.

Q4 price assertions account for the Phase 3 tick order: raw stock decays before the first interaction. Shared event-schema approval and contract 1.2 end-to-end file input are tracked as limitations, not hidden by isolated test success.
