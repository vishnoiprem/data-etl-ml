# Advanced PySpark — CTO / Principal Study Plan

**Source course:** Data Vidhya — *Advanced PySpark* by Darshil Parmar.
**Course URL:** https://datavidhya.com/learn/ (PySpark advanced course)
**Coverage:** 2 modules • 19 lessons
**Audience:** Data engineers targeting **Staff → Principal → Director →
VP/CTO** track with deep PySpark expertise — RDDs, low-level APIs,
structured streaming, and the 11 interview patterns that show up in
every DE technical interview.

> **How to use this file.** Each lesson has four lenses:
>
> 1. **Theory** — mental model and the PySpark primitive.
> 2. **Practical Example** — concrete code, configs, decisions.
> 3. **AI Use Case** — where GenAI / ML slots in or on top of this lesson.
> 4. **CTO / Principal Motivation** — career reason; what decisions
>    you're trusted with at senior levels.
>
> This is the **interview-prep companion** to the PySpark track.
> Module 1 covers the **advanced APIs** that distinguish Senior from
> Staff PySpark engineers (UDFs, Pandas UDFs, RDDs, broadcast
> variables, structured streaming). Module 2 covers the **11
> interview patterns** that show up in 80% of DE PySpark interviews —
> flatten nested JSON, dedup, SCD2, sessionization, DQ framework,
> optimize the spark job, streaming pipeline, custom partitioner,
> idempotent upsert, error handling, and quiz.
>
> The Principal-level PySpark engineer can whiteboard any of these 11
> patterns in 5 minutes and implement them in 30. They know when to
> reach for a UDF vs a built-in function, when RDDs beat DataFrames,
> and how to tune a 1 TB Spark job from 4 hours to 30 minutes.

---

# Module 1 · Advanced APIs & Streaming (8 lessons)

## Lesson 1 — User Defined Functions (UDFs) (Video)

### Theory

UDFs extend Spark SQL with **custom Python/Scala/JVM logic**.
Mental model:

- **Python UDF** — `pyspark.sql.functions.udf(lambda x: ...)`. Row at
  a time, serializes between JVM and Python (slow).
- **Pandas UDF (vectorized)** — `pandas_udf` decorator. Operates on
  Apache Arrow batches (10-100× faster than row-at-a-time UDFs).
- **Scalar vs grouped vs window** Pandas UDFs — different signatures,
  different performance.
- **Registration** — as DataFrame function or SQL function.

### Practical Example

A scalar UDF vs a Pandas UDF on the same data:

```python
from pyspark.sql.functions import udf, pandas_udf, PandasUDFType
from pyspark.sql.types import StringType
import pandas as pd

# Row-at-a-time UDF — slow
@udf(returnType=StringType())
def mask_email_slow(email: str) -> str:
    if email is None: return None
    local, _, domain = email.partition("@")
    return f"{local[0]}***@{domain}"

# Pandas UDF — fast (vectorized via Arrow)
@pandas_udf(StringType())
def mask_email_fast(emails: pd.Series) -> pd.Series:
    return emails.fillna("").apply(lambda e: e[0] + "***@" + e.split("@")[1])

# Both registered as SQL functions
spark.udf.register("mask_email_slow", mask_email_slow)
spark.udf.register("mask_email_fast", mask_email_fast)
```

On a 100M-row DataFrame: row UDF = ~10 minutes, Pandas UDF = ~30
seconds. **20× speedup.**

### AI Use Case

**AI-generated UDFs.** "Write a Pandas UDF to detect fraud in
transactions" → AI generates the UDF with type hints, vectorized
batch processing, and a unit test. The Principal's edge: 5× faster
UDF authoring.

### CTO / Principal Motivation

UDF discipline is **the difference between a working Spark job and
a fast one**. The Principal's standard: "every UDF in our codebase
is a Pandas UDF unless there's a reason otherwise; every UDF has a
unit test." CTOs see this as **compute cost reduction** — UDF
optimization often yields 10× cost savings.

---

## Lesson 2 — UDFs & Pandas UDFs (Article)

