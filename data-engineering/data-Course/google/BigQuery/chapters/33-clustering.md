# 4.8 — Clustering

> **Section 4 · Partitioning & Clustering · Lectures 4.9–4.10 · 4:42 + 2:54**

## 🎯 What you will learn

- What clustering does that partitioning cannot
- How BigQuery sorts and blocks clustered data
- The cost, limits, and maintenance of clustering
- When clustering is worth it and when it is not

---

## 🧠 Concept

Clustering organizes table data by the values of one or more columns, so BigQuery can skip whole
**blocks** when your filters match.

### Partitioning vs Clustering

| | Partitioning | Clustering |
|---|---|---|
| **Organizes by** | Date or integer range | Column values (sorted) |
| **Prunes at** | Partition level | Block level, within a partition |
| **Maximum columns** | 1 | 4 |
| **Improves over time?** | ❌ No | ✅ Yes — re-clustered automatically |
| **Cost to apply** | One-time at creation | One-time at creation, then free |
| **Storage overhead** | Minimal | ~5–20% |
| **Best for** | Time-range filters | Equality and range filters on high-cardinality columns |

💡 **They solve different problems.** Partitioning says "I only want January." Clustering says
"within January, I only want customer 12345."

### How clustering works internally

```
Without clustering — blocks are arbitrary:
┌────────┬────────┬────────┬────────┐
│ rows   │ rows   │ rows   │ rows   │   ← a filter on customer_id must read
│ 1-5000 │ 5001-  │ 10001- │ 15001- │     EVERY block that might contain it
│        │ 10000  │ 15000  │ 20000  │
└────────┴────────┴────────┴────────┘

With CLUSTER BY customer_id — blocks are sorted:
┌────────┬────────┬────────┬────────┐
│ cust   │ cust   │ cust   │ cust   │
│ 00001- │ 00005- │ 00009- │ 00013- │
│ 00004  │ 00008  │ 00012  │ 00016  │
└────────┴────────┴────────┴────────┘
   ▲
   └── A filter on customer_id = '00003' skips blocks 2, 3, 4
```

### The sorting is lexicographic

For strings, clustering sorts in **byte order**, not numeric order:

```
'cust_10' < 'cust_2'    ← because '1' (0x31) < '2' (0x32)
```

This matters for range filters on string columns. A filter like `customer_id BETWEEN 'cust_100'
AND 'cust_200'` will scan a wider range than expected.

💡 **Zero-pad numeric identifiers if you cluster on them as strings.** `cust_000123` sorts
correctly; `cust_123` does not.

### BigQuery re-clusters automatically

This is clustering's most important and least-known property:

- Data is stored in **sort blocks**, sorted by the clustering columns
- Each block holds up to **~10,000 distinct values** per clustering column
- When data is written, it is placed into the correct sorted position
- **BigQuery periodically re-clusters in the background** to merge small blocks

💡 **Clustering improves over time, without you doing anything.** A table with poor clustering
today may be well-clustered next month, because the background re-clustering job merges blocks.

⚠️ **This is not instant.** Do not cluster a table today and expect a query to be fast right
away — especially for a freshly loaded table.

---

## 🧠 The Rules

### Limits

| Rule | Value |
|------|-------|
| Maximum clustering columns | **4** |
| Column types allowed | `DATE`, `BOOL`, `INT64`, `STRING`, `FLOAT64`, `NUMERIC`, `TIMESTAMP`, `DATETIME`, `GEOGRAPHY` |
| `ARRAY`/`STRUCT` columns | ❌ Not allowed as a clustering column (but a field *inside* a struct can be) |
| Maximum partition columns | 1 |

### Ordering matters

```sql
-- Clustering columns are ordered by selectivity
CLUSTER BY customer_id, status
```

💡 **Order clustering columns from most selective to least selective.** The first column is the
primary sort key. If `customer_id` is highly selective (millions of distinct values) and `status`
has 5 values, put `customer_id` first.

---

## 🛠️ Hands-On

### 1. Create a clustered table

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_clustered`
PARTITION BY order_date
CLUSTER BY customer_id, status
OPTIONS (
  description = "Orders clustered by customer and status",
  partition_expiration_days = 730,
  require_partition_filter = TRUE
)
AS SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

```bash
bq mk --table \
  --time_partitioning_type=DAY \
  --time_partitioning_field=order_date \
  --range_partitioning_field=customer_id \
  --clustering_fields=customer_id,status \
  YOUR_PROJECT_ID:curated.orders_clustered_cli
