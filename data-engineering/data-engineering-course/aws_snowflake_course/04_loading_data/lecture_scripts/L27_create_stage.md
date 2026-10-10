---
l_id: L27
title: Creating stage
duration: "8:00"
prereqs: ["L26"]
downloads:
  - "../../downloads/sample_data.zip"
---

# L27 — Creating Stage

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — Loading Data
> **Duration:** ~8:00

## Prereqs

L26 — Understanding stages. The `LOADER` role from L24 will
be used in the hands-on.

## Key terms

- **`PUT` command** — uploads a local file to an internal
  stage via SnowSQL / Snowflake CLI. Not available from
  Snowsight.
- **SnowSQL** — the legacy CLI client. Replaced by the
  Snowflake CLI for most use cases.
- **Snowflake CLI** — the modern CLI (`snow` command).
  Supports `snow stage put`, `snow stage list`, etc.
- **Snowsight "Load data"** — UI upload for small files.

## Lecture

In this lecture we create a stage and put a real file in it.
We cover the three ways to upload files to an internal stage:
SnowSQL, the Snowflake CLI, and the Snowsight UI.

### Step 1 — Create the stage

```sql
USE ROLE SYSADMIN;
USE DATABASE DEMO;
USE SCHEMA RAW;

CREATE STAGE IF NOT EXISTS demo_stage
  DIRECTORY = (ENABLE = TRUE)
  FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"');
```

`DIRECTORY = (ENABLE = TRUE)` enables the stage's directory
table, which lets you query the file list with SQL.

### Step 2 — Upload a file

**Option A — Snowsight UI**

1. Click **Data** → **Databases** → `DEMO` → `RAW` → **Stages**.
2. Click `DEMO_STAGE`.
3. Click **+ Files** in the top right.
4. Drag a CSV (e.g. `orders.csv` from `sample_data.zip`) into
   the upload area.
5. Wait for the upload to complete.

**Option B — SnowSQL (legacy CLI)**

```bash
snowsql -a <account> -u loader_user -r LOADER -w LOADING_WH

PUT file:///path/to/orders.csv @DEMO.RAW.demo_stage;
```

**Option C — Snowflake CLI (modern)**

```bash
snow stage put ./orders.csv @DEMO.RAW.demo_stage \
  --connection my_connection \
  --database DEMO --schema RAW
```

For production pipelines, prefer the **Snowflake CLI** —
it's modern, scriptable, and integrates with CI/CD.

### Step 3 — Verify the upload

```sql
LIST @DEMO.RAW.demo_stage;
```

You should see one row for the uploaded file: name, size,
MD5, last modified.

### Step 4 — Query the file directly (optional)

With `DIRECTORY = (ENABLE = TRUE)`, you can query the
directory table:

```sql
SELECT *
FROM DIRECTORY(@DEMO.RAW.demo_stage);
```

The directory table has columns: `RELATIVE_PATH`, `SIZE`,
`LAST_MODIFIED`, `MD5`. Useful for building load manifests
or auditing.

### Step 5 — Create the target table

```sql
CREATE OR REPLACE TABLE DEMO.RAW.ORDERS (
  order_id    NUMBER,
  customer_id NUMBER,
  order_date  DATE,
  amount      NUMBER(10,2),
  status      VARCHAR(20)
);
```

The column types should match the CSV. We'll load the file
in L29.

### Permissions check

Make sure the `LOADER` role has the right grants:

```sql
GRANT USAGE ON STAGE DEMO.RAW.demo_stage TO ROLE LOADER;
GRANT READ ON STAGE DEMO.RAW.demo_stage TO ROLE LOADER;
```

`READ` is required to `LIST` and `COPY INTO` from the stage.
`WRITE` is required to `PUT` files.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE DATABASE DEMO;
USE SCHEMA RAW;

-- 1. Create stage
CREATE STAGE IF NOT EXISTS demo_stage
  DIRECTORY = (ENABLE = TRUE)
  FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"');

-- 2. Grant access to LOADER
GRANT USAGE ON DATABASE DEMO TO ROLE LOADER;
GRANT USAGE ON SCHEMA DEMO.RAW TO ROLE LOADER;
GRANT READ, WRITE ON STAGE DEMO.RAW.demo_stage TO ROLE LOADER;

-- 3. (Upload via UI — see lecture body)
LIST @DEMO.RAW.demo_stage;

-- 4. Create target table
CREATE OR REPLACE TABLE ORDERS (
  order_id    NUMBER,
  customer_id NUMBER,
  order_date  DATE,
  amount      NUMBER(10,2),
  status      VARCHAR(20)
);
```

## Quiz prep

- What is the difference between `READ` and `WRITE` on a
  stage? (READ = LIST and COPY FROM; WRITE = PUT files to)
- What does `DIRECTORY = (ENABLE = TRUE)` enable? (The
  directory table — queryable file metadata)
- What is the modern CLI for Snowflake? (The Snowflake CLI
  / `snow` command)

## What's next

Next up is **L28 — COPY command**, where we run the actual
load.
