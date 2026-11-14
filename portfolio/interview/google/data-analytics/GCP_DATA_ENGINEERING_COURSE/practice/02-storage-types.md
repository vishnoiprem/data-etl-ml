# 2 — Types of Storage in BigQuery

> **Practice Module 2 · BigQuery · 40 minutes**

## 🎯 What you will learn

- Every kind of table BigQuery can hold, and — the question that matters — **where the bytes
  physically live** for each.
- The difference between a logical view and a materialized view, stated so a stakeholder
  understands the bill difference.
- Why snapshots and clones are not backups, and what they actually are.
- When an external table beats a managed table, and when it quietly costs you more.
- How to write a `CREATE TABLE` that will still be correct in a year.

---

## 🧠 Concept

### The one question that separates the categories

> **Does BigQuery own the data, or does it just point at it?**

Every storage type in BigQuery answers this question differently, and almost every mistake in
this area comes from confusing "I can query it" with "BigQuery stores it".

### Standard tables — BigQuery owns the bytes

A **standard table** holds structured records in BigQuery's own columnar storage. This is the
default, and it is what most of this course assumes.

Three sub-forms:

| Form | What it is | Writable? | Storage cost |
|---|---|---|---|
| **Table** | The normal case | Yes | Full copy |
| **Table snapshot** | A read-only, point-in-time copy of a table | No | Only the bytes that *changed* since the base |
| **Table clone** | A lightweight, writable copy of a table | Yes | Only the difference from the base table |

**Snapshots and clones are not backups.** This distinction matters more than it looks:

- A **snapshot** is read-only and shares unchanged blocks with its base table. It is a
  point-in-time *view of storage*, good for "what did this table look like on 1 March" — audit,
  reproduction, safe exploration of a destructive change.
- A **clone** is writable and shares unchanged blocks with its base until you modify it.

Both are cheap because BigQuery stores only the **difference** from the base table. That is
exactly why neither protects you against a corrupted base table, an accidental `DELETE` that
also propagates, or a region-level problem. **A backup is a different artifact with a different
lifecycle.** If your retention story is "we have snapshots", you do not have a retention story.

### External tables — the bytes live elsewhere

An **external table** references data stored outside BigQuery. The data is *not* in BigQuery's
storage, and BigQuery does not own it.

| Form | Where the data lives | Fine-grained security |
|---|---|---|
| **BigLake tables** | Cloud Storage, Amazon S3, Azure Blob Storage | ✅ Yes |
| **Object tables** | Unstructured objects in Cloud Storage | ✅ Yes |
| **Non-BigLake external tables** | Cloud Storage, Google Drive, Bigtable | ❌ No |

**BigLake** is the one to reach for. It brings the external data into BigQuery's table model
*and* adds table-level fine-grained security, which the plain external table lacks. The
practical difference: with a non-BigLake external table, anyone with read access to the bucket
can read the rows, no matter what the BigQuery table says.

**Object tables** are for unstructured data — images, PDFs, audio. They point at objects rather
than rows, and BigQuery treats each object as a record with metadata. This is the foundation
under the multimodal features in module 7.

### Logical views vs materialized views

This is the distinction most worth being crisp about, because it is a cost decision dressed as a
schema decision.

| | Logical view | Materialized view |
|---|---|---|
| When the query runs | **Every time you query it** | Precomputed, refreshed periodically |
| Where the result lives | Nowhere — it is just a stored query | **In BigQuery storage** |
| Cost of reading | Full cost of the underlying scan | Cost of reading a small table |
| Data freshness | Always current | As of the last refresh |
| Storage cost | Free | Billed as active logical storage |

A **logical view** is a named query. Nothing is precomputed; when you read it, BigQuery runs the
underlying query and bills you for the bytes that query scans. It is always fresh and it costs
nothing to store.

A **materialized view** is a **precomputed view**. Its results are periodically cached, and that
cache is **stored in BigQuery storage** — so it appears on your storage bill. In exchange,
reading it is cheap and fast.

**When to use which:**

- **Logical view** — the definition changes, the consumers are few, freshness matters, and the
  underlying tables are small or already cheap to scan. It is the right default.
- **Materialized view** — the definition is stable, the view is read constantly, and the
  underlying scan is expensive. A dashboard hitting a 2 TB join 200 times an hour is the
  canonical case.

