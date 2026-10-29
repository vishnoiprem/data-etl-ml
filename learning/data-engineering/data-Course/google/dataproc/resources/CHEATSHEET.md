# Dataproc + PySpark Cheat Sheet

> One page per topic. Keep it open in a tab.

---

## `gcloud dataproc clusters` — lifecycle

```bash
# Create
gcloud dataproc clusters create CLUSTER \
  --region=us-central1 \
  --image-version=2.2-debian12 \
  --master-machine-type=n2-standard-4 \
  --worker-machine-type=n2-standard-4 \
  --num-workers=2 \
  --num-secondary-workers=1 \
  --secondary-worker-type=spot \
  --service-account=SA@PROJECT.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --delete-max-idle=30m \
  --delete-max-age=8h \
  --labels=env=dev,course=dataproc

# List
gcloud dataproc clusters list --region=us-central1
gcloud dataproc clusters list --region=us-central1 \
  --format="table(name,status,config.workerConfig.numInstances,status.state)"

# Describe
gcloud dataproc clusters describe CLUSTER --region=us-central1
gcloud dataproc clusters describe CLUSTER --region=us-central1 \
  --format="value(config.clusterConfig.clusterUuid)"

# Update (labels, autoscaling policy, metadata)
gcloud dataproc clusters update CLUSTER --region=us-central1 \
  --labels=env=prod
gcloud dataproc clusters update CLUSTER --region=us-central1 \
  --autoscaling-policy=my-policy

# Start / stop (stop preserves disks; you still pay for them)
gcloud dataproc clusters start CLUSTER --region=us-central1
gcloud dataproc clusters stop CLUSTER --region=us-central1

# Delete  ← the command you must always remember
gcloud dataproc clusters delete CLUSTER --region=us-central1
```

⚠️ **The `--` separator.** Everything after `--` goes to your driver program,
not to gcloud.

---

## `gcloud dataproc jobs submit`

```bash
# PySpark
gcloud dataproc jobs submit pyspark main.py \
  --cluster=CLUSTER \
  --region=us-central1 \
  -- main.py --arg1 value1 --arg2 value2

# Spark (Java/Scala) — needs --class or --jar
gcloud dataproc jobs submit spark \
  --class=com.example.Main \
  --jars=gs://bucket/lib.jar \
  --cluster=CLUSTER --region=us-central1

# Spark SQL
gcloud dataproc jobs submit spark-sql query.sql \
  --cluster=CLUSTER --region=us-central1

# Hadoop / Hive / Pig / Presto
gcloud dataproc jobs submit hadoop --jar=gs://b/x.jar --cluster=C
gcloud dataproc jobs submit hive --file=q.hql --cluster=C
gcloud dataproc jobs submit pig --file=q.pig --cluster=C
gcloud dataproc jobs submit presto --file=q.sql --cluster=C

# The four ways to ship code and dependencies
--jars=gs://b/lib.jar          # Java/Scala libs → classpath
--py-files=helpers.py          # Python modules → sys.path
--files=config.json            # Any file → working directory
--archives=bundle.zip          # Extracted into working directory

# Spark config for THIS job only
--properties="spark.executor.memory=8g,spark.sql.shuffle.partitions=400"
--properties-file=spark.properties

# Labels on the job (cost attribution, filtering)
--labels=run_date=2026-10-27,pipeline=retail
```

⚠️ **`gcloud dataproc jobs submit`, not `gcloud dataproc clusters submit`.** The
older form appears in most tutorials and Stack Overflow answers. It was
superseded.

---

## `gcloud dataproc jobs` — observing

