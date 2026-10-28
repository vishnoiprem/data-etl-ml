## Exercises

1. **Timeout versus SLA.** For a daily DAG with a two-hour SLA and a sensor that waits up to 30 minutes, give the `timeout`, `execution_timeout`, `retries` and `sla` values you would use, and say which one fires if the source file never arrives.
2. **Harder — a readiness rule.** Write a function `ready_for_load(lines)` that returns True only when the data has at least 1 000 accepted rows **and** fewer than 100 rejected rows. Test it against `orders.csv` and against `malformed_orders.csv`, and explain why a plain "file exists" check would be wrong for both.
3. **Harder — the backfill SLA.** A run for logical date `2026-01-15` is executed by a backfill on `2026-01-20` and finishes at `2026-01-20 04:00 UTC`. Using a two-hour SLA, decide whether the run met its SLA, and explain why the answer must not depend on the date the backfill was executed.
