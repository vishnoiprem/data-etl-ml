"""
Problem 10: Bot / Duplicate Filtering before Sessionization
Meta flavor: "Pre-filter Meta events to remove bot traffic and duplicate clicks before computing session metrics — otherwise DAU and engagement are inflated."

How to Think:
- Two filters applied in order:
  1. Drop bot events: `WHERE NOT is_bot AND user_agent NOT LIKE '%facebookexternalhit%'`.
  2. Deduplicate identical events: keep first occurrence per (user_id, event_name, event_ts).
- After filtering, run the standard sessionization pipeline.
- Optional second pass: drop sessions created entirely from bots (in case filtering was lossy).

How to Remember:
- Filter -> dedupe -> sessionize is the canonical pipeline.
- Bot tagging often comes from a separate classifier column, not heuristics — respect the source-of-truth.
- Duplicates are usually (user_id, event_name, event_ts) triplets; use `ROW_NUMBER` to dedupe.

AI Use Cases
- DAU accuracy: filtering bots often reduces DAU by 2-5%.
- Engagement KPIs: bot-free sessions reveal the true distribution.
- Fraud detection: clusters of dedup'd-but-suspicious events become training data.
"""
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "2026-09-23 09:00:00", "open", False),
    ("u1", "2026-09-23 09:00:00", "open", False),     # duplicate
    ("u1", "2026-09-23 09:05:00", "scroll", False),
    ("u2", "2026-09-23 09:10:00", "open", True),      # bot
    ("u2", "2026-09-23 09:11:00", "click_ad", True),  # bot
    ("u3", "2026-09-23 10:00:00", "open", False),
    ("u3", "2026-09-23 10:30:00", "open", False),     # new session
]
schema = ["user_id", "event_ts", "event_name", "is_bot"]
df = spark.createDataFrame(events, schema).withColumn("event_ts", col("event_ts").cast("timestamp"))

# 1) Filter bots
clean = df.filter(~col("is_bot"))

# 2) Dedupe by (user_id, event_name, event_ts)
w_dup = Window.partitionBy("user_id", "event_name", "event_ts").orderBy("event_ts")
dedup = clean.withColumn("rn", row_number().over(w_dup)).filter(col("rn") == 1).drop("rn")

# 3) Sessionize
w = Window.partitionBy("user_id").orderBy("event_ts")
out = (
    dedup.withColumn("prev_ts", lag("event_ts").over(w))
         .withColumn("is_new", when(col("prev_ts").isNull() | ((col("event_ts").cast("long") - col("prev_ts").cast("long")) > 1800), 1).otherwise(0))
         .withColumn("session_id", concat_ws("_", col("user_id"), sum("is_new").over(w)))
)
out.show(truncate=False)

# SQL (Presto / Hive)
SQL = """
WITH clean AS (
  SELECT * FROM events WHERE is_bot = false
),
dedup AS (
  SELECT *
  FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id, event_name, event_ts ORDER BY event_ts) AS rn FROM clean) t
  WHERE rn = 1
),
lagged AS (
  SELECT *, LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) AS prev_ts FROM dedup
)
SELECT user_id, event_ts, event_name,
       CONCAT(user_id, '_',
              SUM(CASE WHEN prev_ts IS NULL OR (event_ts - prev_ts) > INTERVAL '30' MINUTE THEN 1 ELSE 0 END)
              OVER (PARTITION BY user_id ORDER BY event_ts)
       ) AS session_id
FROM lagged
"""
