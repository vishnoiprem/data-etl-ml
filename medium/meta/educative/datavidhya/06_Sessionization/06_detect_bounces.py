"""
Problem 06: Detect Bounces (single-event sessions)
Meta flavor: "Find users whose Facebook session contained only one event — these 'bounces' signal low engagement and are critical for onboarding optimization."

How to Think:
- A bounce is a session with exactly one event.
- After sessionizing, GROUP BY session_id, count rows; keep sessions where count == 1.
- Often bounces are filtered out before deeper engagement analysis because their duration is zero.

How to Remember:
- HAVING COUNT(*) = 1 is the canonical bounce filter.
- Single-event sessions also arise from mis-tracked client events — distinguish real bounces from telemetry bugs.

AI Use Cases
- Onboarding funnel: count bounces per step to find drop-off surfaces.
- Bot detection: a user with 90% bounce sessions is suspicious.
- Ad quality: bounce rate after ad click is a key relevance signal.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "2026-09-23 09:00:00", "open"),
    ("u1", "2026-09-23 09:01:00", "exit"),       # session S1: 2 events
    ("u1", "2026-09-23 10:00:00", "open"),       # session S2: 1 event -> bounce
    ("u2", "2026-09-23 11:00:00", "open"),       # session S3: 1 event -> bounce
    ("u2", "2026-09-23 12:00:00", "open"),
    ("u2", "2026-09-23 12:05:00", "view_post"),  # session S4: 2 events
    ("u2", "2026-09-23 13:00:00", "view_post"),
    ("u2", "2026-09-23 13:02:00", "react"),
    ("u2", "2026-09-23 13:10:00", "click_ad"),   # session S4 continues
]
df = spark.createDataFrame(events, ["user_id", "event_ts", "event_name"]).withColumn("event_ts", col("event_ts").cast("timestamp"))

w = Window.partitionBy("user_id").orderBy("event_ts")
sid_df = (
    df.withColumn("prev_ts", lag("event_ts").over(w))
      .withColumn("is_new", when(col("prev_ts").isNull() | ((col("event_ts").cast("long") - col("prev_ts").cast("long")) > 1800), 1).otherwise(0))
      .withColumn("session_id", concat_ws("_", col("user_id"), sum("is_new").over(w)))
)

bounces = (
    sid_df.groupBy("user_id", "session_id")
          .agg(count("*").alias("events_in_session"))
          .where(col("events_in_session") == 1)
)
bounces.show(truncate=False)

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
SELECT user_id, session_id, event_ts AS bounce_at, event_name AS bounce_event
FROM sessions
GROUP BY user_id, session_id, event_ts, event_name
HAVING COUNT(*) = 1
"""
