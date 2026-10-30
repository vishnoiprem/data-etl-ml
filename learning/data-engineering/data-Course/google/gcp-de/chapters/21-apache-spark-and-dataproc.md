# 5.2 — Apache Spark and Google Cloud Dataproc

> **Section 5 · Processing & Orchestration · Lecture 5.2 · 8:00**

## 🎯 What you will learn

- The Spark programming model: RDDs, why DataFrames displaced them, Catalyst, and Tungsten
- Spark SQL, the lazy DAG, transformations versus actions, and the cost model of a shuffle
- Shuffle partition sizing and skew: how to diagnose and fix both
- Dataproc cluster types: Standard, Ephemeral, and the Serverless batch path
- The job submission flow through Dataproc Serverless and Cluster
- PySpark, notebooks, and workflow templates
- The Spot / preemptible strategy for batch work, and autoscaling
- Cluster operation, quotas, and the real cost model
- The honest verdict: Dataproc versus Dataflow

---

## 🧠 Concept

### What Spark actually changed

Spark was not faster than MapReduce because of better parallelisation. MapReduce already parallelised well. Spark was faster because it changed **where data lives between stages**.

MapReduce's intermediate results always go through HDFS: mappers write to local disk, the framework transfers them over the network, reducers write their own output to HDFS, and the next job reads it back from HDFS. Every stage boundary is a trip to a distributed filesystem.

Spark keeps intermediate results **in memory** in the executor processes. A chain of transformations becomes a single job. That single change eliminated the I/O that dominated MapReduce.

Three ideas followed from it:

1. **In-memory iteration.** A loop over a dataset no longer reloads from disk.
2. **A rich API.** `map`, `filter`, `reduceByKey`, `groupByKey`, `join`, `sort` — composable, and over DataFrames, SQL-like.
3. **A unified engine.** The same engine runs batch SQL, streaming (Structured Streaming), machine learning (MLlib), and graph processing (GraphX).

### RDDs and why DataFrames replaced them

The **Resilient Distributed Dataset** was the original abstraction: an immutable, partitioned, distributed collection with fault-tolerant lineage. Every transformation creates a new RDD and records a lineage edge. If a partition is lost, Spark replays the lineage to rebuild it.

RDDs exposed the underlying storage model directly. Users had to think about partitioning, serialization, and memory to write correct RDD code. In practice this produced code that was fast in the hands of Spark's authors and slow in everyone else's.

The **DataFrame** replaced the RDD as the primary abstraction. A DataFrame is a distributed table with a **schema** — column names, types, and nullability. That single change unlocked three things:

- **Catalyst**, the query optimizer. It can push predicates down, prune columns, reorder joins, and choose join strategies because it knows the schema.
- **Tungsten**, the execution and memory model. It uses off-heap memory, columnar in-memory storage, and whole-stage code generation.
- **Spark SQL**, and therefore the DataFrame API, the SQL API, and structured streaming all share one optimizer and one code generator.

The lesson is worth stating plainly: **a schema is what makes optimization possible.** Spark became an industry engine the moment its DataFrames were no longer just "RDDs of tuples."

### The Catalyst optimizer

Catalyst is a rule-based optimizer that rewrites a logical plan. Its rules matter operationally because they determine what actually runs:

- **Predicate pushdown** moves filters closer to the source so less data is read. On BigQuery Storage Read or on Parquet with partition pruning, this is the difference between reading 1 percent and 100 percent of a table.
- **Column pruning** reads only referenced columns. Parquet and ORC are columnar, so this is nearly free at scan time.
- **Constant folding** evaluates deterministic expressions at planning time.
- **Join reordering** reorders joins where the cost model predicts a better plan, notably converting star-schema joins to broadcast joins.
- **Aggregate pushdown** pushes partial aggregation below a join when it is safe.

Catalyst also generates code: **whole-stage codegen** compiles the physical plan into a single generated method, eliminating the overhead of boxing and virtual dispatch. This is why Spark 2 and 3 are significantly faster than Spark 1 on the same hardware, independent of cluster size.

### Tungsten: the memory model

Tungsten changed how Spark stores and moves data:

- **Off-heap memory management.** The JVM's managed heap causes GC pauses proportional to live data. Tungsten manages memory outside the JVM heap, so a 32 GB executor does not need a 32 GB Java heap and does not spend its life in garbage collection.
- **Columnar in-memory storage.** Columns of the same type are stored contiguously, which is cache-friendly and compressible.
- **Whole-stage code generation** as described above.

