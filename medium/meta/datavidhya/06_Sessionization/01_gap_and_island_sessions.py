"""
Problem 01: Sessionize raw hits with the gap-and-island pattern (30-min rule).

Meta flavor: "Turn this raw hit log into sessions. A gap over 30 minutes starts
a new session."

How to Think - the canonical 3-step pattern, memorise it:
  1. LAG the timestamp within the user, ordered by time.
  2. Flag a new session: previous is NULL (first hit) OR gap > threshold.
  3. Cumulative SUM of that flag = the session number. This is the "island".
- Why SUM and not ROW_NUMBER: the flag is 1 only at boundaries, so a running
  sum increments exactly once per new session and holds steady inside one.
- The threshold is a BOUNDARY question: is exactly 30 minutes a new session or
  the same one? This file uses strictly-greater-than, so a 30-minute gap stays
  in the same session. User 3's 29-minute gap tests the near-boundary case.
  State your choice; interviewers plant a value right on the line.

How to Remember:
- "LAG, flag, cumulative SUM."

Spark note:
- One window partitioned by user, ordered by time. Watch for skew: a bot user
  with millions of hits lands entirely in one partition.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect
from pyspark.sql import functions as F, Window

SQL = """
WITH flagged AS (
    SELECT user_id, hit_ts,
           CASE WHEN LAG(hit_ts) OVER (PARTITION BY user_id ORDER BY hit_ts) IS NULL
                     OR (UNIX_TIMESTAMP(hit_ts)
                         - UNIX_TIMESTAMP(LAG(hit_ts) OVER (PARTITION BY user_id ORDER BY hit_ts))
                        ) > 30 * 60
                THEN 1 ELSE 0 END AS is_new_session
    FROM raw_hits
)
SELECT user_id, hit_ts,
       SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY hit_ts
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_num
FROM flagged
ORDER BY user_id, hit_ts
"""
expect("gap-and-island session assignment", SQL, [
    (1, "2026-01-01 10:00:00", 1),
    (1, "2026-01-01 10:10:00", 1),
    (1, "2026-01-01 10:25:00", 1),
    (1, "2026-01-01 12:00:00", 2),
    (1, "2026-01-01 12:05:00", 2),
    (2, "2026-01-01 08:00:00", 1),
    (2, "2026-01-01 08:20:00", 1),
    (3, "2026-01-01 09:00:00", 1),
    (3, "2026-01-01 11:00:00", 2),
    (3, "2026-01-01 15:00:00", 3),
    (3, "2026-01-01 15:29:00", 3),
])

# ---- PySpark DataFrame API, same 3 steps ---------------------------------
w = Window.partitionBy("user_id").orderBy("hit_ts")
wc = w.rowsBetween(Window.unboundedPreceding, Window.currentRow)
df = (spark.table("raw_hits")
      .withColumn("prev_ts", F.lag("hit_ts").over(w))
      .withColumn("is_new_session",
                  F.when(F.col("prev_ts").isNull(), 1)
                   .when(F.unix_timestamp("hit_ts") - F.unix_timestamp("prev_ts") > 30 * 60, 1)
                   .otherwise(0))
      .withColumn("session_num", F.sum("is_new_session").over(wc))
      .orderBy("user_id", "hit_ts")
      .select("user_id", "hit_ts", "session_num"))
assert [tuple(r) for r in df.collect()] == [
    (1, "2026-01-01 10:00:00", 1), (1, "2026-01-01 10:10:00", 1),
    (1, "2026-01-01 10:25:00", 1), (1, "2026-01-01 12:00:00", 2),
    (1, "2026-01-01 12:05:00", 2), (2, "2026-01-01 08:00:00", 1),
    (2, "2026-01-01 08:20:00", 1), (3, "2026-01-01 09:00:00", 1),
    (3, "2026-01-01 11:00:00", 2), (3, "2026-01-01 15:00:00", 3),
    (3, "2026-01-01 15:29:00", 3)]
print("[PASS] sessionization — DataFrame API matches SQL")
