# 3.9 — Restore Deleted Data

> **Section 3 · Running Queries with Various Query Settings · Lecture 3.13 · 4:09**

## 🎯 What you will learn

- The three recovery mechanisms: time travel, table snapshots, and undelete
- How to restore a dropped table, an overwritten table, and deleted rows
- The exact limits of each mechanism
- Building a recovery procedure you can actually rely on

---

## 🧠 Concept

BigQuery gives you three overlapping recovery mechanisms. Knowing which to use, and their
durations, is what makes an incident survivable.

| Mechanism | Scope | Window | Cost | Requires setup? |
|-----------|-------|--------|------|-----------------|
| **Time travel** (`FOR SYSTEM_TIME AS OF`) | Read a past state of a table | 7 days (table age) | Query cost | No |
| **Undelete** (`undelete`) | Recover a dropped table | 30 days | Free (metadata) | No |
| **Table snapshots** | Explicit point-in-time copy | Forever (until deleted) | Storage | Yes — must create them |
| **Streaming buffer** | Recent streaming inserts | ~7 days | None | No |

---

## 🧠 Time Travel

Every managed table in BigQuery retains its state for **7 days** (or the table's age, whichever is
shorter).

### Reading a past state

```sql
-- What did the table look like 3 hours ago?
SELECT COUNT(*) AS rows_3h_ago
FROM `YOUR_PROJECT_ID.curated.orders`
  FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR);

-- At an exact timestamp
SELECT *
FROM `YOUR_PROJECT_ID.curated.orders`
  FOR SYSTEM_TIME AS OF TIMESTAMP('2026-10-27 14:00:00 UTC')
LIMIT 100;
```

💡 **Time travel works on views, materialized views, and table snapshots too** — not just tables.

### Restoring a table

```sql
-- Restore the full table to its state 2 hours ago
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders`
AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

⚠️ **A `CREATE OR REPLACE` restore drops the current table's grants, labels, partitioning, and
clustering.** For a production table, restore into a new name and swap:

```sql
-- ✅ Safe restore + swap
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_restored`
AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;

-- Validate before swapping
SELECT
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_restored`) AS restored_rows,
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`)         AS current_rows;

-- Swap
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`      RENAME TO orders_broken;
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_restored` RENAME TO orders;
```

### Recovering specific deleted rows

```sql
-- Find rows that existed 1 hour ago but not now
SELECT
    old.order_id,
    old.customer_id,
    old.total_amount
FROM (
    SELECT order_id, customer_id, total_amount
    FROM `YOUR_PROJECT_ID.curated.orders`
      FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
) AS old
LEFT JOIN (
    SELECT order_id FROM `YOUR_PROJECT_ID.curated.orders`
) AS new
USING (order_id)
WHERE new.order_id IS NULL;
```

💡 **This "anti-join against time travel" pattern** is the standard way to recover a subset of
deleted rows without restoring the whole table.

---

## 🧠 Undelete

A dropped table is not immediately gone. BigQuery keeps it for **30 days**, and `UNDELTET` restores
it **free of charge** (it is a metadata operation).

```sql
-- Restore a dropped table
UNDELTET `YOUR_PROJECT_ID.curated.orders_deleted_at_20261027`;
```

```sql
-- Restore and give it a new name in one step
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders`
AS SELECT * FROM `YOUR_PROJECT_ID.curated.orders_deleted_at_20261027`;
```

```bash
# Undelete via the CLI
bq undelete YOUR_PROJECT_ID:curated.orders_deleted_at_20261027

# List deleted tables (in the trash)
bq ls --project_id=YOUR_PROJECT_ID --max_results=200 | grep -i deleted
```

⚠️ **The undelete window is 30 days** — but only if the table was *dropped*, not if the table's
project was deleted. And the name is still reserved, so a new table cannot take it until the
window expires or the table is purged.

---

## 🧠 Table Snapshots

