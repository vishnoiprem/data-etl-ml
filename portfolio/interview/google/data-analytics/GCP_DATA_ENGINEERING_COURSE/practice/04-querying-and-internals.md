# 4 — Querying BigQuery and What Happens Internally

> **Practice Module 4 · BigQuery · 50 minutes**

## 🎯 What you will learn

- The four stages every BigQuery query passes through, and which one you actually optimise.
- What happens inside a single query, step by step, on a real table.
- Why a join against a small table has no shuffle at all.
- How skew turns a fast engine into a slow one.
- What AutoMode changes, and what it does not.

---

## 🧠 Concept

### The four stages

```text
SCAN → SHUFFLE → AGGREGATE → WRITE
```

Every query moves through these, though a simple `SELECT COUNT(*)` skips straight from scan to
aggregate and writes almost nothing.

| Stage | What it does | When it dominates |
|---|---|---|
| **Scan** | Reads the bytes, applying partition and column pruning | Cost — always |
| **Shuffle** | Redistributes rows by join or grouping key across workers | Wall-clock time on joins |
| **Aggregate / compute** | Groups, joins, filters, calculates | CPU |
| **Write** | Materialises the result set | Large results |

**You optimise the scan stage.** Not because the others do not matter, but because scan is what
you are billed for, and because the byte reduction you can achieve there is typically two orders
of magnitude larger than anything the later stages offer.

### The mechanics of each stage

**Scan.** BigQuery reads column blocks from Colossus. Partition pruning excludes whole
partitions at the metadata level — never opened. Column pruning excludes columns that are not
referenced. Clustering excludes blocks within the remaining columns, when the filter is
selective.

**Shuffle.** A join or a `GROUP BY` on a key other than the clustered layout requires rows with
the same key to meet. BigQuery does this by shipping rows across the network to the worker that
owns that key's partition. This is the expensive stage, and it is where **skew** happens: if one
key owns 40% of the rows, one worker does 40% of the work while the others idle.

**Aggregate.** Filtering, grouping and computing. Cheap relative to the shuffle, unless the
intermediate data is enormous — which is why pre-aggregating upstream helps.

**Write.** The output. BigQuery writes query results to a temporary location and streams them to
the client; writing to a destination table makes it durable and billable storage.

### The decisive fact about joins

> **A join against a small dimension table is a broadcast hash join with no shuffle at all.**

BigQuery can hold the small side of the join in memory on every worker. No rows cross the
network. The join becomes a local hash lookup, and the "shuffle" stage simply does not exist for
that operation.

This is why the shape of your schema matters more than the shape of your query:

- Join a 10 GB fact table to a 2 MB dimension table → broadcast, no shuffle.
- Join a 10 GB fact table to a 10 GB fact table → full shuffle, and the network is the bottleneck.

The same query text can be a broadcast or a full shuffle, depending purely on **table sizes**.
That is why "should the dimension table be in its own table?" is a real question with a real
answer: *yes, because then it stays small enough to broadcast.*

### AutoMode

BigQuery has two query-planning modes:

- The **legacy query plan**, which follows the join order and strategy you wrote.
- **AutoMode**, in which BigQuery reorders and re-strategises the plan itself.

AutoMode is the modern default. It applies optimisations you would otherwise have to write
yourself — join reordering, pushing filters down toward the scan, choosing between shuffle and
broadcast strategies based on actual table statistics.

**What AutoMode does not do:** it does not fix a schema problem. If your dimension table is
growing towards a size that can no longer be broadcast, AutoMode cannot rescue it — the
underlying cost of a full shuffle is irreducible. It optimises *the plan*; it does not change
*your data layout*.

