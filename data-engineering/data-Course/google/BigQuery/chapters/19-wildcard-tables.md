# 3.2 — Wildcard Tables

> **Section 3 · Running Queries with Various Query Settings · Lectures 3.3–3.4 · 8:10 + 4:01**

## 🎯 What you will learn

- The two wildcard syntaxes and the exact rules governing each
- Every limitation of wildcard tables — and the workarounds
- The correct way to query many daily tables
- When wildcard tables are *worse* than a single partitioned table

---

## 🧠 Concept

A **wildcard table** is a single table name that expands to many tables at query time. It saves you
from writing `UNION ALL` across fifty daily tables.

### Syntax 1 — Single wildcard (`_`)

Matches **exactly one** character in the table name.

```sql
-- Matches exactly ONE table
SELECT * FROM `YOUR_PROJECT_ID.raw.events_20260101`;
```

```
events_20260101  →  matches events_20260101        (exact)
events_2026010   →  does not match (9 chars, not 10)
events_202601011 →  does not match (11 chars)
```

### Syntax 2 — Double wildcard (`*`)

Matches **zero or more** characters.

```sql
-- Matches ALL tables starting with events_
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events_*`;
```

```
events_20260101  →  matches
events_20260102  →  matches
events_2026      →  matches
events_          →  matches
events           →  does NOT match (no trailing underscore)
```

### The combined form

```sql
-- The standard daily-partition pattern
SELECT
    DATE(REPLACE(table_id, 'events_', '')) AS event_date,
    COUNT(*) AS row_count
FROM `YOUR_PROJECT_ID.raw.events_*`
GROUP BY event_date
ORDER BY event_date;
```

### Using the `table_id` pseudo-column

Every wildcard expansion exposes a `table_id` column containing the full name of the underlying
table. This is the key to extracting metadata from the name.

```sql
-- The canonical daily-aggregate pattern
SELECT
    DATE(REPLACE(table_id, 'events_', '')) AS event_date,
    COUNT(*)                               AS total_events,
    COUNT(DISTINCT user_id)                AS unique_users
FROM `YOUR_PROJECT_ID.raw.events_*`
WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY event_date
ORDER BY event_date;
```

💡 **The `WHERE` on a wildcard table works per-expanded-table**, and — critically — **partition
filters are applied within each table**. This is the most important performance property of
wildcard tables.

---

## ⚠️ Limitations

This is where wildcard tables earn their reputation for being a trap.

### 1. No pruning of tables by size or age

A wildcard `events_*` expands to **all** matching tables, including a 3-year-old 2 TB table. You
cannot tell BigQuery "only the last 7 days" at the expansion level — only inside each table.

```sql
-- ❌ THIS SCANS EVERYTHING — the WHERE is inside each table, not on table selection
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events_*`;
```

### 2. No `_PARTITIONTIME` across the expansion

`_PARTITIONTIME` is per-table. Referencing it in a wildcard query works, but each table is
partitioned independently, and a table with no partitions contributes nothing.

### 3. The referenced tables are not the only ones read

BigQuery reads the **schema metadata** of every matching table, even those whose partitions are
fully pruned. With 10,000 daily tables, this metadata cost adds up.

### 4. LIMIT does not help

```sql
-- ❌ Reads everything, then returns 10 rows
SELECT * FROM `YOUR_PROJECT_ID.raw.events_*` LIMIT 10;
```

BigQuery cannot stop early because it does not know which table has the matching rows without
reading them.

### 5. Query cost equals the sum of all expanded tables

Three years of daily tables = 1,095 tables = the full cost of scanning all of them.

### 6. Schema differences cause errors

If two tables have different schemas, the wildcard query fails unless the differences are
compatible. BigQuery unions the schemas, but conflicting column types in the same position cause
an error.

### 7. `CREATE OR REPLACE TABLE AS` with a wildcard is dangerous

```sql
-- ⚠️ DANGEROUS: creates ONE table, but reads ALL matched tables
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.all_events`
AS SELECT * FROM `YOUR_PROJECT_ID.raw.events_*`;
```

This is legitimate but must be paired with careful filters.

---

## 🛠️ The right way: filter with a partition-aware predicate

```sql
-- ✅ CORRECT: filter on the pseudo-column of each table
SELECT
    DATE(REPLACE(table_id, 'events_', '')) AS event_date,
    COUNT(*) AS events
FROM `YOUR_PROJECT_ID.raw.events_*`
WHERE _PARTITIONTIME >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY event_date;
```

Wait — for ingestion-time partitioned tables, `_PARTITIONTIME` is available. But for
**date-column** partitioned tables, the partition column is the column itself:

```sql
-- ✅ CORRECT for DATE-column partitioned tables
SELECT
    DATE(REPLACE(table_id, 'events_', '')) AS event_date,
    COUNT(*) AS events
