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

-- Solution
-- --------
WITH metrics AS (
    SELECT
        customer_id,
        CAST(julianday('2024-12-31') - julianday(MAX(purchase_date)) AS INTEGER) AS recency_days,
        COUNT(*)                                                                AS frequency,
        SUM(amount)                                                             AS monetary
    FROM transactions
    GROUP BY customer_id
),
bucketed AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        NTILE(4) OVER (ORDER BY recency_days ASC)    AS r_score,  -- lower recency = higher score
        NTILE(4) OVER (ORDER BY frequency DESC)      AS f_score,  -- higher freq = higher score
        NTILE(4) OVER (ORDER BY monetary DESC)       AS m_score
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
        WHEN r_score = 4 AND f_score = 4                THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3              THEN 'Loyal'
        WHEN r_score >= 3 AND f_score <= 2              THEN 'Potential Loyalists'
        WHEN r_score <= 2 AND f_score >= 3              THEN 'At Risk'
        WHEN r_score = 1                                THEN 'Hibernating'
        ELSE                                            'Other'
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
