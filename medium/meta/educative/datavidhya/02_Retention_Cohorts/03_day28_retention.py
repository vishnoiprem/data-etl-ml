"""
Problem 03: Day-28 Retention (D28).

Meta flavor: Of users who signed up today, what % returned within 28 days
(typically the "habit-formation" milestone)?

How to Think:
- Two flavors:
  1) Punctual D28 = active on signup_date + 28 only.
  2) Rolling D28 = active at least once in [signup_date + 1, signup_date + 28] (preferred in Meta).

How to Remember:
- "Punctual D28: date = +28. Rolling D28: BETWEEN +1 AND +28."

AI Use Cases:
- Habit-formation tracking.
- 28-day re-engagement campaigns.
- Long-tail retention modeling.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_add

spark = SparkSession.builder.getOrCreate()

signups = spark.createDataFrame(
    [(i, "2026-01-01") for i in range(1, 31)],
    ["user_id", "signup_date"],
)
# 30 users signed up; some active between day 2 and day 29
active_rows = [(i, "2026-02-01") for i in range(1, 11)]   # day 31 - not retained in 28d
active_rows += [(i, "2026-01-29") for i in range(11, 18)]  # day 28 - punctual D28
active_rows += [(i, "2026-01-15") for i in range(18, 25)]  # within rolling 28d
activity = spark.createDataFrame(active_rows, ["user_id", "event_date"])

signups.createOrReplaceTempView("signups")
activity.createOrReplaceTempView("activity")

result = spark.sql("""
SELECT
  COUNT(DISTINCT s.user_id)                                                                       AS cohort,
  -- Punctual D28 (activity on day +28)
  COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 28) THEN s.user_id END)        AS punctual_d28,
  -- Rolling D28 (activity within 1..28 days)
  COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 28
                      THEN s.user_id END)                                                        AS rolling_d28
FROM signups s
LEFT JOIN activity a USING (user_id)
""")
result.show(truncate=False)

SQL = """
SELECT
  COUNT(DISTINCT s.user_id) AS cohort,
  COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 28) THEN s.user_id END) AS punctual_d28,
  COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 28
                      THEN s.user_id END) AS rolling_d28
FROM signups s
LEFT JOIN activity a USING (user_id);
"""