**Tungsten's practical rule:** keep the data in memory but do not try to keep everything in memory. Spark's unified memory manager divides an executor's memory between execution space, storage space, and user memory, with the boundary elastic. A dataset too large for memory spills to disk — which is fine; what is not fine is a dataset so large that it spills repeatedly, because that reintroduces the MapReduce I/O pattern Spark was built to avoid.

### Lazy evaluation and the DAG

Spark does not execute transformations when you call them. A transformation returns a new DataFrame and records an operation in a **logical plan**. The DAG is materialised when an **action** is called:

- Actions that write: `write`, `saveAsTable`, `toPandas`
- Actions that return data to the driver: `collect`, `count`, `show`, `take`, `first`
- Actions that measure: `describe`, `summary`

This is not an implementation detail. It is the mechanism behind Spark's **catalyst for whole-stage optimisation**: the optimizer sees the whole query, not one operation at a time, so it can push filters across the entire pipeline.

The cost: **every action triggers a full re-execution** of the plan (or a recomputation of the affected partitions if the result is cached). Forgetting to cache a DataFrame that is used three times means computing it three times. This is the single most common Spark performance mistake.

The rule: **persist only what is reused, and persist deliberately.**

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("events").getOrCreate()

# A lineage that is cheap to recompute should not be cached.
enriched = (
    spark.read.csv("gs://bucket/events.csv", header=True)
    .withColumn("amount_eur", col("amount") * col("rate"))
)

# A lineage that is expensive (a scan plus a shuffle) and used more than
# once should be cached. The StorageLevel MEMORY_AND_DISK is safer than
# MEMORY_ONLY, because an un-cacheable partition would otherwise fail.
expensive = (
    spark.read.parquet("gs://bucket/events/")
    .groupBy("region")
    .agg(sum("amount_eur").alias("revenue"))
)
expensive.cache()
expensive.count()   # materialise it once; this action populates the cache
```

### Transformations versus actions, and the shuffle

Transformations are lazy and cheap to describe; actions are expensive and cause execution. Every shuffle — a repartition, `groupByKey`, `reduceByKey`, `join` (except a broadcast join), `distinct`, `sortBy` — is a boundary where data is:

1. Serialised
2. Partitioned by key
3. Written to local disk
4. Transferred across the network
5. Read and merged by the target side

The shuffle is where Spark's time and money go. Two principles follow.

**Prefer hash-aggregating over sort-aggregating.** `reduceByKey` performs a **partial aggregation in the mapper** before the shuffle, so the network carries pre-aggregated values. `groupByKey` carries every value. The difference is often an order of magnitude in shuffled bytes for the same result. The rule of thumb: `groupByKey` is a bug; use `reduceByKey`, `aggregateByKey`, or a DataFrame `groupBy().agg()`.

**Prefer a broadcast join when one side is small.** A broadcast join replicates the small side to every executor and avoids the shuffle entirely. Spark's `autoBroadcastJoinThreshold` (10 MB by default) decides this automatically. A join where one side is 50 MB is a classic shuffle-join that could have been a broadcast.

### Shuffle partitions and skew

**Shuffle partition count.** Spark splits the shuffle into `spark.sql.shuffle.partitions` partitions (default 200). Too few partitions means each task handles too much data and the cluster idles at the tail of the stage. Too many means each partition is tiny and per-task overhead dominates.

The sizing heuristic:

```text
target partition size ≈ 128 MB  (the rule of thumb for shuffle data)
shuffle partitions = max(total shuffle bytes / 128 MB, number of cores)
```

Tune it with an **AQE** (Adaptive Query Execution) setting rather than by hand when possible:

```python
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```

AQE coalesces small shuffle partitions at runtime into larger ones, which solves the "200 partitions of 2 MB each" problem automatically. AQE skew join handling splits skewed partitions into sub-partitions and replicates the small side, which fixes skew joins without code changes. Note that `spark.sql.shuffle.partitions` remains the *initial* count; AQE may reduce it afterwards.

**Skew.** Skew is when one key holds a disproportionate share of the data. Symptoms:

- One task in a stage runs for hours while its siblings finish in minutes
- `Task` duration distribution in the Spark UI is a long tail
- Executor CPU usage is near zero while the stage is "running", because all executors are waiting on the one slow task

Causes and fixes:

| Cause | Fix |
|---|---|
| Hot key (a large customer, a common join key) | Salting: add a random prefix `0`–`N` to the key, aggregate, then re-aggregate on the unsalted key |
| Small dimension side not broadcast | Raise the broadcast threshold or force the broadcast hint |
| Partitioning by a low-cardinality column badly | Repartition on a higher-cardinality key |
| Null keys | Filter or coalesce nulls into a dedicated partition |

Salting in DataFrame SQL:

```python
from pyspark.sql import functions as F

