"""
Problem 05: Retention Heatmap (cohort x day-N pivot).

Meta flavor: PM wants a heatmap: rows = signup-week cohorts, columns = week 0..7.
Cell value = retention rate.

How to Think:
- Step 1: Compute weekly cohort + week_offset + active count (problem 04).
- Step 2: Divide active_count by cohort_size to get retention rate.
- Step 3: Pivot to wide format using conditional aggregation (Presto lacks PIVOT in older versions).

How to Remember:
- "Long -> wide via SUM(CASE WHEN offset = N THEN rate END)."

AI Use Cases:
- Cohort dashboards.
- Heatmap visualization for retention.
- Feature creation (per-cohort retention rate).
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, countDistinct, date_trunc, datediff, floor, first

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
WITH cohort_sizes AS (
  SELECT DATE_TRUNC('week', signup_date) AS cohort_week,
         COUNT(DISTINCT user_id) AS cohort_size
  FROM signups
  GROUP BY 1
),
activity_long AS (
  SELECT DATE_TRUNC('week', s.signup_date) AS cohort_week,
         FLOOR(DATEDIFF(a.event_date, s.signup_date) / 7) AS week_offset,
         COUNT(DISTINCT s.user_id) AS active_users
  FROM signups s
  LEFT JOIN activity a USING (user_id)
  GROUP BY 1, 2
)
SELECT
  a.cohort_week,
  MAX(CASE WHEN week_offset = 0 THEN active_users END) * 1.0 / MAX(cs.cohort_size) AS w0,
  MAX(CASE WHEN week_offset = 1 THEN active_users END) * 1.0 / MAX(cs.cohort_size) AS w1,
  MAX(CASE WHEN week_offset = 2 THEN active_users END) * 1.0 / MAX(cs.cohort_size) AS w2
FROM activity_long a
JOIN cohort_sizes cs USING (cohort_week)
GROUP BY a.cohort_week
ORDER BY a.cohort_week
""")
result.show()

SQL = """
WITH cohort_sizes AS (
  SELECT DATE_TRUNC('week', signup_date) AS cohort_week,
         COUNT(DISTINCT user_id) AS cohort_size
  FROM signups GROUP BY 1
),
activity_long AS (
  SELECT DATE_TRUNC('week', s.signup_date) AS cohort_week,
         FLOOR(DATEDIFF(a.event_date, s.signup_date) / 7) AS week_offset,
         COUNT(DISTINCT s.user_id) AS active_users
  FROM signups s LEFT JOIN activity a USING (user_id)
  GROUP BY 1, 2
)
SELECT
  a.cohort_week,
  MAX(CASE WHEN week_offset = 0 THEN active_users END) * 1.0 / MAX(cs.cohort_size) AS w0,
  MAX(CASE WHEN week_offset = 1 THEN active_users END) * 1.0 / MAX(cs.cohort_size) AS w1,
  MAX(CASE WHEN week_offset = 2 THEN active_users END) * 1.0 / MAX(cs.cohort_size) AS w2
FROM activity_long a JOIN cohort_sizes cs USING (cohort_week)
GROUP BY 1 ORDER BY 1;
"""
