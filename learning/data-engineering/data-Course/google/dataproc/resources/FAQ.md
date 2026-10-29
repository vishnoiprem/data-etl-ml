# Dataproc + PySpark FAQ

> The questions students actually ask.

---

## Getting started

### Do I need a GCP account to follow the course?

Yes. Dataproc is a Google Cloud service, so you need a project with billing enabled. But the cost of completing every exercise is genuinely small — a single-node cluster for a few hours per week is a few dollars a month.

You do **not** need a credit card for the first steps: every chapter up to "Writing a DataFrame to a sink" can be done in PySpark on your laptop (see "Can I run this locally?" below). The GCP account is needed for the submitted-job, GCS, and BigQuery exercises.

### Do I need to worry about accidentally running up a huge bill?

The three protections, in order of importance:

1. **Always set `--delete-max-idle=30m` and `--delete-max-age=8h` on every cluster.** A cluster with no activity for 30 minutes deletes itself. This alone prevents the "forgot about it over the weekend" bill.
2. **Delete the cluster when the chapter is done.** `gcloud dataproc clusters delete CLUSTER --region=us-central1`.
3. **Set a budget alert** at $5, $20, and $50. It does not cap spending, but it tells you within minutes rather than at the end of the month.

A 3-worker `n2-standard-4` cluster runs about $3–4/hour. A month of forgetting costs more than the course.

### Can I run this locally?

Yes, and you should for the first several chapters. Install PySpark and use `local[*]`:

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("local").master("local[*]").getOrCreate()
```

`local[*]` uses all your machine's cores. `resources/spark_helpers.py` handles this: `get_spark(local=True)` builds a local session, `get_spark(local=False)` builds a cluster-mode one.

What you **cannot** do locally:
- `gs://` paths (unless you install `gcsfs` and authenticate, which is fiddly)
- Writing to BigQuery (needs a real project and credentials)
- Distributed behaviour — no partial task failure, no shuffle across nodes

What you **can** do locally: everything about DataFrames, joins, window functions, and the SQL API. That is most of the course.

### Which region should I use?

`us-central1` for the widest machine-type availability and the most public sample data. If your organisation has data-residency requirements, pick the matching region from the start — a cluster's region determines where its VMs and its staging bucket live, and moving it later means rebuilding everything.

### Which Python version?

Dataproc's `2.2-debian12` image ships Python 3. The `requirements.txt` in this course targets Python 3.9+ with 3.11 recommended. Keep your local venv on the same major version as the cluster to avoid surprises with pandas/pyarrow behaviour.

### Which Spark version?

`2.2-debian12` ships **Spark 3.5.3**. The `requirements.txt` pins `pyspark>=3.5.0` so your local environment matches. Never install a PySpark version that differs from the cluster's by more than a minor version — the Python-to-JVM protocol breaks in confusing ways.

---

## Clusters & cost

### How much will this cost me?

Roughly, for a course-sized cluster (1 master + 2 workers on `n2-standard-4`):

| Item | Approximate cost |
|------|------------------|
| Master `n2-standard-4` | ~$0.19 / hour |
| Worker `n2-standard-4` (x2) | ~$0.38 / hour |
| Spot secondary worker | ~$0.03 / hour |
| Persistent disk (100 GB, per node) | ~$0.05 / hour per node |
| **Total per hour** | **~$0.65 – $0.75** |

BigQuery is on-demand: $6.25 per TiB scanned, with 1 TiB free per month. The course's datasets are measured in megabytes, so BigQuery cost is effectively zero.

Realistic total for completing the course carefully: **$10 – $30.**

### Temporary cluster or persistent cluster?

| | Temporary | Persistent |
|---|---|---|
| Created | Per job | Once, manually |
| Deleted | With the job | By you, or by `--delete-max-age` |
| Cost | Only while the job runs | Continuous |
| Startup latency | ~2–4 minutes | Zero after creation |
| Good for | Production batch ETL, CI | Development, streaming, exploration |

**Rule for this course:** develop on a persistent cluster with `--delete-max-idle=30m --delete-max-age=8h`, then delete it when you finish the day. For anything you submit repeatedly, use a temporary cluster.

💡 **A persistent cluster with a 30-minute idle timeout is nearly as cheap as a temporary one**, and it removes the 3-minute startup from every experiment. The risk with a persistent cluster is only that you forget it exists — which `--delete-max-age` handles.

