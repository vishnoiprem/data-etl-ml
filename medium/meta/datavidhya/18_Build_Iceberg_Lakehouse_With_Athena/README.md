# 18 — Build an Iceberg Lakehouse with Athena

A runnable, **offline-first** mirror of the AWS Skill Builder lab
**"Build an Iceberg Lakehouse with Athena."** Eight stages, nine shell
scripts that map exactly to the lab's "click in the console" instructions,
plus a pytest suite that simulates Athena/Iceberg in-process via PyIceberg.
No AWS credentials needed for verification.

```
                       ┌──────────────────────────────────┐
                       │   athena-iceberg-lakehouse-bucket │
                       │                                     │
                       │   raw/orders/orders.csv  (seed)     │
                       │                                     │
                       │   iceberg-warehouse/                │
                       │     orders_iceberg/                 │
                       │       metadata/      (JSON manifests)
                       │       data/          (Parquet)      │
                       └──────────────┬──────────────────────┘
                                      │  DML / DDL
                                      ▼
                       ┌──────────────────────────────────┐
                       │   Athena (engine v3)               │
                       │                                     │
                       │   SELECT / UPDATE / DELETE /       │
                       │   FOR SYSTEM_VERSION AS OF /       │
                       │   INSERT INTO ...                   │
                       └──────────────────────────────────────┘
```

## Files

| Path                                                | Purpose                                  |
|-----------------------------------------------------|------------------------------------------|
| `sample_data/orders.csv`                            | The 12-row seed CSV the lab provisions   |
| `lakehouse.py`                                      | PyIceberg-backed simulator (Hive + Iceberg tables, snapshots, time travel) |
| `01_iceberg_lakehouse_with_athena.py`               | Self-asserting driver (8 stages, 27 checks) |
| `scripts/00_set_lakehouse.sh`                       | Helper: set BUCKET / DATABASE / WORKGROUP |
| `scripts/01_register_csv.sh` through `08_teardown.sh` | Eight stage scripts (one per lab stage) |
| `scripts/run_all.sh`                                | Optional: run stages 1–7 in sequence     |
| `tests/conftest.py`                                 | Pytest fixture: fresh lakehouse per test |
| `tests/test_lakehouse.py`                           | 13 pytest tests, no AWS creds            |
| `README.md`                                         | This file                                |

## The 8 lab stages — mapped to artifacts

| Stage | Lab step                                                      | Artifact                                |
|-------|---------------------------------------------------------------|-----------------------------------------|
| 1     | Stage the seed CSV behind a Hive external table               | `01_register_csv.sh`, `test_stage1_*`   |
| 2     | `CREATE TABLE AS SELECT` into an Iceberg table                | `02_ctas_iceberg.sh`, `test_stage2_*`   |
| 3     | Row-level `UPDATE` (placed → shipped for order 1001)          | `03_update.sh`, `test_stage3_*`         |
| 4     | Bulk `DELETE` (drop all cancelled orders)                     | `04_delete.sh`, `test_stage4_*`         |
| 5     | Time travel via `FOR SYSTEM_VERSION AS OF` and timestamp     | `05_time_travel.sh`, `test_stage5_*`    |
| 6     | `INSERT INTO` adds two rows, grows the snapshot count         | `06_insert.sh`, `test_stage6_*`         |
| 7     | Inspect `$snapshots` / `$files` / `$manifests` metadata      | `07_metadata.sh`, `test_stage7_*`       |
| 8     | Snapshot isolation — old reads stay stable across writes     | driver stage 8, `test_stage8_*`         |

## Run it offline (no AWS account)

```bash
cd medium/meta/datavidhya/18_Build_Iceberg_Lakehouse_With_Athena/

# Self-asserting driver -- 27 checks, all PASS.
../../../.env/bin/python 01_iceberg_lakehouse_with_athena.py

# pytest -- 13 tests, all PASS.
../../../.env/bin/python -m pytest tests/ -v
```

