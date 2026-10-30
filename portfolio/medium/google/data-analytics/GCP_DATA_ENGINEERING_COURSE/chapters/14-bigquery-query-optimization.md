# 3.3 — BigQuery Query Optimization

> **Section 3 · Analytics & Warehousing · Lecture 3.3 · 8:00**

## 🎯 What you will learn

- **The bytes-billed rule** — the single law that governs BigQuery cost, and everything that follows from it
- Why `SELECT *` is the single most expensive habit in analytics
- Partition pruning, and the difference between pruning and filtering
- Clustering (physical reordering), what it actually gives you, and when it does not
- Nested vs repeated vs flat schema design, and when denormalisation is correct
- Avoiding repeated full scans: materialised views, aggregate tables, and the incremental pattern
- How to read the dry run and the query plan
- Avoiding `ORDER BY` on huge tables, and the `ORDER BY` alternatives
- The full cost model with concrete numbers from `cost_model`
- A checklist you can apply to any query before it runs in production

---

## 🧠 Concept

### The bytes-billed rule

> **On-demand BigQuery charges you for the bytes your query reads — not the bytes it returns, not the rows it touches, not the time it takes.**

Everything else in this chapter is a consequence of this rule. If you internalise one thing, internalise this.

**Why bytes and not results.** Because BigQuery's storage is immutable and columnar. When you run a query, the engine reads **column chunks** from storage and decompresses them. The work it does — filtering, joining, aggregating — is not directly billed. The bytes it pulled off storage are. A query that reads 1 TB and returns 10 rows costs exactly the same as a query that reads 1 TB and returns 10 million rows.

This is why the optimisation literature for BigQuery looks so different from the optimisation literature for a traditional database. In a row-store, you optimise the *plan*: better index, different join order, avoid a nested loop. In BigQuery, the plan matters much less; the **shape of the read** is what matters. You are not trying to make the engine do less work with the data it has — you are trying to make it not fetch the data in the first place.

**Three corollaries that will reframe how you write queries:**

1. **Adding a `WHERE` clause does not reduce the bytes read** — unless the filter enables pruning. A filter applied *after* the read reduces rows but not bytes. This is the single most misunderstood fact about BigQuery.
2. **The number of columns matters as much as the number of rows.** `SELECT COUNT(*)` on a wide table reads every column's metadata and one column's data; `SELECT *` reads everything.
3. **The join's cost is dominated by the shuffle**, which reads the join inputs — so a join between a 1 TB table and a 40 MB table can cost more than the scan of the 1 TB table, because both sides are shuffled.

### The measurement: dry run and bytes billed

Before changing anything, measure. BigQuery will tell you exactly what a query will cost, for free.

```bash
bq query --use_legacy_sql=false --dry_run \
  'SELECT region, COUNT(*) AS n, SUM(amount_eur) AS rev
   FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
   GROUP BY region'
```

The output tells you the total bytes that would be processed and the bytes that would be billed. Three fields matter:

- **Total bytes processed** — the raw I/O. What the engine reads.
- **Total bytes billed** — what you pay. This accounts for the **minimum 10 MB per table referenced**,. It is frequently *higher* than processed bytes for small tables.
- **Estimated bytes processed after partition pruning** — what the same query would read with an appropriate partition filter.

**The gap between processed and billed is a diagnostic.** When `total_bytes_billed` is 10 MB on a query that processed 200 bytes, the minimum-billing rule is dominating: the table is tiny and you are paying the floor. Billed can differ from processed for other reasons (for example cached results or the minimum-bytes rule), so treat the gap as a prompt to investigate. Neither is a problem per se — but a dashboard of 40 tiny tables is billed at 400 MB per refresh, and you should know that before you ship it.

**In Python**, the same measurement with the same discipline:

```python
from google.cloud import bigquery

client = bigquery.Client()

job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
job = client.query(sql, job_config=job_config)

processed = int(job.total_bytes_processed or 0)
billed = int(job.total_bytes_billed or 0)
print(f"processed: {processed:,} bytes")
print(f"billed:    {billed:,} bytes")
print(f"estimated cost: ${billed / 1024**4 * 6.25:.4f}")
```

**In the console**, the same information is in the query plan: the "Bytes Processed" row in the top stage, and the "Read" row showing bytes read from each table.

### The query plan

The plan is a DAG of stages. Reading it is a skill, and the skill is mostly about three numbers:

- **Bytes read** — per stage, per table. The largest number here is your target.
- **Slot-ms** — the compute consumed. High slot-ms with low bytes read means the query is shuffle-bound.
- **Rows read vs rows returned** — a large ratio means the filter is not pruning.

The pattern to look for:

```text
Stage S00: Input
  Read: 1.2 TB from fact_events        ← the problem starts here
Stage S01: Shuffle
  Output: 4800 rows                    ← the shuffle is small
Stage S02: Aggregate
  Output: 4 rows
```

When the read is 1.2 TB and the output is 4 rows, you are paying for 1.2 TB to produce 4 rows — and the 4 rows are the same 4 rows you got from 50 MB of data last time. That is the partition-pruning conversation.

The other pattern to look for:

```text
Stage S00: Input
  Read: 1.2 TB from fact_events
Stage S01: Shuffle
  Output: 1.1 TB                      ← the shuffle is huge
```

Here the bytes are genuinely needed, but the shuffle is nearly as large as the input. That is a join or a distribution-sensitive aggregation. The fix is not a better filter; it is reducing the join input size — which means denormalising, or pre-aggregating.

### Rule 1: never `SELECT *`

`SELECT *` reads every column, including the wide ones you do not need. In a columnar store this is catastrophic, because the columns you did not select still cost bytes.

```sql
-- BAD: reads every column of every row.
SELECT * FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
WHERE event_dt = '2026-01-15';

-- GOOD: reads only what the query needs.
SELECT event_id, event_ts, region_key, amount_eur
FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
WHERE event_dt = '2026-01-15';
```

**The mechanism that surprises people:** BigQuery has an optimisation where, for `SELECT COUNT(*)` on a table with no partitioning, it can read a small amount of metadata instead of the data. This means `SELECT COUNT(*)` can be *cheaper* than `SELECT *` on the same table. Which is exactly backwards from every row-store intuition you have.

**The `SELECT *` trap in practice.** `SELECT *` is not only a cost problem; it is a **correctness** problem. It couples your query to the table's schema. When someone adds a column, your query's output changes shape — and every downstream consumer of that query breaks, often silently, because `SELECT *` in a `CREATE TABLE AS` produces a table with a new column and downstream `INSERT` statements now mismatch.

The rule: **never `SELECT *` in production code.** Never in a `CREATE TABLE AS SELECT`. Never in a BI tool's default extract. If you need the whole row, write the columns out — it takes two extra minutes and makes the schema change a non-event.

