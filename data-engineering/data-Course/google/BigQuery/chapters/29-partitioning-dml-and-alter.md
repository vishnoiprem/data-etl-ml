# 4.6 — ALTER, COPY & DML on Partitioned Tables

> **Section 4 · Partitioning & Clustering · Lecture 4.7 · 5:25**

## 🎯 What you will learn

- How to add, drop, and replace partitions
- How DML interacts with partitioning — and why it is expensive
- `MERGE` patterns on partitioned tables
- Copy and snapshot operations on partitioned tables
- The rules for DML and partition filters

---

## 🧠 Concept

DML on BigQuery mutates data **in place** by rewriting the affected blocks. On a partitioned table,
this has specific consequences you need to understand.

### The DML operations

| Operation | Type | Cost | Notes |
|-----------|------|------|-------|
| `INSERT` | Row-level append | Write only | Fast, especially with streaming |
| `UPDATE` | Row-level modify | **Rewrites affected blocks** | Expensive on large ranges |
| `DELETE` | Row-level remove | **Rewrites affected blocks** | Expensive on large ranges |
| `MERGE` | Insert + update + delete | **Rewrites affected blocks** | The workhorse |

💡 **The key concept: BigQuery DML rewrites whole blocks, not individual rows.** If you update
one row, BigQuery rewrites the entire block (typically 100–500 MB) containing that row. This is
why a "small" update on a huge table can cost hundreds of dollars.

### DML and partitioning interact well — when you use partition filters

```sql
-- ✅ Cheap: the affected rows are in one partition
UPDATE `YOUR_PROJECT_ID.curated.orders_dp`
SET status = 'cancelled'
WHERE order_date = DATE '2026-01-15' AND status = 'pending';

-- ❌ Expensive: touches every partition
UPDATE `YOUR_PROJECT_ID.curated.orders_dp`
SET status = 'cancelled'
WHERE status = 'pending';
```

💡 **Always scope DML to a partition.** It reduces both the number of blocks rewritten and the
risk of an accidental full-table mutation.

---

## 🧠 Partition management

### Dropping a partition

```sql
-- By date
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_dp`
DROP PARTITION order_date = DATE '20260101';

-- By a range
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_dp`
DROP PARTITION order_date < DATE '20260101';

-- By pseudo-column (ingestion-time)
ALTER TABLE `YOUR_PROJECT_ID.raw.events_it`
DROP PARTITION _PARTITIONDATE = '20260101';
```

```bash
bq rm --partition_filter=order_date=20260101 \
  YOUR_PROJECT_ID:curated.orders_dp
```

⚠️ **Dropping a partition deletes the data immediately** and cannot be undone (not even by time
travel — the partition is gone).

### Replacing a partition

```sql
-- Replace one day's data atomically
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_dp`
REPLACE PARTITION order_date = DATE '2026-01-15'
AS SELECT * FROM `YOUR_PROJECT_ID.staging.orders_20260115`;
```

💡 **`REPLACE PARTITION` is the idempotent re-load pattern.** It atomically swaps a day's data —
perfect for correcting a bad load or re-running a pipeline. No duplicates, no gaps, and it is
safer than `DELETE` + `INSERT`.

```sql
-- The bad way
DELETE FROM `YOUR_PROJECT_ID.curated.orders_dp` WHERE order_date = DATE '2026-01-15';
INSERT INTO `YOUR_PROJECT_ID.curated.orders_dp` SELECT * FROM `YOUR_PROJECT_ID.staging.orders_20260115`;
-- ❌ Not atomic — a failure between the two leaves the partition empty
```

### Adding a partition explicitly

```sql
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_dp`
ADD PARTITION order_date = DATE '2026-01-15';
```

---

## 🧠 MERGE on partitioned tables

`MERGE` is the operation you will use most in production pipelines.

```sql
-- The canonical incremental upsert
MERGE `YOUR_PROJECT_ID.curated.orders_dp` AS t
USING (
    SELECT *
    FROM `YOUR_PROJECT_ID.staging.orders_delta`
    WHERE order_date = DATE '2026-01-15'      -- scope the source
) AS s
ON t.order_date = s.order_date
  AND t.order_id = s.order_id
WHEN MATCHED THEN
    UPDATE SET
        total_amount = s.total_amount,
        status       = s.status,
        updated_at   = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (order_date, order_id, customer_id, total_amount, status)
    VALUES (s.order_date, s.order_id, s.customer_id, s.total_amount, s.status);
```

⚠️ **The `ON` clause must include the partition key.** Without it, BigQuery must scan every
partition to find matches — destroying the performance benefit of partitioning.

```sql
-- ❌ Slow: the join key alone forces a full scan of all partitions
ON t.order_id = s.order_id

-- ✅ Fast: partition key first
ON t.order_date = s.order_date AND t.order_id = s.order_id
```

