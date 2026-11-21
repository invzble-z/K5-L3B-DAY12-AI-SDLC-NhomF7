# Plan — DaySim soak

1. Parse `--seed`, `--days`, and `--out`; validate seed integer and positive day count.
2. Create one real `Session` in day mode with the requested day count.
3. Drive one interact edge at Gather start and one `shop_done` edge on Shop entry; leave Quan untouched.
4. Observe day completion, cumulative earned/reputation/score, runtime exceptions and actual wall duration.
5. Write JSON even after a caught simulation crash when the output path remains writable; return nonzero unless every requested day completes without a crash.
6. Test CLI, one/multiple/ten days, replay, runtime failure and output-path failure; record real ten-day proof.