**Exception to know about:** BigLake and external tables over Parquet do support `SELECT *` efficiently, because the Parquet footer carries the schema and column chunks are read individually. But even there, name your columns.

### Rule 2: partition pruning is not filtering

This distinction is worth its own rule because getting it wrong costs 100× and produces no error.

**Filtering** (post-read): the engine reads all the data, then discards rows that fail the predicate. Bytes read: everything.

**Pruning** (pre-read): the engine consults the partition metadata, determines which partitions could match, and never fetches the blocks for the others. Bytes read: only the matching partitions.

```sql
-- Reads the ENTIRE table, then filters. If the table has 365 partitions
-- and you want one day, this reads 365 days.
SELECT COUNT(*) FROM fact_events WHERE event_dt = '2026-01-15';

-- Reads ONE partition.
SELECT COUNT(*) FROM fact_events
WHERE event_dt BETWEEN '2026-01-15' AND '2026-01-15';
```

**The critical detail:** pruning happens only when the predicate is a **constant** that BigQuery can evaluate at plan time. If you pass the partition filter as a *query parameter* or derive it from another table, pruning may not happen.

```sql
-- Prunes: the date is a literal.
WHERE event_dt BETWEEN '2026-01-01' AND '2026-01-15'

-- May NOT prune: the value is not known at plan time.
WHERE event_dt BETWEEN @start_date AND @end_date
```

**This is the single most common and most expensive BigQuery mistake in BI tools.** A Looker Studio dashboard with a date filter that compiles to a parameterised query reads the whole table on every refresh. The fix is to ensure the tool generates literal partition predicates, or to use a **partitioned view** — a view that statically evaluates the filter against the partition column, forcing pruning:

```sql
CREATE VIEW `YOUR_PROJECT_ID.curated_us-central1.v_fact_events` AS
SELECT * EXCEPT (event_dt)
FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
WHERE event_dt BETWEEN '2026-01-01' AND '2026-12-31';
```

Querying the view with a narrower date range still prunes, because the view's definition contains the literal bounds and the optimiser can intersect them with the query's bounds.

**The exception to the exception:** BigQuery supports **partition parameterisation** for time-unit columns, which lets you prune even with dynamic filters:

```sql
-- Query parameter with partition pruning.
SELECT COUNT(*) FROM fact_events
WHERE event_dt BETWEEN @start_date AND @end_date;
```

with the parameter passed as a `TIMESTAMP`/`DATE` and the table partitioned by `DATE`. If the parameter is a literal date (not a derived expression), pruning works. Confirm with a dry run — always.

**How to choose the partition column.** The rule is short: **partition on the column you filter by, almost always.** Not the column you group by, not the column with the highest cardinality, not the column that is most convenient to load. The column you filter by.

The course's `pipeline_logic.suggest_partitioning()` encodes exactly this rule, and its candidate list is `["event_dt", "event_ts"]` — the timestamp columns, because those are what a time-range query filters on.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import suggest_partitioning, event_time_bounds, hours_spanned

# The partition column is chosen by the filter, not by the data.
print("suggested partition column:", suggest_partitioning([]))
```

**Time-unit partitioning.** BigQuery supports `DAY`, `HOUR`, `MONTH`, `YEAR` and `TIMESTAMP_TRUNC`-based ingestion-time partitioning. The choice is a direct trade:

| Partitioning | Partitions | Per-partition minimum | Best for |
|---|---|---|---|
| `DATE` | ~365/year | ~1 MB | Daily batch, most BI workloads |
| `TIMESTAMP` (hourly) | ~8,760/year | ~1 MB | Sub-minute freshness, streaming |
| `DATETIME` | ~365/year | — | Timestamp-typed data |
| `MONTH` | 12/year | — | Very large backfills |
| `INGESTION_TIME` | — | — | Streaming appends, arrival ordering |

Note that BigQuery has a **10,000-partition limit** per table and charges a small fee for partitions beyond the first 10,000. Hourly partitioning on a multi-year table hits that.

**The ingestion-time vs column partitioning decision.** Column partitioning (`PARTITION BY event_dt`) lets you filter on your *business* date. Ingestion-time partitioning (`PARTITION BY _PARTITIONTIME`) lets you filter on *arrival* date. Column partitioning is almost always right for a warehouse, because analysts ask questions in business time. Ingestion-time partitioning is right for a log table where you need to know what arrived when — for reprocessing, for late-arriving data, for debugging a pipeline.

**The important detail about integer partitioning.** BigQuery lets you partition on an `INT64` column, where each distinct value is a partition. This is extremely useful for **user-scoped tables** — partition by `user_id` and then every query for a user reads exactly one partition. It is also a trap: if your data has high cardinality and no partitioning discipline, you get 10,000 one-row partitions, each billed the 10 MB minimum.

### Rule 3: clustering, and what it actually gives you

Clustering sorts data within each partition by up to four columns. BigQuery calls it *physical reordering* in the console, and it was formerly called *clustering* (the name changed in 2024, which is why you will see both in older documentation).

**The mechanism.** When you cluster by `region_key, event_type`, BigQuery sorts rows within a partition by `region_key` first, then `event_type`. The sort key is stored as min/max *prefix* metadata on each block. So a filter `WHERE region_key = 3` can be answered from the block metadata alone — blocks whose `region_key` range does not include 3 are skipped entirely, without reading their data.

**What clustering does and does not do:**

- **Does:** skip row groups *within* a partition. Composes with partitioning: partition by date, cluster by region, and one region on one day reads a tiny slice.
- **Does not:** skip whole partitions. Only partitioning does that.
- **Does not:** require a rescan when you add a clustering column. New data is clustered with the new keys; existing data is not re-clustered until it is rewritten.
- **Does not:** help `GROUP BY` much, unless the clustering column is the grouping column — then it reduces the shuffle, because rows with the same key are already together.

**When clustering helps most:** high-cardinality equality filters. `WHERE customer_id = 'X'` on a table clustered by `customer_id` reads a tiny fraction of the partition. Clustering by a low-cardinality column (say, `country` with 30 values) helps less, because with 30 values each value still occupies a large fraction of the partition.

**When to add it:** cluster by the columns you filter on *after* the partition filter — typically the second and third most common filters in your queries.

**The rule of four.** BigQuery allows up to four clustering columns, and it sorts by them lexicographically. Cluster by `(most_filtered, second_most_filtered, third_most_filtered, fourth_most_filtered)`.

**Physical reordering vs the older "clustering" cost model.** Historically, BigQuery's clustering feature was billed at $0.02 per TB of data *reclustered*, and you had to invoke a re-clustering job. Under physical reordering, the clustering is applied to newly written data automatically and there is no reclustering fee for the initial application. This matters for a large backfill: you should add clustering to the table *before* the backfill, not after, because adding it after means the historical data is unclustered until it is rewritten.

### Rule 4: schema design — nested, repeated, flat

BigQuery supports three shapes, and the choice is a real trade-off.

**Flat (one row per entity, columns for everything):**

```sql
CREATE TABLE fact_events (
  event_id STRING, event_ts TIMESTAMP, region_key INT64,
  amount_eur FLOAT64, currency STRING
);
```

**Repeated (an array of records):**

```sql
CREATE TABLE fact_orders (
  order_id STRING,
  order_ts TIMESTAMP,
  customer_key INT64,
  line_items ARRAY<STRUCT<
    sku STRING,
    qty INT64,
    unit_price_eur FLOAT64
  >>
);
```

**Nested (a struct, non-repeated):**

```sql
CREATE TABLE fact_orders (
  order_id STRING,
  customer STRUCT<key INT64, tier STRING, country STRING>,
  shipping STRUCT<city STRING, postcode STRING>
);
```

**When each is right:**

| Shape | Right when | Cost characteristic |
|---|---|---|
| Flat | One row per fact, no sub-entities | Simplest, most predictable |
| Repeated | A parent has a variable number of children read together | Avoids the join; array is read as one block |
| Nested | Fixed sub-entity attributes | Attributes read together stay together |

**The key insight: a repeated field avoids a join.** If `fact_orders` has 10,000 rows each with 3 line items, and `fact_line_items` is a separate table with 30,000 rows, then the join between them requires a 30,000-row shuffle — and the bytes read on both sides. Keeping the line items in an array means the order and its items are read from the same column chunk, and BigQuery's nested execution (the Dremel contribution from chapter 3.2) can aggregate inside the array without materialising the join.

**The classic example: `ARRAY_AGG` versus `JOIN` for a one-to-many.**

```sql
-- Flattened: 30,000 rows joined back to 10,000. Expensive.
SELECT o.order_id, SUM(li.qty) AS total_qty
FROM fact_orders o
JOIN fact_line_items li USING (order_id)
GROUP BY o.order_id;