💡 **The `MERGE` partition-key rule applies to the `ON` clause, not the `USING` clause.** The
`USING` subquery should also be partition-filtered, but the critical one is `ON` — that is what
determines which partitions BigQuery must touch.

### Idempotent MERGE patterns

```sql
-- Pattern 1: Only insert missing rows (never updates)
-- Idempotent by construction
MERGE `YOUR_PROJECT_ID.curated.orders_dp` t
USING (SELECT * FROM `YOUR_PROJECT_ID.staging.orders_delta`) s
ON t.order_date = s.order_date AND t.order_id = s.order_id
WHEN NOT MATCHED THEN INSERT (order_date, order_id, customer_id, total_amount)
VALUES (s.order_date, s.order_id, s.customer_id, s.total_amount);
```

```sql
-- Pattern 2: Full upsert (update + insert)
-- Idempotent as long as the source is a complete picture of the partition
MERGE `YOUR_PROJECT_ID.curated.orders_dp` t
USING (SELECT * FROM `YOUR_PROJECT_ID.staging.orders_delta`) s
ON t.order_date = s.order_date AND t.order_id = s.order_id
WHEN MATCHED THEN UPDATE SET total_amount = s.total_amount, status = s.status
WHEN NOT MATCHED THEN INSERT (order_date, order_id, customer_id, total_amount, status)
VALUES (s.order_date, s.order_id, s.customer_id, s.total_amount, s.status);
```

```sql
-- Pattern 3: Delete + insert for a full-partition refresh
-- Idempotent, and cheaper than row-level DML
BEGIN
    DELETE FROM `YOUR_PROJECT_ID.curated.orders_dp` WHERE order_date = DATE '2026-01-15';
    INSERT INTO `YOUR_PROJECT_ID.curated.orders_dp` (order_date, order_id, customer_id, total_amount)
    SELECT order_date, order_id, customer_id, total_amount
    FROM `YOUR_PROJECT_ID.staging.orders_20260115`;
END;
```

💡 **Pattern 3 is the best for daily full-refresh partitions.** It is simple, idempotent, and
avoids the row-matching cost of `MERGE` entirely. The only downside is that it writes the whole
partition rather than just the changed rows.

---

## 🧠 COPY and snapshots on partitioned tables

```sql
-- Copy preserves partitioning and clustering
CREATE TABLE `YOUR_PROJECT_ID.backup.orders_backup`
COPY `YOUR_PROJECT_ID.curated.orders_dp`;

-- Snapshot preserves partitioning too
CREATE SNAPSHOT TABLE `YOUR_PROJECT_ID.backup.orders_snapshot`
FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY) AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders_dp`;
```

```bash
# Copy a single partition
bq cp \
  YOUR_PROJECT_ID:curated.orders_dp\$20260115 \
  YOUR_PROJECT_ID:backup.orders_20260115
```

⚠️ **Copying a table with `partition_expiration_days` set** — the copy inherits the option, and
its partitions will start expiring on the copy's own schedule. Usually you want to *remove*
expiration on a backup.

```sql
-- Remove expiration on the backup
ALTER TABLE `YOUR_PROJECT_ID.backup.orders_backup`
SET OPTIONS (partition_expiration_days = NULL);
```

⚠️ **Changing `partition_expiration_days` rewrites the table.** For a large backup, accept the
default or recreate the backup with the correct options.

---

## 🛠️ Hands-On

### 1. Demonstrate the DML cost difference

```sql
-- ❌ Expensive: no partition filter
UPDATE `YOUR_PROJECT_ID.curated.orders_dp`
SET status = 'reviewed'
WHERE status = 'pending';

-- ✅ Cheap: partition-scoped
UPDATE `YOUR_PROJECT_ID.curated.orders_dp`
SET status = 'reviewed'
WHERE order_date = DATE '2026-01-15' AND status = 'pending';
```

```sql
-- Compare
SELECT
    job_id,
    total_bytes_processed,
    ROUND((total_bytes_processed / POW(1024, 3)), 2) AS mb_rewritten,
    ROUND(total_slot_ms / 1000, 2) AS slot_seconds,
    SUBSTR(query, 1, 80) AS query_head
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'UPDATE'
ORDER BY creation_time DESC
LIMIT 10;
```

### 2. REPLACE PARTITION — the idempotent reload

```sql
-- Stage the corrected data
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.staging.orders_correction` AS
SELECT
    order_date, order_id, customer_id,
    total_amount * 0.9 AS total_amount,   -- 10% correction
    status
FROM `YOUR_PROJECT_ID.curated.orders_dp`
WHERE order_date = DATE '2026-01-15';

-- Atomically replace the partition
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_dp`
REPLACE PARTITION order_date = DATE '2026-01-15'
AS SELECT * FROM `YOUR_PROJECT_ID.staging.orders_correction`;