### Theory

The five Pandas UDF types in detail. Mental model:

| Type | Signature | Use case |
|------|-----------|----------|
| **Scalar** | `(pd.Series) -> pd.Series` | Vectorized row transform |
| **Grouped aggregate** | `(pd.DataFrame) -> scalar` | Custom aggregation |
| **Grouped map** | `(pd.DataFrame) -> pd.DataFrame` | Group-level transforms (split-apply-combine) |
| **Map iterator** | `(Iterator[pd.DataFrame]) -> Iterator[pd.DataFrame]` | Stateful streams |
| **Grouped agg (multiple)** | `(Tuple[pd.Series]) -> Tuple[scalar]` | Multi-column group agg |

### Practical Example

A grouped-map Pandas UDF for per-user normalization:

```python
@pandas_udf("user_id string, score double", PandasUDFType.GROUPED_MAP)
def normalize_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Z-score normalize per user."""
    df["score"] = (df["score"] - df["score"].mean()) / df["score"].std()
    return df

normalized = (df.groupBy("user_id")
              .apply(normalize_scores))
```

Use case: sessionization, per-user anomaly detection, ranking within
groups.

### AI Use Case

**AI-optimized Pandas UDF.** AI converts row UDFs to Pandas UDFs,
groups, type-checks. The Principal's edge: 10× speedup from
automated refactor.

### CTO / Principal Motivation

The "convert row UDFs to Pandas UDFs" initiative is **the highest-ROI
Spark refactor**. Every Principal has done it; every CTO sees the
compute bill drop. Standard deliverable: a CI rule that flags new
row UDFs.

---

## Lesson 3 — Lower Level APIs Overview (Video)

### Theory

Spark's three API layers. Mental model:

- **DataFrame API** (high-level) — declarative, optimized by Catalyst,
  default for most work.
- **Dataset API** (typed, JVM only) — strongly-typed DataFrame, JVM
  type safety.
- **RDD API** (low-level) — distributed collection, no Catalyst
  optimization, manual control.

The decision tree:

1. Can I express this with DataFrame operations? → Use DataFrame.
2. Do I need per-element complex logic that DataFrames don't support?
   → Pandas UDF.
3. Do I need fine-grained control over partitioning, ordering, or
   state? → RDD.

### Practical Example

A DataFrame vs RDD comparison on a count:

```python
# DataFrame (Catalyst-optimized)
df.groupBy("user_id").count().show()

# RDD (no optimization, you manage everything)
rdd.map(lambda row: (row.user_id, 1)) \
   .reduceByKey(lambda a, b: a + b) \
   .collect()
```

The DataFrame version is faster and more readable. Only reach for
RDD when the DataFrame API doesn't support what you need.

### AI Use Case

**AI-driven DataFrame vs RDD advisor.** AI scans code, recommends
DataFrame refactor when possible. The Principal's edge: 2-5×
faster jobs from automated refactor.

### CTO / Principal Motivation

RDD code is **technical debt**. It bypasses Catalyst and Tungsten,
so optimizations don't apply. The Principal's standard: "no new
RDD code; existing RDD code is on the refactor roadmap."

---

## Lesson 4 — Resilient Distributed Datasets (RDDs) (Video)

### Theory

RDDs in depth. Mental model:

- **RDD** — immutable, distributed collection of objects.
- **Partitions** — units of parallelism (one per `parallelize` slice
  or per block of input file).
- **Lineage** — DAG of transformations that produced the RDD.
- **Transformations** — lazy (`map`, `filter`, `groupByKey`,
  `reduceByKey`, `join`).
- **Actions** — eager (`count`, `collect`, `saveAsTextFile`).
- **Narrow vs wide dependencies** — narrow = no shuffle; wide = shuffle.
- **Persistence** — `persist(StorageLevel.MEMORY_AND_DISK)` to avoid
  recomputation.

### Practical Example

A word count with RDDs (the classic example):

