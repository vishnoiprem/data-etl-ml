-- Problem 6 — Total sales and unique paying customers, grouped by payment type
-- Difficulty: Easy | Round: Screening | Pattern: GROUP BY + COUNT(DISTINCT) + SUM + ORDER BY DESC

-- Goal
-- ----
-- For each payment_type, return:
--   * total_sales   = SUM(amount)
--   * unique_customers = COUNT(DISTINCT customer_id)
-- Sorted by total_sales DESC.

-- Interview script
-- ----------------
-- "Joins are inner by default; I want all payment types, even if they
--  have no transactions. LEFT JOIN from payment_types to transactions.
--  COUNT(DISTINCT ...) handles the 'unique' requirement. The sort order
--  matches the question's phrasing ('sorted in descending order by
--  payment type' likely means 'by the sales metric'). I'll comment that
--  choice in the interview."

-- Solution
-- --------
SELECT
    pt.name                                  AS payment_type,
    COALESCE(SUM(t.amount), 0)               AS total_sales,
    COUNT(DISTINCT t.customer_id)            AS unique_customers
FROM payment_types AS pt
LEFT JOIN transactions AS t ON t.payment_type_id = pt.payment_type_id
GROUP BY pt.payment_type_id, pt.name
ORDER BY total_sales DESC;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- credit_card: most rows. Nina, Priya, Rosa, Tariq, Uma -> 5 unique.
-- paypal:      Oscar (3 txs), Sam (3 txs) -> 2 unique.
-- gift_card:   Quentin only -> 1 unique.
-- ('credit_card', 245.48, 5)
-- ('paypal', 80.25, 2)
-- ('gift_card', 34.75, 1)
--
-- Talk-track follow-ups
-- ---------------------
-- "Why COALESCE on SUM but not on COUNT?"
--   -> SUM over an empty group returns NULL, which would show up as
--      blank — COALESCE turns it into 0. COUNT(DISTINCT) over an empty
--      group correctly returns 0, no COALESCE needed.
-- "Could you also show the share of total sales?"
--   -> Yes, add a window function: 100.0 * SUM(amount) / SUM(SUM(amount))
--      OVER () — that computes the grand total once and divides per row.
