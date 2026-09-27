"""
Q11: Campaign Success Rate by Language   [Medium | Aggregation]

Success rate grouped by language, sorted by rate.

How to Think:
- AVG over a 0/1 flag IS the rate; you rarely need SUM/COUNT.
  AVG(is_success) * 100 is shorter and less error-prone than two counts.
- Multiply by 100.0 (decimal literal) so integer division cannot bite.
- Always return the denominator alongside a rate. "100% success" on 3 campaigns
  means nothing, and volunteering the sample size is a product-sense signal.

Spark note:
- Single shuffle aggregate; nothing clever required.
"""
from _seeds import spark, expect

SQL = """
SELECT language,
       COUNT(*) AS campaigns,
       SUM(is_success) AS successes,
       ROUND(100.0 * AVG(is_success), 2) AS success_rate_pct
FROM campaigns
GROUP BY language
ORDER BY success_rate_pct DESC, language
"""

expect("Q11 campaign success rate by language", SQL, [
    ("th", 3, 3, 100.00),
    ("en", 4, 2, 50.00),
    ("ja", 2, 0, 0.00),
])
