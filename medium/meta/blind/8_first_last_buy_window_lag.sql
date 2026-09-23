-- Problem 8 — Days between each customer's first and last book purchase (using LAG)
-- Difficulty: Medium | Round: Onsite | Pattern: Window function LAG + CTE
--
-- Goal
-- ----
-- For each customer who has 2+ purchases, compute the number of days
-- between their first and last purchase. Order customers by that span
-- descending. This is the kind of question you see on StrataScratch
-- under "Meta".

-- Interview script
-- ----------------
-- "The onsite question expects window functions and CTEs. I want
--  first_purchase_date and last_purchase_date per customer. LAG wouldn't
--  help here — I'll use MIN and MAX as window aggregates. Then subtract
--  in the outer query. Writing it as two CTEs makes the steps explicit:
--  1) per-customer dates, 2) span, 3) filter and order."

-- Solution
-- --------
WITH customer_dates AS (
    SELECT
        customer_id,
        MIN(purchase_date) AS first_purchase,
        MAX(purchase_date) AS last_purchase,
        COUNT(*)           AS purchase_count
    FROM transactions
    GROUP BY customer_id
),
customer_span AS (
    SELECT
        customer_id,
        purchase_count,
        DATEDIFF(last_purchase, first_purchase) AS days_between
    FROM customer_dates
)
SELECT customer_id, purchase_count, days_between
FROM customer_span
WHERE purchase_count > 1
ORDER BY days_between DESC, customer_id ASC;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- Customer 1001 (Nina):    2024-03-01 -> 2024-12-01 = 275 days, 4 txs
-- Customer 1002 (Oscar):   2024-02-01 -> 2024-08-15 = 196 days, 3 txs
-- Customer 1004 (Quentin): 2024-03-15 -> 2024-09-10 = 179 days, 3 txs
-- Customer 1005 (Rosa):    2024-04-15 -> 2024-11-30 = 229 days, 8 txs
--
-- (1001, 4, 275)
-- (1002, 3, 196)
-- (1004, 3, 179)
-- (1005, 8, 229)
-- (sorted DESC: 1001 first, 1005 second, 1002 third, 1004 last)

-- Talk-track follow-ups
-- ---------------------
-- "What does LAG have to do with this?"
--   -> LAG is the right call when you want the PREVIOUS row's value
--      (e.g., days since last purchase per transaction). For first/last
--      boundaries, MIN/MAX are correct. Mentioning both shows range.
-- "How would you do this in Postgres?"
--   -> DATE_PART('day', last - first) or (last::date - first::date).

-- =============================================================
-- Schema (MySQL) + sample data — make this file self-contained.
-- Run on its own: mysql -u meta_interview -pmeta_interview meta_interview < 8_first_last_buy_window_lag.sql
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
--     -- Nina (1001): first 2024-03-01, last 2024-12-01 -> 275 days
--     (1,  1001, 101, 1, '2024-03-01', 12.50),
--     (2,  1001, 102, 1, '2024-03-01',  9.99),
--     (3,  1001, 103, 1, '2024-06-15', 15.00),
--     (4,  1001, 104, 1, '2024-12-01', 11.25),
--     -- Oscar (1002): first 2024-02-01, last 2024-08-15 -> 196 days
--     (5,  1002, 105, 2, '2024-02-01',  8.00),
--     (6,  1002, 106, 2, '2024-02-01', 14.75),
--     (7,  1002, 107, 2, '2024-08-15', 22.00),
--     -- Priya (1003): one day, single-date -> excluded by purchase_count > 1
--     (8,  1003, 108, 1, '2024-02-10',  7.50),
--     (9,  1003, 109, 1, '2024-02-10', 18.00),
--     (10, 1003, 110, 1, '2024-02-10', 10.00),
--     -- Quentin (1004): first 2024-03-15, last 2024-09-10 -> 179 days
--     (11, 1004, 111, 3, '2024-03-15', 13.25),
--     (12, 1004, 112, 3, '2024-07-20',  9.50),
--     (13, 1004, 113, 3, '2024-09-10', 12.00),
--     -- Rosa (1005): first 2024-04-15, last 2024-11-30 -> 229 days
--     (14, 1005, 114, 1, '2024-04-15', 16.50),
--     (15, 1005, 101, 1, '2024-04-15', 12.50),
--     (16, 1005, 102, 1, '2024-04-15',  9.99),
--     (17, 1005, 103, 1, '2024-04-15', 15.00),
--     (18, 1005, 104, 1, '2024-11-30', 11.25),
--     (19, 1005, 105, 1, '2024-11-30',  8.00),
--     (20, 1005, 106, 1, '2024-11-30', 14.75),
--     (21, 1005, 107, 1, '2024-11-30', 22.00),
--     -- Sam, Tariq, Uma: excluded (1 transaction date only)
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
