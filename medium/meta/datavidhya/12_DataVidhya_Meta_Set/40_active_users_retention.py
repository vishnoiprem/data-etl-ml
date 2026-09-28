"""
Q40: Active Users Retention   [Medium | Date/Time Functions, Aggregate Functions]
DataVidhya slug: active-users-retention

Month by month: active_users, retained_users (also active in the IMMEDIATELY
PRECEDING calendar month), and retention_rate as a FRACTION (not a percentage).

How to Think:
- Collapse to the user-month grain FIRST: `SELECT DISTINCT user_id,
  trunc(event_date,'MM')`. Every later count is then a plain count, and the
  "each user counts at most once per month" rule is satisfied structurally
  rather than by remembering to write DISTINCT three times.
- Retention is a SELF-JOIN of that grain against itself shifted one month:
  `p.month = add_months(c.month, -1)`. Say it out loud as "this month's users
  who also appear in last month's set."
- Then LEFT JOIN the retained counts back onto the month list, so the earliest
  month survives with 0.

The trap:
- retention_rate is a FRACTION (0.5), not a percentage (50.0). Multiplying by
  100 is the most common miss here, and 0.5 vs 50.0 both "look right".
- The earliest month must APPEAR with retained_users = 0 and rate 0.0, not be
  omitted and not be NULL. That is what the LEFT JOIN + COALESCE is for.
- "Immediately preceding CALENDAR month" -- use add_months(month, -1), not
  `month - 30 days` and not LAG over the observed months. LAG on a table with a
  GAP silently compares against the last month that HAS data: if March is
  missing, LAG makes April's predecessor February and inflates retention. That
  case is asserted below because the shipped data has no gap.
- Do not sum monthly actives to get a total; returning users would double count.

Spark note:
- `trunc(date,'MM')` returns a DATE (first of month), which is what the spec
  wants. `date_trunc('MONTH', ...)` returns a TIMESTAMP and will not match the
  expected DATE output.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("40-active-users-retention")
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
# Exactly the rows DataVidhya ships with the question.
# Jan: users 1,2. Feb: users 1,4. Only user 1 spans both.
spark.sql("""
CREATE OR REPLACE TEMP VIEW events AS
SELECT * FROM VALUES
    (1, DATE'2024-01-01', 'login'),
    (1, DATE'2024-02-01', 'login'),
    (2, DATE'2024-01-02', 'login'),
    (4, DATE'2024-02-01', 'login')
AS t(user_id, event_date, event_type)
""")

from pyspark.sql import functions as F

SQL = """
WITH user_months AS (
    -- collapse to the user-month grain up front
    SELECT DISTINCT user_id, TRUNC(event_date, 'MM') AS month
    FROM events
),
monthly AS (
    SELECT month, COUNT(*) AS active_users
    FROM user_months
    GROUP BY month
),
retained AS (
    SELECT c.month, COUNT(*) AS retained_users
    FROM user_months c
    JOIN user_months p
      ON p.user_id = c.user_id
     AND p.month   = ADD_MONTHS(c.month, -1)   -- calendar month, not 30 days
    GROUP BY c.month
)
SELECT m.month,
       m.active_users,
       COALESCE(r.retained_users, 0) AS retained_users,
       ROUND(COALESCE(r.retained_users, 0) / m.active_users, 2) AS retention_rate
FROM monthly m
LEFT JOIN retained r ON r.month = m.month
ORDER BY m.month
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt

expect("Q40 monthly retention", SQL, [
    (dt.date(2024, 1, 1), 2, 0, 0.0),
    (dt.date(2024, 2, 1), 2, 1, 0.5),
])

# DataFrame API equivalent.
user_months = (spark.table("events")
               .select("user_id", F.trunc("event_date", "MM").alias("month"))
               .distinct())
monthly = user_months.groupBy("month").agg(F.count(F.lit(1)).alias("active_users"))
cur, prv = user_months.alias("c"), user_months.alias("p")
retained = (cur.join(prv,
                     (F.col("p.user_id") == F.col("c.user_id")) &
                     (F.col("p.month") == F.add_months(F.col("c.month"), -1)))
            .groupBy(F.col("c.month").alias("month"))
            .agg(F.count(F.lit(1)).alias("retained_users")))
