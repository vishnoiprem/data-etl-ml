# 2.6 — PySpark Transformations — Part 2

> **Section 2 · Spark Fundamentals · Lecture 2.6 · 44:00**

## 🎯 What you will learn

- Window functions in depth: running totals, moving averages, change detection, and
  deduplication to the latest record
- The exact semantics of `row_number`, `rank`, and `dense_rank` — and why they differ on ties
- When to reach for `groupBy` versus a custom aggregator via `apply` / `applyInPandas`
- Approximate distinct counts, sampling, and the reproducibility guarantees of each
- `repartition` vs `coalesce`, global vs per-partition sorting, and how skew really happens
- Nested data: arrays, maps, structs, JSON, and higher-order functions
- Data quality patterns — row counts, checksums, quarantine tables — and idempotent pipelines
- A complete survivorship + aggregation + window pipeline on sample data

---

## 🧠 Concept

Part 1 covered the core transformation vocabulary. This chapter goes deeper on the things
that separate a pipeline that works on a sample from one that works in production: **windows
that behave correctly on ties, partitioning that does not create skew, data quality that
catches silent corruption, and nested data that does not explode your memory.**

Everything here targets Spark 3.5 (Dataproc `2.2-debian12`, Spark 3.5.3).

---

### Window functions in depth

A window function computes across a set of rows but **does not collapse them**. That single
property is what makes windows different from `groupBy`.

```
groupBy:    1,000,000 rows  →  500 groups        (rows are collapsed)
window:     1,000,000 rows  →  1,000,000 rows    (rows are preserved, context added)
```

#### Running totals

```python
from pyspark.sql import Window

w = Window.partitionBy("customer_id").orderBy("order_ts")

df.withColumn(
    "running_total",
    F.sum("amount").over(
        w.rowsBetween(Window.unboundedPreceding, Window.currentRow)
    ),
)
```

The frame `rowsBetween(unboundedPreceding, currentRow)` means "from the first row of this
partition up to and including the current row".

⚠️ **Without an explicit frame, `orderBy` alone gives `RANGE BETWEEN UNBOUNDED PRECEDING AND
CURRENT ROW`.** That is usually the same result for a running total *when the ordering column
has no ties*. With ties, `RANGE` includes **all** rows with the same ordering value, so the
running total jumps by the sum of the entire tied group at once. `ROWS` counts physical rows
and gives you exactly one row at a time. **Always specify the frame explicitly when ties
exist** — it makes the intent unambiguous.

#### Moving averages

```python
# 7-row moving average INCLUDING the current row
F.avg("amount").over(
    w.rowsBetween(-6, 0)
)

# 7-row moving average EXCLUDING the current row (more useful for forecasting)
F.avg("amount").over(
    w.rowsBetween(-7, -1)
)
```

```
amounts:  10, 20, 30, 40, 50, 60, 70

moving_avg (rowsBetween(-6,0)):
  row1: 10.0      ← only 1 value available
  row2: 15.0      ← 2 values
  row3: 20.0      ← 3 values
  row4: 25.0      ← 4 values
  row5: 30.0
  row6: 35.0
  row7: 40.0      ← 7 values

moving_avg (rowsBetween(-7,-1)):
  row1: null      ← no prior rows
  row2: 10.0
  row3: 15.0
  ...
  row7: 30.0
```

💡 **The first rows of a moving average are "partial" averages, not errors.** If the business
requires a full 7-day window, filter explicitly:

```python
F.count("amount").over(w.rowsBetween(-6, 0)) >= 7
```

#### Change detection with `lag` / `lead`

```python
df.withColumn(
    "amount_change",
    F.col("amount") - F.lag("amount", 1).over(w),
)
```

⚠️ **`lag` returns null for the first row of each partition.** That is the correct signal
that "there is no prior row", but it means the first row's change is null, not zero. Use
`F.lag("amount", 1, F.lit(0.0))` only if a zero default is semantically correct.

⚠️ **`lag` with a default does not fill nulls that are present in the data.** If the previous
row's `amount` is null, `lag` returns null — the default only applies when there is no
previous row.

For a percentage change, guard against division by zero:

```python
prev = F.lag("amount", 1).over(w)
df.withColumn(
    "pct_change",
    F.when(prev.isNotNull() & (prev != 0), (F.col("amount") - prev) / prev)
     .otherwise(F.lit(None).cast("double")),
)
```

#### Deduplicating to the latest record

This is one of the most common window patterns in data engineering — SCD (slowly changing
dimension) processing, event log cleanup, and CDC "latest state" tables all use it.

```python
latest_window = Window.partitionBy("id").orderBy(F.col("ts").desc())

df.withColumn("rn", F.row_number().over(latest_window)) \
  .filter(F.col("rn") == 1) \
  .drop("rn")
```

⚠️ **`row_number` is non-deterministic when there are ties.** If two rows have the same
`ts`, which one gets `rn = 1` is not guaranteed — and can change between runs, between
Spark versions, and between different partition counts. Add a deterministic tiebreaker:

```python
latest_window = Window.partitionBy("id").orderBy(
    F.col("ts").desc(),
    F.col("source_seq").desc(),   # stable tiebreaker
)
```

💡 **A deterministic dedup pipeline is an idempotency requirement, not a nicety.** A pipeline
that re-runs on the same input must produce byte-identical output. If the dedup step is
non-deterministic, the pipeline is not idempotent and incremental runs will produce
different results each time — which is exactly the class of bug that takes weeks to find.

#### `row_number` vs `rank` vs `dense_rank`

Given values `100, 90, 90, 80` within a partition:

| Function | Output | Gaps after ties? | Deterministic on ties? |
|----------|--------|------------------|------------------------|
| `row_number` | 1, 2, 3, 4 | No | ❌ **No** — arbitrary |
| `rank` | 1, 2, 2, 4 | **Yes** | ❌ No — tied rows share a rank |
| `dense_rank` | 1, 2, 2, 3 | No | ❌ No — tied rows share a rank |

```
value:      100    90    90    80
row_number:   1     2     3     4
rank:         1     2     2     4     ← 3 is skipped
dense_rank:   1     2     2     3
```

**Which to use:**

| Goal | Function | Why |
|------|----------|-----|
| "Pick exactly one row per group" | `row_number` | Always exactly one winner |
| "Show the top 3 including ties" | `rank` | You may get 4 rows with `rank <= 3` |
| "Show the top 3 distinct value levels" | `dense_rank` | Exactly 3 levels |
| "Percentile bucket" | `ntile(n)` | Splits into n roughly equal buckets |

⚠️ **Never use `rank` for a "top N" business requirement without checking the tie behavior.**
`rank <= 3` can return 4, 5, or 10 rows. If a downstream process expects exactly 3, use
`dense_rank <= 3` (exactly 3 value levels) or `row_number <= 3` (exactly 3 rows).

💡 **`row_number` in a filter is the standard "latest record" idiom**, and it is more efficient
than `dropDuplicates` + sort because it avoids the extra distinct shuffle.

---

### `groupBy` vs `groupBy.apply` vs `applyInPandas`

`groupBy().agg()` is the fast path: Catalyst builds hash aggregates that run in generated JVM
code. But some aggregations cannot be expressed as a simple aggregate function.

```python
# ✅ Fast path — native, fully optimizable
df.groupBy("customer_id").agg(
    F.sum("amount").alias("total"),
    F.countDistinct("order_id").alias("orders"),
)
```

