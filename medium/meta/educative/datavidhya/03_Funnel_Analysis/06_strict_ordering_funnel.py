"""
Problem 06: Strict Ordering Funnel (step1 -> step2 -> step3 in that order).

Meta flavor: "Of users who clicked BEFORE they added to cart, what % completed
purchase?" Strict ordering is critical for attribution.

How to Think:
- For each user, get MIN(timestamp) per step.
- A user reaches step k if MIN(step_k) > MIN(step_(k-1)).
- Step k count = users where all prior MINs exist and step k MIN > previous MIN.

How to Remember:
- "min(step_k_ts) > min(step_(k-1)_ts) -> reached step k in order."

AI Use Cases:
- Attribution modeling.
- Path-aware conversion analysis.
- Sequential recommender evaluation.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, min, when

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [
        # user 1: impression < click < purchase -> reaches all 3 in order
        (1, "impression", "2026-01-01 10:00:00"),
        (1, "click",      "2026-01-01 10:01:00"),
        (1, "purchase",   "2026-01-01 10:05:00"),
        # user 2: purchase before click -> does NOT count as ordered funnel
        (2, "impression", "2026-01-01 10:00:00"),
        (2, "purchase",   "2026-01-01 10:01:00"),
        (2, "click",      "2026-01-01 10:02:00"),
    ],
    ["user_id", "event_name", "ts"],
)
events.createOrReplaceTempView("events")

result = spark.sql("""
WITH per_user AS (
  SELECT user_id,
         MIN(CASE WHEN event_name = 'impression' THEN ts END) AS impression_ts,
         MIN(CASE WHEN event_name = 'click'      THEN ts END) AS click_ts,
         MIN(CASE WHEN event_name = 'purchase'   THEN ts END) AS purchase_ts
  FROM events GROUP BY user_id
)
SELECT
  COUNT(*) AS total_users,
  COUNT(CASE WHEN impression_ts IS NOT NULL THEN 1 END) AS reached_impression,
  COUNT(CASE WHEN click_ts IS NOT NULL AND click_ts > impression_ts THEN 1 END) AS reached_click_in_order,
  COUNT(CASE WHEN purchase_ts IS NOT NULL AND purchase_ts > click_ts AND click_ts > impression_ts
             THEN 1 END) AS reached_purchase_in_order
FROM per_user
""")
result.show()

SQL = """
WITH per_user AS (
  SELECT user_id,
         MIN(CASE WHEN event_name = 'impression' THEN ts END) AS impression_ts,
         MIN(CASE WHEN event_name = 'click'      THEN ts END) AS click_ts,
         MIN(CASE WHEN event_name = 'purchase'   THEN ts END) AS purchase_ts
  FROM events GROUP BY user_id
)
SELECT
  COUNT(CASE WHEN impression_ts IS NOT NULL THEN 1 END) AS reached_impression,
  COUNT(CASE WHEN click_ts > impression_ts THEN 1 END) AS reached_click_in_order,
  COUNT(CASE WHEN purchase_ts > click_ts AND click_ts > impression_ts THEN 1 END) AS reached_purchase_in_order
FROM per_user;
"""
