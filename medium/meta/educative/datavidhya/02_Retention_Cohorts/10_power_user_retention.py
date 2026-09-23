"""
Problem 10: Power-User Retention Curves (top-decile vs median).

Meta flavor: Compare retention of top-decile users (by lifetime engagement)
against median users. Top-decile curve must stay much higher.

How to Think:
- Step 1: Compute lifetime events per user; bucket via NTILE(10).
- Step 2: Join bucket back to signups + activity; compute retention per bucket.
- Step 3: Plot / return both curves for comparison.

How to Remember:
- "NTILE -> bucket -> retention by bucket."

AI Use Cases:
- Power-user feature treatment.
- Tiered engagement strategy.
- Cohort forecasting by user segment.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, countDistinct, ntile, date_add
from pyspark.sql.window import Window

spark = SparkSession.builder.getOrCreate()

signups = spark.createDataFrame(
    [(i, "2026-01-01") for i in range(1, 11)],
    ["user_id", "signup_date"],
)
# Different activity volumes per user
activity = spark.createDataFrame(
    [(1, d) for d in range(1, 6)] +     # user 1: 5 events
    [(2, d) for d in range(1, 11)] +    # user 2: 10 events
    [(3, d) for d in range(1, 16)] +    # user 3: 15 events -> top decile proxy
    [(4, d) for d in range(1, 3)] +     # user 4: 2 events
    [(5, d) for d in range(1, 4)] +
    [(6, d) for d in range(1, 2)] +
    [(7, d) for d in range(1, 2)] +
    [(8, d) for d in range(1, 2)] +
    [(9, d) for d in range(1, 2)] +
    [(10, d) for d in range(1, 2)],
    ["user_id", "event_day"],
)
activity.createOrReplaceTempView("activity")
signups.createOrReplaceTempView("signups")

# Compute lifetime activity and bucket
activity_with_dt = spark.sql("""
  SELECT user_id, DATE_ADD(CAST('2026-01-01' AS DATE), CAST(event_day AS INT)) AS event_date
  FROM activity
""")
activity_with_dt.createOrReplaceTempView("activity_dt")

buckets = spark.sql("""
  SELECT user_id, NTILE(10) OVER (ORDER BY COUNT(*) DESC) AS engagement_decile
  FROM activity_dt
  GROUP BY user_id
""")
buckets.createOrReplaceTempView("buckets")

result = spark.sql("""
SELECT b.engagement_decile,
       COUNT(DISTINCT s.user_id) AS cohort,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 7
                           THEN s.user_id END) AS d7_retained,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 7
                           THEN s.user_id END) * 1.0 / COUNT(DISTINCT s.user_id) AS d7_retention
FROM signups s
JOIN buckets b USING (user_id)
LEFT JOIN activity_dt a USING (user_id)
GROUP BY b.engagement_decile
ORDER BY b.engagement_decile
""")
result.show()

SQL = """
WITH lifetime AS (
  SELECT user_id, COUNT(*) AS lifetime_events FROM activity GROUP BY user_id
),
buckets AS (
  SELECT user_id, NTILE(10) OVER (ORDER BY lifetime_events DESC) AS decile FROM lifetime
)
SELECT b.decile,
       COUNT(DISTINCT s.user_id) AS cohort,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 7
                           THEN s.user_id END) AS d7_retained,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 7
                           THEN s.user_id END) * 1.0 / COUNT(DISTINCT s.user_id) AS d7_retention
FROM signups s JOIN buckets b USING (user_id)
LEFT JOIN activity a ON a.user_id = s.user_id
GROUP BY b.decile ORDER BY 1;
"""
