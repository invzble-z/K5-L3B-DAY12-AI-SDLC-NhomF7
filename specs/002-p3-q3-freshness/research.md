# Research and decisions

- `docs/plan/phase-3.md` assigns restaurant stock/reservation, 0.25 freshness points per second, threshold 30, exact Fraction arithmetic and stable ID tie-breaking to Quoosc.
- `game.contract.json` contains freshness tuning but remains version 1.1; `inventory.py` supports v1.2 by explicit version, while the shared default has not switched. Keep global contract ownership with Integrator.
- Existing Q4 price tests originally expected the full input freshness on the first tick. Phase 3 tick order decays stock before interaction, so test expectations were adjusted to the actual one-tick fraction; price formula itself remains Kiên's implementation.
- No shared `unfulfillable` event schema exists. The implementation uses a clearly labeled proposal and asks for approval in `docs/clarify.md` #16.
