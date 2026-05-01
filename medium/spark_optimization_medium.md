# Stop Guessing, Start Tuning: A Practical Spark Optimization Guide for Databricks on Azure

*4 layers every data engineer needs to master — with real prototype code*

---

By **Prem Vishnoi** · Head of Data & AI · 8 min read

---

Most Spark performance problems aren't mysterious. They fall into one of four layers: how your data is stored on disk, how the engine executes your queries, how your cluster is sized, and which configuration knobs you've turned. Fix the right layer and you don't just speed things up — you cut Azure costs significantly.

This guide covers all four, in order of impact, with prototype code you can drop into your Databricks environment today.

---

## 1. Data Storage & Layout Optimization

The foundation of a high-performance Spark workspace is efficient file management on Delta Lake. No amount of executor tuning will save you if the engine is reading ten times more data than it needs to.

### Liquid Clustering — The Modern Replacement for Partitioning

If you're starting a new Delta table in 2025, use Liquid Clustering. It replaces the old `PARTITION BY` + `ZORDER BY` combination with a single, adaptive mechanism that:

- Automatically adjusts data layout to your actual query patterns
- Prevents the classic over-partitioning problem (millions of tiny files)
- Re-clusters only new and changed data incrementally — not the full table

```python
# Enable on CREATE
spark.sql("""
  CREATE OR REPLACE TABLE sales.transactions
  CLUSTER BY (sale_date, store_id, product_id)
  AS SELECT * FROM raw.transactions
""")

# Or ALTER an existing Delta table
spark.sql("ALTER TABLE sales.transactions CLUSTER BY (sale_date, store_id)")

# Trigger incremental re-clustering
spark.sql("OPTIMIZE sales.transactions")
```

### File Compaction and Data Skipping

For tables you haven't migrated to Liquid Clustering yet, `OPTIMIZE` with `ZORDER BY` is still your best tool. It merges small files into ~1GB targets and co-locates data so Spark can skip irrelevant files during filtered scans.

```python
# Classic OPTIMIZE + Z-ORDER for legacy tables
spark.sql("""
  OPTIMIZE sales.legacy_transactions
  ZORDER BY (sale_date, customer_id)
""")

# Verify skipping is working — look for "numFilesSkipped" in the output
spark.conf.set("spark.databricks.delta.stats.skipping", "true")
df = spark.read.table("sales.transactions")
df.filter("sale_date = '2025-01-15' AND store_id = 42").explain("formatted")
```

### VACUUM — Don't Forget the Cleanup

Every `DELETE`, `UPDATE`, and `MERGE` leaves old data files behind for time-travel. VACUUM removes them beyond your retention threshold. Left unmanaged, this metadata bloat slows down every query.

```python
# DRY RUN first — always
spark.sql("VACUUM sales.transactions RETAIN 168 HOURS DRY RUN")

# Then run it for real (168h = 7 days default)
spark.sql("VACUUM sales.transactions RETAIN 168 HOURS")

# Refresh column stats for the optimizer
spark.sql("ANALYZE TABLE sales.transactions COMPUTE STATISTICS FOR ALL COLUMNS")
```

**Rule of thumb:** Schedule `OPTIMIZE` + `VACUUM` as a nightly Databricks Workflow job on your busiest tables. It's cheap and the cumulative payoff is significant.

---

## 2. Execution Engine & Query Efficiency

Once your data is well-organized, the next layer is how Spark executes your queries.

### Adaptive Query Execution (AQE) — Enable It Everywhere

AQE is the single most impactful feature added to Spark in recent years. Instead of relying on static statistics, it re-optimizes query plans at runtime based on actual data sizes. It handles:

- **Skew joins** — automatically splits large partitions
- **Dynamic join type selection** — switches to broadcast joins when a table turns out smaller than expected
- **Post-shuffle partition coalescing** — collapses 800 partitions down to 40 when the data doesn't justify it

```python
# Enable AQE globally (on by default in DBR 14+, but be explicit)
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewFactor", "5")
```

### Broadcast Hash Joins — Eliminate Shuffle for Dimension Tables

When joining a large fact table to a small dimension table, broadcast the small one. This sends the dimension to every executor so the fact table never moves across the network.

```python
from pyspark.sql import functions as F

fact    = spark.read.table("sales.transactions")    # large
dim_str = spark.read.table("ref.stores")            # small dimension

# Explicit broadcast hint
result = fact.join(
    F.broadcast(dim_str),
    fact.store_id == dim_str.store_id
)

# Raise the auto-broadcast threshold (default 10MB → safe at 200MB for dimensions)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 200 * 1024 * 1024)
```