df = (monthly.join(retained, "month", "left")
      .withColumn("retained_users", F.coalesce("retained_users", F.lit(0)))
      .withColumn("retention_rate",
                  F.round(F.col("retained_users") / F.col("active_users"), 2))
      .select("month", "active_users", "retained_users", "retention_rate")
      .orderBy("month"))
assert [tuple(r) for r in df.collect()] == [
    (dt.date(2024, 1, 1), 2, 0, 0.0),
    (dt.date(2024, 2, 1), 2, 1, 0.5),
]
print("[PASS] Q40 DataFrame API matches SQL")

# ------------------------------------------------ fraction, not percentage
rate = spark.sql(SQL).collect()[1][3]
assert float(rate) == 0.5, rate
print("[PASS] Q40 retention_rate is 0.5 (a fraction), not 50.0")

# ------------------------------------------------ the month-gap trap
# March has no activity. add_months gives April retained = 0 (correct);
# LAG over observed months makes February April's predecessor and reports 1.
spark.sql("""
CREATE OR REPLACE TEMP VIEW events AS
SELECT * FROM VALUES
    (1, DATE'2024-01-01', 'login'),
    (1, DATE'2024-02-01', 'login'),
    (2, DATE'2024-01-02', 'login'),
    (4, DATE'2024-02-01', 'login'),
    (1, DATE'2024-04-05', 'login')
AS t(user_id, event_date, event_type)
""")

expect("Q40 month gap: April has no immediate predecessor", SQL, [
    (dt.date(2024, 1, 1), 2, 0, 0.0),
    (dt.date(2024, 2, 1), 2, 1, 0.5),
    (dt.date(2024, 4, 1), 1, 0, 0.0),
])

lag_based = spark.sql("""
WITH user_months AS (SELECT DISTINCT user_id, TRUNC(event_date,'MM') AS month FROM events),
shifted AS (
    SELECT user_id, month,
           LAG(month) OVER (PARTITION BY user_id ORDER BY month) AS prev_observed
    FROM user_months
)
SELECT month, COUNT(*) AS retained_users
FROM shifted WHERE prev_observed IS NOT NULL
GROUP BY month ORDER BY month
""").collect()
assert [(r[0], r[1]) for r in lag_based] == [
    (dt.date(2024, 2, 1), 1), (dt.date(2024, 4, 1), 1),
], lag_based
print("[PASS] Q40 LAG over observed months wrongly retains April across the March gap")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 has window functions but lacks ADD_MONTHS. The portable
# substitute is DATE_SUB(c.month, INTERVAL 1 MONTH) for "preceding calendar
# month". The same self-join on user_id + shifted month gives the retained
# set. TRUNC(date, 'MM') in Spark is DATE_FORMAT(event_date, '%Y-%m-01') in
# MySQL -- both return the first day of the month as a DATE.
#
# CREATE TABLE events (
#     user_id    INT         NOT NULL,
#     event_date DATE        NOT NULL,
#     event_type VARCHAR(16) NOT NULL,
#     KEY ix_events_user_date (user_id, event_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO events (user_id, event_date, event_type) VALUES
#     (1, '2024-01-01', 'login'),
#     (1, '2024-02-01', 'login'),
#     (2, '2024-01-02', 'login'),
#     (4, '2024-02-01', 'login');
#
# WITH user_months AS (
#     SELECT DISTINCT user_id,
#            DATE_FORMAT(event_date, '%Y-%m-01') AS month
#     FROM events
# ),
# monthly AS (
#     SELECT month, COUNT(*) AS active_users
#     FROM user_months GROUP BY month
# ),
# retained AS (
#     SELECT c.month, COUNT(*) AS retained_users
#     FROM user_months c
#     JOIN user_months p
#       ON p.user_id = c.user_id
#      AND p.month   = DATE_SUB(c.month, INTERVAL 1 MONTH)
#     GROUP BY c.month
# )
# SELECT m.month,
#        m.active_users,
#        COALESCE(r.retained_users, 0) AS retained_users,
#        ROUND(COALESCE(r.retained_users, 0) / m.active_users, 2) AS retention_rate
# FROM monthly m
# LEFT JOIN retained r ON r.month = m.month
# ORDER BY m.month;
#
# -- Expected:
# -- 2024-01-01 2 0 0.00
# -- 2024-02-01 2 1 0.50
