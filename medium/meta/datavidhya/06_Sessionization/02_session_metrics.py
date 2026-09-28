"""
Problem 02: Per-session metrics (duration, hit count).

Meta flavor: "Average session length on Reels, and how many videos per session."

How to Think:
- Roll the sessionized rows up to one row per (user, session). That is the
  session-grain fact table you would actually build.
- Duration = last hit - first hit. Note what this does NOT capture: the time
  the user spent on the final hit before leaving. A single-hit session gets
  duration 0, which is right for "span of activity" and wrong for "time spent".
  Real implementations either add an assumed dwell for the last hit or use an
  explicit session_end event. Raise this — it is a genuine modelling decision,
  not a detail.
- Users 3's first two sessions are single-hit, so 0-minute durations are
  expected here rather than a bug.

Spark note:
- Reuses the window from problem 01, then one group-by. Two shuffles total.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("02-session-metrics")
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
    (1, "2026-01-01 10:00:00"), (1, "2026-01-01 10:10:00"), (1, "2026-01-01 10:25:00"),
    (1, "2026-01-01 12:00:00"), (1, "2026-01-01 12:05:00"),
    (2, "2026-01-01 08:00:00"), (2, "2026-01-01 08:20:00"),
    (3, "2026-01-01 09:00:00"),
    (3, "2026-01-01 11:00:00"),
    (3, "2026-01-01 15:00:00"), (3, "2026-01-01 15:29:00"),
],
    ["user_id", "hit_ts"]
).createOrReplaceTempView("raw_hits")


SQL = """
WITH flagged AS (
    SELECT user_id, hit_ts,
           CASE WHEN LAG(hit_ts) OVER (PARTITION BY user_id ORDER BY hit_ts) IS NULL
                     OR (UNIX_TIMESTAMP(hit_ts)
                         - UNIX_TIMESTAMP(LAG(hit_ts) OVER (PARTITION BY user_id ORDER BY hit_ts))
                        ) > 30 * 60
                THEN 1 ELSE 0 END AS is_new_session
    FROM raw_hits
),
sessions AS (
    SELECT user_id, hit_ts,
           SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY hit_ts
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_num
    FROM flagged
)
SELECT user_id, session_num,
       COUNT(*) AS hits,
       MIN(hit_ts) AS session_start,
       MAX(hit_ts) AS session_end,
       CAST((UNIX_TIMESTAMP(MAX(hit_ts)) - UNIX_TIMESTAMP(MIN(hit_ts))) / 60 AS INT)
           AS duration_min
FROM sessions
GROUP BY user_id, session_num
ORDER BY user_id, session_num
"""
expect("per-session metrics", SQL, [
    (1, 1, 3, "2026-01-01 10:00:00", "2026-01-01 10:25:00", 25),
    (1, 2, 2, "2026-01-01 12:00:00", "2026-01-01 12:05:00", 5),
    (2, 1, 2, "2026-01-01 08:00:00", "2026-01-01 08:20:00", 20),
    (3, 1, 1, "2026-01-01 09:00:00", "2026-01-01 09:00:00", 0),
    (3, 2, 1, "2026-01-01 11:00:00", "2026-01-01 11:00:00", 0),
    (3, 3, 2, "2026-01-01 15:00:00", "2026-01-01 15:29:00", 29),
])

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data (same as problem 01):
#   CREATE TABLE raw_hits (
#       user_id INT NOT NULL,
#       hit_ts  DATETIME NOT NULL
#   );
#   INSERT INTO raw_hits (user_id, hit_ts) VALUES
#       (1, '2026-01-01 10:00:00'), (1, '2026-01-01 10:10:00'),
#       (1, '2026-01-01 10:25:00'), (1, '2026-01-01 12:00:00'),
#       (1, '2026-01-01 12:05:00'),
#       (2, '2026-01-01 08:00:00'), (2, '2026-01-01 08:20:00'),
#       (3, '2026-01-01 09:00:00'), (3, '2026-01-01 11:00:00'),
#       (3, '2026-01-01 15:00:00'), (3, '2026-01-01 15:29:00');
#
# Per-session metrics (roll up sessionized rows):
#   WITH flagged AS (
#       SELECT user_id, hit_ts,
#              CASE
#                WHEN LAG(hit_ts) OVER (PARTITION BY user_id ORDER BY hit_ts) IS NULL
#                  THEN 1
#                WHEN TIMESTAMPDIFF(SECOND,
#                       LAG(hit_ts) OVER (PARTITION BY user_id ORDER BY hit_ts),
#                       hit_ts) > 30 * 60
#                  THEN 1
#                ELSE 0
#              END AS is_new_session
#       FROM raw_hits
#   ),
#   sessions AS (
#       SELECT user_id, hit_ts,
#              SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY hit_ts
#                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_num
#       FROM flagged
#   )
#   SELECT user_id, session_num,
#          COUNT(*) AS hits,
#          MIN(hit_ts) AS session_start,
#          MAX(hit_ts) AS session_end,
#          CAST(TIMESTAMPDIFF(SECOND, MIN(hit_ts), MAX(hit_ts)) / 60 AS SIGNED) AS duration_min
#   FROM sessions
#   GROUP BY user_id, session_num
#   ORDER BY user_id, session_num;
# Caveat: duration = last_hit - first_hit. It does NOT capture the time the
# user spent on the FINAL hit before leaving. A single-hit session gets 0
# (correct for "span of activity", wrong for "time spent"). Real impls add
# an assumed dwell for the last hit or use an explicit session_end event.