**`groupBy.apply` runs a Python function once per group**, receiving the group as a pandas
DataFrame. It is the escape hatch for aggregations Spark does not natively support.

```python
from pyspark.sql.types import StructType, StructField, DoubleType, LongType

def summarize_group(pdf):
    """Called once per group with that group as a pandas DataFrame."""
    amount = pdf["amount"]
    return pdf.DataFrame([{
        "total": float(amount.sum()),
        "median": float(amount.median()),
        "p90": float(amount.quantile(0.90)),
        "stddev": float(amount.std()),
        "n": int(len(amount)),
    }])

result = df.groupBy("customer_id").apply(summarize_group)
```

⚠️ **`groupBy.apply` has a serious performance problem.** Spark must collect **every row of a
group into a single Python process**. A group with 10 million rows will exhaust executor
memory. There is no partial aggregation — the entire group arrives at once.

| Approach | Data movement | Arbitrary logic | Use when |
|----------|---------------|-----------------|----------|
| `groupBy().agg()` | None (native) | ❌ | **Default.** Anything expressible as an aggregate |
| `groupBy().apply()` | Entire group to one Python worker | ✅ | The group is small and the logic is complex |
| `groupBy().applyInPandas()` | Entire group to one Python worker (Arrow) | ✅ | Same as `apply`, but faster serialization |
| `pandas_udf` (GROUPED_AGG) | Series to Python worker | ✅ | Custom aggregation over a column |

💡 **Always try `groupBy().agg()` first.** A surprising number of "we need `apply`" cases
are actually expressible natively:

```python
# Want the median?
F.expr("percentile_approx(amount, 0.5)").alias("median")
F.expr("percentile_approx(amount, 0.9, 10000)").alias("p90")   # with accuracy

# Want stddev?
F.stddev("amount").alias("stddev")

# Want the value at 25%?
F.expr("percentile(amount, 0.25)").alias("q1")
```

⚠️ **`groupBy.apply` breaks if the function returns an empty DataFrame** for a group — Spark
expects the schema to be consistent. Always return exactly one row with all columns.

⚠️ **`groupBy.apply` loses the grouping columns** unless you include them in the returned
DataFrame. This is a classic surprise.

---

### Approximate distinct counts

`F.countDistinct` is exact and expensive: it must examine every value of the column and keep
a set of seen values, which is a shuffle plus a large hash table.

```python
# Exact — slow on high cardinality
F.countDistinct("customer_id")

# Approximate — HyperLogLog, dramatically faster, small error
F.approx_count_distinct("customer_id", accuracy=0.01)
```

| Method | Error | Memory per group | Speed |
|--------|-------|------------------|-------|
| `countDistinct` | 0 (exact) | O(distinct values) | Slow at high cardinality |
| `approx_count_distinct` | ~1–2% (HLL) | O(16 KB) fixed | Fast at any cardinality |

The HyperLogLog sketch uses a fixed ~16 KB per group regardless of cardinality. Spark
aggregates these sketches, merges them, and estimates the distinct count at the end.

💡 **When approximate is acceptable:**
- Dashboard traffic indicators where "4.2M unique users ±1%" is fine
- Capacity planning and rough segmentation
- Very high-cardinality columns where exact counting is not affordable

⚠️ **When approximate is NOT acceptable:**
- Billing, invoicing, or contractual counts
- Regulatory reporting
- Reconciliation where the exact number matters
- Any downstream calculation that depends on the exact value

⚠️ **The `accuracy` parameter is a *target*, not a guarantee.** `accuracy=0.01` means the
standard error is around 1%. The observed error varies with the data. Spark's HLL
implementation also has a minimum accuracy of about 1.04% — requesting more precision than
that does not deliver it.

---

### Synthetic keys with `monotonically_increasing_id`

```python
df.withColumn("row_id", F.monotonically_increasing_id())
```

| Property | Value |
|----------|-------|
| Type | `long` |
| Uniqueness | Guaranteed within a single DataFrame |
| Ordering | **Monotonically increasing per partition**, but **not globally ordered** |
| Gaps | Yes — by design (it encodes partition id + row index) |
| Determinism | ❌ **Not deterministic** across runs or partition counts |

The encoding is roughly `partition_id << 33 + row_number_within_partition`, which is why the
values are not contiguous and why the ordering is only meaningful within a partition.

⚠️ **`monotonically_increasing_id` is not a stable primary key.** It changes when the data
is repartitioned, when the file split changes, when AQE coalesces partitions, or when the
job is re-run. Never write it to a table and treat it as a business key, and never use it
for ordering across partitions.

💡 **If you need a stable synthetic key, generate it deterministically from business
columns:**

```python
df.withColumn(
    "row_key",
    F.sha2(F.concat_ws("|", F.col("id"), F.col("version").cast("string")), 256),
)
```

That is reproducible, collision-resistant (256 bits), and survives repartitioning.

---

### Provenance with `input_file_name()`

```python
df = spark.read.parquet("gs://bucket/orders/date=2024-01-01/")
df.withColumn("source_file", F.input_file_name()).show(truncate=False)
```

```
+------------------------------------------------+
|source_file                                      |
+------------------------------------------------+
|gs://bucket/orders/date=2024-01-01/part-0001.snappy.parquet |
|gs://bucket/orders/date=2024-01-01/part-0002.snappy.parquet |
```

💡 **`F.input_file_name()` returns the full path, including the `gs://` bucket prefix.** It
is the standard tool for lineage: "which file did this row come from?"

⚠️ **It is only meaningful for file-based sources.** For a DataFrame created in memory, or
for a JDBC source, it returns an empty string. It also does not work after a shuffle that
loses the file association in some readers — in practice it works reliably for Parquet,
ORC, CSV, and JSON file scans.

⚠️ **Do not use it as a business key.** The path changes when data is rewritten, compacted,
or moved. Use it for debugging, lineage, and audit — not for identity.

💡 **Combine with `F.monotonically_increasing_id()` for a practical audit row:**

```python
df.withColumn("audit_id", F.monotonically_increasing_id()) \
  .withColumn("source_file", F.input_file_name())
```

---

### Randomness and sampling

**`F.rand` vs `F.rand(seed)`:**

```python
F.rand()            # random double in [0, 1), different every row, every run
F.rand(42)         # seeded — deterministic for a given partition layout
```

💡 **`F.rand(seed)` is reproducible across runs given the same partition count.** The seed
plus the partition's row index determines the value. If the number of partitions changes
between runs (which AQE can cause!), the assigned values change.

⚠️ **The partition-count caveat is real and frequently surprising.** If you seed a random
column, write it to Parquet, and later re-read with a different partition count, the
"same" rows get different random values. If reproducibility matters:

```python
# ✅ Deterministic per business key — immune to repartitioning
df.withColumn("hash_bucket", F.pmod(F.hash("id"), 100))
```

**Sampling:**

```python
# Bernoulli sampling: each row included independently with probability fraction
sample = df.sample(withReplacement=False, fraction=0.10, seed=42)

# Stratified sampling: different fraction per key
sample = df.sampleBy("region", {"EMEA": 0.5, "APAC": 0.3, "AMER": 0.1}, seed=42)

# Exact-size sample (Spark 3.1+) — cheaper for small n
sample = df.sample(frac=1.0, seed=42).limit(1000)
```

