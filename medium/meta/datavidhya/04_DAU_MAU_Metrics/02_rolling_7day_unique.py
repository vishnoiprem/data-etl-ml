"""
Problem 02: Rolling 7-day unique users (rolling WAU).

Meta flavor: "Give me a 7-day rolling unique-user count so the weekday
seasonality stops screaming at me."

How to Think:
- COUNT(DISTINCT ...) cannot be a window function. That rules out the obvious
  `COUNT(DISTINCT user_id) OVER (ORDER BY date ROWS 6 PRECEDING)`.
- A rolling DISTINCT genuinely needs each day joined to the 7-day window of
  days behind it, because a user active on day 1 and day 7 must be counted once
  across that window but separately in a different window. Unlike a cumulative
  distinct count (see the running-distinct problem), the first-seen trick does
  NOT work here — the set of days in scope keeps changing.
- So: self-join on DATEDIFF BETWEEN 0 AND 6, then COUNT DISTINCT per anchor day.

The trap:
- Anchor on the day list, not the event list, or days with zero activity vanish
  from the series. Here every day has activity, so the shapes agree — on real
  data add a calendar spine.

Spark note:
- This self-join is a range join and it does NOT scale: every day fans out to
  7 days of events. At Meta volume you would instead maintain a daily
  first-seen/last-seen table, or accept HyperLogLog (approx_count_distinct)
  sketches that can be merged across days. Say that out loud — the interviewer
  is usually waiting for exactly this scaling caveat.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("02-rolling-7day-unique")
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
WITH days AS (SELECT DISTINCT event_date FROM events)
SELECT d.event_date,
       COUNT(DISTINCT e.user_id) AS rolling_7d_unique
FROM days d
JOIN events e
  ON DATEDIFF(d.event_date, e.event_date) BETWEEN 0 AND 6
GROUP BY d.event_date
ORDER BY d.event_date
"""
expect("rolling 7-day unique users", SQL, [
    ("2026-01-01", 3),
    ("2026-01-02", 6),
    ("2026-01-03", 6),
    ("2026-01-08", 7),
    ("2026-01-09", 5),
    ("2026-01-30", 1),
])

# The mergeable-sketch alternative that DOES scale. approx_count_distinct is
# HyperLogLog under the hood; the error is a few percent, which is acceptable
# for a trend line and unacceptable for billing.
APPROX = """
WITH days AS (SELECT DISTINCT event_date FROM events)
SELECT d.event_date, APPROX_COUNT_DISTINCT(e.user_id) AS approx_7d_unique
FROM days d
JOIN events e ON DATEDIFF(d.event_date, e.event_date) BETWEEN 0 AND 6
GROUP BY d.event_date
ORDER BY d.event_date
"""
expect("rolling 7-day unique (HLL approx, exact at this size)", APPROX, [
    ("2026-01-01", 3), ("2026-01-02", 6), ("2026-01-03", 6),
    ("2026-01-08", 7), ("2026-01-09", 5), ("2026-01-30", 1),
])
