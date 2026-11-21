# Feature: Phase 4 deterministic DaySim soak

## Scope

Implement AC-P4-03 assigned to Quoosc: run the actual `DaySim` for a requested number of days in one process, using deterministic bot inputs and writing observed gameplay results. This does not implement the benchmark, browser UI, package, or release tasks owned by other teammates.

## Requirements

- CLI: `python -m chonoi.soak --seed 7 --days 10 --out soak.json`.
- Use `Session("day", ...)` and the real DaySim/QuanSim/GatherSim code; no browser or fabricated gameplay events/results.
- Bot docks at the gather start, leaves QuanSim to run by its rules, and closes each Shop through `shop_done`.
- Days after day 5 use DaySim's configured repeat plan.
- Output includes requested/completed days, real crash count, one result per completed day and measured wall duration.
- Same seed/tuning gives identical gameplay fields; wall duration may vary.
- Invalid arguments fail with code 2; runtime/output failures return nonzero and diagnostics are retained when output is writable.

## Acceptance

AC-P4-03 is verified only when the real 10-day command finishes with `days_completed=10`, `crashes=0`, ten ordered results, successful gameplay-field replay comparison, and exit code 0. Current proof records those conditions. The selected bot deliberately gathers no ingredients, so current earned amounts are zero; this is real observed gameplay under the requested fast-dock policy.
