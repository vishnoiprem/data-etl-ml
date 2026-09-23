"""
Problem 02: Conversion rate between consecutive steps
Meta flavor: "Compute the click-through-rate and add-to-cart rate of an Instagram Shopping ad in the last 24 hours."

How to Think:
- Conversion rate between step N and step N+1 = users_at_(N+1) / users_at_N.
- Never use the very first step as the denominator when comparing step pairs.
- Outer-join step counts on a fixed step list so the math is predictable.
- Alias every step to a constant column so the join stays readable.

How to Remember:
- Pattern: "step1_users / step2_users, never total over total."
- Round to 4 decimals for dashboards; raw float for ML features.
- For Meta ads, exclude `robot_user_id = TRUE` to avoid bot inflation.

AI Use Cases:
- CTR prediction features come straight from past step-pair conversion rates.
- Real-time bidding uses click-to-cart rates to estimate purchase CVR.
- Bandit policies choose creative variants by per-step conversion lift.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

events = [
    ("u1", "impression", "2026-09-23 10:00:00"),
    ("u1", "click",      "2026-09-23 10:01:00"),
    ("u1", "add_to_cart","2026-09-23 10:05:00"),
    ("u2", "impression", "2026-09-23 10:02:00"),
    ("u2", "click",      "2026-09-23 10:03:00"),
    ("u3", "impression", "2026-09-23 10:04:00"),
    ("u3", "purchase",   "2026-09-23 10:09:00"),
]
df = spark.createDataFrame(events, ["user_id", "event_name", "event_ts"])

step_users = (df
    .withColumn("step", when(col("event_name")=="impression", 1)
                          .when(col("event_name")=="click",      2)
                          .when(col("event_name")=="add_to_cart",3)
                          .when(col("event_name")=="purchase",   4))
    .filter(col("step").isNotNull())
    .groupBy("user_id")
    .agg(max("step").alias("max_step"))
    .groupBy("max_step")
    .agg(countDistinct("user_id").alias("users"))
    .orderBy("max_step"))

# Compute pairwise conversion by LAG
rates = (step_users
         .withColumn("prev_users", lag("users").over(Window.orderBy("max_step")))
         .withColumn("conv_rate", col("users") / col("prev_users"))
         .filter(col("prev_users").isNotNull()))
rates.show()

# SQL (Presto / Hive)
SQL = """
WITH step_users AS (
  SELECT max_step, users
  FROM (
    SELECT user_id,
           MAX(CASE event_name
               WHEN 'impression' THEN 1
               WHEN 'click'      THEN 2
               WHEN 'add_to_cart'THEN 3
               WHEN 'purchase'   THEN 4 END) AS max_step
    FROM events
    WHERE event_ts >= CURRENT_TIMESTAMP - INTERVAL '1' DAY
    GROUP BY user_id
  ) t
  GROUP BY max_step
)
SELECT max_step,
       users,
       LAG(users) OVER (ORDER BY max_step)               AS prev_users,
       users * 1.0 / LAG(users) OVER (ORDER BY max_step) AS conv_rate
FROM step_users
ORDER BY max_step;
"""
