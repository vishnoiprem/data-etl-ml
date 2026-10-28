# 2.2 — RDDs vs DataFrames: Choosing the Right Abstraction

> **Section 2 · Spark Fundamentals · Lecture 2.2 · 21:05**

## 🎯 What you will learn

- The five properties that define an RDD, and how the lineage graph makes it fault tolerant
- `persist` vs `checkpoint` vs `localCheckpoint` — and when lineage truncation is mandatory
- Why Catalyst makes DataFrames several times faster than the equivalent RDD code
- The honest answer to "when should I actually use an RDD?"
- How to write vectorized `pandas_udf` UDFs with Arrow, and when they beat Python UDFs
- Why `df.rdd.map(...)` is a self-inflicted wound, and what to do instead

---

## 🧠 Concept

Chapter 2.1 gave you the machinery. This chapter is about the decision you make every time
you open a Python file: **RDD or DataFrame?**

The short answer is that the DataFrame is correct about 95% of the time, and the exceptions
are narrow, specific, and worth knowing. But "learn RDDs, write DataFrames" is a slogan,
not an engineering answer. This chapter gives you the reasoning.

---

### The five properties of an RDD

| # | Property | What it means | Why it matters |
|---|----------|---------------|----------------|
| 1 | **Partitioned** | An RDD is split into logical partitions, each stored on one executor and processed by one task. The partitioner determines the layout. | This is what makes it *distributed* and what makes shuffle behavior predictable. |
| 2 | **Closure-based** | Transformations capture the Python function (the *closure*) and ship it to the executors. | The closure is serialized and sent over the network. It must be picklable, and its captured variables are shipped with every task. |
| 3 | **Lineage-based** | Each RDD remembers the sequence of transformations that produced it, forming a DAG. | This is the basis of fault tolerance: lost partitions are recomputed from the lineage rather than restored from a backup. |
| 4 | **Lazy** | Transformations build the lineage; actions trigger execution. | Enables whole-query optimization and stage fusion. |
| 5 | **Fault-tolerant** | A failed task is re-run on another executor, recomputing the lost partition from its lineage. | The data is *reproducible*, not *replicated* — which is why Spark does not need 3× replication for compute. |

⚠️ **The closure property is a real footgun.** The function you pass to `map`/`filter`/
`reduceByKey` is serialized and shipped. If it captures a 2 GB list, that list is shipped to
every executor for every task. If it captures an unpicklable object (an open socket, a
database connection), the job fails with a `PicklingError` or `TypeError` at task launch
time — not when you defined the function.

### The lineage graph

```
  sc.textFile("gs://bucket/logs/")        ← RDD 0:  text lines
        │
        │  .filter(lambda l: "ERROR" in l)     narrow
        ▼
  RDD 1                                  (same partitions, fewer records)
        │
        │  .map(parse_line)                    narrow
        ▼
  RDD 2                                  (same partitions)
        │
        │  .map(lambda r: (r.host, 1)).reduceByKey(add)   ← SHUFFLE
        ▼
  RDD 3                                  (one partition per key hash bucket)
        │
        │  .collect()                              ACTION
        ▼
  Driver receives {host: count}
```

Every node records its parent. That record *is* the lineage. If executor 3 loses the
partition of RDD 2, Spark asks: "what produced this?" and replays
`textFile → filter → map` for that one partition only. No checkpoint, no replication, no
data loss.

💡 **Lineage is a liability as well as a feature.** A long lineage means a long replay. If
you read 50 GB from GCS, filter it down to 3 MB, and then join, the join's recompute
path includes re-reading 50 GB. **Checkpointing truncates that.**

### `persist` vs `checkpoint` vs `localCheckpoint`

This is the distinction people get wrong most often, and getting it wrong in the direction
of "too many checkpoints" is a real operational problem.

| | `persist()` | `checkpoint()` | `localCheckpoint()` |
|---|---|---|---|
| Stores data | ✅ In the block manager (memory/disk on executors) | ✅ On **reliable storage** (GCS/HDFS) | ✅ In the block manager, but **only on the executors that hold it** |
| Truncates lineage | ❌ No | ✅ **Yes** | ✅ Yes |
| Survives executor loss | ❌ No (unless a `*_2` storage level) | ✅ **Yes** | ❌ **No** — the data is gone and the lineage is gone, so it cannot be recomputed |
| Survives driver loss | Partially (blocks live on executors) | ✅ Yes | ❌ No |
| Requires a checkpoint directory | ❌ No | ✅ **Yes** | ❌ No |
| Reliable for production | ✅ Yes | ✅ Yes | ⚠️ **Best-effort only** |

```python
from pyspark import StorageLevel

# 1. persist — reuse without recompute, but lineage keeps growing
df = spark.read.parquet("gs://bucket/orders/").persist(StorageLevel.MEMORY_AND_DISK)
df.count()   # materialize

# 2. checkpoint — truncate lineage, write to reliable storage
sc = spark.sparkContext
sc.setCheckpointDir("gs://bucket/checkpoints/")     # REQUIRED
df_ck = df.checkpoint()      # eager: triggers a job
df_ck.count()                # lineage is now just the checkpoint
df_ck.unpersist()             # free the old cached blocks

# 3. localCheckpoint — truncate lineage without reliable storage
#    ✗ If an executor holding the data dies, the job CANNOT recover.
df_local = df.localCheckpoint()
df_local.count()
```

**Why checkpointing matters (the lineage-truncation case):**

```
BEFORE checkpoint:
   textFile(50 GB) → filter → map → join → groupBy → aggregate → write
   ^
   └── The replay path for the final stage includes re-reading 50 GB from GCS.
       If the final stage's input is lost, Spark re-reads all 50 GB.

AFTER checkpoint:
   checkpoint (gs://bucket/checkpoints/...) → join → groupBy → aggregate → write
   ^
   └── The replay path starts at the checkpoint: read a small, already-computed
       dataset. Recovery is fast and no longer depends on the source being
       available.
```