```bash
# List
gcloud dataproc jobs list --region=us-central1 --limit=20
gcloud dataproc jobs list --region=us-central1 --cluster=CLUSTER
gcloud dataproc jobs list --region=us-central1 --state-filter=active
gcloud dataproc jobs list --region=us-central1 --state-filter=inactive

# Describe
gcloud dataproc jobs describe JOB_ID --region=us-central1
gcloud dataproc jobs describe JOB_ID --region=us-central1 \
  --format="value(status.state)"          # DONE / ERROR / CANCELLED / RUNNING
gcloud dataproc jobs describe JOB_ID --region=us-central1 \
  --format="value(driverOutputUri)"

# Wait (blocks; prints driver output)
gcloud dataproc jobs wait JOB_ID --region=us-central1

# Kill a stuck job
gcloud dataproc jobs kill JOB_ID --region=us-central1
```

⚠️ **Job states are `DONE` and `ERROR` — not `SUCCEEDED` and `FAILED`.** The
console shows "Succeeded"/"Failed"; the API shows `DONE`/`ERROR`. Automation
that checks for `SUCCEEDED` never matches.

⚠️ **`--state-filter` accepts only `ACTIVE` and `INACTIVE`.** You cannot filter
for `ERROR` directly.

---

## `gcloud dataproc workflow submit`

```bash
# Submit a workflow whose YAML lives in GCS
gcloud dataproc workflow submit \
  --workflows.gcs_uri=gs://bucket/workflows/retail.yaml \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID

# With parameter overrides
gcloud dataproc workflow submit \
  --workflows.gcs_uri=gs://bucket/workflows/retail.yaml \
  --region=us-central1 \
  --workflows.template_id=retail \
  --workflows.parameters=run_date=2026-10-27,mode=full

# Instances (a workflow's DAG of jobs)
gcloud dataproc workflow instances list --region=us-central1
gcloud dataproc workflow instances describe INSTANCE_ID --region=us-central1
```

⚠️ **Workflows require the Dataproc Workflows API and the `composer` API to be
enabled.** The YAML must live in GCS, not locally.

A minimal workflow YAML:

```yaml
jobs:
- jobId: extract-sales
  sparkSql:
    queryFileUri: gs://bucket/sql/extract.sql
    queryFileMode: gs://bucket/sql/extract.sql
    labels:
      env: dev
- jobId: build-mart
  sparkSql:
    queryFileUri: gs://bucket/sql/mart.sql
    queryFileMode: gs://bucket/sql/mart.sql
  dependencies:
  - extract-sales
```

---

## IAM — the real roles

| Role | Grants | Give to |
|------|--------|---------|
| `roles/dataproc.admin` | Full Dataproc control | Platform admins |
| `roles/dataproc.editor` | Manage clusters, jobs, operations | Engineers, the pipeline SA |
| `roles/dataproc.viewer` | Read-only | Analysts |
| `roles/dataproc.worker` | Data-plane access | **The cluster's VM SA** |
| `roles/dataproc.serverlessEditor` | Serverless batches and sessions | Serverless users |
| `roles/dataproc.serverlessViewer` | Read-only serverless | Observability |
| `roles/storage.objectAdmin` | Full bucket object control | The pipeline SA |
| `roles/storage.objectViewer` | Read bucket objects | The pipeline SA (raw bucket) |
| `roles/bigquery.jobUser` | Run BigQuery jobs | The pipeline SA |
| `roles/bigquery.dataEditor` | Read + write table data | The pipeline SA |
| `roles/bigquery.dataViewer` | Read table data | Analysts |
| `roles/iam.serviceAccountUser` | Act as a service account | Cluster creators |

⚠️ **`roles/dataproc.developer` does not exist.** Neither does
`roles/dataproc.clusterUser`.

```bash
# Grant
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SA@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/dataproc.worker"

# Bucket-scoped
gcloud storage buckets add-iam-policy-binding gs://BUCKET \
  --member="serviceAccount:SA@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Act as
gcloud iam service-accounts add-iam-policy-binding SA@PROJECT_ID.iam.gserviceaccount.com \
  --member="user:you@example.com" \
  --role="roles/iam.serviceAccountUser"

# Inspect
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:SA@PROJECT_ID.iam.gserviceaccount.com" \
  --format="value(bindings.role)"
```

