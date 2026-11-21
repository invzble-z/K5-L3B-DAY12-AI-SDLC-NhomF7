# Plan — Q3 Quán freshness

1. Preserve legacy count stock and normalize individual stock to the shared `Item` model.
2. Add contract-driven exact freshness decay before customer/stove interactions.
3. Centralize usable-stock counting, freshest-first atomic reservation and ID-based consume/release behavior.
4. Emit threshold-crossing `spoiled`; retry affected reservations once in stable order; preserve stock IDs on failure.
5. Add isolated QuanSim tests with real `Item` instances and fixtures; run Q3, Phase 3 price, P1/P2 integration and repository regression.
6. Record provisional event schema, verification and outstanding team-owned AC in proof/handoff docs.

No shared contract version or unrelated cook/price mechanics are changed by this plan.
