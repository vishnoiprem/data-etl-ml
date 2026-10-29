"""
Problem 05: L7 Active Users (active in last 7 days).

Meta flavor: For each day, how many distinct users were active in the
preceding 7 days (inclusive)?

How to Think:
- For each day D, count distinct users with event_date in [D-6, D].
- Self-join or use a window + range.

How to Remember:
- "L7(D) = COUNT(DISTINCT user_id) WHERE event_date BETWEEN D-6 AND D."

AI Use Cases:
- Reach metric for ad campaigns.
- Power-user targeting.
- Cohort feature for ranking.

================================================================================
MySQL 8.0+ version (no window functions, no recursive CTE):
================================================================================
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct, date_sub

spark = SparkSession.builder.getOrCreate()

events = spark.createDataFrame(
    [(1, "2026-01-01"), (1, "2026-01-03"), (1, "2026-01-05"),
     (2, "2026-01-02"),
     (3, "2026-01-08")],
    ["user_id", "event_date"],
)
events.createOrReplaceTempView("events")

result = spark.sql("""
WITH days AS (SELECT DISTINCT event_date AS dt FROM events)
SELECT d.dt,
       COUNT(DISTINCT e.user_id) AS l7_active_users
FROM days d
LEFT JOIN events e ON e.event_date BETWEEN DATE_SUB(d.dt, 6) AND d.dt
GROUP BY d.dt
ORDER BY d.dt
""")
result.show()

SQL = """
WITH days AS (SELECT DISTINCT event_date AS dt FROM events)
SELECT d.dt,
       COUNT(DISTINCT e.user_id) AS l7_active_users
FROM days d
LEFT JOIN events e ON e.event_date BETWEEN DATE_SUB(d.dt, 6) AND d.dt
GROUP BY d.dt
ORDER BY d.dt;
"""


# ──────────────────────────────────────────────────────────────────────────────
# MySQL 8.0+ setup (no window functions, as-of CTE pattern)
# ──────────────────────────────────────────────────────────────────────────────
MYSQL_SETUP = """
CREATE TABLE events (
    user_id    INT NOT NULL,
    event_date DATE NOT NULL,
    event_name VARCHAR(32) NOT NULL,
    KEY idx_events_date (event_date),
    KEY idx_events_user_date (user_id, event_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO events (user_id, event_date, event_name) VALUES
    (1, '2026-01-01', 'open'), (1, '2026-01-02', 'open'), (1, '2026-01-08', 'open'),
    (2, '2026-01-01', 'open'),
    (3, '2026-01-01', 'open'), (3, '2026-01-02', 'open'),
    (4, '2026-01-02', 'open'), (4, '2026-01-03', 'open'), (4, '2026-01-09', 'open'),
    (5, '2026-01-02', 'open'),
    (6, '2026-01-02', 'open'), (6, '2026-01-03', 'open'), (6, '2026-01-30', 'open'),
    (7, '2026-01-08', 'open'),
    (8, '2026-01-08', 'open'), (8, '2026-01-09', 'open');
"""

# Single as-of date. Counts distinct users active in [D-6, D] inclusive.
# No window functions; uses a CROSS JOIN + WHERE to prune the scan via the
# (event_date) index.
MYSQL_L7_SINGLE = """
WITH as_of AS (SELECT '2026-01-08' AS d)
SELECT a.d AS as_of_date,
       COUNT(DISTINCT e.user_id) AS l7_users
FROM as_of a
CROSS JOIN events e
WHERE e.event_date BETWEEN DATE_SUB(a.d, INTERVAL 6 DAY) AND a.d
GROUP BY a.d;
"""

# Multiple as-of dates via UNION ALL of literals — no recursive CTE needed.
# This is the portable MySQL 8.0+ idiom.
MYSQL_L7_L28_MULTI = """
WITH as_of AS (
    SELECT '2026-01-08' AS d UNION ALL SELECT '2026-01-30'
)
SELECT a.d AS as_of_date,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 6
                           THEN e.user_id END) AS l7_users,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 27
                           THEN e.user_id END) AS l28_users
FROM as_of a
CROSS JOIN events e
WHERE e.event_date >= DATE_SUB(a.d, INTERVAL 27 DAY)
GROUP BY a.d
ORDER BY a.d;
"""
