# Soak output data model

```json
{
  "days": 10,
  "days_completed": 10,
  "crashes": 0,
  "results": [
    {"day": 1, "earned": 0, "reputation": 3.0, "score": 300}
  ],
  "duration_s": 0.0
}
```

The sample values illustrate shape only. Each result is captured after the corresponding Shop closes. `earned` is the actual daily increase in DaySim's cumulative earned field; `score` uses the same contract formula as runner snapshots (`cumulative earned + reputation_multiplier × floor(reputation)`). `duration_s` is measured wall time and is excluded from replay equality. On a runtime exception, `diagnostics` is added with the actual day and exception text; completed results are retained.
