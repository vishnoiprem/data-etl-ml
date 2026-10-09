# Module 05 — Loading

> **6 lessons · ~3 hours**

The "L" in ETL. Where the data lands. This module covers the
six patterns every loader implements: bulk loading, streaming,
upsert, partitioning, idempotency, and the lakehouse-specific
patterns that come up at every senior interview.

Author: **Prem Vishnoi &lt;prem.vishnoi@example.com&gt;**

---

## Lessons

| # | Lesson | What you'll learn |
|---|---|---|
| 19 | [Bulk Loading (COPY INTO, Parquet, ORC)](design/19_bulk_loading.md) | The fastest way to land large files. |
| 20 | [Streaming Loading (Kafka, Kinesis, Pub/Sub)](design/20_streaming_loading.md) | The right pattern when latency matters. |
| 21 | [Upsert and Merge Patterns](design/21_upsert_and_merge_patterns.md) | MERGE INTO, INSERT ON CONFLICT, SCD2 close. |
| 22 | [Partitioning Strategies in the Warehouse](design/22_partitioning_strategies.md) | Date, key, and bucket partitioning. |
| 23 | [Idempotency and Exactly-Once Semantics](design/23_idempotency_and_exactly_once.md) | The hardest problem in data engineering. |
| 24 | [Loading into a Lakehouse](design/24_loading_into_a_lakehouse.md) | Delta Lake, Iceberg, Hudi. |

---

## Code

- [`code/bulk_loader.py`](code/bulk_loader.py) — bulk Parquet-style
  loader (using SQLite as the stand-in for a warehouse).
- [`code/streaming_loader.py`](code/streaming_loader.py) — Kafka-style
  streaming loader with batching and a simulated broker.
- [`code/upsert.py`](code/upsert.py) — `merge_into` upsert helper
  with the spec'd 10→5 change test.
- [`code/partitioning.py`](code/partitioning.py) — date and key
  partitioning writer.
- [`code/idempotency.py`](code/idempotency.py) — wrapper that
  dedupes a stream by a key.
- [`tests/test_loading.py`](tests/test_loading.py) — 25+ unit tests.

---

## How the lessons connect

Loading is the *bottom* of the medallion. The pattern is:

```
extract → transform → load
                          ↓
            bronze (raw) → silver (cleaned) → gold (curated)
                          ↓
                       serving
```

Each layer in the medallion uses a different load pattern. Bronze
is bulk. Silver is upsert. Gold is bulk-with-partition-overwrite.
Serving is reverse-ETL.

By the end of this module you'll know which pattern fits which
layer — and you'll have the code to back it up.