> ⚠️ **Verify before you rely on it.** AutoMode's behaviour and its defaults have changed across
> BigQuery releases. Check the current
> [BigQuery documentation](https://docs.cloud.google.com/bigquery/docs) for the present state of
> query planning rather than trusting a remembered flag name. The interview-safe framing is:
> *"BigQuery plans queries automatically in AutoMode; I still design the table layout, because
> automatic planning cannot fix a bad layout."*

---

## 🛠️ Hands-On

### 🌐 Needs a BigQuery project — walk one query through the engine

The reference table again:

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

Now the query:

```sql
SELECT store_id, SUM(sales_amount) AS revenue
FROM `retail.analytics.sales`
WHERE sale_date = '2026-11-13'
GROUP BY store_id;
```

### What happens internally

1. **Partition pruning.** BigQuery reads only the `20261113` partition rather than scanning all
   three years. The predicate is on the partition column, so the other partitions are excluded
   from the metadata — never opened.
2. **Column pruning.** It reads only the required columns, primarily `store_id` and
   `sales_amount`. `transaction_id`, `sale_date` and `customer_id` are never opened.
3. **Parallel processing.** Dremel distributes the scanning and aggregation work across slots.
4. **Shuffle.** BigQuery may redistribute intermediate data by `store_id` to combine partial
   totals.
5. **Final result.** The query returns total revenue for each store.

**Notice that clustering by `store_id` is not especially useful for block pruning in this
particular query, because there is no selective `store_id` filter.** Clustering becomes more
beneficial when the query filters for particular stores:

```sql
-- Here clustering does the work: most blocks are skipped.
SELECT SUM(sales_amount) AS revenue
FROM `retail.analytics.sales`
WHERE sale_date = '2026-11-13'
  AND store_id = 'S-114';
```

This is the single most misunderstood point in BigQuery performance work. Clustering is often
installed "because it is best practice", and then it does nothing, because the queries do not
filter on the clustered column. **Clustering is a filter optimisation. If you never filter, it
is storage you paid for and did not use.**

### 💻 Runs locally — the shuffle, priced

You cannot run Dremel locally, but you can model the stage that actually costs you.

```python
import sys
sys.path.insert(0, "../project/core")
from cost_model import estimate

# The same 10 TB table, scanned by a query with and without a partition filter.
full = estimate("bigquery", scanned_tb=10.0, apply_free_tier=False).total
pruned = estimate("bigquery", scanned_tb=0.1, apply_free_tier=False).total

print(f"full scan:      ${full:.2f}")
print(f"pruned scan:    ${pruned:.2f}")
print(f"saving:         ${full - pruned:.2f}  ({full / pruned:.0f}x)")
```

Expected output:

```text
full scan:      $62.50
pruned scan:    $0.62
saving:         $61.88  (100x)
```

**The scan stage is where the money is.** A shuffle costs wall-clock time and slots, not bytes
scanned — and under on-demand pricing, bytes scanned is what you are billed for.

### 💻 Runs locally — why pre-aggregation upstream is a cost decision

```python
import sys
sys.path.insert(0, "../project/core")
from cost_model import estimate

# A dashboard re-aggregates the raw table 200 times a month.
RAW_TB = 10.0
READS = 200

raw = estimate("bigquery", scanned_tb=RAW_TB * READS, apply_free_tier=False).total

# The same dashboard, reading a pre-aggregated table of 0.05 TB.
PRE_AGG_TB = 0.05
pre = estimate("bigquery", scanned_tb=PRE_AGG_TB * READS,
               storage_gb=200, apply_free_tier=False).total

print(f"re-aggregate raw:     ${raw:,.2f}")
print(f"read pre-aggregated:  ${pre:,.2f}")
print(f"saving:               ${raw - pre:,.2f}  ({raw / pre:.0f}x)")
```

Expected output:

```text
re-aggregate raw:     $12,500.00
read pre-aggregated:  $66.50
saving:               $12,433.50  (188x)
```

The pre-aggregated table costs storage and a refresh job, and it removes **the shuffle** as well
as the scan — because the aggregation has already happened.

### 🌐 Needs a BigQuery project — read the query plan

```bash
bq query --use_legacy_sql=false --format=pretty '
EXPLAIN
SELECT store_id, SUM(sales_amount) AS revenue
FROM `retail.analytics.sales`
WHERE sale_date = '2026-11-13'
GROUP BY store_id
'
```

For a live job, the plan is in the job's statistics:

```sql
SELECT
  job_id,
  total_bytes_billed,
  total_bytes_processed,
  total_slot_ms,
  reservation_id
FROM `YOUR_PROJECT_ID.region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
ORDER BY job_creation_time DESC
LIMIT 5;
```

`total_slot_ms` is the compute the job consumed. Compare it against `total_bytes_billed`: a job
with small bytes and large slot time is shuffle-bound, not scan-bound. **That ratio is the
diagnostic**, and it is how you tell a "my table is too big" problem from a "my join is
skewed" problem.

---

## 🛠️ Common Errors and Fixes

**"The query is fast but scans a terabyte."**

That is the expected behaviour, not a bug. BigQuery read the columns it needed at the
column-block granularity, before your `WHERE` clause could eliminate individual rows. If you need
fewer bytes, the fix is layout — partition and cluster — not query text.

**"Why does a `WHERE` clause on a non-clustered column not reduce bytes scanned?"**

Because clustering prunes *blocks*, and blocks are only organised by the clustering columns. A
filter on an unclustered column still has to read every block that contains the partitioned
range. The rows are eliminated after the read, so the bytes are still billed.

**"The join is slow, and the tables are not that big."**

Check for **skew** before anything else:

```sql
SELECT
  store_id,
  COUNT(*) AS row_count
FROM `retail.analytics.sales`
WHERE sale_date = '2026-11-13'
GROUP BY store_id
ORDER BY row_count DESC
LIMIT 10;
```

If one key dominates, that worker is doing most of the work while the others idle. Adding slots
makes it worse, not better — it distributes the waiting. The fix is to salt the key or
pre-aggregate, not to buy more compute.

**"Adding slots did not make the query faster."**

This is the correct and expected outcome in the skew case, and also whenever the query is
bottlenecked on network transfer during the shuffle rather than on CPU. Slots add parallelism to
the stages that are CPU-bound. If the bottleneck is a single skewed worker or a network shuffle,
extra slots sit idle.

**"The join used a lot of bytes but should have been a broadcast join."**

A broadcast join requires the small side to fit in the memory available per worker. As your
dimension table grows, it crosses that threshold and becomes a full shuffle — silently, with no
error, just a slower query and a bigger bill. **Watch the size of your dimension tables.** This
is the most common way a pipeline that was fast in January becomes slow in November.

**"My query returned a different number of rows yesterday and today."**

Usually **non-deterministic aggregation**. `FLOAT64` sums are not guaranteed to be
order-independent, and parallel execution changes the order. Module 5 covers why: use `NUMERIC`
for anything that must be exact.

---

## 💡 Production Notes

### The four questions to ask about any slow query

In this order, every time:

1. **How many bytes were scanned?** If it is large, the fix is layout.
2. **Was there a shuffle?** If yes, the cost is network, and the fix is a smaller dimension
   table or pre-aggregation.
3. **Was the join key skewed?** If yes, no amount of compute fixes it.
4. **Could the small side have been broadcast instead?** If yes, split the dimension into its own
   table.

### What to optimise, and what to leave alone

| Optimise | Leave alone |
|---|---|
| Table layout (partition, cluster) | The `WHERE` clause on a clustered column |
| Splitting large dimension tables out | Join *order* — AutoMode handles it |
| Pre-aggregating for repeated dashboards | Filter expressions in general |
| Column selection in views | `SELECT *` in a *view definition* only if it is a materialized view |
| `maximumBytesBilled` on every job | Anything that requires a human to read the query |

### The performance review checklist

- [ ] Is every large table partitioned by a date?
- [ ] Is every table clustered on the columns queries actually filter on?
- [ ] Are dimension tables small enough to stay broadcastable — and is that monitored?
- [ ] Do repeated dashboard queries read a materialized view?
- [ ] Does every job have `maximumBytesBilled`?
- [ ] Is `total_slot_ms` monitored against `total_bytes_billed` to catch skew?

---

## 🔑 Key Takeaways

- **Scan → Shuffle → Aggregate → Write.** Optimise the **scan** — it is what you are billed for.
- A single query does: **partition pruning → column pruning → parallel scan → shuffle → result.**
- **Clustering only pays when you filter on the clustered column.** Aggregating over every value
  of it earns nothing.
- **A join against a small table has no shuffle.** Same query text, different table sizes,
  completely different execution plan.
- **Skew is the real cause of slow joins.** More slots distribute the waiting; they do not fix it.
- **AutoMode optimises the plan, not the layout.** It cannot rescue a dimension table that grew
  too large to broadcast.
- The diagnostic ratio: **small bytes + large slot time = shuffle-bound.**
- Use **`NUMERIC`**, not `FLOAT64`, for exact aggregates — parallel `FLOAT64` sums are not
  deterministic.

---

## 📚 Practice Exercises

1. Explain the four stages of a BigQuery query, and state which one you optimise and why. Then
   explain the difference between the stage you optimise and the stage that dominates wall-clock
   time, using a join on two large tables as the example.

2. Take the `retail.analytics.sales` query from this module and list exactly what each of the
   five internal steps does for it — which columns are read, which partitions are excluded, and
   whether a shuffle occurs. Then write the variant of the query where clustering does the work,
   and say what changes.

3. Model the cost of a dashboard that re-aggregates a 10 TB raw table 200 times a month, and of
   the same dashboard reading a pre-aggregated table, using the cost model in
   `project/core/cost_model.py`. Print both, state the break-even read count, and explain what
   the pre-aggregated table costs in storage and refresh work.

4. Explain why a join against a small dimension table has no shuffle, and describe what happens to
   that join as the dimension table grows. Then explain how you would monitor for the crossing
   point, and why the crossing is silent.

5. A colleague reports that a join over 5 GB tables takes 40 minutes. List your diagnostic steps
   in order, with the specific query or metric for each step, and state what remediation each
   finding implies.

6. Explain why `total_bytes_billed` and `total_slot_ms` should be monitored together rather than
   separately. Give the specific symptom of each of three ratios: small/large, large/large, and
   large/small, and say what each one means.

7. Describe a schema change you would make to a table that is currently slow because of a
   shuffle-bound join. Your answer must cover where the dimension table lives, whether it stays
   broadcastable, and how you would make the migration without downtime.

8. Explain the claim "AutoMode makes query optimisation unnecessary" and then refute it in
   terms of table layout, skew, and dimension table size. Finish by stating what AutoMode
   *does* let you stop worrying about.

---

## 📖 Further Reading

- [BigQuery overview](https://docs.cloud.google.com/bigquery/docs/introduction)
- [Partitioned tables](https://docs.cloud.google.com/bigquery/docs/partitioned-tables)
- [Clustered tables](https://docs.cloud.google.com/bigquery/docs/creating-clustered-tables)
- [Controlling costs](https://docs.cloud.google.com/bigquery/docs/controlling-costs)
- [Query syntax in GoogleSQL](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax)
- [Course interview bank: Analytics and Cost](../interview/03-analytics-and-cost.md)
- [Course interview bank: Top 40](../interview/top-40.md)