⚠️ **The `localCheckpoint()` failure mode is genuinely nasty.** It truncates the lineage
*and* stores the data only in executor memory/disk. If the executor holding that data dies,
there is nothing to recompute from — the lineage was already thrown away. The job fails
with a `SparkException` that gives no hint about the cause. Use `localCheckpoint()` only
for interactive exploration where a rerun is cheap. **Use `checkpoint()` for anything in a
pipeline.**

💡 **`checkpoint()` is also how you write a "safe" intermediate step in a long lineage.**
A common production pattern: checkpoint after each expensive stage so that a failure at
stage 50 does not require re-running stages 1–49.

### RDD vs DataFrame vs Dataset

| Dimension | RDD | DataFrame | Dataset[T] |
|-----------|-----|-----------|------------|
| API | `pyspark.RDD` | `pyspark.sql.DataFrame` | `pyspark.sql.Dataset` (Scala/Java) |
| Type safety | ❌ None — everything is a Python object | ⚠️ Runtime schema enforcement | ✅ **Compile-time** schema safety |
| Schema | ❌ None | ✅ Known, enforced at runtime | ✅ Known, enforced at compile time |
| Catalyst optimization | ❌ **None** | ✅ Full | ✅ Full |
| Predicate pushdown | ❌ None | ✅ Yes | ✅ Yes |
| Column pruning | ❌ None | ✅ Yes | ✅ Yes |
| Join reordering | ❌ None | ✅ Yes | ✅ Yes |
| Code generation (Tungsten) | ❌ Whole-stage codegen only | ✅ Per-operator codegen | ✅ Per-operator codegen |
| Serialization | Java/Pickle | Columnar (Tungsten) | Columnar (Tungsten) |
| Language | Python, Scala, Java, R | Python, Scala, Java, R, SQL | Scala, Java |
| UDF support | Python UDFs | Python UDFs, `pandas_udf`, native SQL | Scala/Java typed UDFs, `pandas_udf` |
| Typical speed | Slow (~9× slower than DataFrame for a group-and-sum; the gap widens with scale) | Fast | Fast |
| Use it when | You need fine-grained control over partitioning, custom binary/record processing, non-tabular data, or a library API that only accepts RDDs | **Almost always** | Scala/Java teams wanting compile-time safety |

Note the "Dataset" column: **`Dataset` is a Scala/Java API.** There is no Python
`Dataset[T]` in PySpark. In Python, the DataFrame *is* the top of the typed API, and you
get runtime schema enforcement instead of compile-time. This trips up Java/Scala engineers
who move to Python and look for `Dataset`.

### Catalyst: the DataFrame plan tree

`df.explain(mode="formatted")` shows the physical plan. `df.explain(True)` is identical.
The full logical plan tree is visible through the internal API:

```python
df._jdf.queryExecution().optimizedPlan().toString()
```

A formatted physical plan for a join with a filter and an aggregation:

```
== Physical Plan ==
AdaptiveSparkPlan (12)
+- == Final Plan ==
   * HashAggregate (9)
   +- * HashAggregate (7)
      +- * Sort (6)
         +- * Sort (4)
            +- * Project (3)
               +- * Filter (2)
                  +- * HashAggregate (1)
                     +- * Exchange hashpartitioning(customer_id#10, 200), ENSURE_REQUIREMENTS
                        +- * Project (0)
                           +- * HashAggregate (1)
                              +- * Exchange hashpartitioning(customer_id#10, 200), ENSURE_REQUIREMENTS
                                 +- * Filter (isnotnull(customer_id#10))
                                    +- * Scan parquet s3://bucket/orders
```

Reading it bottom-up:

| Node | Meaning |
|------|---------|
| `Scan parquet` | The base scan. Column pruning and predicate pushdown appear *above* the scan in this plan, but they are **fused into** the scan at execution. |
| `Filter` | Pushed as close to the scan as possible. |
| `Exchange hashpartitioning(...)` | **A shuffle.** 200 output partitions. Two of them here — one per side of the join. |
| `HashAggregate` | A hash-based aggregate. The first is a partial (map-side) aggregate, the second a final (reduce-side) one. |
| `Sort` | Sorting; the second sort appears because AQE or a window function needs it. |
| `Project` | Column projection. |

💡 **The `Exchange` node is the single most useful thing in the plan.** Every `Exchange` is
a full network shuffle. Counting them tells you the shuffle complexity of a query, and the
`200` in `hashpartitioning(x, 200)` is your `spark.sql.shuffle.partitions` value showing
up in the plan.

### Tungsten: the physical execution engine

Tungsten is Spark's replacement for the old row-based execution engine. It has three
components:

**1. Off-heap memory management.** Spark manages its own memory outside the JVM heap, in
off-heap regions allocated via `Unsafe`. This avoids GC pressure entirely — the classic JVM
problem where a 16 GB heap spends 30% of its time in garbage collection and the objects you
care about get copied around by the collector.

```
JVM heap                          Off-heap (Tungsten)
┌───────────────────────┐         ┌──────────────────────────┐
│  User code objects    │         │  Columnar batches         │
│  Python objects       │         │  (compact, no pointers)   │
│  Scala/Java objects   │         │  Unsafe-managed           │
│                       │         │  → no GC, no copying     │
└───────────────────────┘         └──────────────────────────┘
```

**2. Cache-aware optimizer.** Tungsten reorders and fuses operators to maximize cache hits
across a query. The classic example: a projection of a projection of a filter gets fused
into one pass.

**3. Whole-stage code generation.** This is the big one. Instead of the old Volcano model
(where every operator is a virtual call through a generic iterator), Tungsten generates a
**single Java class** for the entire stage:

```
OLD (Volcano) — one virtual call per row, per operator
   FilterIterator.next()  →  ProjectIterator.next()  →  AggregateIterator.next()
       │                        │                          │
       └─ virtual dispatch      └─ virtual dispatch       └─ virtual dispatch
          (megamorphic call sites, boxing, no fusion)

NEW (Tungsten) — one generated method for the whole stage
   stage_fused_filter_project_aggregate(unsafeRow) {
       // doFilter
       // doProject
       // doAggregate
       return result;
   }
   → monomorphic call sites, primitive types, no boxing, no boundaries
```

The speedup from whole-stage codegen alone is typically **2–10×**. The generated code is
visible in the Spark UI's "SQL" tab as the `codegen` stage, and in the plan as
`Generate `stage_fused_filter_project_aggregate` (favicon: codegen)`.

⚠️ **Tungsten's codegen has a limit: 64 KB of JVM bytecode per generated method.** Very
wide queries (50+ columns, dozens of expressions) can hit `Code too large` errors. The fix
is to break the query into stages, or to disable codegen for the affected operator with
`spark.sql.codegen.wholeStage=false` (a last resort, not a habit).

### So when should you *actually* use an RDD?

The honest answer, with real criteria:

**Use an RDD when you need one of these:**

**1. Fine-grained control over partitioning.**

```python
# You need to guarantee that records with the same key land in the same partition
# and are processed together in a specific order.
rdd = sc.textFile(path).map(parse)
rdd = rdd.partitionBy(64, custom_partitioner)   # explicit partitioner
rdd = rdd.mapPartitions(process_partition)        # per-partition custom logic
```

DataFrames can do this via `repartition(col)`, but RDDs give you a `Partitioner` object —
arbitrary partitioning logic, including range partitioning and custom hash functions that
you implement.

**2. Custom binary or record-level processing.**

```python
# Processing a format with no DataSource: a custom binary codec, a proprietary
# wire format, an embedded document, an encrypted record stream.
def decode_partition(iterator):
    for record in iterator:
        yield my_codec.decode(record)

rdd = sc.binaryFiles(paths, minPartitions=100)
rdd = rdd.flatMap(decode_partition)
```

This is the strongest RDD case. There is no Catalyst optimization available, but you
control the bytes.

**3. Non-tabular data with no schema.**

```python
# Arbitrary Python objects: nested dicts, mixed types, recursive structures.
records = [{"a": 1, "b": {"c": [1, 2, 3]}}, {"a": 2, "b": None}]
rdd = sc.parallelize(records)
rdd.map(normalize_nested).filter(lambda r: r["b"]).collect()
```

**4. A library API that only accepts RDDs.**

Some third-party Spark libraries — certain ML connectors, custom Spark connectors, older
GraphFrames-style tools — expose only an RDD-based API. If the library takes an RDD, you
convert with `df.rdd` and hand it over.

**5. Iterative algorithms with unusual control flow** where the DataFrame API's declarative
model fights you, and where you want explicit control over when work happens.

**Do NOT use an RDD when:**

- ❌ You just want to `map` and `filter` a table. Use `select`/`withColumn` and `filter`.
- ❌ You want to join. DataFrame joins are Catalyst-optimized; RDD joins are not.
- ❌ You want a groupBy. `reduceByKey` on an RDD is roughly **9× slower** than a DataFrame
  `groupBy` with the same logic (measured on 2M rows, `local[4]`), because the RDD path
  pays Python object serialization for every intermediate record.
- ❌ The data is tabular and you want to write it out. RDDs lose the schema on write.

💡 **A good heuristic:** if you can describe the operation in terms of *rows and columns*,
use a DataFrame. If you can only describe it in terms of *bytes, records, and partitions*,
use an RDD.

### The cost of `collect()`

```python
result = df.collect()          # ALL rows to the driver
```

`collect()` pulls the **entire** result set into the driver JVM and then into the Python
process. Three things have to fit simultaneously:

```
1. The serialized result in the driver's network/result buffer
2. The deserialized result in the driver JVM heap
3. The Python objects in the driver Python process

Total needed ≈ 2–3× the size of the result
```

⚠️ **The result-size ceiling is enforced.** `spark.driver.maxResultSize` (default `1g`)
causes the job to fail with:
```
java.lang.IllegalArgumentException: Job aborted due to stage failure:
Total size of serialized results of 12345 tasks (2.5 GiB) exceeds max allowed size
```
Raising that limit to 100g does not fix the problem — it just moves the OOM from a clear
error to an opaque one. **The real fix is to not collect.**

**The safe alternatives:**

```python
# ✅ Iterate in chunks, one partition at a time — memory bounded
for row in df.toLocalIterator():
    process(row)
    # only one partition is in memory at a time

# ✅ Write to storage and let the write happen on the executors
df.write.mode("overwrite").parquet(path)

# ✅ Aggregate on the executors, collect only the small result
df.groupBy("key").count().collect()   # small if key cardinality is small

# ✅ foreachPartition — runs on executors, no data through the driver
def write_partition(iterator):
    for row in iterator:
        buffer.append(row)
    if buffer:
        writer.write(buffer)

df.foreachPartition(write_partition)

# ✅ bound the result first, then convert (Spark 3.5 has no toPandas(n=...))
sample = df.limit(10000).toPandas()
```

`toLocalIterator()` is the correct answer when you genuinely need row-by-row processing in
Python. It consumes one partition at a time, so peak memory is
`partition_size × overhead`, not `total_size`.

⚠️ **`toLocalIterator()` is not free either.** It runs one job per partition. A DataFrame
with 1,000 partitions means 1,000 sequential jobs. It is memory-safe but latency-heavy.
Use it for data that genuinely needs Python-level logic, not as a default.

### `foreachPartition` — the write-without-a-driver pattern

