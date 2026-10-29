"""
Problem 02: Day-7 Retention (D7).

Meta flavor: Of users who signed up on Day 0, what % were active on Day 7?

How to Think:
- Same framework as D1 with DATE_ADD(signup_date, 7) or DATEDIFF(event_date, signup_date) = 7.
- DATEDIFF is more robust to timezones; DATE_ADD forces a calendar date.

How to Remember:
- "D7 = activity exactly 7 calendar days after signup."
- Or use DATEDIFF >= 7 AND DATEDIFF < 8 for week-wide windows.

AI Use Cases:
- Cohort performance tracking.
- New product feature ramp-up.
- Lifecycle stage classification.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_add, datediff

spark = SparkSession.builder.getOrCreate()

signups = spark.createDataFrame(
    [(i, f"2026-01-{(i % 5) + 1:02d}") for i in range(1, 6)],
    ["user_id", "signup_date"],
)
activity = spark.createDataFrame(
    [(1, "2026-01-08"),
     (2, "2026-01-09"),
     (3, "2026-01-07"),  # too early
     (4, "2026-01-13"),
     (5, "2026-01-12")],
    ["user_id", "event_date"],
)
signups.createOrReplaceTempView("signups")
activity.createOrReplaceTempView("activity")

result = spark.sql("""
SELECT s.signup_date,
       COUNT(DISTINCT s.user_id) AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7)
                           THEN s.user_id END) AS retained_d7,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7)
                           THEN s.user_id END) * 1.0 / COUNT(DISTINCT s.user_id) AS d7_retention
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY s.signup_date
ORDER BY s.signup_date
""")
result.show()

SQL = """
SELECT s.signup_date,
       COUNT(DISTINCT s.user_id) AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7)
                           THEN s.user_id END) AS retained_d7,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7)
                           THEN s.user_id END) * 1.0 / COUNT(DISTINCT s.user_id) AS d7_retention
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY s.signup_date;
"""
