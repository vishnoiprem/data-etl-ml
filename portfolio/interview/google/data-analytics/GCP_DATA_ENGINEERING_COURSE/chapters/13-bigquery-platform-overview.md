# 3.2 — BigQuery Platform Overview

> **Section 3 · Analytics & Warehousing · Lecture 3.2 · 8:00**

## 🎯 What you will learn

- How BigQuery's architecture actually works: Dremel, Colossus, and the separation of storage from compute
- The columnar storage model, row groups, and why the storage layer is invisible to you
- The resource hierarchy: organization → project → dataset → table, and what lives where
- Query execution: the distributed, slot-based model and why there are no indexes
- Editions and reservations: Standard, Enterprise, Enterprise Plus, and the capacity pricing model
- Slot-milliseconds, slot-hours, and the on-demand vs flat-rate decision
- The BQ CLI, the Python client, and scheduled queries — the three ways you actually run BigQuery
- Materialised views, and when they are worth it
- **When BigQuery is the wrong answer** — and what to use instead

---

## 🧠 Concept

### The one-sentence thesis

BigQuery is a **serverless, columnar, distributed SQL engine over a petabyte-scale storage service**, with no cluster to size, no index to maintain, and no storage/compute coupling — and you pay for exactly the bytes your queries read (or, on flat rate, for exactly the capacity you reserve).

Every design decision in the service follows from the last clause. Understanding the service means understanding which model you are buying, because **on-demand and flat-rate are two different products with different economics**, and the choice determines how your team works for the next two years.

### Storage and compute separation

The defining architectural decision. BigQuery splits the system into two independent halves:

```text
┌───────────────────────────────────────────────────────────────┐
│  COMPUTE — Google Compute Engine clusters (the "workers")      │
│  Dremel executes distributed SQL. Slots are the unit of       │
│  compute. Workers are stateless and spun up per query.        │
└───────────────────────────────────────────────────────────────┘
              ▲                        ▲
              │ reads blocks           │ reads metadata
              │                        ▼
┌───────────────────────────────────────────────────────────────┐
│  STORAGE — Colossus (Google's distributed file system)        │
│  Immutable, columnar blocks on GFS. No volume, no mount,      │
│  no capacity planning. Replicated and durable.                │
└───────────────────────────────────────────────────────────────┘
```

**Why this matters so much.** In a traditional warehouse — Teradata, Oracle, Snowflake's pre-2023 model, Hadoop/Hive — compute and storage are (or were) coupled. You provision a cluster with N nodes and M terabytes. The consequences:

- You must size the cluster. Too small, queries queue. Too large, you pay for idle compute.
- You must size the storage separately, and if you grow data past the cluster's disk you need a resize.
- Storage and compute are on different timescales, so one of them is always wrong.

BigQuery removes the coupling entirely. Storage is a service that grows on its own; compute is provisioned per query from a pool you either borrow (on-demand) or reserve (flat rate). A query that needs 500 TB scans 500 TB whether you have a cluster or not. There is no cluster to resize, no node to fail, and no "the disk is full" state.

**The consequence for the data engineer:** you stop thinking about capacity and start thinking about **bytes read**. Your unit of cost is the byte, and every architectural decision — partitioning, clustering, `SELECT *` avoidance, denormalisation — is really a decision about *how many bytes the query reads*.

### Colossus: the storage layer

Colossus is Google's distributed file system, and it is what BigQuery stores data in. The properties that matter to you:

- **Immutable.** Once a block is written, it is not modified. Updates and deletes are implemented as *new* blocks plus a metadata update marking the old ones as superseded. This is why BigQuery `UPDATE` and `DELETE` on large tables are expensive and slow: they rewrite column chunks.
- **Columnar.** Data is stored by column, not by row (chapter 3.1 covered why).
- **Distributed and replicated.** Blocks are spread across data centres and regions. A single block loss is tolerated without data loss.
- **Object-store-like interface underneath.** BigQuery's storage is not exposed as files, but the free-tier pricing recognises that reads of Cloud Storage data are free, which is why **BigLake** (chapter 3.4) is able to query Parquet/Iceberg files directly on GCS with the same engine.

**The blocks are immutable and the metadata is mutable.** The metadata (table schema, partition information, row counts, storage statistics) lives in a separate, transactional metadata store. Queries read metadata first — cheap, small, cached — and then fetch only the column blocks they need.

**This is the mechanism behind partition pruning.** When you query with a partition filter, BigQuery consults the metadata to determine which partition decorators match, and only fetches the blocks for matching partitions. No blocks for excluded partitions are read, and no bytes for them are billed.

### Dremel: the query engine

Dremel is Google's distributed, columnar query engine. Its design is from the 2010 paper *Dremel: Interactive Analysis of Web-Scale Datasets*, and three of its ideas are directly visible to you in BigQuery.

**1. Nested data and columnar execution.** Dremel's central contribution is executing over *nested* data (arrays, records) in a columnar store, without materialising the nesting. In BigQuery terms: a `REPEATED` field does not require exploding rows; the engine can push the aggregation inside the repeated record. This is why BigQuery can store nested JSON natively and still aggregate efficiently.

