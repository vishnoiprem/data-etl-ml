"""
Problem 07: Sessionization with Array-of-Events (Presto)
Meta flavor: "Group events into arrays so that every session becomes a single row with an `events ARRAY<ROW(...)>` payload — convenient for downstream ML pipelines."

How to Think:
- Two layers: first tag each row with session_id (the cumsum approach), then collapse to one row per session with `array_agg(event_struct) ORDER BY event_ts`.
- Presto's `array_agg` with `ORDER BY` keeps the chronological order inside the array.
- Result: one row per session with `start_ts`, `end_ts`, and an `events` array.

How to Remember:
- `array_agg(ROW(event_ts, event_name) ORDER BY event_ts)` returns rows of type `ROW`.
- `events[1]` and `events[-1]` give the first and last event of the session in Presto.
- This is the input shape most ML models expect (a sequence per session).

AI Use Cases
- Sequence models: feed the session events into a transformer/RNN.
- Embedding pre-training: skip-thought or BERT-style contrastive learning over sessions.
- Rule mining: extract frequent sub-sequences of (event_name) per session.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "2026-09-23 09:00:00", "open"),
    ("u1", "2026-09-23 09:05:00", "scroll"),
    ("u1", "2026-09-23 10:00:00", "open"),
    ("u2", "2026-09-23 11:00:00", "click_ad"),
    ("u2", "2026-09-23 11:02:00", "view_post"),
]
df = spark.createDataFrame(events, ["user_id", "event_ts", "event_name"]).withColumn("event_ts", col("event_ts").cast("timestamp"))

w = Window.partitionBy("user_id").orderBy("event_ts")
sid_df = (
    df.withColumn("prev_ts", lag("event_ts").over(w))
      .withColumn("is_new", when(col("prev_ts").isNull() | ((col("event_ts").cast("long") - col("prev_ts").cast("long")) > 1800), 1).otherwise(0))
      .withColumn("session_id", concat_ws("_", col("user_id"), sum("is_new").over(w)))
)

session_arrays = (
    sid_df.groupBy("user_id", "session_id")
          .agg(
              min("event_ts").alias("session_start"),
              max("event_ts").alias("session_end"),
              collect_list(struct("event_ts", "event_name")).alias("events")
          )
)
session_arrays.show(truncate=False)

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
SELECT user_id,
       MIN(event_ts) AS session_start,
       MAX(event_ts) AS session_end,
       ARRAY_AGG(ROW(event_ts, event_name) ORDER BY event_ts) AS events
FROM sessions
GROUP BY user_id, SUBSTR(session_id, LENGTH(user_id) + 2)
"""
