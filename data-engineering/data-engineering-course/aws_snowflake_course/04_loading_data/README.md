# Section 4 — Loading Data

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L24–L32
> **Duration:** ~67 min

This section is the heart of the data engineering workflow
in Snowflake. We cover **RBAC roles** (the security
foundation for the rest of the course), the **loading
methods** (`COPY INTO`, Snowpipe, Snowsight wizard,
Snowpark), **stages** (internal and external), the
**`COPY INTO` command** end-to-end, **column-level
transformations** during load (`$1`, `TRY_CAST`,
`LATERAL FLATTEN`), and the **`ON_ERROR` option** that
controls what happens on bad data.

By the end of this section you should be able to load CSV
and JSON files into Snowflake from a stage, apply
transformations during load, and pick the right
`ON_ERROR` policy.

| L# | Title | Min |
|---|---|---|
| L24 | Roles in Snowflake | 9:00 |
| L25 | Loading methods | 7:00 |
| L26 | Understanding stages | 8:00 |
| L27 | Creating stage | 8:00 |
| L28 | COPY command | 10:00 |
| L29 | Create a stage & load data | 9:00 |
| L30 | Transforming data | 9:00 |
| L31 | Additional transformation techniques | 9:00 |
| L32 | Copy option: ON_ERROR | 8:00 |

## Key concepts you'll need later

- **System roles** — `ACCOUNTADMIN` → `SECURITYADMIN` →
  `USERADMIN` / `SYSADMIN` → custom roles → `PUBLIC`.
- **Stages** — internal (Snowflake-managed) and external
  (S3/ADLS/GCS). Referenced with `@<stage>`.
- **`COPY INTO`** — bulk-load command; idempotent via
  64-day load history.
- **Transforms during load** — `SELECT` in `FROM`,
  positional `$1`, casts, regex, `LATERAL FLATTEN`.
- **`ON_ERROR`** — `ABORT_STATEMENT` (safe default),
  `CONTINUE`, `SKIP_FILE`, `SKIP_FILE_<n>`,
  `SKIP_FILE_<n>%`.
- **`METADATA$FILENAME` / `METADATA$FILE_ROW_NUMBER`** —
  audit columns for traceability.

## What comes next

Section 5 is **Copy Options** — we cover **file format
objects** (named, reusable format specs), the **`ON_ERROR`
recap**, **`VALIDATION_MODE`** (dry-run), **`RETURN_FAILED_ONLY`**,
**working with rejected records**, **`SIZE_LIMIT`**,
**`TRUNCATECOLUMNS` + `FORCE` + load history**. By L40
you'll be able to debug a failing load end-to-end and
recover gracefully from partial failures.