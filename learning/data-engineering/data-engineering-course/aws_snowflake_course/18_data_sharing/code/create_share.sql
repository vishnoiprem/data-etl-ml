-- ============================================================================
-- 18_data_sharing / create_share.sql
-- ----------------------------------------------------------------------------
-- Secure Data Sharing: zero-copy, account-to-account, no ETL.
-- The provider creates a SHARE, grants USAGE on the database and SELECT on
-- the tables, then adds a consumer account.
--
-- Lecture reference: "Secure Data Sharing" (Section 18, L02)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. Source data the provider will share ────────────────────────────
CREATE OR REPLACE TABLE SHARE_PRODUCTS (
    product_id   NUMBER,
    product_name VARCHAR,
    list_price   NUMBER(18, 2)
);
INSERT INTO SHARE_PRODUCTS VALUES
    (1, 'Snowboard',  499.00),
    (2, 'Helmet',     129.00),
    (3, 'Goggles',     79.00);

-- A secure view hides the price column from consumers.
CREATE OR REPLACE SECURE VIEW V_SHARE_PRODUCTS AS
SELECT product_id, product_name
FROM   SHARE_PRODUCTS;

-- ── 2. Create the share object ────────────────────────────────────────
CREATE OR REPLACE SHARE ORDERS_SHARE
    COMMENT = 'Product catalog share for downstream consumer accounts';

-- ── 3. Grant USAGE on the database and schema ─────────────────────────
GRANT USAGE ON DATABASE SNOWFLAKE_DEMO      TO SHARE ORDERS_SHARE;
GRANT USAGE ON SCHEMA   GETTING_STARTED     TO SHARE ORDERS_SHARE;

-- ── 4. Grant SELECT on the underlying table (provider can revoke later)─
GRANT SELECT ON TABLE   SHARE_PRODUCTS       TO SHARE ORDERS_SHARE;
GRANT SELECT ON VIEW    V_SHARE_PRODUCTS     TO SHARE ORDERS_SHARE;

-- ── 5. (Optional) Lock the data so it cannot be exported by the consumer
ALTER SHARE ORDERS_SHARE SET ACCOUNTS = ('consumer_account_1');

-- ── 6. Add a second consumer using a different pattern ────────────────
ALTER SHARE ORDERS_SHARE ADD ACCOUNTS = ('consumer_account_2');

-- ── 7. Inspect the share ─────────────────────────────────────────────
SHOW SHARES LIKE 'ORDERS_SHARE';
DESC SHARE ORDERS_SHARE;

-- ── 8. On the consumer side, they would create a database from the share
-- CREATE OR REPLACE DATABASE CONSUMER_SHARE_DB
--   FROM SHARE <provider_account>.ORDERS_SHARE;
-- Then SELECT normally — no data movement happens.
