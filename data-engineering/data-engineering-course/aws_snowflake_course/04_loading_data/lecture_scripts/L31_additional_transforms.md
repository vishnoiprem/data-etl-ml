---
l_id: L31
title: Additional transformation techniques
duration: "9:00"
prereqs: ["L30"]
downloads: []
---

# L31 — Additional Transformation Techniques

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — Loading Data
> **Duration:** ~9:00

## Prereqs

L30 — Transforming data. This lecture extends the transform
pattern with more advanced techniques.

## Key terms

- **`LATERAL FLATTEN`** — turns nested arrays/objects into
  rows. Standard pattern for unnesting JSON.
- **`REGEXP_REPLACE`** — regex substitution.
- **`TRY_CAST`** — safe cast: returns NULL on failure instead
  of erroring.
- **`IFF(condition, a, b)`** — short-form `CASE WHEN`.
- **`NULLIF(a, b)`** — returns NULL if equal, else `a`.
- **`COALESCE(a, b, c, ...)`** — first non-NULL.

## Lecture

This lecture extends the transform pattern with the most
useful SQL functions for loading data: regex, safe casts,
conditionals, and basic JSON flattening.

### `TRY_CAST` for robust loading

The standard cast `::TYPE` raises an error on bad data. The
`TRY_CAST` returns NULL instead:

```sql
SELECT
  $1::NUMBER                                AS order_id,
  TRY_CAST($3 AS DATE)                      AS order_date,  -- NULL on bad date
  TRY_CAST($4 AS NUMBER(10,2))               AS amount
FROM @demo_stage/orders.csv;
```

This is the recommended pattern when the source data is
untrusted.

### `REGEXP_REPLACE` for cleaning strings

```sql
SELECT
  $1::NUMBER                                AS order_id,
  REGEXP_REPLACE($5, '[^A-Za-z]', '')        AS status_clean,  -- only letters
  LOWER(TRIM($2))                           AS customer_email
FROM @demo_stage/orders.csv;
```

`REGEXP_REPLACE(string, pattern, replacement)` follows
POSIX/ICU regex syntax. Common patterns:

- `[^A-Za-z]` — anything that's not a letter
- `^\\s+|\\s+$` — leading/trailing whitespace
- `\\s+` — runs of whitespace
- `\\d+` — digits

### `IFF`, `NULLIF`, `COALESCE`

`IFF(condition, a, b)` is short-form `CASE WHEN condition THEN
a ELSE b END`:

```sql
SELECT
  $1::NUMBER                                                  AS order_id,
  IFF($5 = 'PENDING', TRUE, FALSE)                            AS is_pending,
  NULLIF($4, '')                                              AS amount,        -- empty string → NULL
  COALESCE($4::NUMBER(10,2), 0)                               AS amount_default -- NULL → 0
FROM @demo_stage/orders.csv;
```

`NULLIF(a, b)` returns NULL when `a = b` (useful for empty
strings). `COALESCE` returns the first non-NULL value.

### Conditional transforms with `CASE`

For more complex branching, use `CASE`:

```sql
SELECT
  $1::NUMBER AS order_id,
  CASE
    WHEN $5 = 'A' THEN 'APPROVED'
    WHEN $5 = 'P' THEN 'PENDING'
    WHEN $5 = 'R' THEN 'REJECTED'
    ELSE 'UNKNOWN'
  END AS status_long
FROM @demo_stage/orders.csv;
```

### Flattening JSON arrays with `LATERAL FLATTEN`

For a JSON file with an array of items per order:

```json
{"order_id": 1, "items": [{"sku": "A", "qty": 2}, {"sku": "B", "qty": 1}]}
{"order_id": 2, "items": [{"sku": "C", "qty": 5}]}
```

You can flatten the array into rows:

```sql
COPY INTO ORDER_ITEMS (order_id, sku, qty)
  FROM (
    SELECT
      $1:order_id::NUMBER        AS order_id,
      f.value:sku::VARCHAR        AS sku,
      f.value:qty::NUMBER        AS qty
    FROM @demo_stage/orders_nested.json f,
         LATERAL FLATTEN(input => $1:items) f
  )
  FILE_FORMAT = (TYPE = JSON);
```

Each item in the array becomes its own row in `ORDER_ITEMS`.
We cover flattening in depth in section 6.

### Combining transforms and validation

A common production pattern is to **load raw** then
**transform in a separate step** for validation. But for
simple cases, in-line transforms are more efficient:

```sql
COPY INTO ORDERS_CLEAN (order_id, customer_id, order_date, amount, status)
  FROM (
    SELECT
      TRY_CAST($1 AS NUMBER)                          AS order_id,
      TRY_CAST($2 AS NUMBER)                          AS customer_id,
      TRY_CAST($3 AS DATE)                            AS order_date,
      TRY_CAST($4 AS NUMBER(10,2))                    AS amount,
      UPPER(REGEXP_REPLACE(TRIM($5), '[^A-Za-z]', '')) AS status
    FROM @demo_stage/orders.csv
  )
  FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1)
  ON_ERROR = 'CONTINUE';
```

`ON_ERROR = 'CONTINUE'` ensures that rows that fail
validation don't abort the whole load.

## Hands-on

```sql
-- Load with TRY_CAST and regex cleaning
COPY INTO ORDERS_CLEAN (order_id, customer_id, order_date, amount, status)
  FROM (
    SELECT TRY_CAST($1 AS NUMBER)              AS order_id,
           TRY_CAST($2 AS NUMBER)              AS customer_id,
           TRY_CAST($3 AS DATE)                AS order_date,
           TRY_CAST($4 AS NUMBER(10,2))        AS amount,
           UPPER(TRIM($5))                     AS status
    FROM @demo_stage/orders.csv
  )
  FILE_FORMAT = (TYPE = CSV
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 SKIP_HEADER = 1)
  ON_ERROR = 'CONTINUE';

SELECT * FROM ORDERS_CLEAN LIMIT 10;
```

## Quiz prep

- What is the difference between `CAST` and `TRY_CAST`?
  (`CAST` raises an error on bad data; `TRY_CAST` returns
  NULL)
- What does `LATERAL FLATTEN` do? (Turns nested arrays into
  rows)
- What is the short-form `CASE WHEN ... THEN ... ELSE ...
  END`? (`IFF(condition, a, b)`)

## What's next

Next up is **L32 — Copy option: ON_ERROR**, the first
section-5 lecture on `COPY INTO` options.
