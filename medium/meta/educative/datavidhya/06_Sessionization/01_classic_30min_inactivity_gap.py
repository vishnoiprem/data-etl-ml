"""
Problem 01: Classic 30-min Inactivity Gap Sessionization
Meta flavor: "Given raw events from Facebook/Instagram, group them into user sessions using the industry-standard 30-minute inactivity gap rule."

How to Think:
- A session ends when there is no user activity for 30+ minutes.
- For each user, sort events chronologically and compute the gap to the previous event.
- Flag rows where the gap > 30 minutes as session starters.
- Use a cumulative sum of these flags to assign a session_id within each user.

How to Remember:
- lag() to compute gap, sum(case when gap > threshold then 1 else 0 end) over (partition by user order by ts) gives the session number.
- The first event per user is always a session starter (NULL previous).

AI Use Cases
- Funnel analysis: assign conversion credit to the session containing the target event.
- Engagement metrics: daily active users vs sessions-per-DAU ratio.
- A/B testing: split users by session-level exposure to an experimental feature.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

# inline sample: events(user_id, event_ts, event_name)
events = [
    ("u1", "2026-09-23 10:00:00", "click"),
    ("u1", "2026-09-23 10:05:00", "view"),
    ("u1", "2026-09-23 10:45:00", "purchase"),  # 40m gap, new session
    ("u1", "2026-09-23 10:47:00", "view"),
    ("u2", "2026-09-23 11:00:00", "click"),
]
df = spark.createDataFrame(events, ["user_id", "event_ts", "event_name"])
df = df.withColumn("event_ts", col("event_ts").cast("timestamp"))

w = Window.partitionBy("user_id").orderBy("event_ts")
gap_df = (
    df.withColumn("prev_ts", lag("event_ts").over(w))
      .withColumn("is_new_session", when(col("prev_ts").isNull() | ((col("event_ts").cast("long") - col("prev_ts").cast("long")) > 1800), 1).otherwise(0))
)
session_df = gap_df.withColumn("session_id", concat_ws("_", col("user_id"), sum("is_new_session").over(w)))
session_df.show(truncate=False)

# SQL (Presto / Hive)
SQL = """
WITH lagged AS (
  SELECT user_id, event_ts, event_name,
         LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) AS prev_ts
  FROM events
),
flags AS (
  SELECT user_id, event_ts, event_name,
         CASE WHEN prev_ts IS NULL OR (event_ts - prev_ts) > INTERVAL '30' MINUTE THEN 1 ELSE 0 END AS is_new_session
  FROM lagged
)
SELECT user_id, event_ts, event_name,
       CONCAT(user_id, '_', SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY event_ts)) AS session_id
FROM flags
"""
