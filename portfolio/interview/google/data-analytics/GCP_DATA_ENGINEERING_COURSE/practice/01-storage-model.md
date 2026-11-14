# 1 — BigQuery's Storage Model

> **Practice Module 1 · BigQuery · 45 minutes**

## 🎯 What you will learn

- The five components that make up BigQuery, and the memory trick that keeps them in order.
- How BigQuery separates storage from compute, and why that separation is the whole design.
- How columnar storage turns "read less" into "pay less".
- What BigQuery actually bills for, in the three units that matter.
- How to defend BigQuery in an architecture review against PostgreSQL, Snowflake or Redshift.

---

## 🧠 Concept

### The five components

| Component | Purpose | Remember |
|---|---|---|
| Serverless | Google manages infrastructure | No server management |
| Colossus | Distributed storage system | Where data lives |
| Capacitor | Compressed columnar storage format | How data is organized |
| Dremel | Distributed query execution engine | How SQL is processed |
| Slots | Virtual compute units | Resources executing queries |

### The memory trick

```text
S → C → C → D → S

Serverless → Colossus → Capacitor → Dremel → Slots
```

Read it as a journey of a single query. You start at **Serverless** — you never touch a server.
Your data sits in **Colossus**, the distributed storage system. It is stored in **Capacitor**,
Google's compressed columnar format. **Dremel** takes your SQL and executes it across the fleet.
And the actual compute doing the work is **Slots**.

If you can say those five sentences in order, you can answer "what is BigQuery and how does it
work internally" at any level of seniority.

### Why serverless is a real architectural claim, not a marketing word

Most warehouses have a shape: a cluster of machines that hold data, and the same or adjacent
machines that compute over it. Capacity planning is the hard part — you size the cluster for the
peak, you pay for the trough, and a re-shard is a procurement event.

BigQuery separates the two. **Colossus** stores data, **Dremel + Slots** compute over it, and
Google's network — petabit scale — connects them. Storage and compute scale independently. A
dataset does not live on a disk that must be attached to a compute node; a query borrows slots for
as long as it runs and returns them.

The practical consequence: **there is no cluster to size, and no re-shard to plan.** The two
things that consume most of an engineer's time in a self-managed warehouse simply do not exist
here. What replaces them is cost discipline — because the resource is metered per byte and per
slot-hour, and both are visible on the bill.

### How columnar storage turns "read less" into "pay less"

BigQuery stores data **column by column, in blocks**. Two consequences follow, and together they
are the whole optimisation story:

1. **Column pruning.** A query that selects `store_id` and `sales_amount` reads only those two
   columns. The other columns are never opened. Their bytes are never billed.
2. **Block pruning.** Because columns are also sorted and grouped into blocks, a filter on a
   clustered column can skip entire *blocks* within the remaining columns.

Both are reductions in **bytes scanned**, and bytes scanned is the billing unit. This is the
mechanism behind every "how do I make this cheaper" question in BigQuery: you are not asking the
engine to be faster, you are asking it to *read fewer bytes*. If a query change does not reduce
bytes scanned, it did not reduce the on-demand bill.

### What BigQuery bills for

| Unit | Price (`us-central1`) | Charged when |
|---|---:|---|
| On-demand bytes scanned | $6.25 per TB | Every query, under on-demand pricing |
| Slot-hour | $0.06 | Under capacity/flat-rate pricing |
| Active logical storage | per GB-month | Your data sits in BigQuery |
| Long-term logical storage | per GB-month | Data older than 90 days |

Two of these are usually conflated. **Storage** is what you keep; **scan** is what you read. A
table can cost almost nothing to store and a fortune to query, and that asymmetry is why
"our warehouse bill is huge" is nearly always a *scan* problem, not a *storage* problem.

> **The free-tier trap.** The monthly free tier includes 1 TB of scanned bytes. If you model a
> 1 TB query with a free tier applied, the answer is `$0.00` — and you will conclude that BigQuery
> is free. It is not. The course's cost model reproduces this exactly, and module 2 of the
> `interview/` bank explains why.

---

## 🛠️ Hands-On

### 💻 Runs locally — the 100× partition win

