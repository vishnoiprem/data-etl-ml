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
# MySQL 8.0 supports CTEs and the same VALUES-derived anchor table. One pass,
# two conditional DISTINCT counts — push DATEDIFF lower bound into a WHERE
# filter (or partition pruning on a real table) so you only scan 28 days.
#
#   WITH as_of AS (
#       SELECT * FROM (VALUES ROW('2026-01-08'), ROW('2026-01-30')) AS t(d)
#   )
#   SELECT a.d AS as_of_date,
#          COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 6
#                              THEN e.user_id END) AS l7_users,
#          COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 27
#                              THEN e.user_id END) AS l28_users
#   FROM as_of a
#   CROSS JOIN events e
#   GROUP BY a.d
#   ORDER BY a.d;
#
# Notes:
# - DATEDIFF(a, b) returns a - b in days in MySQL, matching Spark's usage here.
# - To restrict the scan, add WHERE e.event_date >= a.d - INTERVAL 27 DAY
#   (planner-aware: anchor the lower bound from the smallest as_of date).
# - If running on MySQL 5.7 or MariaDB without VALUES-as-table, use a UNION ALL
#   of SELECT ... constants instead.
