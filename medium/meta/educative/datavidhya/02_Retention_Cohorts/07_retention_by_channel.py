"""
Problem 07: Retention by Acquisition Channel.

Meta flavor: Growth team wants D7 retention segmented by signup_channel
(organic, paid_insta, paid_fb) so they can reallocate spend.

How to Think:
- Add signup_channel to the join key (or to signups; assume it lives there).
- GROUP BY (signup_date, signup_channel) for cohort-level breakdown.
- Compare retention across channels with side-by-side columns.

How to Remember:
- "Group by (cohort_date, cohort_channel) -> retention per segment."

AI Use Cases:
- Marketing attribution + retention modeling.
- Channel ROI computation.
- Incrementality / uplift features.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_add

spark = SparkSession.builder.getOrCreate()

signups = spark.createDataFrame(
    [(1, "2026-01-01", "organic"),
     (2, "2026-01-01", "paid_fb"),
     (3, "2026-01-01", "paid_fb"),
     (4, "2026-01-01", "organic")],
    ["user_id", "signup_date", "signup_channel"],
)
activity = spark.createDataFrame(
    [(1, "2026-01-08"),
     (2, "2026-01-08"),
     (4, "2026-01-08")],
    ["user_id", "event_date"],
)
signups.createOrReplaceTempView("signups")
activity.createOrReplaceTempView("activity")

result = spark.sql("""
SELECT s.signup_date,
       s.signup_channel,
       COUNT(DISTINCT s.user_id)                                                                AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7) THEN s.user_id END)   AS retained_d7,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7) THEN s.user_id END) * 1.0
         / COUNT(DISTINCT s.user_id)                                                            AS d7_retention
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY s.signup_date, s.signup_channel
ORDER BY s.signup_date, s.signup_channel
""")
result.show()

SQL = """
SELECT s.signup_date,
       s.signup_channel,
       COUNT(DISTINCT s.user_id) AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7) THEN s.user_id END) AS retained_d7,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7) THEN s.user_id END) * 1.0
         / COUNT(DISTINCT s.user_id) AS d7_retention
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY s.signup_date, s.signup_channel
ORDER BY 1, 2;
"""