Snapshots are explicit, permanent, point-in-time copies. Unlike time travel, they do not expire.

```sql
-- Create a snapshot
CREATE SNAPSHOT TABLE `YOUR_PROJECT_ID.curated.orders_snapshot_20261027`
FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR) AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;

-- Restore from a snapshot
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders`
AS SELECT * FROM `YOUR_PROJECT_ID.curated.orders_snapshot_20261027`;
```

### Automating snapshots

```sql
-- A scheduled query that keeps 30 days of daily snapshots
CREATE SCHEDULED QUERY `YOUR_PROJECT_ID.analytics.daily_snapshot`
OPTIONS (
  schedule = "0 1 * * *",
  time_zone = "UTC",
  destination_table = "YOUR_PROJECT_ID.backup.orders_daily",
  write_disposition = "WRITE_APPEND",
  maximum_bytes_billed = 10000000000
)
AS
SELECT
    CURRENT_DATE()       AS snapshot_date,
    order_id,
    customer_id,
    order_date,
    total_amount,
    status
FROM `YOUR_PROJECT_ID.curated.orders`;
```

⚠️ **`WRITE_APPEND` on a snapshot destination accumulates.** You must prune old snapshots
yourself, or use a partitioned table with `partition_expiration_days` so BigQuery handles it:

```sql
-- Better: a partitioned snapshot table with automatic expiry
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.backup.orders_snapshots`
PARTITION BY snapshot_date
OPTIONS (partition_expiration_days = 30)
AS
SELECT
    CURRENT_DATE() AS snapshot_date,
    *
FROM `YOUR_PROJECT_ID.curated.orders`;

-- Then the scheduled query appends to the current partition
CREATE SCHEDULED QUERY `YOUR_PROJECT_ID.analytics.daily_snapshot`
OPTIONS (
  schedule = "0 1 * * *",
  destination_table = "YOUR_PROJECT_ID.backup.orders_snapshots",
  write_disposition = "WRITE_APPEND",
  maximum_bytes_billed = 10000000000
)
AS
SELECT CURRENT_DATE() AS snapshot_date, *
FROM `YOUR_PROJECT_ID.curated.orders`;
```

---

## 🛠️ Hands-On: A Complete Recovery Drill

### Scenario

A pipeline ran `DELETE FROM orders WHERE order_date = '2026-10-27'` and removed 50,000 rows of
today's orders. Recover them.

### Step 1 — Assess

```sql
-- Confirm the damage
SELECT
    COUNT(*) AS current_rows,
    COUNTIF(order_date = CURRENT_DATE()) AS today_rows
FROM `YOUR_PROJECT_ID.curated.orders`;

-- What was the count 1 hour ago?
SELECT COUNT(*) AS rows_1h_ago
FROM `YOUR_PROJECT_ID.curated.orders`
  FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);
```

### Step 2 — Recover into a side table (never restore in place first)

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.recovery.orders_20261027_recovered`
AS
SELECT *
FROM `YOUR_PROJECT_ID.curated.orders`
  FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
WHERE order_date = DATE '2026-10-27';
```

### Step 3 — Validate

```sql
-- Row counts match the pre-delete state
SELECT
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID.recovery.orders_20261027_recovered`) AS recovered,
    (SELECT COUNT(*)
     FROM `YOUR_PROJECT_ID.curated.orders`
       FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
     WHERE order_date = DATE '2026-10-27') AS expected;

-- Checksum comparison
SELECT
    (SELECT SUM(total_amount) FROM `YOUR_PROJECT_ID.recovery.orders_20261027_recovered`) AS recovered_sum,
    (SELECT SUM(total_amount)
     FROM `YOUR_PROJECT_ID.curated.orders`
       FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
     WHERE order_date = DATE '2026-10-27') AS expected_sum;
