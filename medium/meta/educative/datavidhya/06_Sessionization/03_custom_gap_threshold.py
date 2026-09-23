"""
Problem 03: Custom Gap Threshold (e.g., 10 min)
Meta flavor: "An Instagram Reels A/B test measures attention per micro-session — redefine the inactivity cutoff from 30 min to 10 min via a config parameter."

How to Think:
- Treat the inactivity threshold as a parameter, not a hard-coded constant.
- Replace the literal 1800 seconds (or INTERVAL '30' MINUTE) with a configurable value passed via Spark conf, a UDF, or a SQL bind variable.
- The logic is identical to the classic problem; only the comparison constant changes.

How to Remember:
- 1800 sec = 30 min; 600 sec = 10 min. Always document the threshold inside the SQL as a named CTE for readability.
- Parameterize via session configs in Hive or `${gap_seconds}` in Presto.

AI Use Cases
- A/B test sensitivity analysis: try thresholds from 5 to 60 minutes.
- Engagement granularity tuning: short sessions for short-form content, long for messaging.
- Cost optimization: tighter thresholds = more sessions = more downstream joins.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()
GAP_SECONDS = 600  # 10 minutes, configurable

events = [
    ("u1", "2026-09-23 12:00:00", "play"),
    ("u1", "2026-09-23 12:08:00", "like"),    # 8m gap, same session
    ("u1", "2026-09-23 12:25:00", "share"),   # 17m gap, new session
    ("u1", "2026-09-23 12:30:00", "play"),
]
df = spark.createDataFrame(events, ["user_id", "event_ts", "event_name"]).withColumn("event_ts", col("event_ts").cast("timestamp"))

w = Window.partitionBy("user_id").orderBy("event_ts")
flag_col = when(col("prev_ts").isNull() | ((col("event_ts").cast("long") - col("prev_ts").cast("long")) > GAP_SECONDS), 1).otherwise(0)

out = (
    df.withColumn("prev_ts", lag("event_ts").over(w))
      .withColumn("is_new", flag_col)
      .withColumn("session_id", concat_ws("_", col("user_id"), sum("is_new").over(w)))
)
out.show(truncate=False)

# SQL (Presto / Hive)
SQL = """
WITH lagged AS (
  SELECT *, LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) AS prev_ts FROM events
)
SELECT user_id, event_ts, event_name,
       CONCAT(user_id, '_',
              SUM(CASE WHEN prev_ts IS NULL OR (event_ts - prev_ts) > INTERVAL '10' MINUTE THEN 1 ELSE 0 END)
              OVER (PARTITION BY user_id ORDER BY event_ts)
       ) AS session_id
FROM lagged
"""
