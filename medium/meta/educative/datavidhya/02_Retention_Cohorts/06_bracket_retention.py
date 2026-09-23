"""
Problem 06: Bracket Retention (D1, D7, D28 in ONE query).

Meta flavor: PM wants all three retention numbers in one row per cohort
to feed a single dashboard tile.

How to Think:
- Each bracket is a separate CASE WHEN with COUNT(DISTINCT).
- One JOIN with activity, multiple CASE branches.
- Compute cohort_size once via window or subquery.

How to Remember:
- "Cohort + 3 CASE WHEN -> D1, D7, D28 in one pass."

AI Use Cases:
- Single dashboard query.
- Cohort summary tables.
- A/B test retention deltas.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_add

spark = SparkSession.builder.getOrCreate()

signups = spark.createDataFrame(
    [(1, "2026-01-01"), (2, "2026-01-01"), (3, "2026-01-01")],
    ["user_id", "signup_date"],
)
activity = spark.createDataFrame(
    [(1, "2026-01-02"),  # D1 for user 1
     (2, "2026-01-08"),  # D7 for user 2
     (3, "2026-01-29")], # D28 for user 3
    ["user_id", "event_date"],
)
signups.createOrReplaceTempView("signups")
activity.createOrReplaceTempView("activity")

result = spark.sql("""
SELECT s.signup_date,
       COUNT(DISTINCT s.user_id)                                                                AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 1)  THEN s.user_id END) AS retained_d1,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7)  THEN s.user_id END) AS retained_d7,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 28) THEN s.user_id END) AS retained_d28
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY s.signup_date
""")
result.show()

SQL = """
SELECT s.signup_date,
       COUNT(DISTINCT s.user_id)                                                                AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 1)  THEN s.user_id END) AS retained_d1,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7)  THEN s.user_id END) AS retained_d7,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 28) THEN s.user_id END) AS retained_d28
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY s.signup_date;
"""