### How do I set up autoscaling?

Create a policy file and import it:

```yaml
# autoscaling-policy.yaml
clusterType: STANDARD
workerConfig:
  minInstances: 2
  maxInstances: 20
  weight: 1
secondaryWorkerConfig:
  minInstances: 0
  maxInstances: 50
  weight: 1
basicAlgorithm:
  cooldownPeriod: 2m
  yarnConfig:
    scaleUpFactor: 0.05
    scaleDownFactor: 1.0
    gracefulDecommissionTimeout: 1h
```

```bash
gcloud dataproc autoscaling-policies import my-policy \
  --source=autoscaling-policy.yaml --region=us-central1

gcloud dataproc clusters create my-cluster \
  --region=us-central1 \
  --autoscaling-policy=my-policy \
  --master-machine-type=n2-standard-4 \
  --worker-machine-type=n2-standard-4 \
  --image-version=2.2-debian12
```

⚠️ **Autoscaling does not work with** HDFS-based workloads (DataNode decommissioning takes hours), Structured Streaming (the cluster shape is pinned), YARN node labels, or idle-cluster scale-down. It scales **worker VMs** horizontally only — never the machine type.

⚠️ **When you use Dataproc autoscaling, leave `spark.executor.instances` unset** so Spark's dynamic allocation can decide how many executors per worker. Setting it disables dynamic allocation.

### How do I choose a machine type?

Match the ratio to the bottleneck:

| Workload | Machine type | Why |
|----------|--------------|-----|
| General ETL | `n2-standard-4` | Balanced 1:1 CPU:memory |
| Heavy shuffles, wide aggregations | `n2-highmem-4` | More RAM per core; survives GC pressure |
| CPU-bound string processing, large UDFs | `n2-highcpu-8` | More cores; but only 3.6 GB RAM each |
| Interactive exploration | `n2-highmem-4` | Cache more without spilling |
| ARM-compatible only | `c4a-standard-4` | Cheaper per vCPU; some native libraries break |

⚠️ **`n1-standard-1` is not supported on 2.0+ images.** Shared-core types (`e2-micro`, `f1-micro`) are not supported at all. For a tiny cluster, use `--cluster-type=single-node`.

⚠️ **The classic mistake is `highcpu` for a shuffle-heavy join.** You get four cores and then spend all your time in GC. If you are shuffling, buy memory.

### Why did my cluster get preempted?

Because Spot VMs can be reclaimed at any time. In Dataproc this affects **secondary workers** only — primary workers are on-demand and are not preempted.

**This is by design, and it is safe for batch jobs.** Spark's execution model is fault-tolerant: when an executor dies, its tasks are reported back to the scheduler and re-assigned to another worker. You lose compute time, not correctness.

**If you need the work to finish without interruption:**
- Move the job to primary workers (`--num-workers=N`, `--num-secondary-workers=0`).
- Raise `spark.task.maxFailures` (default 4) so Spark tolerates more retries.
- Avoid putting a single huge task on one worker.

### How do I stop a cluster but keep its data?

```bash
gcloud dataproc clusters stop CLUSTER --region=us-central1
```

A stopped cluster keeps its disks and its configuration, and it does **not** bill for CPU — but it **does** bill for the persistent disks. A stopped cluster with 3 × 100 GB disks costs about $0.15/hour.

Or, on creation:

```bash
--stop-max-idle=30m
--stop-max-age=8h
--stop-expiration-time=2026-10-28T18:00:00Z
```

### How do I delete a cluster I forgot about?

```bash
gcloud dataproc clusters list --region=us-central1
gcloud dataproc clusters delete CLUSTER --region=us-central1
```

To delete every cluster in a region:

```bash
for c in $(gcloud dataproc clusters list --region=us-central1 --format="value(name)"); do
  gcloud dataproc clusters delete "$c" --region=us-central1 --quiet
done
```

---

## PySpark & Spark

### Why is my job stuck in PENDING?

`PENDING` means the Dataproc Jobs API has the job but the cluster's agent has not started it yet. Common causes:

1. **The cluster is still provisioning.** Cluster creation takes 2–4 minutes. The job waits.
2. **The cluster is `RUNNING` but busy.** Dataproc limits concurrent jobs to `max((masterMemoryMb - 3584) / 1024, 5)`. With a small master, that is 5. A 6th job waits.
3. **A job-management race.** Submitting jobs in a tight loop can race. Space submissions out by at least a fraction of a second.

