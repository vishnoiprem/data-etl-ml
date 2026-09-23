-- Problem 10 — RFM segmentation using NTILE
-- Difficulty: Medium | Round: Onsite | Pattern: NTILE + multi-CTE

-- Goal
-- ----
-- Classic RFM (Recency, Frequency, Monetary) segmentation:
--   * Recency  = days since last purchase (lower = better)
--   * Frequency = total number of purchases
--   * Monetary  = total spend
-- Bucket each into 4 quantile buckets via NTILE(4), then label customers
-- 'Champions' (top freq + top monetary + recent), 'At Risk' (low freq
-- + high recency), etc.

-- Interview script
-- ----------------
-- "RFM is the standard marketing question. The mechanic is three
--  aggregates per customer, then NTILE on each. Combining the buckets
--  into a label is a CASE expression. I'll use three CTEs — one for
--  raw metrics, one for bucketed scores, one for labeling."

-- Solution (MySQL-compatible — uses DATEDIFF instead of julianday)
-- --------
WITH metrics AS (
    SELECT
        customer_id,
        DATEDIFF('2024-12-31', MAX(purchase_date)) AS recency_days,
        COUNT(*)                                   AS frequency,
        SUM(amount)                                AS monetary
    FROM transactions
    GROUP BY customer_id
),
bucketed AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        NTILE(4) OVER (ORDER BY recency_days ASC) AS r_score,  -- lower recency = higher score
        NTILE(4) OVER (ORDER BY frequency   DESC) AS f_score,  -- higher freq = higher score
        NTILE(4) OVER (ORDER BY monetary    DESC) AS m_score
    FROM metrics
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    CASE
        WHEN r_score = 4 AND f_score = 4    THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3  THEN 'Loyal'
        WHEN r_score >= 3 AND f_score <= 2  THEN 'Potential Loyalists'
        WHEN r_score <= 2 AND f_score >= 3  THEN 'At Risk'
        WHEN r_score = 1                    THEN 'Hibernating'
        ELSE                                     'Other'
    END AS segment
FROM bucketed
ORDER BY r_score DESC, f_score DESC, m_score DESC, customer_id;

