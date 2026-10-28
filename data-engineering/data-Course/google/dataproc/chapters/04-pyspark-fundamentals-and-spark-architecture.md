# 2.1 — PySpark Fundamentals & Spark Architecture

> **Section 2 · Spark Fundamentals · Lecture 2.1 · 24:38**

## 🎯 What you will learn

- The driver/executor model: who plans the job, who does the work, and how they talk
- The cluster manager layer, and how Dataproc replaces the YARN parts you never see
- How a logical plan becomes a DAG, stages, and tasks — and where the shuffle lands
- Why transformations are lazy, and what Catalyst actually does with your query
- The knobs that decide how fast your job runs: `shuffle.partitions`, executor memory, cores
- Reading and writing data correctly: schemas, formats, partitioning, and write modes

---

## 🧠 Concept

### The architecture in one picture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          DRIVER  (one per Spark application)               │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │  SparkSession  /  SparkContext                                      │  │
│   │      │                                                             │  │
│   │      ├──▶ User code  (your .py file)                                │  │
│   │      │                                                             │  │
│   │      ├──▶ Catalyst ──▶ Logical Plan ──▶ Optimized Logical Plan     │  │
│   │      │                                     │                       │  │
│   │      │                                     ▼                       │  │
│   │      │                            Physical Plan (DAG)                │  │
│   │      │                                     │                       │  │
│   │      ├──▶ DAGScheduler   ◀── splits the DAG into STAGES             │  │
│   │      │         │                                                     │  │
│   │      ├──▶ TaskScheduler  ◀── dispatches TASKS to executors          │  │
│   │      │         │                                                     │  │
│   │      └──▶ BlockManager  ◀── where cached/persisted data lives       │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                          ▲                          ▲                      │
│                     RPC / messages            RPC / messages               │
└──────────────────────────┼──────────────────────────┼──────────────────────┘
                           │                          │
              ┌────────────▼───────────┐   ┌──────────▼───────────┐
              │  EXECUTOR 1            │   │  EXECUTOR 2          │
              │  ├ Task thread 1       │   │  ├ Task thread 1     │
              │  ├ Task thread 2       │   │  ├ Task thread 2     │
              │  ├ Task thread 3       │   │  └ Task thread 3     │
              │  ├ Task thread 4       │   │                      │
              │  ├ Cache (MEMORY)       │   │  ├ Cache (MEMORY)    │
              │  └ Disk spill area      │   │  └ Disk spill area   │
              └────────────┬───────────┘   └──────────┬───────────┘
                           │                          │
                           └──────────┬───────────────┘
                                      ▼
                    ┌──────────────────────────────┐
                    │  STORAGE  (GCS / HDFS / disk) │
                    │  • shuffle files             │
                    │  • spill files               │
                    │  • checkpoint files           │
                    └──────────────────────────────┘
```

**The driver** runs your Python code. It is a JVM process with a Python gateway attached.
It does almost no data processing itself. Its jobs are:

1. Parse and analyze your code into a **logical plan**.
2. Hand the plan to the **optimizer** (Catalyst) to produce a physical plan.
3. Convert the physical plan into a **DAG of stages**.
4. Coordinate **task scheduling** across executors.
5. Collect results back to the driver when you call an action.

**The executors** are the JVM processes on the workers. Each one runs several **task
threads**, and each task thread processes one **partition** of data. Executors also hold the
**cache** (block manager) and the **disk spill** area.

### The cluster manager layer

Spark does not talk to workers directly. It talks to a **cluster manager**, which allocates
containers and reports back the resources of each worker.

| Cluster manager | Where it runs | Notes |
|-----------------|---------------|-------|
| `standalone` | Spark's own | Simple; rarely used in production |
| `yarn` | Hadoop | The classic Hadoop-on-cloud setup |
| `kubernetes` | K8s | The modern default; used by Dataproc Serverless |
| `local` | Your laptop | `master="local[*]"` — all threads in one JVM |

**On Dataproc (cluster mode)**, the workers are provisioned by Google, and Spark runs in
**YARN mode** on top of the Dataproc-managed Hadoop layer. From your code's point of view it
is `yarn`; the practical difference from self-managed YARN is that Google handles node
provisioning, JDK patching, and worker lifecycle.

⚠️ **On a Dataproc cluster, never set `master` in your code.** `SparkSession.builder.getOrCreate()`
without a `master` uses whatever the cluster is configured with (`yarn`). If you hardcode
`master="local[*]"` in a script that you later submit to Dataproc, **the entire job runs
inside the driver JVM on a single node** and ignores every worker you paid for. This is one
of the most common and most expensive mistakes in this course's topic area.

### The job lifecycle: DAG → Stages → Tasks → Shuffle

```
USER CODE
   │
   │  df = spark.read.parquet(path)          ← read is lazy, builds a plan
   │  df2 = df.filter(F.col("amount") > 100) ← transformation, lazy
   │  df3 = df2.join(dim, on="id")           ← shuffle boundary
   │  df3.write.mode("overwrite").parquet(out)  ← ACTION → everything fires
   ▼
DAGScheduler
   │
   ├── Parses the physical plan into a DAG of RDD dependencies
   │
   ├── Finds SHUFFLE BOUNDARIES (wide dependencies):
   │      • join         → hash-partition both sides by key
   │      • groupByKey / reduceByKey → repartition by key
   │      • window / orderBy → range partition
   │      • repartition / repartitionByRange
   │      • distinct / dropDuplicates
   │
   ├── Splits the DAG into STAGES at each shuffle boundary
   │      (a stage = everything between two shuffles)
   │
   └── For each stage, creates one TASK PER PARTITION
          (a task = one unit of work on one partition of one executor)
```

```
                 STAGE 0                      STAGE 1                    STAGE 2
             (map-side)                    (reduce-side)              (final)
            ┌───────────┐  shuffle      ┌───────────────┐           ┌───────────┐
 Parquet ──▶│  Filter   │──write──────▶│  Join + Group  │──write───▶│  Write    │
  Scan     │  Project  │   files      │  Aggregate     │  files    │  Parquet  │
            └───────────┘               └───────────────┘           └───────────┘
             4 partitions                  200 partitions            1 partition
             4 tasks                      200 tasks                 1 task
                                           ▲
                                           └── the shuffle: network transfer + sort