Check the actual state:

```bash
gcloud dataproc jobs describe JOB_ID --region=us-central1 \
  --format="value(status.state, status.substate, status.details)"
```

`SETUP_DONE` means the service has it and setup is complete. `RUNNING` with substate `QUEUED` means the agent submitted it to YARN and it is waiting for resources.

### What is a shuffle and why is it slow?

A shuffle is the redistribution of data across executors. It happens on joins, group-bys, window functions, and sorts.

The cost: map output is **serialized**, **written to disk**, **transferred over the network**, and **deserialized** on the other side. Four expensive operations, and it happens at every stage boundary.

**A shuffle is the single biggest cost in a Spark job.** Reducing shuffles is usually the highest-leverage optimisation. The three tools:
- **Broadcast** the small side of a join (`F.broadcast(small_df)`) — eliminates the shuffle entirely.
- **Raise `spark.sql.autoBroadcastJoinThreshold`** if your dimension is a few MB and the fact is large.
- **Let AQE handle it** — it coalesces small partitions and splits skewed ones at runtime.

### Why is my job slow?

Read the Spark UI's Stages tab, in this order:

1. **Which stage is slow?** Not the last one — the longest one.
2. **Look at the task durations.** If one task takes 10× the others, that is **skew**.
3. **Look at the "Shuffle Read/Write" columns.** If the shuffle size is large, the join or group-by is the problem.
4. **Look at the "Duration" vs "GC Time".** If GC dominates, you need more memory per executor, not more executors.
5. **Check the input size.** If it is small and the job is slow, the problem is the plan, not the data.

Common causes in order of likelihood:
- **Skewed join key** — one key has most of the rows.
- **Too many shuffle partitions** — 200 tiny tasks each doing almost nothing.
- **A Python UDF** — serializing data across the JVM boundary.
- **`collect()` on a large result** — pulls everything to the driver.
- **Too few executor instances** — you forgot to set `spark.executor.instances`, so Spark ran on one executor.

### How do I avoid skew?

**1. Use AQE's skew handling** (enabled by default in Spark 3.2+):

```
spark.sql.adaptive.enabled=true
spark.sql.adaptive.skewJoin.enabled=true
```

AQE detects a partition that is much larger than the median and splits it.

**2. Broadcast the small side.** If one side of the join is under ~10 MB, broadcast it and there is no shuffle to skew.

**3. Salt the key.** Add a random suffix to the hot key, join, then aggregate away the salt:

```python
from pyspark.sql import functions as F

salted = fact.withColumn("salt", (F.rand() * 10).cast("int"))
salted = salted.withColumn("join_key", F.concat(F.col("key"), F.lit("-"), F.col("salt")))
dim_salted = dim.withColumn("salt", F.lit(0))  # replicate the dim 10 times
result = salted.join(dim_salted, "join_key")
```

**4. Filter the nulls out.** `key IS NULL` and `"UNKNOWN"` are the most common skew culprits. Handle them separately.

**5. Look at the task distribution in the Spark UI.** If the 90th percentile is 10× the median, that is skew.

### Why is my Python UDF slow?

A Python UDF requires a **separate Python process on every executor**. Spark must:
1. Serialize the row to bytes.
2. Send it across the Python↔JVM boundary (Py4J).
3. Run your Python function.
4. Serialize the result back.

That round-trip costs milliseconds per row. A UDF on a million rows is a million round-trips.

**The fix, in order of preference:**

| Approach | Speed | Use when |
|----------|-------|----------|
| A built-in function | 100× | There is one (`F.regexp_replace`, `F.to_timestamp`, `F.split`) |
| A SQL expression | 100× | It can be expressed in SQL |
| A **Pandas UDF** (vectorized) | 10× | Your logic genuinely needs Python (`pandas_udf`) |
| A Scala UDF | 5× | You are willing to write Scala |
| A plain Python UDF | 1× | Last resort |

💡 **The most common Python UDF in this course is a date parser.** You do not need one:

```python
# Instead of a UDF
F.to_timestamp(F.col("ts"), "yyyy-MM-dd'T'HH:mm:ss")
```

A **vectorized (Pandas) UDF** processes a whole Arrow batch at once and is often 10–20× faster than a row-at-a-time Python UDF:

```python
from pyspark.sql.functions import pandas_udf
import pandas as pd

@pandas_udf("string")
def norm(s: pd.Series) -> pd.Series:
    return s.str.strip().str.upper()
```

