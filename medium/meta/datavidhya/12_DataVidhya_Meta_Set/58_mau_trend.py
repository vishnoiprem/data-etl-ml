"""
Q58: Monthly Active Users (MAU) with Trend   [Medium | Window Functions, Aggregate Functions]
DataVidhya slug: monthly-active-users-mau-trend

Per month: mau (distinct users), prev_mau (the previous month IN THE RESULT),
and growth_rate = (mau - prev_mau) / prev_mau * 100 to 2dp. Earliest month gets
NULL for both.

How to Think:
- Two layers. Aggregate to one row per month FIRST, then LAG over that. Trying
  to LAG over the raw events makes no sense -- there is nothing to lag until the
  months exist.
- LAG returns NULL on the first row, and every downstream expression involving
  it becomes NULL automatically. That is exactly what the spec wants here, so do
  NOT COALESCE it away.
- Grain: one row per calendar month present in the data.

The trap:
- COMPARE THIS TO Q40. Q40 says "the immediately preceding CALENDAR month" and
  therefore needs `add_months(month, -1)`; this question says "the immediately
  preceding month IN THE RESULT" and therefore needs LAG over observed months.
  With a data gap those give different answers, and the correct function is
  whichever the wording names. Two nearly identical questions, opposite
  answers -- asserted on gapped data below.
- growth_rate is a PERCENTAGE (100.00) here, whereas Q40's retention_rate is a
  fraction (0.5). Same family of question, different unit.
- Summing DAU to get MAU double counts. Each user counts once per month no
  matter how many events: user 1 logs in twice in January, and January's mau is
  2, not 3.
- Integer division: `(mau - prev_mau) / prev_mau` with bigint operands truncates
  to 0 in Presto/Hive. Multiply by 100.0.
- The earliest month must APPEAR with NULLs, not be dropped.
- `trunc(date,'MM')` returns DATE; `date_trunc` returns TIMESTAMP.

Spark note:
- The LAG window has no PARTITION BY, so all months land in one partition.
  That is fine -- there are only ever a few hundred months.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("58-mau-trend")
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
# User 1 logs in twice in January -- January's mau is 2, not 3.
spark.sql("""
CREATE OR REPLACE TEMP VIEW events AS
SELECT * FROM VALUES
    (1, DATE'2024-01-05', 'login'),
    (1, DATE'2024-01-15', 'login'),
    (2, DATE'2024-01-08', 'purchase'),
    (1, DATE'2024-02-03', 'login'),
    (2, DATE'2024-02-07', 'purchase'),
    (3, DATE'2024-02-10', 'login'),
    (4, DATE'2024-02-14', 'view'),
    (1, DATE'2024-03-05', 'login'),
    (2, DATE'2024-03-10', 'purchase')
AS t(user_id, event_date, event_type)
""")

from pyspark.sql import functions as F, Window as W

# LAG over OBSERVED months -- the spec says "the previous month in the result".
SQL = """
WITH monthly AS (
    SELECT TRUNC(event_date, 'MM')  AS month,
           COUNT(DISTINCT user_id)  AS mau
    FROM events
    GROUP BY TRUNC(event_date, 'MM')
),
trended AS (
    SELECT month,
           mau,
           LAG(mau) OVER (ORDER BY month) AS prev_mau
    FROM monthly
)
SELECT month,
       mau,
       prev_mau,
       ROUND((mau - prev_mau) * 100.0 / prev_mau, 2) AS growth_rate
FROM trended
ORDER BY month
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt

EXPECTED = [
    (dt.date(2024, 1, 1), 2, None, None),
    (dt.date(2024, 2, 1), 4, 2,  100.00),
    (dt.date(2024, 3, 1), 2, 4,  -50.00),
]
expect("Q58 MAU with month-over-month growth", SQL, EXPECTED)

# DataFrame API equivalent.
monthly = (spark.table("events")
           .groupBy(F.trunc("event_date", "MM").alias("month"))
           .agg(F.countDistinct("user_id").alias("mau")))
df = (monthly.withColumn("prev_mau", F.lag("mau").over(W.orderBy("month")))
      .withColumn("growth_rate",
                  F.round((F.col("mau") - F.col("prev_mau")) * F.lit(100.0)
                          / F.col("prev_mau"), 2))
      .select("month", "mau", "prev_mau", "growth_rate")
      .orderBy("month"))
assert [(r[0], r[1], r[2], None if r[3] is None else float(r[3]))
        for r in df.collect()] == EXPECTED
print("[PASS] Q58 DataFrame API matches SQL")

