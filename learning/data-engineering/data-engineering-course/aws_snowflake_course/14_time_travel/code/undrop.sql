-- ============================================================================
-- 14_time_travel / undrop.sql
-- ----------------------------------------------------------------------------
-- Recovers a dropped table or schema within the Time-Travel retention window.
-- After the retention window, only Fail-Safe can recover (Snowflake support).
--
-- Lecture reference: "Time Travel: UNDROP" (Section 14, L02)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. Create the table, drop it, then UNDROP it ──────────────────────
CREATE OR REPLACE TABLE UNDROP_DEMO (id NUMBER, label VARCHAR);
INSERT INTO UNDROP_DEMO VALUES (1, 'first'), (2, 'second');

DROP TABLE UNDROP_DEMO;
-- (At this point the table is GONE from SHOW TABLES, but data is still
--  available in Time Travel for up to DATA_RETENTION_TIME_IN_DAYS.)

SHOW TABLES LIKE 'UNDROP_DEMO';   -- empty

-- ── 2. UNDROP — bring it back identical to its pre-drop state ──────────
UNDROP TABLE UNDROP_DEMO;

SELECT * FROM UNDROP_DEMO ORDER BY id;

-- ── 3. UNDROP a schema (in case the whole schema is dropped) ──────────
CREATE OR REPLACE SCHEMA UNDROP_SCHEMA_DEMO;
USE SCHEMA UNDROP_SCHEMA_DEMO;
CREATE OR REPLACE TABLE A (id NUMBER);
CREATE OR REPLACE TABLE B (id NUMBER);
DROP SCHEMA UNDROP_SCHEMA_DEMO;
UNDROP SCHEMA UNDROP_SCHEMA_DEMO;
SHOW TABLES IN SCHEMA UNDROP_SCHEMA_DEMO;

-- ── 4. UNDROP a database ──────────────────────────────────────────────
CREATE OR REPLACE DATABASE UNDROP_DB_DEMO;
CREATE OR REPLACE TABLE UNDROP_DB_DEMO.PUBLIC.X (id NUMBER);
DROP DATABASE UNDROP_DB_DEMO;
UNDROP DATABASE UNDROP_DB_DEMO;
SHOW DATABASES LIKE 'UNDROP_DB_DEMO';

-- ── 5. What if the same name was re-created? UNDROP fails — rename one ─
--    Pattern: rename the new object, then UNDROP the old one.
--    (This is for the assignment; not executed here.)
