# Soak test plan

Run `python -m unittest tests.test_p4_soak -v` for argument validation, one day, ten days, gameplay-field replay, runtime crash accounting and output-path failure. The ten-day unit test shortens durations in copied tuning but still runs the real DaySim. Separately run the production tuning command twice with seed 7 and compare `days`, `days_completed`, `crashes`, and `results`; do not compare `duration_s`.

Evidence from actual production-tuning runs is stored under `docs/proof/phase-4/`.
