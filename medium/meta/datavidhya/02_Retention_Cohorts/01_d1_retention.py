"""
Problem 01: D1 retention by signup cohort.

Meta flavor: "What share of users who signed up on a given day came back the next day?"

How to Think:
- Retention is ALWAYS cohort / day-offset. Name both out loud before writing SQL.
- "D1" at Meta = active on exactly signup_date + 1 (bounded/classic retention).
- Denominator = cohort size, NOT total users. Getting this wrong is the #1 error.
- LEFT JOIN the activity, never INNER — an INNER JOIN silently drops churned
  users and inflates retention to 100%.

How to Remember:
- "Cohort on the left, activity on the right, LEFT JOIN, count DISTINCT."

The integer-division trap:
- COUNT(...)/COUNT(...) is integer division in Presto/Hive -> returns 0.
  Multiply by 100.0 (a decimal literal) to force floating point.

AI Use Cases:
- Early-churn labels for a propensity model.
- Cohort features for LTV regression.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import expect

SQL = """
SELECT u.signup_date AS cohort,
       COUNT(DISTINCT u.user_id) AS cohort_size,
       COUNT(DISTINCT e.user_id) AS retained_d1,
       ROUND(100.0 * COUNT(DISTINCT e.user_id) / COUNT(DISTINCT u.user_id), 2) AS pct_d1
FROM users u
LEFT JOIN events e
       ON e.user_id = u.user_id
      AND e.event_date = DATE_ADD(u.signup_date, 1)
GROUP BY u.signup_date
ORDER BY u.signup_date
"""

expect("D1 retention by cohort", SQL, [
    ("2026-01-01", 3, 2, 66.67),
    ("2026-01-02", 3, 2, 66.67),
    ("2026-01-08", 2, 1, 50.00),
])
