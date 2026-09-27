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
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect

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