```python
rdd = sc.textFile("s3://bucket/text/")
words = (rdd.flatMap(lambda line: line.split())
            .map(lambda word: (word, 1))
            .reduceByKey(lambda a, b: a + b))
words.saveAsTextFile("s3://bucket/output/")
```

Wide dependency: `reduceByKey` triggers a shuffle. Mitigation: use
`reduceByKey` instead of `groupByKey` (pre-aggregates locally).

### AI Use Case

**AI-driven RDD refactor.** AI converts RDD pipelines to DataFrames,
preserving semantics. The Principal's edge: faster, more reliable
code.

### CTO / Principal Motivation

RDD knowledge is **the on-call differentiator**. When a Shuffle
spills to disk or an OOM happens, RDD knowledge tells you why.
Principals who understand RDDs debug incidents in minutes that
others debug in hours.

---

## Lesson 5 — Broadcast Variables & Accumulators (Video)

### Theory

Shared variables in Spark. Mental model:

- **Broadcast variable** — read-only variable sent to all executors
  once. Used for **lookup tables, small reference data**.
- **Accumulator** — write-only variable aggregated from executors to
  driver. Used for **counters, sums, custom metrics**.

The common mistake: sending a 1 GB lookup table without broadcasting
→ sent with every task (1000× duplication).

### Practical Example

A broadcast lookup join:

```python
# Without broadcast — full shuffle
enriched = df.join(lookup_df, "country_code")

# With broadcast — lookup copied to each executor once
from pyspark.sql.functions import broadcast
enriched = df.join(broadcast(lookup_df), "country_code")
```

For lookups < 100 MB, `broadcast` hint eliminates the shuffle. For
larger lookups, use a real join strategy (bucket join, sort-merge
join).

```python
# Accumulator example — error counter
errors = sc.accumulator(0)

def process(row):
    try:
        return transform(row)
    except Exception:
        errors.add(1)
        return None

rdd.map(process).collect()
print(f"Errors: {errors.value}")
```

### AI Use Case

**AI-driven broadcast advisor.** AI scans joins, recommends broadcast
where applicable. The Principal's edge: automatic query
optimization.

### CTO / Principal Motivation

Broadcast + accumulator discipline is **the small-code-big-impact
lever**. One well-placed broadcast saves a shuffle on every job.
The Principal's deliverable: a query plan review checklist.

---

## Lesson 6 — RDDs & Low-Level APIs (Article)

### Theory

The complete RDD reference. Mental model — the API surface:

- **Creation** — `sc.parallelize()`, `sc.textFile()`,
  `sparkContext.createRDD()`.
- **Transformations** — `map`, `flatMap`, `filter`, `distinct`,
  `union`, `intersection`, `subtract`, `cartesian`, `groupByKey`,
  `reduceByKey`, `aggregateByKey`, `sortByKey`, `join`, `cogroup`.
- **Actions** — `collect`, `count`, `take`, `first`, `top`,
  `reduce`, `fold`, `aggregate`, `foreach`, `saveAsTextFile`,
  `countByKey`, `countByValue`.
- **Persistence** — `persist()`, `cache()`, `unpersist()`.
- **Partitioning** — `partitionBy(numPartitions, partitionFunc)`,
  `repartition`, `coalesce`.

### Practical Example

A custom partitioner for skewed data:

```python
# Custom partitioner
def user_bucket_partition(key):
    # Send hot users to fewer partitions to avoid skew
    return hash(key) % 100 if key not in HOT_USERS else hash(key) % 10

rdd.partitionBy(100, user_bucket_partition)
```

Use case: when 1% of keys account for 50% of traffic, normal hash
partitioning creates hot partitions. Custom partitioner mitigates.

### AI Use Case

**AI-driven partitioner advisor.** AI watches Spark UI skew metrics,
recommends custom partitioner. The Principal's edge: 5-10×
faster jobs from skew elimination.

### CTO / Principal Motivation

Data skew is **the #1 cause of slow Spark jobs**. The Principal's
deliverable: a **skew detection + mitigation cookbook** (salting,
custom partitioner, broadcast join, AQE skew join). CTOs see this
as **job reliability improvement**.

---