```

### Step 4 — Merge the recovered rows back

```sql
MERGE `YOUR_PROJECT_ID.curated.orders` t
USING `YOUR_PROJECT_ID.recovery.orders_20261027_recovered` s
ON t.order_id = s.order_id
WHEN NOT MATCHED THEN
    INSERT (order_id, customer_id, order_date, total_amount, status)
    VALUES (s.order_id, s.customer_id, s.order_date, s.total_amount, s.status);
```

💡 **`MERGE` with only a `WHEN NOT MATCHED` clause is idempotent** — running it twice inserts
nothing the second time. This is the safe recovery pattern: re-runnable, no duplicates.

### Step 5 — Clean up

```sql
DROP TABLE `YOUR_PROJECT_ID.recovery.orders_20261027_recovered`;
```

---

## 🛠️ Recovery Reference

| Situation | Mechanism | Exact statement |
|-----------|-----------|-----------------|
| Rows deleted | Time travel + anti-join | `CREATE OR REPLACE TABLE x AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR) SELECT * FROM x` |
| Table dropped | Undelete | `UNDELTET \`proj.ds.table\`` |
| Table overwritten | Time travel | `CREATE OR REPLACE TABLE x AS OF ... SELECT * FROM x` |
| Table dropped >30 days ago | Snapshots (if taken) | `CREATE OR REPLACE TABLE x AS SELECT * FROM snapshot` |
| Schema broken | Time travel | `CREATE OR REPLACE TABLE x AS OF ... SELECT ... FROM x` |
| Bad data, no delete | Snapshot | `CREATE OR REPLACE TABLE x AS SELECT * FROM snapshot` |
| Need a permanent audit trail | Scheduled snapshots | Scheduled query → partitioned backup table |

---

## 💡 Production Notes

- **Time travel costs query fees** because restoring runs a query. Undelete is free.
- **Time travel requires the table to still exist.** If it was dropped, use undelete.
- **External tables have no time travel** — BigQuery does not own the files. If you need
  recoverability, snapshot the GCS bucket's object versions.
- **A 30-day undelete window means a dropped table's name is blocked** for 30 days. Name your
  drop-targets predictably.
- **Test your recovery procedure.** An untested backup is a hypothesis, not a backup. Run the drill
  quarterly in a non-production project.

---

## 🔑 Key Takeaways

- Three mechanisms: **time travel (7 days)**, **undelete (30 days, free)**, **snapshots (permanent)**.
- Restore into a **new table, validate, then swap** — never restore in place first.
- **`MERGE` with only `WHEN NOT MATCHED` is idempotent** — the safe recovery pattern.
- Time travel costs query fees; undelete does not.
- External tables have no time travel — protect them at the GCS layer.
- **Test recovery quarterly.** An untested backup is a hypothesis.

---

## 📚 Practice Exercises

1. **Recovery drill.** Run the full drill end-to-end on a scratch table: delete rows, recover them,
   validate, merge, and clean up. Record the actual timings and costs.

2. **Restore a dropped table.** Drop a table, wait, and restore it with `UNDELTET`. Then drop it
   again and restore it with a time-travel `CTAS` (which will fail — the table no longer exists).
   Explain the failure and the correct sequence.

3. **Snapshot strategy.** Design a snapshot scheme for a 20 TB warehouse that costs less than $100
   /month, provides 90 days of recovery, and requires no manual intervention. Include the exact
   DDL and the pruning mechanism.

4. **Runbook.** Write a one-page incident runbook for "someone deleted data from a BigQuery table"
   that a junior engineer can follow at 3am without escalation. Include decision points.

5. **Cost of the drill.** Write a query that estimates the monthly cost of time-travel-based
   recovery operations, based on `INFORMATION_SCHEMA.JOBS` for `CREATE TABLE AS SELECT` jobs
   against your own tables.

---

## 📖 Further Reading

- Time travel — https://cloud.google.com/bigquery/docs/time-travel
- Undelete — https://cloud.google.com/bigquery/docs/undelete-a-table
- Table snapshots — https://cloud.google.com/bigquery/docs/table-snapshots