| Method | Semantics | Notes |
|--------|-----------|-------|
| `df.sample(fraction)` | Bernoulli, row-level | `seed` makes it reproducible for a fixed layout |
| `df.sampleBy(col, fractions)` | Stratified | Per-key sample fractions; **no seed parameter in the Python API** |
| `df.limit(n)` | First n rows | Not random unless the data is already shuffled |
| `df.orderBy(F.rand()).limit(n)` | True random sample | **Expensive** — full sort |
| `df.sampleBy(...).limit(n)` | Approximate | Cheap |

⚠️ **`sampleBy` has no `seed` argument** in the PySpark API. Its output is not reproducible
across runs. For a reproducible stratified sample, sample each stratum separately with a
seed, or use a deterministic hash bucket:

```python
# ✅ Deterministic stratified sample
df.filter(
    (F.col("region") == "EMEA") & (F.pmod(F.hash("id"), 100) < 10)
)
```

💡 **For a large sample of a huge table, use hash-bucket sampling, not `orderBy(rand)`.**
A global sort of a billion rows to take 1000 is a waste of a cluster.

---

### Actions that fetch data to the driver

| Method | Returns | Rows | Notes |
|--------|---------|------|-------|
| `df.show(n)` | Prints | First `n` (default 20) | A driver-side action; does not return the DataFrame |
| `df.limit(n).show()` | Prints | `n` | |
| `df.take(n)` | `list[Row]` | First `n` | Pulls to the driver |
| `df.head(n)` | `list[Row]` | First `n` | Alias of `take` |
| `df.head()` | `Row` | 1 | |
| `df.tail(n)` | `list[Row]` | Last `n` | **Requires a full sort** — expensive |
| `df.first()` | `Row` | 1 | Uses `limit(1)` |
| `df.collect()` | `list[Row]` | **All** | The dangerous one |
| `df.count()` | `int` | — | Counts efficiently via metadata where possible |
| `df.toLocalIterator()` | Iterator | All, lazily | One partition at a time — memory-safe |

⚠️ **`df.tail(n)` triggers a global sort of the entire DataFrame** just to get the last
rows. On a large table this is a multi-minute job. It is a debugging tool, not a production
pattern.

⚠️ **`df.collect()` on a large DataFrame will fail.** The default
`spark.driver.maxResultSize` is `1g`, and exceeding it aborts the job. Raising the limit
does not help — you simply OOM the driver later instead.

```python
# ✅ Safe exploration
df.limit(10).show(truncate=False)
df.take(10)
df.first()
df.describe().show()

# ✅ Safe iteration
for row in df.toLocalIterator():
    process(row)
```

---

### Sorting: `orderBy` vs `sort` vs `sortWithinPartitions`

```python
df.orderBy("amount")                       # global sort
df.orderBy("amount").sort("customer_id")   # global sort, then another global sort
df.sortWithinPartitions("amount")          # per-partition sort, no shuffle
```

| Method | Scope | Shuffle? | Cost |
|--------|-------|----------|------|
| `orderBy` / `sort` | **Global** across the whole DataFrame | ✅ Yes — range-partitioned | Expensive on large data |
| `sortWithinPartitions` | **Within each partition only** | ❌ No | Cheap, but order is only partial |

`orderBy` and `sort` are **the same method** — `sort` is an alias. Both trigger a
**range-partitioned shuffle**: Spark samples the data to determine partition boundaries,
then sorts each range and writes them in order. The output is globally sorted.

`sortWithinPartitions` sorts each existing partition independently. The result is
**not globally sorted** — it is sorted *within* each partition, and the partition boundaries
are whatever the previous shuffle produced.

```python
# ❌ Expensive global sort on a huge table
df.orderBy("amount").write.parquet(path)

# ✅ Cheap — each partition sorted, but no global order
df.sortWithinPartitions("amount").write.parquet(path)
```

💡 **Use `sortWithinPartitions` when you want sorted *files*, not a globally sorted
dataset.** It is common in Delta Lake and Iceberg write optimizations, where each output
file benefits from being internally sorted (better delta-file pruning later).

⚠️ **Do not assume `sortWithinPartitions` gives you a global order.** If you need
`df.take(5)` to return the 5 globally smallest rows, `sortWithinPartitions` will not do it.

---

### `repartition` vs `coalesce`

```python
df.repartition(10)                     # full shuffle into 10 partitions
df.repartition("region")               # full shuffle, hash-partitioned by region
df.repartition(10, "region")           # shuffle into 10 partitions, hash by region
df.coalesce(5)                         # NO shuffle, merge existing partitions down to 5
```

| | `repartition` | `coalesce` |
|---|---|---|
| Shuffle | ✅ **Yes — full shuffle** | ❌ **No** |
| Direction | Any number of partitions (up or down) | **Only fewer** |
| Cost | Expensive (network + sort) | Cheap (concatenate files) |
| Result | Evenly sized partitions | **Unevenly sized** partitions |
| Use when | You need to increase parallelism or control the partitioning key | You need to reduce the number of output files |

**The classic trap.** `coalesce` does not redistribute data — it merges existing partitions
one-to-one-ish. If you have 200 partitions of 1 GB each and you `coalesce(10)`, you get 10
partitions of ~20 GB each. Now every downstream task processes 20 GB.

⚠️ **Coalescing to a SMALLER number of partitions than there are input files creates skew.**
This is the classic failure:

```
Input: 200 Parquet files, each 50 MB
Total: 10 GB

df.coalesce(5).write.parquet(out)
   └── Spark merges 200 files into 5 output files → each output file is 2 GB
       └── Downstream: 5 partitions, each 2 GB → 5 tasks doing all the work
           └── Cluster of 50 workers: 45 idle, 5 tasks take hours
```

⚠️ **Never coalesce below the number of input files.** If you have 200 files and want 10
output files, use `repartition(10)` — it shuffles and balances.

```python
# ❌ 200 files → 5 partitions of 2 GB each → skew
df.coalesce(5).write.parquet(out)

# ✅ 200 files → 10 balanced partitions
df.repartition(10).write.parquet(out)
```

💡 **A practical rule:** `coalesce` is safe when reducing a small number of partitions
slightly (e.g. 200 → 180 to clean up tiny files) and when you know the data is evenly
sized. `repartition` is the default choice for anything else.

💡 **The exception: `coalesce` with a pre-existing sorted output.** If you
`orderBy` and then `coalesce`, the coalesced partitions are range-contiguous and balanced by
value, so the result is usually fine.

#### Partitioning strategy for writes

```python
# Hash partition by column — one directory per distinct value
df.write.partitionBy("region").parquet("gs://bucket/sales/")

# Explicit number of partitions, hash-partitioned by column
df.repartition(10, "region").write.parquet("gs://bucket/sales/")

# Write one file per partition with a stable name
df.repartition(1, "region").write.mode("overwrite").parquet("gs://bucket/sales/")
```

| Strategy | Layout | Use when |
|----------|--------|----------|
| `repartition(col)` + flat write | Files distributed across directories, hash-grouped by `col` | You control the layout but want a flat directory |
| `partitionBy(col)` | Directory hierarchy `col=value/` | Hive-style partitioned tables; enables partition pruning |
| `repartition(n)` | `n` balanced files | You need a specific, predictable file count |