**2. The distributed join.** Rather than shipping one huge table to one worker, Dremel distributes it across many workers, each processing a slice, with the shuffle happening in a distributed hash join. Shuffle is the expensive part — it is where network and disk I/O happen — and it is why the *size of the join inputs* is the single biggest driver of query cost, more than the size of the scan.

**3. Massive parallelism with a fixed fan-out.** A query is broken into stages; each stage runs across hundreds or thousands of workers; the stages are connected by shuffles. This is a MapReduce-shaped pipeline with a lot more sophistication in the middle.

**What Dremel means for you:** there are no indexes, no primary keys (in the enforced sense), and no physical table design you control beyond partitioning and clustering. Query performance comes from **reducing bytes read** and **reducing shuffle volume**, nothing else.

### The resource hierarchy

```text
Organization (acme.example.com)
└── Folder (engineering)
    └── Project (gcp-de-course)          ← billing, IAM, quotas live here
        └── Dataset (curated_us-central1) ← a namespace for tables
            ├── Table (fact_events)        ← partitioned, clustered
            ├── Table (dim_region)
            ├── View (v_daily_revenue)
            ├── Materialized view (mv_daily_revenue)
            └── Routine (proc_load_events) ← SQL or JavaScript, scheduled
        └── Dataset (raw_us-central1)
            └── Table (events_raw)
```

**Project** is the unit of billing, IAM, quotas and audit. This is the practical boundary: a project is the smallest thing you can hand to a team with its own budget and its own permissions.

**Dataset** is a namespace within a project. Two things matter:

- **Datasets are regional.** A dataset lives in one location (`US`, `EU`, `us-central1`, `europe-west4`). A dataset with a `_` in the name (a *wildcard dataset*, e.g. `curated_us-central1`) exists in every region and requires the `_` to be present in the table reference. The course's local project uses exactly this convention.
- **Dataset-level access control.** `bigquery.dataViewer` on a dataset grants read on every table in it. For most BI and analyst access, dataset-level grants are the right granularity; table-level grants are for exceptions.

**Table** types, and when each is right:

| Type | Materialised? | Cost | Use when |
|---|---|---|---|
| Standard table | Yes | Storage + scan | The default. Facts, dims, staging |
| View | No | Free | A logical alias; the query is expanded each time |
| Materialised view | Yes | Storage + refresh | The same expensive subquery is queried repeatedly |
| Snapshot table | Yes | Storage | Point-in-time copy of a table, cheap to query |
| External table | External | Query the file | Data already in GCS, Parquet/CSV/ORC |
| Logical view over external | No | — | Definitions for files you do not own |

**Routine** is a SQL procedure or JavaScript function, schedulable. This is where a `CREATE OR REPLACE PROCEDURE` that loads a partition lives.

### Columnar storage, row groups, and physical reordering

BigQuery stores data as **column chunks** grouped into **row groups**. The row group is the physical unit of scanning: a few thousand rows, and for each column within it, BigQuery stores the values plus **per-block metadata** — a null count, and min/max values.

That metadata is what makes predicate pushdown fast. For a filter like `event_dt >= '2026-01-10' AND event_dt < '2026-01-11'`, BigQuery reads the min/max of the `event_dt` blocks and skips entire blocks whose range cannot match — before reading a single data value.

**Physical reordering** (formerly "clustering") takes this further. BigQuery automatically sorts data within partitions by up to four clustering columns, and stores the sort key as **min/max prefix** metadata. The effect: a filter on the leading clustering columns can prune at the *block* level, so a query touching one region reads one contiguous slice of the partition rather than the whole partition.

Note the distinction from **partitioning**, which is often confused with it:

| | Partitioning | Clustering |
|---|---|---|
| Granularity | Whole partitions, one filter column | Row-group sorting, up to 4 columns |
| Pruning mechanism | Partition decorator → skip entire partitions | Min/max prefix → skip row groups within a partition |
| Cardinality | Low (a few thousand partitions max) | High |
| Cost of adding | Rescans the table | No rescan; applied to new data |
| Best filter | Date/time range | Equality and range on high-cardinality columns |

**Partitioning** reduces the number of blocks read. **Clustering** reduces the number of blocks *within* a partition. They compose: partition by date, cluster by region, and a query for one region on one day reads a tiny fraction of a single partition.

### Query execution and slots

**A slot** is a virtual CPU used to execute a query. BigQuery measures compute in **slot-milliseconds**: the number of slots multiplied by the time they are held.

- 1 slot for 1 second = 1000 slot-milliseconds.
- 1 slot-hour = 3,600,000 slot-milliseconds = 3,600 slot-seconds.

This is the metric that appears in `INFORMATION_SCHEMA.JOBS` and in the billing export, and it is the metric that tells you whether a query is efficient. A query that scans 1 TB and takes 10 seconds on 100 slots used 1,000 slot-seconds. The same query scanning 1 TB on 10 slots took 100 seconds. **Same bytes, ten times the compute.**

**The pipeline of a query, stage by stage:**