# ------------------------------------------------ the earliest month keeps its NULLs
first = spark.sql(SQL).collect()[0]
assert first[2] is None and first[3] is None, first
print("[PASS] Q58 earliest month appears with NULL prev_mau and NULL growth_rate")

# ------------------------------------------------ MAU is not the sum of DAU
dau_sum = spark.sql("""
WITH dau AS (
    SELECT event_date, COUNT(DISTINCT user_id) AS d FROM events GROUP BY event_date
)
SELECT SUM(d) FROM dau WHERE event_date < DATE'2024-02-01'
""").collect()[0][0]
jan_mau = [r for r in spark.sql(SQL).collect() if r[0] == dt.date(2024, 1, 1)][0][1]
assert (dau_sum, jan_mau) == (3, 2), (dau_sum, jan_mau)
print("[PASS] Q58 summing January's DAU gives 3; MAU is 2 (user 1 counted once)")

# ------------------------------------------------ LAG vs add_months on a data GAP
# This question wants LAG (previous month IN THE RESULT). Q40 wants the previous
# CALENDAR month. With April missing they disagree.
spark.sql("""
CREATE OR REPLACE TEMP VIEW events AS
SELECT * FROM VALUES
    (1, DATE'2024-01-05', 'login'),
    (2, DATE'2024-01-08', 'login'),
    (1, DATE'2024-02-03', 'login'),
    (2, DATE'2024-02-07', 'login'),
    (3, DATE'2024-02-10', 'login'),
    (4, DATE'2024-02-14', 'login'),
    (1, DATE'2024-05-05', 'login')
AS t(user_id, event_date, event_type)
""")

# LAG: May's predecessor is February (the previous month in the result).
expect("Q58 with a gap, LAG uses the previous month IN THE RESULT", SQL, [
    (dt.date(2024, 1, 1), 2, None, None),
    (dt.date(2024, 2, 1), 4, 2,  100.00),
    (dt.date(2024, 5, 1), 1, 4,  -75.00),
])

calendar = spark.sql("""
WITH monthly AS (
    SELECT TRUNC(event_date,'MM') AS month, COUNT(DISTINCT user_id) AS mau
    FROM events GROUP BY TRUNC(event_date,'MM')
)
SELECT c.month, c.mau, p.mau AS prev_mau
FROM monthly c LEFT JOIN monthly p ON p.month = ADD_MONTHS(c.month, -1)
ORDER BY c.month
""").collect()
may = [r for r in calendar if r[0] == dt.date(2024, 5, 1)][0]
assert may[2] is None, may
print("[PASS] Q58 add_months (Q40's rule) gives May a NULL predecessor; LAG gives 4 -- "
      "the wording decides")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 has LAG() and the same first-then-LAG over observed months
# pattern. The TRUNC-to-month is `DATE_FORMAT(event_date, '%Y-%m-01')` in
# MySQL -- that is the equivalent of Spark's TRUNC(d, 'MM'). DO NOT use
# DATE_FORMAT with the Java-style 'yyyy-MM' here, because the result would
# be a STRING, not a DATE -- sorting still works, but date arithmetic on
# it does not.
#
# CREATE TABLE events (
#     user_id    INT          NOT NULL,
#     event_date DATE         NOT NULL,
#     event_type VARCHAR(16)  NOT NULL,
#     KEY ix_events_user_date (user_id, event_date),
#     KEY ix_events_date      (event_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO events (user_id, event_date, event_type) VALUES
#     (1, '2024-01-05', 'login'),    (1, '2024-01-15', 'login'),
#     (2, '2024-01-08', 'purchase'), (1, '2024-02-03', 'login'),
#     (2, '2024-02-07', 'purchase'), (3, '2024-02-10', 'login'),
#     (4, '2024-02-14', 'view'),     (1, '2024-03-05', 'login'),
#     (2, '2024-03-10', 'purchase');
#
# WITH monthly AS (
#     SELECT DATE_FORMAT(event_date, '%Y-%m-01') AS month,
#            COUNT(DISTINCT user_id) AS mau
#     FROM events
#     GROUP BY DATE_FORMAT(event_date, '%Y-%m-01')
# ),
# trended AS (
#     SELECT month, mau,
#            LAG(mau) OVER (ORDER BY month) AS prev_mau
#     FROM monthly
# )
# SELECT month, mau, prev_mau,
#        ROUND((mau - prev_mau) * 100.0 / prev_mau, 2) AS growth_rate
# FROM trended
# ORDER BY month;
#
# -- Expected:
# -- 2024-01-01 2 NULL  NULL
# -- 2024-02-01 4 2      100.00
# -- 2024-03-01 2 4      -50.00
