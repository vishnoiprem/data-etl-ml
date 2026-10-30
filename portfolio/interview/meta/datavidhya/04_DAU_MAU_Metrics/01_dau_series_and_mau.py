"""
Problem 01: DAU series, MAU, and stickiness.

Meta flavor: "What is DAU/MAU for this surface, and is it improving?"

How to Think:
- DAU = COUNT(DISTINCT user_id) per day. MAU = COUNT(DISTINCT user_id) per
  month. MAU is NOT the sum of DAUs — that double counts returning users, and
  it is the single most common error on this question.
- Stickiness = avg(DAU) / MAU. Say which denominator you use for avg(DAU):
  days WITH activity, or all calendar days in the month? They differ whenever
  the product has dead days. This file uses days-with-activity and says so.
- Vocabulary matters at Meta: "stickiness" means DAU/MAU. Do not call it
  "sticky ratio" or improvise a definition.

How to Remember:
- "DAU/MAU, capped at 1. Sum of DAUs is not MAU."

Spark note:
- Two distinct-count aggregations, two shuffles. On a partitioned events table
  both prune to the month.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("01-dau-series-and-mau")
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

from pyspark.sql import functions as F

DAU = """
SELECT event_date, COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY event_date
ORDER BY event_date
"""
expect("DAU series", DAU, [
    ("2026-01-01", 3), ("2026-01-02", 5), ("2026-01-03", 2),
    ("2026-01-08", 3), ("2026-01-09", 2), ("2026-01-30", 1),
])

STICKY = """
WITH dau AS (
    SELECT event_date, COUNT(DISTINCT user_id) AS dau
    FROM events GROUP BY event_date
),
mau AS (
    SELECT DATE_FORMAT(event_date, 'yyyy-MM') AS ym,
           COUNT(DISTINCT user_id) AS mau
    FROM events GROUP BY DATE_FORMAT(event_date, 'yyyy-MM')
)
SELECT m.ym, m.mau,
       ROUND(AVG(d.dau), 2) AS avg_dau,
       ROUND(100.0 * AVG(d.dau) / m.mau, 2) AS stickiness_pct
FROM mau m
JOIN dau d ON DATE_FORMAT(d.event_date, 'yyyy-MM') = m.ym
GROUP BY m.ym, m.mau
ORDER BY m.ym
"""
expect("MAU + stickiness (avg over active days)", STICKY, [("2026-01", 8, 2.67, 33.33)])

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
# DAU series (MySQL 8.0+):
#   SELECT event_date, COUNT(DISTINCT user_id) AS dau
#   FROM events
#   GROUP BY event_date
#   ORDER BY event_date;
#
# MAU + stickiness (avg over active days; DATE_FORMAT bucket = '%Y-%m'):
#   WITH dau AS (
#       SELECT event_date, COUNT(DISTINCT user_id) AS dau
#       FROM events GROUP BY event_date
#   ),
#   mau AS (
#       SELECT DATE_FORMAT(event_date, '%Y-%m') AS ym,
#              COUNT(DISTINCT user_id) AS mau
#       FROM events GROUP BY DATE_FORMAT(event_date, '%Y-%m')
#   )
#   SELECT m.ym, m.mau,
#          ROUND(AVG(d.dau), 2)               AS avg_dau,
#          ROUND(100.0 * AVG(d.dau) / m.mau, 2) AS stickiness_pct
#   FROM mau m
#   JOIN dau d ON DATE_FORMAT(d.event_date, '%Y-%m') = m.ym
#   GROUP BY m.ym, m.mau
#   ORDER BY m.ym;
# Note: stickiness definition is unchanged — DAU/MAU, capped at 1. Stickiness
# uses days-with-activity in the numerator (NOT all calendar days of the month);
# this differs whenever the product has dead days.

# ---- PySpark DataFrame API ------------------------------------------------
dau_df = (spark.table("events").groupBy("event_date")
          .agg(F.countDistinct("user_id").alias("dau")).orderBy("event_date"))
assert [tuple(r) for r in dau_df.collect()] == [
    ("2026-01-01", 3), ("2026-01-02", 5), ("2026-01-03", 2),
    ("2026-01-08", 3), ("2026-01-09", 2), ("2026-01-30", 1)]
print("[PASS] DAU — DataFrame API matches SQL")
