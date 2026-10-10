-- ============================================================================
-- 06_unstructured_data / flatten_array.sql
-- ----------------------------------------------------------------------------
-- LATERAL FLATTEN to explode nested arrays into rows.  This is the workhorse
-- for any JSON ingestion pipeline in Snowflake.
--
-- Lecture reference: "LATERAL FLATTEN" (Section 6, L02)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- Re-use the typed table from parse_json.sql.  Re-create defensively.
CREATE OR REPLACE TABLE RAW_EVENTS_RAW (payload VARIANT);
INSERT INTO RAW_EVENTS_RAW SELECT PARSE_JSON('{
    "event_id": "ev-001",
    "user":    { "id": 42, "email": "alice@example.com" },
    "items":   [ { "sku": "A1", "qty": 2 }, { "sku": "B7", "qty": 1 } ],
    "ts":      "2026-10-10T12:00:00Z"
}');
INSERT INTO RAW_EVENTS_RAW SELECT PARSE_JSON('{
    "event_id": "ev-002",
    "user":    { "id": 17, "email": "bob@example.com" },
    "items":   [ { "sku": "C3", "qty": 4 } ],
    "ts":      "2026-10-10T12:05:00Z"
}');

-- ── 1. Basic flatten — one row per item per event ───────────────────────
SELECT
    e.payload:event_id::VARCHAR                                AS event_id,
    f.INDEX                                                     AS item_idx,
    f.VALUE:sku::VARCHAR                                        AS sku,
    f.VALUE:qty::NUMBER                                         AS qty
FROM   RAW_EVENTS_RAW e,
       LATERAL FLATTEN(input => e.payload:items) f
ORDER  BY event_id, item_idx;

-- ── 2. Flatten with OUTER => TRUE so events with empty arrays stay ─────
SELECT
    e.payload:event_id::VARCHAR                                AS event_id,
    f.INDEX                                                     AS item_idx,
    f.VALUE:sku::VARCHAR                                        AS sku
FROM   RAW_EVENTS_RAW e,
       LATERAL FLATTEN(input => e.payload:items, OUTER => TRUE) f
ORDER  BY event_id, item_idx;

-- ── 3. Build a properly normalised order-item table ────────────────────
CREATE OR REPLACE TABLE ORDER_ITEMS AS
SELECT
    e.payload:event_id::VARCHAR                                AS event_id,
    e.payload:user.id::NUMBER                                  AS user_id,
    f.INDEX                                                     AS line_no,
    f.VALUE:sku::VARCHAR                                        AS sku,
    f.VALUE:qty::NUMBER                                         AS qty
FROM   RAW_EVENTS_RAW e,
       LATERAL FLATTEN(input => e.payload:items) f;

SELECT * FROM ORDER_ITEMS ORDER BY event_id, line_no;

-- ── 4. Two levels deep — flatten orders, then items inside each order ─
CREATE OR REPLACE TABLE NESTED_ORDERS (payload VARIANT);
INSERT INTO NESTED_ORDERS SELECT PARSE_JSON('{
    "order_id": "o-1",
    "shipments": [
        { "ship_id": "s1", "lines": [ { "sku": "A1", "qty": 1 }, { "sku": "B7", "qty": 3 } ] },
        { "ship_id": "s2", "lines": [ { "sku": "C3", "qty": 2 } ] }
    ]
}');

SELECT
    o.payload:order_id::VARCHAR                                AS order_id,
    s.INDEX                                                     AS shipment_idx,
    s.VALUE:ship_id::VARCHAR                                    AS ship_id,
    l.INDEX                                                     AS line_idx,
    l.VALUE:sku::VARCHAR                                        AS sku,
    l.VALUE:qty::NUMBER                                         AS qty
FROM   NESTED_ORDERS o,
       LATERAL FLATTEN(input => o.payload:shipments) s,
       LATERAL FLATTEN(input => s.VALUE:lines) l
ORDER  BY order_id, shipment_idx, line_idx;