-- Nested: one read of 10,000 rows, aggregated inside the array.
SELECT
  order_id,
  (SELECT SUM(item.qty) FROM UNNEST(line_items) AS item) AS total_qty
FROM fact_orders;
```

**The nested version reads 10,000 rows instead of 40,000 and needs no shuffle.** This is the single most valuable schema decision in BigQuery, and it is a direct consequence of the bytes-billed rule.

**The costs of nested, stated honestly:**

- **You lose the ability to query a nested array as if it were a table.** `UNNEST` is required, and a `UNNEST` in a `WHERE` clause can defeat pruning if the nested field is the partition column.
- **One oversized row.** A repeated field with 100,000 elements creates a single row larger than sensible limits, and it is stored as one contiguous value. BigQuery caps a single cell at 100 MB and a row at 100 MB (so a repeated field cannot exceed 100 MB per row).
- **Writing to nested tables requires more care.** `MERGE` on a nested array is possible but fiddly; `CREATE OR REPLACE` is often simpler.
- **Querying nested data in BI tools** is more awkward than flat columns. Looker Studio handles nested fields poorly.

**The rule of thumb:** nest when the child is *always* read with the parent (a line item with its order), and flatten when the child is queried independently (line items across all orders, for a product report). If the child is queried independently, a separate fact table at the child's grain is not just acceptable — it is correct, because it gives the child its own grain and its own partition.

**Schema evolution.** BigQuery allows you to `ALTER TABLE ... ADD COLUMN` freely and to relax nullability. You cannot easily drop a column or change its type, and changing a field from `NULLABLE` to `REQUIRED` fails if existing rows violate it. The advice: add columns freely, and treat the schema as append-only.

### Rule 5: denormalisation, and when it is correct

In OLTP, denormalisation is a cache — a copy of data maintained for read speed, at the cost of write consistency. In a warehouse, denormalisation is different: there is no consistency to maintain, because the denormalised copy is **immutable history**.

**The rule:** in a warehouse, denormalise when it removes a join, and accept that the dimension's attributes are frozen at the time of the fact. This is not a bug — it is *correct*, and it is called a **slowly changing dimension of type 2** when you keep the history explicitly.

```sql
-- The fact carries the dimension attributes as they were at the time
-- of the event. No join. No inconsistency possible.
CREATE TABLE fact_events (
  event_id        STRING NOT NULL,
  event_dt        DATE   NOT NULL,
  region_code     STRING NOT NULL,   -- was 'AMER' on 2026-01-15
  region_name    STRING NOT NULL,   -- was 'Americas' then
  channel_code   STRING NOT NULL,
  amount_eur      FLOAT64 NOT NULL
)
PARTITION BY event_dt
CLUSTER BY region_code, channel_code;
```

Now `SELECT SUM(amount_eur) GROUP BY region_code` reads one table, one partition, no shuffle.

**The trade you are making.** In exchange for removing the join, you give up:

- **The ability to update dimension attributes retroactively.** If Marketing renames "AMER" to "AMERICAS" next quarter, the historical fact rows still say "AMER". You need a new table, a view that maps old to new, or a proper type-2 dimension.
- **Storage duplication.** The dimension attributes are repeated on every fact row. For a wide dimension (say 50 attributes), that is 50 attributes × N rows of storage. At $0.02/GB-month, this is usually cheap — and it is why columnar storage enables denormalisation in the first place.
- **The risk of inconsistency at write time.** The denormalised copy must be written correctly. If the ETL writes "AMER" in one place and "Americas" in another, the fact table has two codes for one region. This is why you denormalise from a **single conformed dimension**, in one place in the pipeline, never from the source.

**When NOT to denormalise:** when the dimension is genuinely high-cardinality *and* wide (a customer dimension with 200 attributes and 10 million customers). Then the duplication is enormous and the join — properly designed, on a clustered key — is cheaper. Denormalise the *hot* columns; keep the rest joined.

**The SCD decision.** There are three standard treatments for a changing dimension attribute:

| Type | Behaviour | Storage | Use when |
|---|---|---|---|
| Type 1 | Overwrite in place | Smallest | The history does not matter (e.g. a typo fix) |
| Type 2 | New row with validity dates | Largest | History matters ("what was the customer's tier *at the time*?") |
| Type 3 | History in separate columns | Awkward | Rarely; only for one or two tracked attributes |

In a warehouse, **type 2 is usually already implicit** — the fact rows record the attribute as it was, because the fact was written at that time. You only need explicit type 2 in the dimension table when you query the dimension itself over time.

### Rule 6: stop reading the same thing repeatedly

The most common waste in an analytics stack is not a bad query; it is **the same query run forty times a day** because a dashboard, a scheduled job and three analysts each recompute the same aggregate.

**Three patterns, in increasing order of sophistication:**

**Pattern 1 — Materialised view.** BigQuery materialises the view's result and refreshes it. Best when the underlying data changes in a way that allows a partial refresh (partition-level), and the view is queried often.

```sql
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.curated_us-central1.mv_daily_region` AS
SELECT
  event_dt,
  region_key,
  COUNT(*) AS event_count,
  SUM(amount_eur) AS revenue_eur
FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
GROUP BY event_dt, region_key;
```

