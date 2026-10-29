"""
Problem 01: Classic 4-step funnel (impression -> click -> add_to_cart -> purchase).

Meta flavor: Marketplace funnel — listing_viewed, message_sent, offer_made,
offer_accepted. PM wants the count at each step.

How to Think:
- For each event, count distinct user_ids (or listing_ids).
- Use a sequence of conditional aggregations.
- Express results as a single row with step columns.

How to Remember:
- "Count distinct per step, pivot via MAX(CASE WHEN event = step THEN 1 END)."

AI Use Cases:
- Conversion optimization at each funnel step.
- Drop-off point identification.
- Funnel features for downstream ML.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, max as smax

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [
        # 100 impressions, 50 clicks, 20 add_to_cart, 5 purchases
        (i, "impression", "2026-01-01") for i in range(1, 101)
    ] + [
        (i, "click",        "2026-01-01") for i in range(1, 51)
    ] + [
        (i, "add_to_cart",  "2026-01-01") for i in range(1, 21)
    ] + [
        (i, "purchase",     "2026-01-01") for i in range(1, 6)
    ],
    ["user_id", "event_name", "event_date"],
)
events.createOrReplaceTempView("events")

result = spark.sql("""
SELECT
  COUNT(DISTINCT CASE WHEN event_name = 'impression'   THEN user_id END) AS step1_impression,
  COUNT(DISTINCT CASE WHEN event_name = 'click'        THEN user_id END) AS step2_click,
  COUNT(DISTINCT CASE WHEN event_name = 'add_to_cart'  THEN user_id END) AS step3_add_to_cart,
  COUNT(DISTINCT CASE WHEN event_name = 'purchase'     THEN user_id END) AS step4_purchase
FROM events
WHERE event_date = '2026-01-01'
""")
result.show()

SQL = """
SELECT
  COUNT(DISTINCT CASE WHEN event_name = 'impression'   THEN user_id END) AS step1_impression,
  COUNT(DISTINCT CASE WHEN event_name = 'click'        THEN user_id END) AS step2_click,
  COUNT(DISTINCT CASE WHEN event_name = 'add_to_cart'  THEN user_id END) AS step3_add_to_cart,
  COUNT(DISTINCT CASE WHEN event_name = 'purchase'     THEN user_id END) AS step4_purchase
FROM events;
"""