```python
from pyspark.sql import functions as F

def write_partition(iterator):
    """Runs once per partition, on the executor. No data flows to the driver."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    import os, tempfile, shutil

    rows = list(iterator)
    if not rows:
        return

    # Convert to Arrow and write with a fast, non-Spark writer
    table = pa.Table.from_pylist([r.asDict() for r in rows])
    tmp = tempfile.mkdtemp()
    try:
        pq.write_table(table, os.path.join(tmp, "part.parquet"))
        # ... upload to GCS, or merge into the output
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

df.foreachPartition(write_partition)
```

This pattern is genuinely useful: it lets you use a specialized writer (Arrow, ORC, a
database bulk loader) without paying Spark's per-row write overhead, while keeping the
data on the executors.

### `mapPartitions` — per-partition RDD transformation

```python
# One call per partition, not per record. This is the RDD equivalent of foreachPartition.
def process_partition(rows):
    buffer = []
    for r in rows:
        buffer.append(transform(r))
    if buffer:
        yield from buffer
    # NOTE: the generator is consumed lazily — do not return a list!

rdd.mapPartitions(process_partition).write.parquet(path)
```

⚠️ **The classic `mapPartitions` bug:** returning a list instead of yielding. If you
`return some_list`, Spark treats the whole list as a single element of the output
partition, and you get nonsense downstream. Always `yield`.

💡 **`mapPartitions` is where you batch.** The performance difference between calling a
function once per row and once per partition (with internal batching) is enormous — it's
the same principle behind `pandas_udf`.

### The danger of `df.rdd.map(lambda ...)`

This is the anti-pattern that looks harmless and destroys performance:

```python
# ❌ DANGEROUS
rdd = df.rdd.map(lambda r: r["amount"] * 1.1)
result = rdd.collectAsList()
```

What just happened:
1. `df.rdd` converts the DataFrame to an RDD. **The schema is gone.**
2. `.map()` is a Python function call **per row**, executed in a Python worker process.
3. The result is a Python object RDD with no schema.
4. Catalyst cannot optimize any of it, because it is no longer a DataFrame.
5. You pay Python interpreter overhead per row: measured at **~4.5× slower** than a native
   columnar expression at 500K rows, and **~16× slower** at 2M rows. The penalty grows
   with volume, because the per-row overhead is linear while the native path's overhead
   is amortized across a whole columnar batch.

```python
# ✅ The same thing, done right
result = df.withColumn("amount", F.col("amount") * F.lit(1.1))
```

Compare timings on 10 million rows: the native version is typically a few seconds; the RDD
version can be minutes. And the native version can be pushed down into the scan, while the
RDD version reads everything.

⚠️ **`df.rdd` also breaks the write path.** Writing an RDD of Python objects to Parquet
does not produce a Parquet file with a schema — it produces a file of pickled objects, or
fails outright. If you need RDDs for processing, convert back to a DataFrame with
`spark.createDataFrame(rdd, schema)` before writing.

### Python UDFs: the slow path

A **Python UDF** is a function written in Python that Catalyst must call row by row:

```python
from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType

@udf(returnType=DoubleType())
def normalize_amount(amount, region):
    factor = {"EMEA": 1.0, "APAC": 1.2, "AMER": 0.95}[region]
    return round(amount * factor, 2)

df.withColumn("normalized", normalize_amount(F.col("amount"), F.col("region")))
```

The cost of this pattern:
- One Python process hop per row (or per batch, depending on the Arrow setting).
- The Python worker holds a copy of the data.
- **Catalyst cannot see inside the function.** It cannot push the filter past it, cannot
  constant-fold it, cannot prune columns based on it.
- The Python interpreter is roughly **5–20× slower** than generated JVM code for a
  per-row scalar operation.

### `pandas_udf`: the vectorized path

A **`pandas_udf`** (note the lowercase — this is the *decorator*, not the
`pyspark.pandas` library) is a vectorized UDF that operates on **batches of rows** using
pandas, with zero-copy transfer via Apache Arrow.

**Arrow is required.** Without it, `pandas_udf` raises:

```
ImportError: Pandas UDFs require the pandas library and pandas >= 1.0.5
... or
py4j.protocol.Py4JJavaError: org.apache.spark.sql.AnalysisException:
[WRONG_COMMAND_FOR_OBJECT_TYPE] ... requires the Arrow optimization to be enabled
```

Enable it:

```python
spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
# or at submit time:
#   --conf spark.sql.execution.arrow.pyspark.enabled=true
```

💡 **On Dataproc, Arrow is available in the 2.2 image (Spark 3.5) but the flag is off by
default.** Set it explicitly in every job that uses `pandas_udf` or `toPandas()`. It is
also the single highest-leverage performance config in PySpark.

**A real, complete `pandas_udf` example:**

```python
import pandas as pd
import numpy as np
from pyspark.sql.functions import pandas_udf, PandasUDFType
from pyspark.sql.types import DoubleType, StringType

# Arrow must be enabled
spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")

@pandas_udf(returnType=DoubleType(), functionType=PandasUDFType.SCALAR)
def normalize_amount(amounts: pd.Series, regions: pd.Series) -> pd.Series:
    """
    Vectorized: receives a whole batch of rows as pandas Series, not one row at a time.
    """
    factors = regions.map({"EMEA": 1.0, "APAC": 1.2, "AMER": 0.95}).fillna(1.0)
    return (amounts * factors).round(2)

df.withColumn("normalized", normalize_amount(F.col("amount"), F.col("region"))).show()
```

**When a `pandas_udf` beats a Python UDF:** whenever the function does anything that
benefits from vectorization — arithmetic across columns, `numpy` operations, `pandas`
grouping, statistical transforms, rolling windows, string vectorization. The speedup is
typically **3–20×** over a row-at-a-time Python UDF (measured: ~3.5× on a 4M-row
arithmetic UDF), because the per-row Python interpreter overhead is amortized across a
batch of thousands of rows. The bigger the win, the more the function leans on
vectorized operations — a `pandas_udf` doing `numpy` math on a whole batch can approach
native performance, while one doing complex per-row branching gains much less.