Refresh it on a schedule (a scheduled query that re-runs the definition, or BigQuery's built-in refresh). Cost: the refresh reads the base table and the result costs storage. The break-even is roughly: if the view is queried more times than it takes to refresh it, it pays.

**Pattern 2 — Aggregate table.** A separate fact table at a coarser grain, maintained by a scheduled query. This is the *conform* of Pattern 1 but explicit, and it lets you control the refresh schedule exactly.

```sql
CREATE TABLE `YOUR_PROJECT_ID.curated_us-central1.fact_daily_region` (
  event_dt    DATE   NOT NULL,
  region_key  INT64  NOT NULL,
  event_count INT64  NOT NULL,
  revenue_eur FLOAT64 NOT NULL
)
PARTITION BY event_dt
CLUSTER BY region_key;
```

```sql
CREATE OR REPLACE PROCEDURE `YOUR_PROJECT_ID.curated_us-central1.proc_refresh_daily_region`(target_date DATE)
BEGIN
  DECLARE target_partition STRING DEFAULT FORMAT_DATE('%Y%m%d', target_date);
  BEGIN TRANSACTION;
    DELETE FROM `YOUR_PROJECT_ID.curated_us-central1.fact_daily_region`
      WHERE event_dt = target_date;
    INSERT INTO `YOUR_PROJECT_ID.curated_us-central1.fact_daily_region`
      (event_dt, region_key, event_count, revenue_eur)
    SELECT event_dt, region_key, COUNT(*), SUM(amount_eur)
    FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
    WHERE event_dt = target_date
    GROUP BY event_dt, region_key;
  END TRANSACTION;
END;
```

Note the `DELETE` + `INSERT` inside a transaction rather than `MERGE`: it is idempotent, and it reads one partition of the base table. `MERGE` would also work but is noisier for this shape.

**Pattern 3 — Incremental aggregation.** Do not recompute the whole aggregate; recompute only what changed. This is the pattern that scales, and it is the one a production warehouse needs.

The rule: **an aggregate fact table at daily grain can be incrementally maintained, because a day's partition depends only on that day's fact partition.** The course's data is a perfect illustration:

```text
fact_events (partition 20260115)  ->  fact_daily_region (partition 20260115)
```

Recomputing only the affected partition is O(one day) instead of O(all history). If late-arriving data changes yesterday, you recompute yesterday's partition. If the dimension changes, you recompute the affected range — which is why conformed dimensions that are type-2 need a "recompute the range since the change" job.

**The incremental pattern in code**, using the course's own helpers:

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    aggregate_events,
    build_bigquery_rows,
    filter_rows_for_partition,
    partition_for_date,
    partition_for_event,
)

TARGET_DATE = "2026-01-15"


def incremental_daily_aggregate(rows: list[dict], logical_date: str) -> list[dict]:
    """Recompute only the partition affected by the load.

    Args:
        rows: All rows in the batch.
        logical_date: The logical date being loaded.

    Returns:
        The aggregate rows for that partition only.
    """
    partition = partition_for_date(logical_date)
    partition_rows = filter_rows_for_partition(rows, partition)
    summary = aggregate_events(partition_rows)
    return [
        {
            "event_dt": logical_date,
            "region": region,
            "event_count": values["event_count"],
            "revenue_eur": values["revenue_eur"],
        }
        for region, values in sorted(summary.items())
    ]
```

### Rule 7: `ORDER BY` on a huge table

`ORDER BY` forces BigQuery to materialise and sort the entire result set before returning the first row. On a small result this is free; on a large one it is a memory spill and a very long wait.

```sql
-- Sorts the entire result set. On 100M rows, this spills.
SELECT event_id, amount_eur
FROM fact_events
ORDER BY amount_eur DESC
LIMIT 100;
```

**The optimisation that always works: order after limit, using a subquery or a window function.**

```sql
-- WRONG: sorts everything, then keeps 10.
SELECT event_id, amount_eur
FROM fact_events
ORDER BY amount_eur DESC
LIMIT 10;

-- RIGHT: takes 10 first (no sort), then sorts 10 rows.
SELECT event_id, amount_eur
FROM (
  SELECT event_id, amount_eur
  FROM fact_events
  WHERE event_dt BETWEEN '2026-01-01' AND '2026-01-15'
  ORDER BY amount_eur DESC
  LIMIT 10
)
ORDER BY amount_eur DESC;
```

**But BigQuery already does this optimisation** — the "top-N" rewrite. BigQuery recognises `ORDER BY ... LIMIT n` and converts it into a bounded top-N, avoiding the full sort. This is why the second version above is mostly for *other* engines, and why it is not the important point.

**The important point is different: `ORDER BY` disables the streaming result buffer.** BigQuery normally streams results back as they are produced, so a client can start processing rows immediately. With `ORDER BY`, it must finish the sort first, so the client waits for the entire query. For an interactive query that is a latency problem. For a **scheduled query writing to a table**, `ORDER BY` is pure waste — the table has no order, and the sort cost is real.

**The rule:** `ORDER BY` is a presentation concern. Do it in the BI tool, in the client, or not at all. In a scheduled query writing to a table, omit it. If the output genuinely must be ordered, `ORDER BY` on a *partitioned* table with a `LIMIT` is fine, and `ORDER BY` on the clustering column is cheaper because the data is already sorted.

**The related trap: `ORDER BY` on a non-clustered column in a partitioned table** forces a full sort of the partition, which for a large partition is a spill to disk. If you genuinely need ordering, cluster by that column.

### The complete optimisation checklist

Run through this before any query that will run in production or on a schedule.

```text
□  Columns: is every column I select actually needed? No SELECT *.
□  Partitions: does the query have a partition filter that prunes?
             Is it a literal or a parameter that still prunes?
             Check with a dry run.
□  Clustering: do the non-partition filters hit a clustering column?
□  Joins: how many bytes enter the shuffle? Can the join be removed
          by denormalising or by nesting?
□  Repeats: is this query re-reading data another query already read?
            Should it be a materialised view or an aggregate table?
□  Sort: is ORDER BY needed? If yes, is it on the clustering column?
□  Cache: would the query result cache serve this? (Identical query,
          same day, unmodified tables.)
□  Cost: what is the dry-run bytes billed? Is that acceptable?
□  Shape: is the result small? (A query returning 10M rows to a BI
           tool is a design problem, not a query problem.)
