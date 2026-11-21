# Feature: Q3 Quán inventory freshness and ID reservations

## Status and source

This feature owns the Phase 3 customer/stock work assigned to Quoosc. Sources are `docs/plan/phase-3.md`, the current `game.contract.json` freshness tuning, and the item rules in `docs/contracts/README.md`. The shared manifest remains contract version 1.1; changing that version or its schema is outside this feature's authority.

## User stories

- As the restaurant simulation, I keep each physical ingredient's ID and exact freshness until it is cooked or handed off.
- As a customer order arrives, I reserve a complete recipe from usable stock, choosing the freshest items and breaking ties by stable ID order.
- As stock ages, I emit one `spoiled` event per item that crosses below the configured freshness threshold.
- As an order loses a reserved ingredient to spoilage, I release its whole reservation and make one atomic replacement attempt.

## Acceptance criteria

- Quan decay per tick is `freshness.quan_decay_per_s / tick_hz`, using `Fraction`; pause does not step QuanSim.
- Freshness is clamped at zero. Stock at or below the spoiled threshold cannot be reserved.
- Selection is all-or-nothing by recipe, freshest first and ID order for ties; no physical ID can be held by two customers.
- `spoiled` is emitted once on a threshold crossing, in ID order, with `location: "stock"`.
- Affected orders are handled by `order_tick`, then table ID. Old reservations are released before one retry. Failure leaves the customer waiting without stock reservation and records the proposed `unfulfillable` status/event.
- Legacy count inventories retain their existing behavior. Individual stock uses the shared `Item` type.
- Deterministic same-seed simulation and P1/P2/Q4 regression remain covered.

## Known contract boundary

The `unfulfillable` event payload is provisional: `{customer_id, table_id, dish_id}`. It is not listed in the shared event contract. See clarify #16 and the Q3 proof; this feature does not claim external acceptance for that schema.