Enable Arrow for it:

```
spark.sql.execution.arrow.pyspark.enabled=true
```

### Why did my data duplicate on re-run?

**The most common cause: `WRITE_APPEND` on a re-run.** The append mode adds rows; it does not replace. Running the job twice loads everything twice.

**The fix — pick one:**

**A. Delete the partition, then append.** This is the pattern the course's SQL uses:

```sql
DELETE FROM `p.gold.fact_sales` WHERE sales_date = DATE '2026-10-27';
-- then MERGE / append the day's rows
```

**B. Use a MERGE** (upsert). Idempotent by construction — the SQL scripts in this course use it.

**C. Use `WRITE_TRUNCATE` with `partitionField`.** This truncates only the named partition:

```python
(df.write
  .format("bigquery")
  .option("writeDisposition", "WRITE_TRUNCATE")
  .option("temporaryGcsBucket", "my-bucket")
  .option("partitionField", "sales_date")
  .save("my-project.gold.fact_sales"))
```

⚠️ **`WRITE_TRUNCATE` without `partitionField` deletes the whole table.** For a fact table, that means losing all history. If you want a full rebuild, that is what you want — but you must know which mode you are in.

**D. `mode("overwrite")` on Parquet** replaces the whole directory. For a full rebuild of a dataset, this is correct and simple.

The deeper issue: **a non-idempotent write is a design bug, not a usage error.** A pipeline that cannot be re-run safely will eventually be re-run at 3am by someone who has not read the code.

### How do I debug locally?

**1. Run the exact same code with `local[*]`.** The DataFrame logic is identical. You lose distribution, not correctness.

```python
from spark_helpers import get_spark
spark = get_spark(app_name="debug", local=True)
```

**2. `df.explain(True)`** — read the plan. The answer is usually in there.

**3. `df.printSchema()` and `df.show(5, truncate=False)`** — check the shape before the logic.

**4. Print intermediate values:**

```python
df.withColumn("stage", F.lit("after_filter")).show(20, truncate=False)
```

**5. `df.rdd.map(lambda r: r).take(5)`** — when you need to see the raw rows.

**6. Attach a debugger** — in a notebook, `df.explain()` and `%debug` work. For a script, use `pdb.set_trace()`.

**7. For the driver specifically**, the log is `stdout`. Read it with:

```bash
gcloud dataproc jobs wait JOB_ID --region=us-central1
```

### Why is my job running with only one executor?

Because `spark.executor.instances` defaults to **1**, and it overrides the cluster's actual worker count.

Two fixes:

**A. Set it explicitly** (per job, via `--properties`):

```bash
gcloud dataproc jobs submit pyspark main.py --cluster=CLUSTER \
  --properties="spark.executor.instances=8,spark.executor.memory=4g,spark.executor.cores=2" \
  -- main.py
```

**B. Use dynamic allocation** (let Spark decide, based on demand):

```
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.minExecutors=2
spark.dynamicAllocation.maxExecutors=40
spark.dynamicAllocation.initialExecutors=8
```

⚠️ **Setting `spark.executor.instances` disables dynamic allocation.** If you use Dataproc autoscaling, leave it unset.

⚠️ **Always set `spark.dynamicAllocation.maxExecutors`.** The default is `infinity`, and an unbounded executor count plus a data bug is an unbounded bill.

### How do I read the driver logs?

```bash
# Block until done and print the output
gcloud dataproc jobs wait JOB_ID --region=us-central1

# Just the output URI
gcloud dataproc jobs describe JOB_ID --region=us-central1 \
  --format="value(driverOutputUri)"

# Read it from GCS
gcloud storage cat gs://STAGING_BUCKET/google-cloud-dataproc-metainfo/JOB_ID/*/stdout
```

In Cloud Logging:

```bash
gcloud logging read \
  "resource.type=cloud_dataproc_cluster \
   AND resource.labels.cluster_name=my-cluster \
   AND severity>=WARNING" \
  --project=YOUR_PROJECT_ID --limit=50
```

💡 **Your `print()` statements are what you want.** Spark's progress bars go to stderr and are extremely noisy. The driver stdout is the signal.

### How do I cancel a stuck job?

```bash
gcloud dataproc jobs kill JOB_ID --region=us-central1
```

Or find it first:

