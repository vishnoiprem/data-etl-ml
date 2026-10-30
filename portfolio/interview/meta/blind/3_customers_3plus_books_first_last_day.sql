-- Problem 3 — Customers buying 3+ books on BOTH first and last day, excluding one-tx customers
-- Difficulty: Medium | Round: Screening | Pattern: per-day aggregation + HAVING + EXCEPT-style exclusion

-- Goal
-- ----
-- Find customers such that:
--   * They have >= 3 books on their FIRST purchase date
--   * AND >= 3 books on their LAST purchase date
--   * AND their first and last purchase dates are DIFFERENT days
--
-- "Excluding those with only one transaction" — each row in
-- `transactions` is ONE book, so a customer who bought 3 books in one
-- visit has 3 rows. Counting rows would let one-visit customers through
-- (first day == last day). The question only makes sense if first and
-- last are different visits, so: COUNT(DISTINCT purchase_date) > 1.
-- State this interpretation out loud before writing the SQL.

-- Interview script
-- ----------------
-- "I need per-customer aggregates of book counts on two specific dates.
--  The first date is min(purchase_date); the last date is max(purchase_date).
--  I'll compute three columns: books_on_first_day, books_on_last_day,
--  active_days. Rows are books, not visits, so 'more than one
--  transaction' means active_days > 1. Aggregate once per customer."

-- Solution
-- --------
WITH tx_with_bounds AS (
    SELECT
        customer_id,
        purchase_date,
        MIN(purchase_date) OVER (PARTITION BY customer_id) AS first_day,
        MAX(purchase_date) OVER (PARTITION BY customer_id) AS last_day
    FROM transactions
),
per_customer AS (
    SELECT
        customer_id,
        COUNT(DISTINCT purchase_date) AS active_days,
        SUM(CASE WHEN purchase_date = first_day THEN 1 ELSE 0 END) AS books_on_first_day,
        SUM(CASE WHEN purchase_date = last_day  THEN 1 ELSE 0 END) AS books_on_last_day
    FROM tx_with_bounds
    GROUP BY customer_id
)
SELECT customer_id
FROM per_customer
WHERE active_days > 1          -- first and last purchase are different days
  AND books_on_first_day >= 3
  AND books_on_last_day  >= 3
ORDER BY customer_id;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- Rosa  (1005): 4 books on 2024-04-15 (first), 4 books on 2024-11-30 (last). QUALIFIES
-- Priya (1003), Sam (1006), Uma (1008): 3 books, but all on ONE day
--   (first == last) -> excluded by active_days > 1.
-- Nina (1001): 2 books on first day -> excluded.
-- (1005,)
--
-- Talk-track follow-ups
-- ---------------------
-- "What if first_day == last_day?"
--   -> Then books_on_first_day == books_on_last_day, and the customer
--      would trivially qualify with >= 3 books. COUNT(*) > 1 does NOT
--      catch this (3 books = 3 rows); active_days > 1 does. If the
--      interviewer says one-day buyers should count, drop that filter
--      and the answer becomes 1003, 1005, 1006, 1008.
-- "Why use window functions inside a CTE?"
--   -> To compute first_day / last_day once per customer without
--      self-joining transactions. Easier to read than two correlated
--      subqueries.

