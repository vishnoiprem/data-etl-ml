-- =====================================================================
-- Iceberg row-level DELETE patterns
-- =====================================================================

-- 1) Standard row-level delete (Iceberg rewrites affected files only)
DELETE FROM lakehouse.bronze_events
WHERE user_id = 'user_42';

-- 2) Delete across multiple tables in one workflow
DELETE FROM lakehouse.silver_events       WHERE user_id = 'user_42';
DELETE FROM lakehouse.gold_user_features_daily WHERE user_id = 'user_42';
DELETE FROM lakehouse.gold_session_metrics     WHERE user_id = 'user_42';

-- 3) Verify deletion (must return 0 rows)
SELECT COUNT(*) FROM lakehouse.silver_events WHERE user_id = 'user_42';
SELECT COUNT(*) FROM lakehouse.gold_user_features_daily WHERE user_id = 'user_42';

-- 4) For aggregates that may re-identify, mark instead of delete
--    (e.g. add a "deleted_user" flag column)
ALTER TABLE lakehouse.gold_funnel_daily
ADD COLUMN deletion_marker MAP<STRING, BOOLEAN>;

UPDATE lakehouse.gold_funnel_daily
SET deletion_marker['user_42'] = TRUE
WHERE
    -- heuristic: any row that was uniquely attributable to user_42
    -- (in practice: query audit log for which rows user_42 contributed to)
    TRUE;

-- 5) Snapshot expiration to fully purge deleted data from history
ALTER TABLE lakehouse.silver_events
SET TBLPROPERTIES (
    'gc.enabled' = 'true',
    'history.expire.max-snapshot-age-ms' = '0'    -- purge all retained snapshots
);

CALL local.system.expire_snapshots('lakehouse.silver_events');
