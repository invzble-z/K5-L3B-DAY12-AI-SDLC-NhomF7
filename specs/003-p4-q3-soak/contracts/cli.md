# CLI contract — `chonoi.soak`

```text
python -m chonoi.soak --seed INTEGER --days POSITIVE_INTEGER --out PATH
```

- All three arguments are required. Seed accepts any integer, matching `Streams`; days must be at least 1.
- Argument errors: argparse code 2; no result file is written.
- Success: code 0 only when the requested number of days completed with zero crashes and the JSON file was written.
- Runtime crash, derived tick-bound exhaustion or output error: nonzero. If simulation crashes but writing is possible, JSON includes a real crash count and diagnostic.
- Gameplay fields: `days`, `days_completed`, `crashes`, `results[]` (`day`, `earned`, `reputation`, `score`). `duration_s` is measured and may vary.
- Does not accept mock result data, browser flags, inventory overrides, or synthetic event injection.
