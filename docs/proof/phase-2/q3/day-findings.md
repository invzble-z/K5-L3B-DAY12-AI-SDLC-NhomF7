# Day/Q3 integration findings — 2026-11-21

Verified branch HEAD: `5b79199`, merge of `origin/main` `ba17f4d`.
Integration test commits: `84f9546`, `053867b`; proof files are a documentation-only follow-up.

## T07 — DaySim and QuanSim

### Verified

- `DaySim._init_quan()` constructs the real `QuanSim` and gives it a copy of the accumulated Gather inventory through `quan_sc["stock"]`.
- With a non-empty plan, the selected dish set reaches QuanSim. The Phase 2 manifest mapping for D1–D5 is readable; the same interface also accepts a list-shaped test copy. Snapshot/event plan contents remain unchanged.
- Gather hold `ca_loc ×1` became Quan physical stock `ca_loc ×1` exactly once. Reservation left physical stock at 1 and `snapshot.stock` at 0. Cooking consumed it once; a second consume returned false. Customer departure released unused reservation; physical stock stayed 1 and availability returned to 1.
- A new Day builds a new QuanSim with empty customers and `elapsed_ticks=0`; Day 2 event order and day counter matched the fixture.
- One-day and three-day headless smoke scenarios ended with `days_complete`, correct `days_completed`, expected event order, and byte-identical three-day replay.
- A fixture payment was emitted once (price 60, tip 12); DaySim cumulative money changed from 10 to 82 while earned changed from 0 to 72.
- With the real manifest customer tuning, DaySim produced arrivals at elapsed ticks 120 and 1020 (`120 + 900k`), choosing T1 then T2 and unique customer IDs.

### Unresolved integration defects (DaySim/Runner owner: `invzble-z`)

1. **Empty filter becomes full menu.** In `DaySim._init_quan()`, `set(plan.get("dishes", {}).keys()) if plan.get("dishes") else None` returns `None` for `{}`. `QuanSim` defines `None` as full menu and `set()` as no menu. Runtime reproduction with enough `ca_loc`/`bong_sung` stock, automatic arrivals enabled and first-arrival tick 1 produced `planned_dishes is None` and `customer_arrived` for `ca_loc_nuong_trui` under an empty plan. Do not alter QuanSim's `None`/empty-set semantics. Minimal DaySim suggestion: always pass `set(plan.get("dishes", {}).keys())` when a day plan object exists; PO must still decide whether an empty day menu should be playable.
2. **Reputation not propagated.** Day-level scenario reputation 4.25 yielded QuanSim reputation 3.0 at the first shift. A customer payment with a tip changed DaySim reputation to 3.2, but next day's QuanSim started again at 3.0. Minimal proposal: pass `self.reputation` into the Quan scenario when constructing each shift, preserving explicit fixture behavior if the contract requires it.
3. **Pause snapshot tick mismatch.** After pause, `phase_tick` and phase timer held, and no gameplay schedule advanced, but `Session.snapshot().sim_tick` followed the outer tick (1, then 2). The contract says `sim_tick` stands still while paused. Runner owner should maintain an active simulation tick separate from outer tick.

The above defects are covered by expected-failure tests in `tests/test_p2_q3_day_integration.py`; they remain unresolved here because DaySim and Runner are owned by the Integrator. T07 is PARTIAL.

Concrete patch direction for the owner (not applied):

```python
# DaySim._init_quan
menu_filter = set(plan.get("dishes", {}).keys())
quan_sc["reputation"] = self.reputation

# Session
self.sim_tick = 0
# after sim.step(inp), increment only when the Day phase is running after
# the step (a resume step runs gameplay; a pause-entry step does not).
if self.mode != "day" or self.sim.state == "running":
    self.sim_tick += 1
```

Use `self.sim_tick` for snapshot/end `sim_tick`, leaving outer `tick` monotonic. The owner should reconcile an explicitly supplied `quan.reputation` fixture with day-level reputation before applying the DaySim change.

## T08 — Q3/Q4 and Phase 3

- Q3/Q4 Phase 2 tests: 19/19 passed, including two independent stoves, six dishes, order ordering, reservation consumption, payment and the Q4-F1 reproduction.
- Phase 3 price/freshness tests: 4/4 passed; no Phase 3 implementation changed.
- **Q4-F1 remains reproducible** on `5b79199`: a customer can leave during cooking and the dish can still finish and be picked up. This is a reproduction, not a fix. Policy (cancel, retain or reuse) needs PO `nganhduong123` and module owner `ttkien0710` before a code change.
- `no_dish` and customer/order event payload remain unresolved contract questions.

## T09 — contract/source limitations

- `game.contract.json` uses `day_plan` mapping keys `"1"`–`"5"`. `docs/contracts/README.md`'s proposal says Ticket-02 specifies a list and lists different D2–D5 dishes/amounts. The original Ticket-02/Test Contract source was not present in the checkout and could not be established from repository docs; neither source was selected as canonical.
- No change was made to `game.contract.json`, `docs/contracts/`, or inventory schema. Counts in `day_plan.dishes` remain selection data; this work does not treat them as quotas.
- Integrator/PO must supply/confirm the authoritative Ticket-02, mapping/list shape, canonical D2–D5 data, count semantics, `no_dish`, and event/state contracts.

## T10 — QA/handoff

- Test and proof artifacts are committed on `p2/q3-day-integration`. This is engineering evidence, not QA approval.
- No QA review submission was present for this new branch at verification time. Minh must review after the owner fixes.
- Personal reflection is still for Quốc to confirm.
