-- ============================================================================
-- 08_loading_from_aws / aws_storage_integration.sql
-- ----------------------------------------------------------------------------
-- End-to-end S3 → Snowflake via a STORAGE_INTEGRATION.  Trust is established
-- with a single IAM role; no static credentials ever live in Snowflake.
--
-- Pre-requisites (performed by the data platform engineer, NOT in SQL):
--   1. Create an IAM role in the AWS account with a trust policy that allows
--      Snowflake's principal (STORAGE_AWS_IAM_USER_ARN + STORAGE_AWS_EXTERNAL_ID
--      returned by DESC INTEGRATION).
--   2. Attach an S3 read/write policy to that role.
--
-- Lecture reference: "Loading from S3 with a storage integration" (Section 8, L02)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. The storage integration (no secrets stored) ─────────────────────
CREATE STORAGE INTEGRATION IF NOT EXISTS S3_INT
    TYPE                       = EXTERNAL_STAGE
    STORAGE_PROVIDER           = 'AWS_S3'
    ENABLED                    = TRUE
    STORAGE_AWS_ROLE_ARN       = 'arn:aws:iam::111122223333:role/SnowflakeS3Role'
    STORAGE_ALLOWED_LOCATIONS  = ('s3://avilx-demo-bucket/data/',
                                  's3://avilx-demo-bucket/landing/');

-- ── 2. Get the trust values Snowflake expects on the IAM role ──────────
DESC INTEGRATION S3_INT;
-- Look at:  STORAGE_AWS_IAM_USER_ARN   → put as Principal in the trust policy
--           STORAGE_AWS_EXTERNAL_ID    → put as Condition sts:ExternalId

-- ── 3. CSV file format for the orders data ─────────────────────────────
CREATE OR REPLACE FILE FORMAT S3_CSV_FF
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('\\N', '');

-- ── 4. External stage bound to the integration ─────────────────────────
CREATE OR REPLACE STAGE S3_ORDERS_STAGE
    STORAGE_INTEGRATION = S3_INT
    URL                 = 's3://avilx-demo-bucket/data/orders/'
    FILE_FORMAT         = S3_CSV_FF;

-- ── 5. Verify the stage is reachable (LIST is cheap) ────────────────────
LIST @S3_ORDERS_STAGE;

-- ── 6. Target table ────────────────────────────────────────────────────
CREATE OR REPLACE TABLE S3_ORDERS_RAW (
    order_id     NUMBER,
    customer_id  NUMBER,
    order_date   DATE,
    total_amount NUMBER(18, 2)
)
DATA_RETENTION_TIME_IN_DAYS = 1;

-- ── 7. COPY INTO from S3 ───────────────────────────────────────────────
COPY INTO S3_ORDERS_RAW
FROM   @S3_ORDERS_STAGE
ON_ERROR = CONTINUE
PURGE    = FALSE
RETURN_FAILED_ONLY = TRUE;

-- ── 8. Confirm row counts ──────────────────────────────────────────────
SELECT COUNT(*) AS rows_loaded, SUM(total_amount) AS total
FROM   S3_ORDERS_RAW;