This is the single most important number in BigQuery. It is worth typing out rather than
reading, because the number is what you say in the interview.

```python
import sys
sys.path.insert(0, "../project/core")
from pipeline_logic import estimated_scan_bytes

rows = [
    {"event_id": f"e{i}", "user_id": f"u{i}", "event_dt": "2026-01-15",
     "region": "AMER" if i % 2 else "EMEA", "amount_eur": 10.0}
    for i in range(4800)
]

full = estimated_scan_bytes(rows, partitioned=False)
pruned = estimated_scan_bytes(rows, partitioned=True, partition_prune_ratio=0.01)

print(f"unpartitioned bytes: {full:,}")
print(f"pruned to 1% bytes:  {pruned:,}")
print(f"reduction:           {full / pruned:.0f}x")
```

Expected output:

```text
unpartitioned bytes: 501,780
pruned to 1% bytes:  5,017
reduction:           100x
```

The byte count is the serialised length of the rows, so it depends on how wide your schema is —
change the columns and the number moves. The **ratio** is the number that generalises: pruning
one partition out of a hundred cuts the scan by 100×, whatever the row width.

The same shape at real scale, using the course's cost model:

```python
import sys
sys.path.insert(0, "../project/core")
from cost_model import estimate

# A 10 TB table, scanned whole, versus the same table pruned to one partition.
whole = estimate("bigquery", scanned_tb=10.0, apply_free_tier=False).total
pruned = estimate("bigquery", scanned_tb=0.1, apply_free_tier=False).total

print(f"unpartitioned: ${whole:.2f}")
print(f"partitioned:   ${pruned:.2f}")
print(f"ratio:         {whole / pruned:.0f}x")
```

Expected output:

```text
unpartitioned: $62.50
partitioned:   $0.62
ratio:         100x
```

**$62.50 versus $0.62.** That is the answer to "how do you control BigQuery cost" — the table
layout, not the query text, did the work.

### 💻 Runs locally — the five components, in code

Each component has a measurable consequence. You can model BigQuery's behaviour without a BigQuery
account, because the model is deterministic.

```python
import sys
sys.path.insert(0, "../project/core")
from cost_model import estimate, compare_architectures, format_comparison

# Slots: compute is metered, and it is metered separately from storage.
print("=== Slots: 1000 slot-hours ===")
print(estimate("bigquery", slot_hours=1000).total)

# Colossus + Capacitor: storage is metered per GB-month, separately again.
print("\n=== Colossus: 1 TB of active logical storage ===")
print(estimate("bigquery", storage_gb=1024).total)

# Dremel: the same workload, four architectures, one comparison.
print("\n=== Dremel: the same workload, four architectures ===")
print(format_comparison(compare_architectures()))
```

Expected output:

```text
=== Slots: 1000 slot-hours ===
60.0

=== Colossus: 1 TB of active logical storage ===
20.48

=== Dremel: the same workload, four architectures ===
| Architecture | Monthly cost |
|---|---|
| Streaming on Dataflow | $0.0000 |
| Spark on Dataproc | $0.0000 |
| Batch on BigQuery (partitioned) | $0.0625 |
| Batch on BigQuery (unpartitioned) | $6.2500 |
```

Two of those rows are `$0.0000` because `compare_architectures()` defaults to
`streaming_hours=0.0`. **Never read a `$0.00` streaming row as free** — it means "no streaming
hours were configured", not "streaming is free". This is exactly the trap the course notebook
`03-price-the-architectures.ipynb` calls out, and it is worth knowing before an interviewer
finds it for you.

### 🌐 Needs a BigQuery project — see the layers for yourself

```bash
bq query --use_legacy_sql=false --format=pretty '
SELECT
  COUNT(*)                    AS rows,
  COUNT(DISTINCT region)      AS regions,
  MIN(event_date)             AS first_day,
  MAX(event_date)             AS last_day
FROM `YOUR_PROJECT_ID.YOUR_DATASET.events`
'
```

Then ask BigQuery what it actually did:

```bash
bq query --use_legacy_sql=false --format=pretty '
SELECT
  job_id,
  total_bytes_billed,
  total_bytes_processed,
  num_child_jobs,
  destination_table.dataset_id
FROM `YOUR_PROJECT_ID.region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = "QUERY"
ORDER BY job_creation_time DESC
LIMIT 10
'
```

`total_bytes_billed` is the number that appears on your invoice. `total_bytes_processed` is what
BigQuery touched. When the two diverge sharply, a cache hit or a free-tier credit is involved.

---

## 🛠️ Common Errors and Fixes

**"Why does my dry run say 0 bytes?"**

A dry run estimates bytes scanned without executing. If the query is fully satisfied by a
materialized view, or the table is empty, the estimate is genuinely zero. It is not the tool
failing.

**"I partitioned the table and my bill did not change."**

Three likely causes, in order of likelihood:

1. **The filter does not reference the partition column.** Partition pruning is a metadata
   operation on the predicate — a filter on a different column prunes nothing.
2. **The partition column is not the one you partitioned by.** Ingestion-time partitioning exposes
   `_PARTITIONDATE`, a pseudo-column, not your event timestamp.
3. **You are reading a view over the table**, and the view's definition lost the predicate.

**"The query is fast but the bill is large."**

This is the normal state of affairs, and it is worth being able to explain in one breath. Speed and
cost are both functions of bytes read, but they are not the same function: BigQuery reads bytes
*in parallel*, so a query that reads 10 TB across a thousand slots finishes in minutes, while a
query that reads 10 GB on one slot finishes in seconds. **Fast is not cheap.** The only lever
that moves both is reading fewer bytes.

**"Is BigQuery cheaper than my warehouse?"**

Only if you answer with a workload, not a price. BigQuery bills per byte scanned, so a table that
is written once and read constantly — a dashboard — is exactly the wrong shape for on-demand.
That workload wants a materialized view, or capacity pricing. Answering "BigQuery is cheap"
without this nuance is the fastest way to lose an architecture interview.

---

## 💡 Production Notes

### The L6 answer: why BigQuery instead of PostgreSQL

This is the question that separates a candidate who has read documentation from one who has
architected a system. Here is the framing that works.

**PostgreSQL** is built for transactional applications: frequent individual record reads and
writes, row-level concurrency control, and durability guarantees per transaction. It is a
fantastic operational database.

**BigQuery** is optimized for analytical workloads: large scans, aggregations, joins, and
reporting across substantial datasets. It does not do transactions, and it is not trying to.

The mistake is asking which is better. They answer different questions. The right question is
**"is this access pattern analytical or transactional?"** — and the honest answer for most
organisations is that they need both, with CDC (module 3 of this suite) carrying changes between
them. The operational database answers *"what is true now?"*; the warehouse answers *"what
happened?"*.

### How BigQuery scales

Three mechanisms, in the order they matter:

1. **Storage scales independently.** Colossus distributes data across the fleet. There is no
   primary to fail over from and no volume to extend.
2. **Compute scales independently.** Dremel distributes work across slots. More available compute
   improves parallelism.
3. **But parallelism is not the same as performance.** Query duration also depends on data
   distribution, the shuffle, query design, and available work. More slots on a badly skewed join
   makes the skew worse, not better — it distributes the waiting.

That third point is the one that shows experience. "Add more slots" is not a fix.

### How to optimise cost

| Lever | What it does | Applies to |
|---|---|---|
| Partition pruning | Skips whole partitions at the metadata level | Range filters, usually dates |
| Clustering | Skips blocks inside a partition | Equality filters and grouping |
| Column pruning | Reads only the referenced columns | Every query, automatically |
| Incremental processing | Reads only what changed | Batch pipelines |
| Materialized views | Serves a precomputed result | Dashboards, repeated queries |
| Workload monitoring | Finds the queries that cost the most | Ongoing |
| `maximumBytesBilled` | Fails a query that would cost too much | Every job, always |

Under **on-demand** pricing, reducing billed bytes generally reduces cost. Under **capacity**
pricing, you additionally optimise *slot utilisation* and reservations — because you pay for the
slots whether or not they are busy, an idle reservation is pure waste.

### The rule I write into every pipeline

Put `maximumBytesBilled` on every job. Without it, a bad join on a 40 TB table is a $250
surprise and a pager alert. With it, the job **fails fast** — which is the correct behaviour at
3am, and infinitely cheaper than succeeding expensively.

---

## 🔑 Key Takeaways

- **S → C → C → D → S.** Serverless, Colossus, Capacitor, Dremel, Slots. Say it in order.
- Storage and compute scale **independently**. That separation is the architecture, not a feature.
- BigQuery is **columnar**, so it prunes columns and blocks. Every optimisation reduces bytes
  scanned, and bytes scanned is the billing unit.
- Three billing units: **bytes scanned** (on-demand), **slot-hours** (capacity), **GB-month**
  (storage). A huge bill is almost always a scan problem.
- The free tier cancels 1 TB of scans per month. Model with `apply_free_tier=False` when you want
  the price list rather than the bill.
- **Fast is not cheap.** Both track bytes read, but parallel reads make expensive queries feel
  instant.
- BigQuery is not "better than PostgreSQL" — it answers a different question. Analytical access
  pattern, or transactional?
- More slots do not fix a skewed join. They distribute the waiting.

---

## 📚 Practice Exercises

1. Write out the five-component chain from memory — component, purpose, and what it maps to in the
   query lifecycle — and then write the one-line memory trick. Then explain the chain using a
   query you have actually run: which component held the data, which read it, which executed it,
   and which units were billed.

2. Using `estimated_scan_bytes` from `project/core/pipeline_logic.py`, build a table of scan cost
   for a 10 TB table at prune ratios of 100%, 10%, 1% and 0.1%, convert each to TB, price each at
   $6.25 per TB, and print the four figures. Confirm the ratio between the first and last is
   1000×.

3. Using `estimate` from `project/core/cost_model.py`, compute the monthly bill for a workload
   that scans 10 TB unpartitioned, then the same workload partitioned, then the same workload
   served entirely from a materialized view. Print all three and identify which one is a
   *recurring* cost and which is a one-off.

4. Explain in two minutes why `compare_architectures()` returns two `$0.00` rows by default, and
   what you would have to pass to make those two rows meaningful. Then state what each row would
   cost if you set `streaming_hours=24` and explain why the Dataproc row would be cheaper than the
   Dataflow row — and why that does not make Dataproc the right answer.

5. Using `estimate("bigquery", scanned_tb=...)`, find the scan volume at which the flat-rate cost
   of 1000 slot-hours equals the on-demand cost of the same work. Then state what you would
   recommend to a team whose query volume is 5× that threshold and 5× below it, and why the
   recommendation is not symmetric.

6. Write the argument for choosing BigQuery over PostgreSQL for a new analytics product, in
   exactly four sentences: what the workload is, what PostgreSQL does badly at it, what BigQuery
   does well at it, and what you would still need PostgreSQL for. Then flip the argument — write
   the four sentences that recommend PostgreSQL — and say which of the two products in your
   portfolio would actually benefit.

7. Take a query from the `interview/` bank that has a `$62.50` figure attached to it. Identify
   which of the seven cost levers in this module applies, state what the bytes-scanned would be
   before and after, and explain to a non-engineer why the fix was a table layout change and not
   a query rewrite.

8. Explain what would break if you removed the `maximumBytesBilled` limit from a nightly job, and
   separately, what would break if you set it too low. Both failure modes are real, both have
   different remedies, and saying only one of them is the mark of someone who has not operated
   this.

---

## 📖 Further Reading

- [BigQuery overview](https://docs.cloud.google.com/bigquery/docs/introduction)
- [BigQuery pricing](https://cloud.google.com/bigquery/pricing)
- [BigQuery quotas and limits](https://docs.cloud.google.com/bigquery/quotas)
- [Partitioned tables](https://docs.cloud.google.com/bigquery/docs/partitioned-tables)
- [Clustered tables](https://docs.cloud.google.com/bigquery/docs/creating-clustered-tables)
- [Controlling costs](https://docs.cloud.google.com/bigquery/docs/controlling-costs)
- [Cost estimation and control best practices](https://docs.cloud.google.com/bigquery/docs/best-practices-costs)
- [Course interview bank: Analytics and Cost](../interview/03-analytics-and-cost.md)