-- Expected output (against schema.sql sample data, last_day=2024-12-31)
-- ---------------------------------------------------------------------
-- Recency as of 2024-12-31:
--   1001 Nina:  2024-12-01 -> 30 days ago
--   1002 Oscar: 2024-08-15 -> 138 days ago
--   1003 Priya: 2024-02-10 -> 325 days ago
--   1004 Q:     2024-09-10 -> 112 days ago
--   1005 Rosa:  2024-11-30 -> 31 days ago
--   1006 Sam:   2024-04-12 -> 263 days ago
--   1007 Tariq: 2024-05-20 -> 225 days ago
--   1008 Uma:   2024-06-15 -> 199 days ago
-- Frequency: Rosa 8, Nina 4, Q/Oscar/Sam/Priya 3, Tariq/Uma 1
-- Monetary: Nina highest, then Rosa, etc.
--
-- Exact segment assignments vary with NTILE bucket boundaries; what
-- matters is the SHAPE: top spenders who bought recently are Champions.
--
-- Talk-track follow-ups
-- ---------------------
-- "What's the difference between NTILE and PERCENT_RANK?"
--   -> NTILE assigns equal-sized groups (4 each for NTILE(4)).
--      PERCENT_RANK gives a 0..1 percentile rank — useful for
--      continuous scores.
-- "Why reverse the order for recency?"
--   -> Lower recency_days is better. ASC means the smallest value gets
--      bucket 1 — but I want the SMALLEST recency_days (most recent) to
--      get the HIGHEST r_score. So I order ASC and the bucket number
--      lines up with recency descending. This is the convention.
--
-- =============================================================
-- Schema (MySQL) + sample data — make this file self-contained.
-- Run on its own: mysql -u meta_interview -pmeta_interview meta_interview < 10_rfm_segmentation.sql
-- =============================================================
-- USE meta_interview;
--
-- DROP TABLE IF EXISTS rfm_segments;
-- DROP TABLE IF EXISTS transactions;
-- DROP TABLE IF EXISTS invitations;
-- DROP TABLE IF EXISTS payment_types;
-- DROP TABLE IF EXISTS customers;
-- DROP TABLE IF EXISTS books;
-- DROP TABLE IF EXISTS authors;
--
 CREATE TABLE authors (
     author_id   INT          NOT NULL,
     name        VARCHAR(100) NOT NULL,
     website_url VARCHAR(255) NULL,
     PRIMARY KEY (author_id)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

 CREATE TABLE books (
     book_id   INT            NOT NULL,
     author_id INT            NOT NULL,
     title     VARCHAR(255)   NOT NULL,
     price     DECIMAL(10, 2) NOT NULL,
     PRIMARY KEY (book_id),
     KEY idx_author (author_id)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

 CREATE TABLE customers (
     customer_id   INT          NOT NULL,
     name          VARCHAR(100) NOT NULL,
     registered_on DATE         NOT NULL,
     invited_by    INT          NULL,
     PRIMARY KEY (customer_id),
     KEY idx_invited_by (invited_by)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

 CREATE TABLE payment_types (
     payment_type_id INT          NOT NULL,
     name            VARCHAR(50)  NOT NULL,
     PRIMARY KEY (payment_type_id)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

 CREATE TABLE transactions (
     transaction_id  INT            NOT NULL,
     customer_id     INT            NOT NULL,
     book_id         INT            NOT NULL,
     payment_type_id INT            NOT NULL,
     purchase_date   DATE           NOT NULL,
     amount          DECIMAL(10, 2) NOT NULL,
     PRIMARY KEY (transaction_id),
     KEY idx_customer (customer_id),
     KEY idx_book (book_id),
     KEY idx_payment (payment_type_id),
     KEY idx_purchase_date (purchase_date)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

 CREATE TABLE invitations (
     inviter_id INT NOT NULL,
     invitee_id INT NOT NULL,
     PRIMARY KEY (inviter_id, invitee_id),
     KEY idx_invitee (invitee_id)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

 CREATE TABLE rfm_segments (
     customer_id     INT            NOT NULL,
     recency_days    INT            NOT NULL,
     frequency       INT            NOT NULL,
     monetary        DECIMAL(12, 2) NOT NULL,
     r_score         TINYINT        NOT NULL,
     f_score         TINYINT        NOT NULL,
     m_score         TINYINT        NOT NULL,
     segment         VARCHAR(32)    NOT NULL,
     last_updated    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                            ON UPDATE CURRENT_TIMESTAMP,
     PRIMARY KEY (customer_id),
     KEY idx_segment (segment)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

 INSERT INTO authors (author_id, name, website_url) VALUES
     (1, 'Alice Walker',    'https://alice.com'),
     (2, 'Brandon Kim',     'https://kim.io'),
     (3, 'Carla Diaz',      NULL),
     (4, 'Dmitri Volkov',   'volkov.net'),
     (5, 'Esha Patel',      'esha.com/about'),
     (6, 'Feng Liu',        NULL);

 INSERT INTO books (book_id, author_id, title, price) VALUES
     (101, 1, 'The Color Book',     12.50),
     (102, 1, 'Walking Tales',       9.99),
     (103, 1, 'Color Theory',       15.00),
     (104, 1, 'Sunrise Stories',    11.25),
     (105, 1, 'Letters Home',       8.00),
     (106, 1, 'Garden Essays',      14.75),
     (107, 2, 'Kim Recipes',        22.00),
     (108, 3, 'Diaz Diaries',        7.50),
     (109, 4, 'Volkov Voyages',     18.00),
     (110, 5, 'Patel Poems',        10.00),
     (111, 5, 'Indian Sunsets',     13.25),
     (112, 5, 'Monsoon Verses',      9.50),
     (113, 5, 'Spice Markets',      12.00),
     (114, 5, 'Temple Bells',       16.50),
     (115, 6, 'Liu Letters',         8.75);

 INSERT INTO payment_types (payment_type_id, name) VALUES
     (1, 'credit_card'),
     (2, 'paypal'),
     (3, 'gift_card');

 INSERT INTO customers (customer_id, name, registered_on, invited_by) VALUES
     (1001, 'Nina',    '2024-01-15', NULL),
     (1002, 'Oscar',   '2024-02-01', 1001),
     (1003, 'Priya',   '2024-02-10', 1001),
     (1004, 'Quentin', '2024-03-05', 1002),
     (1005, 'Rosa',    '2024-04-12', NULL),
     (1006, 'Sam',     '2024-04-12', NULL),
     (1007, 'Tariq',   '2024-05-20', 1003),
     (1008, 'Uma',     '2024-06-01', 1001);

 INSERT INTO transactions (transaction_id, customer_id, book_id, payment_type_id, purchase_date, amount) VALUES
     (1,  1001, 101, 1, '2024-03-01', 12.50),
     (2,  1001, 102, 1, '2024-03-01',  9.99),
     (3,  1001, 103, 1, '2024-06-15', 15.00),
     (4,  1001, 104, 1, '2024-12-01', 11.25),
     (5,  1002, 105, 2, '2024-02-01',  8.00),
     (6,  1002, 106, 2, '2024-02-01', 14.75),
     (7,  1002, 107, 2, '2024-08-15', 22.00),
     (8,  1003, 108, 1, '2024-02-10',  7.50),
     (9,  1003, 109, 1, '2024-02-10', 18.00),
     (10, 1003, 110, 1, '2024-02-10', 10.00),
     (11, 1004, 111, 3, '2024-03-15', 13.25),
     (12, 1004, 112, 3, '2024-07-20',  9.50),
     (13, 1004, 113, 3, '2024-09-10', 12.00),
     (14, 1005, 114, 1, '2024-04-15', 16.50),
     (15, 1005, 101, 1, '2024-04-15', 12.50),
     (16, 1005, 102, 1, '2024-04-15',  9.99),
     (17, 1005, 103, 1, '2024-04-15', 15.00),
     (18, 1005, 104, 1, '2024-11-30', 11.25),
     (19, 1005, 105, 1, '2024-11-30',  8.00),
     (20, 1005, 106, 1, '2024-11-30', 14.75),
     (21, 1005, 107, 1, '2024-11-30', 22.00),
     (22, 1006, 108, 2, '2024-04-12',  7.50),
     (23, 1006, 109, 2, '2024-04-12', 18.00),
     (24, 1006, 110, 2, '2024-04-12', 10.00),
     (25, 1007, 111, 1, '2024-05-20', 13.25),
     (26, 1008, 112, 1, '2024-06-15',  9.50),
     (27, 1008, 113, 1, '2024-06-15', 12.00),
     (28, 1008, 114, 1, '2024-06-15', 16.50);

 INSERT INTO invitations (inviter_id, invitee_id) VALUES
     (1001, 1002),
     (1001, 1003),
     (1001, 1008),
     (1002, 1004);
--
  Persist the RFM segments into the target table (production form):
  TRUNCATE TABLE rfm_segments;
  INSERT INTO rfm_segments
      (customer_id, recency_days, frequency, monetary,
       r_score, f_score, m_score, segment)
  WITH metrics AS (
      SELECT
          customer_id,
          DATEDIFF('2024-12-31', MAX(purchase_date)) AS recency_days,
          COUNT(*)                                   AS frequency,
          SUM(amount)                                AS monetary
      FROM transactions
      GROUP BY customer_id
  ),
  bucketed AS (
      SELECT
          customer_id,
          recency_days,
          frequency,
          monetary,
          NTILE(4) OVER (ORDER BY recency_days ASC) AS r_score,
          NTILE(4) OVER (ORDER BY frequency   DESC) AS f_score,
          NTILE(4) OVER (ORDER BY monetary    DESC) AS m_score
      FROM metrics
  )
  SELECT
      customer_id,
      recency_days,
      frequency,
      monetary,
      r_score,
      f_score,
      m_score,
      CASE
          WHEN r_score = 4 AND f_score = 4    THEN 'Champions'
          WHEN r_score >= 3 AND f_score >= 3  THEN 'Loyal'
          WHEN r_score >= 3 AND f_score <= 2  THEN 'Potential Loyalists'
          WHEN r_score <= 2 AND f_score >= 3  THEN 'At Risk'
          WHEN r_score = 1                    THEN 'Hibernating'
          ELSE                                     'Other'
      END AS segment
  FROM bucketed;
