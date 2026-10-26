---
l_id: L30
title: Transforming data
duration: "9:00"
prereqs: ["L29"]
downloads: []
---

# L30 — Transforming Data

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — Loading Data
> **Duration:** ~9:00

## Prereqs

L29 — Create a stage & load data. You should have `ORDERS`
loaded from CSV and `CUSTOMERS_RAW` loaded from JSON.

## Key terms

- **Column-level transform** — applies a SQL expression to a
  column at load time. The expression can be a cast, a
  function, a CASE, a regex, etc.
- **`SELECT` in `FROM`** — the recommended way to do column
  transforms during `COPY INTO`.
- **`$1`, `$2`, ...** — positional references to the file's
  columns in CSV/JSON loads.
- **`METADATA$FILENAME`** — a pseudo-column giving the source
  file name. Useful for auditing.
- **`METADATA$FILE_ROW_NUMBER`** — the row number within the
  source file.

## Lecture

The most useful form of `COPY INTO` is the **transform** form,
where you apply SQL expressions to each column at load time.
This avoids the round-trip of "load raw, then UPDATE" and is
the standard pattern for ELT.

### The transform pattern

```sql
COPY INTO ORDERS
  FROM (
    SELECT
      $1::NUMBER              AS order_id,
      $2::NUMBER              AS customer_id,
      $3::DATE                AS order_date,
      $4::NUMBER(10,2)        AS amount,
      UPPER(TRIM($5))         AS status,
      METADATA$FILENAME       AS source_file,
      METADATA$FILE_ROW_NUMBER AS source_row
    FROM @demo_stage/orders.csv
  )
  FILE_FORMAT = (TYPE = CSV
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 SKIP_HEADER = 1)
  ON_ERROR = 'ABORT_STATEMENT';
```

Each `$1`, `$2`, ... is the raw string from the file; the
`::TYPE` cast converts it. You can wrap the value in any SQL
expression:

- `UPPER(...)` — uppercase a string
- `TRIM(...)` — strip whitespace
- `CAST(... AS DATE)` or `::DATE` — type conversion
- `REGEXP_REPLACE(...)` — regex substitution
- `CASE WHEN ... THEN ... END` — branching logic

### Why use transforms

Three benefits:

1. **Single pass.** Load and transform in one step, not two.
2. **Audit trail.** `METADATA$FILENAME` and
   `METADATA$FILE_ROW_NUMBER` let you trace any row back to
   its source.
3. **Type safety.** Explicit casts catch bad data at load
   time, not at query time.

### Loading semi-structured data with transforms

For JSON, the `:` accessor and `PARSE_JSON` are common:

```sql
COPY INTO CUSTOMERS_RAW (id, name, email, signup_date)
  FROM (
    SELECT
      $1:id::NUMBER                       AS id,
      $1:name::VARCHAR                    AS name,
      $1:email::VARCHAR                   AS email,
      $1:signup_date::DATE                AS signup_date
    FROM @demo_stage/customers.json
  )
  FILE_FORMAT = (TYPE = JSON);
```

This pulls the JSON fields out of the `VARIANT` column and
inserts them as strongly-typed columns in a relational
table.

### Rejecting bad rows with `CASE`

```sql
SELECT
  $1::NUMBER                                                          AS order_id,
  $2::NUMBER                                                          AS customer_id,
  $3::DATE                                                            AS order_date,
  CASE WHEN $4 ~ '^[0-9]+\.?[0-9]*$' THEN $4::NUMBER(10,2) ELSE NULL END AS amount,
  UPPER(TRIM($5))                                                     AS status
FROM @demo_stage/orders.csv
```

The `CASE WHEN ... ~ '^[0-9]+...'` checks if the value matches
a numeric pattern; if not, store `NULL` instead of failing.

### Partitioned loads with `WHERE`

You can filter rows in the `COPY INTO FROM (SELECT ...)`
form:

```sql
COPY INTO ORDERS
  FROM (
    SELECT $1, $2, $3, $4, $5
    FROM @demo_stage/orders_2024.csv
    WHERE $3::DATE >= '2024-01-01'
  )
  FILE_FORMAT = (TYPE = CSV);
```

> The `WHERE` is applied **per file** during parsing. It's
> more efficient than a post-load delete but less efficient
> than partitioning files by date in the stage.

## Hands-on

```sql
-- Load with transforms
COPY INTO ORDERS (order_id, customer_id, order_date, amount, status)
  FROM (
    SELECT $1::NUMBER       AS order_id,
           $2::NUMBER       AS customer_id,
           $3::DATE         AS order_date,
           $4::NUMBER(10,2) AS amount,
           UPPER(TRIM($5))  AS status
    FROM @demo_stage/orders.csv
  )
  FILE_FORMAT = (TYPE = CSV
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 SKIP_HEADER = 1)
  ON_ERROR = 'CONTINUE';

SELECT * FROM ORDERS LIMIT 5;
```

## Quiz prep

- What does `METADATA$FILENAME` provide? (The source file
  name for the row)
- What does `$1` refer to? (The first column of the file
  being loaded)
- Why use transforms during `COPY INTO`? (Single pass, audit
  trail, type safety)

## What's next

Next up is **L31 — Additional transformation techniques**,
where we cover flatten, regex, and conditional logic.
