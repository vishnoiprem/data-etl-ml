"""
Q14: Days Between First and Last Post   [Medium | Date Functions, Aggregation]

For users who posted 2+ times in 2024, the days between first and last post.

How to Think:
- Filter to 2024 FIRST, then aggregate. The "2+ posts" count must be counted
  within 2024 only, not lifetime.
- DATEDIFF(MAX(d), MIN(d)) in one pass. No self-join needed to get both ends —
  reaching for a self-join here is a tell that you do not trust aggregates.
- Note the boundary semantics: Jan 1 to Dec 31 is 365 days, not 366, even in a
  leap year, because it is a difference not an inclusive count.

The trap:
- User 4 has a 2023 post plus two 2024 posts. If the year filter is missing or
  applied after the HAVING, their span becomes ~100 days instead of 10.
- User 3 has exactly one 2024 post and must be excluded.

Spark note:
- Push the year predicate into the scan; on a date-partitioned posts table this
  is the difference between reading one year and reading all history.
"""
from _seeds import spark, expect

SQL = """
SELECT user_id,
       COUNT(*) AS posts_2024,
       DATEDIFF(MAX(post_date), MIN(post_date)) AS days_between
FROM user_posts
WHERE post_date >= DATE '2024-01-01'
  AND post_date <  DATE '2025-01-01'
GROUP BY user_id
HAVING COUNT(*) >= 2
ORDER BY days_between DESC, user_id
"""

expect("Q14 days first-to-last post 2024", SQL, [
    (2, 3, 365), (1, 2, 30), (4, 2, 10),
])
