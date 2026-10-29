"""
Problem 01: Day-1 Retention (D1).

Meta flavor: Of users who signed up today, what % came back and produced any
active event tomorrow?

How to Think:
- Step 1: Get users who signed up (signup event).
- Step 2: Get users active on day N (active event).
- Step 3: For each signup_date, count distinct users active on signup_date + 1.

How to Remember:
- "Signups -> cohorts -> Day-N-active join -> aggregate."

AI Use Cases:
- Onboarding funnel health check.
- New-user activation modeling.
- Retention as a feature in recommendation systems.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_add

spark = SparkSession.builder.getOrCreate()

signups = spark.createDataFrame(
    [(1, "2026-01-01"), (2, "2026-01-01"), (3, "2026-01-01"), (4, "2026-01-02")],
    ["user_id", "signup_date"],
)
activity = spark.createDataFrame(
    [(1, "2026-01-01"), (1, "2026-01-02"),  # user 1: D0+D1
     (2, "2026-01-02"),                    # user 2: D0+D1
     (3, "2026-01-04"),                    # user 3: D0 only
     (4, "2026-01-03"), (4, "2026-01-04")], # user 4: D1+D2
    ["user_id", "event_date"],
)

# D1 retention
signups.createOrReplaceTempView("signups")
activity.createOrReplaceTempView("activity")

result = spark.sql("""
SELECT s.signup_date,
       COUNT(DISTINCT s.user_id)                                            AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 1)
                           THEN s.user_id END)                              AS retained_d1,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 1)
                           THEN s.user_id END) * 1.0 / COUNT(DISTINCT s.user_id) AS d1_retention
FROM signups s
LEFT JOIN activity a ON s.user_id = a.user_id
GROUP BY s.signup_date
ORDER BY s.signup_date
""")
result.show()

SQL = """
SELECT s.signup_date,
       COUNT(DISTINCT s.user_id)                                            AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 1)
                           THEN s.user_id END)                              AS retained_d1,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 1)
                           THEN s.user_id END) * 1.0 / COUNT(DISTINCT s.user_id) AS d1_retention
FROM signups s
LEFT JOIN activity a ON s.user_id = a.user_id
GROUP BY s.signup_date;
"""
