# Data Pipeline Design — Capstone Exercise

> **Final exercise for the data_pipeline_design track**

Design and build a small end-to-end pipeline from scratch. The
goal is to put every module's ideas together: storage
abstractions, extraction, transformation, loading, and
orchestration. The pipeline is small enough to build in an
afternoon and rich enough to exercise every layer of the track.

---

## Scenario

You are the first data engineer at a small e-commerce
company. The engineering team has a Postgres database with
two tables: `users` and `orders`. They want a daily
pipeline that:

1. Extracts the previous day's `orders` and the
   corresponding `users` rows.
2. Transforms the data into a star schema:
   - `dim_users` (one row per user, with SCD2 columns
     `effective_from`, `effective_to`, `is_current`).
   - `fct_orders_daily` (one row per day, with totals).
3. Loads both into a SQLite warehouse using a bulk loader
   and an idempotency key.
4. Runs three data-quality checks on the result:
   `not_null(id)` on `dim_users`, `unique(order_id)` on
   `fct_orders_daily`, and `row_count_between` on
   `fct_orders_daily`.
5. Wraps the whole thing in a DAG with retries on the
   extract step.

You may use any of the abstractions from modules 02-06. The
acceptance test (in `tests/test_capstone.py`) verifies all
five steps.

---

## Layout

Put your work in `data_pipeline_design/exercise/`:

```
exercise/
  exercise.md       # this file
  code/
    pipeline.py     # the full pipeline
```

A reasonable acceptance test seeds a fake
Postgres-equivalent (a `QueryRunner` with `users` and
`orders`), runs the pipeline, and asserts:

- `dim_users` has the expected SCD2 rows.
- `fct_orders_daily` has one row per day with correct
  totals.
- The data-quality suite ran and produced three
  expectations.
- The DAG recorded the right execution order and marked
  every task DONE.
- A second run with the same idempotency key is a
  no-op.

---

## Hints

The five building blocks:

- **Extract**: a `QueryRunner` select with a date filter.
  Use the `JDBCExtractor` pattern from module 03 for
  the watermark, or just write a plain `SELECT` since
  the test seeds the database directly.

- **Transform**: a small Python function that takes a
  list of dicts and returns a list of dicts. Use
  `dedupe_by_key` from module 05 for the SCD2 logic.

- **Load**: use `bulk_load` from module 05. Generate a
  load_id from the run date and pass it to the bulk
  loader.

- **Data quality**: use `run_suite` from module 04 with
  three expectations.

- **Orchestration**: use the `Dag` from module 06.
  Register five tasks (`extract`, `transform_users`,
  `transform_orders`, `load`, `quality_check`); the
  quality check depends on the load.

---

## Stretch goals

If you finish early, add:

- A retry decorator on the extract step with
  `max_attempts=3` and `backoff=0.1`.
- A monitoring wrapper that records the duration of
  every task via `SLATracker`.
- A partitioned write: write `fct_orders_daily` to
  per-day partitions using `DatePartitioner`.
- A second pipeline that runs only the load step, so
  the team can backfill a missed date.