```bash
gcloud dataproc jobs list --region=us-central1 --state-filter=active
```

To stop the job from inside the driver code, call `sys.exit(1)` or raise an exception — Spark will shut the executors down.

### What is the difference between `cache()` and `persist()`?

`cache()` is `persist()` with the default storage level (`MEMORY_AND_DISK` for DataFrames). `persist()` lets you choose:

| Storage level | Speed | Reliability |
|---------------|-------|-------------|
| `MEMORY_ONLY` | Fastest | Recomputes on loss |
| `MEMORY_AND_DISK` (default) | Fast | Spills to disk |
| `DISK_ONLY` | Slower | Safe |
| `MEMORY_ONLY_SER` | Fast | Recomputes, less memory |

⚠️ **Always `unpersist()` when you are done.** A cached DataFrame holds memory on every executor until it is released. Caching without unpersisting is the most common cause of "why is my second job slower than my first".

### What is the difference between a transformation and an action?

A **transformation** builds a plan; it does not execute. A **action** triggers the job.

```python
df.filter(F.col("x") > 1)      # transformation — nothing happens
df.count()                     # action — the job runs NOW
```

⚠️ **Each action re-executes the whole plan**, unless the data is cached or checkpointed. Three actions on the same un-cached DataFrame means three full computations.

### What is `collect()` and why is it dangerous?

`collect()` pulls every row into the driver's memory as a Python list. If the DataFrame has a million rows, your master node's heap must hold them.

```python
rows = df.collect()       # 1M rows → driver OOM
rows = df.limit(10).collect()   # fine
rows = df.take(10)              # fine
```

⚠️ **The driver runs on the master node.** A `collect()` that OOMs takes down the master, which kills every executor and the job. Use `limit()`, `take()`, `show()`, or `toPandas()` on a bounded result.

### When should I use an RDD instead of a DataFrame?

Almost never, for structured data. Use an RDD when:

- Your data is genuinely unstructured and you need fine-grained control over the record format.
- You need a custom partitioning or a custom serialization.
- You are chaining many narrow transformations and want to avoid the Catalyst optimizer's overhead.

For everything else — joins, aggregations, window functions, CSV/Parquet/JSON, BigQuery — the DataFrame API is faster, safer, and more readable.

---

## BigQuery & GCS

### Why is my write to BigQuery failing?

The error messages tell you which layer failed. Work down this list:

**"403 ... does not have permission to run a job"** → The identity needs `roles/bigquery.jobUser`.

**"Access Denied: ... storage.googleapis.com"** or **"403 ... does not have storage.buckets.get"** → Two separate problems:
- The cluster was created without `--scopes=https://www.googleapis.com/auth/cloud-platform`. The default Compute Engine scope list excludes BigQuery and GCS write access. **This is the most common cause of "works in Jupyter, fails when submitted".**
- The identity needs `roles/storage.objectAdmin` on the staging bucket.

**"Could not find the temporary bucket"** → `temporaryGcsBucket` is missing or misspelled, and the connector has nowhere to write the Parquet files.

**"Cannot write to a table with no partition"** → You used `WRITE_TRUNCATE` on a table that has no partitioning. Add `partitionField`, or use `WRITE_APPEND`.

**"Schema mismatch"** → The DataFrame's schema does not match the table. Check `df.printSchema()` against the table definition. `enableModeCheckForSchemaFields=false` relaxes it.

**"Access Denied: User ... does not have storage.buckets.create"** → The connector's default behaviour creates a temporary bucket if you do not specify one. Always specify `temporaryGcsBucket`.

### What is a temporary GCS bucket and why do I need one?

The BigQuery connector works in two steps:
1. Write Parquet files to a GCS bucket.
2. Issue a BigQuery LOAD job pointing at those files.

The bucket in step 1 is a **staging area** — intermediate files, not data. By default, if you do not specify one, the connector tries to create a temporary bucket for you, which needs `storage.buckets.create` permission and surprises people.

**Best practice: create your own staging bucket with a lifecycle rule** that deletes the files after a day, and pass it explicitly:

```python
.option("temporaryGcsBucket", "my-project-bq-staging")
```

The lifecycle rule:

```json
[
  { "action": { "type": "Delete" }, "condition": { "age": 1 } }
]
```

### What is the difference between the BigQuery connector and the Storage Write API?