The classic mistake is materializing because "views are slow" without checking whether the
underlying query is expensive. If the base table is 100 MB, a logical view is already fast and
you have added a storage bill and a staleness problem for nothing.

### Open table formats

BigQuery supports open table formats — **Iceberg**, **Delta**, and **Hudi** — through the
BigLake metastore. The reason they matter: the data lives in Cloud Storage (or S3, or Azure) in
a format that *other engines can also read*.

This is the **interoperability** play. A company that has standardised on Iceberg can point
BigQuery at it for analytics and keep Spark or Trino for other workloads, with one copy of the
data. The trade-off is that you give up some BigQuery-native optimisation in exchange for the
format's portability, and you take on metastore management.

---

## 🛠️ Hands-On

### 💻 Runs locally — choosing a storage type

There is no BigQuery here, but the decision is arithmetic, and arithmetic runs anywhere.

```python
import sys
sys.path.insert(0, "../project/core")
from cost_model import estimate

# A dashboard reads the same expensive join all day.
SCAN_TB = 2.0
READS_PER_DAY = 200
DAYS = 30

# Logical view: every read pays the full scan.
logical = estimate("bigquery", scanned_tb=SCAN_TB * READS_PER_DAY * DAYS,
                   apply_free_tier=False).total

# Materialized view: one refresh, then every read is a small table scan.
materialized = estimate("bigquery", scanned_tb=SCAN_TB * DAYS,       # refreshes
                        storage_gb=50,                                # cached result
                        apply_free_tier=False).total

print(f"logical view:      ${logical:,.2f}")
print(f"materialized view: ${materialized:,.2f}")
print(f"difference:        ${logical - materialized:,.2f}")
```

Expected output:

```text
logical view:      $75,000.00
materialized view: $376.00
difference:        $74,624.00
```

That is the whole argument for materialized views, in one line: **$75,000 versus $376 for the
same numbers.** And note the cost *moves* — it does not vanish. You have traded query cost for
storage cost and for a refresh job. That trade is worth making at 200 reads a day and is a
terrible trade at two.

### 💻 Runs locally — snapshot and clone economics

```python
import sys
sys.path.insert(0, "../project/core")
from cost_model import estimate

TABLE_GB = 500

full_copy = estimate("cloud-storage", storage_gb=TABLE_GB,
                     apply_free_tier=False).total

# A snapshot stores only the bytes that changed since the base table.
changed = TABLE_GB * 0.02
snapshot = estimate("cloud-storage", storage_gb=changed,
                    apply_free_tier=False).total

print(f"full copy:  ${full_copy:,.4f}")
print(f"snapshot:   ${snapshot:,.4f}  (2% of the table changed)")
print(f"ratio:      {full_copy / snapshot:.0f}x")
```

Expected output:

```text
full copy:  $10.0000
snapshot:   $0.2000  (2% of the table changed)
ratio:      50x
```

### 🌐 Needs a BigQuery project — create the reference table

This is the table the rest of the suite reasons about. Create it partitioned and clustered:

```sql
CREATE TABLE `retail.analytics.sales` (
    transaction_id STRING,
    store_id STRING,
    sale_date DATE,
    customer_id STRING,
    sales_amount NUMERIC
)
PARTITION BY sale_date
CLUSTER BY store_id;
```

Every clause in that statement earns its place:

- **`NUMERIC`, not `FLOAT64`.** `NUMERIC` is exact decimal — 38-digit precision, scale 9. Money
  that is *approximately* right is not money. Module 5 covers the type system in full.
- **`PARTITION BY sale_date`.** Partitioning is a **range** operation. A `WHERE sale_date BETWEEN
  '2026-11-01' AND '2026-11-30'` predicate skips every other partition at the metadata level.
- **`CLUSTER BY store_id`.** Clustering organises data *within* each partition. It helps
  **equality** filters and grouping — `WHERE store_id = 'S-114'`.

**And the caveat that catches people:** clustering on `store_id` does *not* help this query much,
because there is no selective `store_id` filter in it:

```sql
SELECT store_id, SUM(sales_amount) AS revenue
FROM `retail.analytics.sales`
WHERE sale_date = '2026-11-13'
GROUP BY store_id;
```

Here the partition prune does the work — one partition, not three years — and the clustering
contributes little, because the query touches every store in that partition. **Clustering pays
off when the query filters for particular values of the clustered column.** If your query
aggregates over all stores, you are paying the clustering storage cost for nothing.

