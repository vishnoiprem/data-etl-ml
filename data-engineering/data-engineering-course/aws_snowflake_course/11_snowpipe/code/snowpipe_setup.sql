-- ============================================================================
-- 11_snowpipe / snowpipe_setup.sql
-- ----------------------------------------------------------------------------
-- AUTO_INGEST Snowpipe: an SQS notification drives a serverless pipe that
-- COPY INTO's new files into a target table automatically.
--
-- Pre-requisites (AWS side, run by the data platform engineer):
--   1. IAM role allowing SQS ReceiveMessage + DeleteMessage.
--   2. SNS topic or S3 Event Notification configured to fan-out to that SQS.
--   3. Snowflake's IAM user + external id from DESC INTEGRATION added as
--      a trust principal on the IAM role.
--
-- Lecture reference: "Snowpipe + auto-ingest" (Section 11, L02)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. Notification integration — wires Snowflake to the SQS queue ────
CREATE NOTIFICATION INTEGRATION IF NOT EXISTS SQS_INT
    TYPE                       = QUEUE
    ENABLED                    = TRUE
    DIRECTION                  = INBOUND
    NOTIFICATION_PROVIDER      = 'AWS_SQS'
    AWS_SQS_ARN                = 'arn:aws:sqs:us-east-1:111122223333:snowflake-snowpipe-q'
    AWS_SQS_ROLE_ARN           = 'arn:aws:iam::111122223333:role/SnowpipeSqsRole';

-- Confirm & grab the trust values
DESC NOTIFICATION INTEGRATION SQS_INT;
-- SF_AWS_IAM_USER_ARN + SF_AWS_EXTERNAL_ID must be added to the IAM trust.

-- ── 2. Reuse the S3 storage integration from section 8 ─────────────────
--    (Created here defensively in case this script is run standalone.)
CREATE STORAGE INTEGRATION IF NOT EXISTS S3_INT
    TYPE                       = EXTERNAL_STAGE
    STORAGE_PROVIDER           = 'AWS_S3'
    ENABLED                    = TRUE
    STORAGE_AWS_ROLE_ARN       = 'arn:aws:iam::111122223333:role/SnowflakeS3Role'
    STORAGE_ALLOWED_LOCATIONS  = ('s3://avilx-demo-bucket/landing/');

-- ── 3. Pipe-ready file format ─────────────────────────────────────────
CREATE OR REPLACE FILE FORMAT SNOWPIPE_CSV_FF
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('\\N', '');

-- ── 4. Target table (micro-partition friendly sorts) ──────────────────
CREATE OR REPLACE TABLE SNOWPIPE_ORDERS (
    order_id     NUMBER,
    customer_id  NUMBER,
    order_date   DATE,
    total_amount NUMBER(18, 2)
)
DATA_RETENTION_TIME_IN_DAYS = 1;

-- ── 5. The pipe itself ────────────────────────────────────────────────
CREATE OR REPLACE PIPE SNOWPIPE_ORDERS_PIPE
    AUTO_INGEST = TRUE
    ERROR_INTEGRATION = SQS_INT
AS
COPY INTO SNOWPIPE_ORDERS
FROM   @S3_INT/orders/                          -- the storage integration stage
FILE_FORMAT = (FORMAT_NAME = SNOWPIPE_CSV_FF)
ON_ERROR    = CONTINUE;

-- ── 6. Capture the SQS ARN Snowflake generates for us ────────────────
DESC PIPE SNOWPIPE_ORDERS_PIPE;
--   notification_channel_name — paste this as the S3 Event notification target.

-- ── 7. Validate the pipe definition with PIPE_STATUS ─────────────────
SELECT SYSTEM$PIPE_STATUS('SNOWPIPE_ORDERS_PIPE') AS pipe_status;
