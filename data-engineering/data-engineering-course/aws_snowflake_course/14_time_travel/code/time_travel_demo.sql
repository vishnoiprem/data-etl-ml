-- ============================================================================
-- 14_time_travel / time_travel_demo.sql
-- ----------------------------------------------------------------------------
-- Time Travel: query a table as it was in the past, then recover data with
-- UNDROP and `CREATE TABLE ... CLONE ... AT (OFFSET => ...)`.
--
-- Lecture reference: "Time Travel" (Section 14, L01)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. The "users" table (one full day of retention by default) ───────
CREATE OR REPLACE TABLE USERS_TT (
    user_id     NUMBER,
    email       VARCHAR,
    updated_at  TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
);
DATA_RETENTION_TIME_IN_DAYS = 1;             -- standard edition, default 1 day

INSERT INTO USERS_TT (user_id, email) VALUES
    (1, 'alice@example.com'),
    (2, 'bob@example.com'),
    (3, 'carol@example.com');

-- ── 2. Mutate the table — this is the "disaster" we'll recover from ───
UPDATE USERS_TT SET email = 'alice+old@example.com' WHERE user_id = 1;
DELETE FROM USERS_TT       WHERE user_id = 3;
INSERT INTO USERS_TT (user_id, email) VALUES (4, 'dave@example.com');

SELECT * FROM USERS_TT ORDER BY user_id;

-- ── 3. Time Travel: snapshot from 5 minutes ago ───────────────────────
SELECT *
FROM   USERS_TT AT (OFFSET => -60*5)
ORDER  BY user_id;

-- ── 4. Time Travel: snapshot before a known statement ────────────────
--    Replace <query_id> with the actual id of the DELETE above.
--    (This is normally captured dynamically — left as a comment for the demo.)
-- SELECT * FROM USERS_TT BEFORE (STATEMENT => '<query_id>');

-- ── 5. Restore: recreate the table as it was 5 minutes ago ────────────
CREATE OR REPLACE TABLE USERS_TT_RESTORED CLONE USERS_TT AT (OFFSET => -60*5);
SELECT * FROM USERS_TT_RESTORED ORDER BY user_id;
