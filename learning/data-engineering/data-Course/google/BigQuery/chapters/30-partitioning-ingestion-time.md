# 4.4 — Ingestion-Time Partitioned Tables

> **Section 4 · Partitioning & Clustering · Lecture 4.4 · 9:22**

## 🎯 What you will learn

- How ingestion-time partitioning works
- The `_PARTITIONTIME` pseudo-column and its rules
- `__PARTITIONS_SUMMARY__` and the partition metadata tables
- `partition_expiration_days` and the partition lifecycle
- When to use ingestion-time vs date-column partitioning

---

## 🧠 Concept

Ingestion-time partitioning automatically routes each row to a partition based on **when it was
loaded**. It requires no schema change and no column.

### Creating one

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.raw.events_it`
PARTITION BY DATE(_PARTITIONTIME)
AS
SELECT * FROM `YOUR_PROJECT_ID.raw.events`;
```

```bash
bq mk --table \
  --time_partitioning_type=DAY \
  --time_partitioning_field=_PARTITIONTIME \
  YOUR_PROJECT_ID:raw.events_it
```

💡 **The partition column is `_PARTITIONTIME`, a pseudo-column.** It is populated by BigQuery at
load time and cannot be written to directly. If you need the *business* event date, use a
date-column partition instead.

### The `_PARTITIONTIME` rules

| Rule | Detail |
|------|--------|
| Value | The **UTC** timestamp of when the row was loaded |
| Granularity | `DAY` (default) or `HOUR` |
| Readable in queries | ✅ Yes, as `_PARTITIONTIME` |
| Writable by the user | ❌ No — inserts cannot set it |
| Filterable | ✅ Yes |
| Available in `SELECT *` | ❌ No — must be referenced explicitly |
| `NULL` | Never — every row has a partition |

```sql
-- Read it explicitly
SELECT
    _PARTITIONTIME                AS load_time,
    DATE(_PARTITIONTIME)          AS load_date,
    event_id,
    event_type
FROM `YOUR_PROJECT_ID.raw.events_it`
LIMIT 10;
```

⚠️ **The partition column is NOT included in `SELECT *`.** This surprises people. You must name
`_PARTITIONTIME` explicitly.

### `_PARTITIONDATE`

A convenience pseudo-column holding just the date part.

```sql
SELECT
    _PARTITIONDATE AS load_date,
    COUNT(*)
FROM `YOUR_PROJECT_ID.raw.events_it`
WHERE _PARTITIONDATE = DATE '2026-10-01'
GROUP BY load_date;
```

---

## 🧠 Partition Metadata Tables

Every partitioned table exposes special `INFORMATION_SCHEMA` views.

### `__PARTITIONS_SUMMARY__`

```sql
SELECT
    partition_id,
    total_rows,
    total_logical_bytes,
    ROUND(total_logical_bytes / POW(1024, 3), 2) AS size_gb
FROM `YOUR_PROJECT_ID.raw.events_it.__PARTITIONS_SUMMARY__`
ORDER BY partition_id DESC
LIMIT 30;
```

### `__PARTITIONS__`

The same, but **one row per partition per file** — more granular, useful for finding which file
holds a specific row.

```sql
-- Which file holds the row with this event_id?
SELECT
    partition_id,
    file_id,
    row_count,
    ROUND(total_logical_bytes / POW(1024, 2), 2) AS size_mb
FROM `YOUR_PROJECT_ID.raw.events_it.__PARTITIONS__`
WHERE partition_id = '20261001';
```

💡 **`__PARTITIONS__` is the tool for pinpointing data location.** It tells you exactly which
file contains a specific row — invaluable when investigating a bad load or a specific incident.

---

## 🧠 Partition Expiration

This is the mechanism that keeps partition counts (and storage costs) under control.

```sql
-- Drop partitions older than 30 days, automatically
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.raw.events_it`
PARTITION BY DATE(_PARTITIONTIME)
OPTIONS (
  partition_expiration_days = 30
)
AS SELECT * FROM `YOUR_PROJECT_ID.raw.events_it`;
```

```bash
bq mk --table \
  --time_partitioning_type=DAY \
  --time_partitioning_field=_PARTITIONTIME \
  --partition_expiration_days=30 \
  YOUR_PROJECT_ID:raw.events_it_exp
