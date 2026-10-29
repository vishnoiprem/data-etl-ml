"""
Q41: App Click-Through Rate (CTR)   [Medium | CASE WHEN, Aggregate Functions]
DataVidhya slug: aggregation-app-click-through-rate

Over 2022 events only, per app: ctr = 100 * clicks / impressions. Exclude apps
with no 2022 impressions.

How to Think:
- Both numerator and denominator come from the SAME rows, distinguished only by
  event_type. That is a conditional aggregate, not a self-join and not two
  subqueries: SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END).
- The exclusion rule is a condition on an AGGREGATE (impressions = 0), so it
  belongs in HAVING. Putting it in WHERE is impossible -- the count does not
  exist yet at WHERE time.
- Narrate the metric choice: CTR's denominator is impressions, so an app that
  was never shown has an undefined CTR. Excluding it is correct, not a
  convenience.

The trap:
- App 105 has a click and ZERO impressions. Without the HAVING it becomes a
  divide-by-zero: Spark returns NULL (so the app appears with a NULL ctr),
  Postgres raises. Either way the row must not be there at all.
- The 2021-12-31 impression for app 101 is OUTSIDE the window. Forget the year
  filter and 101 has 3 impressions -> 33.33 instead of 50.00. Note the filter
  applies to the numerator too, not just the denominator.
- Integer division: use 100.0.
- Do not use COUNT(event_type = 'click'); COUNT counts non-NULLs, and `false`
  is not NULL, so it counts everything. Use SUM(CASE...) or
  COUNT(CASE WHEN ... THEN 1 END).

Spark note:
- `WHERE YEAR(event_date) = 2022` blocks partition pruning on a date-partitioned
  table because the predicate wraps the column in a function. Write
  `event_date >= DATE'2022-01-01' AND event_date < DATE'2023-01-01'` in
  production -- sargable, and prunes.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("41-app-ctr")
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
# Event 4 is a 2021 impression (out of window); app 105 has a click but no
# impressions at all.
spark.sql("""
CREATE OR REPLACE TEMP VIEW events AS
SELECT * FROM VALUES
    (1, 101, 'impression', DATE'2022-01-05'),
    (2, 101, 'impression', DATE'2022-01-06'),
    (3, 101, 'click',      DATE'2022-01-07'),
    (4, 101, 'impression', DATE'2021-12-31'),
    (5, 102, 'impression', DATE'2022-01-10'),
    (6, 102, 'impression', DATE'2022-01-11'),
    (7, 102, 'impression', DATE'2022-01-12'),
    (8, 102, 'click',      DATE'2022-01-13'),
    (9, 105, 'click',      DATE'2022-03-10')
AS t(event_id, app_id, event_type, event_date)
""")

from pyspark.sql import functions as F

# Sargable date range rather than YEAR(event_date) -- prunes partitions.
SQL = """
SELECT app_id,
       ROUND(100.0 * SUM(CASE WHEN event_type = 'click'      THEN 1 ELSE 0 END)
                   / SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END), 2) AS ctr
FROM events
WHERE event_date >= DATE'2022-01-01'
  AND event_date <  DATE'2023-01-01'
GROUP BY app_id
HAVING SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END) > 0
ORDER BY app_id
"""

spark.sql(SQL).show(truncate=False)

expect("Q41 CTR per app", SQL, [(101, 50.00), (102, 33.33)])

# DataFrame API equivalent.
clicks = F.sum(F.when(F.col("event_type") == "click", 1).otherwise(0))
impressions = F.sum(F.when(F.col("event_type") == "impression", 1).otherwise(0))
df = (spark.table("events")
      .filter((F.col("event_date") >= F.lit("2022-01-01").cast("date")) &
              (F.col("event_date") < F.lit("2023-01-01").cast("date")))
      .groupBy("app_id")
      .agg(clicks.alias("clicks"), impressions.alias("impressions"))
      .filter(F.col("impressions") > 0)
      .select("app_id",
              F.round(F.lit(100.0) * F.col("clicks") / F.col("impressions"), 2).alias("ctr"))
      .orderBy("app_id"))
assert [(r[0], float(r[1])) for r in df.collect()] == [(101, 50.0), (102, 33.33)]
print("[PASS] Q41 DataFrame API matches SQL")

# ------------------------------------------------ the zero-impressions trap
# Without HAVING, app 105 divides by zero -- Spark yields NULL, not an error.
no_having = spark.sql("""
SELECT app_id,
       ROUND(100.0 * SUM(CASE WHEN event_type = 'click'      THEN 1 ELSE 0 END)
                   / SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END), 2) AS ctr
FROM events
WHERE event_date >= DATE'2022-01-01' AND event_date < DATE'2023-01-01'
GROUP BY app_id ORDER BY app_id
""").collect()
assert [(r[0], None if r[1] is None else float(r[1])) for r in no_having] == [
    (101, 50.0), (102, 33.33), (105, None),
], no_having
print("[PASS] Q41 without HAVING, app 105 appears with a NULL ctr (silent divide-by-zero)")

# ------------------------------------------------ the year-filter trap
unfiltered = spark.sql("""
SELECT ROUND(100.0 * SUM(CASE WHEN event_type = 'click'      THEN 1 ELSE 0 END)
                   / SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END), 2) AS ctr
FROM events WHERE app_id = 101
""").collect()[0][0]
assert float(unfiltered) == 33.33, unfiltered
print("[PASS] Q41 keeping the 2021 impression gives app 101 a CTR of 33.33, not 50.00")

# ------------------------------------------------ COUNT(condition) counts everything
bad_count, good_count = spark.sql("""
SELECT COUNT(event_type = 'click')          AS bad,
       COUNT(CASE WHEN event_type = 'click' THEN 1 END) AS good
FROM events WHERE app_id = 101
""").collect()[0]
assert (bad_count, good_count) == (4, 1), (bad_count, good_count)
print("[PASS] Q41 COUNT(cond) returns 4 (false is not NULL); COUNT(CASE...) returns 1")

# ---- MySQL way ----------------------------------------------------------
# MySQL 8.0 supports the same SUM(CASE WHEN ... THEN 1 ELSE 0 END) pattern
# in the WHERE/GROUP BY/HAVING flow. The HAVING impressions > 0 filter is
# what keeps app 105 out of the result; without it, MySQL returns NULL
# silently.
#
# CREATE TABLE events (
#     event_id   INT         NOT NULL,
#     app_id     INT         NOT NULL,
#     event_type VARCHAR(16) NOT NULL,
#     event_date DATE        NOT NULL,
#     PRIMARY KEY (event_id),
#     KEY ix_events_app_date (app_id, event_date)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO events (event_id, app_id, event_type, event_date) VALUES
#     (1, 101, 'impression', '2022-01-05'),
#     (2, 101, 'impression', '2022-01-06'),
#     (3, 101, 'click',      '2022-01-07'),
#     (4, 101, 'impression', '2021-12-31'),
#     (5, 102, 'impression', '2022-01-10'),
#     (6, 102, 'impression', '2022-01-11'),
#     (7, 102, 'impression', '2022-01-12'),
#     (8, 102, 'click',      '2022-01-13'),
#     (9, 105, 'click',      '2022-03-10');
#
# SELECT app_id,
#        ROUND(100.0 * SUM(CASE WHEN event_type = 'click'      THEN 1 ELSE 0 END)
#                    / SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END), 2) AS ctr
# FROM events
# WHERE event_date >= '2022-01-01'
#   AND event_date <  '2023-01-01'
# GROUP BY app_id
# HAVING SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END) > 0
# ORDER BY app_id;
#
# -- Expected: (101, 50.00), (102, 33.33).