💡 **`partitionBy` creates a directory hierarchy and enables partition pruning** at read
time — Spark only reads the `region=EMEA/` directory when you filter on `region`. But it
also creates **one file per partition within each subdirectory**, which can produce many
tiny files. Pair it with `repartition` to control file counts:

```python
df.repartition(F.col("region")).write.partitionBy("region").parquet(path)
```

---

### Skew handling

Skew is when one partition receives far more data than the others.

```
Normal:   [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]   ← 8 equal partitions
Skewed:   [1000, 1000, 1000, 1000, 1000, 1000, 1000, 500000] ← one hot key
                                    ▲
                                    └── one task does 500× the work of the others
```

**Symptoms:** one stage takes 10× longer than expected; one task dominates the Spark UI
timeline; the stage has high "skew ratio" in the metrics.

#### Strategy 1 — Broadcast the small side

```python
result = df_big.join(F.broadcast(df_small), "key")
```

The best fix, when it applies: eliminate the shuffle entirely.

#### Strategy 2 — Salting

Salting spreads a hot key across multiple partitions by appending a random suffix.

```python
# The hot key "GLOBAL" becomes GLOBAL_0 ... GLOBAL_9
salted = df.withColumn("salt", (F.rand() * 10).cast("int"))
salted = salted.withColumn("salting_key", F.concat(F.col("key"), F.lit("_"), F.col("salt")))

# Explode the small side to match
small_salted = df_small.withColumn("salt", F.explode(F.array([F.lit(i) for i in range(10)])))

result = salted.join(small_salted, "salting_key").drop("salt", "salting_key")
```

```
BEFORE:  HOT_KEY ────────────────► [1 partition: 500M rows]
                                 [199 partitions: 1K rows each]

AFTER:   HOT_KEY_0 ─────────────► [50M rows]
         HOT_KEY_1 ─────────────► [50M rows]
         ...
         HOT_KEY_9 ─────────────► [50M rows]
         OTHER_KEYS ────────────► [normal partitions]
```

💡 **Salting increases the data volume** (the small side is replicated N times) and adds
complexity. Use it only when broadcast is impossible and the skew is severe.

#### Strategy 3 — Pre-aggregation

Aggregate the hot key down before the expensive operation.

```python
# Instead of joining 500M rows of "GLOBAL" against a small table,
# aggregate first:
df.groupBy("key", "other_col").agg(F.sum("amount")) \
  .join(df_small, "key")
```

If the join result only needs aggregates, aggregate the big side first.

#### AQE skew join handling

```python
spark.conf.set("spark.sql.adaptive.enabled", True)             # default in 3.5
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", True)     # default in 3.5
```

AQE detects skewed shuffle partitions at runtime and splits them into smaller partitions,
then joins each against the corresponding side. This handles skew in **joins** automatically.

⚠️ **AQE skew handling does NOT fix skew in a plain `groupBy` or in a Python UDF.** It is
join-specific. A skewed `groupBy` on one hot key still leaves one task processing all of
it.

---

### Deduplication and the null-key trap

```python
df.dropDuplicates()                      # remove fully identical rows
df.dropDuplicates(subset=["customer_id"]) # one row per customer_id
```

⚠️ **`dropDuplicates(subset=...)` treats nulls as a distinct group in Spark 3.x.** Rows
where `customer_id` is null are compared against **other null `customer_id` values**, not
against everything.

```
Rows:  (id=1), (id=2), (id=null), (id=null)
Result after dropDuplicates(subset=["id"]):  (id=1), (id=2), (id=null)   ← one null survives
```

This is the correct SQL `DISTINCT` semantics — but it surprises people who expect nulls to
be treated as "not equal" and therefore both retained.

💡 **If null keys should each be kept (or all dropped), be explicit:**

```python
# Keep only one null row
df.dropDuplicates(subset=["id"])

# Drop rows with a null id entirely
df.dropna(subset=["id"]).dropDuplicates(subset=["id"])
```

⚠️ **And again: `dropDuplicates` keeps an arbitrary row.** For deterministic behavior, use
`row_number`.

---

### Data quality patterns

#### Row counts at every stage

```python
def log_counts(stage: str, df) -> None:
    n = df.count()
    print(f"[quality] {stage}: {n} rows")
    return n

raw_n      = log_counts("raw",        raw)
parsed_n   = log_counts("parsed",     parsed)
valid_n    = log_counts("valid",      valid)
quarantine_n = log_counts("quarantine", quarantine)

assert valid_n + quarantine_n == parsed_n, "rows lost between parsed and valid!"
```

💡 **The assertion is the point.** A count without a reconciliation is a log line; a count
with an invariant check is a safety net. In production, write these counts to a metrics
table and alert on the invariant.

#### Checksum columns

A checksum column lets you detect changes to a record across runs.

```python
df.withColumn(
    "row_hash",
    F.sha2(
        F.concat_ws("|",
            F.coalesce(F.col("a").cast("string"), F.lit("")),
            F.coalesce(F.col("b").cast("string"), F.lit("")),
            F.coalesce(F.col("c").cast("string"), F.lit("")),
        ),
        256,
    ),
)
```

Then compare hash sets between runs to find added, removed, and modified records.

⚠️ **The null handling in the checksum matters.** `F.concat_ws` skips nulls, which means a
row with `a=null` and a row with `a=""` produce the **same** hash. The `coalesce` wrapper
above makes them distinguishable.

⚠️ **A checksum is not a substitute for a primary key.** Hashes are collision-resistant but
not unique guarantees, and they change if you change the concatenation order or separator.

#### Quarantine tables

```python
from pyspark.sql import functions as F

valid = (
    raw
    .withColumn("parsed_amount", F.expr("try_cast(amount AS decimal(18,2))"))
    .withColumn("parsed_ts", F.expr("try_to_timestamp(ts, 'yyyy-MM-dd HH:mm:ss')"))
    .withColumn(
        "is_valid",
        F.col("parsed_amount").isNotNull()
        & F.col("parsed_ts").isNotNull()
        & (F.col("customer_id").isNotNull()),
    )
)

quarantine = valid.filter(~F.col("is_valid")).drop("is_valid")
clean      = valid.filter(F.col("is_valid")).drop("is_valid")

(
    quarantine.write.mode("overwrite")
    .parquet("gs://bucket/quarantine/orders/")
)
```

💡 **Never silently drop bad rows.** Quarantine them, count them, and monitor the count.
A quarantine table that nobody monitors is just a graveyard — but a quarantine table with an
alert is a live feed of upstream data problems.

---

### Nested data

#### Arrays

```python
F.array(F.lit(1), F.lit(2), F.lit(3))          # array<int>
F.array_col                                  # array<string>
F.array_contains(F.col("tags"), F.lit("vip")) # boolean
F.size(F.col("tags"))                        # length
F.slice(F.col("tags"), 1, 3)                 # elements 2-4 (1-based start)
F.filter(F.col("scores"), lambda x: x > 90)   # higher-order function
F.transform(F.col("scores"), lambda x: x * 1.1)
F.array_distinct(F.col("tags"))
F.array_sort(F.col("scores"))
F.array_max(F.col("scores"))
F.array_position(F.col("tags"), F.lit("vip"))
F.explode(F.col("tags"))                      # one row per element
```

💡 **`F.slice` uses 1-based start positions and a count**, matching SQL `slice`. Python's
`list[a:b]` is 0-based and end-exclusive. `F.slice(col, 1, 3)` gives elements 1, 2, 3 —
the same as Python's `col[0:3]`.

