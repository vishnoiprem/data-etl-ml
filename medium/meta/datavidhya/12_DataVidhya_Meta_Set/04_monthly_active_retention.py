"""
Q04: Monthly Active User Retention   [Medium | Joins, Date Functions]

Find users active in July 2022 AND also active in June 2022.
Active = performed 'sign-in', 'like', or 'comment'.

How to Think:
- The action filter is the whole question. Applying it to only one side of the
  comparison is the classic wrong answer.
- Two equally valid shapes: self-join on user_id across the two months, or
  aggregate with conditional flags and HAVING. The flag form scans once.
- Month boundaries: use a half-open range [2022-07-01, 2022-08-01) rather than
  BETWEEN with an end date, so a timestamp at 23:59 does not fall out.

The traps:
- User 4 was active in June and appears in July, but their July row is 'logout',
  which is NOT a qualifying action. Excluded.
- User 5 is active June and August, skipping July. Excluded.

Spark note:
- Single pass + HAVING. No self-join means no second shuffle of the big table.
"""
from _seeds import spark, expect

SQL = """
SELECT user_id
FROM user_actions
WHERE action IN ('sign-in', 'like', 'comment')
GROUP BY user_id
HAVING MAX(CASE WHEN action_date >= DATE '2022-07-01'
                 AND action_date <  DATE '2022-08-01' THEN 1 ELSE 0 END) = 1
   AND MAX(CASE WHEN action_date >= DATE '2022-06-01'
                 AND action_date <  DATE '2022-07-01' THEN 1 ELSE 0 END) = 1
ORDER BY user_id
"""

expect("Q04 monthly active retention", SQL, [(1,)])