-- =============================================================
-- Schema (MySQL) + sample data — make this file self-contained.
-- Run on its own: mysql -u meta_interview -pmeta_interview meta_interview < 3_customers_3plus_books_first_last_day.sql
-- =============================================================
-- USE meta_interview;
--
-- DROP TABLE IF EXISTS transactions;
-- DROP TABLE IF EXISTS invitations;
-- DROP TABLE IF EXISTS payment_types;
-- DROP TABLE IF EXISTS customers;
-- DROP TABLE IF EXISTS books;
-- DROP TABLE IF EXISTS authors;
--
-- CREATE TABLE authors (
--     author_id   INT          NOT NULL,
--     name        VARCHAR(100) NOT NULL,
--     website_url VARCHAR(255) NULL,
--     PRIMARY KEY (author_id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
--
-- CREATE TABLE books (
--     book_id   INT            NOT NULL,
--     author_id INT            NOT NULL,
--     title     VARCHAR(255)   NOT NULL,
--     price     DECIMAL(10, 2) NOT NULL,
--     PRIMARY KEY (book_id),
--     KEY idx_author (author_id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
--
-- CREATE TABLE customers (
--     customer_id   INT          NOT NULL,
--     name          VARCHAR(100) NOT NULL,
--     registered_on DATE         NOT NULL,
--     invited_by    INT          NULL,
--     PRIMARY KEY (customer_id),
--     KEY idx_invited_by (invited_by)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
--
-- CREATE TABLE payment_types (
--     payment_type_id INT          NOT NULL,
--     name            VARCHAR(50)  NOT NULL,
--     PRIMARY KEY (payment_type_id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
--
-- CREATE TABLE transactions (
--     transaction_id  INT            NOT NULL,
--     customer_id     INT            NOT NULL,
--     book_id         INT            NOT NULL,
--     payment_type_id INT            NOT NULL,
--     purchase_date   DATE           NOT NULL,
--     amount          DECIMAL(10, 2) NOT NULL,
--     PRIMARY KEY (transaction_id),
--     KEY idx_customer (customer_id),
--     KEY idx_book (book_id),
--     KEY idx_payment (payment_type_id),
--     KEY idx_purchase_date (purchase_date)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
--
-- CREATE TABLE invitations (
--     inviter_id INT NOT NULL,
--     invitee_id INT NOT NULL,
--     PRIMARY KEY (inviter_id, invitee_id),
--     KEY idx_invitee (invitee_id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
--
-- INSERT INTO authors (author_id, name, website_url) VALUES
--     (1, 'Alice Walker',    'https://alice.com'),
--     (2, 'Brandon Kim',     'https://kim.io'),
--     (3, 'Carla Diaz',      NULL),
--     (4, 'Dmitri Volkov',   'volkov.net'),
--     (5, 'Esha Patel',      'esha.com/about'),
--     (6, 'Feng Liu',        NULL);
--
-- INSERT INTO books (book_id, author_id, title, price) VALUES
--     (101, 1, 'The Color Book',     12.50),
--     (102, 1, 'Walking Tales',       9.99),
--     (103, 1, 'Color Theory',       15.00),
--     (104, 1, 'Sunrise Stories',    11.25),
--     (105, 1, 'Letters Home',       8.00),
--     (106, 1, 'Garden Essays',      14.75),
--     (107, 2, 'Kim Recipes',        22.00),
--     (108, 3, 'Diaz Diaries',        7.50),
--     (109, 4, 'Volkov Voyages',     18.00),
--     (110, 5, 'Patel Poems',        10.00),
--     (111, 5, 'Indian Sunsets',     13.25),
--     (112, 5, 'Monsoon Verses',      9.50),
--     (113, 5, 'Spice Markets',      12.00),
--     (114, 5, 'Temple Bells',       16.50),
--     (115, 6, 'Liu Letters',         8.75);
--
-- INSERT INTO payment_types (payment_type_id, name) VALUES
--     (1, 'credit_card'),
--     (2, 'paypal'),
--     (3, 'gift_card');
--
-- INSERT INTO customers (customer_id, name, registered_on, invited_by) VALUES
--     (1001, 'Nina',    '2024-01-15', NULL),
--     (1002, 'Oscar',   '2024-02-01', 1001),
--     (1003, 'Priya',   '2024-02-10', 1001),
--     (1004, 'Quentin', '2024-03-05', 1002),
--     (1005, 'Rosa',    '2024-04-12', NULL),
--     (1006, 'Sam',     '2024-04-12', NULL),
--     (1007, 'Tariq',   '2024-05-20', 1003),
--     (1008, 'Uma',     '2024-06-01', 1001);
--
-- INSERT INTO transactions (transaction_id, customer_id, book_id, payment_type_id, purchase_date, amount) VALUES
--     (1,  1001, 101, 1, '2024-03-01', 12.50),
--     (2,  1001, 102, 1, '2024-03-01',  9.99),
--     (3,  1001, 103, 1, '2024-06-15', 15.00),
--     (4,  1001, 104, 1, '2024-12-01', 11.25),
--     (5,  1002, 105, 2, '2024-02-01',  8.00),
--     (6,  1002, 106, 2, '2024-02-01', 14.75),
--     (7,  1002, 107, 2, '2024-08-15', 22.00),
--     (8,  1003, 108, 1, '2024-02-10',  7.50),  -- Priya first/last = 2024-02-10 (3 books)
--     (9,  1003, 109, 1, '2024-02-10', 18.00),
--     (10, 1003, 110, 1, '2024-02-10', 10.00),
--     (11, 1004, 111, 3, '2024-03-15', 13.25),
--     (12, 1004, 112, 3, '2024-07-20',  9.50),
--     (13, 1004, 113, 3, '2024-09-10', 12.00),
--     (14, 1005, 114, 1, '2024-04-15', 16.50),  -- Rosa first day: 4 books
--     (15, 1005, 101, 1, '2024-04-15', 12.50),
--     (16, 1005, 102, 1, '2024-04-15',  9.99),
--     (17, 1005, 103, 1, '2024-04-15', 15.00),
--     (18, 1005, 104, 1, '2024-11-30', 11.25),  -- Rosa last day: 4 books
--     (19, 1005, 105, 1, '2024-11-30',  8.00),
--     (20, 1005, 106, 1, '2024-11-30', 14.75),
--     (21, 1005, 107, 1, '2024-11-30', 22.00),
--     (22, 1006, 108, 2, '2024-04-12',  7.50),  -- Sam first/last = 2024-04-12 (3 books)
--     (23, 1006, 109, 2, '2024-04-12', 18.00),
--     (24, 1006, 110, 2, '2024-04-12', 10.00),
--     (25, 1007, 111, 1, '2024-05-20', 13.25),  -- Tariq: 1 tx only
--     (26, 1008, 112, 1, '2024-06-15',  9.50),  -- Uma first/last = 2024-06-15 (3 books)
--     (27, 1008, 113, 1, '2024-06-15', 12.00),
--     (28, 1008, 114, 1, '2024-06-15', 16.50);
--
-- INSERT INTO invitations (inviter_id, invitee_id) VALUES
--     (1001, 1002),
--     (1001, 1003),
--     (1001, 1008),
--     (1002, 1004);