## Lesson 7 — Structured Streaming (Article)

### Theory

Structured Streaming = Spark's stream processing API. Mental model:

- **Source** — Kafka, Kinesis, file source, socket, rate.
- **Sink** — Kafka, file sink, console, foreach, memory.
- **Trigger** — `processingTime("30 seconds")`, `once()`, `continuous`
  (experimental), `availableNow` (micro-batch).
- **Output modes** — `append` (only new rows), `update` (changed
  rows), `complete` (full result, only with aggregations).
- **Checkpoint** — durable location for state and offsets.
- **Watermark** — bound for late data (`withWatermark("ts", "10
  minutes")`).
- **Stateful operations** — aggregations, dropDuplicates, joins.

### Practical Example

A streaming pipeline with watermark + dedup:

```python
(spark.readStream
      .format("kafka")
      .option("kafka.bootstrap.servers", "broker:9092")
      .option("subscribe", "events")
      .load()
      .selectExpr("cast(value as string) as json")
      .select(from_json("json", schema).alias("e"))
      .select("e.*")
      .withWatermark("event_time", "10 minutes")
      .dropDuplicates(["event_id"])
      .writeStream
      .format("iceberg")
      .outputMode("append")
      .option("checkpointLocation", "s3://checkpoints/events/")
      .trigger(availableNow=True)
      .start("s3://lake/silver/events/")
      .awaitTermination())
```

### AI Use Case

**AI-driven streaming tuning.** AI watches streaming lag and
checkpoint size, recommends micro-batch interval, watermark,
trigger. The Principal's edge: 2× throughput from AI tuning.

### CTO / Principal Motivation

Structured Streaming is **the default Spark streaming API in
2026**. The Principal owns the **streaming standard** (Kafka +
Iceberg + checkpointing in S3); the CTO owns the **streaming
architecture** narrative.

---

## Lesson 8 — Quiz: Advanced APIs & Streaming

### Theory

Validate: UDF vs Pandas UDF, RDD vs DataFrame, broadcast +
accumulator patterns, structured streaming fluency.

### Practical Example

The 10-question drill:

1. Pandas UDF vs row UDF — speedup factor?
2. When to use RDD over DataFrame?
3. Broadcast threshold?
4. Watermark purpose?
5. Checkpoint location choice?
6. Output mode for aggregations?
7. Trigger modes?
8. Hot partition mitigation?

### AI Use Case

AI-generated flashcards + Spark job optimization drills.

### CTO / Principal Motivation

This quiz is the **prerequisite for the interview-pattern module**
that follows.

---

# Module 2 · Interview Patterns (11 lessons)

## Lesson 1 — Flatten Nested JSON

### Theory

The classic interview problem. Mental model:

- **Approach 1** — schema-on-read with `from_json` + dot notation.
- **Approach 2** — `explode` + `select` for arrays.
- **Approach 3** — recursive UDF for deeply nested JSON.

The trick: know the schema. Without it, you write a generic UDF that
fails on edge cases.

### Practical Example

Flatten this nested event:

```json
{
  "event_id": "abc",
  "user": {
    "id": "u1",
    "profile": {"country": "US", "age": 30}
  },
  "items": [
    {"sku": "A", "qty": 2},
    {"sku": "B", "qty": 1}
  ]
}
```

```python
schema = StructType([
    StructField("event_id", StringType()),
    StructField("user", StructType([
        StructField("id", StringType()),
        StructField("profile", StructType([
            StructField("country", StringType()),
            StructField("age", IntegerType())
        ]))
    ])),
    StructField("items", ArrayType(StructType([
        StructField("sku", StringType()),
        StructField("qty", IntegerType())
    ])))
])

# Flatten
df = (spark.read.json("s3://raw/")
        .select("event_id",
                col("user.id").alias("user_id"),
                col("user.profile.country"),
                col("user.profile.age"),
                explode("items").alias("item"))
        .select("event_id", "user_id", "country", "age",
                col("item.sku"), col("item.qty")))
```

### AI Use Case