---

## PySpark API — the essentials

```python
from pyspark.sql import SparkSession, functions as F, types as T

spark = SparkSession.builder.appName("job").getOrCreate()

# READ
df = spark.read.parquet("gs://bucket/path")
df = spark.read.csv("gs://bucket/path/*.csv", header=True, inferSchema=True)
df = spark.read.json("gs://bucket/path/*.json")
df = spark.read.format("delta").load("gs://bucket/path")
df = spark.read.jdbc(url, table, props)          # JDBC
df = spark.read.table("project.dataset.table")   # BigQuery / Hive metastore
df = spark.read.csv("s3://bucket/path")           # S3a
df = spark.read.text("gs://bucket/path")

# SELECT / FILTER
df.select("a", "b", F.col("c").cast("double"))
df.select(F.when(F.col("x") > 10, "big").otherwise("small").alias("bucket"))
df.filter(F.col("status") == "COMPLETED")
df.filter(F.col("ts").between("2026-01-01", "2026-02-01"))
df.filter(F.expr("a IS NOT NULL AND b > 0"))
df.withColumn("net", F.col("gross") - F.col("discount"))
df.dropDuplicates(["order_id"])
df.dropna(subset=["order_id", "amount"])

# JOIN
df.join(other, on="id", how="inner")
df.join(other, on=["store_id", "date"], how="left")
df.join(F.broadcast(small_df), "id")             # force a broadcast hash join
df.join(other, df.id == other.other_id, "left")  # non-equi condition
df.crossJoin(other)                              # Cartesian — expensive

# GROUP BY / AGGREGATE
df.groupBy("store_id").count()
df.groupBy("store_id").agg(
    F.sum("amount").alias("revenue"),
    F.avg("amount").alias("avg_amount"),
    F.countDistinct("order_id").alias("orders"),
    F.min("ts"), F.max("ts"),
    F.collect_set("category").alias("categories"),
)
df.groupBy("store_id", F.to_date("ts").alias("d")).sum("amount")
df.cube("a", "b")   # multi-dimensional rollup
df.rollup("a", "b")

# WINDOW
df.withColumn("rn", F.row_number().over(F.Window.partitionBy("id").orderBy(F.desc("ts"))))
df.withColumn("rank", F.rank().over(F.Window.partitionBy("cat").orderBy(F.desc("amt"))))
df.withColumn("prev", F.lag("amt", 1).over(F.Window.partitionBy("id").orderBy("ts")))
df.withColumn("ma", F.avg("amt").over(F.Window.partitionBy("id").orderBy("ts").rowsBetween(6, 0)))
df.withColumn("z", (F.col("x") - F.avg("x").over(w)) / F.stddev_pop("x").over(w))

# QUALIFY — dedup to latest (Spark 3.4+)
df.withColumn("rn", F.row_number().over(F.Window.partitionBy("id").orderBy(F.desc("ts")))) \
  .filter(F.col("rn") == 1)

# WRITE
df.write.mode("overwrite").parquet("gs://bucket/out")
df.write.mode("overwrite").option("partitionOverwriteMode", "DYNAMIC").parquet("gs://bucket/out")
df.write.mode("append").format("parquet").save("gs://bucket/out")
df.write.mode("overwrite").partitionBy("date").json("gs://bucket/out")
df.write.mode("overwrite").format("parquet").option("compression", "snappy").save("gs://bucket/out")

# BigQuery
df.write.format("bigquery").option("temporaryGcsBucket", "bucket").option("writeDisposition", "WRITE_APPEND").save("project.dataset.table")

# Other sinks
df.write.format("delta").mode("overwrite").save("gs://bucket/out")
df.write.format("iceberg").mode("overwrite").save("gs://bucket/out")
df.write.format("console").show(20, truncate=False)

# UTILITIES
df.printSchema()
df.show(5)
df.describe().show()
df.count()                       # ACTION — triggers a job
df.columns
df.dtypes
df.schema
df.rdd.getNumPartitions()
df.explain(True)
df.rdd.map(lambda r: r).collect()   # ACTION
df.toPandas()                      # ACTION — pulls to the driver
df.cache(); df.unpersist()
df.persist()
df.coalesce(1).write.mode("overwrite").parquet("gs://b/out")   # one file
df.repartition(10).write.mode("overwrite").parquet("gs://b/out")
df.repartition("date").write.mode("overwrite").parquet("gs://b/out")
```