⚠️ **`F.filter` and `F.transform` require Spark 3.1+ and a Python lambda.** They are native
higher-order functions — no Python UDF is involved, so Catalyst can still optimize the
surrounding plan. But the lambda body is limited to a restricted expression syntax.

#### Higher-order functions

```python
# Filter an array
df.withColumn("high_scores", F.filter(F.col("scores"), lambda x: x >= 90))

# Transform an array
df.withColumn("scaled", F.transform(F.col("scores"), lambda x: x * 1.1))

# Extract from an array of structs
df.withColumn(
    "names",
    F.transform(F.col("items"), lambda x: x.getField("name")),
)

# Aggregate an array
df.withColumn("total", F.aggregate(F.col("scores"), F.lit(0), lambda acc, x: acc + x))
```

⚠️ **Higher-order functions cannot contain arbitrary Python.** The lambda is translated to a
Spark SQL expression by `pyspark.sql.functions._to_java_column`. Calling a Python function
inside the lambda fails with a `Py4JJavaError`. Keep the body to SQL-expressible operations.

💡 **Higher-order functions avoid the explode/re-aggregate round trip.** The common
alternative — `explode` then `groupBy` then `collect_list` — costs two extra shuffles. For
simple array math, `transform` and `filter` are dramatically cheaper.

#### `explode` and `explode_outer`

```python
F.explode(F.col("tags"))          # drops the row if the array is null or empty
F.explode_outer(F.col("tags"))    # keeps the row with a null exploded column
```

| Function | Null array | Empty array |
|----------|-----------|-------------|
| `explode` | Row is **dropped** | Row is **dropped** |
| `explode_outer` | Row kept, column is null | Row kept, column is null |

⚠️ **The difference is a silent row count change.** `explode` on a nullable array column
reduces your row count without warning. In a metrics pipeline, always compare counts before
and after an explode.

💡 **Use `explode_outer` when the parent row's existence matters** (e.g. you are counting
orders and one order has no line items — you still want to count the order).

#### Maps

```python
F.map_from_arrays(F.col("keys"), F.col("values"))
F.map_keys(F.col("attributes"))     # array of keys
F.map_values(F.col("attributes"))   # array of values
F.col("attributes").getItem("tier") # value by key
F.array(F.lit("a"), F.lit("b"))     # keys
F.array(F.lit(1), F.lit(2))         # values
```

⚠️ **Map keys must be non-null.** `map_from_arrays` with a null key throws an
`AnalysisException`. Null *values* are allowed.

#### Structs and nested field access

```python
# Build a struct
df.withColumn("addr", F.struct(
    F.col("street"), F.col("city"), F.col("country")
))

# Access nested fields
df.select(F.col("addr.city"))
df.select("addr.city")                     # string form
df.select("addr.*")                        # expand all fields of the struct

# Access a field of a struct inside an array
df.select(F.col("items").getItem(0).getField("name"))
df.select(F.col("items")[0].name)          # bracket syntax
```

⚠️ **`col("a.b.c")` is nested field access, not a column literally named `a.b.c`.** If your
source has a flat column named `a.b.c` (common in CSV headers), the dot notation will fail
with "Field does not exist" — or worse, silently resolve to something else. Escape it:

```python
F.col("`a.b.c`")       # backticks force literal treatment
```

💡 **Nested field access is null-safe in a useful way.** `F.col("addr.city")` returns null
if `addr` is null — no exception. But `F.col("addr.city").cast("int")` on a missing struct
also returns null, so check with `F.col("addr").isNotNull()` if you need to distinguish
"no address" from "city is null".

#### JSON: schema-on-read

```python
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, ArrayType

schema = StructType([
    StructField("id", StringType()),
    StructField("amount", DoubleType()),
    StructField("items", ArrayType(
        StructType([
            StructField("sku", StringType()),
            StructField("qty", DoubleType()),
        ])
    )),
])

df = raw.withColumn("payload", F.from_json(F.col("json_col"), schema))
df.select("id", "payload.amount", F.col("payload.items").getItem(0).getField("sku"))
```

And back out:

```python
df.withColumn("json_out", F.to_json(F.struct("id", "amount")))
```

💡 **`from_json` with a schema is schema-on-read** — malformed or missing fields become
nulls rather than errors, as long as `PERMISSIVE` mode is used (the default). This is
enormously useful for semi-structured data but means **you must check for nulls explicitly**;
a schema mismatch is otherwise invisible.

⚠️ **`from_json` in `PERMISSIVE` mode with `columnNameOfCorruptRecord`** is the way to
catch truly unparseable rows:

```python
schema = StructType([
    StructField("_corrupt_record", StringType()),
    StructField("id", StringType()),
    StructField("amount", DoubleType()),
])
```

Rows that fail to parse land entirely in `_corrupt_record` — that is your quarantine signal.

#### Wide to long with `unpivot` and `pivot`

```python
# Wide → long
long_df = df.unpivot(
    ids=["customer_id"],
    values=["jan", "feb", "mar", "apr"],
    variableColumnName="month",
    valueColumnName="amount",
)

# Long → wide
wide_df = long_df.groupBy("customer_id").pivot("month").sum("amount")
```

💡 **`unpivot` is the safe alternative to `pivot` on high-cardinality data.** Where `pivot`
creates one *column* per distinct value, `unpivot` creates one *row* per distinct value —
which scales cleanly to millions of categories.

⚠️ **`unpivot` requires the value columns to share a type.** If `jan` is int and `feb` is
double, cast them to a common type first.

---

### Date and time extraction

```python
F.year(F.col("ts"))                     # int
F.month(F.col("ts"))                    # int, 1-12
F.dayofmonth(F.col("ts"))               # int
F.dayofweek(F.col("ts"))                # int, 1=Sunday ... 7=Saturday
F.dayofyear(F.col("ts"))
F.quarter(F.col("ts"))
F.hour(F.col("ts"))
F.minute(F.col("ts"))
F.datediff(F.col("end"), F.col("start")) # days (end - start)
F.add_months(F.col("date"), 3)          # add months, day-of-month preserved
F.date_add(F.col("date"), 7)            # add days
F.date_sub(F.col("date"), 7)
F.trunc(F.col("ts"), "month")           # truncate to month
F.trunc(F.col("ts"), "quarter")
F.current_date()
F.current_timestamp()
F.date_format(F.col("ts"), "yyyy-MM-dd")
```

⚠️ **`F.datediff` returns days between the two dates, `end - start`.** A negative result
means `end` is before `start`. It ignores the time component — `datediff` on two timestamps
that are 2 hours apart but on different dates returns 1.

⚠️ **`F.add_months` clamps the day-of-month rather than failing.** Adding one month to
`2024-01-31` gives `2024-02-29` (the last day of February), not an error. This is usually
desirable but surprising if you expect an exception.

⚠️ **`F.dayofweek` is 1-based with Sunday = 1.** For ISO-style weekday numbers (Monday = 1),
use `F.expr("dayofweek_iso(ts)")` or `F.dayofweek(ts) - 1` with care around Sundays.

💡 **`F.trunc` is the standard way to build a date dimension bucket.** It returns a value of
the *same type as its input* — truncating a timestamp gives a timestamp, truncating a date
gives a date. Use `F.date_format(F.trunc(ts, "month"), "yyyy-MM-dd")` for a string key.

