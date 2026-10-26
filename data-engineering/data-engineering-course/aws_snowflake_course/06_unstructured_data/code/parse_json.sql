-- ============================================================================
-- 06_unstructured_data / parse_json.sql
-- ----------------------------------------------------------------------------
-- VARIANT, PARSE_JSON, dot/colon navigation, and get_path().
-- Companion file: flatten_array.sql (next demo) covers LATERAL FLATTEN.
--
-- Lecture reference: "Semi-structured data with VARIANT" (Section 6, L01)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. A small landing table of raw JSON payloads ───────────────────────
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

-- ── 2. Dot / colon navigation ───────────────────────────────────────────
--    `:` is the long form of `.`; either works in SELECT.
SELECT payload:event_id                              AS event_id,
       payload:user.id::NUMBER                       AS user_id,
       payload:user.email::VARCHAR                   AS email,
       payload:ts::TIMESTAMP_TZ                      AS event_ts
FROM   RAW_EVENTS_RAW;

-- ── 3. get_path() — safer for keys with spaces or special characters ─────
SELECT GET_PATH(payload, 'user.id')::NUMBER          AS user_id,
       GET_PATH(payload, 'items[0].sku')::VARCHAR   AS first_sku
FROM   RAW_EVENTS_RAW;

-- ── 4. TYPEOF + IS_ARRAY / IS_OBJECT guards ─────────────────────────────
SELECT payload,
       TYPEOF(payload:items)                         AS items_type,
       TYPEOF(payload:user)                          AS user_type,
       IFF(payload:event_id IS NOT NULL, 'yes', 'no') AS has_id
FROM   RAW_EVENTS_RAW;

-- ── 5. ARRAY_SIZE without flattening (just the count) ────────────────────
SELECT payload:event_id                              AS event_id,
       ARRAY_SIZE(payload:items)                     AS item_count
FROM   RAW_EVENTS_RAW;

-- ── 6. Promote the JSON to a typed table for downstream consumers ───────
CREATE OR REPLACE TABLE RAW_EVENTS_TYPED AS
SELECT
    payload:event_id::VARCHAR             AS event_id,
    payload:user.id::NUMBER               AS user_id,
    payload:user.email::VARCHAR           AS email,
    payload:ts::TIMESTAMP_TZ              AS event_ts,
    payload:items                         AS items_array
FROM   RAW_EVENTS_RAW;

SELECT * FROM RAW_EVENTS_TYPED;