---

## Spark configuration — defaults and when to tune

| Property | Default | Tune when |
|----------|---------|-----------|
| `spark.executor.instances` | **1** (!) | Always set it, or your 50-node cluster runs as one executor |
| `spark.executor.memory` | 1g | Wide aggregations, big shuffles, `collect()`-heavy work |
| `spark.executor.cores` | 1 | 4–5 is the sweet spot; more means worse GC pressure |
| `spark.driver.memory` | 1g | The driver runs on the master; raise it if you `collect()` |
| `spark.sql.shuffle.partitions` | 200 | Too few for big data, too many for small data. AQE usually fixes it |
| `spark.sql.adaptive.enabled` | `true` (3.2+) | Leave it on — it coalesces shuffle partitions at runtime |
| `spark.sql.adaptive.skewJoin.enabled` | `true` | Leave it on; it handles skewed joins |
| `spark.sql.adaptive.coalescePartitions.enabled` | `true` | Leave it on |
| `spark.dynamicAllocation.enabled` | `false` | Enable when the workload varies; **requires** `spark.executor.instances` unset |
| `spark.dynamicAllocation.minExecutors` | `spark.dynamicAllocation.initialExecutors` | Set with the above |
| `spark.dynamicAllocation.maxExecutors` | `infinity` | **Always set this** — infinity + a bug = unbounded cost |
| `spark.dynamicAllocation.executorIdleTimeout` | 60s | Fine as-is |
| `spark.serializer` | Java serialization | Use `KryoSerializer` — faster and smaller payloads |
| `spark.sql.autoBroadcastJoinThreshold` | 10 MB | Raise it to broadcast a dimension table of a few thousand rows |
| `spark.sql.files.maxPartitionBytes` | 128 MB | Lower it for small files; raise for huge ones |
| `spark.sql.parquet.compression.codec` | `snappy` | `zstd` for better ratio, `gzip` for compatibility |
| `spark.sql.shuffle.partitions` after AQE | varies | AQE merges small partitions — the static value matters less |
| `spark.sql.broadcastTimeout` | 300s | Raise it if a broadcast is timing out |
| `spark.task.maxFailures` | 4 | Raise it on Spot-heavy clusters to survive preemption churn |
| `spark.speculation` | `false` | Enable only for straggler-prone jobs; it costs double compute |
| `spark.sql.adaptive.localShuffleReader.enabled` | `true` | Leave it on |
| `spark.sql.execution.arrow.pyspark.enabled` | `false` | Enable for fast Pandas UDFs and `toPandas()` |
| `spark.sql.execution.arrow.maxRecordsPerBatch` | 10000 | Tune for wide rows |
| `spark.sql.adaptive.forceOptimizeSkewedJoin` | `false` | Enable for a known-skewed workload |
| `spark.default.parallelism` | total cores | Roughly matches the default executor count |
| `spark.sql.parquet.outputTimestampType` | `INT64` | Use `INT96` for Hive compatibility |
| `spark.sql.session.timeZone` | JVM default | **Set it explicitly** — a timezone difference corrupts every date |

💡 **The rule:** do not tune a config before you have read `explain()` and seen
where the time goes. AQE handles most of the shuffle-partition question on its
own.

---

## Reading `explain()`

```python
df.explain(True)     # the full physical plan, parsed
df.explain(mode="formatted")   # Spark 3.4+: the formatted plan
```

