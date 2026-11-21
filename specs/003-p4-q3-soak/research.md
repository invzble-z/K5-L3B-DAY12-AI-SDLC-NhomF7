# Research and decisions

- Phase 4 plan assigns Quoosc the soak CLI and requires one process, actual DaySim, a fast deterministic bot, real outputs and 10-day replay.
- Gather start is the dock position, so an `interact` edge ends that phase through normal GatherSim behavior. Quan receives no scripted actions. Shop closes with the normal `shop_done` input.
- DaySim itself repeats configured D1–D5 plans after day 5; soak does not rewrite day planning or gameplay tuning.
- The bot's explicit fast-dock policy results in zero earned money in current runs. This is reported as observed data, not a simulated success score.
