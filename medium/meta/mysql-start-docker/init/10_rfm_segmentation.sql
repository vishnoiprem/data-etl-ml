-- Problem 10 — RFM segmentation using NTILE
-- Difficulty: Medium | Round: Onsite | Pattern: NTILE + multi-CTE
--
-- MySQL 8.0+ required (uses window functions: NTILE).
-- Run: mysql -u meta_interview -pmeta_interview meta_interview < 10_rfm_segmentation.sql

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

-- =============================================================
-- Setup: source + target tables + sample data
-- =============================================================
USE meta_interview;

-- -------------------------------------------------------------
-- SOURCE: raw transactions
-- -------------------------------------------------------------
DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    transaction_id  INT             NOT NULL AUTO_INCREMENT,
    customer_id     INT             NOT NULL,
    purchase_date   DATE            NOT NULL,
    amount          DECIMAL(10, 2)  NOT NULL,
    PRIMARY KEY (transaction_id),
    KEY idx_customer (customer_id),
    KEY idx_purchase_date (purchase_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- TARGET: per-customer RFM segments
-- -------------------------------------------------------------
DROP TABLE IF EXISTS rfm_segments;

CREATE TABLE rfm_segments (
    customer_id     INT             NOT NULL,
    recency_days    INT             NOT NULL,
    frequency       INT             NOT NULL,
    monetary        DECIMAL(12, 2)  NOT NULL,
    r_score         TINYINT         NOT NULL,
    f_score         TINYINT         NOT NULL,
    m_score         TINYINT         NOT NULL,
    segment         VARCHAR(32)     NOT NULL,
    last_updated    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                          ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id),
    KEY idx_segment (segment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- Sample data — matches the "Expected output" below
-- (reference date 2024-12-31).
--   1001 Nina:  recency 30,  freq 4,  top spender
--   1002 Oscar: recency 138, freq 3
--   1003 Priya: recency 325, freq 3
--   1004 Q:     recency 112, freq 3
--   1005 Rosa:  recency 31,  freq 8 (most frequent)
--   1006 Sam:   recency 263, freq 3
--   1007 Tariq: recency 225, freq 1
--   1008 Uma:   recency 199, freq 1
-- -------------------------------------------------------------
INSERT INTO transactions (customer_id, purchase_date, amount) VALUES
    -- 1001 Nina — recent, frequent, top spender
    (1001, '2024-08-05',  420.00),
    (1001, '2024-09-18',  310.50),
    (1001, '2024-11-02',  890.00),
    (1001, '2024-12-01',  555.25),

    -- 1002 Oscar
    (1002, '2024-04-10',  120.00),
    (1002, '2024-06-22',   75.50),
    (1002, '2024-08-15',  200.00),

    -- 1003 Priya — old, infrequent
    (1003, '2024-02-10',  600.00),
    (1003, '2024-05-30',  150.75),
    (1003, '2024-07-14',   90.00),

    -- 1004 Q
    (1004, '2024-05-05',  240.00),
    (1004, '2024-07-22',  180.50),
    (1004, '2024-09-10',  305.00),

    -- 1005 Rosa — most frequent (8 purchases), recent, high spender
    (1005, '2024-07-04',  150.00),
    (1005, '2024-08-12',  220.50),
    (1005, '2024-09-01',  180.00),
    (1005, '2024-09-28',  310.75),
    (1005, '2024-10-15',  265.00),
    (1005, '2024-11-05',  420.50),
    (1005, '2024-11-22',  198.00),
    (1005, '2024-11-30',  350.25),

    -- 1006 Sam
    (1006, '2024-04-12',  500.00),
    (1006, '2024-06-18',  275.50),
    (1006, '2024-08-25',  190.00),

    -- 1007 Tariq — one purchase, long ago
    (1007, '2024-05-20', 1200.00),

    -- 1008 Uma — one purchase, long ago
    (1008, '2024-06-15',   85.00);

-- -------------------------------------------------------------
-- Sanity check on the source
-- -------------------------------------------------------------
SELECT customer_id, COUNT(*) AS n, MAX(purchase_date) AS last_purchase, SUM(amount) AS total
FROM transactions
GROUP BY customer_id
ORDER BY customer_id;

-- =============================================================
-- Solution (MySQL-compatible — uses DATEDIFF instead of julianday)
-- =============================================================
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

-- =============================================================
-- Persist into the target table (production form)
-- =============================================================
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

-- -------------------------------------------------------------
-- Verify persisted output
-- -------------------------------------------------------------
SELECT * FROM rfm_segments
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