```

### How it works

```
Day 0:   load into partition 20261027
Day 1:   load into partition 20261028
...
Day 30:  partition 20260927 is DROPPED automatically
```

⚠️ **Expiration is evaluated on partition age, not on row age.** And the expiration clock starts
when the partition is created, not when the data arrives.

⚠️ **Changing `partition_expiration_days` rewrites the table.** Set it correctly the first time.

### Manually dropping a partition

```sql
-- Delete a specific partition
ALTER TABLE `YOUR_PROJECT_ID.raw.events_it`
DROP PARTITION _PARTITIONDATE = '20260101';

-- Drop a range
ALTER TABLE `YOUR_PROJECT_ID.raw.events_it`
DROP PARTITION _PARTITIONDATE < '20260101';
```

```bash
bq rm --partition_filter=_PARTITIONDATE=20260101 \
  YOUR_PROJECT_ID:raw.events_it
```

💡 **Manual partition drops are the fastest way to recover storage cost** — the data is deleted
immediately rather than waiting for the expiration sweep.

---

## 🧠 Ingestion-time vs date-column partitioning

| Aspect | Ingestion-time | Date column |
|--------|---------------|-------------|
| Partition key | `_PARTITIONTIME` | Your own DATE/TIMESTAMP column |
| Granularity | DAY or HOUR | DAY (or the column's natural grain) |
| Set by | BigQuery at load | You, in the data |
| Late-arriving data | Lands in the *load* partition, not the event-date partition | Lands in the correct event-date partition |
| Requires a column | ❌ No | ✅ Yes |
| Business reporting | ❌ Load date ≠ event date | ✅ Correct |
| Schema change needed | ❌ No | ✅ Yes |

### The late-arriving data problem

This is the decisive difference.

```sql
-- Ingestion-time: a 2026-01-05 event loaded on 2026-01-10
-- lands in partition 20260110
SELECT _PARTITIONDATE, event_id, event_ts
FROM `YOUR_PROJECT_ID.raw.events_it`
WHERE event_id = 'e_2026_01_05_late';
-- → partition 20260110, but event_ts is 2026-01-05
```

```sql
-- Date-column: the same event lands in partition 20260105
SELECT order_date, event_id
FROM `YOUR_PROJECT_ID.raw.events_partitioned`
WHERE event_id = 'e_2026_01_05_late';
-- → partition 20260105 ✓
```

💡 **Use ingestion-time when:**
- The data has no meaningful business date
- You are doing a pure append-only archive of raw events
- You want zero schema effort
- Load order *is* the business meaning (e.g. "what arrived today")

💡 **Use date-column partitioning when:**
- You report on business dates (almost always)
- Late-arriving data is common
- You need the partition to match a business dimension
- You want to join on the partition key

⚠️ **Most production use cases want date-column partitioning.** Ingestion-time is a convenience for
raw landing zones where you will transform into a date-partitioned curated table anyway.

---

## 🛠️ Hands-On

### 1. Create and load

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.raw.events_it`
PARTITION BY DATE(_PARTITIONTIME)
OPTIONS (
  description = "Raw events partitioned by load time",
  partition_expiration_days = 30,
  labels = [('tier', 'raw')]
);
```

```bash
# Load three daily files — each goes into its own partition
bq load --source_format=CSV --autodetect --replace \
  YOUR_PROJECT_ID:raw.events_it gs://YOUR_PROJECT_ID-bq-course/staging/events_2026-10-01.csv

bq load --source_format=CSV --autodetect --replace \
  YOUR_PROJECT_ID:raw.events_it gs://YOUR_PROJECT_ID-bq-course/staging/events_2026-10-02.csv
```

⚠️ **Careful: `--replace` with a partitioned table.** `--replace` truncates the *entire table*,
not just the target partition. Use `--replace` only when you intend to reload everything, or load
into a specific partition using a partition decorator.

```bash
# Load into a SPECIFIC partition (safe for incremental loads)
bq load --source_format=CSV --autodetect \
  YOUR_PROJECT_ID:raw.events_it$__PARTITIONS_SUMMARY__ \
  gs://YOUR_PROJECT_ID-bq-course/staging/events_2026-10-03.csv
```

💡 **Loading into a specific partition** is the correct pattern for daily incremental loads. It
makes the load idempotent — re-running the same load replaces only that day's data.

### 2. Inspect the partitions

```sql
SELECT
    partition_id,
    total_rows,
    ROUND(total_logical_bytes / POW(1024, 2), 2) AS size_mb
