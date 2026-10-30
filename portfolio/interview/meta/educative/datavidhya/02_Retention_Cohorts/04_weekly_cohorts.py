"""
Problem 04: Weekly Retention Cohorts.

Meta flavor: Group signups by signup-week, then show how each cohort retains
over the next 8 weeks (Mon-Sun alignment).

How to Think:
- Step 1: Derive signup_week (DATE_TRUNC('week', signup_date)).
- Step 2: For each cohort, for each week_offset in 0..8, count distinct active users.
- Step 3: Pivot for readability OR keep long format.

How to Remember:
- "DATE_TRUNC('week', dt) -> cohort. DATEDIFF('week', ...) -> offset."

AI Use Cases:
- Cohort dashboards.
- Long-term retention tracking.
- Churn-risk feature engineering.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_trunc, datediff, floor

spark = SparkSession.builder.getOrCreate()

signups = spark.createDataFrame(
    [(i, f"2026-01-{(i % 7) + 1:02d}") for i in range(1, 15)],
    ["user_id", "signup_date"],
)
activity = spark.createDataFrame(
    [(i, "2026-01-15") for i in range(1, 11)],
    ["user_id", "event_date"],
)
signups.createOrReplaceTempView("signups")
activity.createOrReplaceTempView("activity")

result = spark.sql("""
SELECT
  DATE_TRUNC('week', s.signup_date)                                       AS cohort_week,
  FLOOR(DATEDIFF(a.event_date, s.signup_date) / 7)                        AS week_offset,
  COUNT(DISTINCT s.user_id)                                               AS active_users
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY DATE_TRUNC('week', s.signup_date), FLOOR(DATEDIFF(a.event_date, s.signup_date) / 7)
ORDER BY cohort_week, week_offset
""")
result.show()

SQL = """
SELECT
  DATE_TRUNC('week', s.signup_date)                                AS cohort_week,
  FLOOR(DATEDIFF(a.event_date, s.signup_date) / 7)                 AS week_offset,
  COUNT(DISTINCT s.user_id)                                        AS active_users
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY 1, 2
ORDER BY 1, 2;
"""
