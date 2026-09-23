"""
Problem 02: SUM-over-flag trick (assign session_id with cumulative sum)
Meta flavor: "From a Facebook News Feed clickstream, derive `session_id` purely from a windowed SUM over a flag — the canonical cumulative-sum pattern."

How to Think:
- Instead of materializing timestamps, just produce a 0/1 flag per row.
- SUM(...) OVER (ORDER BY ts) acts as a running counter that increments only at session boundaries.
- This avoids expensive self-joins and works on streaming as well as batch.

How to Remember:
- CUME_DIST? No — classic cumulative SUM-of-flag is the simplest, fastest session-id generator.
- The trick is sum(case when ...) over (partition by user_id order by ts rows between unbounded preceding and current row).

AI Use Cases
- Real-time sessionization in Flink/Spark Structured Streaming.
- Cohort assignment by session number (1st session vs Nth session).
- Attribution: bucket impressions by session for short-window conversion lifts.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

# inline sample
events = [
    ("u1", "2026-09-23 09:00:00", "open"),
    ("u1", "2026-09-23 09:10:00", "scroll"),
    ("u1", "2026-09-23 09:55:00", "like"),  # new session
    ("u2", "2026-09-23 10:00:00", "open"),
]
df = spark.createDataFrame(events, ["user_id", "event_ts", "event_name"]).withColumn("event_ts", col("event_ts").cast("timestamp"))

w = Window.partitionBy("user_id").orderBy("event_ts").rowsBetween(Window.unboundedPreceding, Window.currentRow)
out = (
    df.withColumn("flag", when((col("event_ts").cast("long") - lag("event_ts", 1, col("event_ts")).over(Window.partitionBy("user_id").orderBy("event_ts")).cast("long")) > 1800, 1).otherwise(0))
      .withColumn("session_seq", sum("flag").over(w))
      .withColumn("session_id", concat_ws("_", col("user_id"), col("session_seq")))
)
out.show(truncate=False)

# SQL (Presto / Hive)
SQL = """
SELECT user_id, event_ts, event_name,
       CONCAT(user_id, '_',
              SUM(CASE WHEN (event_ts - LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts)) > INTERVAL '30' MINUTE
                       OR LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) IS NULL
                       THEN 1 ELSE 0 END)
              OVER (PARTITION BY user_id ORDER BY event_ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
       ) AS session_id
FROM events
"""
