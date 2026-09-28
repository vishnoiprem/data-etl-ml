"""
Q06: Monthly Active, Churned, and Resurrected Users   [Medium | Windows, CTEs]

From a user activity log, compute per month: MAU, new, churned, resurrected.

How to Think:
- Four mutually-exclusive-ish states, all defined by comparing THIS month's
  active set to PRIOR months. Define each precisely BEFORE writing SQL:
    MAU         = distinct users active this month
    new         = first-ever active month is this month
    churned     = active last month, NOT active this month
    resurrected = active this month, NOT last month, but active some month
                  before that
- "Resurrected" is what separates a strong answer from an average one. Most
  candidates conflate it with "new". The distinguishing test is whether the
  user has ANY earlier activity, which is MIN(month) < previous month.
- Churn is attributed to the month the user is ABSENT, so a churn row describes
  a user who has no row in that month. You cannot GROUP BY a month the user is
  missing from — you need the month spine, hence the cross join.

Spark note:
- Build a small month spine and cross join it to distinct users. That is a
  broadcast on the spine, so it stays cheap even at billions of events.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("06-mau-churn-resurrect")
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
    (1, "2026-01-10"), (1, "2026-02-10"), (1, "2026-03-10"),
    (2, "2026-01-15"),
    (3, "2026-02-20"), (3, "2026-03-05"),
    (4, "2026-01-05"), (4, "2026-03-25"),
],
    ["user_id", "event_date"]
).createOrReplaceTempView("activity_log")


SQL = """
WITH um AS (            -- one row per user per active month
    SELECT DISTINCT user_id, DATE_FORMAT(event_date, 'yyyy-MM') AS ym
    FROM activity_log
),
first_seen AS (
    SELECT user_id, MIN(ym) AS first_ym FROM um GROUP BY user_id
),
months AS (SELECT DISTINCT ym FROM um),
grid AS (               -- every user x every month, with activity flags
    SELECT m.ym,
           u.user_id,
           CASE WHEN a.user_id IS NOT NULL THEN 1 ELSE 0 END AS active,
           f.first_ym
    FROM months m
    CROSS JOIN (SELECT DISTINCT user_id FROM um) u
    LEFT JOIN um a ON a.user_id = u.user_id AND a.ym = m.ym
    JOIN first_seen f ON f.user_id = u.user_id
),
flagged AS (
    SELECT ym, user_id, active, first_ym,
           LAG(active) OVER (PARTITION BY user_id ORDER BY ym) AS prev_active
    FROM grid
)
SELECT ym,
       SUM(active) AS mau,
       SUM(CASE WHEN active = 1 AND ym = first_ym THEN 1 ELSE 0 END) AS new_users,
       SUM(CASE WHEN active = 0 AND prev_active = 1 THEN 1 ELSE 0 END) AS churned,
       SUM(CASE WHEN active = 1 AND prev_active = 0 AND ym > first_ym
                THEN 1 ELSE 0 END) AS resurrected
FROM flagged
GROUP BY ym
ORDER BY ym
"""

expect("Q06 mau/new/churned/resurrected", SQL, [
    ("2026-01", 3, 3, 0, 0),
    ("2026-02", 2, 1, 2, 0),
    ("2026-03", 3, 0, 0, 1),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports CTEs, LAG, and the user x month grid via CROSS JOIN.
# The month grain is DATE_FORMAT(event_date, '%Y-%m') (MySQL's pattern codes,
# not Spark's Java-style 'yyyy-MM'). The "resurrected" definition is what
# separates a strong answer from an average one -- it requires an earlier
# activity month, not just a gap from the previous month.
#
# CREATE TABLE activity_log (
#     user_id    INT  NOT NULL,
#     event_date DATE NOT NULL,
#     KEY ix_al_user_date (user_id, event_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO activity_log (user_id, event_date) VALUES
#     (1, '2026-01-10'), (1, '2026-02-10'), (1, '2026-03-10'),
#     (2, '2026-01-15'),
#     (3, '2026-02-20'), (3, '2026-03-05'),
#     (4, '2026-01-05'), (4, '2026-03-25');
#
# WITH um AS (            -- one row per user per active month
#     SELECT DISTINCT user_id, DATE_FORMAT(event_date, '%Y-%m') AS ym
#     FROM activity_log
# ),
# first_seen AS (
#     SELECT user_id, MIN(ym) AS first_ym FROM um GROUP BY user_id
# ),
# months AS (SELECT DISTINCT ym FROM um),
# grid AS (               -- every user x every month, with activity flags
#     SELECT m.ym,
#            u.user_id,
#            CASE WHEN a.user_id IS NOT NULL THEN 1 ELSE 0 END AS active,
#            f.first_ym
#     FROM months m
#     CROSS JOIN (SELECT DISTINCT user_id FROM um) u
#     LEFT JOIN um a ON a.user_id = u.user_id AND a.ym = m.ym
#     JOIN first_seen f ON f.user_id = u.user_id
# ),
# flagged AS (
#     SELECT ym, user_id, active, first_ym,
#            LAG(active) OVER (PARTITION BY user_id ORDER BY ym) AS prev_active
#     FROM grid
# )
# SELECT ym,
#        SUM(active) AS mau,
#        SUM(CASE WHEN active = 1 AND ym = first_ym THEN 1 ELSE 0 END) AS new_users,
#        SUM(CASE WHEN active = 0 AND prev_active = 1 THEN 1 ELSE 0 END) AS churned,
#        SUM(CASE WHEN active = 1 AND prev_active = 0 AND ym > first_ym
#                 THEN 1 ELSE 0 END) AS resurrected
# FROM flagged
# GROUP BY ym
# ORDER BY ym;
#
# -- Expected:
# -- 2026-01  3  3  0  0
# -- 2026-02  2  1  2  0
# -- 2026-03  3  0  0  1
