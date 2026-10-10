---
l_id: L32
title: Copy option: ON_ERROR
duration: "8:00"
prereqs: ["L31"]
downloads: []
---

# L32 — Copy Option: ON_ERROR

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — Loading Data
> **Duration:** ~8:00

## Prereqs

L31 — Additional transformation techniques. This is the last
lecture in section 4; we drill into the `ON_ERROR` option
that controls what happens when a load hits bad data.

## Key terms

- **`ON_ERROR = 'ABORT_STATEMENT'`** — the default. If any
  row fails, the entire load is rolled back.
- **`ON_ERROR = 'CONTINUE'`** — load valid rows, log the
  failures. The load succeeds.
- **`ON_ERROR = 'SKIP_FILE'`** — if any row in a file fails,
  skip the entire file.
- **`ON_ERROR = 'SKIP_FILE_<n>'`** — skip the file if more
  than `n` errors.
- **`ON_ERROR = 'SKIP_FILE_<n>%'`** — skip the file if more
  than `n%` of rows fail.
- **VALIDATE_TABLE_FUNCTION** — return detailed error
  information after a failed load.

## Lecture

The `ON_ERROR` option is the most important `COPY INTO`
option for production. It controls what happens when a row
fails to parse, cast, or violate a constraint. Picking the
right value is the difference between a load that fails
loudly and one that silently corrupts your data.

### The options

```sql
COPY INTO my_table
  FROM @my_stage
  FILE_FORMAT = (TYPE = CSV)
  ON_ERROR = '<option>';
```

| Option | Behavior |
|---|---|
| `ABORT_STATEMENT` | If any row errors, abort and roll back. Default. |
| `CONTINUE` | Load valid rows; log errors. The load succeeds. |
| `SKIP_FILE` | If any row in a file errors, skip the whole file. |
| `SKIP_FILE_<n>` | Skip a file if more than `n` rows error. |
| `SKIP_FILE_<n>%` | Skip a file if more than `n%` of rows error. |

### `ABORT_STATEMENT` — the safe default

```sql
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1)
  ON_ERROR = 'ABORT_STATEMENT';
```

If any row fails to cast, the load is rolled back; no rows
are inserted. The `COPY INTO` returns an error code. This is
the right default for **data integrity**.

> **Production rule.** Start with `ABORT_STATEMENT`. Move
> away from it only when you have a specific reason.

### `CONTINUE` — best-effort load

```sql
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1)
  ON_ERROR = 'CONTINUE';
```

If 5 out of 1000 rows fail, those 5 are skipped and 995 are
loaded. The `COPY INTO` succeeds, but the result includes
metadata about the skipped rows.

> **Use when.** You have a tolerant load (e.g. a clickstream
> where a few malformed events are OK) and you want
> best-effort ingestion.

### `SKIP_FILE` — fail-loud at the file level

```sql
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1)
  ON_ERROR = 'SKIP_FILE';
```

If any row in a file fails, the whole file is skipped. Useful
when you trust the file format but not the contents.

### `SKIP_FILE_10` — bounded tolerance

```sql
ON_ERROR = 'SKIP_FILE_10';     -- skip file if >10 errors
ON_ERROR = 'SKIP_FILE_5%';     -- skip file if >5% errors
```

A bounded-tolerance version. Skips a file only if errors
exceed the threshold.

### Inspecting errors after a `CONTINUE` load

After a `CONTINUE` load, the result of `COPY INTO` includes
information about skipped rows. To get the detailed error
list:

```sql
SELECT *
FROM TABLE(VALIDATE(my_table, JOB_ID => '<last_query_id>));
```

Returns one row per error: file, row, column, error message,
rejected record.

### `VALIDATION_MODE` — dry run

For pre-load validation:

```sql
COPY INTO my_table
  FROM @my_stage
  FILE_FORMAT = (TYPE = CSV)
  VALIDATION_MODE = 'RETURN_ALL_ERRORS';
```

This validates the load without inserting any rows. Returns
the count of rows that would be loaded, plus all errors.
Invaluable for testing.

Section 5 covers `VALIDATION_MODE` in depth.

### Choosing the right `ON_ERROR`

| Workload | Recommended `ON_ERROR` |
|---|---|
| Financial data | `ABORT_STATEMENT` |
| User events | `CONTINUE` |
| Reference data | `ABORT_STATEMENT` |
| Web logs | `SKIP_FILE_10%` |
| After pre-validation | `ABORT_STATEMENT` |

## Hands-on

```sql
-- 1. Pre-validate
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1)
  VALIDATION_MODE = 'RETURN_ALL_ERRORS';

-- 2. Tolerant load
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1)
  ON_ERROR = 'CONTINUE';

-- 3. Inspect any errors
SELECT * FROM TABLE(VALIDATE(ORDERS, JOB_ID => '_last'));
```

## Quiz prep

- What is the default `ON_ERROR` behavior?
  (`ABORT_STATEMENT`)
- What does `ON_ERROR = 'CONTINUE'` do? (Loads valid rows;
  logs errors)
- What is the difference between `SKIP_FILE` and
  `SKIP_FILE_5%`? (Numeric vs percentage threshold for
  skipping a file)

## Key takeaways

- `ON_ERROR` controls the load's response to bad rows.
- Default `ABORT_STATEMENT` is the safest.
- `CONTINUE` for tolerant, best-effort loads.
- `VALIDATION_MODE` lets you dry-run before committing.

## What's next

Next up is **L33 — File format object**, the first lecture
in section 5. We move from inline `FILE_FORMAT` syntax to
named file format objects.