```

### 2. Inspect the clustering metadata

```sql
SELECT
    table_name,
    clustering_fields
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE 'orders_clustered%';
```

```sql
-- The dedicated clustering view
SELECT *
FROM `YOUR_PROJECT_ID.curated.orders_clustered.INFORMATION_SCHEMA.CLUSTERING_INFORMATION`
LIMIT 10;
```

### 3. Measure the clustering benefit

```sql
-- ❌ Non-clustered table: filter on customer_id only
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp`
WHERE customer_id = 'cust_000042';

-- ✅ Clustered table: same filter, but blocks are skipped
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_clustered`
WHERE customer_id = 'cust_000042';
```

```sql
-- Compare the bytes
SELECT
    CASE
        WHEN query LIKE '%orders_dp%' THEN 'not_clustered'
        ELSE 'clustered'
    END AS table_type,
    ROUND((total_bytes_processed / POW(1024, 3)), 2) AS mb_processed,
    ROUND(total_slot_ms / 1000, 2) AS slot_seconds
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE query LIKE '%cust_000042%'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY creation_time DESC;
```

### 4. Add clustering to an existing table

```sql
-- ⚠️ This REWRITES the entire table
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_dp`
SET OPTIONS (enable_refresh = TRUE);  -- placeholder — see below

-- The supported way is a CTAS with clustering
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_reclustered`
PARTITION BY order_date
CLUSTER BY customer_id, status
OPTIONS (
  partition_expiration_days = 730,
  require_partition_filter = TRUE
)
AS SELECT * FROM `YOUR_PROJECT_ID.curated.orders_dp`;
```

⚠️ **You cannot add clustering to an existing table without rewriting it.** The path is:
CTAS into a new table with clustering → validate → swap.

### 5. Clustering a nested field

```sql
-- A field inside a STRUCT can be a clustering column
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_nested_clustered`
PARTITION BY order_date
CLUSTER BY customer.customer_id, customer.segment
AS SELECT * FROM `YOUR_PROJECT_ID.curated.orders_nested`;
```

### 6. The clustering trade-off measurement

```sql
-- Storage cost of clustering
SELECT
    t.table_name,
    ROUND(t.size_bytes / POW(1024, 3), 2) AS size_gb,
    t.partition_count,
    t.clustering_fields
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES` t
WHERE t.dataset_name = 'curated'
  AND t.clustering_fields IS NOT NULL;
```

Compare the size of a clustered table with its unclustered twin.

---

## 💡 Production Notes

- **Clustering helps most when the filter column has high cardinality** and you filter on a
  narrow range or specific value. For a column with 5 distinct values, clustering gains little.
- **Clustering does not help with `LIKE '%pattern%'`** — a substring match cannot use sorted blocks.
- **Clustering does not help with aggregations over the whole table.** It prunes *reads*, not
  *scans for aggregation*.
- **The 5–20% storage overhead is worth it when the clustered column is in most queries.** It is
  not worth it for a column used in 2% of queries.
- **Do not cluster on a column you never filter on.** You pay storage and rewrite cost for
  nothing.
- **Clustering and `require_partition_filter` work together well.** One prunes at the partition
  level, the other at the block level.

---

## 🔑 Key Takeaways

- Clustering sorts data by column values so BigQuery can skip **blocks** within a partition.
- **Partitioning and clustering are complementary** — partition reduces the data set, clustering
  reduces the data within it.
- Up to **4 clustering columns**; order them by selectivity.
- **BigQuery re-clusters automatically in the background** — clustering improves over time.
- Cost: **5–20% storage overhead** and a **full table rewrite** to apply.
- Only worth it when the clustering column appears in most queries and has high cardinality.

---

## 📚 Practice Exercises

1. **Clustering decision.** For each table, decide: cluster, and on which columns (up to 4)?
   - (a) 8 TB orders table; queries filter on customer_id, status, and date range
   - (b) 500 GB products table; queries filter on category and brand
   - (c) 50 TB events table; queries filter on device_id
   - (d) 2 GB customers table; queries filter on country

2. **Measure the benefit.** Create a clustered and an unclustered version of the same 5 GB table.
   Run 10 different filter patterns against each and record `total_bytes_processed`. Write the
   conclusion: which filters benefit, and by how much.

3. **Re-clustering behaviour.** Design an experiment to measure how long BigQuery takes to
   re-cluster a table after a bulk load. Load 1M rows in random key order, measure query latency
   immediately, then daily for a week.

4. **Migration plan.** Write the complete plan for adding clustering to a 20 TB production table
   with 100 dependent views and 500 BI users. Cover: method, downtime, validation, rollback, and
   the cost.

5. **String clustering gotcha.** Demonstrate the lexicographic sorting problem with `cust_10` vs
   `cust_2`. Show how a range filter behaves differently on clustered and unclustered tables, and
   provide the zero-padding fix.

---

## 📖 Further Reading

- Clustered tables — https://cloud.google.com/bigquery/docs/clustered-tables
- Clustering information view — https://cloud.google.com/bigquery/docs/information-schema-clustering-information
- Workload management and clustering — https://cloud.google.com/bigquery/docs/clustered-tables