FROM `YOUR_PROJECT_ID.raw.events_it.__PARTITIONS_SUMMARY__`
ORDER BY partition_id;
```

### 3. Query with pruning

```sql
-- Prunes
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events_it`
WHERE _PARTITIONDATE = DATE '2026-10-01';

-- Prunes
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events_it`
WHERE _PARTITIONTIME >= TIMESTAMP '2026-10-01 00:00:00 UTC'
  AND _PARTITIONTIME <  TIMESTAMP '2026-10-03 00:00:00 UTC';
```

### 4. The partition decorator

```sql
-- Query a single partition directly
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events_it$20261001`;

-- A partition range
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events_it$20261001:20261002`;

-- The latest partition
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events_it$__PARTITIONS_SUMMARY__` LIMIT 1;
```

```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events_it$20261001`'
```

### 5. Hourly partitioning

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.raw.events_hourly`
PARTITION BY TIMESTAMP_TRUNC(_PARTITIONTIME, HOUR)
OPTIONS (partition_expiration_days = 7)
AS SELECT * FROM `YOUR_PROJECT_ID.raw.events_it`;
```

```sql
-- Query one hour
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events_hourly`
WHERE _PARTITIONTIME = TIMESTAMP '2026-10-01 14:00:00 UTC';
```

⚠️ **Hourly partitions = 24 per day.** With a 10,000-partition limit, you get **416 days** of
history. Set `partition_expiration_days` accordingly (7–30).

### 6. Drop a partition manually

```sql
-- Free the storage immediately
ALTER TABLE `YOUR_PROJECT_ID.raw.events_it`
DROP PARTITION _PARTITIONDATE = '20260101';

-- Verify
SELECT COUNT(*) AS remaining_partitions
FROM `YOUR_PROJECT_ID.raw.events_it.__PARTITIONS_SUMMARY__`;
```

---

## 💡 Production Notes

- **The 30-day time-travel window and ingestion-time partitions interact.** Time travel on a
  table whose partitions have expired cannot recover expired data. Your real retention is
  `min(partition_expiration_days, 7 days of time travel)`.
- **`--replace` on a partitioned table truncates everything.** Use partition decorators for
  incremental loads.
- **`__PARTITIONS__` is your forensic tool.** Use it to find exactly which file holds a specific
  row when investigating a data issue.
- **Ingestion-time partitioning is a good fit for a raw landing zone** that you later transform
  into a date-partitioned curated table. It decouples "when did it arrive" from "when did it
  happen".

---

## 🔑 Key Takeaways

- Ingestion-time partitioning routes rows by **load time**; `_PARTITIONTIME` is a read-only
  pseudo-column, and it is **not** in `SELECT *`.
- `__PARTITIONS_SUMMARY__` and `__PARTITIONS__` expose partition and file-level metadata.
- `partition_expiration_days` is the automatic defense against the 10,000-partition limit.
- **Ingestion-time is wrong for business-date reporting** because late arrivals land in the wrong
  partition.
- Load into a **specific partition** with a partition decorator for idempotent incremental loads.
- `--replace` truncates the whole table — not just one partition.

---

## 📚 Practice Exercises

1. **Late-arriving data.** Design a load process for events that can arrive up to 30 days late.
   Compare ingestion-time and date-column partitioning. Which does the business need, and why?

2. **Partition decorator design.** Write a load script (bash) that loads a daily file into a
   specific partition, is idempotent, and handles failure. Include a verification step.

3. **Partition forensics.** Using `__PARTITIONS__`, write a query that finds which file contains
   a given `event_id`. Then write the procedure to read just that file's contents.

4. **Hourly vs daily.** A table receives 2M events/hour. Compare hourly and daily partitioning on:
   partition count over 12 months, pruning granularity, storage overhead, and cost.

5. **Expiration audit.** Write a query that lists every partitioned table in a project along with
   its `partition_expiration_days`, its current partition count, and a projection of when it will
   hit the 10,000 limit. Make it a daily alert.

---

## 📖 Further Reading

- Ingestion-time partitioned tables — https://cloud.google.com/bigquery/docs/partitioned-tables#ingestion_time
- Partition metadata — https://cloud.google.com/bigquery/docs/partitioned-tables#metadata
- Partition decorators — https://cloud.google.com/bigquery/docs/table-decorators
