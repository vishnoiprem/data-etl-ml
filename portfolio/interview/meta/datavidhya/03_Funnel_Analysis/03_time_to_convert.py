"""
Problem 03: Time to convert through the funnel.

Meta flavor: "How long does it take a viewer to purchase, and is that getting
slower?"

Business Question
-----------------
For users who entered the funnel and completed it, how long did conversion
take? This is a latency question: between the user's first view and the
purchase that resulted from it, how many minutes (or hours, or days) elapsed?
Tracking this over time tells product whether the funnel is speeding up or
slowing down — a sudden +20% jump in median time-to-convert is often the
first signal of a checkout-bug release.

How to Think
------------
- Latency between two events for the same user: pivot to min-timestamp
  columns, then subtract. UNIX_TIMESTAMP difference / 60 gives minutes.
- Only users who did BOTH ends appear — the inner comparison naturally drops
  non-converters, which is correct: a non-converter has no conversion time,
  which is NOT the same as a conversion time of zero. Never COALESCE the
  result to 0; the missing row IS the signal that they did not convert.
- Report a median (or percentiles) rather than a mean in the real interview:
  conversion-time distributions are heavily right-skewed, and the mean is
  dragged by a few users who bought weeks later. Saying that unprompted is
  the product-sense signal here — interviewers want to hear you reach for
  a robust statistic.
- The first query gives per-user latency (useful for outlier inspection);
  the second query rolls it up to a distribution (useful for dashboards).
- Watch the divisor: / 60.0 (float) gives minutes; an integer / 60 would
  zero out every sub-minute conversion. The same integer-division trap as
  retention applies.

How to Remember
---------------
"Non-converter has no conversion time — never COALESCE that to zero."

Spark / Performance Note
------------------------
- percentile_approx is the scalable choice; exact PERCENTILE sorts the
  whole partition (fine on 2 rows, expensive at scale). The expected row
  count for the median assertion is tiny on purpose, so PERCENTILE is the
  correct choice here and you get the interpolated median for free.
- If you ever flip to approximate, PERCENTILE_APPROX returns an actual data
  point (10.0 for {10, 20}) instead of interpolating to 15.0 — wrong on
  small data, fine at scale.

AI Use Cases
------------
- Time-to-convert is the primary label for "fast" vs. "slow" cohorts in
  LTV regression — fast converters usually have higher retention.
- p90 time-to-convert is a key SLA metric for the checkout reliability
  dashboard.
- Per-user latency feeds sessionization and dwell-time models downstream.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("03-time-to-convert")
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
    (1, "view",     "2026-01-01 10:00:00"),
    (1, "message",  "2026-01-01 10:05:00"),
    (1, "purchase", "2026-01-01 10:20:00"),
    (2, "view",     "2026-01-01 11:00:00"),
    (2, "message",  "2026-01-01 11:30:00"),
    (3, "view",     "2026-01-01 12:00:00"),
    (3, "purchase", "2026-01-01 12:10:00"),   # skipped 'message'
    (4, "view",     "2026-01-02 09:00:00"),
    (5, "view",     "2026-01-02 09:30:00"),
    (5, "view",     "2026-01-02 09:40:00"),   # duplicate step
    (5, "message",  "2026-01-02 09:50:00"),
],
    ["user_id", "step", "event_ts"]
).createOrReplaceTempView("funnel_events")


SQL = """
WITH per_user AS (
    SELECT user_id,
           MIN(CASE WHEN step = 'view'     THEN event_ts END) AS view_ts,
           MIN(CASE WHEN step = 'purchase' THEN event_ts END) AS buy_ts
    FROM funnel_events
    GROUP BY user_id
)
SELECT user_id,
       ROUND((UNIX_TIMESTAMP(buy_ts) - UNIX_TIMESTAMP(view_ts)) / 60.0, 2) AS minutes_to_buy
FROM per_user
WHERE buy_ts IS NOT NULL AND view_ts IS NOT NULL
ORDER BY user_id
"""
expect("time to convert per user", SQL, [(1, 20.00), (3, 10.00)])

AGG = """
WITH per_user AS (
    SELECT user_id,
           MIN(CASE WHEN step = 'view'     THEN event_ts END) AS view_ts,
           MIN(CASE WHEN step = 'purchase' THEN event_ts END) AS buy_ts
    FROM funnel_events GROUP BY user_id
),
conv AS (
    SELECT (UNIX_TIMESTAMP(buy_ts) - UNIX_TIMESTAMP(view_ts)) / 60.0 AS mins
    FROM per_user WHERE buy_ts IS NOT NULL AND view_ts IS NOT NULL
)
SELECT COUNT(*) AS converters,
       ROUND(AVG(mins), 2) AS avg_mins,
       ROUND(PERCENTILE(mins, 0.5), 2) AS median_mins
