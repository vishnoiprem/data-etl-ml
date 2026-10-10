---
l_id: L26
title: Understanding stages
duration: "8:00"
prereqs: ["L25"]
downloads: []
---

# L26 — Understanding Stages

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — Loading Data
> **Duration:** ~8:00

## Prereqs

L25 — Loading methods. This lecture drills into stages, the
prerequisite for `COPY INTO`.

## Key terms

- **Stage** — a named location where data files are stored
  for loading (and for unloading from Snowflake).
- **Internal stage** — a stage stored in Snowflake-managed
  storage. Created with `CREATE STAGE`.
- **External stage** — a stage that points at an external
  cloud storage location (S3 bucket, Azure container, GCS
  bucket). Created with `CREATE STAGE ... URL = ...`.
- **Stage object** — the Snowflake-level named reference.
  Points at a directory and credentials.
- **Stage path** — `@<stage_name>/<sub-path>/` in SQL.
  Stages are referenced with the `@` prefix.

## Lecture

A **stage** is a named reference to a storage location where
your data files live. Stages are the bridge between your
files in S3/ADLS/GCS (or Snowflake-managed storage) and the
`COPY INTO` command.

### Two types of stages

**Internal stage** — files live in Snowflake-managed
storage. You don't see the underlying S3 bucket; Snowflake
manages it.

```sql
CREATE STAGE my_internal_stage
  DIRECTORY = (ENABLE = TRUE);
```

Useful for:

- Small one-off files uploaded via the UI.
- Files that are produced by Snowflake (e.g. unloaded data
  from another table).

**External stage** — points at your own S3/ADLS/GCS bucket.
The files live in your cloud account; you pay the cloud
provider for storage.

```sql
CREATE STAGE my_s3_stage
  URL = 's3://my-bucket/path/'
  STORAGE_INTEGRATION = my_aws_integration
  FILE_FORMAT = (TYPE = CSV);
```

Useful for:

- Production data lakes.
- Files produced by other systems (Kafka, Kinesis,
  Airflow).

### The `@` prefix

Stages are referenced with `@` in SQL:

```sql
LIST @my_s3_stage;
LIST @my_s3_stage/path/to/2024/01/;
LIST @%my_table;     -- user stage for the current user
LIST @~my_table;     -- table stage for the current table
```

- `@<name>` — named stage
- `@%<table_name>` — user stage for a table (auto-created)
- `@~<table_name>` — table stage for a table (auto-created)

The `@%` and `@~` forms are convenient for small files but
rarely used in production.

### Listing files in a stage

```sql
LIST @my_s3_stage;
```

Returns one row per file: name, size, MD5, last modified.
This is the SQL equivalent of `aws s3 ls`.

### Stage credentials

For external stages, Snowflake needs credentials to read from
your bucket. Two options:

1. **Direct credentials** (not recommended for production):

```sql
CREATE STAGE my_s3_stage
  URL = 's3://my-bucket/path/'
  CREDENTIALS = (AWS_KEY_ID = '...' AWS_SECRET_KEY = '...');
```

2. **Storage integration** (recommended): a Snowflake object
   that holds an IAM role / service principal. Credentials
   are never exposed in SQL.

```sql
-- Created once, reused across stages
CREATE STORAGE INTEGRATION my_aws_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123:role/snowflake-access'
  STORAGE_ALLOWED_LOCATIONS = ('s3://my-bucket/');

CREATE STAGE my_s3_stage
  URL = 's3://my-bucket/path/'
  STORAGE_INTEGRATION = my_aws_integration;
```

Section 8 covers storage integrations for AWS in detail.

### Stages and load history

When you `COPY INTO`, Snowflake records which files were
loaded. Subsequent `COPY INTO` against the same files skips
them (unless you use `FORCE = TRUE`).

This is how Snowflake guarantees **exactly-once** loading
semantics for the same set of files.

## Hands-on

```sql
USE ROLE SYSADMIN;

-- Create a small internal stage
CREATE STAGE IF NOT EXISTS DEMO.RAW.demo_internal_stage
  DIRECTORY = (ENABLE = TRUE);

-- List (empty for now)
LIST @DEMO.RAW.demo_internal_stage;
```

## Quiz prep

- What is the difference between an internal and external
  stage? (Internal = Snowflake-managed storage; external =
  S3/ADLS/GCS in your cloud account)
- What is the `@` prefix in Snowflake SQL? (Reference to a
  stage)
- Why are storage integrations preferred over direct
  credentials? (Credentials are not exposed in SQL; rotated
  centrally)

## What's next

Next up is **L27 — Creating stage**, where we create both an
internal and an external stage and put a real file in the
internal one.