```

The **shuffle** is the expensive boundary. Spark writes the map-side output to disk (on GCS
or local disk), then the reduce-side tasks fetch exactly the partitions they need. Every
join and every aggregation pays this cost. Everything else is "narrow" — a map followed by a
filter stays in the same partition and the same task.

💡 **Stages are the unit of parallelism *and* the unit of recomputation.** If a stage's
input is lost, Spark re-runs the entire parent stage. This is why `persist()` on a DataFrame
that is read from GCS is one of the highest-value optimizations available.

### The two schedulers

| Component | Class | Responsibility |
|-----------|-------|----------------|
| **DAGScheduler** | `org.apache.spark.scheduler.DAGScheduler` | Turns a job's physical plan into stages and tasks. Decides which stage to run next, based on dependencies and data locality. Handles stage-level retries. |
| **TaskScheduler** | `org.apache.spark.scheduler.TaskScheduler` (with `LocalSchedulerBackend` / `ExecutorAllocationManager`) | Dispatches individual tasks to executors, tracks running/failed tasks, and retries failed tasks. |

They are separate because the DAGScheduler thinks in *dataflow* (stage 5 depends on stage 4)
while the TaskScheduler thinks in *resources* (which executor has a free core right now).

💡 **Data locality** is the DAGScheduler's superpower. If a stage's parent produced its
output in a partition that lives on executor 3, the task for that partition is scheduled on
executor 3. That turns a network transfer into a local disk read. This is why Spark
"moves computation to the data" without an explicit HDFS block-location API.

### SparkSession, SparkContext, and the entry point

```
SparkContext  (Scala: SparkContext)
   └── the core runtime: cluster manager connection, task scheduler,
       block manager, configuration, serializer
       └── SparkSession  (Scala: SparkSession)
              └── SQLContext / DataFrameReader / DataFrameWriter
              └── Catalog (metadata for tables, views, functions)
```

`SparkContext` is the low-level object. `SparkSession` is the high-level, user-facing wrapper
that was introduced in Spark 2.0 to unify DataFrame, SQL, and Dataset APIs on top of a single
entry point. In PySpark 3.5 you create a `SparkSession` and get the `SparkContext` from it.

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .master("local[*]")                       # omit on a cluster — uses yarn there
    .appName("MyApp")                         # shows in the Spark UI and Dataproc UI
    .config("spark.sql.shuffle.partitions", "200")
    .getOrCreate()
)

sc = spark.sparkContext        # the SparkContext underneath
print(sc.appName)              # 'MyApp'
print(sc.master)               # 'local[*]' or 'yarn'
print(sc.defaultParallelism)   # total cores across the cluster
```

- `.getOrCreate()` returns the **existing** session if one is already active, otherwise
  creates a new one. This is why it is safe to call in a notebook cell and in a `spark-submit`
  script.
- `SparkSession.getActiveSession()` returns the active session (or `None` in a fresh
  process). `SparkSession.builder.getOrCreate()` is the correct way to obtain one.
- `sc.getConf()` returns the `SparkConf` — every `config()` you set and every
  `--conf` you passed to `spark-submit` is visible there.

⚠️ **`SparkSession.getActiveSession()` returns `None` in a `spark-submit` script before you
create the session.** In Dataproc's `spark-submit`, the session is *not* pre-created. Always
build it explicitly:

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("MyApp").getOrCreate()
```

### Lazy evaluation: the single most important mental model

**Transformations are lazy. Actions are eager.**

| Kind | Examples | Runs when? |
|------|----------|-----------|
| **Transformation** (lazy) | `select`, `filter`, `where`, `groupBy`, `join`, `withColumn`, `drop`, `distinct`, `orderBy`, `limit`, `union`, `alias`, `rdd.map`, `rdd.filter` | Nothing happens. A plan is recorded. |
| **Action** (eager) | `count`, `show`, `collect`, `take`, `first`, `toPandas`, `write`, `foreach`, `toLocalIterator`, `rdd.collect`, `rdd.count` | The plan is executed and results are produced. |

```python
# NOTHING HAPPENS HERE. No file is read, no task is scheduled.
df = spark.read.parquet("gs://bucket/orders/")

# STILL NOTHING. This just adds a filter to the plan.
filtered = df.filter(F.col("amount") > 100)

# THIS RUNS EVERYTHING. The plan is optimized, turned into stages and tasks,
# and the results are returned to the driver.
filtered.show()
```

**Why is laziness good?** Three reasons:

1. **The optimizer sees the whole query.** Catalyst builds a *logical plan* — a tree of
   relational operators — and only then optimizes it. If `filter` executed immediately, the
   optimizer would never know to push that filter down into the Parquet scan, and it would
   have to read every row of every file first.
2. **Fusion.** A chain of transformations becomes a single physical operator. `filter` then
   `select` then `filter` is one compiled stage, not three passes over the data.
3. **Cheap re-planning.** You can build a complex pipeline and only pay for it at the end.

#### What Catalyst actually does

```
        YOUR CODE
            │
            ▼
   ┌─────────────────────┐
   │  UNRESOLVED LOGICAL │  ← names not yet bound to a schema
   │      PLAN           │
   └─────────┬───────────┘
             │  analysis
             ▼
   ┌─────────────────────┐
   │  RESOLVED LOGICAL   │  ← schema known, types resolved
   │      PLAN           │
   └─────────┬───────────┘
             │  optimization  ← ← ← THIS IS THE IMPORTANT PART
             ▼
   ┌─────────────────────┐
   │  OPTIMIZED LOGICAL  │
   │      PLAN           │
   └─────────┬───────────┘
             │  physical planning
             ▼
   ┌─────────────────────┐
   │  PHYSICAL PLAN      │  ← actual operators, actual byte layout
   │      (DAG)          │
   └─────────────────────┘
```

Catalyst's rule set includes, among others:

- **Predicate pushdown** — push a filter into the scan so fewer files/rows are read.
- **Column pruning** — drop unreferenced columns before the scan.
- **Constant folding** — evaluate `1 + 1` at plan time.
- **Join reordering** — reorder joins so the cheapest cardinality estimates come first.
- **Projection pushdown** — remove unnecessary `Project` operators.
- **Partition pruning** — use Parquet/ORC footers to skip entire row groups.
- **Common subexpression elimination** — reuse identical computed expressions.
- **Inlining and predicate pushdown through views** — expands `CREATE VIEW`.

**Critical detail: Catalyst cannot optimize what it cannot see.** A **Python UDF is an opaque
black box** to Catalyst. It cannot be pushed down, cannot be constant-folded, and blocks
predicate pushdown past it. This is why native SQL expressions and `F.expr` are so much
faster than Python UDFs — chapter 2.2 covers this in depth.

### `spark.sql.shuffle.partitions` — the most consequential config in Spark

Every shuffle produces `spark.sql.shuffle.partitions` output partitions on the reduce side.
The default is **200**.

```
Reduce-side task count = spark.sql.shuffle.partitions

