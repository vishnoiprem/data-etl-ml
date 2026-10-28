## Exercises

1. **The invariant.** Write `check_no_double_count(destination, source)` that returns `True` only when every region's revenue in `destination` equals the source's within one cent. Then use `apply_load` to show it passing for `mode="truncate"` after two runs and failing for `mode="append"` after two runs.
2. **Harder — deterministic keys.** Construct three rows for the same `order_id` but different partitions (`20260115`, `20260116`) and show that `dedup_key` produces two distinct keys while three rows in the *same* partition produce one. Explain why the partition must be part of the key.
3. **Harder — backfill safety.** A backfill re-runs logical date `2026-01-10` today. Name three things in a typical DAG that would break under backfill, and say for each what the fix is.
