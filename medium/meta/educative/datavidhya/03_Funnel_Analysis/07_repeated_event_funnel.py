"""
Problem 07: Repeated-event funnel (count ALL events, not just first)
Meta flavor: "Total ad impressions vs total clicks vs total add-to-carts on Instagram Reels campaign."

How to Think:
- This is event-level counts, not user-level. A user who clicks 3 times counts 3x.
- Use COUNT(*) per event_name, not COUNT(DISTINCT user_id).
- Useful for "engagement volume" metrics like impressions-served, clicks-served.
- Often paired with a user-level funnel in the same dashboard.

How to Remember:
- Pattern: "GROUP BY event_name -> COUNT(*)."
- Never use this for "conversion" -- users buy once even if they click 10x.
- Impressions > clicks > carts should always hold (a sanity check).

AI Use Cases:
- Volume forecasting models use raw event counts to size infrastructure.
- Per-event counts feed ad-revenue pipelines (CPM = impressions / 1000).
- Anomaly detection on event streams (Spike Arrest) runs on these counts.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "impression",  "2026-09-23 10:00:00"),
    ("u1", "impression",  "2026-09-23 10:00:30"),
    ("u1", "click",       "2026-09-23 10:01:00"),
    ("u1", "add_to_cart", "2026-09-23 10:05:00"),
    ("u2", "impression",  "2026-09-23 10:02:00"),
    ("u2", "click",       "2026-09-23 10:03:00"),
    ("u2", "click",       "2026-09-23 10:04:00"),
    ("u2", "add_to_cart", "2026-09-23 10:05:00"),
    ("u2", "purchase",    "2026-09-23 10:07:00"),
]
df = spark.createDataFrame(events, ["user_id","event_name","event_ts"])

vol = (df.groupBy("event_name")
         .agg(count("*").alias("event_count"))
         .orderBy(col("event_count").desc()))
vol.show()

# SQL (Presto / Hive)
SQL = """
SELECT event_name, COUNT(*) AS event_count
FROM events
WHERE event_date = CURRENT_DATE
GROUP BY event_name
ORDER BY event_count DESC;
"""
