"""
Q33: Rolling 7-Day Active User Count   [Hard | Date/Time Functions, Analytics]
DataVidhya slug: rolling-7day-active-users

For each date present in user_actions, count the DISTINCT users active in the
inclusive window [date - 6 days, date]. Order by action_date.

How to Think:
- The instinct is `COUNT(DISTINCT user_id) OVER (... ROWS BETWEEN 6 PRECEDING
  AND CURRENT ROW)`. That is not legal SQL -- DISTINCT is not allowed inside a
  window function in Spark, Presto, or Postgres. Recognising this in the first
  30 seconds is what the question is testing.
- So the shape is a RANGE SELF-JOIN, not a window:
    dates  -> the distinct anchor dates you must report on
    du     -> distinct (date, user) pairs
    join   -> du.action_date BETWEEN anchor - 6 AND anchor, then COUNT DISTINCT
- Dedupe to (date, user) BEFORE the join. It shrinks the join and makes the
  intent legible; COUNT(DISTINCT) would fix the arithmetic either way.

The trap:
- ROWS vs days. `ROWS BETWEEN 6 PRECEDING` counts six PRECEDING ROWS, not six
  days. Here one row happens to be one day so it coincidentally matches -- which
  is exactly why the shipped data does not catch the bug. With two actions on
  one day, a ROWS frame silently shortens the window. Use a date range.
- "Each date PRESENT in user_actions" -- report only observed dates. Do not
  generate a dense calendar with sequence()/explode(); a gap in the data must
  stay a gap in the output.
- The window is INCLUSIVE at both ends, so it spans 7 days: date-6 .. date.
  `date - 7` gives an 8-day window and is the most common off-by-one here.
- Rolling distinct is NOT summable. You cannot add daily counts and you cannot
  derive it from yesterday's answer; each window must be recounted.

Spark note:
- The join is a range predicate, so Spark cannot hash-join it and falls back to
  a broadcast nested loop. Fine at this scale. On a real events table, compute
  first_action_date per user and count users whose activity intersects each
  window, or keep a rolling HyperLogLog sketch per day and merge 7 sketches --
  approx_count_distinct is mergeable, exact COUNT(DISTINCT) is not.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("33-rolling-7day-active-users")
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
# Exactly the rows DataVidhya ships with the question: one new user per day.
spark.sql("""
CREATE OR REPLACE TEMP VIEW user_actions AS
SELECT * FROM VALUES
    (1, 1, DATE'2024-01-01', 'click'),
    (2, 2, DATE'2024-01-02', 'view'),
    (3, 3, DATE'2024-01-03', 'like'),
    (4, 4, DATE'2024-01-04', 'share'),
    (5, 5, DATE'2024-01-05', 'click'),
    (6, 6, DATE'2024-01-06', 'view'),
    (7, 7, DATE'2024-01-07', 'like'),
    (8, 8, DATE'2024-01-08', 'share')
AS t(action_id, user_id, action_date, action_type)
""")

from pyspark.sql import functions as F

SQL = """
WITH anchors AS (
    SELECT DISTINCT action_date FROM user_actions
),
user_days AS (
    SELECT DISTINCT action_date, user_id FROM user_actions
)
SELECT a.action_date,
       COUNT(DISTINCT ud.user_id) AS rolling_7day_active_users
FROM anchors a
JOIN user_days ud
  ON ud.action_date BETWEEN DATE_SUB(a.action_date, 6) AND a.action_date
GROUP BY a.action_date
ORDER BY a.action_date
"""

spark.sql(SQL).show(truncate=False)

import datetime as dt


def d(day):
    return dt.date(2024, 1, day)


expect("Q33 rolling 7-day active users", SQL, [
    (d(1), 1), (d(2), 2), (d(3), 3), (d(4), 4),
    (d(5), 5), (d(6), 6), (d(7), 7), (d(8), 7),
])

# DataFrame API equivalent -- same range self-join.
ua = spark.table("user_actions")
anchors = ua.select("action_date").distinct().alias("a")
user_days = ua.select("action_date", "user_id").distinct().alias("ud")
df = (anchors.join(
        user_days,
        (F.col("ud.action_date") >= F.date_sub(F.col("a.action_date"), 6)) &
        (F.col("ud.action_date") <= F.col("a.action_date")))
      .groupBy(F.col("a.action_date").alias("action_date"))
      .agg(F.countDistinct("ud.user_id").alias("rolling_7day_active_users"))
      .orderBy("action_date"))
assert [tuple(r) for r in df.collect()] == [
    (d(1), 1), (d(2), 2), (d(3), 3), (d(4), 4),
    (d(5), 5), (d(6), 6), (d(7), 7), (d(8), 7),
]
print("[PASS] Q33 DataFrame API matches SQL")

# ------------------------------------------------ DISTINCT-in-a-window is illegal
try:
    spark.sql("""
    SELECT action_date,
           COUNT(DISTINCT user_id) OVER (
               ORDER BY action_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
           ) AS rolling
    FROM user_actions
    """).collect()
    raise AssertionError("expected DISTINCT inside a window function to be rejected")
except Exception as e:
    assert "AssertionError" not in type(e).__name__, e
    print("[PASS] Q33 COUNT(DISTINCT ...) OVER (...) is rejected -- range self-join required")

# ------------------------------------------------ the ROWS-vs-DAYS trap
# Two actions land on 2024-01-08, so a 7-PRECEDING-ROWS frame covers fewer than
# 7 days. The date-range answer is unaffected.
spark.sql("""
CREATE OR REPLACE TEMP VIEW user_actions AS
SELECT * FROM VALUES
    (1, 1, DATE'2024-01-01', 'click'),
    (2, 2, DATE'2024-01-02', 'view'),
    (3, 3, DATE'2024-01-03', 'like'),
    (4, 4, DATE'2024-01-04', 'share'),
    (5, 5, DATE'2024-01-05', 'click'),
    (6, 6, DATE'2024-01-06', 'view'),
    (7, 7, DATE'2024-01-07', 'like'),
    (8, 8, DATE'2024-01-08', 'share'),
    (9, 8, DATE'2024-01-08', 'click'),
    (10, 9, DATE'2024-01-08', 'view')
AS t(action_id, user_id, action_date, action_type)
""")

# Jan 8 window is Jan 2-8 -> users 2..9 = 8 distinct. User 8 acted twice and
# still counts once; user 1 (Jan 1) is outside the window.
expect("Q33 duplicate same-day actions counted once", SQL, [
    (d(1), 1), (d(2), 2), (d(3), 3), (d(4), 4),
    (d(5), 5), (d(6), 6), (d(7), 7), (d(8), 8),
])

# Show it directly: for the final row, a 6-PRECEDING-ROWS frame reaches back to
# Jan 4, a 5-day window -- not the Jan 2 the spec requires.
frame_start = spark.sql("""
SELECT window_start FROM (
    SELECT MIN(action_date) OVER (ORDER BY action_date, action_id
                                  ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS window_start,
           ROW_NUMBER() OVER (ORDER BY action_date DESC, action_id DESC) AS rn
    FROM user_actions
) WHERE rn = 1
""").collect()[0][0]
assert frame_start == d(4), frame_start
print(f"[PASS] Q33 ROWS frame starts {frame_start} (5 days), spec needs {d(2)} -- ROWS is not DAYS")
