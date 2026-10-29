"""
Problem 02: Partitioned Hive/Parquet writes.

Meta flavor: Hive-style partitioning + atomic directory swap. Show the
PySpark pattern for safe, idempotent, partitioned Parquet writes.

How to Think:
- Partition by dt (and optionally country / surface).
- Write to staging path, then atomic rename to prod.
- Enable dynamic partition; bucket for hot columns if needed.

How to Remember:
- "Write to staging, then atomic rename."
- "partitionBy('dt','country') for Hive; bucketing for joins."

AI Use Cases:
- Auto-detect good partition columns from query history.
- Compaction recommendations for small files.
- Cost-aware partition design.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.getOrCreate()

# Sample events DataFrame
events = spark.createDataFrame(
    [(1, "2026-01-01", "US", "feed"),
     (2, "2026-01-01", "US", "reels"),
     (3, "2026-01-02", "IN", "feed")],
    ["user_id", "dt", "country", "surface"]
)

staging = "s3://staging/events/"
prod    = "s3://prod/events/"

# 1) Write partitioned to staging
(events
 .repartition("dt", "country")          # avoid small files
 .write
 .mode("append")
 .partitionBy("dt", "country")          # Hive-style dirs
 .parquet(staging))

# 2) Atomic swap (S3 doesn't have rename, but use Hive ALTER TABLE
#    or distcp + delete); for Iceberg/Hudi use MERGE / CREATE PARTITION.
spark.sql(f"""
    MSCK REPAIR TABLE prod.events
""")

# Optional: convert to Delta / Iceberg for true ACID + time travel.
# spark.sql("CONVERT TO DELTA prod.events")