Data size        Tasks        Result
────────────────────────────────────────────────────────────
10 rows          200          200 tasks, 199 of them do nothing.
                              Massive overhead: 200 × ~1 ms task
                              startup ≈ 200 ms of pure waste.

10 GB            200          ~50 MB per task. Reasonable.

1 TB             200          ~5 GB per task. Too big — spills to disk,
                              long GC pauses, possible OOM.

1 PB            200          Catastrophic. A single task handling 5 GB
                              of shuffled data cannot fit in memory.
```

The right value scales with data volume, not with cluster size:

```
Recommended ≈ (total shuffle data bytes) / (target bytes per task)

target bytes per task ≈ 128 MB – 256 MB   (a good default)

So: 100 GB shuffled / 200 MB ≈ 500 partitions
```

💡 **Rule of thumb:** keep the number of shuffle partitions to roughly 1–3× the number of
executor cores in the cluster, and never lower it below ~1 partition per core. Set it *per
job* with `.config(...)` — and remember that `spark.sql.shuffle.partitions` set on the
cluster is overridden by a `spark-submit --conf` and then by a builder `.config()`.

⚠️ **The "200 tasks for 10 rows" problem** is the single most common source of "why is my
tiny job taking 30 seconds". A 10-row `groupBy` still launches 200 reduce tasks, and each one
has to be scheduled, launched on an executor, and torn down. On a Dataproc cluster with
separate worker JVMs, each of those has JVM + Python worker startup cost. Fix it explicitly
for small data:

```python
spark.conf.set("spark.sql.shuffle.partitions", "8")
```

or in `spark-submit`:

```bash
gcloud dataproc clusters submit spark \
  --conf spark.sql.shuffle.partitions=8 \
  --jobs-file=jobs.json
```

### Executors, cores, and memory

| Config | Default | What it controls |
|--------|---------|------------------|
| `spark.executor.memory` | `1g` | JVM heap per executor. If the executor needs >4 GB, `spark.executor.memoryOverhead` (default `max(384m, 0.1 × executor.memory)`) must also grow. |
| `spark.executor.cores` | `1` | Task threads per executor. More cores = more concurrent tasks = more memory pressure. Usually 4–5. |
| `spark.executor.instances` | `2` | Executors per node. Dataproc sets this from your machine type. |
| `spark.driver.memory` | `1g` | Heap of the driver JVM. The driver holds the plan, the results of `collect()`, and all Python objects. |
| `spark.driver.maxResultSize` | `1g` | Hard limit on the size of a single result pulled to the driver. Exceeding it kills the job. |
| `spark.memory.fraction` | `0.6` | Share of executor heap reserved for execution vs. storage. |
| `spark.sql.shuffle.partitions` | `200` | Output partitions of every shuffle. |
| `spark.sql.adaptive.enabled` | `true` | **AQE** — coalesces shuffle partitions at runtime based on actual sizes. |
| `spark.sql.adaptive.coalescePartitions.enabled` | `true` | AQE: merge small shuffle partitions into fewer tasks. |
| `spark.sql.adaptive.skewJoin.enabled` | `true` | AQE: split skewed shuffle partitions in joins. |
| `spark.serializer` | `org.apache.spark.serializer.KryoSerializer` | Use Kryo, not Java serialization, for smaller and faster task payloads. |
| `spark.sql.execution.arrow.pyspark.enabled` | `false` | Enables Arrow for `toPandas()` and is **required** for `pandas_udf`. |

**The arithmetic that matters.** Total executor memory in a Dataproc cluster:

```
memory_per_executor = spark.executor.memory + spark.executor.memoryOverhead

total_cluster_memory = memory_per_executor × spark.executor.instances × num_workers

total_cores = spark.executor.cores × spark.executor.instances × num_workers
```

On Dataproc, `spark.executor.memory` is **not set directly** — it is derived from the
machine type. A `n1-standard-4` (4 vCPU, 15 GB) yields roughly:
`executor.memory = 8g`, `executor.cores = 4`, `executor.instances = 1`, `memoryOverhead ≈ 1.2g`.
💡 **The reliable way to see the real values** is to ask the running cluster, not to guess:

```python
sc = spark.sparkContext
print(sc.getConf().get("spark.executor.memory"))
print(sc.getConf().get("spark.executor.cores"))
print(sc.defaultParallelism)   # total task slots in the cluster
```

**Driver memory is the silent killer.** The driver is a single JVM. It holds:
- The query plan (small)
- The results of every `collect()`, `toPandas()`, and `groupBy().count()` aggregation
- Every Python object in a `foreach` closure

A `df.groupBy("customer_id").count()` on 50 million distinct keys returns 50 million rows to
the driver. That is not an aggregation problem — that is an out-of-memory problem. The
memory-safe alternatives are covered in chapter 2.2.

⚠️ **`spark.driver.memory` is a JVM heap setting and is not settable at runtime.** It must be
set at submission time:

```bash
gcloud dataproc clusters submit spark \
  --driver-memory=8g \
  --executor-memory-overhead=2g \
  --jobs-file=jobs.json
```

Setting it via `spark.conf.set()` after the session is created has **no effect** — the driver
JVM's heap is already fixed. Same for `spark.executor.memory`.

### RDDs: the original abstraction

An RDD (Resilient Distributed Dataset) is a distributed, immutable collection of objects,
partitioned across the cluster, with a lineage graph that lets Spark recompute lost data.

```python
rdd = sc.parallelize([1, 2, 3, 4, 5], numSlices=2)
rdd.getNumPartitions()   # 2
rdd.collect()            # [1, 2, 3, 4, 5]
```

| Creation API | Use |
|-------------|-----|
| `sc.parallelize(list, numSlices)` | From a local Python collection. The data is shipped to the executors. `numSlices` = number of parallel tasks. |
| `sc.textFile(path)` | From text files. One record per line. |
| `sc.hadoopFile(path, ...)` | From a Hadoop `InputFormat` (e.g. Avro, ORC via `newAPIHadoopFile`). |
| `df.rdd` | Convert a DataFrame to an RDD. **You lose the schema and the Catalyst optimizations.** |
| `sc.sequenceFile(path)` | From a Hadoop SequenceFile (Java-serialized). |

**RDD operations.**

```python
# Narrow transformations (no shuffle, stay in-partition)
rdd.map(lambda x: x * 2)
rdd.filter(lambda x: x % 2 == 0)
rdd.flatMap(lambda x: [x, x])
rdd.mapPartitions(fn)          # one call per partition, not per record