### 🌐 Needs a BigQuery project — the storage taxonomy, on the real thing

```bash
bq ls --project_id=YOUR_PROJECT_ID --format=prettyjson YOUR_DATASET
```

Look at the `type` field on each entry. Then check where the bytes live for an external table:

```sql
SELECT
  table_name,
  type,
  creation_time
FROM `YOUR_PROJECT_ID.YOUR_DATASET.INFORMATION_SCHEMA.TABLES`
ORDER BY type, table_name;
```

### 🌐 Needs a BigQuery project — materialized view

```sql
CREATE MATERIALIZED VIEW `retail.analytics.sales_daily_mv`
PARTITION BY sale_date
CLUSTER BY store_id
AS
SELECT
  sale_date,
  store_id,
  SUM(sales_amount) AS revenue,
  COUNT(*)         AS transactions
FROM `retail.analytics.sales`
GROUP BY sale_date, store_id;
```

Then compare what each costs to read:

```sql
-- Logical view: full price every time.
SELECT COUNT(*) FROM `retail.analytics.sales_v`;

-- Materialized view: a small cached table.
SELECT COUNT(*) FROM `retail.analytics.sales_daily_mv`;
```

The materialized view has a **refresh** cost and a **staleness** cost. Neither is free, and
neither is visible in the query itself — which is exactly why you should decide deliberately
rather than by habit.

---

## 🛠️ Common Errors and Fixes

**"My external table query is slow and reads a huge number of bytes."**

External tables read the files they point at. They do not have BigQuery's columnar layout unless
the underlying files are already columnar (Parquet, ORC, Avro — not CSV or JSON). Reading a CSV
external table scans the whole file and pays for every byte. **Convert to Parquet.**

**"The query works, but row-level security does not apply."**

You are probably on a non-BigLake external table, which does not support table-level fine-grained
security. Move to a BigLake table. Confirm with:

```sql
SELECT table_name, type FROM `YOUR_PROJECT_ID.YOUR_DATASET.INFORMATION_SCHEMA.TABLES`;
```

**"The materialized view is stale and I cannot see why."**

Materialized views refresh on a schedule you configure, not on write. There is a refresh window
and the view is only as fresh as its last successful refresh. Check the refresh state rather than
assuming the data pipeline is broken.

**"The snapshot did not restore my deleted rows."**

A snapshot is a point-in-time copy. If you deleted rows *after* the snapshot was taken, they are
still gone from the base table — but the snapshot still holds the pre-deletion state. If you
expected the snapshot to be a backup of the *current* data, that is the confusion. A snapshot is
a copy **of a moment**, not a copy **of a table**.

**"The table has 10,000 partitions and now it will not accept more."**

That is the hard limit. Partitioning by hour on a busy table, or partitioning by a
high-cardinality column, gets you there fast. The fix is to reduce the partition count —
usually by switching to a coarser granularity (day instead of hour) — and this cannot be done
in place; you create a new table and copy.

---

## 💡 Production Notes

### Choose storage type by asking four questions

1. **Who owns the bytes?** If a governance team owns them in Cloud Storage and other engines
   read them too, you want an **external BigLake table** or an **open format**. If you own them
   and only BigQuery reads them, you want a **standard table**.
2. **How often is it read, and how expensive is the underlying scan?** Read constantly and
   expensively → **materialized view**. Read rarely → **logical view**.
3. **Do you need a point-in-time copy, or a safe place to experiment?** Experiment → **clone**
   (writable). "What did it look like then?" → **snapshot** (read-only). Neither is a backup.
4. **Does the data need row-level or column-level security?** If yes, it must be a **BigLake**
   table or a standard table — not a plain external table.

### The rule for `CREATE TABLE`

```sql
CREATE TABLE `retail.analytics.sales` (...)
PARTITION BY sale_date
CLUSTER BY store_id;
```

Two rules that survive every review:

1. **Partition by a date, always.** Not an hour, not a country, not a customer. A date, because
   the overwhelming majority of analytical queries have a date range. And if the table is
   append-only, consider ingestion-time partitioning too, so that a late-arriving record still
   lands in a partition you can prune.
2. **Cluster by the columns you filter and group by, up to four.** Partition first, then cluster
   on the *next* most-selective columns. Both are cheap. Both are effectively free.

And the one that is not optional:

3. **Set `maximumBytesBilled` on every load and query job.** A partition mistake should fail the
   job, not the budget.

