"""
Problem 02: D7 retention by signup cohort.

Meta flavor: "D7 retention for the January 1 cohort."

How to Think:
- Identical shape to D1; only the offset changes. Parameterise the offset rather
  than writing seven near-identical queries (see 06_retention_curve_d0_d7.py).
- Watch the reporting window: a cohort younger than 7 days CANNOT have D7 data.
  Reporting 0% for an immature cohort is a real bug — exclude it instead.
  Here the 2026-01-08 cohort genuinely has no D7 activity in the seed data.

How to Remember:
- "Same skeleton, new offset. Guard the immature cohorts."

AI Use Cases:
- D7 is the standard early-retention target variable for growth models.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import expect

SQL = """
SELECT u.signup_date AS cohort,
       COUNT(DISTINCT u.user_id) AS cohort_size,
       COUNT(DISTINCT e.user_id) AS retained_d7,
       ROUND(100.0 * COUNT(DISTINCT e.user_id) / COUNT(DISTINCT u.user_id), 2) AS pct_d7
FROM users u
LEFT JOIN events e
       ON e.user_id = u.user_id
      AND e.event_date = DATE_ADD(u.signup_date, 7)
GROUP BY u.signup_date
ORDER BY u.signup_date
"""

expect("D7 retention by cohort", SQL, [
    ("2026-01-01", 3, 1, 33.33),
    ("2026-01-02", 3, 1, 33.33),
    ("2026-01-08", 2, 0, 0.00),
])
