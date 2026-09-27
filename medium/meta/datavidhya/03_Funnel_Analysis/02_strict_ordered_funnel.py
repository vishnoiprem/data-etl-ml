"""
Problem 02: STRICT ordered funnel — each step must happen AFTER the previous.

Meta flavor: "Only count a purchase if the user actually messaged first."

How to Think:
- A strict funnel is a chain of self-joins (or min-timestamp comparisons):
  first view, then the earliest message AFTER that view, then the earliest
  purchase AFTER that message.
- Using MIN(ts) per (user, step) and comparing is cheaper than joining raw
  events, and it is the version that survives duplicate events.
- The difference from the loose count is the whole lesson: user 3 purchased at
  12:10 with no message at all, so strict `purchase` is 1, not 2.

How to Remember:
- "Loose = independent counts. Strict = monotonically increasing timestamps."

Spark note:
- Pivot to one row per user (min ts per step) FIRST. Then the comparisons are
  row-local with no further shuffle — much better than chained joins on events.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect

SQL = """
WITH per_user AS (
    SELECT user_id,
           MIN(CASE WHEN step = 'view'     THEN event_ts END) AS view_ts,
           MIN(CASE WHEN step = 'message'  THEN event_ts END) AS msg_ts,
           MIN(CASE WHEN step = 'purchase' THEN event_ts END) AS buy_ts
    FROM funnel_events
    GROUP BY user_id
),
reached AS (
    SELECT user_id,
           CASE WHEN view_ts IS NOT NULL THEN 1 ELSE 0 END AS did_view,
           CASE WHEN view_ts IS NOT NULL AND msg_ts > view_ts THEN 1 ELSE 0 END AS did_msg,
           CASE WHEN view_ts IS NOT NULL AND msg_ts > view_ts
                     AND buy_ts > msg_ts THEN 1 ELSE 0 END AS did_buy
    FROM per_user
)
SELECT 'view' AS step, SUM(did_view) AS users, 1 AS step_num FROM reached
UNION ALL SELECT 'message', SUM(did_msg), 2 FROM reached
UNION ALL SELECT 'purchase', SUM(did_buy), 3 FROM reached
ORDER BY step_num
"""
expect("strict ordered funnel", SQL, [
    ("view", 5, 1), ("message", 3, 2), ("purchase", 1, 3),
])
