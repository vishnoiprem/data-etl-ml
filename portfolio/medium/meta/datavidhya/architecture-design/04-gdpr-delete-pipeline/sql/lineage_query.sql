-- =====================================================================
-- Lineage Discovery — find every place a user's data lives
-- =====================================================================

-- 1) Find all tables containing user_id column
SELECT
    table_catalog,
    table_schema,
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE column_name IN ('user_id', 'userid', 'uid', 'hashed_user_id')
  AND table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY table_catalog, table_schema, table_name;

-- 2) Sample row counts per table (to estimate delete cost)
SELECT
    CONCAT(table_schema, '.', table_name) AS qualified_name,
    total_rows
FROM lakehouse_catalog.table_stats
WHERE column_has_user_id = TRUE
ORDER BY total_rows DESC;

-- 3) Find lineage-derived tables (downstream of tables containing user_id)
-- Requires OpenLineage / DataHub — pseudo-query below
WITH RECURSIVE lineage AS (
    -- Anchor: tables that contain user_id column
    SELECT table_name, 0 AS depth
    FROM table_columns
    WHERE column_name = 'user_id'

    UNION ALL

    -- Recursive: tables that read from above
    SELECT d.downstream_table, l.depth + 1
    FROM lineage l
    JOIN lineage_edges d ON l.table_name = d.upstream_table
    WHERE l.depth < 5
)
SELECT DISTINCT table_name, MIN(depth) AS min_depth
FROM lineage
GROUP BY table_name
ORDER BY min_depth, table_name;
