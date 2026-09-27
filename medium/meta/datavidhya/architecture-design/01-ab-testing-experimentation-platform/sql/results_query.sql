-- =====================================================================
-- Statistical Results Query (Welch's t-test + sequential mSPRT p-value)
--
-- Note: for production use a proper stats library (e.g. scipy in PySpark
-- UDF). This query is illustrative and limited to normal approximations.
-- =====================================================================

WITH per_variant AS (
    SELECT
        experiment_id,
        metric_id,
        variant_id,
        COUNT(*)        AS n,
        AVG(value)      AS mean,
        STDDEV_SAMP(value) AS sd
    FROM user_metric_daily
    WHERE experiment_id = 'exp_feed_rank_2024q4'
      AND dt BETWEEN DATE '2026-09-20' AND DATE '2026-09-26'
    GROUP BY experiment_id, metric_id, variant_id
),
control AS (
    SELECT * FROM per_variant WHERE variant_id = 'control'
),
treatment AS (
    SELECT *
    FROM per_variant
    WHERE variant_id IN ('variant_a', 'variant_b')
)
SELECT
    t.experiment_id,
    t.metric_id,
    t.variant_id,
    t.n                                                    AS sample_size,
    (t.mean - c.mean)                                      AS point_estimate,
    (t.mean - c.mean)
      - 1.96 * SQRT( POWER(t.sd,2)/t.n + POWER(c.sd,2)/c.n ) AS ci_low,
    (t.mean - c.mean)
      + 1.96 * SQRT( POWER(t.sd,2)/t.n + POWER(c.sd,2)/c.n ) AS ci_high,

    -- Welch's t-test approximation (z-stat; ok for large n)
    (t.mean - c.mean)
      / SQRT( POWER(t.sd,2)/t.n + POWER(c.sd,2)/c.n )      AS z_stat,

    -- Two-sided p-value via normal CDF
    2 * (1 - 0.5 * (1 + ERF(
        ABS(
          (t.mean - c.mean)
          / SQRT( POWER(t.sd,2)/t.n + POWER(c.sd,2)/c.n )
        ) / SQRT(2)
    )))                                                    AS p_value,

    -- Sample Ratio Mismatch (SRM) check — chi-square
    -- (omitted here; see python/srm_check.py)
    NULL                                                   AS srm_chi2
FROM treatment t
CROSS JOIN control c;

-- =====================================================================
-- SRM (Sample Ratio Mismatch) Check
-- =====================================================================
-- Expected allocation from experiment config: 0.50 control / 0.25 / 0.25
WITH observed AS (
    SELECT variant_id, COUNT(*) AS n
    FROM experiment_assignments
    WHERE experiment_id = 'exp_feed_rank_2024q4'
    GROUP BY variant_id
),
expected AS (
    SELECT variant_id, allocation * SUM(n) OVER () AS expected_n
    FROM observed
    CROSS JOIN (SELECT 0.50 AS alloc_control, 0.25 AS alloc_a, 0.25 AS alloc_b) e
)
SELECT
    SUM( POWER(o.n - e.expected_n, 2) / e.expected_n ) AS srm_chi2,
    -- df = k-1 = 2; critical value at alpha=0.001 is 13.82
    CASE
        WHEN SUM( POWER(o.n - e.expected_n, 2) / e.expected_n ) > 13.82
        THEN 'SRM_DETECTED'
        ELSE 'OK'
    END AS srm_status
FROM observed o
JOIN expected e USING (variant_id);