salted = (
    df.withColumn("salt", (F.rand() * 16).cast("int"))
      .withColumn("composite_key", F.concat(F.col("key"), F.lit("-"), F.col("salt")))
)

partial = salted.groupBy("composite_key").agg(F.sum("value").alias("partial"))
final = partial.groupBy("key").agg(F.sum("partial").alias("total"))
```

The extra aggregation is the price of not letting one task carry the whole group.

### Dataproc: the three cluster shapes

Dataproc is GCP's managed Apache Spark, Hadoop, and Hive. It offers three ways to run a job, and choosing between them is the most important decision on the service.

#### 1. Standard clusters (also called "Cluster" mode)

A long-lived cluster that runs continuously. You create it, submit jobs to it with `spark-submit` or the job API, and delete it when finished.

- **Good for:** interactive development, a burst of closely-related jobs that share a cache, jobs with long setup, teams that want a stable endpoint.
- **Bad for:** a single daily job. A cluster that exists 24 hours to run a 20-minute job wastes 23.7 hours of machine time.
- **Cost:** billed for the entire lifetime of the cluster, whether or not a job is running.

#### 2. Ephemeral clusters

Created by the Dataproc job API, run one job, and are deleted when it finishes. You pay for the cluster's actual lifetime plus a small per-job fee.

- **Good for:** scheduled batch jobs, one-shot pipelines, anything where the cluster has no long-term state.
- **This is the default choice for production batch work on Dataproc.**

#### 3. Serverless batch (and the newer "Dataproc Serverless" sessions)

You submit a job and Google provisions the compute, YARN-equivalent resources, and job history for that submission. There is no cluster to manage.

- **Good for:** scheduled pipelines, CI jobs, short-lived interactive sessions, teams with no Hadoop expertise.
- **Limits:** no persistent HDFS, restricted access to cluster-level services, and some Spark features (notably certain Spark-on-Spark streaming sources and long-lived services) are unavailable.

**The decision:** if you want a cluster to survive between jobs and hold state, use a Standard cluster. If you want to run a job and forget about it, use an ephemeral cluster or the Serverless batch path. The vast majority of production pipelines should be ephemeral or serverless.

### The job submission flow

Serverless batch submission:

```bash
gcloud dataproc jobs submit pyspark \
  --project=my-project \
  --region=us-central1 \
  --job-file=gs://my-bucket/jobs/main.py \
  --labels=team=data-platform \
  -- spark.submit.executor.instances=4 \
  -- spark.submit.executor.memory=4g \
  -- spark.submit.driver.memory=2g
```

The flow is:

1. The service creates a short-lived runtime with a YARN-equivalent resource manager.
2. The driver is launched; it reads the job file from Cloud Storage.
3. Executors are allocated; the driver submits stages.
4. The job writes output to Cloud Storage, BigQuery, or BigLake.
5. The runtime is torn down. Job logs and the Spark UI are retained for a period.

Standard cluster creation and submission:

```bash
gcloud dataproc clusters create events-etl \
  --project=my-project \
  --region=us-central1 \
  --zone=us-central1-a \
  --image-version=2.2-debian12 \
  --master-machine-type=standard-machine-types-4 \
  --worker-machine-type=standard-machine-types-4 \
  --worker-count=3 \
  --initialization-actions=gs://my-bucket/init/setup.sh \
  --metadata=spark-env-version=3 \
  --max-idle-duration=30m \
  --max-lifetime=2h \
  --no-ttl

gcloud dataproc jobs submit pyspark \
  --project=my-project \
  --region=us-central1 \
  --cluster=events-etl \
  --jars=gs://my-bucket/libs/extra-lib.jar \
  -- spark.submit.executor.instances=6 \
  -- spark.submit.executor.memory=8g \
  -- spark.submit.executor.cores=4 \
  -- spark.submit.driver.memory=4g
```

Note the two different `spark.submit.*` arguments. On a Standard cluster, `--master` is implicit (the cluster's YARN endpoint). On a Serverless job you may need to specify `--spark.submit.master=spark://...` or rely on the managed defaults, and the file must live in Cloud Storage — you cannot reference a local path.

### PySpark

PySpark is Spark's Python API. It runs the Python driver on the cluster, but the **Python workers are separate processes**; PySpark uses a `py4j` gateway for the JVM and a pipe for Python worker data.

Practical consequences:

- Python UDFs serialise data to the Python process and back. They are slow. Prefer **native functions** (`F.when`, `F.coalesce`, `F.expr`, `F.from_json`) and only fall back to a Python UDF when there is no SQL equivalent.
- The Python driver and the Python workers both need the same libraries. Ship them in the job file's directory or install them via an initialization action.
- Arrow can cut serialisation cost dramatically when the data is small; enable `spark.sql.execution.arrow.pyspark.enabled=true` and use `toPandas()` / `pandas_udf` carefully — Arrow has a 2 GB limit per record batch and will fail with `ArrowInvalid` on very large payloads.
- The `pyspark` package version must match the cluster's Spark version, within the minor version the runtime supports.

### Notebooks and workflow templates

Dataproc clusters expose the Jupyter notebook component on port 8123, and the interactive session component on port 10021. Both are tunneled:

```bash
gcloud compute ssh my-project/us-central1-a/events-etl-m \
  --ssh-flag="-D 1080 -N" \
  --tunnel-through-iap \
  -- -L 8123:localhost:8123
```

Then open `http://localhost:8123`. For the interactive session:

```bash
gcloud compute start-jupyter-notebook ...   # classic cluster
gcloud dataproc sessions create ...          # serverless interactive session
```

**Workflow templates** are Dataproc's answer to "the same six Spark jobs, in the same order, with the same arguments". A template is a YAML file describing a DAG of operators — `SparkSql`, `SparkJob`, `Pig`, `HiveQuery`, `SparkSubmit` — with dependencies and parameter substitution. It is managed by Workflows API, not by Airflow.

**My opinion:** workflow templates are a legitimate choice when you want zero dependency on an orchestrator, but they are weak on conditional logic, dynamic branching, and backfills. If you already run Airflow, drive Spark jobs from Airflow and keep the template file for reference. If you do not run Airflow and the DAG is static, templates are a reasonable lightweight option.

### Spot / preemptible VMs and autoscaling

Dataproc supports **Spot VMs** for workers. A Spot worker costs roughly a third of an on-demand worker and can be reclaimed by Google at any time, with a 30-second warning.

The upside is large for batch work: if you size the cluster so that most workers are Spot and tolerate interruption, your compute bill falls by two-thirds.

The cost is interruption. When a Spot worker is preempted:

- The YARN container is lost.
- The stage is recomputed. Spark's lineage guarantees this, but recomputation is expensive for shuffle-heavy stages whose upstream data was evicted.
- Long-running stages can fail permanently if the driver decides the task is too slow to retry.

The rules that keep Spot usable:

1. Enable **Spark speculation** so slow tasks are duplicated onto another executor. `spark.speculation=true`, `spark.speculation.quantile=0.9`.
2. Make the job **checkpoint frequently** so a lost stage does not force a full recompute.
3. Set `spark.speculation.multiplier` conservatively — too much speculation on a preemptible cluster multiplies the interruption probability.
4. Do **not** use Spot for the master node. Losing the master loses the whole job.
5. Use `gcloud dataproc clusters create --no-preemptible` for the master, and Spot for workers. On Dataproc Serverless, use the batch/temporary execution mode.

**Autoscaling** in Dataproc Serverless and in managed clusters adjusts worker count against a minimum and maximum. It is genuinely useful for bursty workloads and genuinely dangerous if the minimum is high (idle cost) or the maximum is above quota (job rejection). Autoscale also interacts badly with Spark's static stage partitioning: a stage's tasks are assigned at stage start, so a scale-up mid-stage does not help that stage.

### Cluster operation, quotas, and cost

Operationally, the things that bite:

- **Quota.** A cluster is Compute Engine instances in a region. The relevant quotas are CPUs per region and the per-instance-group limit. A request that exceeds quota is rejected at creation, not at run time.
- **Image version churn.** Dataproc image versions (for example `2.2-debian12`) bundle a specific Spark, Hadoop, Python, and connector set. Pin the image version in infrastructure code; never use `latest` in anything automated.
- **Metadata and initialization actions** are where you install extra packages and set configuration. An initialization action that fails can leave a cluster in a broken state with the action's error only visible in the cluster's action logs.
- **Idle cluster cost.** A Standard cluster that nothing touches bills continuously. `--max-idle-duration` and `--max-ttl` are the safety net, and you should set both.
- **Job history and the Spark UI.** On Dataproc, the Spark UI and job history are retained for a limited period after the cluster is deleted. Capture what you need before you tear the cluster down.

### The cost model

Dataproc bills per vCPU-hour for the cluster (master and workers), with different rates for standard and preemptible, plus management fees. The course model uses $0.0476 per vCPU-hour:

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, compare_architectures, format_comparison

estimate_4_workers = estimate("dataproc", vcpu_hours=40)
print(estimate_4_workers)