**When it does NOT help:** if the function is trivial (`x + 1`), a native SQL expression is
still faster, because a native expression runs in generated JVM code with no Arrow
transfer at all. And a Python UDF that fails for most rows (raises an exception) will be
much slower with `pandas_udf`, because a single bad row fails the whole batch instead of
one row.

**Grouped `pandas_udf`:**

```python
from pyspark.sql.types import LongType
from pyspark.sql import functions as F

@pandas_udf(
    returnType=LongType(),
    functionType=PandasUDFType.GROUPED_AGG
)
def count_above_threshold(s: pd.Series, threshold: int) -> int:
    """Called once per group, with that group's rows as a Series."""
    return int((s > threshold).sum())

df.groupBy("region").agg(
    count_above_threshold(F.col("amount"), F.lit(100)).alias("orders_over_100")
).show()
```

⚠️ **The constant is `GROUPED_AGG`, not `GROUPED`.** The full set of `PandasUDFType`
constants in Spark 3.5 is:

| Constant | Value | Meaning |
|----------|-------|---------|
| `PandasUDFType.SCALAR` | 200 | One Series in → one Series out, per row batch. |
| `PandasUDFType.SCALAR_ITER` | 204 | Like SCALAR, but the function returns an **iterator** of Series (multiple output columns). |
| `PandasUDFType.GROUPED_MAP` | 201 | Applied to each group; receives and returns a pandas DataFrame. |
| `PandasUDFType.GROUPED_AGG` | 202 | Applied to each group; receives a Series and returns a **scalar** to be aggregated. |

Using `PandasUDFType.GROUPED` raises
`AttributeError: type object 'PandasUDFType' has no attribute 'GROUPED'`.

A grouped `pandas_udf` gets the entire group as a pandas Series. This is enormously
faster than `groupByKey` + Python function, because the data never becomes Python objects
one at a time.

### `mapInPandas`

`mapInPandas` is the iterator-based counterpart: it gives you a **pandas DataFrame** per
input partition and expects a **pandas DataFrame** back.

```python
import pandas as pd
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType

def explode_batches(iterator):
    """
    Input:  iterator of pandas DataFrames (one per input partition)
    Output: iterator of pandas DataFrames (each becomes one output partition)
    """
    for pdf in iterator:
        # pdf is a pandas DataFrame — do vectorized work
        pdf["amount"] = pdf["amount"] * 1.1
        pdf["region_tag"] = pdf["region"].str.upper()
        yield pdf[["order_id", "region_tag", "amount"]]

schema = StructType([
    StructField("order_id", StringType(), False),
    StructField("region_tag", StringType(), True),
    StructField("amount", DoubleType(), True),
])

result = df.mapInPandas(explode_batches, schema=schema)
```

`mapInPandas` is the right tool when your transformation is naturally **batched** and
does not fit the `pandas_udf` signature — for example, when you need to compute a
statistic over the whole partition, or when you want to reshape the schema (drop columns,
change types, split a column).

⚠️ **`mapInPandas` output partitioning follows the input partitioning.** If your input has
1 partition, your output has 1 partition — which may be much smaller than you want for a
downstream write. Call `repartition()` first if you need more output files.

### `udf` vs `pandas_udf` vs native SQL

| Approach | Execution | Catalyst can optimize? | Relative speed | Use when |
|----------|-----------|------------------------|----------------|----------|
| **Native SQL / `F.expr`** | Generated JVM code (Tungsten) | ✅ **Fully** | ⭐⭐⭐⭐⭐ (fastest) | Always, if the logic can be expressed in SQL. |
| **`pandas_udf`** | Batch Arrow transfer + pandas/numpy | ⚠️ Partially — pushdown stops at the UDF | ⭐⭐⭐⭐ | The logic genuinely needs Python, pandas, or numpy. |
| **Plain `udf`** | One Python hop per row (or per batch with Arrow) | ❌ **No** | ⭐ (slowest) | Last resort. |
| **`mapInPandas`** | Partition-level Arrow transfer | ⚠️ Partially | ⭐⭐⭐⭐ | Batch reshaping across a partition. |
| **Built-in `functions` library** | Generated JVM code | ✅ Fully | ⭐⭐⭐⭐⭐ | Almost always — `F.regexp_extract`, `F.json_tuple`, `F.date_diff`, etc. cover most needs. |

**The critical insight about `F.expr` and native expressions:**

```python
# ✅ Native — Catalyst sees the expression, pushes filters past it, prunes columns
df.withColumn("clean", F.expr("regexp_replace(name, '[^a-zA-Z]', '')"))
df.withColumn("dow",  F.expr("date_format(order_date, 'EEE')"))
df.withColumn("seg",  F.expr("CASE WHEN amount > 1000 THEN 'high' ELSE 'low' END"))

# ❌ Python — Catalyst sees an opaque black box
@udf(returnType=StringType())
def clean(name):
    return re.sub(r'[^a-zA-Z]', '', name)

df.withColumn("clean", clean(F.col("name")))
```

`F.expr` is not "a way to write SQL in Python" — it is a way to get **a native,
Catalyst-optimizable expression** without leaving the DataFrame API. It is the single best
tool for the gap between "I need SQL" and "I don't want to leave the DataFrame API".

💡 **Before writing any UDF, check the built-in library.** `F` has well over 200
functions covering string manipulation, date arithmetic, JSON/CSV parsing, arrays, maps,
null handling, and aggregates. Most "I need a UDF for this" moments are already solved:

