"""
Problem 08: Funnel pivot (steps x dates matrix)
Meta flavor: "Daily funnel trend matrix for the last 14 days on a Facebook Marketplace seller campaign."

How to Think:
- Rows = step, columns = dates. Each cell is the distinct user count for that
  step on that date.
- Compute per (date, step) user counts; then pivot.
- For dates with no events at a step, fill with 0 (NaN poisons charts).
- Sort by date desc so most recent is leftmost for ops dashboards.

How to Remember:
- Pattern: "GROUP BY date, step -> pivot step -> fill zeros."
- Watch out for time zones -- pin to UTC at the SQL boundary.
- For Meta, store date as `event_date` partition column to enable pruning.

AI Use Cases:
- Time-series forecasting models consume pivot matrices as multi-step inputs.
- Drift detection compares today's pivot to a 28-day reference pivot.
- Anomaly detection alerts when a single cell deviates > N sigma from baseline.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "impression",  "2026-09-21"),
    ("u1", "click",       "2026-09-21"),
    ("u2", "impression",  "2026-09-21"),
    ("u2", "click",       "2026-09-21"),
    ("u2", "purchase",    "2026-09-21"),
    ("u3", "impression",  "2026-09-22"),
    ("u3", "click",       "2026-09-22"),
    ("u4", "impression",  "2026-09-22"),
]
df = spark.createDataFrame(events, ["user_id","event_name","event_date"])

step_users = (df
    .withColumn("step", when(col("event_name")=="impression", 1)
                          .when(col("event_name")=="click",      2)
                          .when(col("event_name")=="add_to_cart",3)
                          .when(col("event_name")=="purchase",   4))
    .filter(col("step").isNotNull())
    .groupBy("event_date","user_id")
    .agg(max("step").alias("max_step"))
    .groupBy("event_date","max_step")
    .agg(countDistinct("user_id").alias("users")))

pivot = (step_users
         .groupBy("max_step")
         .pivot("event_date")
         .sum("users")
         .na.fill(0)
         .orderBy("max_step"))
pivot.show()

# SQL (Presto / Hive)
SQL = """
WITH step_users AS (
  SELECT event_date, user_id,
         MAX(CASE event_name
             WHEN 'impression'  THEN 1
             WHEN 'click'       THEN 2
             WHEN 'add_to_cart' THEN 3
             WHEN 'purchase'    THEN 4 END) AS max_step
  FROM events
  WHERE event_date BETWEEN CURRENT_DATE - INTERVAL '14' DAY
                       AND CURRENT_DATE
  GROUP BY event_date, user_id
)
SELECT max_step,
       SUM(CASE WHEN event_date = CURRENT_DATE     - 0  THEN users ELSE 0 END) AS d0,
       SUM(CASE WHEN event_date = CURRENT_DATE     - 1  THEN users ELSE 0 END) AS d1,
       SUM(CASE WHEN event_date = CURRENT_DATE     - 2  THEN users ELSE 0 END) AS d2
       -- ... one column per day
FROM step_users
GROUP BY max_step
ORDER BY max_step;
"""
