-- ============================================================================
-- 10_loading_from_gcp / gcs_integration.sql
-- ----------------------------------------------------------------------------
-- Snowflake → GCS via a STORAGE_INTEGRATION.  Trust is set up by
-- granting the Snowflake service account (returned by DESC INTEGRATION)
-- the Storage Object Viewer / Creator role on the bucket.
--
-- Pre-requisites (GCP side):
--   1. Identify the Snowflake service account from DESC INTEGRATION.
--   2. Grant it `roles/storage.objectViewer` (and Creator if writing).
--
-- Lecture reference: "Loading from Google Cloud Storage" (Section 10, L01)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. Storage integration for GCS ─────────────────────────────────────
CREATE STORAGE INTEGRATION IF NOT EXISTS GCS_INT
    TYPE                       = EXTERNAL_STAGE
    STORAGE_PROVIDER           = 'GCS'
    ENABLED                    = TRUE
    STORAGE_ALLOWED_LOCATIONS  = ('gcs://avilx-demo-bucket/data/',
                                  'gcs://avilx-demo-bucket/landing/');

-- ── 2. Capture the Snowflake service account that needs GCP IAM grant ──
DESC INTEGRATION GCS_INT;
--   STORAGE_GCP_SERVICE_ACCOUNT — grant this the IAM role on the bucket.

-- ── 3. File format (JSON Lines is common for streaming sources) ────────
CREATE OR REPLACE FILE FORMAT GCS_JSON_FF
    TYPE = JSON
    STRIP_OUTER_ARRAY = TRUE
    IGNORE_UTF8_ERRORS = TRUE;

-- ── 4. External stage bound to the integration ─────────────────────────
CREATE OR REPLACE STAGE GCS_EVENTS_STAGE
    STORAGE_INTEGRATION = GCS_INT
    URL                 = 'gcs://avilx-demo-bucket/data/events/'
    FILE_FORMAT         = GCS_JSON_FF;

-- ── 5. Confirm reachability ────────────────────────────────────────────
LIST @GCS_EVENTS_STAGE;

-- ── 6. Target table (VARIANT to mirror source shape) ───────────────────
CREATE OR REPLACE TABLE GCS_EVENTS_RAW (payload VARIANT);

-- ── 7. COPY INTO from GCS (JSON) ───────────────────────────────────────
COPY INTO GCS_EVENTS_RAW
FROM   @GCS_EVENTS_STAGE
ON_ERROR = CONTINUE
PURGE    = FALSE;

-- ── 8. Flatten the payloads to a typed table ──────────────────────────
CREATE OR REPLACE TABLE GCS_EVENTS_TYPED AS
SELECT
    payload:event_id::VARCHAR          AS event_id,
    payload:user_id::NUMBER            AS user_id,
    payload:event_type::VARCHAR        AS event_type,
    payload:ts::TIMESTAMP_TZ           AS event_ts
FROM   GCS_EVENTS_RAW;

SELECT COUNT(*) AS rows_loaded, COUNT(DISTINCT event_type) AS event_types
FROM   GCS_EVENTS_TYPED;
