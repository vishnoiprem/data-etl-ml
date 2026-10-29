"""
Q02: 7-Day Retention Cohort Analysis   [Hard | CTEs, Date Functions]

Calculate day-1 and day-7 retention by WEEKLY signup cohort.

How to Think:
- Two groupings stacked: cohort = week of signup, offset = day since signup.
- Cohort the user ONCE at signup; never re-cohort them by activity date.
- DATE_TRUNC('WEEK', d) in Spark starts weeks on MONDAY. State that out loud —
  if the business defines weeks Sunday-start your numbers silently shift.
- LEFT JOIN each offset separately, or join once and aggregate conditionally.
  The conditional-aggregation form below scans `activity` once instead of twice,
  which is the version to write when the table is billions of rows.

The trap:
- Denominator must be the cohort size, not the number of users who returned.

Spark note:
- One pass over activity + one broadcastable signups side = cheap.
  On real data, broadcast the small cohort table: /*+ BROADCAST(s) */
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("02-weekly-retention-cohort")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")


def expect(title, sql, expected_rows):
    """Run a query and assert its exact rows, in order. Decimal/float safe."""
    import decimal

    def norm(v):
        if isinstance(v, decimal.Decimal):
            return float(v)
        if isinstance(v, float):
            return round(v, 6)
        return v

    got = [tuple(norm(c) for c in r) for r in spark.sql(sql).collect()]
    exp = [tuple(norm(c) for c in r) for r in expected_rows]
    if got != exp:
        print(f"[FAIL] {title}")
        print(f"   expected: {exp}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")
    return got


# ---------------------------------------------------------- sample data
spark.createDataFrame(
    [
    (1, "2026-01-05"), (2, "2026-01-06"), (3, "2026-01-07"),
    (4, "2026-01-12"), (5, "2026-01-13"),
],
    ["user_id", "signup_date"]
).createOrReplaceTempView("signups")

spark.createDataFrame(
    [
    (1, "2026-01-05"), (1, "2026-01-06"), (1, "2026-01-12"),   # D0,D1,D7
    (2, "2026-01-06"), (2, "2026-01-07"),                      # D0,D1
    (3, "2026-01-07"),                                         # D0 only
    (4, "2026-01-12"), (4, "2026-01-13"), (4, "2026-01-19"),   # D0,D1,D7
    (5, "2026-01-13"),                                         # D0 only
],
    ["user_id", "activity_date"]
).createOrReplaceTempView("activity")

from pyspark.sql import functions as F

SQL = """
WITH cohorts AS (
    SELECT user_id,
           signup_date,
           DATE_TRUNC('WEEK', signup_date) AS cohort_week
    FROM signups
)
SELECT CAST(c.cohort_week AS DATE) AS cohort_week,
       COUNT(DISTINCT c.user_id) AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.activity_date = DATE_ADD(c.signup_date, 1)
                           THEN a.user_id END) AS d1_users,
       COUNT(DISTINCT CASE WHEN a.activity_date = DATE_ADD(c.signup_date, 7)
                           THEN a.user_id END) AS d7_users,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.activity_date = DATE_ADD(c.signup_date, 1)
                                         THEN a.user_id END)
                   / COUNT(DISTINCT c.user_id), 2) AS d1_pct,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.activity_date = DATE_ADD(c.signup_date, 7)
                                         THEN a.user_id END)
                   / COUNT(DISTINCT c.user_id), 2) AS d7_pct
FROM cohorts c
LEFT JOIN activity a ON a.user_id = c.user_id
GROUP BY c.cohort_week
ORDER BY c.cohort_week
"""

import datetime as _dt
expect("Q02 weekly D1/D7 retention", SQL, [
    (_dt.date(2026, 1, 5), 3, 2, 1, 66.67, 33.33),
    (_dt.date(2026, 1, 12), 2, 1, 1, 50.00, 50.00),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports CTEs and DATE_ADD. The conditional-aggregate form scans
# `activity` once and uses COUNT(DISTINCT CASE WHEN ... THEN user_id END) to
# count cohort members who returned on day 1 / day 7. The cohort grain is
# fixed at signup -- never re-cohort by activity_date. The week boundary is
# Spark's Monday start; MySQL has no exact equivalent of DATE_TRUNC('WEEK'),
# so use DATE_SUB(d, INTERVAL WEEKDAY(d) DAY) to snap to Monday.
#
# CREATE TABLE signups (
#     user_id     INT  NOT NULL,
#     signup_date DATE NOT NULL,
#     PRIMARY KEY (user_id),
#     KEY ix_signups_date (signup_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE activity (
#     user_id       INT  NOT NULL,
#     activity_date DATE NOT NULL,
#     PRIMARY KEY (user_id, activity_date),
#     KEY ix_activity_date (activity_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO signups (user_id, signup_date) VALUES
#     (1, '2026-01-05'), (2, '2026-01-06'), (3, '2026-01-07'),
#     (4, '2026-01-12'), (5, '2026-01-13');
#
# INSERT INTO activity (user_id, activity_date) VALUES
#     (1, '2026-01-05'), (1, '2026-01-06'), (1, '2026-01-12'),
#     (2, '2026-01-06'), (2, '2026-01-07'),
#     (3, '2026-01-07'),
#     (4, '2026-01-12'), (4, '2026-01-13'), (4, '2026-01-19'),
#     (5, '2026-01-13');
#
# WITH cohorts AS (
#     SELECT user_id,
#            signup_date,
#            DATE_SUB(signup_date, INTERVAL WEEKDAY(signup_date) DAY) AS cohort_week
#     FROM signups
# )
# SELECT c.cohort_week,
#        COUNT(DISTINCT c.user_id) AS cohort_size,
#        COUNT(DISTINCT CASE WHEN a.activity_date = DATE_ADD(c.signup_date, 1)
#                            THEN a.user_id END) AS d1_users,
#        COUNT(DISTINCT CASE WHEN a.activity_date = DATE_ADD(c.signup_date, 7)
#                            THEN a.user_id END) AS d7_users,
#        ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.activity_date = DATE_ADD(c.signup_date, 1)
#                                          THEN a.user_id END)
#                    / COUNT(DISTINCT c.user_id), 2) AS d1_pct,
#        ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.activity_date = DATE_ADD(c.signup_date, 7)
#                                          THEN a.user_id END)
#                    / COUNT(DISTINCT c.user_id), 2) AS d7_pct
# FROM cohorts c
# LEFT JOIN activity a ON a.user_id = c.user_id
# GROUP BY c.cohort_week
# ORDER BY c.cohort_week;
#
# -- Expected:
# -- 2026-01-05  3  2  1  66.67  33.33
# -- 2026-01-12  2  1  1  50.00  50.00