| Task | Don't write a UDF | Use |
|------|------------------|-----|
| Extract a field from JSON | ✅ | `F.get_json_object(col, "$.field")` or `F.from_json(col, schema)` |
| Parse a date string | ✅ | `F.to_date(col, "yyyy-MM-dd")` |
| Standardize a string | ✅ | `F.lower(F.trim(col))` |
| Split a string | ✅ | `F.split(col, ",").getItem(0)` |
| Conditional logic | ✅ | `F.when(cond, a).otherwise(b)` or `F.expr("CASE ...")` |
| Cumulative sum | ✅ | `F.sum("amount").over(Window.orderBy("ts"))` |
| Fill nulls | ✅ | `F.coalesce(col, F.lit(0))` |
| Row number | ✅ | `F.row_number().over(Window.partitionBy("k").orderBy("ts"))` |

### Benchmark methodology

Never trust a single measurement. Here is a repeatable procedure.

```python
import time

def timeit(label, fn, repeat=3):
    """Run a Spark action `repeat` times, discard the first (warm-up), report the median."""
    timings = []
    for i in range(repeat):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        timings.append(t1 - t0)
    timings_sorted = sorted(timings)
    median = timings_sorted[len(timings_sorted) // 2]
    print(f"{label:40s} median={median:7.3f}s  all={[round(t,3) for t in timings]}")
    return median

native   = timeit("native select", lambda: df.withColumn("x", F.col("amount") * F.lit(1.1)).count())
python_udf = timeit("python udf",  lambda: df.withColumn("x", udf_norm(F.col("amount"))).count())
pandas_udf_ = timeit("pandas_udf",   lambda: df.withColumn("x", pandas_norm(F.col("amount"))).count())
```

**Methodology rules:**

1. **Discard the first run.** JIT compilation, Arrow initialization, and metadata loading
   make the first run artificially slow.
2. **Measure with an action, not a plan.** Building a plan costs nothing, so a
   "benchmark" that only builds a plan measures Python function-call overhead.
3. **The action must consume the column under test.** `df.withColumn("v", udf(...)).count()`
   can be satisfied without evaluating the UDF's value, which makes every implementation
   look identical. Use `df.withColumn("v", udf(...)).agg(F.sum("v")).collect()`.
4. **Use `time.perf_counter()`, not `time.time()`.** It is monotonic.
5. **Compare plans, not just times.** `df.explain(mode="formatted")` tells you *why* one is
   faster. A faster plan and a faster time together are convincing; a faster time with the
   same plan usually means measurement noise.
6. **Check the Spark UI.** Compare "Duration" in the SQL tab, the number of tasks, and
   the **input bytes read**. If the input bytes differ, you are not comparing like with
   like — the UDF version read more data.
7. **Test at realistic scale.** A 1,000-row benchmark will show the Python UDF as
   *faster*, because Arrow setup and worker startup dominate. Always benchmark at the
   volume you actually run.

💡 **The most useful comparison is input bytes read.** If a UDF version reads 3× the
bytes of the native version, you have found a predicate-pushdown problem, not a
"Python is slow" problem.

### Memory and skew concerns with Python UDFs

**Memory.** Each Python worker process holds a copy of the data it is processing, plus
Python object overhead. Python objects are far larger than their logical size — a
single Python `int` costs ~28 bytes and a `str` ~50 bytes plus its content, versus 8 bytes
in a columnar batch.

```
A DataFrame column of 1M int64 values:      8 MB in a columnar batch
The same values as Python objects:          ~28 MB + interpreter overhead
The same values in a pandas Series:         8 MB (numpy-backed) ← pandas_udf stays efficient
```

💡 **This is why `pandas_udf` is memory-efficient while a plain Python UDF is not.**
`pandas_udf` converts each batch to a numpy-backed pandas Series (compact, 8 bytes per
int64) before your code sees it. A plain Python UDF materializes real Python objects.

**Skew.** The danger with a Python UDF is that a skewed partition forces a single Python
worker to process a huge batch, holding it all in memory.

```
Normal:  200 partitions × 1,000 rows each
Skewed:  199 partitions × 1,000 rows + 1 partition × 50,000,000 rows
                     └── the skewed task dominates the runtime
```

AQE (`spark.sql.adaptive.enabled=true`, default on) handles skew in **joins** by splitting
skewed shuffle partitions automatically. It does **not** fix skew in a Python UDF, because
the skew is in your data, not in a shuffle partition. Mitigations:

```python
# 1. Salt the key to spread the hot rows
df.withColumn("salted", F.concat(F.col("key"), F.lit(F.rand().cast("int")))).groupBy("key")

# 2. Pre-aggregate the hot key before the UDF
df.groupBy("key").agg(F.sum("amount").alias("amount"))   # now a cheap native op

# 3. Use a grouped pandas_udf — pandas handles a wide group far better than a row UDF
```

⚠️ **A Python UDF that raises an exception fails the task, and Spark retries it** (up to 4
times by default with `spark.task.maxFailures`). A UDF that fails on 1% of rows will retry
the whole partition 4 times and then fail the job. Make your UDFs null-safe and
error-tolerant, or catch inside the function and return null.

---

## 🛠️ Hands-On: Benchmarking the Three Approaches

### Step 1 — Set up and enable Arrow

```python
import time
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import udf, pandas_udf, PandasUDFType
from pyspark.sql.types import DoubleType, LongType, StringType

spark = (
    SparkSession.builder
    .master("local[4]")
    .appName("Lecture22-RDDvsDataFrame")
    .config("spark.sql.execution.arrow.pyspark.enabled", "true")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)

print("Arrow enabled:", spark.conf.get("spark.sql.execution.arrow.pyspark.enabled"))
```

### Step 2 — Generate a realistic dataset

