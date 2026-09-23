"""
Problem 08: Top-100 Users by Stickiness.

Meta flavor: Per-user stickiness = active days in last 28 / 28. Return top 100
users by this metric — Meta uses this list for early-access beta programs.

How to Think:
- Per user, count distinct active days in the 28-day window.
- Divide by 28.
- Rank, take top 100.

How to Remember:
- "active_days_in_28 / 28. ROW_NUMBER or RANK."

AI Use Cases:
- Power-user identification for beta programs.
- ML feature for personalization.
- Reward-program eligibility.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, row_number, date_sub
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, d) for d in range(1, 29)] +  # user 1: every day = stickiness 1.0
    [(2, d) for d in range(1, 15)] +  # user 2: 14 days
    [(3, d) for d in range(1, 5)] +   # user 3: 4 days
    [(4, d) for d in [1, 5, 10]],      # user 4: 3 days
    ["user_id", "event_date"]
)
events.createOrReplaceTempView("events")

result = spark.sql("""
WITH window_bounds AS (SELECT MAX(event_date) AS end_date FROM events),
per_user AS (
  SELECT user_id, COUNT(DISTINCT event_date) AS active_days
  FROM events, window_bounds
  WHERE event_date BETWEEN DATE_SUB(end_date, 27) AND end_date
  GROUP BY user_id
)
SELECT user_id, active_days, active_days / 28.0 AS stickiness
FROM per_user
ORDER BY stickiness DESC
LIMIT 100
""")
result.show()

SQL = """
WITH bounds AS (SELECT MAX(event_date) AS end_date FROM events)
SELECT user_id,
       COUNT(DISTINCT event_date) / 28.0 AS stickiness
FROM events, bounds
WHERE event_date BETWEEN DATE_SUB(end_date, 27) AND end_date
GROUP BY user_id
ORDER BY stickiness DESC
LIMIT 100;
"""
