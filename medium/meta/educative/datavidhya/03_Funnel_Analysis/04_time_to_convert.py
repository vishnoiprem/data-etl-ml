"""
Problem 04: Time-to-convert between steps.

Meta flavor: Average minutes from impression to click, click to add_to_cart,
add_to_cart to purchase. Identify the slowest step.

How to Think:
- For each user, get timestamp of each step.
- Self-join (or use FIRST_VALUE/LAG) to compute deltas.
- Aggregate avg/median per step pair.

How to Remember:
- "delta = step_k_ts - step_(k-1)_ts. AVG(d) per pair."

AI Use Cases:
- Friction detection (slow steps).
- Real-time abandonment triggers.
- Latency features for ranking.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, unix_timestamp, first, avg

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [
        (1, "impression",  "2026-01-01 10:00:00"),
        (1, "click",       "2026-01-01 10:01:00"),  # 60s
        (1, "add_to_cart", "2026-01-01 10:05:00"),  # 240s
        (1, "purchase",    "2026-01-01 10:10:00"),  # 300s
        (2, "impression",  "2026-01-01 11:00:00"),
        (2, "click",       "2026-01-01 11:00:30"),  # 30s
    ],
    ["user_id", "event_name", "ts"],
)

# Pivot: one row per user, columns for each step's timestamp
pivoted = events.groupBy("user_id").pivot("event_name").agg(first("ts"))
pivoted.show(truncate=False)

# Compute deltas
deltas = pivoted.withColumn("impression_to_click",
    (unix_timestamp("click")       - unix_timestamp("impression"))  / 60.0
).withColumn("click_to_cart",
    (unix_timestamp("add_to_cart") - unix_timestamp("click"))       / 60.0
).withColumn("cart_to_purchase",
    (unix_timestamp("purchase")    - unix_timestamp("add_to_cart")) / 60.0
)

avg_deltas = deltas.agg(
    avg("impression_to_click").alias("avg_min_impression_to_click"),
    avg("click_to_cart").alias("avg_min_click_to_cart"),
    avg("cart_to_purchase").alias("avg_min_cart_to_purchase"),
)
avg_deltas.show(truncate=False)

SQL = """
WITH pivoted AS (
  SELECT user_id,
         MAX(CASE WHEN event_name = 'impression'  THEN ts END) AS impression_ts,
         MAX(CASE WHEN event_name = 'click'       THEN ts END) AS click_ts,
         MAX(CASE WHEN event_name = 'add_to_cart' THEN ts END) AS cart_ts,
         MAX(CASE WHEN event_name = 'purchase'    THEN ts END) AS purchase_ts
  FROM events GROUP BY user_id
)
SELECT
  AVG(UNIX_TIMESTAMP(click_ts)    - UNIX_TIMESTAMP(impression_ts)) / 60.0 AS avg_min_impression_to_click,
  AVG(UNIX_TIMESTAMP(cart_ts)     - UNIX_TIMESTAMP(click_ts))      / 60.0 AS avg_min_click_to_cart,
  AVG(UNIX_TIMESTAMP(purchase_ts) - UNIX_TIMESTAMP(cart_ts))       / 60.0 AS avg_min_cart_to_purchase
FROM pivoted;
"""
