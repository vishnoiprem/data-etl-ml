-- ============================================================================
-- 09_loading_from_azure / azure_integration.sql
-- ----------------------------------------------------------------------------
-- Same pattern as S3 but on Azure: STORAGE_INTEGRATION pointing at an
-- Azure Blob / ADLS Gen2 container.  Trust is handled via an Azure
-- application's consent flow (no secrets in Snowflake).
--
-- Pre-requisites performed in Azure (not in SQL):
--   1. Register an Azure AD application.
--   2. Grant the app's service principal "Storage Blob Data Contributor"
--      on the target container.
--   3. Capture the tenant ID (AZURE_TENANT_ID).
--
-- Lecture reference: "Loading from Azure Blob / ADLS" (Section 9, L02)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. Storage integration for Azure ───────────────────────────────────
CREATE STORAGE INTEGRATION IF NOT EXISTS AZURE_INT
    TYPE                       = EXTERNAL_STAGE
    STORAGE_PROVIDER           = 'AZURE'
    ENABLED                    = TRUE
    AZURE_TENANT_ID            = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    STORAGE_ALLOWED_LOCATIONS  = ('azure://avilxsa.blob.core.windows.net/landing/',
                                  'azure://avilxsa.blob.core.windows.net/data/');

-- ── 2. DESC INTEGRATION to inspect the consent URL & Snowflake principal
DESC INTEGRATION AZURE_INT;
--   AZURE_CONSENT_URL          — paste this into a browser as the Azure AD admin
--   AZURE_MULTI_TENANT_APP_NAME — the app name to consent

-- ── 3. CSV file format (CSV with header) ───────────────────────────────
CREATE OR REPLACE FILE FORMAT AZURE_CSV_FF
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE;

-- ── 4. External stage bound to the Azure integration ───────────────────
CREATE OR REPLACE STAGE AZURE_ORDERS_STAGE
    STORAGE_INTEGRATION = AZURE_INT
    URL                 = 'azure://avilxsa.blob.core.windows.net/data/orders/'
    FILE_FORMAT         = AZURE_CSV_FF;

-- ── 5. List what's on the container ─────────────────────────────────────
LIST @AZURE_ORDERS_STAGE;

-- ── 6. Target table ─────────────────────────────────────────────────────
CREATE OR REPLACE TABLE AZURE_ORDERS_RAW (
    order_id     NUMBER,
    customer_id  NUMBER,
    order_date   DATE,
    region       VARCHAR(10),
    total_amount NUMBER(18, 2)
)
DATA_RETENTION_TIME_IN_DAYS = 1;

-- ── 7. COPY INTO from Azure Blob ────────────────────────────────────────
COPY INTO AZURE_ORDERS_RAW
FROM   @AZURE_ORDERS_STAGE
ON_ERROR = CONTINUE
PURGE    = FALSE;

-- ── 8. Audit + sanity check ─────────────────────────────────────────────
SELECT COUNT(*) AS rows_loaded FROM AZURE_ORDERS_RAW;
SELECT * FROM TABLE(VALIDATE(AZURE_ORDERS_RAW, JOB_QUERY_ID => LAST_QUERY_ID()));