**AI-generated flatten code.** "Flatten this JSON schema" → AI
generates the SchemaType + select + explode. The Principal's
edge: 5× faster schema parsing.

### CTO / Principal Motivation

Flatten JSON is the **#1 interview starter**. The candidate who
knows `explode`, `from_json`, and schema-on-read writes the answer
in 2 minutes. The one who doesn't takes 15. Principal level.

---

## Lesson 2 — Deduplication

### Theory

Two patterns:

- **Exact dedup** — `dropDuplicates(["key"])`.
- **Fuzzy dedup** — hash + window; ML-based similarity; Soundex.

For exact dedup at scale, use **partition pruning** — bucket by the
dedup key, dedup per bucket.

### Practical Example

Exact dedup:

```python
deduped = df.dropDuplicates(["event_id"])
# Window function for keep-latest
from pyspark.sql.window import Window
w = Window.partitionBy("user_id").orderBy(col("ts").desc())
deduped = (df.withColumn("rn", row_number().over(w))
             .filter(col("rn") == 1)
             .drop("rn"))
```

### AI Use Case

**AI-driven fuzzy dedup.** AI detects near-duplicates using
embedding similarity. The Principal's edge: better dedup without
exact-match rules.

### CTO / Principal Motivation

Dedup correctness is the **CTO's compliance tool**. "Show me your
dedup at the customer level." The Principal's deliverable: a
dedup pattern catalogue.

---

## Lesson 3 — SCD Type 2

### Theory

Slowly Changing Dimension Type 2 — **track full history per row**.
Mental model:

- **effective_from** — when this version became active.
- **effective_to** — when it stopped being active (NULL = current).
- **is_current** — boolean flag.
- **version** — incrementing integer.

The implementation: in the merge step, close the existing row
(set `effective_to = now()`, `is_current = false`) and insert a
new row.

### Practical Example

SCD2 merge in PySpark:

```python
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "s3://silver/dim_customer/")

(target.alias("t")
 .merge(source.alias("s"), "t.customer_id = s.customer_id AND t.is_current = true")
 .whenMatchedUpdate(
     condition="t.email <> s.email OR t.segment <> s.segment",
     set={
         "effective_to": "current_timestamp()",
         "is_current": "false"
     })
 .whenNotMatchedInsert(values={
     "customer_id": "s.customer_id",
     "email": "s.email",
     "segment": "s.segment",
     "effective_from": "current_timestamp()",
     "effective_to": "lit(None).cast('timestamp')",
     "is_current": "true"
   })
 .execute())
```

### AI Use Case

**AI-driven SCD2 generation.** AI converts a Type 1 dimension into
a Type 2 dimension with the right schema. The Principal's edge:
faster modeling.

### CTO / Principal Motivation

SCD2 is **the audit-grade dimensional pattern**. The Principal owns
the **dim table standard**; the CTO owns the **compliance**
narrative.

---

## Lesson 4 — Sessionization

### Theory

Group events into sessions by inactivity gap. Mental model:

- **Window function** — `lag()` to find previous event time.
- **Session gap** — `event_time - prev_event_time > 30 minutes`.
- **Session ID** — `sum(new_session_flag) over (order by user_id,
  event_time)`.

### Practical Example

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import lag, sum, when, lit

w = Window.partitionBy("user_id").orderBy("event_time")
with_sessions = (events
    .withColumn("prev_ts", lag("event_time").over(w))
    .withColumn("new_session", when(col("prev_ts").isNull() |
                                     (col("event_time") - col("prev_ts") > lit("30 minutes")),
                                  lit(1)).otherwise(lit(0)))
    .withColumn("session_id",
                sum("new_session").over(Window.partitionBy("user_id").orderBy("event_time"))))