-- Verify
SELECT SUM(total_amount) FROM `YOUR_PROJECT_ID.curated.orders_dp`
WHERE order_date = DATE '2026-01-15';
```

### 3. A full daily pipeline in one script

```sql
DECLARE target_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY);
DECLARE rows_affected INT64 DEFAULT 0;

BEGIN
    -- 1. Load today's delta into staging
    EXECUTE IMMEDIATE FORMAT(
        "CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.staging.orders_delta`
         PARTITION BY order_date
         AS SELECT * FROM `YOUR_PROJECT_ID.staging.orders_raw`
         WHERE order_date = @d", target_date
    ) USING target_date;

    -- 2. Count what we are about to change
    EXECUTE IMMEDIATE FORMAT(
        "SELECT COUNT(*) FROM `YOUR_PROJECT_ID.staging.orders_delta`"
    ) INTO rows_affected;

    -- 3. Upsert
    EXECUTE IMMEDIATE FORMAT(
        "MERGE `YOUR_PROJECT_ID.curated.orders_dp` t
         USING `YOUR_PROJECT_ID.staging.orders_delta` s
         ON t.order_date = s.order_date AND t.order_id = s.order_id
         WHEN MATCHED THEN UPDATE SET
             total_amount = s.total_amount, status = s.status
         WHEN NOT MATCHED THEN INSERT
             (order_date, order_id, customer_id, total_amount, status)
         VALUES (s.order_date, s.order_id, s.customer_id, s.total_amount, s.status)"
    );

    -- 4. Log
    SELECT FORMAT('Merged %d rows for %s', rows_affected, target_date) AS log;
END;
```

### 4. Copy a single partition

```bash
bq cp \
  'YOUR_PROJECT_ID:curated.orders_dp$20260115' \
  YOUR_PROJECT_ID:backup.orders_20260115
```

---

## 💡 Production Notes

- **DML is not transactional across statements** unless you wrap it in `BEGIN ... END`. Use
  `BEGIN/END` for multi-statement DML so a failure rolls back.
- **`MERGE` requires the source to be deduplicated on the `ON` key.** If the source has two rows
  with the same key, BigQuery raises an error. Deduplicate the source first.
- **DML on a table with `require_partition_filter = TRUE` must include a partition filter** — this
  is a feature. It makes a catastrophic full-table `UPDATE` impossible.
- **Streaming inserts are much cheaper than DML** for appending new rows, because they do not
  rewrite existing blocks.
- **Batch DML** (`batched` insert/update/delete) is faster than row-level DML for large
  operations.

```python
# Batched DML in Python
from google.cloud import bigquery

client = bigquery.Client()
config = bigquery.QueryJobConfig()
config.dml_batch_size = 1000        # rows per batch
config.maximum_bytes_billed = 10 * 1024**4

client.query(
    "UPDATE `proj.curated.orders` SET status = 'reviewed' WHERE order_date = @d",
    job_config=config,
    query_parameters=[bigquery.ScalarQueryParameter("d", "DATE", "2026-01-15")],
).result()
```

---

## 🔑 Key Takeaways

- **BigQuery DML rewrites whole blocks**, not rows — a small update on a huge table is expensive.
- **Always scope DML to a partition**, and always include the partition key in `MERGE`'s `ON`
  clause.
- **`REPLACE PARTITION` is the correct idempotent reload pattern** — atomic, no duplicates, no
  gaps.
- Copy and snapshot operations preserve partitioning and clustering.
- Watch `partition_expiration_days` when copying a table to a backup.
- Use `BEGIN ... END` for transactional multi-statement DML.

---

## 📚 Practice Exercises

1. **DML cost analysis.** On a 10 TB, 365-partition table, measure the actual cost of:
   (a) updating 1 row, (b) updating 1,000 rows in one partition, (c) updating 1,000 rows spread
   over 100 partitions, (d) updating 1% of the table. Explain the block-rewrite mechanics.

2. **Reload patterns.** Design three reload procedures for a daily partition: (a) a full refresh,
   (b) a delta upsert, (c) a delta with deletions. For each, state the SQL, the idempotency
   property, and the failure recovery path.

3. **MERGE correctness.** Your source table has duplicate `order_id` values within a partition.
   Write the query that detects the duplication, and the dedup query that produces a valid MERGE
   source. Which dedup rule is correct — `ROW_NUMBER() = 1`, or "keep the latest"?

4. **Pipeline script.** Write a complete, transactional daily pipeline as a single SQL script:
   stage → validate → merge → rebuild aggregates → log. Include validation that aborts on
   quality failures.

5. **Backup expiry.** A backup table was copied from a table with `partition_expiration_days = 90`.
   Write the procedure to make the backup permanent, and explain the cost of each option.

---

## 📖 Further Reading

- DML statements — https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax
- Partition management — https://cloud.google.com/bigquery/docs/managing-partitions
- `MERGE` — https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#merge_statement
