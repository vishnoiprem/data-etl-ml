"""
Q16: Spam Post Percentage by Day   [Medium | Joins, String Manipulation]

Percentage of VIEWED posts that are spam, per day. Spam = content contains
the word 'spam'.

How to Think:
- The grain is (day, viewed post). Join views to content, then aggregate by day.
- Denominator = posts viewed that day, NOT all posts. Post 4 is spam but never
  viewed, so it must not appear anywhere in the calculation.
- Case sensitivity: 'SPAM offer inside' is spam. LIKE is case-SENSITIVE in
  Presto/Spark, so LOWER() the column first. Forgetting this undercounts.

The trap and the question worth asking:
- 'anti-spamming tools review' contains 'spam' as a SUBSTRING but is not spam.
  LIKE '%spam%' flags it. Whether that is desired is a definition question you
  should raise: substring match, or word-boundary match via RLIKE '\\\\bspam\\\\b'?
  This query uses substring matching (the literal reading of the question) and
  the docstring records the ambiguity — that is the behaviour to copy in a real
  interview. Post 4 is never viewed here, so the two definitions agree on this
  data; on real data they would not.

Spark note:
- Broadcast the small content/dim table; the views fact is the big side.
"""
from _seeds import spark, expect

SQL = """
SELECT v.view_date,
       COUNT(*) AS posts_viewed,
       SUM(CASE WHEN LOWER(c.content) LIKE '%spam%' THEN 1 ELSE 0 END) AS spam_viewed,
       ROUND(100.0 * SUM(CASE WHEN LOWER(c.content) LIKE '%spam%' THEN 1 ELSE 0 END)
                   / COUNT(*), 2) AS spam_pct
FROM post_views v
JOIN posts_content c ON c.post_id = v.post_id
GROUP BY v.view_date
ORDER BY v.view_date
"""

expect("Q16 spam post % by day", SQL, [
    ("2026-01-01", 4, 2, 50.00),
    ("2026-01-02", 2, 0, 0.00),
])