```
== Physical Plan ==
*(3) HashAggregate (keys: (store_id#10), functions: partial_sum(...))
+- Exchange hashpartitioning(store_id#10, 200), ENSURE_REQUIREMENTS, [plan_id=42]
   +- *(2) HashAggregate (keys: (store_id#10), functions: sum(...))
      +- *(1) Filter (isnotnull(store_id#10) AND (status#5 = COMPLETED))
         +- FileScan csv [order_id#0,store_id#10,...] Batched: true, ...
```

| What you see | What it means | What to do |
|--------------|----------------|------------|
| `Exchange hashpartitioning(..., 200)` | A shuffle happened. 200 is the default partition count | Usually fine with AQE. If there are many tiny partitions, `coalesce` or let AQE do it |
| `Exchange hashpartitioning(..., 200)` **before** a big join | A sort-merge join | If one side is small, `F.broadcast()` it |
| `Sort` / `SortMergeJoin` | A sort-merge join — expensive | Broadcast the small side |
| `BroadcastHashJoin` | The small side was broadcast | Good — but confirm the side is actually small |
| `FileScan` with `PartitionFilters` and no `PushedFilters` | The partition column was not pruned | Filter on the partition column directly, not on a function of it |
| `Filter` above `FileScan` | A row-level filter (not partition pruning) | Still helps; partition pruning is better |
| `InMemoryTableScan` | The data was cached | Fine — that was the point of the cache |
| `Scan ExistingRDD` | You converted to an RDD | Often a sign of falling back to the RDD API unnecessarily |
| `Exchange SinglePartition` | Everything is going to ONE partition | This is your bottleneck. It happens with `coalesce(1)` or a global sort |
| Very skewed task times in the UI | One partition holds most of the data | AQE skew join, or salt the key |
| `Generate explode` | An array was exploded | Expected — but check the output row count |

---

## BigQuery connector — options

| Option | Meaning | Default | Notes |
|--------|---------|---------|-------|
| `temporaryGcsBucket` | Bucket for the LOAD job's staging files | none | **Required** for `WRITE_APPEND` / `WRITE_TRUNCATE` |
| `writeDisposition` | `WRITE_APPEND`, `WRITE_TRUNCATE`, `WRITE_EMPTY` | `WRITE_APPEND` | `WRITE_TRUNCATE` is **not** idempotent on re-run — use `WRITE_APPEND` with a `DELETE` first |
| `createDisposition` | `CREATE_IF_NEEDED`, `CREATE_NEVER` | `CREATE_IF_NEEDED` | |
| `partitionField` | The partition column | none | **Required** for `WRITE_TRUNCATE` to truncate only one partition |
| `partitionExpirationMs` | Expire partitions after N ms | none | Set it to match your retention policy |
| `partitionType` | `DAY`, `HOUR`, `MONTH`, `YEAR` | `DAY` | |
| `partitionRangeMillis` | A custom range partition | none | |
| `catalog` | `hive`, `spark`, `bigquery` | `hive` | Use `bigquery` for managed BigQuery tables |
| `sourceFormat` | The source format | inferred | `parquet` is fastest |
| `allowJitteredPartitions` | Spread writes across random partitions | `true` | Leave on for appends; it avoids hot partitions |
| `enableModeCheckForSchemaFields` | Reject rows with unexpected fields | `true` | Set `false` to allow schema drift |
| `enableModeCheckForPartitionFields` | Reject rows with unexpected partition fields | `true` | |
| `ignoreUnknownValues` | Skip unknown fields | `false` | |
| `useAvroLogicalTypes` | Honour Avro logical types | `true` | |
| `credentials` | Explicit credentials | ADC | |
| `materializationProject` | Project for temp tables | the target project | |
| `view` | Write to a view instead of a table | none | |
| `confidence` | Privacy threshold for the optional Smart Pricing API | none | Unrelated to cost — it only reports PII likelihood |