1. **Planning.** The optimiser reads the metadata, resolves the partition decorators, and chooses a join strategy. This is where a filter on a partition column becomes a small scan instead of a large one.
2. **Distributed scan.** Workers read the required column blocks, in parallel, applying the filter as they go (predicate pushdown — the filter is applied *during* the read, not after).
3. **Shuffle.** Partial results are redistributed across workers for the join and the aggregation. **This is the expensive stage.** It writes to disk and reads across the network.
4. **Aggregation / join.** The final grouping and join.
5. **Finalisation.** Results are assembled and returned to the client.

The practical consequence: **the join is where the money is.** A scan of 1 TB costs $6.25. A join that shuffles 1 TB on each side costs roughly double, and possibly much more if the join key is skewed — because skewed keys send a disproportionate share of rows to one worker, which becomes the straggler that determines the query's wall-clock time.

### Editions

BigQuery offers three editions, differing in managed features (not in performance or scale, which are the same across all editions):

| Capability | Standard | Enterprise | Enterprise Plus |
|---|---|---|---|
| Column-level security | — | Yes | Yes |
| Row-level security | — | Yes | Yes |
| Search index | — | — | Yes |
| Data masking | — | — | Yes |
| Storage encryption CMEK | — | — | Yes |
| Storage and compute isolation | — | — | Yes |
| Fine-grained permissions | — | — | Yes |
| Reservation flexibility | Basic | Flexible | Flexible |
| Free usage tier | Yes | Yes | Yes |
| Concurrency | 100 queries/project | 100 | 100+ |

**The edition is a security and governance choice, not a performance one.** An organisation with row-level security requirements for PII is in Enterprise territory whether or not its queries are fast.

### Reservations, slots and capacity pricing

This is where the economics change, and where most teams get it wrong first.

**Two pricing models:**