FROM conv
"""
# PERCENTILE is exact and interpolates: median of {10, 20} = 15.0.
# PERCENTILE_APPROX would return an actual data point (10.0) instead — fine at
# scale, wrong when you are asserting an interpolated median on 2 rows.
expect("conversion time distribution", AGG, [(2, 15.00, 15.00)])


# ============================================================================
# MySQL equivalent (MySQL 8.0+) -- paste the un-commented block into a
# `mysql` client to reproduce the same results outside of PySpark.
# ============================================================================
# CREATE DATABASE IF NOT EXISTS funnel_demo;
# USE funnel_demo;
#
# CREATE TABLE funnel_events (
#     user_id  INT          NOT NULL,
#     step     VARCHAR(20)  NOT NULL,
#     event_ts DATETIME     NOT NULL
# );
#
# INSERT INTO funnel_events (user_id, step, event_ts) VALUES
#     (1, 'view',     '2026-01-01 10:00:00'),
#     (1, 'message',  '2026-01-01 10:05:00'),
#     (1, 'purchase', '2026-01-01 10:20:00'),
#     (2, 'view',     '2026-01-01 11:00:00'),
#     (2, 'message',  '2026-01-01 11:30:00'),
#     (3, 'view',     '2026-01-01 12:00:00'),
#     (3, 'purchase', '2026-01-01 12:10:00'),   -- skipped 'message'
#     (4, 'view',     '2026-01-02 09:00:00'),
#     (5, 'view',     '2026-01-02 09:30:00'),
#     (5, 'view',     '2026-01-02 09:40:00'),   -- duplicate step
#     (5, 'message',  '2026-01-02 09:50:00');
#
# -- Per-user latency (same as PySpark):
# WITH per_user AS (
#     SELECT user_id,
#            MIN(CASE WHEN step = 'view'     THEN event_ts END) AS view_ts,
#            MIN(CASE WHEN step = 'purchase' THEN event_ts END) AS buy_ts
#     FROM funnel_events
#     GROUP BY user_id
# )
# SELECT user_id,
#        ROUND((UNIX_TIMESTAMP(buy_ts) - UNIX_TIMESTAMP(view_ts)) / 60.0, 2) AS minutes_to_buy
# FROM per_user
# WHERE buy_ts IS NOT NULL AND view_ts IS NOT NULL
# ORDER BY user_id;
#
# -- Per-user expected output: (1, 20.00), (3, 10.00)
#
# -- Distribution roll-up. MySQL 8.0 has no exact PERCENTILE() function;
# -- the canonical median-via-Windows form is below. For 2 rows, it
# -- correctly returns the interpolated 15.00 (avg of 10.00 and 20.00).
# WITH per_user AS (
#     SELECT user_id,
#            MIN(CASE WHEN step = 'view'     THEN event_ts END) AS view_ts,
#            MIN(CASE WHEN step = 'purchase' THEN event_ts END) AS buy_ts
#     FROM funnel_events GROUP BY user_id
# ),
# conv AS (
#     SELECT (UNIX_TIMESTAMP(buy_ts) - UNIX_TIMESTAMP(view_ts)) / 60.0 AS mins
#     FROM per_user WHERE buy_ts IS NOT NULL AND view_ts IS NOT NULL
# ),
# ranked AS (
#     SELECT mins,
#            ROW_NUMBER() OVER (ORDER BY mins) AS rn,
#            COUNT(*)     OVER ()              AS n
#     FROM conv
# )
# SELECT (SELECT COUNT(*) FROM conv) AS converters,
#        ROUND((SELECT AVG(mins) FROM conv), 2) AS avg_mins,
#        ROUND(AVG(CASE WHEN rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2))
#                       THEN mins END), 2) AS median_mins
# FROM ranked;
#
# -- Expected output (same as the PySpark assertion above):
# -- +-----------+----------+------------+
# -- | converters| avg_mins | median_mins|
# -- +-----------+----------+------------+
# -- |         2 |    15.00 |      15.00 |
# -- +-----------+----------+------------+
