"""
Problem 03: Drop-off rate per step (% of previous step)
Meta flavor: "Where does WhatsApp Business onboarding lose the most users?"

How to Think:
- Drop-off at step N = 1 - (users_at_N / users_at_(N-1)).
- It is the complement of step conversion; pick whichever reads better.
- Always anchor at the previous step -- same anti-pattern as conversion rate.
- Sort by drop-off descending to surface the worst leaky step.

How to Remember:
- Pattern: "1 - users_at_N / users_at_(N-1)."
- A drop-off of 0.7 at step 3 says 70% who clicked never added to cart.
- For Meta onboarding, drop-off > 0.5 usually triggers a UX review.

AI Use Cases:
- Onboarding NLP agents surface biggest drop-off steps as remediation targets.
- Funnel drop-off powers the offline policy for inverse-propensity scoring.
- Marketing-ML re-engagement targets users at their highest drop-off step.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "impression", "2026-09-23 10:00:00"),
    ("u1", "click",      "2026-09-23 10:01:00"),
    ("u2", "impression", "2026-09-23 10:02:00"),
    ("u2", "click",      "2026-09-23 10:03:00"),
    ("u2", "add_to_cart","2026-09-23 10:04:00"),
    ("u3", "impression", "2026-09-23 10:05:00"),
    ("u4", "impression", "2026-09-23 10:06:00"),
    ("u4", "purchase",   "2026-09-23 10:10:00"),
]
df = spark.createDataFrame(events, ["user_id", "event_name", "event_ts"])

step_users = (df
    .withColumn("step", when(col("event_name")=="impression", 1)
                          .when(col("event_name")=="click",      2)
                          .when(col("event_name")=="add_to_cart",3)
                          .when(col("event_name")=="purchase",   4))
    .filter(col("step").isNotNull())
    .groupBy("user_id").agg(max("step").alias("max_step"))
    .groupBy("max_step").agg(countDistinct("user_id").alias("users"))
    .orderBy("max_step"))

dropoff = (step_users
           .withColumn("prev_users", lag("users").over(Window.orderBy("max_step")))
           .withColumn("drop_rate",
                       1 - col("users") / col("prev_users"))
           .filter(col("prev_users").isNotNull())
           .orderBy(col("drop_rate").desc()))
dropoff.show()

# SQL (Presto / Hive)
SQL = """
WITH buckets AS (
  SELECT max_step, COUNT(DISTINCT user_id) AS users
  FROM (
    SELECT user_id,
           MAX(CASE event_name
               WHEN 'impression' THEN 1
               WHEN 'click'      THEN 2
               WHEN 'add_to_cart'THEN 3
               WHEN 'purchase'   THEN 4 END) AS max_step
    FROM events
    WHERE event_date = CURRENT_DATE
    GROUP BY user_id
  ) t
  GROUP BY max_step
)
SELECT max_step,
       users,
       1 - users * 1.0 / NULLIF(LAG(users) OVER (ORDER BY max_step), 0) AS drop_rate
FROM buckets
ORDER BY drop_rate DESC;
"""