```python
(df.write
  .format("bigquery")
  .option("writeDisposition", "WRITE_APPEND")
  .option("temporaryGcsBucket", "my-bq-staging")
  .option("partitionField", "sales_date")
  .option("partitionType", "DAY")
  .option("createDisposition", "CREATE_IF_NEEDED")
  .save("my-project.gold.fact_sales"))
```

⚠️ **`WRITE_TRUNCATE` deletes and recreates the whole table** unless you set
`partitionField`. With `partitionField` set, it truncates only that partition —
which is what makes a partition-scoped re-run idempotent.

---

## Cost-saving checklist

**Before you create a cluster**

- [ ] `--delete-max-idle=30m` is set
- [ ] `--delete-max-age=8h` is set
- [ ] `--image-version=2.2-debian12` is pinned
- [ ] `--scopes=https://www.googleapis.com/auth/cloud-platform` is set
- [ ] `--labels=env=...,owner=...` are set (cost attribution)

**While it runs**

- [ ] `--num-secondary-workers` with `--secondary-worker-type=spot` for burst capacity
- [ ] `--num-workers=2` is enough for most course exercises
- [ ] `spark.executor.instances` is set (or dynamic allocation is enabled with a **finite** `maxExecutors`)
- [ ] `spark.sql.adaptive.enabled=true`
- [ ] The driver does not `collect()` a large result
- [ ] The driver does not `cache()` without a matching `unpersist()`

**After it runs**

- [ ] `gcloud dataproc clusters delete CLUSTER --region=us-central1`
- [ ] `gcloud dataproc clusters list` shows no orphans
- [ ] The budget alert is set
- [ ] The BigQuery staging bucket has a lifecycle rule

**BigQuery**

- [ ] Every query filters on the partition column
- [ ] `require_partition_filter = TRUE` where appropriate
- [ ] `maximum_bytes_billed` on every job
- [ ] `CREATE OR REPLACE` for dev; `MERGE` for production
- [ ] The staging bucket's lifecycle rule deletes the temp files

**The BigQuery connector vs the Storage Write API**

| | Connector (default) | Storage Write API |
|---|---|---|
| Mechanism | Write Parquet to GCS, then a LOAD job | Direct streaming inserts via a gRPC stream |
| Throughput | Excellent for batch | Excellent for streaming |
| Cost | Storage for the temp files (transient) | $0.01/GiB after the free tier |
| Idempotency | Easy — partition-scoped `WRITE_APPEND` | Hard — you must deduplicate yourself |
| Best for | Batch ETL from Spark | High-rate streaming |

💡 **For this course's batch jobs, use the connector.** The Storage Write API is
for streaming, and its exactly-once story is harder than the connector's.

---

## Common errors

| Error | Fix |
|-------|-----|
| `unrecognized arguments: main.py` | You forgot the `--` separator |
| `PERMISSION_DENIED: ... service account` | Grant `roles/iam.serviceAccountUser` on the cluster SA |
| `Access Denied: ... does not have permission to run a job` | Grant `roles/bigquery.jobUser` |
| `403 ... storage.googleapis.com` on the cluster | Add `--scopes=https://www.googleapis.com/auth/cloud-platform` |
| `JobStatus.state == SUCCEEDED` never matches | The API state is `DONE` |
| `java.lang.OutOfMemoryError: Java heap space` | Raise `spark.executor.memory`; or the driver is collecting too much |
| `SparkException: Task not found` on Spot workers | Preemption churn — raise `spark.task.maxFailures` |
| `AnalysisException: Table or view not found` | Wrong region or missing dataset — check `bq ls` |
| `BigQueryException: Cannot write to a table with no partition` | Set `partitionField` |
| `Job failed: ... exit code 1` | Read the driver output — `gcloud dataproc jobs wait JOB_ID` |
| `Could not find a usable Spark Connect` | Version mismatch between client and cluster |
| `Kryo serialization failed` | A class is not registered; use `registratorFor` |
| `Total size of serialized results ... is bigger than spark.driver.maxResultSize` | Raise it, or better, stop collecting |
