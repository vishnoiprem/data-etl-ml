"""
Problem 05: L7 Active Users (active in last 7 days).

Meta flavor: For each day, how many distinct users were active in the
preceding 7 days (inclusive)?

How to Think:
- For each day D, count distinct users with event_date in [D-6, D].
- Self-join or use a window + range.

How to Remember:
- "L7(D) = COUNT(DISTINCT user_id) WHERE event_date BETWEEN D-6 AND D."

AI Use Cases:
- Reach metric for ad campaigns.
- Power-user targeting.
- Cohort feature for ranking.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_sub

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-01"), (1, "2026-01-03"), (1, "2026-01-05"),
     (2, "2026-01-02"),
     (3, "2026-01-08")],
    ["user_id", "event_date"],
)
events.createOrReplaceTempView("events")

result = spark.sql("""
WITH days AS (SELECT DISTINCT event_date AS dt FROM events)
SELECT d.dt,
       COUNT(DISTINCT e.user_id) AS l7_active_users
FROM days d
LEFT JOIN events e ON e.event_date BETWEEN DATE_SUB(d.dt, 6) AND d.dt
GROUP BY d.dt
ORDER BY d.dt
""")
result.show()

SQL = """
WITH days AS (SELECT DISTINCT event_date AS dt FROM events)
SELECT d.dt,
       COUNT(DISTINCT e.user_id) AS l7_active_users
FROM days d
LEFT JOIN events e ON e.event_date BETWEEN DATE_SUB(d.dt, 6) AND d.dt
GROUP BY d.dt
ORDER BY d.dt;
"""
