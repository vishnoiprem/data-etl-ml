-- ============================================================================
-- 20_extra_topics / masking_policy.sql
-- ----------------------------------------------------------------------------
-- Column-level masking policy: same table, different result per role.
-- The policy is a CREATE MASKING POLICY, attached to a column with
-- ALTER TABLE ... MODIFY COLUMN ... SET MASKING POLICY.
--
-- Lecture reference: "Dynamic data masking" (Section 20, L06)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. Reusable masking policies ─────────────────────────────────────
--    Tag-based: roles in the 'PII_FULL_ACCESS' tag get plaintext, others do not.
CREATE OR REPLACE MASKING POLICY MP_EMAIL
    AS (val VARCHAR) RETURNS VARCHAR ->
        CASE
            WHEN CURRENT_ROLE() IN ('SYSADMIN', 'SECURITYADMIN', 'PII_FULL_ACCESS')
              OR GET_TAG_VALUES_ON_CURRENT_ROLE('PII_ACCESS') = 'FULL'
            THEN val
            ELSE REGEXP_REPLACE(val, '^(.).*(@.*)$', '\\1***\\2')
        END
        COMMENT = 'Mask email except for privileged roles';

CREATE OR REPLACE MASKING POLICY MP_TOTAL_AMOUNT
    AS (val NUMBER) RETURNS NUMBER ->
        CASE
            WHEN CURRENT_ROLE() IN ('SYSADMIN', 'SECURITYADMIN', 'PII_FULL_ACCESS')
            THEN val
            ELSE 0
        END
        COMMENT = 'Redact order totals except for privileged roles';

-- ── 2. The table that will carry the policy ──────────────────────────
CREATE OR REPLACE TABLE ORDERS_MASKED (
    order_id     NUMBER,
    customer_id  NUMBER,
    email        VARCHAR,
    total_amount NUMBER(18, 2)
);
INSERT INTO ORDERS_MASKED VALUES
    (1, 100, 'alice@example.com', 49.99),
    (2, 200, 'bob@example.com',   79.99);

-- ── 3. Attach the policies ────────────────────────────────────────────
ALTER TABLE ORDERS_MASKED MODIFY COLUMN email        SET MASKING POLICY MP_EMAIL;
ALTER TABLE ORDERS_MASKED MODIFY COLUMN total_amount SET MASKING POLICY MP_TOTAL_AMOUNT;

-- ── 4. Compare: SYSADMIN sees everything; a junior ANALYST role does not
USE ROLE SYSADMIN;
SELECT CURRENT_ROLE() AS role_as_sysadmin, * FROM ORDERS_MASKED;

-- Switch (in a real session) to a different role and you would see masks.
-- USE ROLE ANALYST_JUNIOR;
-- SELECT * FROM ORDERS_MASKED;

-- ── 5. Describe the policies to confirm bindings ─────────────────────
DESC MASKING POLICY MP_EMAIL;
DESC MASKING POLICY MP_TOTAL_AMOUNT;
SHOW MASKING POLICIES;
