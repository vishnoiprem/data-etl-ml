-- Problem 5 — Total authors, % with .com URL, % never made a sale
-- Difficulty: Easy-Medium | Round: Screening | Pattern: multiple aggregates in one pass

-- Goal
-- ----
-- Three numbers, one row:
--   1) Total number of authors
--   2) Percentage of authors whose website_url contains ".com"
--   3) Percentage of authors who have ZERO transactions on any of their books

-- Interview script
-- ----------------
-- "Two independent boolean conditions on authors. The cleanest pattern is
--  one CTE that flags each author, then a single SELECT aggregating
--  counts. LIKE '%\.com%' is portable; I'd note the ESCAPE clause for
--  hygiene. The 'never made a sale' check needs an anti-join: an author
--  whose books appear in NO transaction."

-- Solution
-- --------
WITH author_flags AS (
    SELECT
        a.author_id,
        CASE WHEN a.website_url LIKE '%.com%'           THEN 1 ELSE 0 END AS has_com_url,
        CASE WHEN NOT EXISTS (
            SELECT 1
            FROM books      AS b
            JOIN transactions AS t ON t.book_id = b.book_id
            WHERE b.author_id = a.author_id
        )                                                  THEN 1 ELSE 0 END AS no_sale
    FROM authors AS a
)
SELECT
    COUNT(*)                                           AS total_authors,
    100.0 * SUM(has_com_url) / NULLIF(COUNT(*), 0)     AS pct_with_com_url,
    100.0 * SUM(no_sale)      / NULLIF(COUNT(*), 0)     AS pct_no_sale
FROM author_flags;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- Authors (6 total): Alice, Brandon, Carla, Dmitri, Esha, Feng.
-- .com URLs: Alice (alice.com YES), Brandon (kim.io NO), Carla (NULL NO),
--   Dmitri (volkov.net NO), Esha (esha.com YES), Feng (NULL NO).
--   -> 2 of 6 = 33.33%
-- No sales: Feng's book 115 is never bought; every other author has at
--   least one book that appears in transactions.
--   -> 1 of 6 = 16.67%
-- (6, 33.33, 16.67)
--
-- Talk-track follow-ups
-- ---------------------
-- "What if URL has 'COM' (uppercase)?"
--   -> LIKE is case-insensitive for ASCII in SQLite and in MySQL (default
--      collation); in Postgres use ILIKE or LOWER(website_url) LIKE ...
-- "What if the URL contains a path like '/about.com'?"
--   -> '.' is a literal character in LIKE (only % and _ are wildcards),
--      so '/about.com' WOULD match. Be honest about this in the interview.

-- =============================================================
-- Schema (MySQL) + sample data — make this file self-contained.
-- Run on its own: mysql -u meta_interview -pmeta_interview meta_interview < 5_authors_website_and_no_sale.sql
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
--     (1, 'Alice Walker',    'https://alice.com'),  -- has .com
--     (2, 'Brandon Kim',     'https://kim.io'),
--     (3, 'Carla Diaz',      NULL),
--     (4, 'Dmitri Volkov',   'volkov.net'),
--     (5, 'Esha Patel',      'esha.com/about'),    -- has .com
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
--     (115, 6, 'Liu Letters',         8.75);  -- Feng: never appears in transactions
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
-- -- Note: book 115 (Feng Liu) is intentionally NEVER referenced below,
-- -- so Feng contributes to the "never made a sale" bucket.
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