```

---

## 🛠️ Hands-On

### 1. Build the cost model of an optimisation

The first step of every optimisation is a number. This establishes the baseline and the target.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, BIGQUERY_ONDEMAND_PER_TB


def scan_cost(scanned_tb: float) -> float:
    """Return the USD cost of scanning a given number of TB.

    Args:
        scanned_tb: The TB scanned.

    Returns:
        The cost in USD.
    """
    return estimate(
        "bigquery",
        scanned_tb=scanned_tb,
        monthly=False,
        apply_free_tier=False,
    ).total


scenarios = {
    "unpartitioned full scan": 1.0,
    "partitioned, one day of 100": 1.0 * 0.01,
    "clustered, one region of 4": 1.0 * 0.01 * 0.25,
    "dashboard, 30 queries a day": 0.01 * 30,
}

for name, tb in scenarios.items():
    print(f"{name:32s} {tb:8.4f} TB  ${scan_cost(tb):10.4f}")

print(f"\nOn-demand price: ${BIGQUERY_ONDEMAND_PER_TB} per TB")
```

The numbers give the shape of the whole optimisation story:

```text
unpartitioned full scan         1.0000 TB  $   6.2500
partitioned, one day of 100     0.0100 TB  $   0.0625
clustered, one region of 4      0.0025 TB  $   0.0156
dashboard, 30 queries a day     0.3000 TB  $   1.8750
```

The dashboard line is the important one: a modest-looking dashboard, reading a partitioned table, costs **$1.88 per day, $56 per month** — for a table that is only 1 TB. Multiply by the number of dashboards and it is a line item nobody budgeted. The same dashboard on an unpartitioned table costs $187.50 per day.

### 2. Model partition pruning with the project's own helpers

The project has the partition logic; the optimisation chapter gives it a price.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    aggregate_events,
    build_bigquery_rows,
    estimated_scan_bytes,
    estimated_scan_tb,
    filter_rows_for_partition,
    ingest_events,
    partition_for_date,
    partition_for_event,
    suggest_partitioning,
)


def load_normalised_rows(path: str) -> list[dict]:
    """Load raw CSV lines and normalise them into BigQuery-shaped rows.

    The partition helpers work on normalised events, because the derived
    ``event_dt`` column is what a BigQuery table would actually be
    partitioned by.

    Args:
        path: Path to the raw CSV.

    Returns:
        The BigQuery-shaped rows.
    """
    with open(path, encoding="utf-8") as handle:
        lines = [line.rstrip("\n") for line in handle if line.strip()]
    accepted, _ = ingest_events(lines)
    return build_bigquery_rows(accepted)


rows = load_normalised_rows("sample_data/events.csv")

partition_col = suggest_partitioning(rows)
print("partition column:", partition_col)

target_date = "2026-01-15"
partition = partition_for_date(target_date)
print("partition decorator:", partition)

# The bytes a full scan would read.
full_bytes = estimated_scan_bytes(rows, partitioned=False)
print(f"full scan: {full_bytes:,} bytes ({estimated_scan_tb(rows, partitioned=False):.9f} TB)")

# The bytes a pruned scan reads.
pruned_bytes = estimated_scan_bytes(rows, partitioned=True, partition_prune_ratio=0.01)
print(f"pruned scan: {pruned_bytes:,} bytes ({estimated_scan_tb(rows, partitioned=True):.9f} TB)")

# The rows the pruned scan actually returns.
pruned_rows = filter_rows_for_partition(rows, partition)
print(f"rows after partition filter: {len(pruned_rows)}")

# Verify the aggregate is unchanged by pruning.
full_summary = aggregate_events(rows)
pruned_summary = aggregate_events(pruned_rows)
print("full summary:", full_summary)
print("pruned summary:", pruned_summary)
```

The critical check is the last one: **pruning must not change the answer.** If the pruned aggregate differs from the full aggregate, the partition logic is wrong — and that is a correctness bug that will only show up as a discrepancy between a dashboard and a manual query. This is exactly the kind of thing that must be a test, because the cost saving makes the failure look intentional.

### 3. Compute the cost of the schema choices

Nested versus flat versus joined — priced on the same data.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate
from pipeline_logic import aggregate_events, build_bigquery_rows, ingest_events


def load_normalised_rows(path: str) -> list[dict]:
    """Load raw CSV lines and normalise them into BigQuery-shaped rows.

    ``build_bigquery_rows`` expects *normalised* events, not raw CSV
    dicts: it relies on the derived columns (``event_dt``, ``amount_eur``)
    that ``ingest_events`` produces. Going through the pipeline is not
    incidental here — it is the same path production takes.

    Args:
        path: Path to the raw CSV.

    Returns:
        The BigQuery-shaped rows.
    """
    with open(path, encoding="utf-8") as handle:
        lines = [line.rstrip("\n") for line in handle if line.strip()]
    accepted, rejected = ingest_events(lines)
    print(f"ingest: {len(accepted)} accepted, {len(rejected)} rejected")
    return build_bigquery_rows(accepted)


bq_rows = load_normalised_rows("sample_data/events.csv")

# Flat: one row per event, dimension attributes denormalised onto it.
flat = [
    {
        "event_id": r["event_id"],
        "event_dt": r["event_dt"],
        "region_code": r["region"],
        "channel_code": r["channel"],
        "event_type": r["event_type"],
        "amount_eur": r["amount_eur"],
    }
    for r in bq_rows
]

# Nested: the same data with the region as a struct.
nested = [
    {
        "event_id": r["event_id"],
        "event_dt": r["event_dt"],
        "region": {"code": r["region"], "name": r["region"]},
        "channel_code": r["channel"],
        "amount_eur": r["amount_eur"],
    }
    for r in bq_rows
]

print(f"flat rows: {len(flat)}   nested rows: {len(nested)}")

# Compare the bytes read by each shape for the same aggregate.
def shape_bytes(records: list[dict], select: list[str]) -> int:
    """Estimate the bytes read by a projection over records.

    Args:
        records: The records.
        select: The columns selected.

    Returns:
        The estimated bytes read.
    """
    import json
    total = 0
    for record in records:
        total += len(json.dumps({k: record[k] for k in select}))
    return total


flat_bytes = shape_bytes(flat, ["region_code", "amount_eur"])
nested_bytes = shape_bytes(nested, ["region", "amount_eur"])

print(f"flat projection:   {flat_bytes:,} bytes")
print(f"nested projection: {nested_bytes:,} bytes")

# The joined shape reads the fact table AND the dimension table,
# then shuffles both. The dimension is tiny but the shuffle is not free.
fact_bytes = shape_bytes(flat, ["region_code", "amount_eur"])
dim_bytes = shape_bytes(
    [{"region_code": r["region_code"]} for r in flat[:4]], ["region_code"]
)
print(f"joined: fact {fact_bytes:,} + dim {dim_bytes:,} + shuffle of both sides")
```

The numbers make the point that surprises people: the nested shape reads **more** bytes than the flat one for a simple projection, because the struct carries the field names twice. Nesting is not free. It pays when it eliminates a join — that is the only case where the extra bytes are worth it. The rule is not "nest more"; it is "nest when the join you eliminate is bigger than the duplication you add".

