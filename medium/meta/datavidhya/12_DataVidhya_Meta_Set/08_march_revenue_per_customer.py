"""
Q08: Customer Revenue in March   [Medium | Date Functions, Aggregation]

Revenue per customer for orders placed in March, revenue = quantity * unit_cost,
sorted descending.

How to Think:
- Revenue is computed PER ROW then summed: SUM(quantity * unit_cost).
  SUM(quantity) * SUM(unit_cost) is a different (wrong) number — a classic slip.
- Filter the month with a half-open range on the date, not by extracting MONTH,
  so the predicate stays partition-prunable and the year is not ignored.
  EXTRACT(MONTH ...) = 3 would also match March of every other year.

The trap:
- The seed data has a February and an April order to catch a missing or
  too-wide date filter.

Spark note:
- On a partitioned table, `order_date >= '2026-03-01' AND < '2026-04-01'`
  prunes partitions. `MONTH(order_date) = 3` forces a full scan — this is the
  "would this scan the whole table?" reasoning Meta rewards.
"""
from _seeds import spark, expect

SQL = """
SELECT customer_id,
       ROUND(SUM(quantity * unit_cost), 2) AS revenue
FROM cust_orders
WHERE order_date >= DATE '2026-03-01'
  AND order_date <  DATE '2026-04-01'
GROUP BY customer_id
ORDER BY revenue DESC, customer_id
"""

expect("Q08 March revenue per customer", SQL, [(11, 90.0), (10, 60.0)])
