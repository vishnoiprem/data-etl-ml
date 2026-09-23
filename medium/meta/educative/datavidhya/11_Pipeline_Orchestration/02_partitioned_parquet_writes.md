# Partitioned Hive/Parquet Writes

## Problem
Write Hive-style partitioned Parquet tables safely and idempotently.

## How to Think
1. **Partition columns** – pick low-cardinality, high-selectivity (dt, country).
2. **Repartition** before write to avoid tiny files.
3. **Staging** path then atomic swap.
4. **Repair** partition metadata (`MSCK REPAIR TABLE`).
5. **Consider Delta/Iceberg** for ACID + time-travel.

## How to Remember
- **"Write to staging, then atomic rename."**
- **`partitionBy('dt','country')` + `MSCK REPAIR TABLE`.**

## Code (PySpark)
```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-01", "US", "feed"),
     (2, "2026-01-01", "US", "reels"),
     (3, "2026-01-02", "IN", "feed")],
    ["user_id", "dt", "country", "surface"]
)

staging = "s3://staging/events/"
prod    = "s3://prod/events/"

(events
 .repartition("dt", "country")
 .write
 .mode("append")
 .partitionBy("dt", "country")
 .parquet(staging))

spark.sql("MSCK REPAIR TABLE prod.events")
```

## Common Mistakes
- Over-partitioning (huge metadata, small files).
- Not running `MSCK REPAIR TABLE` -> new partitions invisible.
- Writing directly to prod (no atomic swap, partial data).

## AI Use Cases
- Auto-detect good partition columns from query history.
- Compaction recommendations for small files.
- Cost-aware partition design (S3 request-cost balance).