| | Connector (default) | Storage Write API |
|---|---|---|
| Mechanism | Parquet → GCS → LOAD job | Direct gRPC streaming inserts |
| Throughput | Excellent for batch | Excellent for streaming |
| Cost | Transient GCS storage + the load | $0.01/GiB after the free tier |
| Idempotency | Easy — partition-scoped `WRITE_APPEND` | Hard — you must deduplicate yourself |
| Best for | Batch ETL from Spark | High-rate streaming ingestion |

💡 **For this course's batch jobs, use the connector.** The Storage Write API's exactly-once story is harder than the connector's, and you get no benefit unless you are streaming.

### Why does my BigQuery query cost more than I expected?

Check, in order:

1. **No partition filter.** The query scanned the whole table. This is the cause 80% of the time.
2. **`SELECT *` in a subquery.** Column pruning stops at the subquery boundary.
3. **A join that exploded.** A many-to-many join multiplies the bytes.

The exact answer is in the console's "Execution details" tab, or:

```sql
SELECT job_id, total_bytes_billed
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
ORDER BY total_bytes_billed DESC;
```

### What is a temporary bucket in the context of the connector?

Same answer as above — the GCS staging area for the connector's Parquet files. See "What is a temporary GCS bucket and why do I need one?".

### How do I read from GCS in Spark?

```python
df = spark.read.parquet("gs://my-bucket/sales/")
df = spark.read.csv("gs://my-bucket/sales/*.csv", header=True, inferSchema=True)
df = spark.read.json("gs://my-bucket/claims/*.json")
```

The GCS connector is pre-installed on Dataproc — no JAR to add.

⚠️ **`inferSchema=True` samples the data and can guess wrong.** In production, always pass an explicit schema.

### How do I write partitioned Parquet to GCS?

```python
(df.write
  .mode("overwrite")
  .option("partitionOverwriteMode", "DYNAMIC")
  .partitionBy("sales_date")
  .parquet("gs://my-bucket/gold/fact_sales"))
```

`DYNAMIC` mode is what makes re-runs idempotent: it replaces only the partitions being written, leaving other dates alone. Without it, `overwrite` wipes the entire directory.

### Why is my Spark job not seeing the file I just uploaded?

**1. Wildcard matching happens at job start.** If you uploaded the file after the job began, the job does not see it. Upload first.

**2. The path is wrong.** Use the full `gs://bucket/path` form, not a relative path.

**3. The file has a `_` or `.` in its name.** Spark's glob treats `_` and `.` as single-character wildcards. A file named `orders_2026-10-27.csv` matches `orders_*.csv` — but a directory named `part_0001` can also match `part?0001`. Use `*` where you mean "any".

**4. The listing is stale.** The GCS connector caches directory listings. If a job creates and then reads files in the same run, use `spark.sql.sources.parallelPartitionDiscovery.parallelism` or write and read in separate jobs.

---

## Performance

### How do I read the Spark UI to find the bottleneck?

The **Stages** tab, in this order:

1. **Sort stages by "Duration"** and open the longest one.
2. **Look at the Summary Metrics table** for that stage:
   - **Duration** — total time.
   - **GC Time** — if this is a large fraction, you need more memory, not more executors.
   - **Shuffle Read/Write** — if large, the join or aggregation is the problem.
   - **Input Size/Records** — if tiny and the stage is slow, the plan is the problem.
3. **Look at the task distribution in the Event Timeline.** One long bar among many short ones is **skew**. A uniform wall of bars is a genuinely large workload.
4. **The SQL tab** shows the parsed and analyzed plan with the same skew information.

### What is the difference between `coalesce` and `repartition`?

| | `coalesce(n)` | `repartition(n)` |
|---|---|---|
| Mechanism | Reduces partitions, no shuffle | Redistributes, **with a shuffle** |
| Can it increase the count? | **No** | Yes |
| Can it specify a key? | No | Yes — `repartition("col")` |
| Data placement | Keeps the existing data in the first N partitions | Evenly distributed |

Use `coalesce(1)` to write exactly one output file (for a small result you want to read locally). Use `repartition("col")` to group data by a key before writing.

⚠️ **`coalesce` on a shuffled DataFrame produces badly skewed output files.** The first partition keeps all of partition 0's data; the others get whatever is left. If you have already shuffled, `repartition` is the correct choice.

### Should I cache my DataFrame?

**Yes**, when:
- You use the same DataFrame in **more than one action**.
- The computation is **expensive** (a multi-way join, a heavy window function).
- The DataFrame is small enough to fit in memory.