Internally the driver and tests use `pyiceberg.catalog.memory.InMemoryCatalog`
to simulate the Glue database, Athena engine, and Iceberg metadata layer
in-process; both run with zero network and zero credentials.

## Run it against a real AWS account

```bash
export BUCKET=athena-iceberg-lakehouse-bucket-a1b2c3
export DATABASE=lakehouse_db_a1b2c3
export WORKGROUP=iceberg-lakehouse-Ab3xYz
export AWS_REGION=us-east-1

./scripts/run_all.sh      # stages 1-7
./scripts/08_teardown.sh  # explicit teardown
```

`run_all.sh` runs the seven mutating scripts in order. Stage 0 (capture
resource names) is run separately because it requires pasting the names
from the lab console. Stage 8 (teardown) is also separate so you can
inspect the bucket state before destroying it.

## What each lab stage actually does

### Stage 1 — Hive external table over the CSV

```sql
CREATE EXTERNAL TABLE lakehouse_db_xxxxx.orders_csv (
  order_id     bigint,
  customer_id  bigint,
  amount       string,
  currency     string,
  order_date   string,
  status       string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION 's3://<bucket>/raw/orders/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

Hive tables are **read-only** from Athena's perspective. The CSV stays in
S3 exactly where it was — Athena just maintains a pointer (location +
schema) to it.

### Stage 2 — CTAS into an Iceberg table

```sql
CREATE TABLE lakehouse_db_xxxxx.orders_iceberg
WITH (
  table_type         = 'ICEBERG',
  format             = 'PARQUET',
  write_compression  = 'SNAPPY',
  location           = 's3://<bucket>/iceberg-warehouse/orders_iceberg/'
) AS
SELECT order_id, customer_id, amount, currency, order_date, status
FROM lakehouse_db_xxxxx.orders_csv
WHERE status = 'placed';
```

CTAS with `table_type=ICEBERG` is the one-step "raw → Iceberg" pipeline.
The new table is born Iceberg: a metadata JSON in `metadata/` plus one or
more Parquet data files in `data/`. After this stage there is exactly
**one snapshot**.

### Stage 3 — `UPDATE`

```sql
UPDATE orders_iceberg
SET status = 'shipped'
WHERE order_id = 1001;
```

Athena's UPDATE on an Iceberg table is **copy-on-write**: under the hood
Iceberg issues a `delete` for the old row and an `append` for the new
value, all inside a single ACID transaction. **Two snapshots** are
committed even though only one logical write happened. The snapshot
table will show two new rows after this stage (snapshot 2 = the delete,
snapshot 3 = the insert).

### Stage 4 — `DELETE`

```sql
DELETE FROM orders_iceberg
WHERE status = 'cancelled';
```

Same transaction model: one logical write, one snapshot added. Underneath
Iceberg may use a **position-delete file** (cheaper for tiny deletes) or
a full data-file rewrite; Athena picks automatically based on the row
ratio. Either way, only matching rows vanish.

### Stage 5 — Time travel

```sql
-- Snapshot-based (exact):
SELECT * FROM orders_iceberg
FOR SYSTEM_VERSION AS OF '<snapshot-id>';

-- Timestamp-based (nearest earlier snapshot):
SELECT * FROM orders_iceberg
FOR SYSTEM_TIME AS OF '2026-09-27 12:00:00 UTC';
```

This is the killer feature: a query reads the table **exactly as it was**
at the named snapshot. Newer writes never leak into older reads. The
lab uses this to verify that snapshot 1 still has order 1001 with
status='placed' even after the UPDATE flipped it to 'shipped'.

### Stage 6 — `INSERT INTO`

```sql
INSERT INTO orders_iceberg
VALUES
  (2001, 42, '500.00', 'USD', '2026-09-27', 'placed'),
  (2002, 88, '75.00',  'EUR', '2026-09-27', 'placed');
