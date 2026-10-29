"""
Problem 08: Unbounded vs Bounded Rolling Retention.

Meta flavor: "Rolling 30-day retention" — of users who signed up on Day 0,
what % had any active event in [Day+1, Day+30]?

How to Think:
- Unbounded = "ever returned" (lifetime retention to date).
- Bounded rolling 30 = "active in [signup+1, signup+30]" — finite window.
- Same skeleton; just adjust the upper bound.

How to Remember:
- "Bounded rolling N: BETWEEN 1 AND N. Unbounded: any positive diff."

AI Use Cases:
- Engagement windows for ML features.
- Re-engagement campaign windows.
- Lifetime value projection (bounded vs unbounded).
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, datediff

spark = SparkSession.builder.getOrCreate()

signups = spark.createDataFrame(
    [(i, "2026-01-01") for i in range(1, 21)],
    ["user_id", "signup_date"],
)
activity = spark.createDataFrame(
    [(i, "2026-01-15") for i in range(1, 11)] +  # day 14: bounded
    [(i, "2026-02-15") for i in range(11, 16)],   # day 45: outside bounded 30, inside unbounded
    ["user_id", "event_date"],
)
signups.createOrReplaceTempView("signups")
activity.createOrReplaceTempView("activity")

result = spark.sql("""
SELECT
  COUNT(DISTINCT s.user_id)                                                          AS cohort,
  -- Bounded rolling 30-day retention
  COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 30
                      THEN s.user_id END)                                            AS bounded_30d,
  -- Unbounded "ever returned" retention
  COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) >= 1
                      THEN s.user_id END)                                            AS unbounded
FROM signups s
LEFT JOIN activity a USING (user_id)
""")
result.show(truncate=False)

SQL = """
SELECT
  COUNT(DISTINCT s.user_id) AS cohort,
  COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 30 THEN s.user_id END) AS bounded_30d,
  COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) >= 1               THEN s.user_id END) AS unbounded
FROM signups s
LEFT JOIN activity a USING (user_id);
"""