FROM `YOUR_PROJECT_ID.raw.events_*`
WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY event_date;
```

💡 **This is the correct mental model:** the wildcard expands to N tables, and then **each table
is pruned independently** by the predicate. If the predicate is on a partition column, the
partitions are pruned. If it is not, nothing is pruned and you pay for everything.

---

## 🧠 Wildcard tables vs a single partitioned table

| Aspect | Wildcard tables (many daily tables) | Single partitioned table |
|--------|-------------------------------------|--------------------------|
| Table count | Thousands | 1 |
| Metadata overhead | High (reads schema of every table) | None |
| Query planning | Slower | Faster |
| Partition pruning | Works, per table | Works |
| Ingestion | Simple — write one file per day | Simple — append to one table |
| Schema evolution | Per table, can diverge | Centralized |
| Table-level ACLs | Per table | One |
| Best for | Ingested file-per-day archives | Live, continuously-updated tables |

💡 **The modern recommendation is the single partitioned table.** BigQuery's partition management
(`partition_expiration_days`) does the retention work that used to require deleting files, and
`CREATE OR REPLACE TABLE ... PARTITION BY` makes schema evolution painless.

Use wildcard tables when:
- The data genuinely lives as separate files with separate schemas (an external lake)
- You are migrating from Parquet files in GCS before consolidating
- Different sources have genuinely different structures

---

## 🛠️ Hands-On

### 1. Create a set of daily tables

```sql
-- Simulate a daily-landing pattern
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.raw.events_20260101` AS
SELECT 1 AS event_id, 'click' AS event_type, 100 AS user_id, DATE '2026-01-01' AS event_date
UNION ALL SELECT 2, 'view', 101, DATE '2026-01-01';

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.raw.events_20260102` AS
SELECT 3 AS event_id, 'click' AS event_type, 102, DATE '2026-01-02'
UNION ALL SELECT 4, 'scroll', 103, DATE '2026-01-02';
```

### 2. Query with the single wildcard

```sql
-- Exactly one table matches
SELECT * FROM `YOUR_PROJECT_ID.raw.events_20260101`;
```

### 3. Query with the double wildcard

```sql
-- All matching tables
SELECT table_id, COUNT(*) AS rows
FROM `YOUR_PROJECT_ID.raw.events_*`
GROUP BY table_id;
```

### 4. The canonical daily rollup

```sql
-- ✅ The pattern you will use constantly
SELECT
    DATE(REPLACE(table_id, 'events_', '')) AS event_date,
    COUNT(*)                               AS total_events,
    COUNT(DISTINCT user_id)                AS unique_users,
    COUNTIF(event_type = 'click')          AS clicks
FROM `YOUR_PROJECT_ID.raw.events_*`
GROUP BY event_date
ORDER BY event_date;
```

### 5. List all matching tables first (a good habit)

```sql
-- Inspect the expansion before running an expensive query
SELECT
    table_id,
    ROUND(size_bytes / POW(1024, 2), 2) AS size_mb,
    row_count,
    creation_time
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES`
WHERE table_id LIKE 'raw.events_%'
ORDER BY table_id DESC
LIMIT 30;
```

💡 **Always inspect the expansion before a wildcard query over thousands of tables.** A single
accidentally-matching table can triple your query cost.

### 6. Wildcard over external Parquet files

```sql
-- Query many Parquet files in GCS without creating tables
SELECT
    REGEXP_EXTRACT(TO_JSON_STRING(TABLE_SUFFIX), r'(\d{4}-\d{2}-\d{2})') AS event_date,
    COUNT(*) AS rows
FROM `gs://YOUR_PROJECT_ID-bq-course/raw/events_*.parquet`
GROUP BY event_date;
```

---

## 💡 Production Notes

- **Wildcard expansion cost grows with table count.** At ~10,000 tables, query planning itself
  becomes measurably slow. Consolidate.
- **Never use a wildcard against a table prefix you do not control.** `events_*` will match
  `events_debug`, `events_v2_test`, and `events_backup_old`. Use explicit, well-structured naming.
- **`REPLACE(table_id, 'prefix_', '')` is brittle.** A `REGEXP_EXTRACT` with a date pattern is
  safer, because it only matches actual dates and ignores non-conforming table names.

---

## 🔑 Key Takeaways

- `_` matches exactly one character; `*` matches zero or more.
- The `table_id` pseudo-column exposes the expanded table's name — use it to extract dates.
- **Predicates inside the wildcard query prune each expanded table's partitions** — this is how
  you keep wildcard queries affordable.
- Wildcards have no cross-table pruning, no early `LIMIT`, and cost = sum of all expanded tables.
- **Prefer a single partitioned table** with `partition_expiration_days` for new designs.
- Inspect the expansion via `INFORMATION_SCHEMA.TABLES` before running an expensive wildcard query.

---

## 📚 Practice Exercises

1. **Wildcard to partition migration.** You have 1,095 daily tables in `raw.events_*`. Design the
   migration to a single partitioned table, including the exact SQL, the cutover plan, and the
   rollback.

2. **Cost comparison.** Measure the actual cost of:
   (a) `SELECT COUNT(*) FROM raw.events_*`
   (b) The same with a partition filter
   (c) The same against a single partitioned table
   Record bytes processed in each case.

3. **Prefix hazard.** Your naming convention is `events_YYYYMMDD`. Someone creates a table called
   `events_backup_2026`. Write a wildcard query that only matches the correct tables regardless
   of what else exists.

4. **Metadata cost.** Research how wildcard expansion scales with table count. Design a monitor
   that warns when any table prefix exceeds N tables.

---

## 📖 Further Reading

- Wildcard tables — https://cloud.google.com/bigquery/docs/wildcard-tables
- Table decorators — https://cloud.google.com/bigquery/docs/table-decorators
- INFORMATION_SCHEMA.TABLES — https://cloud.google.com/bigquery/docs/information-schema-tables
