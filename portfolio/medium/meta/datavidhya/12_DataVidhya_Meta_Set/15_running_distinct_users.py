"""
Q15: Running Distinct Count of Users   [Hard | CTEs]

Cumulative count of DISTINCT users over time.

How to Think:
- COUNT(DISTINCT ...) is NOT allowed as a window function. This is the entire
  point of the question, and the reason it is tagged Hard.
- The fix is a reframe, not a workaround: a user contributes to the running
  distinct count exactly once, on the date they FIRST appear. So:
      1. reduce to each user's first-seen date
      2. count first-appearances per date
      3. take a plain cumulative SUM over that
  This is O(one pass) instead of the O(n^2) self-join the tag hints at.
- Keep every date in the output, including dates that add no new users, which
  is why the date spine is LEFT JOINed to the new-user counts.

The trap:
- 2026-01-03 has activity (user 1 returning) but adds NO new distinct user, so
  the running count must stay at 3, not increase. A self-join over "all rows
  up to today" gets this right too, but the first-seen version makes it obvious.

Spark note:
- The self-join version explodes: every date joins to all prior rows. On real
  volumes it OOMs. The first-seen reduction keeps the shuffle tiny.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("15-running-distinct-users")
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
    (1, "2026-01-01"), (2, "2026-01-01"),
    (2, "2026-01-02"), (3, "2026-01-02"),
    (1, "2026-01-03"),
],
    ["user_id", "activity_date"]
).createOrReplaceTempView("daily_users")


SQL = """
WITH first_seen AS (
    SELECT user_id, MIN(activity_date) AS first_date
    FROM daily_users
    GROUP BY user_id
),
new_per_day AS (
    SELECT first_date AS activity_date, COUNT(*) AS new_users
    FROM first_seen
    GROUP BY first_date
),
all_days AS (SELECT DISTINCT activity_date FROM daily_users)
SELECT d.activity_date,
       COALESCE(n.new_users, 0) AS new_users,
       SUM(COALESCE(n.new_users, 0)) OVER (ORDER BY d.activity_date
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_distinct_users
FROM all_days d
LEFT JOIN new_per_day n ON n.activity_date = d.activity_date
ORDER BY d.activity_date
"""

# activity_date is a STRING column here, so no implicit date cast occurs.
expect("Q15 running distinct users", SQL, [
    ("2026-01-01", 2, 2),
    ("2026-01-02", 1, 3),
    ("2026-01-03", 0, 3),
])

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports CTEs and windowed SUM with ROWS BETWEEN UNBOUNDED
# PRECEDING AND CURRENT ROW. The trick of the question is that COUNT(DISTINCT)
# is NOT a valid window aggregate in any major engine -- not MySQL, not Spark,
# not Postgres. The first-seen reduction is the correct reframe: count
# first-appearances per date, then take a plain cumulative SUM. ROWS (not
# RANGE) is the explicit frame so duplicate dates do not collapse.
#
# CREATE TABLE daily_users (
#     user_id        INT  NOT NULL,
#     activity_date  DATE NOT NULL,
#     KEY ix_du_user_date (user_id, activity_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO daily_users (user_id, activity_date) VALUES
#     (1, '2026-01-01'), (2, '2026-01-01'),
#     (2, '2026-01-02'), (3, '2026-01-02'),
#     (1, '2026-01-03');
#
# WITH first_seen AS (
#     SELECT user_id, MIN(activity_date) AS first_date
#     FROM daily_users
#     GROUP BY user_id
# ),
# new_per_day AS (
#     SELECT first_date AS activity_date, COUNT(*) AS new_users
#     FROM first_seen
#     GROUP BY first_date
# ),
# all_days AS (SELECT DISTINCT activity_date FROM daily_users)
# SELECT d.activity_date,
#        COALESCE(n.new_users, 0) AS new_users,
#        SUM(COALESCE(n.new_users, 0)) OVER (ORDER BY d.activity_date
#            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_distinct_users
# FROM all_days d
# LEFT JOIN new_per_day n ON n.activity_date = d.activity_date
# ORDER BY d.activity_date;
#
# -- Expected:
# -- 2026-01-01  2  2
# -- 2026-01-02  1  3
# -- 2026-01-03  0  3
