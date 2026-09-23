"""
Problem 01: Classic 4-step funnel (impression -> click -> add-to-cart -> purchase)
Meta flavor: "Compute the daily purchase funnel on Facebook Marketplace listings."

How to Think:
- Each row in `events` is one user action. A funnel needs one number per step.
- Use a boolean flag per step, then take MAX(by user) to convert events -> users.
- Count distinct users per step. Step 1 (impression) is the denominator.
- Each step's conversion = step_n_users / step_1_users.
- Always partition by date so the funnel reflects a single day, not all time.

How to Remember:
- Pattern: "Boolean per step -> MAX per user -> COUNT(DISTINCT)."
- Self-join (impression ts < click ts < cart ts < purchase ts) is the
  alternative when timestamps must be ordered.
- For Meta, step ordering is enforced by the event payload schema, not by us.

AI Use Cases:
- Powering ad-attribution models: each funnel stage is a feature in the CVR
  prediction pipeline (impression -> click probability, click -> cart, etc.).
- Reinforcement-learning agents use drop-off rates as reward signals.
- Embedding-based lookalike audiences are scored using funnel completion.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

# inline sample: events(user_id, event_name, event_ts)
events = [
    ("u1", "impression", "2026-09-23 10:00:00"),
    ("u1", "click",      "2026-09-23 10:01:00"),
    ("u1", "add_to_cart","2026-09-23 10:05:00"),
    ("u1", "purchase",   "2026-09-23 10:07:00"),
    ("u2", "impression", "2026-09-23 10:02:00"),
    ("u2", "click",      "2026-09-23 10:03:00"),
    ("u3", "impression", "2026-09-23 10:04:00"),
]
df = spark.createDataFrame(events, ["user_id", "event_name", "event_ts"])

# Step 1: flag, then MAX per user, then COUNT(DISTINCT user) per step
flags = (df
         .withColumn("step", when(col("event_name") == "impression", 1)
                     .when(col("event_name") == "click",       2)
                     .when(col("event_name") == "add_to_cart", 3)
                     .when(col("event_name") == "purchase",    4))
         .filter(col("step").isNotNull())
         .groupBy("user_id")
         .agg(max("step").alias("max_step"))
         .groupBy("max_step")
         .agg(countDistinct("user_id").alias("users"))
         .orderBy("max_step"))
flags.show()

# SQL (Presto / Hive)
SQL = """
WITH flagged AS (
  SELECT user_id,
         MAX(CASE event_name
             WHEN 'impression' THEN 1
             WHEN 'click'      THEN 2
             WHEN 'add_to_cart'THEN 3
             WHEN 'purchase'   THEN 4 END) AS max_step
  FROM events
  WHERE event_date = CURRENT_DATE
  GROUP BY user_id
)
SELECT max_step, COUNT(DISTINCT user_id) AS users
FROM flagged
GROUP BY max_step
ORDER BY max_step;
"""
