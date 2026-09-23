"""
Problem 08: Replay/Streaming Sessionization
Meta flavor: "Replay a 24-hour Kafka stream of Meta events from scratch while continuously emitting sessionized output to a downstream sink."

How to Think:
- Spark Structured Streaming supports windowed aggregation with watermark + stateful session windows via `groupBy(session_window)`.
- Or fall back to the batch pattern (lag → flag → cumsum) on each micro-batch, accepting small duplication at batch boundaries.
- Flink's `SESSION` window is purpose-built: `SESSION(ts INTERVAL '30' MINUTE)`.

How to Remember:
- Spark `pyspark.sql.functions.session_window` since 3.2 — `df.groupBy("user_id", session_window("event_ts", "30 minutes"))`.
- For correctness across late-arriving events, watermark + session_window handles out-of-orderness automatically.
- Flink SQL: `SELECT * FROM TABLE(SESSION(TABLE events, DESCRIPTOR(event_ts), INTERVAL '30' MINUTE))`.

AI Use Cases
- Real-time personalization: live features based on the current session.
- Live anomaly detection: alert when a session exceeds normal length.
- Real-time ad pacing: count active sessions per geo every second.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

# Batch-emulation of a streaming pipeline; in production use readStream + session_window
events = [
    ("u1", "2026-09-23 09:00:00", "open"),
    ("u1", "2026-09-23 09:20:00", "scroll"),
    ("u1", "2026-09-23 10:00:00", "open"),  # new session
    ("u2", "2026-09-23 11:00:00", "click_ad"),
    ("u2", "2026-09-23 11:10:00", "view_post"),
]
df = spark.createDataFrame(events, ["user_id", "event_ts", "event_name"]).withColumn("event_ts", col("event_ts").cast("timestamp"))

# Streaming-friendly: use session_window
streaming_df = df.withWatermark("event_ts", "1 hour").groupBy(
    "user_id", session_window(col("event_ts"), "30 minutes")
).agg(
    count("*").alias("event_count"),
    min("event_ts").alias("session_start"),
    max("event_ts").alias("session_end"),
    collect_list("event_name").alias("events_in_order")
)
streaming_df.show(truncate=False)

# SQL (Presto / Hive)
SQL = """
-- Spark Structured Streaming equivalent using session windows
SELECT user_id,
       session_window.start AS session_start,
       session_window.end   AS session_end,
       COUNT(*)             AS event_count,
       COLLECT_LIST(event_name) AS events_in_order
FROM events
WINDOW SESSION(event_ts, INTERVAL '30' MINUTE) AS session_window
GROUP BY user_id, session_window
"""