### 4. Model the incremental refresh, and prove the idempotency

The incremental aggregate is the pattern that scales. This proves it produces the same answer as a full recomputation, and that running it twice changes nothing.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    aggregate_events,
    build_bigquery_rows,
    filter_rows_for_partition,
    ingest_events,
    partition_for_date,
)


def load_normalised_rows(path: str) -> list[dict]:
    """Load raw CSV lines and normalise them into BigQuery-shaped rows.

    Args:
        path: Path to the raw CSV.

    Returns:
        The BigQuery-shaped rows.
    """
    with open(path, encoding="utf-8") as handle:
        lines = [line.rstrip("\n") for line in handle if line.strip()]
    accepted, _ = ingest_events(lines)
    return build_bigquery_rows(accepted)


bq_rows = load_normalised_rows("sample_data/events.csv")

TARGET = "2026-01-15"
partition = partition_for_date(TARGET)


def refresh_partition(all_rows: list[dict], logical_date: str,
                      existing: dict[str, dict]) -> dict[str, dict]:
    """Recompute one partition of the daily aggregate, idempotently.

    Args:
        all_rows: All rows in the fact table.
        logical_date: The partition to refresh.
        existing: The current contents of the aggregate table.

    Returns:
        The updated aggregate table.
    """
    result = dict(existing)
    affected = filter_rows_for_partition(all_rows, partition_for_date(logical_date))
    summary = aggregate_events(affected)
    result[logical_date] = {
        region: dict(values) for region, values in summary.items()
    }
    return result


# Full recomputation, for comparison.
full = {TARGET: aggregate_events(bq_rows)}

# Incremental, run twice.
state: dict[str, dict] = {}
state = refresh_partition(bq_rows, TARGET, state)
first = {k: dict(v) for k, v in state.items()}
state = refresh_partition(bq_rows, TARGET, state)
second = {k: dict(v) for k, v in state.items()}

print("full recompute: ", full[TARGET])
print("incremental #1: ", first[TARGET])
print("incremental #2: ", second[TARGET])
print("idempotent:", first == second)
print("matches full:", full[TARGET] == second[TARGET])
```

The two assertions at the bottom are the ones that belong in CI:

- **Idempotent:** running the refresh twice gives the same result. This is what makes a retry after a failure safe.
- **Matches full:** the incremental result equals a full recomputation. This catches a partition filter that prunes too much.

The expected output for the course data:

```text
full recompute:  {'AMER': {'event_count': 1238, 'revenue_eur': 464848.02}, ...}
incremental #1:  {'AMER': {'event_count': 1238, 'revenue_eur': 464848.02}, ...}
incremental #2:  {'AMER': {'event_count': 1238, 'revenue_eur': 464848.02}, ...}
idempotent: True
matches full: True
```

### 5. Write the query linting rules as code

A checklist that a machine can enforce is worth more than a checklist that a human must remember. This is a linter for the rules in this chapter.

```python
import re
from dataclasses import dataclass, field


@dataclass
class QueryFinding:
    """One problem found in a query.

    Attributes:
        rule: The rule identifier.
        severity: "error" or "warning".
        message: What is wrong.
        suggestion: What to do instead.
    """

    rule: str
    severity: str
    message: str
    suggestion: str


@dataclass
class QueryLinter:
    """A linter for BigQuery SQL, focused on bytes read.

    Attributes:
        findings: The findings, in the order they were detected.
        partitioned_tables: Tables known to be partitioned.
    """

    partitioned_tables: set[str] = field(default_factory=set)
    findings: list[QueryFinding] = field(default_factory=list)

    def lint(self, sql: str) -> list[QueryFinding]:
        """Lint a query.

        Args:
            sql: The SQL text.

        Returns:
            The findings.
        """
        self.findings = []
        lowered = sql.lower()

        # Rule 1: no SELECT *.
        if re.search(r"select\s+\*", lowered):
            self.findings.append(QueryFinding(
                rule="no-select-star",
                severity="error",
                message="SELECT * reads every column, including wide ones",
                suggestion="List the columns explicitly",
            ))

        # Rule 2: a partition filter must be present and literal.
        if any(table in lowered for table in self.partitioned_tables):
            has_partition_filter = re.search(
                r"where[^;]*?(event_dt|_partitiontime|date)\s*"
                r"(between|=|>=|<=|>|<|in)", lowered
            )
            if not has_partition_filter:
                self.findings.append(QueryFinding(
                    rule="missing-partition-filter",
                    severity="error",
                    message="no partition filter; the query reads every partition",
                    suggestion="Add a literal WHERE on the partition column",
                ))
            elif re.search(r"where[^;]*?between\s+@\w", lowered):
                self.findings.append(QueryFinding(
                    rule="parameterised-partition-filter",
                    severity="warning",
                    message="a parameterised partition filter may not prune",
                    suggestion="Use a literal date range or a partitioned view",
                ))

        # Rule 3: ORDER BY in a scheduled query is waste.
        if "order by" in lowered and "limit" not in lowered:
            self.findings.append(QueryFinding(
                rule="order-without-limit",
                severity="warning",
                message="ORDER BY without LIMIT forces a full sort and blocks streaming",
                suggestion="Drop the ORDER BY or add a LIMIT",
            ))

        # Rule 4: a join needs a partition filter on both sides.
        join_count = lowered.count(" join ")
        if join_count and not re.search(r"on\b", lowered):
            self.findings.append(QueryFinding(
                rule="join-without-condition",
                severity="error",
                message="a join without an ON clause is a cross join",
                suggestion="Add an explicit join condition",
            ))

        return self.findings


linter = QueryLinter(partitioned_tables={"fact_events"})

queries = {
    "select star": "SELECT * FROM `p.curated.fact_events`",
    "no filter": (
        "SELECT event_id, amount_eur FROM `p.curated.fact_events` "
        "GROUP BY event_id"
    ),
    "good": (
        "SELECT event_id, region_key, amount_eur "
        "FROM `p.curated.fact_events` "
        "WHERE event_dt BETWEEN '2026-01-01' AND '2026-01-15'"
    ),
    "sorted": (
        "SELECT event_id, amount_eur FROM `p.curated.fact_events` "
        "WHERE event_dt = '2026-01-15' ORDER BY amount_eur DESC"
    ),
}

for name, sql in queries.items():
    findings = linter.lint(sql)
    print(f"{name}: {len(findings)} finding(s)")
    for finding in findings:
        print(f"    [{finding.severity}] {finding.rule}: {finding.message}")
