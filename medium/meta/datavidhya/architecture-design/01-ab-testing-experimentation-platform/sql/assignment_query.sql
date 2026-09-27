-- =====================================================================
-- Deterministic Assignment Query
--
-- Concept:
--   bucket = hash(user_id || experiment_id || salt) % 10000
--   if bucket >= traffic_allocation * 10000 -> user is NOT in experiment
--   else variant = variants[ hash(user_id || experiment_id || variant_salt) % N ]
--
-- We use SHA-256 for cross-language determinism (Python, Java, JS, SQL).
-- =====================================================================

-- 1) Hash function (Spark SQL / Trino compatible)
-- For Trino: use xxhash64 or sha256; for Spark use sha2.
-- Below is the Snowflake/Trino syntax. Adapt to your engine.

WITH user_bucket AS (
    SELECT
        'user_12345' AS user_id,
        'exp_feed_rank_2024q4' AS experiment_id,
        (
            to_number(
                substr(
                    sha2(user_id || ':' || experiment_id || ':layer1', 256),
                    1, 8
                ),
                'XXXXXXXX'
            ) % 10000
        ) / 10000.0 AS bucket
)
SELECT
    user_id,
    experiment_id,
    bucket,
    CASE
        WHEN bucket < 0.50 THEN 'control'
        WHEN bucket < 0.75 THEN 'variant_a'
        ELSE 'variant_b'
    END AS variant_id
FROM user_bucket;
