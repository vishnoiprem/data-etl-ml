"""
Problem 05: Sessions per User per Day
Meta flavor: "For each Meta user, count how many sessions they had on each calendar day — used for DAU quality scoring."

How to Think:
- After sessionizing, derive a session_day = date_trunc('day', session_start).
- Aggregate: GROUP BY user_id, session_day, COUNT(DISTINCT session_id).
- Optionally bucket the day into hour-of-day or weekday for richer reporting.

How to Remember:
- session_day is a property of the session, not the event — compute it after grouping.
- COUNT(DISTINCT session_id) is essential because session_id already encodes the sequence number.

AI Use Cases
- DAU/Sessions-per-DAU ratio as a product health KPI.
- Detecting automation: users with thousands of sessions per day are bots.
- Ad pacing: average sessions per user per day per geo.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "2026-09-23 09:00:00", "open"),
    ("u1", "2026-09-23 10:30:00", "open"),  # new session, same day
    ("u1", "2026-09-24 09:00:00", "open"),  # new day, new session
    ("u2", "2026-09-23 11:00:00", "open"),
    ("u2", "2026-09-23 11:40:00", "open"),  # same session
]
df = spark.createDataFrame(events, ["user_id", "event_ts", "event_name"]).withColumn("event_ts", col("event_ts").cast("timestamp"))

w = Window.partitionBy("user_id").orderBy("event_ts")
sid_df = (
    df.withColumn("prev_ts", lag("event_ts").over(w))
      .withColumn("is_new", when(col("prev_ts").isNull() | ((col("event_ts").cast("long") - col("prev_ts").cast("long")) > 1800), 1).otherwise(0))
      .withColumn("session_id", concat_ws("_", col("user_id"), sum("is_new").over(w)))
      .withColumn("session_day", to_date("event_ts"))
)

per_user_day = (
    sid_df.groupBy("user_id", "session_day")
          .agg(countDistinct("session_id").alias("sessions_in_day"),
               count("*").alias("events_in_day"))
)
per_user_day.show(truncate=False)

# SQL (Presto / Hive)
SQL = """
WITH sessions AS (
  SELECT user_id, event_ts,
         CONCAT(user_id, '_',
                SUM(CASE WHEN prev_ts IS NULL OR (event_ts - prev_ts) > INTERVAL '30' MINUTE THEN 1 ELSE 0 END)
                OVER (PARTITION BY user_id ORDER BY event_ts)
         ) AS session_id,
         DATE(event_ts) AS session_day
  FROM (SELECT *, LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) AS prev_ts FROM events) t
)
SELECT user_id, session_day,
       COUNT(DISTINCT session_id) AS sessions_in_day,
       COUNT(*)                   AS events_in_day
FROM sessions
GROUP BY user_id, session_day
ORDER BY user_id, session_day
"""