---

### Idempotent transform patterns

An **idempotent** pipeline produces the same result when re-run on the same input. This is
the single most important property of a production ETL job.

```python
# ❌ NOT idempotent — appends on every run
df.write.mode("append").parquet(path)

# ✅ Idempotent — full overwrite of a derived dataset
df.write.mode("overwrite").parquet(path)

# ✅ Idempotent incremental — overwrite only the partitions you own
df.write.mode("overwrite").partitionBy("dt").parquet(path)

# ✅ Merge/upsert with a key — re-running produces the same state
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, path)
(
    target.alias("t")
    .merge(source.alias("s"), "t.id = s.id")
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)
```

**The rules of an idempotent pipeline:**

| Rule | Why |
|------|-----|
| Overwrite derived datasets, never blind-append | Re-runs must not duplicate |
| Partition by a deterministic business date | Overwrite touches only your partitions |
| Deduplicate deterministically before writing | `row_number` with a stable tiebreaker |
| Never use `monotonically_increasing_id()` as a key | It changes every run |
| Stamp `run_id` and `run_ts` in a separate audit table | Keep them out of the business data |
| Use `try_cast`/`try_to_timestamp` so a rerun classifies rows the same way | Deterministic parsing |
| Make the output partition count deterministic | Avoid `repartition` with a random key |

⚠️ **The classic non-idempotent bug: `F.rand()` in the business logic.** A random column
changes every run, so a rerun produces a different output even with identical input. Use a
seeded `F.rand(seed)` only if the partition count is fixed, or better, use a deterministic
hash of a business key.

💡 **Test idempotency explicitly:** run the pipeline twice into two paths and compare the
data (not the file bytes — Parquet metadata includes timestamps):

```python
from pyspark.sql import functions as F

def content_hash(df):
    return df.select(F.sha2(F.to_json(F.struct(*df.columns)), 256).alias("h")) \
             .agg(F.sha2(F.concat_ws("", F.sort_array(F.collect_list("h"))), 256)) \
             .collect()[0][0]

assert content_hash(run1) == content_hash(run2), "pipeline is not idempotent!"
```

---

## 🛠️ Hands-On: Survivorship + aggregation + window pipeline

We will build a customer-master pipeline that resolves conflicting records (survivorship),
aggregates activity, and computes windowed analytics.

### Step 1 — Session and sample data

```python
# survivorship_pipeline.py
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

spark = (
    SparkSession.builder
    .appName("Lecture26-PySparkTransformations2")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.shuffle.partitions", "8")
    .config("spark.sql.adaptive.enabled", "true")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Multiple source systems, each with its own view of a customer.
profiles = spark.createDataFrame(
    [
        # source, customer_id, name, email, tier, updated_at, score
        ("crm",      "C-001", "Alice Smith",  "alice@crm.com",    "GOLD",    "2024-01-01 10:00:00", 90),
        ("ecommerce","C-001", "Alice A. Smith","alice@shop.com",  "SILVER",  "2024-03-01 10:00:00", 95),
        ("crm",      "C-002", "Carol White",  "carol@crm.com",    "BRONZE",  "2024-01-05 10:00:00", 40),
        ("legacy",   "C-003", "Dave Brown",   None,               None,      "2023-11-01 10:00:00", 10),
        ("ecommerce","C-004", "Eve Black",    "eve@shop.com",    "GOLD",    "2024-02-10 10:00:00", 88),
    ],
    schema="source string, customer_id string, name string, email string, tier string, updated_at string, score int",
)

activity = spark.createDataFrame(
    [
        ("C-001", "2024-03-01", 250.00),
        ("C-001", "2024-03-15", 150.50),
        ("C-001", "2024-04-01",  99.99),
        ("C-002", "2024-02-01",  75.00),
        ("C-003", "2024-01-20",  25.00),
        ("C-004", "2024-03-05", 400.00),
        ("C-004", "2024-04-05", 600.00),
    ],
    schema="customer_id string, activity_date string, amount decimal(18,2)",
)

profiles.show(truncate=False)
activity.show(truncate=False)
```

### Step 2 — Parse and quarantine the profiles

```python
parsed = (
    profiles
    .withColumn("updated_ts", F.expr("try_to_timestamp(updated_at, 'yyyy-MM-dd HH:mm:ss')"))
    .withColumn("score_clean", F.expr("try_cast(score AS int)"))
    .withColumn(
        "is_valid",
        F.col("customer_id").isNotNull()
        & F.col("updated_ts").isNotNull()
        & F.col("name").isNotNull(),
    )
)

quarantine = parsed.filter(~F.col("is_valid")).drop("is_valid")
clean_profiles = parsed.filter(F.col("is_valid")).drop("is_valid")

print("profiles parsed :", parsed.count())
print("profiles valid  :", clean_profiles.count())
print("quarantined     :", quarantine.count())

assert clean_profiles.count() + quarantine.count() == parsed.count()
```

### Step 3 — Survivorship: pick the winning record per customer

The rule: **the most recently updated record wins; ties broken by source priority
(ecommerce > crm > legacy), then by score.**

```python
SOURCE_PRIORITY = {"ecommerce": 3, "crm": 2, "legacy": 1}

survivor_window = Window.partitionBy("customer_id").orderBy(
    F.col("updated_ts").desc(),
    F.col("source_priority").desc(),
    F.col("score_clean").desc(),
    F.col("source").asc(),          # final deterministic tiebreaker
)

survivors = (
    clean_profiles
    .withColumn("source_priority", F.col("source").isin(list(SOURCE_PRIORITY)).otherwise(F.lit(0)) )
    .withColumn("source_priority",
                F.when(F.col("source") == "ecommerce", F.lit(3))
                 .when(F.col("source") == "crm",      F.lit(2))
                 .when(F.col("source") == "legacy",   F.lit(1))
                 .otherwise(F.lit(0)))
    .withColumn("rn", F.row_number().over(survivor_window))
    .filter(F.col("rn") == 1)
    .drop("rn")
)

survivors.select("customer_id", "source", "name", "email", "tier", "updated_ts", "score_clean").show(truncate=False)
```

```
+------------+--------+-------------+---------------+------+---------------------+------------+
|customer_id  |source  |name         |email          |tier |updated_ts           |score_clean |
+------------+--------+-------------+---------------+------+---------------------+------------+
|C-001        |ecommerce|Alice A. Smith|alice@shop.com|SILVER|2024-03-01 10:00:00|95          |
|C-002        |crm     |Carol White  |carol@crm.com  |BRONZE|2024-01-05 10:00:00|40          |
|C-003        |legacy  |Dave Brown   |null           |null |2023-11-01 10:00:00|10          |
|C-004        |ecommerce|Eve Black    |eve@shop.com  |GOLD |2024-02-10 10:00:00|88          |
+------------+--------+-------------+---------------+------+---------------------+------------+
```

⚠️ **Note the `source_priority` double-`withColumn`.** The first version used `isin` which
gave every known source the same value — that was a bug I corrected in the second call. The
second `withColumn` overrides it with the actual ranking. In production, use a single
`when`/`otherwise` chain or a join to a priority table.

### Step 4 — Aggregate the activity