```

### AI Use Case

**AI-driven sessionization.** AI learns user behavior patterns,
recommends session gaps per cohort. The Principal's edge: better
sessionization accuracy.

### CTO / Principal Motivation

Sessionization is **the metric that defines engagement**. "How
long is a session?" determines MAU/DAU ratios. The Principal owns
the **session definition**; the CTO owns the **engagement metric**
narrative.

---

## Lesson 5 — Data Quality Framework

### Theory

A DQ framework = **rules + tests + alerts**. Mental model:

- **Schema tests** — column types, nullability, uniqueness.
- **Value tests** — accepted values, ranges, regex.
- **Volume tests** — row count thresholds.
- **Freshness tests** — last update < N minutes.
- **Custom tests** — business rules.

Tools: **Great Expectations**, **Deequ**, **dbt tests**, custom
PySpark.

### Practical Example

A Deequ DQ suite:

```python
from pydeequ.checks import Check, CheckLevel
from pydeequ.verification import VerificationSuite

check = Check(spark, CheckLevel.Warning, "events_dq")
check = (check.hasSize(lambda x: x > 1000000)
              .isComplete("event_id")
              .isUnique("event_id")
              .isContainedIn("country", ["US", "UK", "DE"])
              .hasMin("amount", lambda x: x == 0)
              .hasMax("amount", lambda x: x < 100000))

result = VerificationSuite(spark).onData(df).addCheck(check).run()
if result.status != "Success":
    raise Exception("DQ failed")
```

### AI Use Case

**AI-driven DQ rule generation.** AI watches data distributions,
suggests range and uniqueness rules. The Principal's edge: 5× faster
DQ authoring.

### CTO / Principal Motivation

DQ framework is the **CTO's trust tool**. "We catch data issues
before they reach the dashboard." The Principal owns the **DQ
platform**; the CTO owns the **trust narrative**.

---

## Lesson 6 — Optimize Spark Job

### Theory

The 15 Spark optimizations ranked by impact. Mental model:

| Lever | Impact | Effort |
|-------|--------|--------|
| **Shuffle partition tuning** | 3-5× | Low |
| **Broadcast small tables** | 2-10× | Low |
| **Coalesce small files** | 2-3× | Low |
| **AQE (Adaptive Query Execution)** | 2-3× | Low (just enable) |
| **Predicate pushdown** | 2-10× | Medium |
| **Column pruning** | 2-3× | Medium |
| **Persist hot DataFrames** | 2× | Medium |
| **Avoid UDFs (use Pandas UDFs)** | 10× | Medium |
| **Custom partitioner for skew** | 5-10× | High |
| **Salting for skew** | 5-10× | Medium |
| **Bucketing** | 3-5× | High |
| **Whole-stage codegen** | 1.5-2× | Automatic |
| **Vectorized reader** | 2× | Automatic |
| **Tungsten** | Automatic | Automatic |
| **Driver memory / shuffle service** | Stability | Low |

### Practical Example

A "before" and "after" example on the same job:

```python
# Before — 2 hours
df = (spark.read.parquet("s3://raw/")
        .filter(col("country") == "US")
        .groupBy("user_id").sum("amount"))

# After — 12 minutes
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.shuffle.partitions", "200")
df = (spark.read.parquet("s3://raw/")
        .filter(col("country") == "US")  # predicate pushdown
        .groupBy("user_id").sum("amount"))
```

### AI Use Case

**AI-driven Spark tuning.** AI scans Spark UI, recommends the
top 5 levers. The Principal's edge: 10× faster jobs from
automated optimization.

### CTO / Principal Motivation

Spark optimization is **the highest-ROI skill in DE**. A Staff
engineer who can 10× a job saves the company $500k/year in
compute. The Principal's deliverable: a **tuning playbook**.

---

## Lesson 7 — Streaming Pipeline

### Theory

The streaming pipeline interview pattern. Mental model:

- **Source** — Kafka, file, socket.
- **Watermark** — bound for late data.
- **Stateful ops** — aggregations, joins, dedup.
- **Sink** — Iceberg, Kafka, console.
- **Trigger** — processing time, available-now.

The trick: explain **exactly-once via idempotent sinks** (Iceberg,
Delta) plus **checkpoint** durability.

### Practical Example

The full streaming pattern:

```python
(spark.readStream
      .format("kafka").option("subscribe", "events").load()
      .selectExpr("cast(value as string) as v")
      .select(from_json("v", schema).alias("e"))
      .select("e.*")
      .withWatermark("event_time", "10 minutes")
      .groupBy(window("event_time", "5 minutes"), "event_type")
      .count()
      .writeStream
      .format("iceberg")
      .outputMode("append")
      .option("checkpointLocation", "s3://checkpoints/")
      .trigger(processingTime="30 seconds")
      .start("s3://silver/aggregates/"))
