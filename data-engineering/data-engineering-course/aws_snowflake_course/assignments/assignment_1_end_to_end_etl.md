# Assignment 1 — End-to-End CSV → S3 → Snowflake → ELT Pipeline

> **Duration:** 4 hours.  Combines sections 4, 7, 8, 17.

## Goal

Build a production-style pipeline that:

1. Ingests a daily CSV from S3 into a `RAW` table with Snowpipe.
2. Transforms `RAW` → `STG` → `MART` in pure SQL (tasks + streams).
3. Promotes every change to a **zero-copy dev clone** so engineers can
   experiment without breaking production.

## Steps

1. Provision a Snowflake warehouse, a database, and a S3 bucket in your
   own AWS account.
2. Create an IAM role and a `STORAGE INTEGRATION` for the bucket.
3. `PUT` (or auto-ingest) a CSV with ~500 k synthetic orders to the bucket.
4. Build `RAW_ORDERS` and a `PIPE` (auto-ingest) that loads new files
   within ~1 minute of arrival.
5. Create a `STG_ORDERS` (typed) and a `MART_DAILY_AGG` (aggregated) and
   wire them with a `STREAM` + a `TASK` (every 5 minutes, CRON-driven).
6. `CREATE DATABASE DEV_DB CLONE SNOWFLAKE_DEMO AT (OFFSET => -60*5);`
   and confirm `SELECT COUNT(*)` is identical between prod and dev.
7. Drop, re-create, and re-attach all objects using `IF NOT EXISTS` /
   `OR REPLACE` to keep everything idempotent.

## Deliverable

A PR that adds:
- `04_loading_data/code/load_csv.sql` (extended with PUT instructions)
- `11_snowpipe/code/snowpipe_setup.sql` (with real ARN placeholders)
- `20_extra_topics/code/create_task.sql` (consumer of the stream)
- `17_zero_copy_cloning/code/clone_database.sql` (production dev clone)
- `tests/test_pipeline.py` (≥ 6 tests, FakeConnection-based)
- `NOTES.md` (one engineering decision you made and why)

## Bonus

- Add a **masking policy** on the customer email so an `ANALYST_READ` role
  sees `a***@example.com` but `ANALYST_FULL` sees the full address.
- Add a **TABLESAMPLE BERNOULLI (5)** based Power-BI connection string in
  the NOTES.
- Add a **Time-Travel drill**: drop a column, recover it via
  `CREATE TABLE ... CLONE ... AT (OFFSET => -60*60)`.

## Author

Prem Vishnoi <pvishnoi@avilx.com>