options = compare_architectures(scanned_tb=1.0, streaming_hours=24)
print(format_comparison(options))
```

Expected output:

```text
| Architecture | Monthly cost |
|---|---|
| Batch on BigQuery (partitioned) | $0.0625 |
| Spark on Dataproc | $0.5712 |
| Streaming on Dataflow | $1.4280 |
| Batch on BigQuery (unpartitioned) | $6.2500 |
```

The table is sorted cheapest first, so the ordering **changes with the inputs**. With `streaming_hours=0` — the default, and the setting used in Chapter 1.1 — the Dataflow and Dataproc lines are $0.0000 and lead the table. Here, with 24 hours of streaming actually billed, they cost money and the partitioned BigQuery batch becomes the cheapest line.

That reordering is the whole lesson. The comparison is not a fixed ranking of technologies; it is a function of *how long the pipeline is alive* and *how much of the table the query actually reads*. Change either and the winner changes.

The teaching point: Dataproc costs scale with **cluster size × time**, not with data volume. A Spark job that reads 100 GB and a Spark job that reads 100 TB cost the same if they use the same resources for the same duration. That makes Dataproc pricing predictable and BigQuery pricing volume-dependent — the opposite trade-offs.

### The honest verdict: Dataproc vs Dataflow

| Dimension | Dataproc (Spark) | Dataflow (Beam) |
|---|---|---|
| Programming model | Spark SQL, DataFrame, RDD | Beam PCollection/PTransform |
| Execution engine | Spark's own | Managed, autoscales, exactly-once |
| Operations | You manage cluster shape | Fully managed |
| Streaming | Structured Streaming (micro-batch, or continuous) | Native streaming, windows, triggers, watermarks |
| State | Stateful via checkpoints | Managed state, exactly-once |
| Cost shape | Cluster size × time | Work performed, autoscales to zero |
| Skills | Spark is widespread | Beam is a smaller talent pool |
| Best for | Complex batch ETL, custom algorithms, ML pipelines | Streaming, unified batch and stream, managed operations |

**Choose Dataproc when** the work is complex batch ETL, you want the whole Spark ecosystem (MLlib, GraphX, custom UDFs), your team already knows Spark, and the workload is big enough that per-vCPU-hour economics beat a warehouse scan.

**Choose Dataflow when** you need streaming with exactly-once semantics, you want one code path for batch and stream, you do not want to tune clusters, or the workload is spiky and autoscale-to-zero matters.

**Choose neither when** the transformation is expressible in SQL over a partitioned table. BigQuery will usually be cheaper, simpler, and faster than a Spark job doing the same aggregation. This is the most important line in the chapter: reach for Spark when the *shape* of the computation demands it, not because the data is large.

---

## 🛠️ Hands-On

### Exercise 1: the equivalent Spark job

The course's pure pipeline is what a Spark job would compute. Here is the DataFrame version, written so it parses without Spark installed.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events, render_summary_csv

# The Spark equivalent would be:
#
#   spark.read.csv("gs://bucket/events.csv", header=True)
#     .withColumn("amount_eur", col("amount") * col("rate"))
#     .groupBy("region")
#     .agg(count("*").alias("event_count"), sum("amount_eur").alias("revenue_eur"))
#     .orderBy("region")
#
# The grouping key and the aggregates are identical; only the engine differs.

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, rejected = ingest_events(handle.read().splitlines())

summary = aggregate_events(accepted)
print(render_summary_csv(summary))
print("rejected:", len(rejected))
```

Output:

```text
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36
rejected: 0
```

### Exercise 2: reason about the shuffle in the aggregate

The `aggregate_events` step is a shuffle: it groups by `region`, moving rows so that all rows with the same key land on the same side. The cost is proportional to shuffled bytes.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

shuffled_bytes = sum(
    len(str(row["event_id"])) + len(str(row["region"])) + len(str(row["amount_eur"]))
    for row in accepted
)
print(f"rows:            {len(accepted)}")
print(f"approx shuffle:  {shuffled_bytes / 1024:.1f} KiB")
print(f"avg per row:     {shuffled_bytes / len(accepted):.1f} bytes")

summary = aggregate_events(accepted)
for region, values in sorted(summary.items()):
    print(f"{region:6s} {int(values['event_count']):5d} rows")
