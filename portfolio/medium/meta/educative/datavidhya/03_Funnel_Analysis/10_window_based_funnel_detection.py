"""
Problem 10: Window-based funnel detection (within 7 days of step 1)
Meta flavor: "Conversion window of 7 days for Facebook Ads attribution."

How to Think:
- Windowed funnel = step 2..N must occur within K days (often 7) AFTER step 1.
- Anchor on step 1's first occurrence per user; compute step 2..N within
  the window [step1_ts, step1_ts + 7d].
- Use a self-join with timestamp <= INTERVAL '7' DAY, or use `LEAD`/`FIRST_VALUE`
  on the per-user sorted event array.
- For Meta ads, the attribution window is configurable per campaign -- never
  hard-code 7 days without asking.

How to Remember:
- Pattern: "first step1 ts per user -> self-join step2..N within 7d."
- Window length is a business decision -- ask before assuming.
- Long windows inflate conversions; short windows miss considered purchases.

AI Use Cases:
- Multi-touch attribution models compute credit within fixed windows.
- Uplift modeling segments users by their conversion window length.
- Delayed-feedback CVR models use window length to label training data.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "impression",  "2026-09-20 10:00:00"),
    ("u1", "click",       "2026-09-21 10:00:00"),  # +1d, in window
    ("u1", "purchase",    "2026-09-22 10:00:00"),  # +2d, in window
    ("u2", "impression",  "2026-09-10 10:00:00"),
    ("u2", "click",       "2026-09-25 10:00:00"),  # +15d, OUT of window
    ("u3", "impression",  "2026-09-22 10:00:00"),
    ("u3", "purchase",    "2026-09-23 10:00:00"),  # no click; step-skip OK
]
df = spark.createDataFrame(events, ["user_id","event_name","event_ts"])

# First step1 per user = anchor
step1 = (df.filter(col("event_name") == "impression")
          .groupBy("user_id")
          .agg(min("event_ts").alias("anchor_ts")))

# Look up subsequent events within 7 days
within = (step1.alias("a")
          .join(df.alias("b"), col("a.user_id") == col("b.user_id"))
          .where((col("b.event_ts") >= col("a.anchor_ts")) &
                 (col("b.event_ts") <= col("a.anchor_ts") +
                      expr("INTERVAL 7 DAYS")))
          .select(col("a.user_id"),
                  col("b.event_name"),
                  col("b.event_ts"),
                  col("a.anchor_ts")))

windowed = (within
    .groupBy("user_id")
    .agg(countDistinct(
        when(col("event_name")=="click",
             col("event_ts")).otherwise(when(col("event_name")=="purchase",
             col("event_ts")))).alias("later_steps")))
windowed.show()

# SQL (Presto / Hive)
SQL = """
WITH anchor AS (
  SELECT user_id, MIN(event_ts) AS anchor_ts
  FROM events
  WHERE event_name = 'impression'
  GROUP BY user_id
)
SELECT a.user_id,
       COUNT(DISTINCT CASE WHEN b.event_name = 'click'
                           THEN b.event_ts END) AS clicks_in_window,
       COUNT(DISTINCT CASE WHEN b.event_name = 'purchase'
                           THEN b.event_ts END) AS purchases_in_window
FROM anchor a
JOIN events b
  ON a.user_id = b.user_id
 AND b.event_ts >= a.anchor_ts
 AND b.event_ts <= a.anchor_ts + INTERVAL '7' DAY
GROUP BY a.user_id;
"""
