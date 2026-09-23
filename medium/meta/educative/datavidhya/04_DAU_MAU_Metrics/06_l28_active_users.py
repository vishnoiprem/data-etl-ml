"""
Problem 06: L28 Active Users.

Meta flavor: Habituation metric — active in last 28 days.

How to Think:
- Same as L7 but with a 28-day window.
- Often used as a "monthly active" proxy in Meta products.

How to Remember:
- "L28(D) = COUNT(DISTINCT) WHERE event_date BETWEEN D-27 AND D."

AI Use Cases:
- Habit-formation metric.
- Engagement features for ranking.
- Lifecycle-stage classification.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_sub

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-01"), (1, "2026-01-15"), (1, "2026-01-25"),
     (2, "2026-01-05"),
     (3, "2026-02-15")],
    ["user_id", "event_date"],
)
events.createOrReplaceTempView("events")

result = spark.sql("""
WITH days AS (SELECT DISTINCT event_date AS dt FROM events)
SELECT d.dt,
       COUNT(DISTINCT e.user_id) AS l28_active_users
FROM days d
LEFT JOIN events e ON e.event_date BETWEEN DATE_SUB(d.dt, 27) AND d.dt
GROUP BY d.dt
ORDER BY d.dt
""")
result.show()

SQL = """
WITH days AS (SELECT DISTINCT event_date AS dt FROM events)
SELECT d.dt,
       COUNT(DISTINCT e.user_id) AS l28_active_users
FROM days d
LEFT JOIN events e ON e.event_date BETWEEN DATE_SUB(d.dt, 27) AND d.dt
GROUP BY d.dt
ORDER BY d.dt;
"""
