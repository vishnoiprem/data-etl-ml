-- Problem 9 — Running total of sales by date, with a 7-day rolling count of customers
-- Difficulty: Medium-Hard | Round: Onsite | Pattern: Window function SUM OVER + CTE

-- Goal
-- ----
-- For each calendar day with transactions, return:
--   * purchase_date
--   * daily_sales (SUM of amount that day)
--   * running_total_sales (cumulative SUM to date)
--   * rolling_7d_unique_customers (distinct customer count over the last 7 days)

-- Interview script
-- ----------------
-- "The onsite question expects at least one window function. SUM OVER
--  (ORDER BY date) gives running total trivially. The rolling distinct-
--  customer count is harder, for two reasons:
--   1) COUNT(DISTINCT ...) is not allowed inside a window function, and
--      summing DAILY distinct counts double-counts a customer who buys
--      on two days of the same week.
--   2) ROWS BETWEEN 6 PRECEDING means the last 7 ROWS (dates that had
--      sales), not the last 7 CALENDAR days.
--  So I self-join each day to the transactions from the 7 days ending
--  that day and COUNT(DISTINCT customer_id)."

-- Solution
-- --------
WITH daily AS (
    SELECT
        purchase_date,
        SUM(amount) AS daily_sales
    FROM transactions
    GROUP BY purchase_date
),
rolling_customers AS (
    -- Each sales day joined to every transaction in the 7 calendar days
    -- ending that day (day-6 .. day), then a true DISTINCT count.
    SELECT
        d.purchase_date,
        COUNT(DISTINCT t.customer_id) AS rolling_7d_unique_customers
    FROM daily AS d
    JOIN transactions AS t
      ON DATEDIFF(d.purchase_date, t.purchase_date) BETWEEN 0 AND 6
    GROUP BY d.purchase_date
)
SELECT
    d.purchase_date,
    ROUND(d.daily_sales, 2) AS daily_sales,
    ROUND(SUM(d.daily_sales) OVER (ORDER BY d.purchase_date
                                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_total_sales,
    r.rolling_7d_unique_customers
FROM daily AS d
JOIN rolling_customers AS r ON r.purchase_date = d.purchase_date
ORDER BY d.purchase_date;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- Sales days are weeks apart, so most 7-day windows hold 1 customer.
-- 2024-04-15: window 04-09..04-15 has Sam (04-12) + Rosa (04-15) -> 2
-- 2024-06-15: Nina and Uma both bought that day -> 2
-- 2024-12-01: window 11-25..12-01 has Rosa (11-30) + Nina (12-01) -> 2
-- ('2024-02-01', 22.75, 22.75, 1)
-- ('2024-02-10', 35.5, 58.25, 1)
-- ('2024-03-01', 22.49, 80.74, 1)
-- ('2024-03-15', 13.25, 93.99, 1)
-- ('2024-04-12', 35.5, 129.49, 1)
-- ('2024-04-15', 53.99, 183.48, 2)
-- ('2024-05-20', 13.25, 196.73, 1)
-- ('2024-06-15', 53.0, 249.73, 2)
-- ('2024-07-20', 9.5, 259.23, 1)
-- ('2024-08-15', 22.0, 281.23, 1)
-- ('2024-09-10', 12.0, 293.23, 1)
-- ('2024-11-30', 56.0, 349.23, 1)
-- ('2024-12-01', 11.25, 360.48, 2)
--
-- Talk-track follow-ups
-- ---------------------
-- "Why not SUM(...) OVER (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)?"
--   -> ROWS counts rows, not days: with gaps between sales days, 7 rows
--      can span months. Use RANGE BETWEEN INTERVAL 6 DAY PRECEDING
--      (Postgres/MySQL 8) for a true day window on sums — but distinct
--      counts still need the self-join above.
-- "What if you need a row for EVERY calendar day, even with no sales?"
--   -> Build a calendar (date spine) CTE first and LEFT JOIN onto it.
-- "Could you do monthly running totals instead?"
--   -> Use strftime('%Y-%m', purchase_date) for grouping; same SUM OVER.

-- =============================================================
-- Schema (MySQL) + sample data — make this file self-contained.
-- Run on its own: mysql -u meta_interview -pmeta_interview meta_interview < 9_running_total_sales_cte.sql
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
--     (8,  1003, 108, 1, '2024-02-10',  7.50),
--     (9,  1003, 109, 1, '2024-02-10', 18.00),
--     (10, 1003, 110, 1, '2024-02-10', 10.00),
--     (11, 1004, 111, 3, '2024-03-15', 13.25),
--     (12, 1004, 112, 3, '2024-07-20',  9.50),
--     (13, 1004, 113, 3, '2024-09-10', 12.00),
--     (14, 1005, 114, 1, '2024-04-15', 16.50),
--     (15, 1005, 101, 1, '2024-04-15', 12.50),
--     (16, 1005, 102, 1, '2024-04-15',  9.99),
--     (17, 1005, 103, 1, '2024-04-15', 15.00),
--     (18, 1005, 104, 1, '2024-11-30', 11.25),
--     (19, 1005, 105, 1, '2024-11-30',  8.00),
--     (20, 1005, 106, 1, '2024-11-30', 14.75),
--     (21, 1005, 107, 1, '2024-11-30', 22.00),
--     (22, 1006, 108, 2, '2024-04-12',  7.50),
--     (23, 1006, 109, 2, '2024-04-12', 18.00),
--     (24, 1006, 110, 2, '2024-04-12', 10.00),
--     (25, 1007, 111, 1, '2024-05-20', 13.25),
--     (26, 1008, 112, 1, '2024-06-15',  9.50),
--     (27, 1008, 113, 1, '2024-06-15', 12.00),
--     (28, 1008, 114, 1, '2024-06-15', 16.50);
--
-- INSERT INTO invitations (inviter_id, invitee_id) VALUES
--     (1001, 1002),
--     (1001, 1003),
--     (1001, 1008),
--     (1002, 1004);