### What I would never do

- **Store CSV in Cloud Storage and point an external table at it.** Parquet is compressed,
  columnar, and typed. CSV is none of those. The scan cost difference is routinely 5–10×.
- **Materialize a view over a small table.** You have added a storage bill and a staleness
  problem for a speedup nobody needed.
- **Rely on snapshots as the backup strategy.** They share blocks with the base table. They are
  a rollback aid, not a recovery plan.

---

## 🔑 Key Takeaways

- The category question is **"does BigQuery own the bytes, or just point at them?"**
- Standard tables: BigQuery's own columnar storage. **Snapshots** are read-only point-in-time
  copies; **clones** are writable copies. Both store only the *difference* from the base.
- **Snapshots and clones are not backups.** They share blocks with the base table.
- External tables: data lives elsewhere. **BigLake** brings table-level fine-grained security;
  plain external tables do not. **Object tables** handle unstructured data.
- **Logical view** = a stored query, runs every time, free to store, always fresh, costs the
  full scan on every read. **Materialized view** = precomputed, cached *in BigQuery storage*,
  cheap to read, costs storage and staleness.
- **Iceberg / Delta / Hudi** buy interoperability with other engines via the BigLake metastore.
- The reference table: `PARTITION BY sale_date` (range) + `CLUSTER BY store_id` (equality).
- Clustering only pays when the query **filters** on the clustered column. Aggregating over
  every value of it earns nothing.
- Always use **`NUMERIC`** for money, never `FLOAT64`.

---

## 📚 Practice Exercises

1. Write a one-paragraph explanation of the difference between a snapshot and a clone, and a
   second paragraph explaining why neither is a backup. Your paragraph must mention shared
   blocks, because that is the mechanism.

2. You are given a requirement: "give the finance team a read-only copy of last quarter's orders
   so they can work with them without affecting production, and make it cheap." Decide between a
   snapshot and a clone, state which one and why, and say what you would add to make it a genuine
   recovery plan.

3. Model the cost of a dashboard at 200 reads a day of a 2 TB join using the cost model in
   `project/core/cost_model.py`, once as a logical view and once as a materialized view. Print
   both, state the break-even read count at which the materialized view wins, and explain what
   the answer means for a dashboard that is read 50 times a day instead.

4. A team stores their orders as CSV in Cloud Storage and queries them through an external table.
   Explain in three sentences why this is the most expensive possible way to run the same query,
   and describe the migration to Parquet — including whether you would use a standard table or a
   BigLake table, and why the answer depends on who else reads the data.

5. Take the `retail.analytics.sales` table and write three queries against it: one that benefits
   from the partition, one that benefits from the clustering, and one that benefits from neither.
   For each, state which of the two table-layout features did the work, and say what the byte
   saving is in relative terms.

6. Explain when a logical view is the wrong choice and a materialized view is right, to someone
   who knows what a view is but has never seen a storage bill. Include the break-even concept,
   because "it depends on read frequency" is only half an answer — the other half is what
   happens when the refresh job fails.

7. Your organisation has standardised on Iceberg in Cloud Storage, and BigQuery is one of three
   engines reading the same data. List the benefits of the open format for this setup, the
   costs, and what you would need to manage that BigQuery-native storage would have handled
   for you.

8. Using the service catalog in `project/core/service_catalog.py`, list every service whose
   category is `Analytics` or `Storage`, and for each one say whether it could serve as the
   "bytes live elsewhere" layer in an external-table design. Then explain which one you would
   put in front of the data and why.

---

## 📖 Further Reading

- [Creating and using tables](https://docs.cloud.google.com/bigquery/docs/tables)
- [Table snapshots](https://docs.cloud.google.com/bigquery/docs/table-snapshots-intro)
- [Table clones](https://docs.cloud.google.com/bigquery/docs/table-clones-intro)
- [Views](https://docs.cloud.google.com/bigquery/docs/views)
- [BigLake tables](https://docs.cloud.google.com/bigquery/docs/managed-tables)
- [Partitioned tables](https://docs.cloud.google.com/bigquery/docs/partitioned-tables)
- [Clustered tables](https://docs.cloud.google.com/bigquery/docs/creating-clustered-tables)
- [GoogleSQL data types](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/data-types)
- [Course interview bank: Storage and Databases](../interview/02-storage-and-databases.md)