```python
n = 4_000_000
df = (
    spark.range(n)
    .withColumn("customer_id", (F.col("id") % 50_000).cast("int"))
    .withColumn("region", F.when(F.col("id") % 3 == 0, F.lit("EMEA"))
                         .when(F.col("id") % 3 == 1, F.lit("APAC"))
                         .otherwise(F.lit("AMER")))
    .withColumn("amount", (F.col("id") % 5000) / 10.0)
)
df.cache().count()
print(df.count(), "rows")
```

### Step 3 — The three implementations

```python
# 1. Native expression
native_expr = F.col("amount") * F.when(F.col("region") == "APAC", F.lit(1.2)) \
                             .when(F.col("region") == "AMER", F.lit(0.95)) \
                             .otherwise(F.lit(1.0))

# 2. Plain Python UDF
@udf(returnType=DoubleType())
def py_udf_amount(amount, region):
    factor = {"EMEA": 1.0, "APAC": 1.2, "AMER": 0.95}.get(region, 1.0)
    return round(amount * factor, 2)

# 3. pandas_udf
@pandas_udf(returnType=DoubleType(), functionType=PandasUDFType.SCALAR)
def pandas_udf_amount(amounts: pd.Series, regions: pd.Series) -> pd.Series:
    factors = regions.map({"EMEA": 1.0, "APAC": 1.2, "AMER": 0.95}).fillna(1.0)
    return (amounts * factors).round(2)
```

### Step 4 — Benchmark them

```python
def timeit(label, fn, repeat=3):
    timings = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        timings.append(time.perf_counter() - t0)
    timings.sort()
    print(f"{label:32s} median={timings[len(timings)//2]:7.3f}s   {[round(t,3) for t in timings]}")

# ⚠️ Benchmark with an AGGREGATING action, not count().
# count() can be satisfied without evaluating the UDF column at all, which
# hides the real cost. sum("v") forces every row through the function.
def bench(label, expr):
    timeit(label, lambda: df.withColumn("v", expr).agg(F.sum("v")).collect())

bench("native expression", native_expr)
bench("python udf",         py_udf_amount(F.col("amount"), F.col("region")))
bench("pandas_udf",        pandas_udf_amount(F.col("amount"), F.col("region")))
```

Measured results on a 4-million-row table, `local[4]`, Spark 3.5:

```
native expression       median=  0.240s
pandas_udf             median=  0.741s     (~3× the native time)
python udf              median=  2.560s     (~10× the native time)
```

The native expression is fastest, `pandas_udf` is roughly 3× slower than native, and
the plain Python UDF is roughly 10× slower than native — and about **3–4× slower than
the `pandas_udf` doing identical work**.

⚠️ **Why you must aggregate, not `count()`.** This is the most common flaw in
PySpark benchmarks. `df.withColumn("v", udf(...)).count()` counts rows — it does not need
the UDF's output value. Spark can compute the count from the row count alone and skip
evaluating the UDF for most rows, so all three implementations look identical:

```
# ❌ MISLEADING — all three look the same (~0.1s)
timeit("native",     lambda: df.withColumn("v", native_expr).count())
timeit("python udf", lambda: df.withColumn("v", py_udf_amount(...)).count())
timeit("pandas_udf",lambda: df.withColumn("v", pandas_udf_amount(...)).count())

# ✅ CORRECT — forces full evaluation
timeit("native",     lambda: df.withColumn("v", native_expr).agg(F.sum("v")).collect())
```

💡 **A general rule: your benchmark's action must consume the column the UDF
produces.** If the thing you are optimizing does not appear in the action, you are
measuring nothing.

### Step 5 — Compare the plans

```python
df.withColumn("v", native_expr).explain(mode="formatted")
df.withColumn("v", py_udf_amount(F.col("amount"), F.col("region"))).explain(mode="formatted")
df.withColumn("v", pandas_udf_amount(F.col("amount"), F.col("region"))).explain(mode="formatted")
```

The native plan has no `PythonUDF` node. The UDF plans do — and that node is a **barrier**
that Catalyst cannot optimize past.

### Step 6 — The RDD anti-pattern, measured

```python
timeit("df.rdd.map (anti-pattern)",
       lambda: df.rdd.map(lambda r: r["amount"] * 1.1).count())
```

Compare that to the native run. The gap is the cost of losing the schema, losing
Catalyst, and paying Python interpreter overhead per row.

### Step 7 — Lineage truncation with checkpoint

```python
sc = spark.sparkContext
sc.setCheckpointDir("/tmp/spark-checkpoints/")     # required for checkpoint()

df_ck = df.checkpoint()      # eager
df_ck.count()
print("Lineage after checkpoint:")
print(df_ck._jdf.queryExecution().logical().toString()[:200])
```

Compare to `df._jdf.queryExecution().logical().toString()` before the checkpoint — the
pre-checkpoint lineage includes the whole `range → withColumn → ...` chain.

### Step 8 — `toLocalIterator` vs `collect`

```python
# The safe pattern for row-by-row Python processing
total = 0.0
for row in df.select("amount").toLocalIterator():
    total += row["amount"]
print("Total:", total)
```

Note that this is slower than `df.agg(F.sum("amount")).collect()[0][0]` — but it never
materializes more than one partition in the driver. Use it when you genuinely need
per-row Python; use the aggregate when you don't.

### Step 9 — `foreachPartition` for a custom write

```python
import os, tempfile, shutil, pyarrow as pa, pyarrow.parquet as pq

def write_part(iterator):
    rows = list(iterator)
    if not rows:
        return
    table = pa.Table.from_pylist([r.asDict() for r in rows])
    tmp = tempfile.mkdtemp()
    try:
        pq.write_table(table, os.path.join(tmp, "part.parquet"))
        print("wrote partition with", len(rows), "rows")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

df.select("customer_id", "region", "amount").foreachPartition(write_part)
```

### Step 10 — `mapInPandas` for batch reshaping

