"""
Q19: User with Most Friends (Bidirectional)   [Medium | Aggregation, Union]

Find the user(s) with the most ACCEPTED friends, counting A-B as a friendship
for both A and B.

How to Think:
- The table stores each friendship ONCE, as an ordered pair. Counting
  GROUP BY user1_id only counts friendships where you were the initiator —
  roughly half your friends. This is the whole question.
- Fix: UNION ALL the relation with itself, flipped, so each friendship yields
  two rows. Then a plain GROUP BY works.
- UNION ALL, not UNION: (1,2) flipped is (2,1), never a duplicate of an
  existing row, so dedup is pure cost — and if the table ever stored BOTH
  directions, UNION would hide that bug instead of surfacing it.
- Filter status = 'accepted' BEFORE the union, so pending requests never
  become friendships.

The trap:
- User 1 has a 'pending' edge to user 5. If the status filter is missing, user 1
  ties at 3 and the answer becomes wrong.
- Use RANK() = 1 rather than LIMIT 1 so genuine ties all surface.

Spark note:
- UNION ALL then group = one shuffle. Self-join alternatives cost two.
"""
from _seeds import spark, expect

SQL = """
WITH accepted AS (
    SELECT user1_id, user2_id FROM friendships WHERE status = 'accepted'
),
both_ways AS (
    SELECT user1_id AS user_id, user2_id AS friend_id FROM accepted
    UNION ALL
    SELECT user2_id AS user_id, user1_id AS friend_id FROM accepted
),
counts AS (
    SELECT user_id, COUNT(DISTINCT friend_id) AS friend_count
    FROM both_ways
    GROUP BY user_id
),
ranked AS (
    SELECT user_id, friend_count,
           RANK() OVER (ORDER BY friend_count DESC) AS rnk
    FROM counts
)
SELECT user_id, friend_count FROM ranked WHERE rnk = 1 ORDER BY user_id
"""

expect("Q19 most friends bidirectional", SQL, [(3, 3)])
