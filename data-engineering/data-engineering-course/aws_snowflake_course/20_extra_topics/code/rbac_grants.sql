-- ============================================================================
-- 20_extra_topics / rbac_grants.sql
-- ----------------------------------------------------------------------------
-- A minimal role hierarchy: SYSADMIN → ANALYST_FULL → ANALYST_READ.
-- Roles inherit via ROLE hierarchy (GRANT ROLE ... TO ROLE).
--
-- Lecture reference: "RBAC: roles, grants, hierarchies" (Section 20, L07)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. The costumed roles we will use for the demo ───────────────────
--    Use only ACCOUNTADMIN ORGADMIN to set this up — otherwise raises.
--    CREATE ROLE will ROLLBACK if the role already exists, so guard each.
CREATE ROLE IF NOT EXISTS ANALYST_FULL;
CREATE ROLE IF NOT EXISTS ANALYST_READ;
CREATE ROLE IF NOT EXISTS ETL_DEV;

-- ── 2. Build the hierarchy: ANALYST_READ inherits via ANALYST_FULL ──
--    ROLE hierarchies are *additive*: if a role has ALL the privileges
--    needed by the role below it, you can grant one to the other.
GRANT ROLE ANALYST_READ TO ROLE ANALYST_FULL;
GRANT ROLE ANALYST_FULL TO ROLE SYSADMIN;
GRANT ROLE ETL_DEV     TO ROLE SYSADMIN;

-- ── 3. Database / schema grants ──────────────────────────────────────
GRANT USAGE ON DATABASE SNOWFLAKE_DEMO  TO ROLE ANALYST_FULL;
GRANT USAGE ON DATABASE SNOWFLAKE_DEMO  TO ROLE ANALYST_READ;
GRANT USAGE ON DATABASE SNOWFLAKE_DEMO  TO ROLE ETL_DEV;

GRANT USAGE ON SCHEMA GETTING_STARTED   TO ROLE ANALYST_FULL;
GRANT USAGE ON SCHEMA GETTING_STARTED   TO ROLE ANALYST_READ;
GRANT USAGE ON SCHEMA GETTING_STARTED   TO ROLE ETL_DEV;

-- ── 4. SELECT vs ALL PRIVILEGES ──────────────────────────────────────
GRANT SELECT                ON ALL TABLES IN SCHEMA GETTING_STARTED TO ROLE ANALYST_READ;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA GETTING_STARTED TO ROLE ANALYST_FULL;
GRANT ALL PRIVILEGES         ON ALL TABLES IN SCHEMA GETTING_STARTED TO ROLE ETL_DEV;

-- ── 5. Future grants — anything new created in this schema gets them
GRANT SELECT ON FUTURE TABLES IN SCHEMA GETTING_STARTED TO ROLE ANALYST_READ;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA GETTING_STARTED TO ROLE ETL_DEV;

-- ── 6. Warehouse usage ───────────────────────────────────────────────
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE ANALYST_FULL;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE ANALYST_READ;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE ETL_DEV;

-- ── 7. Inspect the grants ────────────────────────────────────────────
SHOW GRANTS TO ROLE ANALYST_FULL;
SHOW GRANTS TO ROLE ANALYST_READ;
SHOW GRANTS TO ROLE ETL_DEV;
SHOW GRANTS OF ROLE ANALYST_READ;    -- roles it inherits

-- ── 8. Grant a user the role (substitute a real user) ───────────────
-- GRANT ROLE ANALYST_READ TO USER avilx_demo_user;