```

The shuffle for this dataset is trivial — about 87 KiB across 4800 rows, roughly 18.6 bytes per row. On a 100 TB dataset the same shape moves 100 TB across the network, and it is the dominant cost of the job. This is the mental model to carry to production: **the shuffle is the job**.

### Exercise 3: pre-aggregation versus raw grouping

`reduceByKey` performs a partial aggregation in the mapper. `groupByKey` does not. Compare the two effects.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events, bucket_by_window

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

# Raw grouping: every (window, region) pair keeps every row.
raw_pairs = bucket_by_window(accepted)
raw_payload = sum(len(rows) for rows in raw_pairs.values())

# Pre-aggregated: the combiner has already reduced each (window, region)
# to two numbers before the shuffle.
partial = {}
for window, rows in raw_pairs.items():
    for region, values in aggregate_events(rows).items():
        partial[(window, region)] = values
pre_payload = len(partial) * 40

print(f"raw grouped payload:    {raw_payload:6d} rows-equivalent")
print(f"pre-aggregated payload: {pre_payload:6d} rows-equivalent")
print(f"reduction factor:       {raw_payload / max(pre_payload, 1):.1f}x")
```

With 96 (window, region) pairs against 4800 rows, the pre-aggregated form carries 1.25 times fewer row-equivalents than the raw grouped form. The ratio is small here only because the windows are narrow; at realistic scale, where one key holds millions of rows, `groupByKey` ships every one of those rows across the network while `reduceByKey` ships a single partial sum. In Spark this is `reduceByKey` versus `groupByKey`; in DataFrame SQL it is `groupBy().agg()` versus a manual `collect_list`.

### Exercise 4: detect skew in the key distribution

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

counts = {
    region: int(values["event_count"])
    for region, values in aggregate_events(accepted).items()
}
total = sum(counts.values())
mean = total / len(counts)
variance = sum((c - mean) ** 2 for c in counts.values()) / len(counts)

print(f"total rows: {total}")
print(f"keys:       {len(counts)}")
print(f"mean:       {mean:.1f}")
print(f"std dev:    {variance ** 0.5:.1f}")
print(f"max/mean:   {max(counts.values()) / mean:.3f}")
print("skewed:", max(counts.values()) / mean > 2.0)
```

A max/mean ratio above 2 suggests skew. Above 10 is a serious problem: one task carries most of the work and the stage's wall-clock time is set by that task alone.

### Exercise 5: cost a Dataproc cluster versus a BigQuery scan

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate

# A Standard cluster with a 4-vCPU master and three 8-vCPU workers,
# running for 2 hours.
cluster = estimate("dataproc", vcpu_hours=28 * 2)
print(cluster)
print()

# A Serverless batch job that runs for 15 minutes on 8 vCPUs.
serverless = estimate("dataproc", vcpu_hours=8 * 0.25)
print(serverless)
print()

# The same aggregation as a partitioned BigQuery query.
warehouse = estimate("bigquery", scanned_tb=0.01)
print(warehouse)
```

The Serverless batch figure is roughly a fifteenth of the Standard cluster figure for the same workers, because the Standard cluster bills for its whole life. This is why ephemeral and serverless are the default choices for scheduled work.

### Exercise 6: the architecture decision table

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import compare_architectures, format_comparison

options = compare_architectures(
    scanned_tb=2.0,
    partition_factor=0.01,
    streaming_hours=8,
    batch_runs=2,
)
print(format_comparison(options))
```

Read the table carefully. The partitioned BigQuery batch is usually the cheapest option because the warehouse charges only for what it scans, and partitioning cuts that by two orders of magnitude. Spark earns its place when the computation cannot be expressed as a SQL aggregation over a partitioned table.

---

## 🛠️ Common Errors and Fixes

### 1. `gcloud dataproc clusters create` fails on quota

```text
ERROR: (gcloud.dataproc.clusters.create) Could not fetch resource:
 - The zone 'us-central1-a' does not have enough resources available to
   satisfy the request: 'n1-standard-4' resources.  Other resources may
   satisfy the request.
