"""
Problem 02: STRICT ordered funnel — each step must happen AFTER the previous.

Meta flavor: "Only count a purchase if the user actually messaged first."

Business Question
-----------------
For the same view -> message -> purchase funnel, how many users reached each
step IN ORDER? The STRICT definition requires each step to occur strictly
after the previous one for the SAME user. A user who jumped straight from
view to purchase without messaging does NOT count toward purchase here.
This is the definition product teams use when diagnosing broken flows vs.
deliberate shortcuts.

How to Think
------------
- A strict funnel is a chain of self-joins, but a cleaner form is: pivot
  per user to (min_view_ts, min_msg_ts, min_buy_ts) once, then compare
  timestamps row-locally.
- Using MIN(ts) per (user, step) and comparing is cheaper than joining raw
  events, and it is the version that survives duplicate events. User 5
  viewed twice and messaged once — without MIN we would over-count views
  and the strict comparison would still work, but the row would be wider
  than it needs to be.
- The difference from the loose count is the whole lesson: user 3 purchased
  at 12:10 with no message at all, so strict `purchase` is 1, not 2.
- Equality (`>=`) vs. strictly-after (`>`): strict funnels almost always want
  `>` so a user who fired view and message in the same millisecond does not
  count as having messaged. Be explicit which one you chose.

How to Remember
---------------
"Loose = independent counts. Strict = monotonically increasing timestamps."

Spark / Performance Note
------------------------
- Pivot to one row per user (min ts per step) FIRST. Then the comparisons
  are row-local with no further shuffle — much better than chained joins
  on raw events.
- Equality checks like `msg_ts > view_ts` are null-propagating, so a user
  who never viewed will return NULL/0 for every flag. That is what you
  want; do not COALESCE it to 0 because 0 here means "did not reach",
  not "reached instantly".

AI Use Cases
------------
- Strict conversion is the right label for "completed purchase through the
  intended flow" in supervised ranking and fraud models.
- Drop in strict purchase rate is a leading indicator of a flow-breaking
  release.
- Strict view -> message conversion is the canonical "did the messaging
  surface get used" KPI.
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