# Wide transformations (shuffle)
rdd.reduceByKey(fn)            # hash-partition by key, combine locally first
rdd.groupByKey()               # hash-partition by key, NO pre-combination
rdd.join(other)                # hash-join on key
rdd.repartition(n)             # round-robin repartition
rdd.partitionBy(n)             # explicit partitioner

# Actions
rdd.collect()                  # entire result to the driver
rdd.take(10)                   # first 10 (more efficient than collect for large data)
rdd.count()
rdd.first()
rdd.reduce(fn)
rdd.foreach(fn)                # runs on executors, no data returned
rdd.saveAsTextFile(path)       # writes directly, never through the driver
```

**`reduceByKey` vs `groupByKey` — the difference that matters.**

```
Data:  ("a", 1), ("b", 2), ("a", 3), ("b", 4), ("a", 5)

groupByKey:
   shuffle ALL (key, value) pairs  →  ("a",[1,3,5]), ("b",[2,4])
   then reduce on each group
   → memory = size of the ENTIRE group on one executor
   → 5 distinct keys is fine; 5 million rows for one key OOMs

reduceByKey:
   shuffle, but COMBINE LOCALLY first (map-side combine)
   → ("a", 1+3+5) after local combine, then shuffled
   → memory = O(number of keys) per partition, not O(group size)
```

💡 **Always prefer `reduceByKey`.** `groupByKey` exists because sometimes you genuinely need
the full group (e.g. to collect a list of values per key), and sometimes `reduceByKey`'s
commutative-and-associative requirement does not hold for your operation. But if you reach
for `groupByKey` when `reduceByKey` would work, you have written a job that will OOM under
exactly the conditions that matter.

**`collect()` vs `take()`** — both pull to the driver, but `take(n)` only needs enough
partitions to satisfy `n`, and Spark optimizes the job to stop early. `collect()` on a
10-billion-row RDD will kill the driver.

### `persist` / `cache` and storage levels

Because transformations are lazy, a DataFrame that is used three times is recomputed three
times unless you cache it.

```python
from pyspark import StorageLevel

df = spark.read.parquet("gs://bucket/orders/")   # expensive: GCS read + parse

df.persist(StorageLevel.MEMORY_AND_DISK)          # materialize it once
df.count()                                          # triggers the read; data is now cached
df.filter(F.col("amount") > 100).count()            # reuses the cache
```

**`cache()` is exactly `persist(StorageLevel.MEMORY_AND_DISK)`** in PySpark (in Scala the
default for `cache()` is `MEMORY_AND_DISK` too, since Spark 2.0). `persist()` with no
argument in PySpark also defaults to `MEMORY_AND_DISK`.

**The exact PySpark `StorageLevel` constants** (verified against Spark 3.5):

| PySpark constant | Printed as | Memory | Disk | Serialized | Notes |
|------------------|------------|--------|------|------------|-------|
| `MEMORY_ONLY` | `Memory Serialized 1x Replicated` | ✅ | ❌ | ✅ | Compressed in memory. Spills to disk if the block doesn't fit — and that spill is *not* stored. Recomputed on demand. |
| `MEMORY_AND_DISK` | `Disk Memory Serialized 1x Replicated` | ✅ | ✅ | ✅ | **The default, and the right default.** Only the parts that don't fit go to disk. |
| `MEMORY_AND_DISK_DESER` | `Disk Memory Deserialized 1x Replicated` | ✅ | ✅ | ❌ | Uncompressed objects in memory. Fastest to read; most memory-hungry. |
| `DISK_ONLY` | `Disk Serialized 1x Replicated` | ❌ | ✅ | ✅ | Only for very large cached data. |
| `DISK_ONLY_2` | `Disk Serialized 2x Replicated` | ❌ | ✅ | ✅ | Two copies on disk — survives one disk failure. |
| `DISK_ONLY_3` | `Disk Serialized 3x Replicated` | ❌ | ✅ | ✅ | Three copies. |
| `MEMORY_ONLY_2` | `Memory Serialized 2x Replicated` | ✅ | ❌ | ✅ | Two replicas — survives executor loss. |
| `MEMORY_AND_DISK_2` | `Disk Memory Serialized 2x Replicated` | ✅ | ✅ | ✅ | Two replicas of everything — survives executor loss. |
| `OFF_HEAP` | `Disk Memory OffHeap Serialized 1x Replicated` | ✅ (off-heap) | ✅ | ✅ | For datasets larger than the heap. Expert territory. |
| `NONE` | `Serialized 1x Replicated` | — | — | — | Don't cache; recompute every time. |

⚠️ **The PySpark names differ from the Scala names, and the difference is a trap.** Many
blog posts and older tutorials list Scala's constants — `MEMORY_ONLY_SER`,
`MEMORY_AND_DISK_SER`, and `MEMORY_AND_DISK` (deserialized). In **PySpark those do not
exist**:

```python
from pyspark import StorageLevel
StorageLevel.MEMORY_ONLY_SER        # AttributeError: type object 'StorageLevel'
                                    #   has no attribute 'MEMORY_ONLY_SER'
```

⚠️ **And note the surprise in `MEMORY_ONLY`:** in PySpark it is the **Serialized** level
(`Memory Serialized`), *not* the deserialized one. Scala's `MEMORY_ONLY` means
deserialized; PySpark's does not. The deserialized variant in PySpark is
`MEMORY_AND_DISK_DESER`. If you are porting Scala code, this is where it breaks.

💡 **In practice, you should use one of exactly three levels:**

| Use | Level |
|-----|-------|
| The default — you want the standard behaviour | `StorageLevel.MEMORY_AND_DISK` |
| You want the fastest reads and the data fits in memory | `StorageLevel.MEMORY_AND_DISK_DESER` |
| You want to survive executor loss and the data is huge | `StorageLevel.DISK_ONLY_2` or `MEMORY_AND_DISK_2` |

⚠️ **"Cache or you'll recompute" is a real, measurable, expensive mistake.** The classic
failure mode:

```python
# BROKEN: the parquet read happens TWICE
df = spark.read.parquet("gs://bucket/orders/")
df.filter(F.col("region") == "EMEA").count()
df.groupBy("customer_id").count().show()
#          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ re-reads and re-parses every file