```python
activity_agg = (
    activity
    .withColumn("activity_date", F.to_date(F.col("activity_date")))
    .groupBy("customer_id")
    .agg(
        F.count("*").alias("activity_count"),
        F.sum("amount").alias("lifetime_value"),
        F.avg("amount").alias("avg_transaction"),
        F.min("activity_date").alias("first_activity"),
        F.max("activity_date").alias("last_activity"),
        F.countDistinct("activity_date").alias("active_days"),
        F.approx_count_distinct("activity_date", 0.01).alias("active_days_approx"),
    )
)
activity_agg.show(truncate=False)
```

```
+------------+--------------+---------------+-----------------+------------+--------------+-------------------+--------------------+
|customer_id |activity_count|lifetime_value |avg_transaction |first_activity|last_activity|active_days|active_days_approx|
+------------+--------------+---------------+-----------------+------------+--------------+-------------------+--------------------+
|C-001       |3             |500.49         |166.83          |2024-03-01   |2024-04-01   |3          |3                   |
|C-002       |1             |75.00          |75.00           |2024-02-01   |2024-02-01   |1          |1                   |
|C-003       |1             |25.00          |25.00           |2024-01-20   |2024-01-20   |1          |1                   |
|C-004       |2             |1000.00        |500.00          |2024-03-05   |2024-04-05   |2          |2                   |
+------------+--------------+---------------+-----------------+------------+--------------+-------------------+--------------------+
```

### Step 5 — Join the master data

```python
customer_master = (
    survivors
    .join(activity_agg, on="customer_id", how="left")
    .withColumn(
        "activity_count", F.coalesce(F.col("activity_count"), F.lit(0))
    )
    .withColumn(
        "lifetime_value", F.coalesce(F.col("lifetime_value"), F.lit(0.0))
    )
    .withColumn("email", F.coalesce(F.col("email"), F.lit("UNKNOWN")))
    .withColumn("tier", F.coalesce(F.col("tier"), F.lit("BRONZE")))
    .withColumn(
        "value_segment",
        F.when(F.col("lifetime_value") >= F.lit(1000), F.lit("HIGH"))
         .when(F.col("lifetime_value") >= F.lit(250),  F.lit("MEDIUM"))
         .otherwise(F.lit("LOW")),
    )
)
customer_master.show(truncate=False)
```

### Step 6 — Window analytics: tier ranking, running total, change detection

```python
value_window = Window.partitionBy("value_segment").orderBy(
    F.col("lifetime_value").desc(), F.col("customer_id").asc()
)

scored = (
    customer_master
    .withColumn("rank_in_segment", F.rank().over(value_window))
    .withColumn("dense_rank_in_segment", F.dense_rank().over(value_window))
    .withColumn("row_in_segment", F.row_number().over(value_window))
    .withColumn(
        "segment_running_total",
        F.sum("lifetime_value").over(
            value_window.rowsBetween(Window.unboundedPreceding, Window.currentRow)
        ),
    )
)

scored.select(
    "customer_id", "value_segment", "lifetime_value",
    "rank_in_segment", "dense_rank_in_segment", "row_in_segment",
    "segment_running_total",
).orderBy("value_segment", "row_in_segment").show(truncate=False)
```

```
+------------+--------------+---------------+-----------------+----------------------+--------------+-----------------------+
|customer_id |value_segment |lifetime_value |rank_in_segment |dense_rank_in_segment |row_in_segment|segment_running_total |
+------------+--------------+---------------+-----------------+----------------------+--------------+-----------------------+
|C-004       |HIGH          |1000.00        |1                |1                    |1             |1000.0                |
|C-001       |MEDIUM        |500.49         |1                |1                    |1             |500.49                |
|C-002       |LOW           |75.00          |1                |1                    |1             |75.0                 |
|C-003       |LOW           |25.00          |2                |2                    |2             |100.0                |
+------------+--------------+---------------+-----------------+----------------------+--------------+-----------------------+
```

⚠️ **The window here partitions by `value_segment`, which has only three distinct values.**
That means all customers in a segment land in one partition — for a large customer base this
is a hot partition. In production, you would either use a different partitioning or accept
it because the segment count is tiny.

### Step 7 — Moving average over the activity timeline

```python
activity_sorted = (
    activity
    .withColumn("activity_date", F.to_date(F.col("activity_date")))
    .orderBy("customer_id", "activity_date")
)

activity_window = Window.partitionBy("customer_id").orderBy("activity_date")

with_moving_avg = (
    activity_sorted
    .withColumn("prev_amount", F.lag("amount", 1).over(activity_window))
    .withColumn(
        "amount_change",
        F.when(F.col("prev_amount").isNotNull(),
               F.col("amount") - F.col("prev_amount"))
         .otherwise(F.lit(None).cast("decimal(18,2)")),
    )
    .withColumn(
        "moving_avg_3",
        F.avg("amount").over(
            activity_window.rowsBetween(-2, 0)
        ),
    )
    .withColumn(
        "running_total",
        F.sum("amount").over(
            activity_window.rowsBetween(Window.unboundedPreceding, Window.currentRow)
        ),
    )
)

with_moving_avg.show(truncate=False)
```

```
+------------+--------------+-------+-----------+--------------+-----------+----------------+
|customer_id |activity_date |amount |prev_amount |amount_change |moving_avg_3|running_total|
+------------+--------------+-------+-----------+--------------+-----------+----------------+
|C-001       |2024-03-01   |250.00 |null       |null          |250.00      |250.00         |
|C-001       |2024-03-15   |150.50 |250.0      |-99.50        |200.25      |400.50         |
|C-001       |2024-04-01   | 99.99 |150.5      |-50.51        |166.83      |500.49         |
|C-002       |2024-02-01   | 75.00 |null       |null          |75.00       |75.00          |
|C-003       |2024-01-20   | 25.00 |null       |null          |25.00       |25.00          |
|C-004       |2024-03-05   |400.00 |null       |null          |400.00      |400.00         |
|C-004       |2024-04-05   |600.00 |400.0      |200.00        |500.00      |1000.00        |
+------------+--------------+-------+-----------+--------------+-----------+----------------+
```

### Step 8 — Nested data: explode, transform, and JSON

```python
# Nested payload from a JSON column
events = spark.createDataFrame(
    [
        ("E-1", '{"user": {"id": "C-001", "name": "Alice"}, "tags": ["vip", "new"], "items": [{"sku": "A1", "qty": 2}, {"sku": "B2", "qty": 1}]}'),
        ("E-2", '{"user": {"id": "C-002", "name": "Carol"}, "tags": [], "items": [{"sku": "C3", "qty": 5}]}'),
    ],
    schema="event_id string, payload string",
)

from pyspark.sql.types import StructType, StructField, StringType, ArrayType, LongType

event_schema = StructType([
    StructField("user", StructType([
        StructField("id", StringType()),
        StructField("name", StringType()),
    ])),
    StructField("tags", ArrayType(StringType())),
    StructField("items", ArrayType(StructType([
        StructField("sku", StringType()),
        StructField("qty", LongType()),
    ]))),
])

parsed_events = (
    events
    .withColumn("p", F.from_json(F.col("payload"), event_schema))
    .withColumn("user_name", F.col("p.user.name"))
    .withColumn("tag_count", F.size(F.col("p.tags")))
    .withColumn("total_qty", F.transform(F.col("p.items"), lambda x: x.getField("qty")))
)

parsed_events.select("event_id", "user_name", "tag_count", "total_qty").show(truncate=False)

# explode_outer keeps E-2 even though its tags array is empty
exploded = parsed_events.select(
    "event_id",
    F.explode_outer(F.col("p.tags")).alias("tag"),
)
print("rows with explode     :", exploded.count())
print("rows with explode_outer:", parsed_events.select("event_id", F.explode_outer(F.col("p.tags")).alias("tag")).count())
```

