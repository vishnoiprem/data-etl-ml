"""
Q10: Friend Request Acceptance Rate   [Medium | Aggregation]

Monthly acceptance rate = accepted / sent * 100, per request month.

How to Think:
- The log holds both 'sent' and 'accepted' rows for the SAME request pair.
  The denominator is sent requests; the numerator is those that were accepted.
- Attribute by the month the request was SENT, not the month it was accepted.
  Otherwise a request sent Jan 31 and accepted Feb 1 inflates February's
  numerator against a denominator it was never part of — a rate above 100%.
- Self-join sent-to-accepted on the (sender, receiver) pair, LEFT, then count.

The traps:
- Integer division: COUNT(...)/COUNT(...) is 0 in Presto/Hive. Force decimal.
- A request sent and never accepted (2->4, 4->6) must stay in the denominator.

Spark note:
- LEFT JOIN on the pair then conditional count = one shuffle, one pass.
"""
from _seeds import spark, expect

SQL = """
WITH sent AS (
    SELECT sender_id, receiver_id, action_date AS sent_date
    FROM friend_requests WHERE action = 'sent'
),
accepted AS (
    SELECT sender_id, receiver_id
    FROM friend_requests WHERE action = 'accepted'
)
SELECT DATE_FORMAT(s.sent_date, 'yyyy-MM') AS request_month,
       COUNT(*) AS requests_sent,
       COUNT(a.sender_id) AS requests_accepted,
       ROUND(100.0 * COUNT(a.sender_id) / COUNT(*), 2) AS acceptance_rate_pct
FROM sent s
LEFT JOIN accepted a
       ON a.sender_id = s.sender_id
      AND a.receiver_id = s.receiver_id
GROUP BY DATE_FORMAT(s.sent_date, 'yyyy-MM')
ORDER BY request_month
"""

expect("Q10 friend request acceptance rate", SQL, [
    ("2026-01", 3, 2, 66.67),
    ("2026-02", 2, 1, 50.00),
])