```

**Cause.** The zone has no free capacity for that machine type, or the per-region CPU quota is exhausted. The message is deliberately ambiguous: it can mean either.

**Fix.** Check `gcloud compute regions describe us-central1 --format="value(quotas)"` and the VM quota for `n1-standard-4`. Then either pick a different zone or a different machine family (the `standard-machine-types-*` aliases roll up many shapes; `n1-standard-4` is one specific instance type). For resilient production pipelines, retry across a list of zones rather than failing.

### 2. `Error: Cluster is in state RUNNING` — or `cannot submit job, cluster is not running`

```text
ERROR: (gcloud.dataproc.jobs.submit.pyspark) Cluster 'events-etl' is in state
TERMINATING, cannot submit job.
```

**Cause.** The cluster hit `--max-idle-duration` or `--max-ttl` and is shutting down, or a previous create failed and left it in a non-running state.

**Fix.** Check `gcloud dataproc clusters describe events-etl --region=us-central1` for the actual status and the `statusState` field. If the cluster is terminating, create a new one. If the state is `ERROR`, read `gcloud dataproc clusters describe --format="value(status.details)"` for the creation error, and delete the cluster before recreating it — a failed cluster often cannot be repaired in place.

### 3. `java.lang.OutOfMemoryError` or `Container killed by YARN for exceeding memory limits`

```text
WARN Container killed by YARN for exceeding memory limits.
5.5 GB of 5 GB physical memory used. Consider boosting job memory or reducing
the memory used by your job.
```

**Cause.** The executor JVM heap plus off-heap memory exceeded the container allocation. Also common: a single partition holding more data than fits in memory, which Spark cannot split further because the partition is indivisible.

**Fix.** Raise the executor allocation and keep the heap below it:

```bash
-- spark.submit.executor.memory=8g \
-- spark.executor.memoryOverhead=2g \
-- spark.executor.memoryOverheadFactor=0.15
```

If a single task still fails, the problem is partition size, not total memory. Repartition the input so no partition is enormous, or use AQE's skew handling to split it.

### 4. `py4j.protocol.Py4JJavaError: An error occurred while calling None.sparkContext`

```text
py4j.protocol.Py4JJavaError: An error occurred while calling None.sparkContext
org.apache.spark.SparkException: Job aborted due to stage failure:
Task not serializable
```

**Cause.** The closure passed to `map` or `filter` captures an object that cannot be serialised — typically a database connection, a file handle, or a module-level Spark session.

**Fix.** Close over only serialisable values. Move the connection inside the function, or use a native column expression instead of a Python UDF. In PySpark, `F.udf` closures must be picklable; the usual offenders are open sockets and `SparkContext` itself.

### 5. `pyspark.errors.exceptions.connect.SparkConnectGrpcException` or version mismatch on submit

```text
ValueError: PySpark requires Python 3.8+, but your version is 3.6
```

or

```text
org.apache.spark.SparkException: Job aborted due to stage failure:
java.lang.NoSuchMethodError: 'void org.apache.spark.sql.Column.<init>(...)'
```

**Cause.** The `pyspark` package version does not match the cluster's Spark version — usually because you installed PySpark locally with a different version than the cluster image, or the image version changed without your dependencies being updated.

**Fix.** Pin the version explicitly:

```bash
pip install "pyspark==3.5.*" \
  --index-url https://pypi.org/simple
