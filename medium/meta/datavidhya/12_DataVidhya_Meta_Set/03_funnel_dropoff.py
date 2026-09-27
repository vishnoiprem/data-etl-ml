"""
Q03: Event Funnel Drop-Off Analysis   [Hard | Joins, CTEs]

Users progress view -> click -> purchase. Compute the drop-off percentage at
each stage and identify where the funnel leaks worst.

How to Think:
- Count DISTINCT USERS per step, not events — user 4 viewed twice and would
  otherwise be double counted.
- Define the funnel order yourself; the event table has no inherent order.
  A VALUES list of (step, step_order) is the cleanest way to pin it.
- "Conversion from previous" uses LAG over the ordered steps.
- drop_off_pct = 100 - conversion_from_previous_pct.

The traps:
- User 5 purchased WITHOUT clicking. A strict funnel should arguably not count
  them, but the naive per-step count does. Say this out loud in the interview:
  "Do you want a strict ordered funnel, or independent step counts?" That single
  question is the product signal Meta is scoring.
- This query uses the LOOSE definition (independent step counts).

Spark note:
- Counting distinct users per step is one shuffle; window over 3 rows is free.
"""
from _seeds import spark, expect

SQL = """
WITH step_order AS (
    SELECT * FROM VALUES ('view', 1), ('click', 2), ('purchase', 3)
                      AS t(step, step_num)
),
per_step AS (
    SELECT s.step,
           s.step_num,
           COUNT(DISTINCT f.user_id) AS users
    FROM step_order s
    LEFT JOIN funnel f ON f.event_name = s.step
    GROUP BY s.step, s.step_num
)
SELECT step,
       users,
       ROUND(100.0 * users / LAG(users) OVER (ORDER BY step_num), 2) AS conv_from_prev_pct,
       ROUND(100.0 - 100.0 * users / LAG(users) OVER (ORDER BY step_num), 2) AS drop_off_pct
FROM per_step
ORDER BY step_num
"""

expect("Q03 funnel drop-off", SQL, [
    ("view", 5, None, None),
    ("click", 3, 60.00, 40.00),
    ("purchase", 2, 66.67, 33.33),
])
