"""
Q13: Popularity Percentage by Domain   [Hard | Aggregation + Window]

Each domain's percentage share of total views.

How to Think:
- Share-of-total needs the grand total on every row. Two ways:
    1. SUM(views) OVER ()          <- window with empty OVER, one pass
    2. CROSS JOIN (SELECT SUM(views) ...) <- explicit, also fine
  Form 1 is what the "Hard" tag is really testing: knowing that OVER () with no
  PARTITION BY and no ORDER BY means "the whole result set".
- Shares must sum to 100. Say that as your own sanity check — interviewers
  notice candidates who verify their own output.

Spark note:
- SUM(...) OVER () collapses to a single partition to compute the total, then
  broadcasts it. Cheap on aggregates, dangerous on raw rows.
"""
from _seeds import spark, expect

SQL = """
SELECT domain,
       views,
       ROUND(100.0 * views / SUM(views) OVER (), 2) AS pct_of_total
FROM domain_views
ORDER BY pct_of_total DESC, domain
"""

expect("Q13 popularity % by domain", SQL, [
    ("facebook.com", 500, 50.00),
    ("instagram.com", 300, 30.00),
    ("whatsapp.com", 150, 15.00),
    ("threads.net", 50, 5.00),
])