**No**, when:
- You use it once. Caching costs a write and a read for no benefit.
- It is much larger than the available memory — it will spill to disk and be slower than recomputing.

```python
df.cache()
df.count()          # materialise the cache
df.groupBy("a").count()
df.groupBy("b").count()
df.unpersist()      # release it
```

💡 **Always call `unpersist()`.** A cached DataFrame holds memory on every executor until released.

### What is AQE and should I always enable it?

**Adaptive Query Execution** rewrites the physical plan at runtime using the shuffle statistics it actually observed, rather than the estimates it had at planning time. It can:

- **Coalesce small shuffle partitions** — 200 tiny tasks become 20 reasonable ones.
- **Split skewed shuffle partitions** — the "one task takes 10× longer" problem.
- **Convert sort-merge joins to broadcast joins** — if one side turns out to be small.

**Yes, enable it.** It is on by default in Spark 3.2+ and it is almost always a win. The exception is a very small dataset where the overhead of the extra planning stage is not worth it.

### How do I reduce the cost of a BigQuery scan from Spark?

The BigQuery connector reads through the Storage API, and BigQuery bills the bytes it reads. The lever is **reading fewer bytes**.

1. **Filter on the partition column** before the join. The connector supports partition pruning if the filter is a literal comparison.
2. **Select only the columns you need.** The connector supports column pruning — `SELECT a, b` really does read only a and b.
3. **Read from Parquet, not CSV.** Parquet is columnar; a query touching 3 of 20 columns reads roughly 3/20 of the bytes.
4. **Partition your Parquet by the date you filter on**, so the connector skips whole files.

```python
df = (spark.read
  .format("bigquery")
  .option("readMethod", "direct")
  .load("my-project.silver.dim_product")
  .select("product_id", "product_name", "category_name"))
```

### How do I choose the number of shuffle partitions?

**Start with AQE and do not set it.** AQE coalesces the partitions for you at runtime.

If you must set it, the rule of thumb is:

```
spark.sql.shuffle.partitions ≈ 2–3 × total executor cores
```

For a 10-worker cluster with 4 cores each, that is 80–120 partitions. The default of **200** is too many for small data (200 tiny tasks, each with fixed overhead) and too few for large data.

**Read the Spark UI after your first run** and look at the shuffle write size per task. If it is a few MB, you have too many partitions. If it is hundreds of MB, you need more.

---

## Troubleshooting

### My job failed. Where do I look?

1. **The driver's exit code and error**, from the API:

```bash
gcloud dataproc jobs describe JOB_ID --region=us-central1 \
  --format="value(status.details, status.state)"
```

2. **The driver stdout/stderr**, which contains the Python traceback:

```bash
gcloud dataproc jobs wait JOB_ID --region=us-central1
```

3. **Cloud Logging** for executor-level errors:

```bash
gcloud logging read \
  "resource.type=cloud_dataproc_cluster \
   AND resource.labels.cluster_name=my-cluster \
   AND textPayload:\"Traceback (most recent call last)\"" \
  --project=YOUR_PROJECT_ID --limit=20
```

4. **The Spark UI** — the History Server runs on the master. Open the cluster's
   Jupyter component and use the **Spark UI** link in the Jupyter toolbar, or
   open the History Server directly on port 18080 through the Component Gateway.

### My job says `ERROR` but the log shows nothing useful.

The traceback is often the *last* thing in the driver output, and Spark's progress bars bury it. Get the raw file:

```bash
gcloud storage cat gs://STAGING_BUCKET/google-cloud-dataproc-metainfo/JOB_ID/*/stderr
```

Also check that your `print()` statements are actually flushed. In some buffering situations, a crash loses buffered stdout. Use `print(..., flush=True)` or `logging.info()`.

### I get `PERMISSION_DENIED: ... does not have permission to use service account`.

You are not allowed to *act as* the cluster's service account. Fix:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  dataproc-cluster-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --member="user:YOUR_EMAIL@example.com" \
  --role="roles/iam.serviceAccountUser" \
  --project=YOUR_PROJECT_ID
```

### I get `Access Denied: BigQuery: User ... does not have permission to run a job`.

Grant `roles/bigquery.jobUser`:

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:dataproc-cluster-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### My cluster creation failed after 10 minutes.

Check the operation:

```bash
gcloud dataproc operations list --region=us-central1 --limit=5 \
  --format="table(name,operationType,status.statusCode,status.errorMessage)"