### Handling Data Skew with Salting

When AQE's built-in skew handling isn't enough — typically when one key value represents a massive fraction of your data — salting distributes the hot key across multiple partitions artificially.

```python
SALT_FACTOR = 10

# Add random salt to the skewed side
skewed_df = fact.withColumn(
    "salted_key",
    F.concat(F.col("customer_id"), F.lit("_"), (F.rand() * SALT_FACTOR).cast("int"))
)

# Explode the small table to match all salt values
dim_exploded = spark.read.table("ref.customers").withColumn(
    "salt", F.explode(F.array([F.lit(i) for i in range(SALT_FACTOR)]))
).withColumn(
    "salted_key", F.concat(F.col("customer_id"), F.lit("_"), F.col("salt"))
)

result = skewed_df.join(dim_exploded, "salted_key")
```

### Photon Engine and Delta Cache

**Photon** is Databricks' C++ vectorized execution engine. You don't change a line of code — you just enable it at the cluster level. It provides the biggest speedups on SQL aggregations, scans, and joins. Reported TCO savings run up to 80% on qualifying workloads.

**Delta Cache** (disk cache) caches remote ADLS/S3 data on local NVMe SSDs. It's transparent — repeated reads of the same data become local disk reads instead of network calls. To use it, you need storage-optimized instance types (Standard_L series on Azure).

```python
# Enable Delta Cache
spark.conf.set("spark.databricks.io.cache.enabled", "true")
spark.conf.set("spark.databricks.io.cache.maxDiskUsage", "50g")

# Pre-warm cache for a frequently queried date range
spark.sql("CACHE SELECT * FROM sales.transactions WHERE sale_date >= '2025-01-01'")
```

---

## 3. Compute & Cluster Tuning

Right-sizing resources is where you stop paying for what you don't use.

### Match Instance Type to Workload

| Workload | Azure Instance | Why |
|---|---|---|
| ETL / heavy transforms | Standard_E-series (memory-optimized) | Large shuffles, joins, ML |
| Interactive analytics | Standard_L-series (storage-optimized) | NVMe SSD activates Delta Cache |
| Structured streaming | Standard_F-series (compute-optimized) | High CPU throughput |

### Enhanced Autoscaling + Auto-Termination

Databricks Enhanced Autoscaling scales down aggressively compared to Apache Spark's native autoscaling. Combined with auto-termination, it eliminates idle DBU burn on All-Purpose clusters.

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import AutoScale

w = WorkspaceClient()

# ETL cluster — memory-optimized, Photon + AQE baked in
etl = w.clusters.create(
    cluster_name            = "data-platform-etl-prod",
    spark_version           = "15.4.x-scala2.12",         # LTS DBR
    node_type_id            = "Standard_E8ds_v4",          # 8 vCPU, 64GB RAM
    driver_node_type_id     = "Standard_E8ds_v4",
    autoscale               = AutoScale(min_workers=2, max_workers=16),
    enable_elastic_disk     = True,
    autotermination_minutes = 30,
    spark_conf = {
        "spark.databricks.photon.enabled"              : "true",
        "spark.sql.adaptive.enabled"                   : "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        "spark.sql.adaptive.skewJoin.enabled"          : "true",
        "spark.serializer"  : "org.apache.spark.serializer.KryoSerializer",
        "spark.databricks.delta.optimizeWrite.enabled" : "true",
        "spark.databricks.delta.autoCompact.enabled"   : "true",
    },
    custom_tags = {"team": "data-platform", "env": "prod"},
)

# Analytics cluster — storage-optimized, Delta Cache on NVMe SSD
analytics = w.clusters.create(
    cluster_name            = "data-platform-analytics",
    spark_version           = "15.4.x-scala2.12",
    node_type_id            = "Standard_L8s_v3",           # NVMe SSD
    autoscale               = AutoScale(min_workers=1, max_workers=8),
    autotermination_minutes = 60,
    spark_conf = {
        "spark.databricks.io.cache.enabled"     : "true",
        "spark.databricks.io.cache.maxDiskUsage": "100g",
        "spark.databricks.photon.enabled"        : "true",
    },
)
```

### Serverless SQL Warehouses for Analysts

For BI dashboards and ad-hoc SQL, Serverless SQL Warehouses are worth moving to entirely. They're instant-on, scale automatically per query, and you pay per query rather than per cluster-hour. No more paying for an idle Pro warehouse over a long weekend.

---

## 4. Parameter Tuning

The configuration layer. Less glamorous than the others, but some of these settings have large, immediate impact.

### Shuffle Partitions — The Most Commonly Mistuned Setting

The default of 200 is almost never right. With AQE enabled, the correct approach is to set it high and let AQE coalesce post-shuffle:

```python
# With AQE: set high, let AQE handle the rest
spark.conf.set("spark.sql.shuffle.partitions", "800")

