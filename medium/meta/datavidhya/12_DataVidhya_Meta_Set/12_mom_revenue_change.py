"""
Q12: Monthly Revenue Percentage Change   [Medium | Windows, Date Functions]

Monthly revenue and month-over-month % change.

How to Think:
- pct_change = (current - previous) / previous * 100, previous via LAG.
- The first month HAS no previous value. It must be NULL, not 0 — reporting 0%
  growth for the first month is a factual error. Do not COALESCE it away.
- Divide-by-zero: if a month can have zero revenue, guard with NULLIF(prev, 0),
  which turns the division into NULL instead of erroring.
- Order the window by a sortable month key. 'yyyy-MM' strings sort correctly;
  'MM-yyyy' does not. Worth stating.

The trap:
- Month 2026-04 is flat versus March, so the answer must be exactly 0.00 —
  distinguishable from the NULL first month. If your query returns 0 for both,
  you have conflated "no change" with "no prior data".

Spark note:
- A single global window (no PARTITION BY) funnels every row to one partition.
  Fine for 4 months of aggregates; never do it on raw events.
"""
from _seeds import spark, expect

SQL = """
SELECT month,
       revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
                   / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2) AS mom_pct_change
FROM monthly_rev
ORDER BY month
"""

expect("Q12 MoM revenue % change", SQL, [
    ("2026-01", 1000.0, None),
    ("2026-02", 1200.0, 20.00),
    ("2026-03",  900.0, -25.00),
    ("2026-04",  900.0, 0.00),
])
