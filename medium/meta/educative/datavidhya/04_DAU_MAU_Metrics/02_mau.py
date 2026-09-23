"""
Problem 02: MAU (Monthly Active Users).

Meta flavor: For each calendar month, count distinct active users.

How to Think:
- DATE_TRUNC('month', event_date) -> month bucket.
- COUNT(DISTINCT user_id) per month.

How to Remember:
- "MAU(M) = COUNT(DISTINCT user_id) WHERE month(event_date) = M."

AI Use Cases:
- Monthly executive dashboards.
- LTV projection.
- Cohort analysis input.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_trunc

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-05"), (1, "2026-02-05"),  # user 1 in Jan + Feb
     (2, "2026-01-15"),                      # user 2 in Jan
     (3, "2026-02-10"),                      # user 3 in Feb
     (3, "2026-02-20")],
    ["user_id", "event_date"],
)
events.createOrReplaceTempView("events")

result = spark.sql("""
SELECT DATE_TRUNC('month', event_date) AS month,
       COUNT(DISTINCT user_id)         AS mau
FROM events
GROUP BY DATE_TRUNC('month', event_date)
ORDER BY month
""")
result.show()

SQL = """
SELECT DATE_TRUNC('month', event_date) AS month,
       COUNT(DISTINCT user_id)         AS mau
FROM events
GROUP BY DATE_TRUNC('month', event_date)
ORDER BY 1;
"""
