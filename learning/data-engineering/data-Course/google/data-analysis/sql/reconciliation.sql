-- reconciliation.sql — the nightly safety net.
--
-- A dashboard is a promise. This query is how you keep it.
--
-- The rule: reconcile **values**, not counts. Two tables can have the
-- same number of rows and completely different contents. A count
-- comparison says "the row counts match" when one row says `EMEA` and
-- the other says `APAC`, which is worse than not checking at all —
-- because it produces a green tick on a broken number.
--
-- The comparison is three-way:
--
--   MISSING        — in the source, not in the dashboard's output
--   EXTRA          — in the dashboard's output, not in the source
--   VALUE_MISMATCH — in both, but the values differ
--
-- `IS DISTINCT FROM` is the right operator here because it is NULL-safe:
-- `a <> b` is NULL (not TRUE) when either side is NULL, so a row with a
-- NULL dimension silently passes a `<>` comparison. `IS DISTINCT FROM`
-- compares NULLs properly — two NULLs are not distinct, a NULL and a
-- value are.

-- ---------------------------------------------------------------------------
-- 1. The source of truth
-- ---------------------------------------------------------------------------
-- The source is the raw table, not the modelled output. Reconciling the
-- modelled output against itself proves nothing.

-- ---------------------------------------------------------------------------
-- 2. The comparison
-- ---------------------------------------------------------------------------

WITH source AS (
    SELECT
        line_id,
        order_id,
        customer_id,
        region,
        channel,
        status,
        total_amount,
        margin_amount,
        created_at
    FROM analytics.orders
),

-- The dashboard's answer: the same data, rolled up to the grain the
-- dashboard actually displays.
dashboard AS (
    SELECT
        line_id,
        order_id,
        customer_id,
        region,
        channel,
        status,
        total_amount,
        margin_amount,
        created_at
    FROM analytics.orders_reporting
),

-- A full outer join, so that a row missing from either side shows up.
-- An INNER join would hide exactly the rows you are looking for.
reconciled AS (
    SELECT
        COALESCE(source.line_id, dashboard.line_id)  AS line_id,
        source.region                                 AS source_region,
        dashboard.region                               AS dashboard_region,
        source.total_amount                           AS source_amount,
        dashboard.total_amount                         AS dashboard_amount,
        source.created_at                             AS source_created_at,
        dashboard.created_at                           AS dashboard_created_at,
        CASE
            WHEN source.line_id IS NULL THEN 'EXTRA'
            WHEN dashboard.line_id IS NULL THEN 'MISSING'
            WHEN source.region IS DISTINCT FROM dashboard.region
              OR source.total_amount IS DISTINCT FROM dashboard.total_amount
              OR source.status IS DISTINCT FROM dashboard.status
              OR source.created_at IS DISTINCT FROM dashboard.created_at
            THEN 'VALUE_MISMATCH'
            ELSE 'OK'
        END AS difference
    FROM source
    FULL OUTER JOIN dashboard
        ON source.line_id = dashboard.line_id
)

SELECT
    difference,
    COUNT(*) AS row_count,
    SUM(ABS(COALESCE(source_amount, 0) - COALESCE(dashboard_amount, 0)))
        AS absolute_amount_difference
FROM reconciled
WHERE difference != 'OK'
GROUP BY difference
ORDER BY difference;

-- ---------------------------------------------------------------------------
-- 3. The grain check
-- ---------------------------------------------------------------------------
-- The most consequential thing that can be wrong with a fact table is a
-- duplicated primary key. Every measure over it is inflated, and the
-- inflation looks like growth.

SELECT
    line_id,
    COUNT(*) AS occurrences
FROM analytics.orders
GROUP BY line_id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;

-- ---------------------------------------------------------------------------
-- 4. The fan-out check
-- ---------------------------------------------------------------------------
-- This is the query that catches the mistake everybody makes once.
-- It compares the revenue of the fact table on its own against the
-- revenue of the fact table joined to the dimension table. They must be
-- equal. If the joined number is larger, a join is fanning out.
--
-- Run it every time someone adds a join to a report.

WITH standalone AS (
    SELECT
        SUM(total_amount) AS revenue,
        COUNT(*)          AS order_lines
    FROM analytics.orders
),

joined AS (
    SELECT
        SUM(o.total_amount) AS revenue,
        COUNT(*)            AS order_lines
    FROM analytics.orders AS o
    LEFT JOIN analytics.customers AS c
        ON o.customer_id = c.customer_id
)

SELECT
    standalone.revenue            AS standalone_revenue,
    joined.revenue                AS joined_revenue,
    joined.revenue - standalone.revenue AS difference,
    standalone.order_lines        AS standalone_lines,
    joined.order_lines            AS joined_lines,
    CASE
        WHEN joined.revenue = standalone.revenue
         AND joined.order_lines = standalone.order_lines
        THEN 'OK'
        ELSE 'FAN-OUT'
    END AS verdict
FROM standalone, joined;

-- ---------------------------------------------------------------------------
-- 5. The freshness check
-- ---------------------------------------------------------------------------
-- A stale pipeline looks exactly like a business event on a chart. This
-- is the query that tells them apart.

SELECT
    MAX(created_at)                        AS newest_row,
    TIMESTAMP_DIFF(
        CURRENT_TIMESTAMP(),
        MAX(created_at),
        HOUR
    )                                      AS age_in_hours,
    CASE
        WHEN MAX(created_at) IS NULL THEN 'NO DATA'
        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(created_at), HOUR) > 48
        THEN 'STALE'
        ELSE 'OK'
    END                                    AS verdict
FROM analytics.orders;
