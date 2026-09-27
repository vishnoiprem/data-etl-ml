"""
Q18: Average Friend Requests Sent Per Week   [Medium | Date Functions, Aggregation]

Average requests sent per week per user, based on their request activity span.

How to Think:
- "Per week over their activity span" needs a denominator DEFINITION, and the
  question does not give one. State your choice explicitly:
      weeks = FLOOR(DATEDIFF(last, first) / 7) + 1
  The +1 matters: a user whose requests all land in one week spans 1 week, not
  0 weeks, and dividing by 0 would error.
- This is the single most important habit in a Meta SQL round: when the metric
  is under-specified, define it out loud and move on. Do not silently pick one.
- Only 'sent' rows belong in the numerator; 'accepted' rows are a different
  event and would double-count.

The trap:
- A user with a single request has span 0 days. Without the +1 (or a GREATEST
  guard) the query divides by zero.

Spark note:
- One shuffle by sender. Denominator is arithmetic on aggregates, no extra pass.
"""
from _seeds import spark, expect

SQL = """
SELECT sender_id,
       COUNT(*) AS requests_sent,
       FLOOR(DATEDIFF(MAX(action_date), MIN(action_date)) / 7) + 1 AS weeks_active,
       ROUND(COUNT(*) / (FLOOR(DATEDIFF(MAX(action_date), MIN(action_date)) / 7) + 1), 2)
           AS avg_requests_per_week
FROM friend_requests
WHERE action = 'sent'
GROUP BY sender_id
ORDER BY sender_id
"""

expect("Q18 avg requests per week", SQL, [
    (1, 2, 1, 2.00),
    (2, 1, 1, 1.00),
    (3, 1, 1, 1.00),
    (4, 1, 1, 1.00),
])
