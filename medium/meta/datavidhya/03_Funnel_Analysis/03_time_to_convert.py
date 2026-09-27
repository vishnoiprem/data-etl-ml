"""
Problem 03: Time to convert through the funnel.

Meta flavor: "How long does it take a viewer to purchase, and is that getting
slower?"

How to Think:
- Latency between two events for the same user: pivot to min-timestamp columns,
  then subtract. UNIX_TIMESTAMP difference / 60 gives minutes.
- Only users who did BOTH ends appear — the inner comparison naturally drops
  non-converters, which is correct: a non-converter has no conversion time,
  which is NOT the same as a conversion time of zero. Never COALESCE it to 0.
- Report a median (or percentiles) rather than a mean in the real interview:
  conversion-time distributions are heavily right-skewed, and the mean is
  dragged by a few users who bought weeks later. Saying that unprompted is
  the product-sense signal here.

Spark note:
- percentile_approx is the scalable choice; exact percentile sorts the whole
  partition.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect

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
       ROUND(PERCENTILE_APPROX(mins, 0.5), 2) AS median_mins
FROM conv
"""
expect("conversion time distribution", AGG, [(2, 15.00, 10.00)])
