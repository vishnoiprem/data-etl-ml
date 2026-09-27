"""
Problem 03: D28 retention by signup cohort.

Meta flavor: "D28 retention — does the product hold users for a month?"

How to Think:
- Same skeleton again. The interesting part is what D28 means for the business:
  D1 measures onboarding, D28 measures habit.
- Only user 6 (signup 2026-01-02, active 2026-01-30) hits D28 in this seed, which
  is exactly the kind of sparse tail you see in real cohort tables.

How to Remember:
- "D1 = onboarding. D7 = interest. D28 = habit."

AI Use Cases:
- D28 is the usual 'good user' label for acquisition-quality scoring.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import expect

SQL = """
SELECT u.signup_date AS cohort,
       COUNT(DISTINCT u.user_id) AS cohort_size,
       COUNT(DISTINCT e.user_id) AS retained_d28,
       ROUND(100.0 * COUNT(DISTINCT e.user_id) / COUNT(DISTINCT u.user_id), 2) AS pct_d28
FROM users u
LEFT JOIN events e
       ON e.user_id = u.user_id
      AND e.event_date = DATE_ADD(u.signup_date, 28)
GROUP BY u.signup_date
ORDER BY u.signup_date
"""

expect("D28 retention by cohort", SQL, [
    ("2026-01-01", 3, 0, 0.00),
    ("2026-01-02", 3, 1, 33.33),
    ("2026-01-08", 2, 0, 0.00),
])
