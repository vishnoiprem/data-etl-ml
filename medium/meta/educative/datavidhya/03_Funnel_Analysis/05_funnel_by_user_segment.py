"""
Problem 05: Funnel by user segment (new vs returning)
Meta flavor: "Funnel comparison of new signups vs returning users on Facebook Reels."

How to Think:
- Build a `users` dimension with `is_new` flag (or cohort date).
- Join events to users; compute step counts per segment.
- A returning user is one with a prior session in the 30 days before today.
- Pivot the result so rows = step, columns = segment, easier to compare.

How to Remember:
- Pattern: "join users first, then funnel; segment by is_new."
- A new user should always have at least one event today (the trigger session).
- For Meta, "new" usually means first-time-ever, not first-time-in-30d.

AI Use Cases:
- Acquisition LTV models segment by new/returning for downstream training.
- Per-segment funnel feeds the policy of bandit exploration vs exploitation.
- Lookalike audiences seed from top-funnel new users with strong CVR.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "new",       "impression",  "2026-09-23 10:00:00"),
    ("u1", "new",       "click",       "2026-09-23 10:01:00"),
    ("u2", "new",       "impression",  "2026-09-23 10:02:00"),
    ("u3", "returning", "impression",  "2026-09-23 10:03:00"),
    ("u3", "returning", "click",       "2026-09-23 10:04:00"),
    ("u3", "returning", "add_to_cart", "2026-09-23 10:05:00"),
    ("u3", "returning", "purchase",    "2026-09-23 10:06:00"),
]
df = spark.createDataFrame(events,
    ["user_id","segment","event_name","event_ts"])

step_users = (df
    .withColumn("step", when(col("event_name")=="impression", 1)
                          .when(col("event_name")=="click",      2)
                          .when(col("event_name")=="add_to_cart",3)
                          .when(col("event_name")=="purchase",   4))
    .filter(col("step").isNotNull())
    .groupBy("segment","user_id")
    .agg(max("step").alias("max_step"))
    .groupBy("segment","max_step")
    .agg(countDistinct("user_id").alias("users"))
    .orderBy("segment","max_step"))

step_users.show()

# Pivot steps -> columns for side-by-side segment comparison
pivoted = (step_users
           .groupBy("max_step")
           .pivot("segment", ["new", "returning"])
           .sum("users")
           .na.fill(0)
           .orderBy("max_step"))
pivoted.show()

# SQL (Presto / Hive)
SQL = """
WITH step_users AS (
  SELECT u.segment, e.user_id,
         MAX(CASE e.event_name
             WHEN 'impression'  THEN 1
             WHEN 'click'       THEN 2
             WHEN 'add_to_cart' THEN 3
             WHEN 'purchase'    THEN 4 END) AS max_step
  FROM events e
  JOIN users  u ON u.user_id = e.user_id
  WHERE e.event_date = CURRENT_DATE
  GROUP BY u.segment, e.user_id
)
SELECT max_step,
       SUM(CASE WHEN segment = 'new'       THEN 1 ELSE 0 END) AS new_users,
       SUM(CASE WHEN segment = 'returning' THEN 1 ELSE 0 END) AS returning_users
FROM step_users
GROUP BY max_step
ORDER BY max_step;
"""
