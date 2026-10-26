---
l_id: L33
title: File format object
duration: "8:00"
prereqs: ["L32"]
downloads: []
---

# L33 — File Format Object

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — Copy Options
> **Duration:** ~8:00

## Prereqs

L32 — Copy option: ON_ERROR. The inline `FILE_FORMAT` syntax
from earlier lectures is great for one-offs; named file
format objects are the production pattern.

## Key terms

- **File format object** — a named, reusable set of file
  format options. Created with `CREATE FILE FORMAT`.
- **Type** — `CSV`, `JSON`, `PARQUET`, `AVRO`, `ORC`, `XML`.
- **Schema-level file format** — scoped to a schema (default).
- **Stage-level file format** — applied to a specific stage
  via `STAGE_FILE_FORMAT`.

## Lecture

In L28 we used inline `FILE_FORMAT = (TYPE = CSV ...)` in the
`COPY INTO` command. For production, you want a **named file
format object** that can be reused across many `COPY INTO`
statements and stages.

### Create a file format

```sql
USE ROLE SYSADMIN;
USE DATABASE DEMO;
USE SCHEMA RAW;

CREATE OR REPLACE FILE FORMAT csv_format
  TYPE                    = CSV
  FIELD_DELIMITER         = ','
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  SKIP_HEADER             = 1
  NULL_IF                 = ('\\N', 'NULL', '')
  TRIM_SPACE              = TRUE
  COMPRESSION             = AUTO
  EMPTY_FIELD_AS_NULL     = TRUE;
```

A single object captures the full set of options for parsing
CSV files in your pipeline.

### Use a file format in `COPY INTO`

```sql
COPY INTO ORDERS
  FROM @demo_stage
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT';
```

`FORMAT_NAME = '<name>'` references the named object. You can
also reference by `FORMAT_NAME => 'csv_format'`.

### The most useful options

**CSV**

| Option | Default | What it does |
|---|---|---|
| `FIELD_DELIMITER` | `,` | Column separator |
| `RECORD_DELIMITER` | `\n` | Row separator |
| `SKIP_HEADER` | 0 | Lines to skip at the start |
| `FIELD_OPTIONALLY_ENCLOSED_BY` | (none) | String quote char |
| `TRIM_SPACE` | FALSE | Strip leading/trailing whitespace |
| `NULL_IF` | (none) | Strings to treat as NULL |
| `EMPTY_FIELD_AS_NULL` | FALSE | Empty string → NULL |
| `COMPRESSION` | AUTO_DETECT | GZIP, BZ2, etc. |

**JSON**

```sql
CREATE FILE FORMAT json_format
  TYPE             = JSON
  COMPRESSION      = AUTO
  STRIP_OUTER_ARRAY = FALSE;  -- TRUE if the file is a top-level array
```

**Parquet**

```sql
CREATE FILE FORMAT parquet_format
  TYPE        = PARQUET
  COMPRESSION = AUTO;
```

Parquet's schema is read from the file; no other options are
needed.

### Attaching a file format to a stage

You can set a default file format on a stage:

```sql
CREATE STAGE my_stage
  URL = 's3://my-bucket/path/'
  STORAGE_INTEGRATION = my_aws_integration
  FILE_FORMAT = csv_format;
```

Then `COPY INTO` from `@my_stage` uses `csv_format` by
default; you can still override with `FILE_FORMAT = (FORMAT_NAME
= '...')`.

### Inspect file formats

```sql
SHOW FILE FORMATS IN SCHEMA DEMO.RAW;
DESC FILE FORMAT DEMO.RAW.csv_format;
```

### Drop / modify

```sql
DROP FILE FORMAT DEMO.RAW.csv_format;
ALTER FILE FORMAT DEMO.RAW.csv_format SET SKIP_HEADER = 2;
```

`ALTER` is metadata-only — instant.

### Inline vs named — when to use which

| Situation | Use |
|---|---|
| One-off ad-hoc load | Inline `FILE_FORMAT = (...)` |
| Reused across many tables | Named file format object |
| Pipeline per environment | Named (different per env) |
| Stage-specific default | Attach to the stage |

## Hands-on

```sql
USE ROLE SYSADMIN;
USE DATABASE DEMO;
USE SCHEMA RAW;

-- Create a named file format
CREATE OR REPLACE FILE FORMAT csv_format
  TYPE = CSV
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  SKIP_HEADER = 1;

-- Use it
COPY INTO ORDERS
  FROM @demo_stage/orders.csv
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  ON_ERROR = 'ABORT_STATEMENT';

-- Inspect
SHOW FILE FORMATS IN SCHEMA DEMO.RAW;
```

## Quiz prep

- What is the difference between an inline `FILE_FORMAT =`
  and a named file format object? (Inline = one-off; named =
  reusable across the schema or stage)
- What option strips whitespace from CSV fields?
  (`TRIM_SPACE = TRUE`)
- How do you attach a file format to a stage? (`FILE_FORMAT
  = <name>` in the `CREATE STAGE` statement)

## What's next

Next up is **L34 — Summary**, a short recap of L28–L33 to
consolidate the `COPY INTO` patterns.