```

This is deliberately small, and deliberately the right shape. Three of the seven checklist items are mechanical — `SELECT *`, missing partition filter, `ORDER BY` without `LIMIT` — and those are the ones that keep coming back. Put the linter in CI and the error-severity findings fail the build.

---

## 🛠️ Common Errors and Fixes

### 1. The query that reads the whole table

```text
-- The query is fast. The bill is not.
-- dry_run output:
-- Total bytes processed: 1,204,382,400
-- Total bytes billed:    1,204,382,400
```

A dashboard with a date filter that compiles to a parameterised predicate. The partition filter is present in the SQL but BigQuery cannot evaluate it at plan time, so nothing prunes and every partition is read.

The fix is a **partitioned view** — a view whose definition contains literal partition bounds, so the optimiser intersects them with the query's bounds:

```sql
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated_us-central1.v_fact_events` AS
SELECT event_id, event_dt, event_ts, region_key, channel_key, amount_eur
FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
WHERE event_dt BETWEEN DATE '2026-01-01' AND DATE '2026-12-31';
```

```sql
-- Now the dashboard queries the view; the narrower filter still prunes.
SELECT region_key, SUM(amount_eur)
FROM `YOUR_PROJECT_ID.curated_us-central1.v_fact_events`
WHERE event_dt BETWEEN '2026-03-01' AND '2026-03-31'
GROUP BY region_key;
```

Verify with a dry run before and after — the bytes processed should drop by the ratio of the date ranges.

### 2. `ORDER BY` on a huge table

```text
ERROR: Resources exceeded during query execution: Your query would process
too many bytes, please split it into smaller queries, or use a partition filter
```

or, when the query does complete but the client hangs:

```text
-- Client waits 4 minutes with zero rows returned.
-- The query is sorting 2 TB to produce 20 rows.
```

The fix is to bound the sort and let the engine do a top-N rather than a full sort:

```sql
-- Correct: the LIMIT bounds the sort.
SELECT event_id, amount_eur
FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
WHERE event_dt BETWEEN '2026-01-01' AND '2026-01-15'
ORDER BY amount_eur DESC
LIMIT 100;
```

And in a **scheduled query writing to a table**, drop the `ORDER BY` entirely — a table has no order, and the sort is pure cost:

```sql
-- Scheduled query: no ORDER BY.
SELECT event_dt, region_key, COUNT(*) AS event_count, SUM(amount_eur) AS revenue_eur
FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
WHERE event_dt = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY event_dt, region_key;
```

### 3. `Invalid partition filter` / the partition column is not the one you think

```text
ERROR: Column event_dt is not partitioned on table
your-project:curated_us-central1.fact_events
```

or the subtler version:

```text
-- The query works but scans everything:
-- WHERE event_date = '2026-01-15'
-- when the table is partitioned by event_dt.
```

A filter on a *similar* column name does not prune. BigQuery requires the filter to reference the **exact partition column**. Note also that a partition filter on a `DATE`-partitioned table must be a `DATE` literal, and a `TIMESTAMP` partition filter needs a `TIMESTAMP`.

The fix — check the actual schema before writing the filter:

```bash
bq show --schema --format=json YOUR_PROJECT_ID:curated_us-central1.fact_events
```

```python
from google.cloud import bigquery

client = bigquery.Client()
table = client.get_table("YOUR_PROJECT_ID.curated_us-central1.fact_events")
print("partitioning:", table.time_partitioning)
print("clustering:", table.clustering_fields)
```

### 4. `exceeded rate limits` from a fan-out dashboard

```text
ERROR: 400 Bad Request: Job exceeded rate limits: resources: too many concurrent queries
```

Thirty dashboard tiles, each running its own query, each running its own sub-query, all firing on page load. The fix is to reduce the number of jobs:

- **One query, not thirty.** Join the tiles' data together in a single query with `UNION ALL` or a conditional aggregate, and let the BI tool split the result.
- **Query an aggregate table**, not the fact table. A tile reading `fact_daily_region` scans kilobytes; the same tile reading `fact_events` scans gigabytes.
- **Materialise the expensive tiles** and let the refresh happen on a schedule.

### 5. The join that costs more than both tables

```text
-- dry run:
-- fact_events:   120 GB read
-- dim_customer:  40 MB read
-- Total bytes processed: 4.6 GB
```

The read was 120 GB; the cost was 4.6 GB, because the join shuffled both sides. This is the case that surprises people most, and the reason is worth understanding: **a join reads its inputs twice** — once to scan, once to shuffle — and the shuffle carries the full joined width.

The fixes, in order of preference:

