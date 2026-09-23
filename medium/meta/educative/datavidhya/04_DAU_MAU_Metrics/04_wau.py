"""
Problem 04: WAU (Weekly Active Users).

Meta flavor: For each calendar week (Mon-Sun), count distinct active users.

How to Think:
- DATE_TRUNC('week', event_date) -> week bucket.
- COUNT(DISTINCT user_id) per week.

How to Remember:
- "WAU(W) = COUNT(DISTINCT user_id) WHERE week(event_date) = W."

AI Use Cases:
- Weekly growth dashboards.
- WAU/MAU comparison for stickiness.
- Short-cycle engagement tracking.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_trunc

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-05"),  # Mon of W1
     (1, "2026-01-07"),  # same week
     (2, "2026-01-05"),
     (3, "2026-01-12"),  # next week
     (4, "2026-01-19")],
    ["user_id", "event_date"],
)
events.createOrReplaceTempView("events")

result = spark.sql("""
SELECT DATE_TRUNC('week', event_date) AS week_start,
       COUNT(DISTINCT user_id)         AS wau
FROM events
GROUP BY DATE_TRUNC('week', event_date)
ORDER BY week_start
""")
result.show()

SQL = """
SELECT DATE_TRUNC('week', event_date) AS week_start,
       COUNT(DISTINCT user_id)         AS wau
FROM events
GROUP BY DATE_TRUNC('week', event_date)
ORDER BY 1;
"""
