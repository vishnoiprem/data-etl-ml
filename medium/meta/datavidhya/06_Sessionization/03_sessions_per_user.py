"""
Problem 03: Sessions per user (and why you should not COUNT DISTINCT session_num).

Meta flavor: "How many sessions does the average user have per day?"

How to Think:
- Once sessions are numbered per user, the session count per user is simply
  MAX(session_num) — the numbering is dense and starts at 1 by construction.
  Equivalent and safer if the numbering scheme ever changes:
  COUNT(DISTINCT session_num).
- The subtle bug to avoid: session_num is only unique WITHIN a user. If you
  ever aggregate across users, you must group by (user_id, session_num) or
  build a globally unique session_key. A global COUNT(DISTINCT session_num)
  across all users returns 3 here, not the true 6 sessions — this file asserts
  both so the failure mode is visible.
- In a real warehouse you would emit session_key = hash(user_id, session_start)
  so downstream joins cannot make this mistake.

Spark note:
- Cheap rollup on the already-sessionized set.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("03-sessions-per-user")
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


BASE = """
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
"""

expect("sessions per user", BASE + """
SELECT user_id, MAX(session_num) AS sessions
FROM sessions GROUP BY user_id ORDER BY user_id
""", [(1, 2), (2, 1), (3, 3)])

expect("total sessions — correct (grouped by user+session)", BASE + """
SELECT COUNT(*) AS total_sessions
FROM (SELECT user_id, session_num FROM sessions GROUP BY user_id, session_num) t
""", [(6,)])

# The WRONG version, asserted so the failure mode is documented rather than
# discovered in production: session_num is not globally unique.
expect("total sessions — WRONG (global distinct session_num)", BASE + """
SELECT COUNT(DISTINCT session_num) AS looks_like_total FROM sessions
""", [(3,)])

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data (same as problems 01/02):
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
# Sessionize (same LAG + flag + cumulative SUM):
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
#   SELECT user_id, MAX(session_num) AS sessions
#   FROM sessions GROUP BY user_id ORDER BY user_id;
#
# Total sessions (correct — group by user+session first):
#   SELECT COUNT(*) AS total_sessions
#   FROM (
#       SELECT user_id, session_num
#       FROM sessions
#       GROUP BY user_id, session_num
#   ) t;
#
# WRONG version (session_num is only unique WITHIN a user):
#   SELECT COUNT(DISTINCT session_num) AS looks_like_total FROM sessions;
# Production tip: emit a globally unique session_key = hash(user_id, session_start)
# so downstream joins cannot accidentally fall into this trap.
