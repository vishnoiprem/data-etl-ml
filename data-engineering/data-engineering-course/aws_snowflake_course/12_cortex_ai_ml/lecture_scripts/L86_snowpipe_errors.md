---
l_id: L86
title: Error handling for Snowpipe loads
duration: "7:00"
prereqs: ["L85 - Configure pipe & notifications"]
---

# L86 — Error handling for Snowpipe loads

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 7:00

## Prereqs

A working Snowpipe from L79–L85.

## Lecture

Snowpipe auto-ingest can't phone you when something fails. Files
arrive at 3 a.m. with a bad header row, the pipe tries to load them,
the load fails, and you find out the next morning when a dashboard
goes empty. This lecture is about closing that gap.

### The two failure modes

1. **Per-file parse failures** — the file is malformed (wrong
   delimiter, a column count mismatch, a value that overflows a
   `NUMBER(10,2)`). Snowpipe records the error in
   `PIPE_USAGE_HISTORY` and moves on to the next file.
2. **Per-load failures** — the `COPY INTO` itself errors out
   (permissions, missing stage, missing file format). The pipe
   *pauses* processing of further files until the underlying issue
   is fixed.

### 1. Always use `ON_ERROR = 'CONTINUE'`

```sql
CREATE OR REPLACE PIPE raw.orders_pipe
  AUTO_INGEST = TRUE
AS
COPY INTO raw.orders_gcs
FROM @raw.my_gcs_stage
FILE_FORMAT = (FORMAT_NAME = 'ff_csv_gcs')
ON_ERROR = 'CONTINUE';
```

`CONTINUE` (or `SKIP_FILE`) means *one bad row doesn't fail the
whole file*. Without it, Snowpipe errors out the entire file on the
first malformed row.

### 2. Build an error integration

```sql
-- One-time setup: a notification integration that can write to
-- your error bucket / event grid
CREATE NOTIFICATION INTEGRATION my_error_int
  TYPE = QUEUE
  NOTIFICATION_PROVIDER = AWS_SQS
  DIRECTION = OUTBOUND
  ENABLED = TRUE
  AWS_SQS_ROLE_ARN = 'arn:aws:iam::123:role/snowflake-error-role'
  AWS_SQS_EXTERNAL_ID = 'snowflake-err-ext'
  AWS_SQS_ARN = 'arn:aws:sqs:us-east-1:123:snowflake-errors';
```

Then attach it to the pipe:

```sql
ALTER PIPE raw.orders_pipe SET ERROR_INTEGRATION = my_error_int;
```

Now Snowpipe pushes a structured error event to your SQS queue for
every failed load. Your consumer (a Lambda, a Task, a cron) can pick
it up and page on-call.

### 3. Validate a pipe without loading

```sql
-- Re-run a pipe's COPY against a single file in VALIDATE mode
SELECT *
FROM TABLE(VALIDATE_PIPE(
  PIPE_NAME => 'raw.orders_pipe',
  START_TIME => DATEADD('hour', -1, CURRENT_TIMESTAMP())
));
```

`VALIDATE_PIPE` returns the rows that *would have failed*, without
actually loading. Use it after a schema change to confirm the pipe
still works.

### 4. Inspect past errors

```sql
SELECT file_name,
       status,
       row_count,
       first_error_message,
       first_error_line_number,
       last_loaded_time
FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
  DATE_RANGE_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
))
WHERE pipe_name = 'ORDERS_PIPE'
  AND status <> 'LOADED'
ORDER BY last_loaded_time DESC;
```

This is the query to put in a daily Task + alert.

### 5. Reset a stuck pipe

If Snowpipe is wedged after a bad file:

```sql
-- Clear the file from the load history so the pipe moves on
REMOVE @raw.my_gcs_stage/pattern='bad_file_*.csv';
ALTER PIPE raw.orders_pipe REFRESH;
```

`REFRESH` makes the pipe re-scan the stage and pick up anything
still pending.

## Key takeaways

- `ON_ERROR = 'CONTINUE'` is the right default for production pipes.
- `ERROR_INTEGRATION` turns Snowpipe failures into events you can
  route, page, or store.
- `VALIDATE_PIPE` is a free pre-flight check after schema changes.

## What's next

In **L87 — Snowflake Cortex AI - Overview** we leave the loading
story behind and start the AI/ML section with a tour of the
Cortex surface.