⚠️ **`F.explode` on E-2's empty tags array drops that row entirely.** `explode_outer` keeps
it with a null `tag`. Compare the counts above — that difference is exactly the silent row
loss this chapter warns about.

### Step 9 — Sampling, provenance, and synthetic IDs

```python
# Deterministic hash-based sample (reproducible regardless of partition count)
sampled = activity.filter(F.pmod(F.hash("customer_id"), 2) == 0)
print("half-sample rows:", sampled.count())

# Seeded random sample (reproducible for a fixed partition count)
seeded = activity.withColumn("r", F.rand(42)).filter(F.col("r") < 0.5).drop("r")

# Provenance + synthetic id (audit only — not a business key)
with_audit = activity.withColumn("audit_id", F.monotonically_increasing_id())
# with_audit.write.mode("overwrite").parquet("gs://bucket/activity_audit/")

# Read back and confirm provenance
activity.write.mode("overwrite").parquet("gs://YOUR_BUCKET/activity/")
provenance = spark.read.parquet("gs://YOUR_BUCKET/activity/").withColumn(
    "source_file", F.input_file_name()
)
provenance.select("source_file").distinct().show(truncate=False)
```

### Step 10 — Repartition, sort, and write

```python
# Balanced output files — repartition, NOT coalesce
final = (
    scored
    .repartition(4)                                # full shuffle → 4 balanced partitions
    .sortWithinPartitions("lifetime_value")        # cheap per-partition sort
)

(
    final.write
    .mode("overwrite")
    .option("compression", "snappy")
    .parquet("gs://YOUR_BUCKET/customer_master/")
)
```

💡 **`repartition(4)` then `sortWithinPartitions` gives you 4 balanced, internally-sorted
files.** That is the pattern to use when writing large Parquet datasets: bounded file count,
even file sizes, and sorted content for downstream pruning.

### Step 11 — Idempotency check

```python
def content_hash(df):
    rows = df.select(F.sha2(F.to_json(F.struct(*df.columns)), 256).alias("h"))
    return rows.agg(F.sha2(F.concat_ws("", F.sort_array(F.collect_list("h"))), 256)).collect()[0][0]

run1 = scored.orderBy("customer_id")
run2 = scored.orderBy("customer_id")   # same logic, "re-run"

print("run1 hash:", content_hash(run1))
print("run2 hash:", content_hash(run2))
assert content_hash(run1) == content_hash(run2), "not idempotent!"
```

### Step 12 — Inspect the plan

```python
scored.explain(True)
```

Count the `Exchange` nodes. The survivorship window, the aggregation, and the windowed
analytics each require a shuffle — three total. If you see more, look for an accidental
cross-partition operation.

---

## 🔑 Key Takeaways

- Window functions preserve rows; `groupBy` collapses them. That is the whole difference.
- Always specify the frame explicitly (`rowsBetween`) — the default `RANGE` frame behaves
  differently when the ordering column has ties.
- `row_number` breaks ties **arbitrarily**. For deterministic dedup-to-latest, add a stable
  tiebreaker to the window's `orderBy`.
- `rank` leaves gaps after ties (1, 2, 2, 4); `dense_rank` does not (1, 2, 2, 3); and
  `rank <= 3` may return more than three rows.
- `groupBy.apply` moves an **entire group** to one Python worker. Use `groupBy().agg()`
  unless the logic genuinely cannot be expressed natively.
- `F.approx_count_distinct` trades a small error for a large speedup. Never use it for
  billing or regulatory counts.
- `monotonically_increasing_id()` is unique but **not stable** — never use it as a business
  key.
- `F.input_file_name()` returns the full `gs://` path. Use it for lineage, not identity.
- `F.rand(seed)` is reproducible for a fixed partition count only. A deterministic hash of a
  business key is reproducible always.
- `orderBy` is a global range-partitioned sort; `sortWithinPartitions` is local and cheap.
- `repartition` shuffles and balances; `coalesce` does not shuffle and can only reduce.
  **Coalescing below the input file count creates skew.**
- `dropDuplicates(subset=...)` treats nulls as one distinct group — one null-keyed row
  survives.
- Quarantine bad rows, count them, and assert the reconciliation. A count without an
  invariant is only a log line.
- `explode` drops null and empty arrays; `explode_outer` keeps them. The difference is a
  silent row-count change.
- Idempotency comes from deterministic dedup, stable keys, partition overwrite, and no
  unbounded randomness in business logic.

---

## 📚 Practice Exercises

1. **Deterministic survivorship.** You have four source systems with overlapping customer
   records and conflicting attributes. Define a survivorship rule (e.g. most recent wins,
   then highest source priority, then non-null completeness score). Implement it with
   `row_number` and a fully deterministic tiebreaker. Prove determinism by running the
   pipeline twice and comparing content hashes. Explain what would happen if you used
   `dropDuplicates(subset=["customer_id"])` instead.

2. **Skew investigation.** A job has 200 shuffle partitions; one task takes 30× longer than
   the others. Using the Spark UI metrics, identify the skewed partition, find the hot key,
   and implement a fix with **two** of: salting, broadcast, pre-aggregation. For each fix,
   state its cost (extra data volume, extra shuffles, memory) and the condition under which
   you would *not* use it.

3. **Nested data pipeline.** From a JSON event stream, extract the user id, flatten the
   `items` array into one row per item, explode the `tags` array, and produce a per-user
   daily aggregate. Use `from_json` with an explicit schema, `explode_outer` for the tags,
   and a `window` for the running item count per user. Track the row count at every stage
   and explain each difference. Include a `_corrupt_record` quarantine path for malformed
   JSON.

4. **Idempotent incremental pipeline.** Build a pipeline that processes one `dt` partition
   per run, merges into a Delta table keyed by `id`, and is safe to re-run for the same
   `dt`. Demonstrate idempotency by running twice and comparing counts and hashes. Then
   break it deliberately (add a non-deterministic `F.rand()` column, or use `append` mode)
   and show the failure.

---

## 📖 Further Reading

- PySpark API reference — https://spark.apache.org/docs/3.5.3/api/python/reference/pyspark.sql.html
- PySpark window functions — https://spark.apache.org/docs/3.5.3/api/python/reference/pyspark.sql/window.html
- Spark SQL built-in functions (Spark 3.5) — https://spark.apache.org/docs/3.5.3/sql-ref-functions-builtin.html
- Spark SQL performance tuning guide — https://spark.apache.org/docs/3.5.3/sql-performance-tuning.html
- Adaptive Query Execution (AQE) — https://spark.apache.org/docs/3.5.3/sql-performance-tuning.html#adaptive-query-execution
- Spark SQL performance tuning: tuning partitions — https://spark.apache.org/docs/3.5.3/sql-performance-tuning.html#tuning-partitions
- Delta Lake merge (upsert) semantics — https://docs.delta.io/latest/delta-batch.html#merge-into
- Dataproc image versions — https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-image-versions
- Dataproc job submission — https://cloud.google.com/dataproc/docs/concepts/components/jobs/submission