**On-demand.** You pay per byte scanned: **$6.25 per TB** (the course's `BIGQUERY_ONDEMAND_PER_TB`), with the first **1 TB per month free** (`FREE_TIER["bigquery_query_tb"]`). No commitment, no capacity planning. Ideal for spiky, unpredictable, exploratory workloads, and for teams starting out.

**Flat rate (capacity pricing).** You reserve capacity in **slot-hours** and pay a committed-use discount. The course's `BIGQUERY_SLOT_HOUR = 0.06` is the on-demand slot-hour rate used for modelling. Reserving capacity is a commitment: you pay whether or not you use it.

**The decision rule, stated plainly:**

```text
On-demand is right when:
  - usage is unpredictable or bursty
  - you are exploring, or the workload is new
  - a single query can dominate your bill (on-demand caps this)

Flat rate is right when:
  - usage is steady and predictable
  - a large share of your queries touch the same tables (BI workloads)
  - you need predictable budgets
  - you need to commit to a spend before the query runs
```

**The reservations model.** Capacity is organised into **projects → reservations → assignments**. A reservation holds capacity; an assignment attaches projects to it. This enables:

- **Cost attribution.** Put each team's project on its own assignment; the bill shows exactly what each team consumed.
- **Isolation.** A noisy project cannot starve a quiet one.
- **Commitment flexibility.** Enterprise editions let you move committed capacity around as demand shifts; Standard is more rigid.
- **Autoscillating reservations.** You set a minimum and maximum slot count, and BigQuery scales within that range. This is the closest BigQuery gets to "provisioned but elastic".

**The free tier.** Every project gets **1 TB of on-demand query processing per month, free**, and **10 GB of storage per month, free**. The `FREE_TIER` dict in the course's `cost_model.py` encodes exactly this. Note that the free tier applies to *on-demand* processing — it does not reduce a flat-rate commitment, and it does not apply to bytes scanned by scheduled queries (which are billed as their own workload).

**The rule of thumb for a team starting out:** stay on on-demand until you have 60 days of `INFORMATION_SCHEMA.JOBS` history showing a steady baseline, then model the flat-rate alternative against that baseline. Do not reserve capacity you cannot point at a stable query.

### The BQ CLI

The `bq` command-line tool is the fastest way to run BigQuery work, and it is scriptable, which makes it the right tool for CI, migrations and shell pipelines.

```bash
# Who am I, and which project am I working in?
bq info

# List datasets in the project.
bq ls --project_id YOUR_PROJECT_ID

# List tables in a dataset.
bq ls --project_id YOUR_PROJECT_ID --dataset_id curated_us-central1

# Run a query. --use_legacy_sql=false is the default in gcloud shell;
# set it explicitly in scripts so you never inherit legacy behaviour.
bq query --use_legacy_sql=false \
  --destination_format=json \
  'SELECT region, COUNT(*) AS event_count, SUM(amount_eur) AS revenue_eur
   FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
   WHERE event_dt BETWEEN "2026-01-01" AND "2026-01-15"
   GROUP BY region
   ORDER BY region'

# Run a query without executing it: dry run, shows bytes billed.
bq query --use_legacy_sql=false --dry_run \
  'SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`'

# Create a partitioned and clustered table.
bq mk --table \
  --time_partitioning_field=event_dt \
  --clustering_fields=region_key,event_type \
  --description="Grain: one row per accepted event" \
  YOUR_PROJECT_ID:curated_us-central1.fact_events

# Load from a local CSV.
bq load --source_format=CSV \
  --skip_leading_rows=1 \
  --replace \
  YOUR_PROJECT_ID:curated_us-central1.fact_events \
  local_events.csv

# Export a table to Cloud Storage.
bq extract \
  YOUR_PROJECT_ID:curated_us-central1.fact_events \
  gs://YOUR_BUCKET/exports/fact_events-*.csv

# Query the job history: the basis of every optimisation decision.
bq ls --jobs --max_results=50 --format=json
```

**The two flags that matter most in scripts:** `--dry_run` (never pay for a query you have not inspected) and `--format=json` (machine-readable output). A shell script that parses human-readable CLI output is a script that breaks on the next release.

### The Python client

`google-cloud-bigquery` is the Python client, and the `bigquery` magic in a notebook is the fastest way to explore.

```python
from google.cloud import bigquery

client = bigquery.Client()

# The dry run: costs nothing, tells you everything you need.
job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
query = """
    SELECT region, COUNT(*) AS event_count, SUM(amount_eur) AS revenue_eur
    FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
    WHERE event_dt BETWEEN '2026-01-01' AND '2026-01-15'
    GROUP BY region
    ORDER BY region
"""
job = client.query(query, job_config=job_config)
print("bytes processed:", job.total_bytes_processed)
print("bytes billed:", job.total_bytes_billed)
print("estimated cost:", job.estimated_bytes_processed / 1e12 * 6.25)

# The real run.
rows = client.query(query).result()
for row in rows:
    print(row.region, row.event_count, row.revenue_eur)
```

**`total_bytes_billed` is not the same as `total_bytes_processed`**, and the difference is worth $6.25/TB. The billed figure accounts for the minimum 10 MB per table referenced in a query (the "minimum bytes billed" rule). The processed figure is the raw I/O. When they diverge significantly, a small table is being scanned for a tiny query and the 10 MB minimum is dominating.

### Scheduled queries

Scheduled queries run a SQL statement on a schedule, with **targeted destination tables**, email notification on failure, and retries.

```bash
bq mk --schedule \
  --schedule_interval=24h \
  --schedule_start_time=2026-01-15T02:00:00Z \
  --target_table=YOUR_PROJECT_ID:curated_us-central1.fact_daily_region \
  --target_write_disposition=WRITE_TRUNCATE \
  --timeout=3600s \
  --labels=owner=analytics,pipeline=daily_rollup \
  --use_legacy_sql=false \
  --description="Daily regional rollup at grain one row per region per day" \
  'SELECT event_dt, region_key, COUNT(*) AS event_count, SUM(amount_eur) AS revenue_eur
   FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
   WHERE event_dt = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
   GROUP BY event_dt, region_key'
```

**Three things to get right:**

1. **`target_write_disposition=WRITE_TRUNCATE` vs `WRITE_APPEND`.** For a daily rollup that is fully recomputed, `WRITE_TRUNCATE` is correct — it makes the job idempotent. `WRITE_APPEND` on a recomputed daily rollup silently double-counts on every retry. This is a classic and very expensive bug.
2. **The destination table should be partitioned.** A scheduled query writing to a partitioned table with a partition decorator writes only that partition.
3. **Scheduled query bytes are billed separately** from your interactive on-demand usage, and the free tier does not apply to them in the same way. A dashboard that runs 24 scheduled queries a day is a commitment; it should be modelled like one.

### Materialised views

A materialised view stores the *result* of a query, refreshed on demand (or on a schedule via a scheduled query). The idea is that a query whose result is expensive to compute and read often should be computed once.

**When it pays:**

- The query is run repeatedly with slightly different filters, and the expensive part is a fixed join or aggregation.
- The underlying data changes in a way that lets you refresh selectively — for example, a partition-level refresh where only the last day changes.
- You need predictable latency for a latency-critical dashboard, independent of the concurrency of the underlying table.

**When it does not pay:**

- The underlying table changes constantly, so the refresh cost equals the read cost.
- The query is not actually expensive.
- You are storing a large result that is read once.

**The trap:** a materialised view whose refresh costs as much as the original query is pure overhead plus storage. Measure the refresh cost against the total cost of the queries it replaces, not against a single query.

### When BigQuery is the wrong answer

This is the section that separates a platform engineer from a service-ticket-filer. BigQuery is excellent for analytics on structured and semi-structured data. It is the wrong tool for a specific and identifiable set of workloads.

| Workload | Why BigQuery is wrong | Use instead |
|---|---|---|
| Point lookups at high QPS | Every lookup is a scan of at least 10 MB; no point-read API | Memorystore, Firestore, Cloud SQL |
| Sub-10 ms latency SLO | Query startup + planning overhead is tens of ms at best | Cloud SQL, Spanner, Memorystore |
| High-frequency small writes | Storage is immutable; writes rewrite column chunks | Firestore, Cloud SQL, Bigtable |
| Transactional invariants with FKs | No enforced foreign keys, no multi-row transactional guarantees | Cloud SQL, Spanner |
| Streaming ingestion of raw blobs | Columnar OLTP write path is a poor fit | Pub/Sub → Dataflow → GCS |
| Semi-structured exploration at scale | You are paying per byte to parse JSON that you will re-parse | BigLake on Parquet, or parse once into a table |
| Very large single CSV/JSONL export | Per-byte billing on data you already own | External tables, BigLake, Dataflow |
| Heavy ML training on raw features | BigQuery is a query engine, not a training platform | Vertex AI, Dataproc, Dataflow |
| Data in a non-GCP cloud | Egress cost at $0.12/GB | Keep the warehouse in the same cloud |

**The specific BigQuery anti-patterns to watch for:**

1. **Using BigQuery as a key-value store.** Every query bills a minimum of 10 MB. If your application does a lookup per request, you are paying $6.25 per TB to read a 200-byte row. Put a cache in front.
2. **Using BigQuery as an ingestion buffer for sub-minute data.** Storage immutability means high-frequency inserts are expensive. Use Pub/Sub, and batch into BigQuery.
3. **JSON as a permanent schema.** Parsing JSON is cheap *once*; paying per byte to re-parse it every day is not. Parse into typed columns in a transformation step, or use BigLake with a schema on the file.
4. **On-demand for a steady workload.** The arithmetic is not subtle: 1 TB/day on-demand is $6.25 × 30 = $187.50/month; the same usage on flat rate at 1 slot-hour/day equivalent is a fraction of that.
5. **External tables over many small files.** The per-file request overhead dominates. Compact them first, or use a table.

**The counter-question to ask before choosing BigQuery:** *what is the query, what does it read, and how often?* If you can answer those three, you can answer whether BigQuery is right. If you cannot, you do not yet have the requirement, and no platform can be chosen.

---

## 🛠️ Hands-On

### 1. Explore the platform model as code

The service catalogue in the course project already models the platform. This hands-on uses it to reason about BigQuery's placement in the GCP estate, and to make the platform-decision part of the course executable.

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import (
    SERVICES,
    REGIONS,
    CATEGORIES,
    DATA_ENG_ROLE,
    get_service,
    regions_for,
    services_by_category,
    services_available_in,
    services_with_deep_dive,
    summary_table,
    format_service_table,
)

bq = get_service("bigquery")
print("id:", bq.id)
print("name:", bq.name)
print("category:", bq.category)
print("regions:", regions_for("bigquery"))
print("summary:", bq.summary)

# What else in the catalogue is an analytics service?
analytics = services_by_category("Analytics")
for svc in analytics:
    print(f"  {svc.id}: {svc.name}")

# Which catalogue services have deep-dive lectures in this course?
deep = services_with_deep_dive()
print("services with a deep dive:", len(deep))
print("bigquery has a deep dive:", "bigquery" in deep)

print(summary_table())
```

### 2. Model the storage/compute separation explicitly

BigQuery's architecture is the reason cost is per byte, not per node. This models the two halves and what each costs.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, BIGQUERY_ONDEMAND_PER_TB, FREE_TIER

print("on-demand price per TB:", BIGQUERY_ONDEMAND_PER_TB)
print("free tier TB per month:", FREE_TIER["bigquery_query_tb"])

# The storage half: cheap, and charged per GB-month.
storage_only = estimate("bigquery", storage_gb=1000, apply_free_tier=False)
print("\n--- storage ---")
print(storage_only)

# The compute half: charged per byte scanned.
scan_only = estimate(
    "bigquery", scanned_tb=1.0, monthly=False, apply_free_tier=False
)
print("\n--- scan ---")
print(scan_only)

# A month's worth of the storage half against one day's worth of scanning.
# Storage for 1 TB is $20.40/month; scanning 1 TB is $6.25 *per query*.
print("\n1 TB stored for a month: $%.2f" % storage_only.total)
print("1 TB scanned once:      $%.2f" % scan_only.total)
print("1 TB scanned 30 times:  $%.2f" % (scan_only.total * 30))
```

The arithmetic is the whole argument for the storage/compute split: **storage is cheap and scan is not.** A table scanned daily costs ~12× more in scan fees over a month than it costs to store. This is why the course's optimisation chapter is really a bytes-read chapter, and why "the data is only 1 TB" is not a defence of an unpartitioned dashboard.

### 3. The three pricing models, side by side

The on-demand / flat-rate / reservation decision, priced for three different workload shapes.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, BIGQUERY_SLOT_HOUR, HOURS_PER_MONTH

# Shape A: bursty. One heavy query a week, 5 TB each.
bursty_tb = 5 * 4
bursty = estimate("bigquery", scanned_tb=bursty_tb, monthly=False, apply_free_tier=False)
print(f"A bursty: {bursty_tb} TB scanned = ${bursty.total:.2f}/month")

# Shape B: steady. A dashboard scanned every hour, 0.05 TB each.
steady_tb = 0.05 * 24 * 30
steady = estimate("bigquery", scanned_tb=steady_tb, monthly=False, apply_free_tier=False)
print(f"B steady on-demand: {steady_tb:.1f} TB = ${steady.total:.2f}/month")

# Shape C: steady on reserved capacity. 1 slot always on.
reserved = estimate(
    "bigquery",
    slot_hours=1 * HOURS_PER_MONTH,
    monthly=True,
    apply_free_tier=False,
)
print(f"C flat rate: 1 slot 24/7 = {1 * HOURS_PER_MONTH} slot-hours = ${reserved.total:.2f}/month")

# Shape D: steady on reserved capacity, sized to the work.
# 50 slot-hours a day for a dashboard workload.
sized = estimate(
    "bigquery",
    slot_hours=50 * 30,
    monthly=True,
    apply_free_tier=False,
)
print(f"D flat rate: 50 slot-hours/day = ${sized.total:.2f}/month")
```

The conclusion the numbers support: on-demand wins for shape A (bursty), on-demand loses badly for shape B (steady, where the same bytes are paid for over and over), and flat rate wins for shape C only if the workload genuinely occupies a slot continuously. **Shape D is the honest answer for most teams**: reserve roughly what your steady baseline consumes, and keep on-demand for the burst on top. That hybrid is exactly what the reservations model is for.

### 4. Explore the project's simulated platform and run the pipeline

The course's `platform_sim.py` builds a demo project with a resource tree, and runs the pipeline through simulated BigQuery tables.

```python
import sys
sys.path.insert(0, "project/core")

from platform_sim import build_demo_project, format_resource_tree, format_pipeline_log

project = build_demo_project()
print(format_resource_tree(project))

# The pipeline: raw -> validated -> aggregated -> published -> loaded.
result = project.run_pipeline([
    "event_id,user_id,event_dt,event_ts,region,channel,event_type,amount,currency"
])
print(format_pipeline_log(result))
```

The resource tree is worth reading as a design. It shows a project with a `curated_us-central1` dataset, a `events-us-central1` topic, a `raw-events-us-central1` bucket, and a service account — which is the minimum viable GCP project for the course pipeline, and a good template for the exercise in the next section.

### 5. Estimate the monthly cost of the course's BigQuery footprint

A realistic configuration for the course pipeline, priced end to end.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, monthly_runway

# Storage: raw (90 days), staging (7 days), curated (2 years).
# Assume 4,800 events/day at roughly 300 bytes each.
bytes_per_event = 300
events_per_day = 4800
daily_mb = bytes_per_event * events_per_day / 1024 / 1024

raw_gb = daily_mb * 90 / 1024
staging_gb = daily_mb * 7 / 1024
curated_gb = daily_mb * 365 * 2 / 1024

print(f"daily volume: {daily_mb:.2f} MB")
print(f"raw (90d):  {raw_gb:.2f} GB")
print(f"staging (7d): {staging_gb:.3f} GB")
print(f"curated (2y): {curated_gb:.2f} GB")

total_storage_gb = raw_gb + staging_gb + curated_gb
storage = estimate("bigquery", storage_gb=total_storage_gb, apply_free_tier=False)
print(storage)

# Queries: a dashboard reading one day per day, plus a weekly full scan.
dashboard_tb = 0.02 * 30
weekly_tb = 1.0 * 4
queries = estimate(
    "bigquery",
    scanned_tb=dashboard_tb + weekly_tb,
    monthly=False,
    apply_free_tier=False,
)
print(queries)
print(f"monthly total: ${storage.total + queries.total:.2f}")
```

Two observations that will matter later. First, the weekly "full scan" line dominates the query cost, and it is the one most likely to be an unpartitioned scan — which is precisely what chapter 3.3 fixes. Second, storage is rounding error next to queries; **the whole optimisation conversation is about bytes read**.

---

## 🛠️ Common Errors and Fixes

### 1. `bq query` with legacy SQL, or the wrong quoting

```text
ERROR: Syntax error: Unexpected keyword [FROM] at [1:8]
```

BigQuery's legacy SQL dialect used a different grammar, and the shell's own quoting fights you. The fix is standard SQL and single quotes:

```bash
bq query --use_legacy_sql=false \
  'SELECT region, COUNT(*) AS n FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events` GROUP BY region'
```

Note the **backticks** around the fully-qualified table name — `project.dataset.table` — and that the whole query is in single quotes so the shell does not interpret the backticks as command substitution. If you use double quotes for the query, the shell will try to run `YOUR_PROJECT_ID:...` as a command.

### 2. `Not found: Table` — the dataset or the region is wrong

```text
Not found: Table YOUR_PROJECT_ID:curated.events
```

The dataset does not exist under that name. Three causes, in order of likelihood:

1. **The dataset name is wrong.** Note the course convention: `curated_us-central1` has an underscore before the region. `curated` alone will not resolve.
2. **The dataset lives in a different region.** A dataset is regional, and a table reference must resolve in the dataset's own location. Check with `bq ls --dataset_id`.
3. **The project is wrong.** You are authenticated as a user whose active project is not the one you think.

The fix — always confirm before you query:

```bash
bq ls --project_id YOUR_PROJECT_ID --datasets
bq ls --project_id YOUR_PROJECT_ID --dataset_id curated_us-central1 --tables
bq info | head -20
```

### 3. `403 Forbidden` — permission, not syntax

```text
ERROR: Access Denied: Table your-project:curated_us-central1.fact_events: User does not have permission to use the table.
```

You have the query but not the table, or you have neither. Note the specific message: "User does not have permission to use the table" — this is a *table-level* IAM denial, not a project-level one.

The fix, in increasing scope:

```bash
# Least privilege first: one table.
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:analyst@example.com" \
  --role="roles/bigquery.dataViewer" \
  --condition='expression=resource.name.startsWith("projects/YOUR_PROJECT_ID/datasets/curated_us-central1/tables/fact_events")'

# Dataset level, for the analysts who need the whole mart.
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="group:analytics@example.com" \
  --role="roles/bigquery.dataViewer"

# Job creation needs this too.
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="group:analytics@example.com" \
  --role="roles/bigquery.jobUser"
```

### 4. The scheduled query that double-counts

```text
ERROR: Already Exists: Table your-project:curated_us-central1.fact_daily_region
```

Or worse — no error, and the numbers are doubled:

```text
-- fact_daily_region has 2 rows per region per day instead of 1.
-- The job was retried after a transient failure and appended again.
```

The cause is `WRITE_APPEND` on a query that fully recomputes the partition. The fix is `WRITE_TRUNCATE`, which makes the job idempotent:

```bash
bq mk --schedule \
  --schedule_interval=24h \
  --target_table=YOUR_PROJECT_ID:curated_us-central1.fact_daily_region \
  --target_write_disposition=WRITE_TRUNCATE \
  --use_legacy_sql=false \
  'SELECT event_dt, region_key, COUNT(*) AS event_count, SUM(amount_eur) AS revenue_eur
   FROM `YOUR_PROJECT_ID.curated_us-central1.fact_events`
   WHERE event_dt = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
   GROUP BY event_dt, region_key'
```

If you genuinely need append semantics (a genuine log of runs), write to a table whose grain is one row per run, not one row per region per day.

### 5. `exceeded rate limits` — the concurrency wall

```text
ERROR: 400 Bad Request: Job exceeded rate limits: resources: too many concurrent queries
```

You have hit the per-project concurrency limit (100 concurrent queries by default). The common cause is a dashboard firing 40 queries at once, each of which fans out into multiple sub-queries.

The fix is to reduce the number of jobs, not to retry harder:

- **Replace the dashboard's many small queries with one query.** Join inside the query rather than in the client.
- **Materialise the recurring aggregate.** A dashboard reading `fact_daily_region` instead of recomputing from `fact_events` turns 40 scans into 40 tiny reads of a small table.
- **Use the query result cache** for identical repeated queries — this is on by default and is defeated by passing `--use_query_cache=false` (which the dry run does deliberately).
- **Raise the limit** in a quota request, which is legitimate for a scheduled workload but is not a substitute for fixing the fan-out.

### 6. The query that bills 10 MB for a 40-row result

```text
-- The confusing case:
-- Table has 40 rows. The query returned in 200 ms.
-- The billing export shows 10.5 MB of processed bytes.
```

This is the **minimum bytes billed** rule: BigQuery bills at least 10 MB per table referenced in a query, even if the table is tiny. It is not a bug and it is not a scan — but it becomes a real problem at scale, when a dashboard with 30 small tables is billed 300 MB per refresh regardless of data size.

The fix is to consolidate small tables into fewer, larger ones — the denormalisation argument from chapter 3.3 — and to check `total_bytes_billed` versus `total_bytes_processed` in the job metadata to see when the minimum is dominating.

---

## 💡 Production Notes

- **Dry-run every query before it becomes a bill.** `bq query --dry_run` or `QueryJobConfig(dry_run=True)` costs nothing and prints the bytes that would be billed. Put it in CI for every SQL file, and make the build fail if bytes processed exceed a threshold.
- **Cost is bytes read, so optimise bytes read.** Before optimising anything else, ask what the query reads. A query that reads 10× fewer bytes is 10× cheaper — before any query-plan tuning.
- **Set the table description to the grain, every time.** `bq mk --description="Grain: one row per accepted event"`. It is free, and it is the first thing anyone reads.
- **Watch `INFORMATION_SCHEMA.JOBS` weekly.** `total_bytes_billed`, `total_slot_ms` and `creation_time` per job, grouped by `job_id` prefix or by user. The top five queries by bytes are usually 80% of the bill and usually have an obvious fix.
- **Pin your dashboards to a materialised or aggregate table.** A BI tool that re-aggregates the fact table on every page load will cost more than the ingestion pipeline it is supposed to be cheaper than.
- **Use `WRITE_TRUNCATE` for recomputed scheduled-query destinations, and test idempotency.** Run the job twice; the result must be identical. A retry after a transient failure is not an edge case, it is Tuesday.
- **Keep the free tier in mind but do not design around it.** 1 TB of on-demand query processing per month is a small budget for a team, and designing to the free tier produces a workload that breaks the moment it is useful. Use it for exploration; price production workloads properly.
- **Version your SQL.** Put DDL and queries in a Git repository, apply them with a migration tool or `bq query` in CI, and never hand-edit a table in the console for anything you intend to keep. Schema drift between the repository and the warehouse is the single most expensive kind of warehouse debt.
- **Plan for the regional dataset.** Datasets are regional. If your users are in Europe, a `US`-multi-region dataset adds egress and latency for no benefit. Choose the dataset location at creation time — it cannot be moved.

---

## 🔑 Key Takeaways

- **BigQuery = storage + compute, fully separated.** Colossus holds immutable columnar blocks; Dremel executes distributed SQL over stateless workers. No cluster to size, no storage to plan.
- **Because of that separation, the unit of cost is the byte read.** Every optimisation in this course is really about bytes.
- **The hierarchy is project → dataset → table**, and the project is the billing and IAM boundary. Datasets are **regional** and cannot be moved.
- **BigQuery has no indexes, by design.** Performance comes from partition pruning, clustering (physical reordering), and reducing shuffle volume — not from index maintenance.
- **Partitioning skips whole partitions; clustering skips row groups within a partition.** They compose and they solve different problems.
- **A slot is a vCPU; compute is measured in slot-milliseconds.** The same bytes can cost very different slot-ms depending on parallelism and shuffle.
- **The join is where the money is.** Shuffle volume, not scan volume, dominates the cost of a multi-table query.
- **Editions are a security and governance choice**, not a performance one. Enterprise for row-level security; Enterprise Plus for search indexes, masking and storage isolation.
- **On-demand for unpredictable and exploratory work; flat rate for steady, committed workloads.** Reservations give you cost attribution, isolation and commitment flexibility. Most teams end up hybrid.
- **The BQ CLI is scriptable and the Python client is embeddable.** Use `--dry_run` and `--format=json`; use `QueryJobConfig(dry_run=True)` before every query that costs money.
- **BigQuery is wrong for point lookups, sub-10 ms SLAs, high-frequency small writes, transactional invariants, and permanent JSON schemas.** The test is: *what is the query, what does it read, and how often?*

---

## 📚 Practice Exercises

1. **Write the BigQuery CLI script for the course pipeline.** A single bash script that: creates the `curated_us-central1` dataset with a description and a default table expiry; creates `fact_events` partitioned by `event_dt` and clustered by `region_key, event_type`; loads `sample_data/events.csv`; runs the dry run and prints the bytes billed; runs the real query producing the summary; and exports the result to a Cloud Storage bucket. Make it idempotent — running it twice must produce the same state.
2. **Model the on-demand versus flat-rate decision from real history.** Write `choose_pricing_model(jobs: list[dict]) -> dict` that takes a list of job records with `total_bytes_billed` and `total_slot_ms`, computes the on-demand cost, estimates the slot-hours required to run the same workload flat rate, and returns a recommendation with the break-even point. Apply it to three synthetic workloads: a nightly ETL, a BI dashboard with 200 daily queries, and an ad-hoc analyst team.
3. **Price the three editions for a regulated workload.** Using `estimate()`, build a comparison for a team that needs row-level security and column-level masking on 50 TB of curated data with a 40-slot-hours/day steady baseline. Show the on-demand cost, the flat-rate cost, and the storage cost, then explain which edition the security requirements force and why the edition choice does not affect the query cost.
4. **Enumerate the catalogue analytics services and decide.** Using `service_catalog.services_by_category()` and `get_service()`, list every service in the catalogue's analytics category, and for each write one sentence on why it would or would not be the right choice for the course's pipeline. Then use `region_status_matrix()` to check which of them are available in each of the 12 catalogue regions, and note what that implies for a multi-region analytics plan.
5. **Design the migration from raw files to BigQuery tables.** Write the full `EXPORT DATA` / `bq load` path from Cloud SQL to a partitioned BigQuery table, including the incremental-load logic (partition decorator, watermark column) and the reconciliation query that proves the row counts and the per-region revenue match `pipeline_logic.EXPECTED_SUMMARY`. Then write the same flow with a `MERGE` for the idempotency check.
6. **Write the reservation topology.** Design projects, reservations and assignments for an organisation with four teams (a large BI team, a small analytics team, an ETL service account, and a sandbox). Show which assignments each project belongs to, what committed-use discount you would target, and how you would use `INFORMATION_SCHEMA` to attribute spend per team. Use `cost_model.estimate()` to show the effect of moving a noisy project onto its own reservation.
7. **Write the "when NOT to use BigQuery" decision record.** Take five workloads from the exercises in chapter 3.1, and for each write the one-line disqualifier — the specific property that makes BigQuery wrong — and the service you would use instead, with its API from `service_catalog.get_service()`. Then show the code that checks the disqualifier.

---

## 📖 Further Reading

- [BigQuery overview](https://cloud.google.com/bigquery/docs/introduction) — the service in one page, and the compute/storage split
- [BigQuery architecture](https://cloud.google.com/bigquery/docs/introduction#architecture) — Dremel and Colossus in detail
- [BigQuery storage overview](https://cloud.google.com/bigquery/docs/storage-overview) — columnar layout, row groups, physical reordering
- [BigQuery pricing](https://cloud.google.com/bigquery/pricing) — on-demand, editions, reservations, free tier
- [BigQuery reservations](https://cloud.google.com/bigquery/docs/reservations-intro) — capacity model, assignments, autoscillating reservations
- [BigQuery editions](https://cloud.google.com/bigquery/docs/editions-intro) — what each edition adds
- [BigQuery best practices for cost](https://cloud.google.com/bigquery/docs/best-practices-cost-optimization) — Google's own cost guidance
- [bq command-line tool reference](https://cloud.google.com/bigquery/docs/bq-command-line-tool) — every flag
- [BigQuery INFORMATION_SCHEMA](https://cloud.google.com/bigquery/docs/information-schema) — the job and reservation metadata views