# AQE coalesce target (default 64MB — raise for large shuffles)
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "256m")
spark.conf.set("spark.sql.adaptive.coalescePartitions.minPartitionSize", "64m")

# Without AQE — calculate manually
def calc_shuffle_partitions(shuffle_bytes: int, target_mb: int = 200) -> int:
    return max(200, shuffle_bytes // (target_mb * 1024 * 1024))
```

### Memory Fractions

```python
# Unified memory (default 0.6 of JVM heap — raise for join-heavy workloads)
spark.conf.set("spark.memory.fraction", "0.75")
spark.conf.set("spark.memory.storageFraction", "0.4")   # cache vs execution split

# Off-heap memory (useful for Pandas UDFs / Arrow)
spark.conf.set("spark.memory.offHeap.enabled", "true")
spark.conf.set("spark.memory.offHeap.size", "4g")
```

### Delta Write Optimizations

```python
# Bin data into fewer, larger files at write time
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")

# Async compaction after writes — prevents small-file accumulation
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.maxFileSize", "134217728")  # 128MB

# Enable Change Data Feed for incremental downstream pipelines
spark.conf.set("spark.databricks.delta.properties.defaults.enableChangeDataFeed", "true")
```

### Kryo Serialization

```python
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
spark.conf.set("spark.kryoserializer.buffer.max", "512m")
```

### Executor Sizing — A Rule of Thumb

```python
def recommend_executor_config(node_vcpus: int, node_ram_gb: int, num_nodes: int):
    """5 cores per executor, 1 core reserved for OS/Databricks agent."""
    cores_per_exec  = 5
    exec_per_node   = (node_vcpus - 1) // cores_per_exec
    ram_per_exec_gb = int((node_ram_gb - 2) / exec_per_node * 0.9)
    total_executors = exec_per_node * num_nodes

    print(f"Executors per node  : {exec_per_node}")
    print(f"Cores per executor  : {cores_per_exec}")
    print(f"RAM per executor    : {ram_per_exec_gb}g")
    print(f"Total executors     : {total_executors}")

    return {
        "spark.executor.cores"    : cores_per_exec,
        "spark.executor.memory"   : f"{ram_per_exec_gb}g",
        "spark.executor.instances": total_executors,
    }

# Example: Standard_E8ds_v4 (8 vCPU, 64GB) × 4 nodes
cfg = recommend_executor_config(8, 64, 4)
for k, v in cfg.items():
    spark.conf.set(k, str(v))
```

---

## Monitoring — Where to Look When Things Go Wrong

No tuning guide is complete without mentioning where to diagnose issues:

- **Spark UI** — your first stop. Look for long-tailed stages (skew), spill to disk, and shuffle read size. A stage that takes 10x longer than its siblings usually means skew or a broadcast threshold that's too low.
- **Query Profile in Databricks** — graphical view of SQL execution plans. Identifies bottlenecks at the operator level.
- **System Tables** — `system.billing.usage` and `system.compute.clusters` for historical DBU analysis. Essential if you're trying to attribute cost spikes to specific jobs or teams.

---

## Summary

| Layer | Top Technique | Immediate Impact |
|---|---|---|
| Storage | Liquid Clustering | Eliminates small-file problem and over-partitioning |
| Engine | AQE + Broadcast joins | Handles skew, eliminates shuffle for dimension joins |
| Cluster | Storage-optimized instance + auto-termination | Delta Cache + no idle spend |
| Parameters | optimizeWrite + AQE shuffle config | Fewer small files at write, self-tuning shuffle |

The single highest-leverage change you can make today: **enable AQE globally, enable `optimizeWrite` and `autoCompact`, and switch new tables to Liquid Clustering**. Those three together cover the majority of production Spark performance issues without touching a single line of business logic.

---

*Prem Vishnoi is Head of Data & AI, building on Azure Databricks across multiple markets. He writes about data engineering, distributed systems, and AI at scale.*

---

*Tags: #DataEngineering #ApacheSpark #Databricks #AzureDataBricks #BigData #DeltaLake #DataPlatform*
