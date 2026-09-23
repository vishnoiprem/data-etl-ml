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

-- =============================================================
-- Schema (MySQL) + sample data — make this file self-contained.
-- Run on its own: mysql -u meta_interview -pmeta_interview meta_interview < 4_top5_invitee_payment.sql
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
