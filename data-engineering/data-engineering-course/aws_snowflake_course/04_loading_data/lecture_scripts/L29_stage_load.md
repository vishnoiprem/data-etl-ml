---
l_id: L29
title: Create a stage & load data
duration: "9:00"
prereqs: ["L28"]
downloads: []
---

# L29 — Create a Stage & Load Data

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — Loading Data
> **Duration:** ~9:00

## Prereqs

L26–L28. This is an end-to-end lab: create a stage, upload a
file, create a table, and run `COPY INTO`.

## Key terms

- **End-to-end load** — stage + file + table + `COPY INTO` +
  verification.
- **JSON loading** — Snowflake ingests JSON as a single
  `VARIANT` column; you parse it with `:` accessors or
  `LATERAL FLATTEN`.

## Lecture

This is the first full hands-on lab in the course. The
end-to-end flow is:

1. Create a stage.
2. Upload files (CSV and JSON).
3. Create target tables.
4. Run `COPY INTO` for each format.
5. Verify and inspect load history.

### Step 1 — Create a stage

```sql
USE ROLE SYSADMIN;
USE DATABASE DEMO;
USE SCHEMA RAW;

CREATE OR REPLACE STAGE demo_stage
  DIRECTORY = (ENABLE = TRUE)
  FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"');
```

### Step 2 — Upload files

Use the Snowsight UI to upload two files into the stage:

- `orders.csv` (CSV)
- `customers.json` (JSON, one JSON object per line)

Or via the Snowflake CLI:

```bash
snow stage put ./orders.csv    @DEMO.RAW.demo_stage \
  --connection my_connection --database DEMO --schema RAW
snow stage put ./customers.json @DEMO.RAW.demo_stage \
  --connection my_connection --database DEMO --schema RAW
```

### Step 3 — Verify the files

```sql
LIST @demo_stage;
```

You should see two files.

### Step 4 — Create target tables

```sql
-- CSV target
CREATE OR REPLACE TABLE ORDERS (
  order_id    NUMBER,
  customer_id NUMBER,
  order_date  DATE,
  amount      NUMBER(10,2),
  status      VARCHAR(20)
);

-- JSON target (one VARIANT column)
CREATE OR REPLACE TABLE CUSTOMERS_RAW (
  payload VARIANT
);
```

### Step 5 — Load CSV

```sql
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (TYPE = CSV
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 SKIP_HEADER = 1)
  ON_ERROR = 'ABORT_STATEMENT';
```

### Step 6 — Load JSON

```sql
COPY INTO CUSTOMERS_RAW
  FROM @demo_stage/customers.json
  FILE_FORMAT = (TYPE = JSON)
  ON_ERROR = 'ABORT_STATEMENT';
```

The `FILE_FORMAT = (TYPE = JSON)` tells Snowflake to expect
newline-delimited JSON (NDJSON). Each line becomes one row
in the `CUSTOMERS_RAW` table with the full JSON in the
`payload` column.

### Step 7 — Verify

```sql
SELECT * FROM ORDERS LIMIT 5;

-- Parse a JSON row
SELECT payload:id          AS id,
       payload:name        AS name,
       payload:email       AS email
FROM CUSTOMERS_RAW
LIMIT 5;
```

The `payload:field` syntax is Snowflake's dot/colon notation
for accessing VARIANT fields. Section 6 covers JSON parsing
in depth.

### Step 8 — Inspect load history

```sql
SELECT file_name,
       row_count,
       status,
       last_load_time
FROM DEMO.INFORMATION_SCHEMA.LOAD_HISTORY
WHERE schema_name = 'RAW'
ORDER BY last_load_time DESC;
```

You should see two successful loads.

### Re-runnability

Re-run any of the `COPY INTO` statements and observe: the
load succeeds but reports 0 rows loaded (load history skips
the file). Use `FORCE = TRUE` to reload.

## Hands-on

Work through steps 1–8 above. The lab is self-contained; you
should end with:

- Two files in `@demo_stage`
- `ORDERS` table populated from CSV
- `CUSTOMERS_RAW` table populated from JSON
- Two rows in `LOAD_HISTORY`

## Quiz prep

- What is the SQL syntax to access a field in a VARIANT
  column? (`column:field_name`)
- How do you load newline-delimited JSON? (`FILE_FORMAT =
  (TYPE = JSON)`)
- What does the load history show for a file that's
  re-loaded? (0 rows, "already loaded")

## What's next

Next up is **L30 — Transforming data**, where we apply
column-level transformations during the load.