1. **Denormalise** the dimension attributes into the fact. The join disappears. (Chapter 3.4's lakehouse, or a classic star with a curated wide fact.)
2. **Aggregate before joining.** If the dashboard needs "revenue by region by month", aggregate the fact to monthly grain *first*, then join the (much smaller) monthly result to the dimension.
3. **Cluster the join key.** If the join must stay, cluster both tables on the key so the shuffle is a hash partition rather than a broadcast — this mainly reduces memory, not bytes.

```sql
-- Fix 2, concretely: aggregate first, then join.
WITH monthly AS (
  SELECT DATE_TRUNC(event_dt, MONTH) AS month, region_key, SUM(amount_eur) AS rev
  FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
  WHERE event_dt BETWEEN '2026-01-01' AND '2026-12-31'
  GROUP BY month, region_key
)
SELECT m.month, r.region_name, m.rev
FROM monthly m
JOIN `YOUR_PROJECT_ID.curated_us-central1.dim_region` r USING (region_key)
ORDER BY m.month, r.region_name;
```

### 6. The `CREATE TABLE AS SELECT` that inherits `SELECT *`

```text
ERROR: Column order mismatch for column amount_eur
```

or the silent version: the new table has 20 columns because the source had 20 columns, and the downstream `INSERT ... SELECT (a, b, c)` now fails with "Number of columns in INSERT does not match".

The fix is to never use `SELECT *` in a DDL, and to state the schema explicitly:

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated_us-central1.fact_daily_region` (
  event_dt    DATE   NOT NULL,
  region_key  INT64  NOT NULL,
  event_count INT64  NOT NULL,
  revenue_eur FLOAT64 NOT NULL
)
PARTITION BY event_dt
CLUSTER BY region_key
AS
SELECT event_dt, region_key, COUNT(*) AS event_count, SUM(amount_eur) AS revenue_eur
FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
WHERE event_dt BETWEEN '2026-01-01' AND '2026-12-31'
GROUP BY event_dt, region_key;
```

Note the explicit column list, the explicit partitioning and clustering, and the partition filter in the `AS` clause. Every one of those is a decision; a `SELECT *` version makes none of them.

---

## 💡 Production Notes

- **Dry-run every query that will run more than once.** `bq query --dry_run` is free and prints the bytes billed. Put it in CI for every SQL file, and fail the build if the bytes exceed a threshold you set. This is the highest-leverage five minutes in a data team's week.
- **Make "no `SELECT *`" a lint rule, not a code-review habit.** Review habits lose to deadlines; a linter does not. `SELECT *` in production SQL is a schema-coupling bug that will fire when someone adds a column.
- **Partition on the column you filter by, and add clustering before the backfill.** Adding clustering after a 2 TB backfill means the history is unclustered until it is rewritten. Physical reordering applies to new data automatically — so get the schema right before the data arrives.
- **Watch `INFORMATION_SCHEMA.JOBS` weekly, grouped by bytes billed.** The top five queries by bytes are usually 80% of the spend and usually have an obvious fix — a missing partition filter or a `SELECT *`.
- **Cache aggressively with the query result cache, but know its limits.** It is on by default and caches identical query text against unmodified tables for 24 hours. It is defeated by different whitespace, a `current_timestamp()` in the text, or any table modification. Do not rely on it; do not fight it either.
- **Make every aggregate refresh idempotent and test it.** Run the job twice, compare, and fail the build if the second run differs. A retried scheduled query that appends doubles your revenue figures, and the doubling is discovered by Finance, not by you.
- **Materialise the recurring aggregates, and measure the refresh cost.** If the refresh costs as much as the queries it replaces, you have added cost, not removed it. Compare the refresh's bytes against the total bytes of the queries it serves.
- **Set per-team budgets and alerts on bytes billed, not on total cost.** BigQuery's budget alerts lag. An alert on `INFORMATION_SCHEMA.JOBS` bytes by `job_id` prefix gives you a same-day signal.
- **Do not tune the query plan before you have tuned the read.** Most BigQuery performance problems are bytes problems. Fix the read (partition, cluster, project fewer columns), then look at the plan.

---

## 🔑 Key Takeaways

- **The bytes-billed rule is the whole chapter.** BigQuery charges for bytes read, not rows returned, not time taken, not work done.
- **Adding a `WHERE` clause does not reduce bytes read — unless it enables pruning.** Pruning is a metadata operation; filtering is a data operation. Only one of them is billed.
- **Never `SELECT *` in production.** It reads every column and couples your query to the schema. A lint rule beats a review habit.
- **Partition on the column you filter by.** Partitioning skips whole partitions; clustering skips row groups within a partition. They compose and solve different problems.
- **A parameterised partition filter may not prune.** Use literals or a partitioned view. Always verify with a dry run.
- **Nested and repeated schemas eliminate joins**, which is the largest cost in a multi-table query — but they add duplication. Nest when the join you remove is bigger than the bytes you add.
- **Denormalisation in a warehouse is not a cache; it is immutable history.** The dimension attributes on a fact row are correct *as of the event*, and that is the point.
- **Stop recomputing the same aggregate.** Materialised views, aggregate tables at their own grain, and incremental partition-level refresh are the patterns that scale.
- **`ORDER BY` is a presentation concern.** It blocks streaming, costs a sort, and is pure waste in a scheduled query writing to a table.
- **Measure before and after.** Dry run first, `INFORMATION_SCHEMA.JOBS` weekly, and a lint rule in CI. Every claim in this chapter has a number attached.

---

## 📚 Practice Exercises

1. **Cost every query in the course project.** Take the queries implied by `pipeline_logic` — the ingest count, the region aggregate, the hourly window aggregate, the partition-filtered extract — and price each at realistic table sizes (1 TB, 10 TB, 100 TB) with and without partitioning and clustering. Produce a table showing the cost under each configuration, and identify the configuration with the lowest cost at each scale. Use `estimate()` and `estimated_scan_tb()`.
2. **Build the full query linter.** Extend the `QueryLinter` from the Hands-On section to cover: unqualified column references in a join, `SELECT` expressions that are constant-folded, a missing `LIMIT` on a query whose projection is `SELECT *`, `ORDER BY` on a column that is not clustered, and a join where the smaller table is not the build side. Test it against twenty queries — ten bad, ten good — and confirm it catches all ten bad ones without false positives.
3. **Prove the incremental refresh is safe under late-arriving data.** Extend the incremental refresh to handle a row that arrives two days late. Show that: (a) the day it belongs to is recomputed correctly, (b) the refresh is still idempotent, (c) the final state matches a full recomputation. Then add a check that detects the case where a late arrival was *not* picked up — the failure mode that silently under-reports revenue.
4. **Design the schema for a real dashboard.** Take a dashboard with five tiles — revenue by region, revenue by channel, top 10 customers, hourly trend, and a cohort retention matrix — and design the tables that serve it. For each tile: the table, its grain, its partitioning, its clustering, and the estimated bytes read per refresh. Then compare the total against a single denormalised fact table with no aggregate tables, and explain what you would build first.
5. **Model the BI fan-out.** Write `estimate_fanout(tiles: list[dict], days: int = 30) -> dict` that takes a list of dashboard tiles (each with a table, a filter, and a query type) and computes the monthly cost of the dashboard under three strategies: (a) each tile queries the fact table directly, (b) each tile queries a daily aggregate table, (c) the tiles are consolidated into one query. Show the numbers and state the break-even point at which consolidation pays for its complexity.
6. **Write the query-plan reading guide as code.** Write `explain_plan(plan: dict) -> str` that takes a simplified query plan (stages with `bytes_read`, `rows_read`, `rows_output`, `slot_ms`) and produces a diagnosis: "read-dominated", "shuffle-dominated", "filter-not-pruning", or "good". Apply it to five plans, including the 1.2 TB-read / 4-row-output case from the Concept section.
7. **Cost the optimisation portfolio for a year.** Using `compare_architectures()` and `estimate()`, build the one-year cost of: (a) an unpartitioned warehouse with a BI dashboard, (b) a partitioned warehouse with the same dashboard, (c) a partitioned + clustered warehouse with aggregate tables, (d) a flat-rate reservation sized to the steady baseline plus on-demand for the burst. Show the total for each, the saving from each optimisation step, and the month at which flat rate overtakes on-demand.

---

## 📖 Further Reading

- [BigQuery pricing](https://cloud.google.com/bigquery/pricing) — the per-byte and per-slot models in full
- [BigQuery cost optimisation best practices](https://cloud.google.com/bigquery/docs/best-practices-cost-optimization) — Google's own guidance on partition, cluster and project
- [Using partition and cluster tables](https://cloud.google.com/bigquery/docs/partitioned-tables) — the partitioning and clustering reference
- [BigQuery partitioned views](https://cloud.google.com/bigquery/docs/partitioned-views) — how to force pruning with dynamic filters
- [BigQuery materialized views](https://cloud.google.com/bigquery/docs/materialized-view-concepts) — when a materialised view pays
- [BigQuery query plans](https://cloud.google.com/bigquery/docs/query-plans) — reading the plan
- [BigQuery best practices for query performance](https://cloud.google.com/bigquery/docs/best-practices-performance) — the engine's own guidance
- [BigQuery INFORMATION_SCHEMA jobs](https://cloud.google.com/bigquery/docs/information-schema-jobs) — the metadata behind every optimisation decision
- [Dremel: Interactive Analysis of Web-Scale Datasets](https://research.google/pubs/pub36632/) — the paper behind the engine