```

### AI Use Case

**AI-generated streaming skeleton.** Describe a stream → AI generates
the read/write/transform code. The Principal's edge: 5× faster
streaming pipeline authoring.

### CTO / Principal Motivation

Streaming pipelines are **the differentiation feature** for
real-time analytics. The Principal owns the **streaming standard**;
the CTO owns the **real-time product** narrative.

---

## Lesson 8 — Custom Partitioner

### Theory

When the default hash partitioner creates hot partitions. Mental
model:

- **Default** — `hash(key) % numPartitions`.
- **Hot key problem** — if 1% of keys account for 50% of records,
  the partition for those keys is 50× larger.
- **Solutions:**
  - **Salting** — append random prefix to hot keys, expand and
    reduce later.
  - **Custom partitioner** — RDD-level control.
  - **AQE skew join** — automatic skew handling (Spark 3.x).

### Practical Example

Salting a join on hot keys:

```python
# Source with hot keys
hot_df = ...  # 90% of rows have user_id in top 1%

# Add salt to spread hot keys
from pyspark.sql.functions import concat, lit, rand, floor

salted_hot = hot_df.withColumn("salt", (floor(rand() * 100)).cast("int")) \
                    .withColumn("salted_key", concat(col("user_id"), lit("_"), col("salt")))

# Replicate other side 100x
replicated_other = other_df.crossJoin(
    spark.range(100).withColumnRenamed("id", "salt")
).withColumn("salted_key", concat(col("user_id"), lit("_"), col("salt")))

joined = salted_hot.join(replicated_other, "salted_key").drop("salt", "salted_key")
```

### AI Use Case

**AI-driven skew detection.** AI watches Spark UI skew metrics,
recommends salting + replication factor. The Principal's edge:
skew-free joins automatically.

### CTO / Principal Motivation

Skew handling is **the on-call superpower**. When a job hangs
because of skew, the engineer who knows salting fixes it in 30
minutes. The Principal owns the **skew playbook**.

---

## Lesson 9 — Idempotent Upsert

### Theory

Idempotent upsert = **MERGE that can run multiple times with the
same result**. Mental model:

- **Target** — existing table (Iceberg, Delta, JDBC).
- **Source** — new data.
- **MERGE** — match keys, update matched, insert not matched.
- **Idempotency** — running twice produces same output as running
  once.

The trick: use a stable merge key (event_id, not ts).

### Practical Example

MERGE into Iceberg:

```python
from pyiceberg.catalog import load_catalog

catalog = load_catalog("lake")
table = catalog.load_table("silver.events")

# Read source
source_df = spark.read.parquet("s3://staging/events/")

