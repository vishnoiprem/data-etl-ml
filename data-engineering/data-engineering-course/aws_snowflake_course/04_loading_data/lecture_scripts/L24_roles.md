---
l_id: L24
title: Roles in Snowflake
duration: "9:00"
prereqs: ["L23"]
downloads: []
---

# L24 — Roles in Snowflake

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — Loading Data
> **Duration:** ~9:00

## Prereqs

L23 — Resource Monitors. This is the first lecture in section
4; we'll set up roles before we load data so the loading
permissions are correct.

## Key terms

- **Role** — a named collection of privileges. Roles are
  granted to users, and privileges flow down.
- **System-defined roles** — `ACCOUNTADMIN`, `SECURITYADMIN`,
  `USERADMIN`, `SYSADMIN`, `PUBLIC`. Pre-created; cannot be
  dropped.
- **Custom role** — a role you create for a specific
  responsibility (e.g. `LOADER`, `ANALYST`).
- **Role hierarchy** — a role can be granted to another role.
  A user with role `B` (which is granted to `A`) implicitly
  has `A`'s privileges.
- **Default role** — the role a user assumes when they log
  in. Set per user.

## Lecture

Snowflake's **role-based access control (RBAC)** model is the
foundation for everything else in this section — every load,
query, and operation in Snowflake runs as a role, and the
role's privileges determine what can be done.

### System-defined roles

Snowflake ships with five system-defined roles, organized in
a hierarchy:

```text
ACCOUNTADMIN                  ← account-level superuser
└── SECURITYADMIN             ← manage users and roles
    ├── USERADMIN             ← create users / roles
    └── SYSADMIN              ← create databases, warehouses
        └── (custom roles)
            ├── LOADER
            ├── ANALYST
            └── PUBLIC        ← every user implicitly has it
```

- **ACCOUNTADMIN** — full control. Can see billing, drop
  accounts, manage resource monitors. Use sparingly.
- **SECURITYADMIN** — manage users and roles globally.
  Inherits `USERADMIN`.
- **USERADMIN** — create users and roles.
- **SYSADMIN** — create databases, schemas, warehouses, and
  tables. Day-to-day admin.
- **PUBLIC** — every user implicitly has this. Default
  privileges for objects without explicit grants.

> **Rule.** The first user created in an account is the
> `ACCOUNTADMIN`. Subsequent users should be created by
> `USERADMIN` and granted only the roles they need.

### Creating a custom role

For a data loading workflow, create a `LOADER` role:

```sql
USE ROLE USERADMIN;

CREATE ROLE LOADER;

-- Grant it to SYSADMIN so SYSADMIN can manage objects on its behalf
GRANT ROLE LOADER TO ROLE SYSADMIN;
```

### Granting privileges

A role by itself has no privileges — you grant them:

```sql
USE ROLE SYSADMIN;

-- Allow the LOADER to use the warehouse
GRANT USAGE ON WAREHOUSE LOADING_WH TO ROLE LOADER;

-- Allow the LOADER to use the database and schema
GRANT USAGE ON DATABASE DEMO TO ROLE LOADER;
GRANT USAGE ON SCHEMA DEMO.RAW TO ROLE LOADER;

-- Allow the LOADER to SELECT from and INSERT into tables
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA DEMO.RAW TO ROLE LOADER;

-- And for future tables
GRANT SELECT, INSERT ON FUTURE TABLES IN SCHEMA DEMO.RAW TO ROLE LOADER;
```

The `ON FUTURE` clause applies the grant to tables created
later — important for production pipelines where new tables
are created automatically.

### Granting the role to a user

```sql
USE ROLE USERADMIN;

CREATE USER loader_user
  PASSWORD = 'temp-password'
  DEFAULT_ROLE = LOADER
  MUST_CHANGE_PASSWORD = TRUE;

GRANT ROLE LOADER TO USER loader_user;
```

### The role hierarchy in action

```sql
-- LOADER can be granted other roles, building a hierarchy
GRANT ROLE LOADER TO ROLE ETL_TEAM;

-- A user with ETL_TEAM inherits LOADER's privileges
GRANT ROLE ETL_TEAM TO USER alice;
```

This is the standard pattern: build a tree of roles from
least-privilege to most-privilege, and grant the right
branch to each user.

### Switching roles

```sql
USE ROLE LOADER;
SELECT CURRENT_ROLE();
```

Every Snowflake session has exactly one **active role** at a
time. Privileges are checked against the active role +
ancestor roles in the hierarchy.

### Inspecting role grants

```sql
-- What does this role have?
SHOW GRANTS TO ROLE LOADER;
SHOW GRANTS ON TABLE DEMO.RAW.ORDERS;

-- What does this user have?
SHOW GRANTS TO USER loader_user;
```

## Hands-on

```sql
USE ROLE USERADMIN;

-- Create the LOADER role and a user
CREATE ROLE IF NOT EXISTS LOADER;
GRANT ROLE LOADER TO ROLE SYSADMIN;

CREATE USER IF NOT EXISTS loader_user
  PASSWORD = 'Temp#Pass2024!'
  DEFAULT_ROLE = LOADER
  MUST_CHANGE_PASSWORD = TRUE;

GRANT ROLE LOADER TO USER loader_user;

-- Grant the required privileges
USE ROLE SYSADMIN;
GRANT USAGE ON WAREHOUSE LOADING_WH TO ROLE LOADER;
GRANT USAGE ON DATABASE DEMO TO ROLE LOADER;
GRANT USAGE ON SCHEMA DEMO.RAW TO ROLE LOADER;
GRANT SELECT, INSERT ON FUTURE TABLES IN SCHEMA DEMO.RAW TO ROLE LOADER;

-- Verify
SHOW GRANTS TO ROLE LOADER;
```

## Quiz prep

- Which system role has full control over an account?
  (`ACCOUNTADMIN`)
- What does `GRANT SELECT, INSERT ON FUTURE TABLES` do?
  (Applies the grant to tables created later)
- What is the default role hierarchy entry point? (`PUBLIC`
  — every user has it implicitly)

## What's next

Next up is **L25 — Loading methods**, where we survey the
different ways to get data into Snowflake: bulk, Snowpipe,
streaming, and the UI wizard.