# FIXED
df = spark.read.parquet("gs://bucket/orders/").persist()
df.count()   # materializes the cache exactly once
```

Note the `df.count()` after `persist()`. **Caching is lazy** — `persist()` only registers
the intent to cache. The data is actually materialized when the first action runs. If your
job ends right after `persist()` without an action, you cached nothing.

💡 **`unpersist()` when done.** Cached blocks occupy executor memory for the lifetime of the
application. In a long-running notebook session, cached data from a one-off analysis will
still be resident when your next (much larger) job runs, causing avoidable GC pressure and
spills. `df.unpersist()` or `spark.catalog.clearCache()`.

### Inspecting your data

```python
df.show(10, truncate=False)      # 10 rows, don't truncate strings
df.printSchema()                # the tree of column names and types
df.count()                      # row count — a full scan, but no data to the driver
df.columns                      # list of column names
df.dtypes                       # list of (name, type) tuples
df.describe()                   # summary stats for numeric columns
df.rdd.getNumPartitions()       # partition count of the underlying RDD
```

`df.show()` is an action that computes the *first* partition and formats it. It does not
read the whole dataset.

**`explain()` — read your plan before you run it.**

```python
df.explain()                    # simple string form
df.explain(mode="formatted")    # tree form, best for reading
df.explain(True)                # same as mode="formatted"
```

A formatted plan for a filter over a Parquet scan looks like:

```
== Physical Plan ==
AdaptiveSparkPlan (14)
+- == Final Plan ==
   * HashAggregate (11)
   +- * HashAggregate (9)
      +- * Filter (7)
         +- * ColumnarToRow (6)
            +- FileScan parquet s3://bucket/orders (5)