# Merge using SQL
spark.sql("""
    MERGE INTO silver.events t
    USING staging.events s
    ON t.event_id = s.event_id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")
```

### AI Use Case

**AI-driven idempotency audit.** AI checks MERGE statements for
non-idempotent operations. The Principal's edge: zero duplicate
data.

### CTO / Principal Motivation

Idempotent upserts are **the reliability foundation**. Every
Principal enforces "every MERGE has a stable merge key." CTOs see
this as **data correctness** at scale.

---

## Lesson 10 — Error Handling Pipeline

### Theory

A production Spark pipeline handles errors gracefully. Mental
model:

- **Bad rows** — quarantine (DLQ), continue.
- **Transient errors** — retry with exponential backoff.
- **Schema drift** — fail fast or allow with version bump.
- **DLQ table** — `events.dlq` for manual review.

### Practical Example

A pipeline with DLQ:

```python
from pyspark.sql.utils import AnalysisException

try:
    df = (spark.readStream
              .format("kafka").option("subscribe", "events").load()
              .selectExpr("cast(value as string) as v")
              .select(from_json("v", schema).alias("e"))
              .select("e.*"))

    # Split bad rows
    good = df.filter(col("event_id").isNotNull())
    bad = df.filter(col("event_id").isNull())

    (good.writeStream.format("iceberg")
          .outputMode("append")
          .option("checkpointLocation", "s3://checkpoints/good/")
          .start("s3://silver/events/"))

    (bad.writeStream.format("iceberg")
          .outputMode("append")
          .option("checkpointLocation", "s3://checkpoints/dlq/")
          .start("s3://silver/events.dlq/"))
except AnalysisException as e:
    logger.error(f"Schema mismatch: {e}")
    alert_oncall(e)
```

### AI Use Case

**AI-driven error classification.** AI categorizes errors by
severity, suggests remediation. The Principal's edge: faster MTTR.

### CTO / Principal Motivation

Error handling is **the difference between a toy pipeline and a
production one**. The Principal owns the **error handling
standard**; the CTO sees the **MTTR dashboard**.

---

## Lesson 11 — Quiz: Interview Patterns

### Theory

Validate: ability to design and implement each of the 10 patterns
above in 15-30 minutes.

### Practical Example

The capstone drill — write all 10 patterns from scratch in 5 hours:

1. Flatten JSON.
2. Dedup.
3. SCD2.
4. Sessionize.
5. DQ framework.
6. Optimize a slow job.
7. Streaming pipeline.
8. Custom partitioner.
9. Idempotent upsert.
10. Error handling.

### AI Use Case

AI-generated pattern-drill exercises with timed feedback.

### CTO / Principal Motivation

Pattern mastery is **the interview gold standard**. The
Principal who can write any pattern in 15 minutes interviews at
Staff/Principal level. The one who can't, plateaus at Senior.

---

# Closing Notes

## The Promotion Path from this Course

| Level        | Skill unlocked by this course | Compensation signal |
|--------------|-------------------------------|---------------------|
| Senior DE    | Writes standard PySpark jobs; uses built-in functions | $150-200k |
| Staff DE     | Writes Pandas UDFs; optimizes Spark jobs; debugs skew | $200-280k |
| Principal DE | Designs the 11 interview patterns; reviews architecture; sets tuning standards | $280-400k |
| Director / VP | Owns PySpark platform; sets coding standards; recruits + grows team | $350-500k+ |
| CTO          | Decides Spark vs Snowflake vs Databricks SQL vs Polars strategy | $400-700k+ |

## The PySpark Principal's Strategic Toolkit

Seven decisions a Principal owns:

1. **DataFrame-first** — every new job starts as DataFrame; RDD only
   when forced.
2. **Pandas UDF default** — every UDF is vectorized; row UDFs banned
   without justification.
3. **Broadcast by default** — every join `<100 MB` is `broadcast()`.
4. **AQE always on** — `spark.sql.adaptive.enabled=true` baseline.
5. **Iceberg/Delta over parquet** — schema enforcement + ACID by
   default.
6. **SCD2 default for dims** — Type 1 only for non-audit dims.
7. **Idempotent MERGE always** — no INSERT, no UPDATE; only MERGE.

## The Two CTO Pillars (PySpark flavor)

This course is the **technical pillar** for PySpark-centric CTOs.
The **other pillar** is the "compute unit economics" narrative —
"$0.005/GB scanned with our Spark tuning playbook" beats "$X/quarter
on Databricks" every time. CTOs who have both pillars close
deals 5× faster.

## Cross-References

- **DE Foundations** — `01_de_foundations_track.md`.
- **DE System Design CTO plan** — `de_system_design_cto_learning_plan.md`
  (Spark in architecture patterns).
- **AWS DE CTO plan** — `aws_de_cto_learning_plan.md` (EMR vs Glue vs
  Athena for Spark workloads).
- **Snowflake full-detail** — `snowflake_full_detail.md` (Snowflake
  Cortex as alternative to PySpark ML).