```

and set the job's `spark-env-version` metadata to match the cluster image version. Check the actual cluster version with `gcloud dataproc clusters describe --format="value(config.softwareConfig.imageVersion)"` and install the identical PySpark version.

### 6. `AnalysisException: Table or view not found: default.events`

```text
AnalysisException: [TABLE_OR_VIEW_NOT_FOUND] The table or view `default.events`
cannot be found among: [customers, orders, region_lookup]
```

**Cause.** The job expects a table in a Hive metastore that does not have it — either the metastore is empty, the wrong metastore location was configured, or the table was created in a different database than the one the job queries.

**Fix.** Register the table explicitly before querying it, or point at the metastore:

```python
spark.sql("CREATE DATABASE IF NOT EXISTS analytics")
spark.read.parquet("gs://bucket/events/").createOrReplaceTempView("events")
```

On Dataproc, the Hive metastore is created with the cluster and destroyed with it. If your jobs need a durable metastore, create a Cloud SQL instance and point `javax.jdo.option.ConnectionURL` at it — and remember that this metastore outlives the cluster, so table definitions persist while the data must live in GCS.

---

## 💡 Production Notes

- **Pin the image version.** Never use `latest`. A silent image change can break a connector, a Python library, or an Avro schema in ways that look like data corruption.
- **Set `--max-idle-duration` and `--max-ttl` on every Standard cluster.** An unbounded cluster is an unbounded bill, and the runaway cluster is one of the classic cloud cost incidents.
- **Prefer Dataproc Serverless batch for scheduled pipelines.** It removes cluster lifecycle from your code and bills only for the work.
- **Keep Spot workers off the master.** And enable speculation when Spot is in use, or a single preemption can fail a long stage.
- **Turn on AQE.** `spark.sql.adaptive.enabled=true` with skew join handling solves most "one task is slow" problems without code changes. Set it at the job level, not by editing the cluster image.
- **Measure shuffle read/write bytes per stage.** That single metric, from the Spark UI or the job history, tells you where the time went and whether a repartition would help.
- **Set `spark.sql.shuffle.partitions` deliberately**, and remember AQE may reduce it afterwards. The static default of 200 is wrong for both tiny and very large jobs.
- **Prefer native SQL functions over Python UDFs.** Every Python UDF round-trips data out of the JVM and back. If you must use one, check whether Arrow is enabled and whether the payload fits under 2 GB.
- **Cache only reused, expensive lineages, and always materialise them with a `count()`.** Otherwise you recompute silently.
- **Keep a durable Hive metastore when jobs need shared table definitions.** A per-cluster metastore makes every job start from nothing.

---

## 🔑 Key Takeaways

- Spark beat MapReduce by keeping intermediate results in memory and collapsing stage boundaries; the lineage model makes recomputation cheap enough to be safe.
- DataFrames replaced RDDs because a schema enables optimisation. Catalyst rewrites logical plans — predicate pushdown, column pruning, join reordering — and Tungsten provides off-heap memory, columnar storage, and whole-stage code generation.
- Transformations are lazy and build a DAG; actions materialise it. Every action re-executes the plan unless the result is persisted, so cache deliberately and materialise with `count()`.
- The shuffle — repartition, groupBy, join, distinct, sort — is where time and money go. Prefer `reduceByKey` over `groupByKey`, broadcast small sides, and size shuffle partitions to roughly 128 MB.
- Skew shows up as one slow task in a stage. Salting, broadcast joins, better key choice, and AQE skew handling are the four fixes; AQE solves most cases for free.
- Dataproc offers Standard (persistent), Ephemeral (one job, then deleted), and Serverless batch. Production batch pipelines should default to ephemeral or serverless; Standard clusters exist for interactive work and shared caches.
- Spot workers cut compute cost by roughly two-thirds but can be preempted. Keep the master on-demand, enable speculation, and checkpoint often.
- The cost shape differs fundamentally: Dataproc bills cluster size × time regardless of data volume, while BigQuery bills data scanned. Reach for Spark when the *shape* of the computation demands it, not because the data is large.
- Dataproc versus Dataflow: Spark for complex batch ETL and custom algorithms with a familiar ecosystem; Dataflow for streaming, exactly-once semantics, unified batch and stream, and zero cluster management.

---

## 📚 Practice Exercises

1. **Write the DataFrame equivalent.** Using `sample_data/events.csv` as the source, write the PySpark script that reads the file, derives `amount_eur` and `event_dt`, and produces the region aggregate. Then write a pure-Python version that produces byte-identical output to `render_summary_csv`, and diff them.
2. **Compare reduceByKey and groupByKey.** Using `bucket_by_window` and `aggregate_by_window`, measure the payload size of raw grouping versus pre-aggregated grouping. Explain in Spark terms which API each maps to and what the network cost difference would be at 100 TB.
3. **Size the shuffle partitions.** Compute the shuffle bytes for the course dataset and derive the number of shuffle partitions at a 128 MB target. Then compute the same for a hypothetical 50 TB dataset and compare with Spark's default of 200.
4. **Detect skew programmatically.** Write a function that takes a list of key counts and returns the max/mean ratio plus a boolean skew flag. Apply it to the region aggregate, to the per-window aggregate, and to a synthetic distribution with one dominant key.
5. **Cost the three Dataproc cluster types.** Using `cost_model.estimate("dataproc", vcpu_hours=...)`, price (a) a Standard cluster with 28 vCPUs alive for 8 hours, (b) the same cluster used by an ephemeral job that runs 20 minutes, and (c) a Serverless batch job with 8 vCPUs for 20 minutes. Explain the gap.
6. **Design a Dataproc cluster for a nightly job.** Specify the image version, machine types, worker count, `--max-idle-duration`, `--max-ttl`, Spot settings, and the AQE configuration properties. Justify every choice in one sentence.
7. **Investigate Hive metastore durability.** Explain what happens to table definitions when an ephemeral Dataproc cluster is deleted, and describe how you would configure a shared Cloud SQL metastore so that a job can `SELECT` from a table another job created.
8. **Decide Spark versus BigQuery.** Take the course pipeline and write down which parts are pure SQL aggregations, which parts need custom logic, and which parts need streaming state. For each part, name the tool you would actually use and defend the choice.

---

## 📖 Further Reading

- [Apache Spark: Programming Guide](https://spark.apache.org/docs/latest/programming-guide.html)
- [Spark SQL Performance Tuning Guide](https://spark.apache.org/docs/latest/sql-performance-tuning.html)
- [Spark Configuration Guide](https://spark.apache.org/docs/latest/configuration.html)
- [Dataproc: Submit a Job](https://cloud.google.com/dataproc/docs/concepts/submitting-jobs)
- [Dataproc: Serverless Batch Jobs](https://cloud.google.com/dataproc/docs/concepts/processors/serverless/batch)
- [Dataproc: Cluster Modes and Components](https://cloud.google.com/dataproc/docs/concepts/cluster-types)
- [Dataproc: Pricing](https://cloud.google.com/dataproc/pricing)
