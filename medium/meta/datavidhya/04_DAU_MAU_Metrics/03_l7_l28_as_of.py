"""
Problem 03: L7 and L28 active users as of a given date.

Meta flavor: "How many L7 and L28 users did Reels have on Jan 30?"

How to Think:
- Meta vocabulary, and getting it wrong marks you as an outsider:
    L7  = distinct users active at least once in the TRAILING 7 days
    L28 = distinct users active at least once in the trailing 28 days
  Note "L7" is NOT "active on 7 of the last 7 days" in the usual DE reading —
  but different teams do use the stricter sense, so CONFIRM the definition
  before writing. The confirmation itself is the signal.
- Trailing window is inclusive of the as-of date: [D-6, D] for L7.
- Compute both in one pass with conditional distinct counts rather than two
  separate scans.

Spark note:
- One scan of events, two conditional COUNT DISTINCTs. On a real table push the
  D-27 lower bound into the partition filter so you read 28 days, not all time.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect

SQL = """
WITH as_of AS (SELECT * FROM VALUES ('2026-01-08'), ('2026-01-30') AS t(d))
SELECT a.d AS as_of_date,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 6
                           THEN e.user_id END) AS l7_users,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.d, e.event_date) BETWEEN 0 AND 27
                           THEN e.user_id END) AS l28_users
FROM as_of a
CROSS JOIN events e
GROUP BY a.d
ORDER BY a.d
"""
expect("L7 / L28 as of date", SQL, [
    ("2026-01-08", 7, 8),
    ("2026-01-30", 1, 5),
])
