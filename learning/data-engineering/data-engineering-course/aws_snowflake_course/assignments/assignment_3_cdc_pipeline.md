# Assignment 3 — CDC Pipeline with Streams + Tasks

> **Duration:** 4 hours.  Combines sections 4, 7, 16, 20.

## Goal

Build a change-data-capture (CDC) pipeline that keeps an aggregated
`DASHBOARD_ORDERS_HOURLY` table in sync with a high-volume
`RAW_EVENTS` source — using nothing but a stream and a task.

## Steps

1. Create a `RAW_EVENTS` (PERMANENT) table with `DATA_RETENTION_TIME_IN_DAYS = 1`.
2. Create an `APPEND_ONLY` stream on it.
3. Create a `DASHBOARD_ORDERS_HOURLY` table keyed on
   `(region, hour_bucket)` with a clustering key.
4. Write a `TASK` that:
   - reads the stream,
   - applies `MERGE` into the dashboard table,
   - sleeps 60 s,
   - loops via `SYSTEM$STREAM_HAS_DATA` (avoid wasted work).
5. Insert 10 000 rows in batches; confirm the dashboard catches up
   within 1 minute of the last insert.
6. Verify storage growth by running `SHOW TABLES` before and after.
7. Convert the `RAW_EVENTS` to **TRANSIENT** to remove Fail-Safe and
   reduce cost; ensure the stream still works.

## Deliverable

A PR that adds:
- `20_extra_topics/code/create_stream.sql` (the change-tracking stream)
- `20_extra_topics/code/create_task.sql` (the merge task)
- `20_extra_topics/code/create_materialized_view.sql` (alternative
  read-side, compare trade-offs in NOTES)
- `tests/test_cdc.py` (≥ 6 tests, FakeConnection-based)
- `NOTES.md` explaining the trade-off you chose (MV vs. stream+task+merge)
  for the specific workload (write rate, query latency, cost).

## Bonus

- Add an **alert** that fires (via Snowflake's native notification
  integration) when the stream has > 1 M pending rows.
- Add a **second** stream on the dashboard table to enable
  outbox-pattern CDC downstream.
- Convert the task graph to a **DAG** (parent task → child task) using
  `AFTER` clauses and document the failure semantics.

## Author

Prem Vishnoi <pvishnoi@avilx.com>