```

```
(5) FileScan parquet s3://bucket/orders [customer_id#12,amount#13,...]
Input [id#1,amount#13,...], grouped by [id#1]
(7) Filter [isnotnull(amount#13) AND (amount#13 > 100)]
(9) HashAggregate(keys=[id#1], functions=[partial_count(1)])
(11) HashAggregate(keys=[id#1], functions=[count(1)])
```

💡 **`explain()` is a free optimization tool.** It costs one plan build and no cluster
resources. If you see `Exchange` nodes you did not expect, you have a shuffle. If you see
`Filter` *above* a `FileScan` rather than pushed into it, your predicate is not reaching the
scan. If the plan says `PythonUDF` where you could use SQL, you have left performance on the
table.

### `toPandas()` and the driver-memory boundary

```python
pdf = df.toPandas()                          # entire DataFrame into driver memory

# Spark 3.5 has NO toPandas(n=...) — take a bounded sample FIRST:
sample = df.limit(100).toPandas()            # first 100 rows only
```

`toPandas()` **collects the whole result to the driver** and converts it. It uses Arrow when
`spark.sql.execution.arrow.pyspark.enabled=true` (much faster and more memory-efficient than
the legacy path), but it is still a full pull into a single process.

⚠️ **`toPandas(n=...)` does not exist in Spark 3.5.** The `n` argument was added in
**Spark 4.0**. Calling it on the Dataproc 2.2 image raises:

```
TypeError: PandasConversionMixin.toPandas() got an unexpected keyword argument 'n'
```

On Spark 3.5, bound the result **before** converting — with `limit()`, `sample()`, or a
filter — so the driver never receives more than you intended:

```python
df.limit(100).toPandas()
df.sample(withReplacement=False, fraction=0.01).toPandas()
df.filter(F.col("order_date") == "2026-01-01").toPandas()
```

💡 **A safer pattern that cannot blow up the driver** — iterate instead of collecting:

```python
# Memory-safe: one partition at a time, never all of it at once
for pdf in df.toLocalIterator():     # returns pandas DataFrames, one per partition
    process(pdf)
```

⚠️ **`toPandas()` is the most common cause of driver OOM in this ecosystem.** It is fine for
a 10 MB result. It is fatal for a 10 GB one. If the driver heap is 8 GB and your result is
9 GB, the job dies with `java.lang.OutOfMemoryError` or `MemoryError` in the Python worker
— even though the executors had plenty of room. The data has to fit in **one** process.

The rule: `toPandas()` is a **sampling and inspection** tool, not a pipeline tool.

### Reading data with `spark.read`

```python
df = spark.read.csv("gs://bucket/orders/")
df = spark.read.csv("gs://bucket/orders/part-*.csv")
df = spark.read.json("gs://bucket/events/")
df = spark.read.parquet("gs://bucket/orders/")
df = spark.read.orc("gs://bucket/orders/")
df = spark.read.avro("gs://bucket/events/")     # requires the spark-avro package
df = spark.read.text("gs://bucket/raw/")
df = spark.read.format("delta").load("gs://bucket/lake/")
```

`format("...").load(...)` is the general form and works for any DataSource.

**The CSV options that matter.**

| Option | Default | Notes |
|--------|---------|-------|
| `header` | `false` | First line is a header row. |
| `inferSchema` | `false` | Infer types by sampling. |
| `mode` | `PERMISSIVE` | `PERMISSIVE` (skip/tolerate bad rows), `FAILFAST` (raise on a malformed row), `DROPMALFORMED` (drop bad rows). |
| `nullValue` | `""` | The string that means null. ⚠️ With `inferSchema`/`schema`, `""` and `"NA"` are **not** null by default. |
| `multiLine` | `false` | Parse the whole file as one JSON value (JSON) or allow newlines inside quoted CSV fields. |
| `escape` | `\` | The escape character. |
| `encoding` | `UTF-8` | Character encoding. |
| `quote` | `"` | The quote character. |
| `dateFormat` | `yyyy-MM-dd` | Parse date strings with this pattern. |
| `timestampFormat` | `yyyy-MM-dd'T'HH:mm:ss[.SSS][XXX]` | Parse timestamp strings. |
| `comment` | — | Lines starting with this are skipped. |
| `enforceSchema` | `true` | Conform to the given schema; drop extra columns. |
| `delimiter` | `,` | Field separator. |
| `sampleRatio` | `1.0` | Fraction of rows to use for `inferSchema` (default 1.0 = all; lower it for speed). |

```python
df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .option("mode", "FAILFAST")
    .option("nullValue", "NULL")
    .option("dateFormat", "yyyy-MM-dd")
    .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
    .option("encoding", "UTF-8")
    .option("multiLine", True)
    .csv("gs://bucket/orders/")
)
```

⚠️ **`inferSchema` vs explicit `schema` — the tradeoff that bites in production.**

| | `inferSchema=True` | Explicit `StructType` |
|---|---|---|
| Setup effort | Zero | You write the schema |
| Correctness on new data | ⚠️ **Silently wrong.** A column of `int64` becomes `double` the first time it sees a decimal; a date column becomes `string` the first time it sees a malformed date. | Always correct. A value that doesn't fit raises a clear error (or becomes null with `PERMISSIVE`). |
| Schema drift | Absorbed silently — the shape of your data changes without anyone noticing | Caught immediately |
| Read speed | Requires an extra scan to sample | One pass |
| **Production verdict** | Exploratory work only | **Use this.** |

💡 **The classic `inferSchema` incident:** a CSV column `amount` is `int64` for 11 months.
One day a value arrives as `"12.50"` and the column silently becomes `double` for the whole
table. Every downstream `amount > 100` comparison, every integer cast, and every dashboard
changes behaviour — and nothing failed. Explicit schemas prevent this entirely.

### Defining a schema explicitly

```python
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, LongType,
    DoubleType, TimestampType, DateType, BooleanType, DecimalType,
)
from pyspark.sql import functions as F

orders_schema = StructType([
    StructField("order_id",    StringType(),    True),
    StructField("customer_id", StringType(),    True),
    StructField("region",      StringType(),    True),
    StructField("amount",      DecimalType(12, 2), False),
    StructField("quantity",    IntegerType(),   True),
    StructField("ordered_at",  TimestampType(), True),
    StructField("is_priority", BooleanType(),   True),
])

df = (
    spark.read
    .option("header", True)
    .schema(orders_schema)
    .mode("FAILFAST")
    .csv("gs://bucket/orders/")
)
```

`StructField(name, dataType, nullable)`. `nullable=False` makes the reader reject nulls
explicitly. `DecimalType(12, 2)` is the right type for money — `DoubleType` is binary
floating point and will lose cents (0.1 + 0.2 != 0.3 in IEEE 754).

### Writing data with `spark.write`

| Mode | Behavior | Use |
|------|----------|-----|
| `append` (default) | Add to existing data | Incremental loads |
| `overwrite` | Replace the target entirely | Full refresh |
| `errorifexists` | Fail if the target exists | **Safe default for pipelines** — a silent overwrite is a data-loss incident |
| `ignore` | Do nothing if the target exists | Idempotent job re-runs |

```python
df.write.mode("overwrite").parquet("gs://bucket/curated/orders/")
df.write.mode("overwrite").option("compression", "snappy").parquet("gs://bucket/curated/orders/")
df.write.mode("append").format("delta").save("gs://bucket/lake/orders/")
df.write.mode("overwrite").partitionBy("region", "order_date").parquet("gs://bucket/curated/orders/")
```

**Partitioning.** `partitionBy` writes separate directories per distinct value, and a
`partition=` predicate on read then prunes entire directories.

```
gs://bucket/curated/orders/region=EMEA/order_date=2026-01-01/part-0000.parquet
gs://bucket/curated/orders/region=EMEA/order_date=2026-01-02/part-0000.parquet
gs://bucket/curated/orders/region=APAC/order_date=2026-01-01/part-0000.parquet
```

```python
# Read only what you need — the filter is used to prune directories
df = spark.read.parquet("gs://bucket/curated/orders/").filter(F.col("order_date") == "2026-01-01")
```

⚠️ **Never partition on a high-cardinality column.** Partitioning by `order_id` or
`customer_id` creates millions of tiny directories — and on GCS, millions of objects with
milliseconds of latency each. The rule of thumb: **fewer than ~10,000 partitions per table**
and **at least ~100 MB of data per partition**. Good partition columns: `order_date`,
`region`, `event_type`. Bad: `user_id`, `session_id`, `transaction_id`.

⚠️ **Partitioning is not a free lunch.** Every partition is a separate file. Tiny files make
reads slow, make the GCS metadata API unhappy, and blow up the `ls` command. A table with
50 million 4 KB files is worse than one table with 500 large files.

**`coalesce` vs `repartition`.**

| | `coalesce(n)` | `repartition(n)` |
|---|---|---|
| Mechanism | Reduces the number of partitions **without a shuffle** | Full shuffle into `n` partitions |
| Distribution | May be uneven — the original partitioning is preserved | Even (round-robin) or by key (`repartition(col)`) |
| Data loss risk | ✅ **Yes** — a coalesce can lose data if upstream data is not uniformly distributed across partitions | No |
| Use when | You just want fewer output files, and you know the data is evenly spread | You need even distribution, or you need to repartition by key |

```python
# Fewer, larger output files — cheap
df.coalesce(10).write.mode("overwrite").parquet(path)

# Even distribution — costs a shuffle
df.repartition(10).write.mode("overwrite").parquet(path)

# Repartition by key — enables efficient downstream joins on that key
df.repartition(10, F.col("customer_id")).write.mode("overwrite").parquet(path)
```

💡 **`coalesce` on a DataFrame with skewed partitions is a data-loss bug waiting to
happen.** It reduces partitions by merging them, and it assumes roughly equal sizes. If
partition 0 has 10× the rows of the others, `coalesce(1)` can drop rows in some Spark
versions and configurations. Use `repartition` when in doubt — the shuffle is far cheaper
than lost data.

### Running locally vs on Dataproc

```python
# LOCAL — everything in one JVM on your machine
spark = SparkSession.builder.master("local[*]").appName("Local").getOrCreate()

# CLUSTER — master omitted; Spark uses `yarn` on Dataproc
spark = SparkSession.builder.appName("Cluster").getOrCreate()
```

| | `local[*]` | Dataproc cluster |
|---|---|---|
| Concurrency | One JVM, N threads | Many JVMs across many nodes |
| Realistic volume | Hundreds of MB | Terabytes |
| `parallelize` data | Actually shipped (locally, cheap) | Shipped over the network |
| Failure handling | None | Task retry, executor replacement |
| Cost | Free | Money |

💡 **Develop locally, validate on the cluster.** The classic "worked locally, failed on the
cluster" causes are: `collect()` on large data (fine locally, OOM on the cluster), an
accidental `master="local[*]"` in the submitted script, `parallelize` of a large list, and
Python UDFs whose dependencies are not installed on the workers.

### `spark-submit` basics

```bash
# Local
spark-submit \
  --master local[4] \
  --conf spark.sql.shuffle.partitions=8 \
  --py-files common.py \
  my_job.py --date 2026-01-01

# On Dataproc — the real path
gcloud dataproc clusters submit spark \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --cluster=my-cluster \
  --jars=gs://bucket/jars/avro-tools-1.11.0.jar \
  --py-files=gs://bucket/jobs/common.py \
  --driver-memory=8g \
  --executor-memory-overhead=2g \
  --properties=spark.sql.shuffle.partitions=200,spark.sql.adaptive.enabled=true \
  --jobs-file=jobs.json
```

The `jobs.json` file:

```json
[
  {
    "label": "etl-orders",
    "mainClass": "org.apache.spark.deploy.SparkSubmit",
    "args": ["gs://bucket/jobs/etl_orders.py", "--date", "2026-01-01"]
  }
]
```

Key flags:

| Flag | Purpose |
|------|---------|
| `--py-files` | Ship `.py`/`.zip` alongside the main script. **Required** for shared modules. |
| `--jars` | Ship JARs (Avro, custom connectors). |
| `--files` | Ship arbitrary files. |
| `--conf` / `--properties` | Set Spark configuration. |
| `--driver-memory` | Driver JVM heap. Must be set here, not at runtime. |
| `--executor-memory-overhead` | Off-heap / shuffle memory per executor. |
| `--py-files` + `spark.submit.pyFiles` | Same thing, Spark-side. |

⚠️ **`--py-files` and `--jars` are not optional on Dataproc.** If your script imports a
local module or uses a third-party library, it must be shipped — the workers do not have
your laptop's filesystem.

### Environment setup: the `pyspark` package vs cluster-provided Spark

There are two mutually exclusive ways to get PySpark:

**A. Use the cluster's Spark (the production path).**
Do **not** `pip install pyspark` on the cluster. The workers already have Spark installed
at `/usr/lib/spark` (or the Dataproc equivalent). Installing a second, different version
into the Python environment causes a version mismatch between the driver and the executors
and produces confusing `ClassNotFoundException` / `Py4JJavaError` failures.

```bash
# On a Dataproc cluster — nothing to install
gcloud dataproc clusters submit spark --jobs-file=jobs.json
```

**B. Install `pyspark` locally (the development path).**

```bash
# Python 3.9–3.11 work with Spark 3.5
pip install "pyspark==3.5.1" pandas pyarrow numpy
```

⚠️ **The `pyspark` pip package must match the cluster's Spark version.** A 3.5.0 driver
talking to 3.5.3 workers is usually fine; a 3.4 driver talking to 3.5 workers is a
liability. Pin it.

```python
import pyspark
print(pyspark.__version__)     # 3.5.1
```

And for the local-vs-cluster `master` switch, the standard pattern is:

```python
import sys
from pyspark.sql import SparkSession

def build_session(app_name):
    builder = SparkSession.builder.appName(app_name)
    if "spark-submit" not in sys.argv[0] and "--cluster" not in sys.argv:
        builder = builder.master("local[*]")
    return builder.getOrCreate()

spark = build_session("MyApp")
```

💡 **Java version matters.** Spark 3.5 supports Java 8, 11, and 17. Java 17 requires
`--add-opens` JVM flags for some operations; the Dataproc 2.2 image ships a supported JDK.
Locally, use Java 11 or 17 with the current 3.5.x patch release.

---

## 🛠️ Hands-On: A Complete Spark Session Tour

### Step 1 — Create the session and inspect the cluster

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
)

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("Lecture21-Fundamentals")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)

sc = spark.sparkContext
print("Spark version :", spark.version)
print("App name      :", sc.appName)
print("Master        :", sc.master)
print("Parallelism   :", sc.defaultParallelism)
print("Shuffle parts :", spark.conf.get("spark.sql.shuffle.partitions"))
print("Active session:", SparkSession.getActiveSession() is not None)
```

### Step 2 — Create sample data with an explicit schema

```python
orders_schema = StructType([
    StructField("order_id",    StringType(),    True),
    StructField("customer_id", StringType(),    True),
    StructField("region",      StringType(),    True),
    StructField("amount",      DoubleType(),    True),
    StructField("quantity",    IntegerType(),   True),
    StructField("ordered_at",  TimestampType(), True),
])

# NOTE: with an explicit schema, the values must already match the declared types.
# A TimestampType column needs a real datetime object, NOT a string.
from datetime import datetime

data = [
    ("o1", "c1", "EMEA", 120.50, 2, datetime(2026, 1, 1, 10, 0, 0)),
    ("o2", "c2", "APAC",  80.00, 1, datetime(2026, 1, 1, 11, 30, 0)),
    ("o3", "c1", "EMEA", 300.00, 5, datetime(2026, 1, 2, 9, 15, 0)),
    ("o4", "c3", "AMER",  45.25, 1, datetime(2026, 1, 2, 14, 45, 0)),
    ("o5", "c1", "APAC", 610.10, 8, datetime(2026, 1, 3, 16, 20, 0)),
]

df = spark.createDataFrame(data, schema=orders_schema)
df.printSchema()
df.show(truncate=False)
```

💡 **Why the strings failed.** With an explicit schema, PySpark **verifies** each Python
value against the declared type rather than converting it. A `str` is not a `TimestampType`,
so it raises:

```
PySparkTypeError: [CANNOT_ACCEPT_OBJECT_IN_TYPE]
`TimestampType()` can not accept object `2026-01-01T10:00:00` in type `str`.
```

Two fixes: pass a real `datetime.datetime` (as above), or read the timestamp as a string
column and convert it with `F.to_timestamp(col, "yyyy-MM-dd'T'HH:mm:ss")` — which is what
you'd do with real CSV data anyway, since a CSV file only ever contains text.

### Step 3 — Prove laziness

```python
# This registers a plan. NO I/O happens.
filtered = df.filter(F.col("amount") > 100)
print("Plan:", filtered._jdf.queryExecution().logical().toString()[:120], "...")

# This triggers it.
print("Count:", filtered.count())
```

Watch the Spark UI (`http://localhost:4040` in local mode) — the job only appears after
the action.

### Step 4 — Read the plan

```python
filtered.explain(mode="formatted")
```

You will see a `Filter` pushed down toward the scan, and the `HashAggregate` for `count`.

### Step 5 — Cache, and prove it prevents recomputation

```python
from pyspark import StorageLevel

df.persist(StorageLevel.MEMORY_AND_DISK)
df.count()                     # materializes the cache

# These two now reuse the cached blocks
df.filter(F.col("region") == "EMEA").count()
df.groupBy("region").count().show()

df.unpersist()
```

### Step 6 — Aggregate and inspect the shuffle

```python
agg = df.groupBy("region").agg(
    F.count("*").alias("orders"),
    F.sum("amount").alias("revenue"),
    F.avg("quantity").alias("avg_qty"),
).orderBy(F.desc("revenue"))

agg.show()
agg.explain(mode="formatted")
```

The `Exchange hashpartitioning(region#5, 200), ENSURE_REQUIREMENTS` node in the plan is the
shuffle. Change `spark.sql.shuffle.partitions` to `8` and re-run `explain` — the number in
the plan changes.

### Step 7 — RDD equivalents

```python
rdd = sc.parallelize([("EMEA", 120.50), ("APAC", 80.00), ("EMEA", 300.00)], numSlices=2)

print("Partitions:", rdd.getNumPartitions())

# reduceByKey does a map-side combine
print(rdd.reduceByKey(lambda a, b: a + b).collect())

# groupByKey does not
print(rdd.groupByKey().mapValues(lambda vs: sum(vs)).collect())

# take() is cheaper than collect() for large results
print(rdd.take(2))
```

### Step 8 — Write with partitioning, then read with pruning

```python
out = "/tmp/orders_by_region"
df.write.mode("overwrite").partitionBy("region").parquet(out)

# Read back and show the physical layout
import os
for root, _, files in os.walk(out):
    for f in files:
        print(os.path.join(root, f))

# Pruned read
pruned = (
    spark.read.parquet(out)
        .filter(F.col("region") == "EMEA")
)
pruned.explain(mode="formatted")   # look for PushedLocalFilters / partition pruning
```

### Step 9 — `toPandas` and its limits

```python
pdf = df.toPandas()
print(type(pdf), pdf.shape)
print(pdf.dtypes)

# Spark 3.5: bound the result BEFORE converting — there is no toPandas(n=...)
small = df.limit(3).toPandas()
print(small.shape)

# The memory-safe alternative: iterate one partition at a time
for row in df.toLocalIterator():
    print(row["order_id"], row["amount"])
```

### Step 10 — Submit it to Dataproc

```bash
# Package the script
gcloud dataproc jobs submit pyspark gs://YOUR_BUCKET/jobs/fundamentals.py \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --cluster=your-dataproc-cluster \
  --driver-memory=4g \
  --properties=spark.sql.shuffle.partitions=200
```

Remove the `.master("local[*]")` line before submitting, or the job will ignore every
worker on the cluster.

---

## 🔑 Key Takeaways

- The **driver** plans and coordinates; the **executors** execute tasks. The driver holds
  the plan and every result you pull to it.
- The **cluster manager** (YARN on Dataproc, K8s on Serverless) allocates containers.
  Never hardcode `master` in a script that will be submitted to a cluster.
- A job becomes a **DAG**, the DAGScheduler splits it at **shuffle boundaries** into
  **stages**, and each stage becomes one **task per partition**.
- The **shuffle** (join, groupBy, distinct, window) is the expensive boundary and the
  thing you optimize first.
- **Transformations are lazy; actions are eager.** Laziness is what lets Catalyst see and
  optimize the whole query, and it lets stages fuse.
- Catalyst builds a **logical plan**, optimizes it (predicate pushdown, column pruning,
  join reordering), then produces a **physical plan**.
- `spark.sql.shuffle.partitions` (default **200**) determines reduce-side task count. Ten
  rows still create 200 tasks unless you lower it.
- `spark.executor.memory`, `spark.executor.cores`, and `spark.executor.memoryOverhead`
  determine per-executor capacity. `spark.driver.memory` must be set at submit time and
  determines how big a result you can pull.
- **Prefer `reduceByKey` over `groupByKey`** — map-side combine bounds memory by key
  count instead of group size.
- **`persist()` is lazy** — you need an action after it to actually materialize. `cache()`
  is `MEMORY_AND_DISK`. `unpersist()` when done.
- **`toPandas()` pulls everything to the driver.** It is an inspection tool, not a
  pipeline tool. `toLocalIterator()` is the memory-safe alternative.
- **Explicit schemas over `inferSchema`** in production — inference silently changes types
  when new data arrives.
- Write modes: `append`, `overwrite`, `errorifexists` (safe default), `ignore`.
  `coalesce` reduces partitions without a shuffle (and can lose data); `repartition` shuffles.
- Don't `pip install pyspark` on the cluster; use the cluster's Spark and ship your code
  with `--py-files`.

---

## 📚 Practice Exercises

1. **Plan reading.** Build a DataFrame with a filter, a join, and a groupBy. Print
   `explain(mode="formatted")` for each intermediate step. Identify every `Exchange` node
   and explain, in one sentence each, what would break if you lowered
   `spark.sql.shuffle.partitions` to 2.

2. **The 200-task problem.** Create a 10-row DataFrame and run
   `df.groupBy("region").count()` with `spark.sql.shuffle.partitions` at 200, then at 4.
   Measure the wall-clock time of each with `time.time()`. Repeat with 1,000,000 synthetic
   rows. Explain why the gap between the two scenarios is so much larger than the data
   ratio suggests.

3. **Cache or recompute.** Time this pipeline with and without `persist()`:
   ```python
   df = spark.read.parquet(path)
   df.filter(F.col("region") == "EMEA").count()
   df.groupBy("customer_id").count().show()
   ```
   Use the Spark UI's "Jobs" and "Stages" tabs to show the difference in the number of
   tasks and total input bytes read.

4. **Schema drift.** Write a CSV where `amount` is `100` for the first 5 rows and `100.50`
   for row 6. Read it with `inferSchema=True` and print `printSchema()`. Then read it with
   an explicit `DecimalType(12, 2)` schema and print `printSchema()`. Explain what would
   have happened to a downstream `amount > 100` filter in production.

5. **Memory safety.** Write a job that computes a `groupBy("customer_id").count()` over a
   large dataset **without** using `collect()`. Then write the version that *does* use
   `collect()` and explain exactly which JVM will die first, and why.

6. **Configuration audit.** On a real Dataproc cluster, print
   `sc.getConf().get("spark.executor.memory")`, `spark.executor.cores`,
   `spark.executor.instances`, and `sc.defaultParallelism`. Compute the total cluster
   memory and total task slots. Then explain what happens to your job if you set
   `spark.conf.set("spark.executor.memory", "32g")` at runtime.

---

## 📖 Further Reading

- Apache Spark architecture overview — https://spark.apache.org/docs/latest/architecture.html
- Spark programming guide (RDDs) — https://spark.apache.org/docs/latest/rdd-programming-guide.html
- Spark SQL, DataFrames, and Datasets guide — https://spark.apache.org/docs/latest/sql-programming-guide.html
- Spark configuration reference — https://spark.apache.org/docs/latest/configuration.html
- Building Spark applications (Python) — https://spark.apache.org/docs/latest/api/python/index.html
- Dataproc submitting jobs — https://cloud.google.com/dataproc/docs/concepts/working-jobs
- Dataproc cluster configuration options — https://cloud.google.com/dataproc/docs/concepts/configuring-clusters
- Dataproc image versions and Spark versions — https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-image-versions
- spark-avro package — https://github.com/databricks/spark-avro
- Arrow for PySpark — https://arrow.apache.org/docs/python/index.html
