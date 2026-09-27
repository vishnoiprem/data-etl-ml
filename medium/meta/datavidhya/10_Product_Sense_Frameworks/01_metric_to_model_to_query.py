"""
Problem 01: The metric -> behaviour -> grain -> query chain (Marketplace).

Meta flavor: "How would you measure the health of Facebook Marketplace?"

THIS IS THE ROUND. Meta's combined technical round chains exactly this:
define the metric, model the tables, write the query, then investigate a move.
The reported signature failure is a model that cannot serve the metric you
named two questions earlier — so derive them in that order, not backwards.

The fixed spine to say out loud (30 seconds, every time):
  1. USER VALUE  - "Marketplace works when people find things worth buying
                    from sellers they trust."
  2. BEHAVIOUR   - the behaviour that PROVES it is completed transactions with
                    repeat buyers, not listing counts or page views.
  3. METRIC      - ONE primary + ONE guardrail:
                     primary   = weekly completed-order GMV per active buyer
                     guardrail = cancellation rate
                    Do NOT recite ten metrics. Pick, then defend.
  4. GRAIN       - "one row per order" for the fact; buyer/seller/date as dims.
  5. QUERY       - write it against the grain you just declared.

Why a guardrail: GMV alone is gameable and can rise while the product rots —
a spike in orders that all cancel is a worse product and a better GMV number.
Naming the guardrail unprompted is the strongest single product signal here.

Spark note:
- Filter to completed BEFORE aggregating; cancellations must never enter GMV.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect

# PRIMARY metric at the declared grain (one row per order).
expect("primary: daily completed GMV", """
SELECT order_date,
       COUNT(*) AS completed_orders,
       ROUND(SUM(gross_amount), 2) AS gmv
FROM orders
WHERE status = 'completed'
GROUP BY order_date
ORDER BY order_date
""", [
    ("2026-01-01", 2, 65.00),
    ("2026-01-03", 1, 60.00),
    ("2026-01-08", 1, 10.00),
])

# GUARDRAIL: cancellation rate over ALL orders, not just completed ones.
# Denominator choice is the whole point — completed-only would always give 0%.
expect("guardrail: cancellation rate", """
SELECT COUNT(*) AS all_orders,
       SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
       ROUND(100.0 * AVG(CASE WHEN status = 'cancelled' THEN 1.0 ELSE 0.0 END), 2)
           AS cancel_rate_pct
FROM orders
""", [(5, 1, 20.00)])

# The composite the primary metric actually names: GMV per active buyer.
expect("primary: GMV per active buyer", """
SELECT COUNT(DISTINCT buyer_id) AS active_buyers,
       ROUND(SUM(gross_amount), 2) AS gmv,
       ROUND(SUM(gross_amount) / COUNT(DISTINCT buyer_id), 2) AS gmv_per_buyer
FROM orders WHERE status = 'completed'
""", [(3, 135.00, 45.00)])