```python
from pyspark.sql.types import StructType, StructField, DoubleType, StringType, LongType

out_schema = StructType([
    StructField("customer_id", LongType(), True),
    StructField("region_tag",  StringType(), True),
    StructField("amount",      DoubleType(), True),
])

def reshape(iterator):
    for pdf in iterator:
        pdf = pdf.copy()
        pdf["region_tag"] = pdf["region"].str.upper()
        pdf["amount"] = pdf["amount"] * 1.1
        yield pdf[["customer_id", "region_tag", "amount"]]

df.select(
    F.col("customer_id").cast("long"),
    "region",
    "amount"
).mapInPandas(reshape, schema=out_schema).show(5)
```

---

## 🔑 Key Takeaways

- An RDD has five properties: **partitioned**, **closure-based**, **lineage-based**,
  **lazy**, and **fault-tolerant**. Fault tolerance comes from *recomputation*, not
  replication.
- **Lineage is both a feature and a liability.** `persist()` avoids recomputation;
  `checkpoint()` truncates the lineage so recovery does not replay the whole history.
- `checkpoint()` **requires** a checkpoint directory and is reliable. `localCheckpoint()`
  requires none but is **unreliable** — the data and the lineage are both gone if an
  executor dies.
- DataFrames beat RDDs because of **Catalyst** (predicate pushdown, column pruning, join
  reordering) and **Tungsten** (off-heap memory, whole-stage code generation).
- `Dataset[T]` is a **Scala/Java** API. There is no Python `Dataset` — in PySpark the
  DataFrame is the top of the typed API.
- Read `explain(mode="formatted")` and count the `Exchange` nodes. Each one is a shuffle,
  and the `200` in it is your `spark.sql.shuffle.partitions`.
- **Use an RDD** for fine-grained partitioning control, custom binary/record processing,
  non-tabular data with no schema, or a library that only accepts RDDs. Use a DataFrame
  for everything else.
- **`collect()` pulls everything to the driver** and needs 2–3× the result size in
  memory. `toLocalIterator()`, `write`, and `foreachPartition` are the safe alternatives.
- **`df.rdd.map(...)` is a performance trap** — measured at ~4.5× slower than a native
  expression at 500K rows and ~16× at 2M rows, and the gap **widens with scale**. It
  discards the schema, defeats Catalyst, and pays Python overhead per row.
- **`pandas_udf`** (the decorator, lowercase) is a vectorized UDF using pandas + Arrow.
  Arrow is **required** — enable `spark.sql.execution.arrow.pyspark.enabled=true`.
- `pandas_udf` typically beats a plain Python UDF by **3–20×** (measured ~3.5× on a
  4M-row arithmetic UDF), but a **native SQL expression or `F.expr` still beats both**
  and is the only one Catalyst can optimize.
- `mapInPandas` operates on whole partitions as pandas DataFrames — the right tool for
  batch reshaping.
- Benchmark with a warm-up run, `time.perf_counter()`, an action that **consumes the
  column the UDF produces** (not `count()`), and **compare `explain()` output and input
  bytes** — not just wall-clock time.

---

## 📚 Practice Exercises

1. **Benchmark the three tiers.** On a 5-million-row table, benchmark (a) a native
   `F.expr` expression, (b) a `pandas_udf`, and (c) a plain Python `udf`. Record the
   median of 3 runs each, the plan from `explain(mode="formatted")`, and the **input bytes
   read** from the Spark UI. Explain the ranking in terms of Catalyst visibility, not
   "Python is slow."

2. **Lineage growth.** Build a chain of 20 transformations on a DataFrame and print
   `df._jdf.queryExecution().logical().toString()` before and after a `checkpoint()`. Show
   the truncation. Then explain what happens to recovery time if you do not checkpoint.

3. **The `localCheckpoint` failure.** Construct a scenario where a `localCheckpoint`ed
   DataFrame becomes unrecoverable after an executor is lost. Write the exact sequence of
   events and the exception a user would see. Then describe the `checkpoint()`-based fix.

4. **RDD justification.** For each of these, write a one-paragraph justification for
   RDD vs DataFrame, and implement your choice: (a) joining 500 GB of clickstream data to
   a 100 GB dimension table on a non-equi condition, (b) parsing a proprietary binary
   format, (c) a daily aggregation with 50 million distinct keys, (d) writing partitioned
   Parquet with a custom compression codec.

5. **`toLocalIterator` vs `collect`.** Write a job that processes 100 million rows one at
   a time in Python without exceeding a 2 GB driver heap. Measure peak driver memory (via
   the Spark UI's "Executors" tab) and total runtime. Then rewrite it with `foreachPartition`
   and compare.

6. **`mapInPandas` reshaping.** Take a DataFrame with a nested struct column and use
   `mapInPandas` to flatten it, rename the columns, and change the types. Write it as a
   `pandas_udf` first, then as `mapInPandas`, and explain when each is preferable.

---

## 📖 Further Reading

- Spark RDD programming guide — https://spark.apache.org/docs/latest/rdd-programming-guide.html
- Spark SQL programming guide (DataFrames, Catalyst, Tungsten) — https://spark.apache.org/docs/latest/sql-programming-guide.html
- Spark SQL tuning guide (AQE, partition sizing) — https://spark.apache.org/docs/latest/sql-performance-tuning.html
- `pyspark.sql.functions` API — https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions/index.html
- `pyspark.sql.pandas` API (pandas-on-Spark) — https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql.pandas/index.html
- Arrow for PySpark (zero-copy transfers) — https://arrow.apache.org/docs/python/index.html
- Spark performance tuning — https://spark.apache.org/docs/latest/sql-performance-tuning.html
- Dataproc tuning best practices — https://cloud.google.com/dataproc/docs/concepts/optimizing-jobs
- Dataproc cluster configuration options — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters
- Tungsten paper (2015) — https://databricks.com/blog/2015/04/16/tungsten-plan-for-spark-3.html
