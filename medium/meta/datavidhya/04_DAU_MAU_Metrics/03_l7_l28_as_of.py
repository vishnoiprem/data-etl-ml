"""
Problem 03: L7 and L28 active users as of a given date.

Meta flavor: "How many L7 and L28 users did Reels have on Jan 30?"

How to Think:
- Meta vocabulary, and getting it wrong marks you as an outsider:
    L7  = distinct users active at least once in the TRAILING 7 days
    L28 = distinct users active at least once in the trailing 28 days
  Note "L7" is NOT "active on 7 of the last 7 days" in the usual DE reading —
  but different teams do use the stricter sense, so CONFIRM the definition
  before writing. The confirmation itself is the signal.
- Trailing window is inclusive of the as-of date: [D-6, D] for L7.
- Compute both in one pass with conditional distinct counts rather than two
  separate scans.

Spark note:
- One scan of events, two conditional COUNT DISTINCTs. On a real table push the
  D-27 lower bound into the partition filter so you read 28 days, not all time.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("03-l7-l28-as-of")
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
    (1, "2026-01-01", "open"),  (1, "2026-01-02", "open"),  (1, "2026-01-08", "open"),
    (2, "2026-01-01", "open"),
    (3, "2026-01-01", "open"),  (3, "2026-01-02", "open"),
    (4, "2026-01-02", "open"),  (4, "2026-01-03", "open"),  (4, "2026-01-09", "open"),
    (5, "2026-01-02", "open"),
    (6, "2026-01-02", "open"),  (6, "2026-01-03", "open"),  (6, "2026-01-30", "open"),
    (7, "2026-01-08", "open"),
    (8, "2026-01-08", "open"),  (8, "2026-01-09", "open"),
],
    ["user_id", "event_date", "event_name"]
).createOrReplaceTempView("events")


SQL = """
WITH as_of AS (SELECT * FROM VALUES ('2026-01-08'), ('2026-01-30') AS t(d))
SELECT a.d AS as_of_date,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 6
                           THEN e.user_id END) AS l7_users,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 27
                           THEN e.user_id END) AS l28_users
FROM as_of a
CROSS JOIN events e
GROUP BY a.d
ORDER BY a.d
"""
expect("L7 / L28 as of date", SQL, [
    ("2026-01-08", 7, 8),
    ("2026-01-30", 1, 5),
])

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE events (
#       user_id    INT NOT NULL,
#       event_date DATE NOT NULL,
#       event_name VARCHAR(32) NOT NULL,
#       KEY idx_events_date (event_date),
#       KEY idx_events_user_date (user_id, event_date)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO events (user_id, event_date, event_name) VALUES
#       (1, '2026-01-01', 'open'), (1, '2026-01-02', 'open'), (1, '2026-01-08', 'open'),
#       (2, '2026-01-01', 'open'),
#       (3, '2026-01-01', 'open'), (3, '2026-01-02', 'open'),
#       (4, '2026-01-02', 'open'), (4, '2026-01-03', 'open'), (4, '2026-01-09', 'open'),
#       (5, '2026-01-02', 'open'),
#       (6, '2026-01-02', 'open'), (6, '2026-01-03', 'open'), (6, '2026-01-30', 'open'),
#       (7, '2026-01-08', 'open'),
#       (8, '2026-01-08', 'open'), (8, '2026-01-09', 'open');
#
# L7 / L28 conditional distinct counts in one pass. MySQL 8.0 has no VALUES
# clause, so use UNION ALL of constants (works on 5.7 / MariaDB too):
#   WITH RECURSIVE as_of(d) AS (
#       SELECT '2026-01-08' UNION ALL SELECT '2026-01-30'
#   )
#   -- simpler and portable form:
#   WITH as_of AS (
#       SELECT '2026-01-08' AS d UNION ALL SELECT '2026-01-30'
#   )
#   SELECT a.d AS as_of_date,
#          COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 6
#                              THEN e.user_id END) AS l7_users,
#          COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 27
#                              THEN e.user_id END) AS l28_users
#   FROM as_of a
#   CROSS JOIN events e
#   WHERE e.event_date >= DATE_SUB(a.d, INTERVAL 27 DAY)   -- prune scan
#   GROUP BY a.d
#   ORDER BY a.d;
#
# Notes:
# - DATEDIFF(a, b) returns a - b in days in MySQL, matching Spark usage.
# - Trailing window is [D-6, D] for L7, inclusive of the as-of date. Confirm
#   "L7" means "active at least once in the trailing 7 days" — some teams use
#   the stricter "active on 7 of the last 7" sense. The confirmation is the
#   signal at Meta.
# - Push DATE_SUB(a.d, INTERVAL 27 DAY) into a WHERE so you scan 28 days, not
#   the whole history.