```

Common causes:
- **Quota.** Check Compute Engine CPU and disk quotas for the region.
- **A missing IAM permission** — see above.
- **No network route to the internet gateway.** Dataproc creates the Private Google Access route automatically, but if you deleted the default route you must add it back.
- **A firewall rule blocking internal traffic.** The cluster VMs need to talk to each other.

### Everything is slow and I do not know why.

Three checks, in order:

1. **The Spark UI's Stages tab.** The longest stage, its GC time, and its shuffle size. This almost always answers it.
2. **`df.explain(True)`.** Look for `Exchange SinglePartition` (a bottleneck) or a `SortMergeJoin` that should have been a broadcast.
3. **The number of executors.** If you did not set `spark.executor.instances`, you are running on one.

### `java.lang.OutOfMemoryError: Java heap space`

The **executor** ran out of heap. Raise `spark.executor.memory` and lower `spark.executor.cores` (more cores with the same memory means less heap per core and worse GC).

If the error mentions the **driver**, the driver ran out of heap. Raise `spark.driver.memory` — or, better, stop `collect()`ing large results.

### `Total size of serialized results ... is bigger than spark.driver.maxResultSize`

You are collecting too much into the driver. Either raise the limit or, much better, reduce the result:

```python
df.count()                          # instead of df.collect()
df.limit(1000).toPandas()           # instead of df.toPandas()
df.write.mode("overwrite").parquet("gs://bucket/out")   # instead of collecting
```

### `SparkException: Task not found` or `ExecutorLostFailure` on Spot workers.

That is **preemption**. The tasks are re-run automatically. If it is happening constantly:

- Raise `spark.task.maxFailures` (default 4) to `10`.
- Move the job to primary workers (`--num-secondary-workers=0`).
- Check that you are not putting one enormous task on a single worker.

### `AnalysisException: Table or view not found: my-project.gold.fact_sales`

1. The dataset does not exist — `bq ls --project_id=my-project`.
2. The table does not exist yet — you are reading before writing.
3. The region is wrong — `bq ls` defaults to `US`. Pass `--location` if your dataset lives elsewhere.
4. The project is wrong — check `spark.conf.get("spark.databricks.project")` equivalent, or just use the fully qualified name.

### `Py4JJavaError: ... java.lang.IllegalArgumentException: Unsupported class file major version`

A Python/Java version mismatch between your local environment and the cluster. The cluster's Python is determined by the image version, not by your laptop. Check with:

```python
import sys; print(sys.version)
```

and compare against the cluster's Python by running a one-line job.

### The job succeeds but the output is empty.

```bash
# Did the input have rows?
# Add this to the driver:
print("INPUT ROWS:", df_input.count())
print("AFTER FILTER:", df_filtered.count())
```

The usual causes:
- A filter that excludes everything (a timezone bug, a date-format mismatch).
- Reading from the wrong path.
- An inner join where the key does not match — a whitespace or case difference between the two sides.

### How do I make my pipeline idempotent?

The checklist:

- [ ] Every write is scoped to a partition or a run date — never a full-table append.
- [ ] `MERGE` instead of `INSERT` for upserts.
- [ ] Deduplicate to the latest version using `QUALIFY` (or `row_number`) on a stable key.
- [ ] The run date is a **parameter**, never `CURRENT_DATE()` inside the transform.
- [ ] A re-run for date X replaces date X and touches nothing else.
- [ ] You can prove it: run twice, compare row counts and checksums.

```sql
-- The proof
SELECT COUNT(*), SUM(net_amount) FROM `p.gold.fact_sales` WHERE sales_date = DATE '2026-10-27';
-- run the job again
SELECT COUNT(*), SUM(net_amount) FROM `p.gold.fact_sales` WHERE sales_date = DATE '2026-10-27';
-- identical
```

---

## Further reading

- Dataproc documentation — https://cloud.google.com/dataproc/docs
- Dataproc image versions — https://cloud.google.com/dataproc/docs/concepts/versioning
- PySpark API reference — https://spark.apache.org/docs/latest/api/python/
- Spark tuning guide — https://spark.apache.org/docs/latest/sql-performance-tuning.html
- BigQuery connector options — https://github.com/GoogleCloudDataproc/spark-bigquery-connector
- BigQuery documentation — https://cloud.google.com/bigquery/docs