```

Adds rows; one new snapshot per commit.

### Stage 7 — Metadata tables

Iceberg exposes virtual $-prefixed metadata tables you can `SELECT` like
any other table:

```
${table}$snapshots    -- one row per commit
${table}$history      -- older name for $snapshots
${table}$files        -- one row per data file (path, size, records)
${table}$manifests    -- one row per manifest file
${table}$partitions   -- partition-level stats
${table}$refs         -- branches and tags
```

The lab walks `$snapshots` (showing the CTAS + UPDATE + DELETE + INSERT
chain) and `$files` (showing the Parquet files Iceberg produced).

### Stage 8 — Snapshot isolation (the ACID guarantee)

Reading an old snapshot after newer writes is the textbook ACID test.
The lab's terminal stage reads snapshot 1 (the CTAS state) **after** the
INSERT and DELETE have happened, and asserts that snapshot 1 still shows
12 rows, none of them with `order_id >= 2000`, and the original `1003`
row still present. This is exactly what `FOR SYSTEM_VERSION AS OF` is
meant to give you — a permanent, immutable view of history.

## Traps the lab expects you to hit

- **Hive tables are NOT Iceberg tables.** Athena can read Hive tables
  and Iceberg tables from the same database, but DML (`UPDATE`,
  `DELETE`, `INSERT INTO`) only works on Iceberg. Trying
  `UPDATE orders_csv ...` fails with "DML is not supported for this
  table type".
- **Athena engine version matters.** Engine version 2 is Hive-only.
  Engine version 3 (pinned by the lab's workgroup) is the one with
  Iceberg support. Check the workgroup's `EngineVersion` before running
  any DML.
- **`UPDATE` produces multiple snapshots.** One logical UPDATE = one
  delete-snapshot + one append-snapshot. The lab's `$snapshots` table
  grows by two rows per UPDATE, not one.
- **`FOR SYSTEM_TIME AS OF` snaps to the nearest earlier snapshot.**
  You don't get the table at the exact instant you asked for; you get
  the most recent snapshot whose `timestamp_ms <= ts`. For millisecond-
  precise reads use `FOR SYSTEM_VERSION AS OF` with the snapshot ID.
- **`$snapshots` is a virtual table.** It is computed from the metadata
  JSON in S3 — no Glue/Athena state. A `SELECT COUNT(*) FROM
  orders_iceberg$snapshots` against the live cluster triggers an
  Iceberg metadata scan, not a data scan.
- **Athena is serverless but query results cost.** Each SELECT against
  a `$`-table scans metadata files in S3. Cheap (a few KB), but
  non-zero. Production dashboards querying `$snapshots` on every
  refresh add up.

## Going to production

Four things to add before this leaves a lab:

1. **Partition the Iceberg table by `order_date`**. Lab keeps the table
   unpartitioned; production should partition by a low-cardinality
   column. Iceberg supports `PARTITIONED BY` in CTAS.
2. **Compaction.** Long-running Iceberg tables accumulate small data
   files (one per write). Athena's `OPTIMIZE` table rewrite (engine v3)
   coalesces them. Run nightly.
3. **Schema evolution.** Iceberg handles `ALTER TABLE ADD COLUMN`
   natively — the data files don't rewrite, only the metadata JSON
   changes. The lab doesn't show this; production does it weekly.
4. **DML cost awareness.** Each UPDATE/DELETE copies the entire
   affected data file (copy-on-write). Bulk DELETEs via `MERGE INTO`
   with a delete-by-partition are cheaper when rows-per-partition is
   small.

## Verification

The lab's "lab complete" check is: a single Iceberg table named
`orders_iceberg` in the Glue database, with at least 5 snapshots in
`$snapshots` covering CTAS + UPDATE + DELETE + INSERT, and at least
one successful `FOR SYSTEM_VERSION AS OF` query showing the original
row count. The driver exercises all of those without AWS. The pytest
suite is the regression net. The shell scripts are the live-account
equivalent.
