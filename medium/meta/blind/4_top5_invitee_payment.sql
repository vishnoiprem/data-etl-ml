-- Problem 4 — Top 5 customers by average payment per book MADE BY THEIR INVITEES
-- Difficulty: Medium | Round: Screening | Pattern: self-join via invitations + AVG

-- Goal
-- ----
-- We have a customer who invited other customers (the inviter). For
-- each inviter, compute the average amount-per-book paid by the people
-- they invited. Return the top 5 inviters by that metric.

-- Two interpretations:
--   A) "average payment per book" = AVG(amount) over invitees' transactions
--      (each row is already one book, so it's just AVG(amount))
--   B) "average payment per book" = SUM(amount) / COUNT(book_id)
--      over invitees' transactions
-- Both produce the same number when each transaction is a single book.
-- For multi-book transactions you'd want (B). We'll do (B) for clarity.

-- Interview script
-- ----------------
-- "I need to join customers to themselves via the invitations table
--  (self-join), then to transactions for the invitees, then aggregate.
--  I'll use a CTE for the invitee transactions so the SQL reads top-down."

-- Solution
-- --------
WITH invitee_payments AS (
    SELECT
        inviter.customer_id         AS inviter_id,
        inviter.name                AS inviter_name,
        t.transaction_id,
        t.amount,
        t.book_id
    FROM customers AS inviter
    JOIN invitations AS i  ON i.inviter_id  = inviter.customer_id
    JOIN customers  AS ie ON ie.customer_id = i.invitee_id
    JOIN transactions AS t ON t.customer_id = ie.customer_id
)
SELECT
    inviter_id,
    inviter_name,
    SUM(amount) * 1.0 / NULLIF(COUNT(book_id), 0) AS avg_payment_per_book
FROM invitee_payments
GROUP BY inviter_id, inviter_name
ORDER BY avg_payment_per_book DESC
LIMIT 5;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- Nina (1001) invited Oscar + Priya + Uma.
--   Their transactions:
--     Oscar: 8.00, 14.75, 22.00  -> total 44.75, 3 books
--     Priya: 7.50, 18.00, 10.00   -> total 35.50, 3 books
--     Uma:   9.50, 12.00, 16.50   -> total 38.00, 3 books
--   All: total 118.25 / 9 books = 13.138...
-- Oscar (1002) invited Quentin.
--   Quentin: 13.25, 9.50, 12.00 = 34.75 / 3 = 11.583...
-- Top 5 by avg payment per book: Nina first, Oscar second.
-- (Only 2 inviters exist in the sample data.)
-- (1001, 'Nina', 13.138888888888889)
-- (1002, 'Oscar', 11.583333333333334)

-- Talk-track follow-ups
-- ---------------------
-- "What if someone was invited by multiple inviters?"
--   -> Their transactions would count toward each inviter. The query
--      above handles that automatically.
-- "What if an inviter invited no one?"
--   -> They don't appear in the join result — that's correct.
