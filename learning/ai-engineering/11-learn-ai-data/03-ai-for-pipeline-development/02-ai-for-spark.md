# Lesson 2 — AI for Spark

> **Type:** Article · Module 3 · AI for Pipeline Development
> Generating PySpark code that's correct on your cluster, your data, and your AQE settings.

---

## Why Spark is its own lesson

Spark looks like Python but its failure modes are different:
- **Cluster config matters.** Executor memory, shuffle partitions, AQE — all change behaviour.
- **Lazy evaluation + actions.** A `collect()` on a 100 B-row DataFrame kills the driver.
- **Shuffle, skew, broadcast.** Specific vocabulary AI doesn't internalise from generic Python.
- **Determinism.** Same code, different cluster, different result.

AI can write Spark. AI can write **broken Spark**. The difference is the context you give it.

---

## The Spark context block

```text
CONTEXT — Spark
- PySpark 3.5 on Databricks Runtime 14.x
- Cluster: 4 workers, 16 cores, 64 GB RAM, 1 driver 16 GB
- AQE enabled (spark.sql.adaptive.enabled=true)
- Shuffle partitions default: 200
- Broadcast threshold: 100 MB
- Iceberg tables on S3, hidden partitioning by ingest_date
- Session config in spark_session.get_session()
```

Without this, AI guesses. Default guesses break production.

---

## The Spark session pin

```python
# spark_session.py — canonical, in repo, referenced in CLAUDE.md
from pyspark.sql import SparkSession

def get_session(app_name: str) -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.shuffle.partitions", "200")
        .config("spark.sql.autoBroadcastJoinThreshold", "104857600")  # 100 MB
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.adaptive.skewJoin.enabled", "true")
        .getOrCreate()
    )
```

Every job uses this. AI references it. Your cluster stays consistent.

---

## The Spark prompt template

```text
ROLE: senior Spark/Databricks engineer.

CONTEXT — SPARK:
{Paste the Spark context block from above}

TASK — SPARK:
Write a PySpark job that:
1. reads raw.stripe.payments (Iceberg, partitioned by ingest_date)
2. filters to ingest_date = {{ ds }}
3. drops rows with NULL payment_id
4. casts amount from cents (int) to USD (decimal(18,2))
5. joins to dim_user on user_id (LEFT, dim.user is small enough to broadcast)
6. writes to marts.fct_payments_daily, partitioned by payment_date

CONSTRAINTS:
- Use the session from spark_session.get_session()
- Do NOT use .collect() — use .count() and .take(5) only
- Specify the broadcast hint explicitly: F.broadcast(dim_user)
- Specify shuffle partitions: df.repartition(200, "user_id")
- Do NOT use Python UDFs — use Spark built-ins only
- Use Iceberg's merge into for idempotency

FORMAT:
1. Job script in a ```python block
2. The 4 unit-test stubs (pytest) covering: null PK, empty result, broadcast skew, idempotent re-run

VERIFICATION:
- row count vs raw layer
- null check on payment_id
- broadcast exchange visible in EXPLAIN
- second run = no new rows
```

---

## The silent Spark bugs to always check

### 1. Driver OOM from `.collect()`
**Symptom:** Driver crashes mid-job.
**Fix:** Never `.collect()`. Use `.count()`, `.take(5)`, write to warehouse.

### 2. Shuffle skew
**Symptom:** Stage runs 100× longer than others; one task takes all the time.
**Cause:** One key dominates a partition (e.g. `user_id = 0` is 30% of rows).
**Fix:**
```python
# salting
df = df.withColumn("salt", (F.rand() * 100).cast("int"))
df_skewed = df_skewed.withColumnRenamed("user_id", "skew_key")
df_skewed = df_skewed.withColumn("skew_key", F.concat(F.col("user_id"), F.lit("_"), F.col("salt")))
```

### 3. Cartesian product
**Symptom:** Row count balloons, stages explode.
**Cause:** Missing join condition.
**Fix:** Always specify join condition. Use `how=` explicitly.

### 4. Small files
**Symptom:** 10,000 files of 1 MB each.
**Cause:** Streaming writes without coalescing.
**Fix:**
```python
df.coalesce(1).write.parquet("...")
# or for batch: df.repartition(numPartitions, "key")
```

### 5. Python UDFs blocking Catalyst
**Symptom:** Job 100× slower than expected.
**Fix:** Pandas UDFs at worst, native Spark functions preferred.

### 6. Broadcast hint missing
**Symptom:** Shuffle on a join that should be broadcast.
**Fix:** `F.broadcast(small_df)` explicitly.

---

## The "explain the Spark plan" prompt

```text
ROLE: senior Spark tuner.

TASK: from the DAG / physical plan below:
1. identify any shuffle joins that should be broadcast
2. identify skewed stages (look at max(task_duration) >> median)
3. identify partitions with >1000 rows per task (likely skew)
4. name the specific code change to fix each
5. estimate the impact (10x faster? 2x? unknown?)
```

AI is decent at this. You verify with the actual Spark UI.

---

## Iceberg-specific patterns

Iceberg has hidden partitioning, snapshot isolation, and time-travel. AI defaults to Delta-like behaviour unless you tell it.

```python
# Iceberg MERGE (idempotent upsert)
from pyspark.sql.functions import current_timestamp

(
    target_delta.alias("t")
    .merge(
        source.alias("s"),
        "t.payment_id = s.payment_id AND t.ingest_date = s.ingest_date"
    )
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)
```

AI writes this correctly if you tell it the table is Iceberg and the primary key is `(payment_id, ingest_date)`.

---

## What AI cannot generate for Spark

- **Cluster sizing decisions.** AI doesn't know workload shape.
- **Cost-aware configuration.** You pick the cluster; AI optimises within it.
- **Streaming fault-tolerance.** Exactly-once, watermarking, late-arrival handling — specify explicitly.
- **Cross-environment parity.** Dev cluster ≠ prod cluster ≠ staging. Test in all three.

---

## The Spark deliverable

```python
# payments_daily.py — three sections, never bundled into one block

def extract(spark, ingest_date):
    """Read raw layer, filter to ingest_date."""
    return (
        spark.read.format("iceberg")
        .table("raw.stripe.payments")
        .filter(F.col("ingest_date") == ingest_date)
    )

def transform(df):
    """Drop nulls, cast, join to dim_user with broadcast."""
    df_clean = df.filter(F.col("payment_id").isNotNull())
    df_cast = df_clean.withColumn(
        "amount_usd", (F.col("amount_cents") / 100).cast("decimal(18,2)")
    )
    dim_user = spark.read.format("iceberg").table("marts.dim_user")
    return df_cast.join(F.broadcast(dim_user), "user_id", "left")

def load(df, ingest_date):
    """MERGE into marts.fct_payments_daily."""
    df_with_date = df.withColumn("payment_date", F.col("created_at").cast("date"))
    df_with_date.write.format("iceberg").mode("append").saveAsTable(
        "marts.fct_payments_daily"
    )
```

Each function has a single responsibility. Each is testable in isolation. AI writes each at 90% quality. You compose them.

---

## What Comes Next

> Lesson 3 — **AI for dbt** — generating dbt models that respect your layer conventions, your materialization strategy, and your test coverage.
