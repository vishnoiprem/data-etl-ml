"""
Problem 04: Session-level Metrics (duration, event count)
Meta flavor: "After splitting Facebook events into sessions, report for each session: start, end, duration, event count, and the device/platform."

How to Think:
- Once session_id exists per row, collapse rows via GROUP BY session_id.
- Session duration = MAX(event_ts) - MIN(event_ts).
- Event count = COUNT(*).
- Optional: array of distinct event_names or first/last event for entry/exit pages.

How to Remember:
- Session metrics live one aggregation above event-level data.
- Express duration as `unix_timestamp(max_ts) - unix_timestamp(min_ts)` or `date_diff` in seconds.

AI Use Cases
- Long-session ranking features for ads ranking.
- Engagement decay: average duration vs time-of-day.
- Power-user segmentation: top decile of session duration.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "2026-09-23 08:00:00", "open"),
    ("u1", "2026-09-23 08:05:00", "view_post"),
    ("u1", "2026-09-23 08:15:00", "react"),
    ("u1", "2026-09-23 09:00:00", "open"),
    ("u2", "2026-09-23 10:00:00", "open"),
    ("u2", "2026-09-23 10:02:00", "click_ad"),
]
df = spark.createDataFrame(events, ["user_id", "event_ts", "event_name"]).withColumn("event_ts", col("event_ts").cast("timestamp"))

w = Window.partitionBy("user_id").orderBy("event_ts")
sid_df = (
    df.withColumn("prev_ts", lag("event_ts").over(w))
      .withColumn("is_new", when(col("prev_ts").isNull() | ((col("event_ts").cast("long") - col("prev_ts").cast("long")) > 1800), 1).otherwise(0))
      .withColumn("session_id", concat_ws("_", col("user_id"), sum("is_new").over(w)))
)

session_metrics = (
    sid_df.groupBy("user_id", "session_id")
          .agg(
              min("event_ts").alias("session_start"),
              max("event_ts").alias("session_end"),
              (unix_timestamp(max("event_ts")) - unix_timestamp(min("event_ts"))).alias("duration_sec"),
              count("*").alias("event_count"),
              countDistinct("event_name").alias("unique_event_types")
          )
)
session_metrics.show(truncate=False)

# SQL (Presto / Hive)
SQL = """
WITH sessions AS (
  SELECT user_id, event_ts, event_name,
         CONCAT(user_id, '_',
                SUM(CASE WHEN prev_ts IS NULL OR (event_ts - prev_ts) > INTERVAL '30' MINUTE THEN 1 ELSE 0 END)
                OVER (PARTITION BY user_id ORDER BY event_ts)
         ) AS session_id
  FROM (SELECT *, LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) AS prev_ts FROM events) t
)
SELECT session_id, user_id,
       MIN(event_ts) AS session_start,
       MAX(event_ts) AS session_end,
       UNIX_TIMESTAMP(MAX(event_ts)) - UNIX_TIMESTAMP(MIN(event_ts)) AS duration_sec,
       COUNT(*) AS event_count,
       COUNT(DISTINCT event_name) AS unique_event_types
FROM sessions
GROUP BY user_id, session_id
"""
