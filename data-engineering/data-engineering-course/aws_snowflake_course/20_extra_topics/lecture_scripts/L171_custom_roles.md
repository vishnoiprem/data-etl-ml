---
l_id: L171
title: Custom roles + practice
duration: "5:00"
prereqs: ["L170"]
---

# L171 — Custom roles + practice

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 5. Roles deep-dive
> **Duration:** 5:00

## Prereqs

L170 — SYSADMIN + practice.

## Key terms

- **Functional role** — a custom role for a job function
  (e.g. `analyst`, `data_engineer`).
- **Layered RBAC** — the pattern of granting roles to other
  roles to form a hierarchy.
- **Future grants** — `GRANT ... ON FUTURE TABLES ...`; the
  recommended way to keep custom roles up to date.

## Lecture

Welcome back. Today's lecture is the production design of a
custom role hierarchy. By the end, you should be able to set
up a complete RBAC model for a typical data team.

### The four-job-function layout

Most data teams need at least these four functional roles:

```text
                              SYSADMIN
                ┌────────────────┼────────────────┐
                │                │                │
             analyst     data_engineer      etl_developer
                │                                
         ┌──────┴──────┐                 
    read_only      read_write                 
```

- **`analyst`** — `SELECT` on curated datasets, no writes.
- **`data_engineer`** — full DDL on data engineering
  databases.
- **`etl_developer`** — `INSERT`/`UPDATE`/`DELETE` on staging
  and production tables.
- **`read_only`** (sub-role of `analyst`) — only public
  data, no PII.

### Building the hierarchy

```sql
USE ROLE SECURITYADMIN;

-- Top-level functional roles
CREATE ROLE analyst;
CREATE ROLE data_engineer;
CREATE ROLE etl_developer;

-- Sub-role for restricted read access
CREATE ROLE read_only;

-- Grant the functional roles to SYSADMIN (so they inherit basics)
GRANT ROLE analyst       TO ROLE sysadmin;
GRANT ROLE data_engineer TO ROLE sysadmin;
GRANT ROLE etl_developer TO ROLE sysadmin;

-- Grant the sub-role to its parent
GRANT ROLE read_only TO ROLE analyst;
```

### Granting privileges

```sql
USE ROLE SYSADMIN;

-- Analyst: SELECT on the curated marts
GRANT USAGE ON DATABASE marts                 TO ROLE analyst;
GRANT USAGE ON SCHEMA marts.finance           TO ROLE analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA marts.finance TO ROLE analyst;
GRANT SELECT ON FUTURE TABLES IN SCHEMA marts.finance TO ROLE analyst;

-- Data engineer: full DDL on data engineering databases
GRANT OWNERSHIP ON DATABASE de_db             TO ROLE data_engineer COPY CURRENT GRANTS;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA de_db.staging TO ROLE data_engineer;

-- ETL developer: read-write on staging
GRANT USAGE ON DATABASE de_db                TO ROLE etl_developer;
GRANT USAGE ON SCHEMA de_db.staging          TO ROLE etl_developer;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA de_db.staging TO ROLE etl_developer;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA de_db.staging TO ROLE etl_developer;

-- Read-only: a subset of analyst
GRANT USAGE ON DATABASE marts                 TO ROLE read_only;
GRANT USAGE ON SCHEMA marts.public           TO ROLE read_only;
GRANT SELECT ON ALL TABLES IN SCHEMA marts.public TO ROLE read_only;
GRANT SELECT ON FUTURE TABLES IN SCHEMA marts.public TO ROLE read_only;
```

### Future grants

The `ON FUTURE TABLES` clauses are critical. They mean *any
table created later in this schema is automatically granted
to the role*. Without them, every new table requires a
manual grant.

### The audit pattern

```sql
-- What can the analyst role do?
SHOW GRANTS TO ROLE analyst;

-- Who is in the analyst role?
SHOW GRANTS OF ROLE analyst;

-- What did the analyst role do this week?
SELECT user_name, query_text, start_time
FROM   TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE  role_name = 'ANALYST'
  AND  start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;
```

Run this weekly. It's the audit that catches privilege creep.

## Hands-on

```sql
USE ROLE SECURITYADMIN;

-- Build the four roles
CREATE ROLE IF NOT EXISTS analyst;
CREATE ROLE IF NOT EXISTS data_engineer;
CREATE ROLE IF NOT EXISTS etl_developer;
CREATE ROLE IF NOT EXISTS read_only;

GRANT ROLE analyst       TO ROLE sysadmin;
GRANT ROLE data_engineer TO ROLE sysadmin;
GRANT ROLE etl_developer TO ROLE sysadmin;
GRANT ROLE read_only     TO ROLE analyst;

-- Add a user
CREATE USER analyst_dave
  PASSWORD = 'Temp_2026!'
  DEFAULT_ROLE = analyst
  MUST_CHANGE_PASSWORD = TRUE;
GRANT ROLE analyst TO USER analyst_dave;
```

## Key takeaways

- A production layout has 4+ functional roles: analyst,
  data engineer, ETL developer, read-only.
- Grant functional roles to `SYSADMIN`; sub-roles to their
  parent.
- Always use `ON FUTURE TABLES` for new-table coverage.
- Audit role grants weekly.

## What's next

L172 — USERADMIN + practice. The user-management role and
when to use it.