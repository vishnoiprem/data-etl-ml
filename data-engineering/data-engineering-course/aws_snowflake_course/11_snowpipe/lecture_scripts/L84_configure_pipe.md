---
l_id: L84
title: Create & configure pipe
duration: "9:00"
prereqs: ["L83 - Creating stage (Snowpipe)"]
---

# L84 — Create & configure pipe

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 11 — Snowpipe
> **Duration:** 9:00

## Prereqs

Table exists, stage exists, file format exists, `LIST @stage` shows
your files.

## Lecture

The pipe is a single DDL statement. The trick is the *post-create*
work: getting the notification channel and wiring the cloud side.

### Create the pipe

```sql
USE SCHEMA raw;

CREATE OR REPLACE PIPE orders_pipe
  AUTO_INGEST = TRUE
  ERROR_INTEGRATION = my_error_int  -- optional, see L86
AS
COPY INTO orders_gcs
FROM @my_gcs_stage
FILE_FORMAT = (FORMAT_NAME = 'ff_csv_gcs');
```

`AUTO_INGEST = TRUE` is the only setting you must specify. Everything
else has sensible defaults.

### Get the notification channel

```sql
SHOW PIPES LIKE 'orders_pipe';

-- The column we want is `notification_channel`
DESC PIPE orders_pipe;
```

The output for a GCS pipe is a `gcs://` URI. For an S3 pipe it's
an SQS ARN. For an Azure pipe it's an Azure Storage event-grid
resource ID. Whatever it is, **copy that value** — you'll paste it
into the cloud config next.

### Verify the pipe sees new files

Once the bucket-to-pipe wiring is in place (L85), drop a file:

```bash
gsutil cp orders_2024_02.csv gs://my-snowflake-demo-bucket/orders/
```

Then watch:

```sql
-- Pipe status
SELECT SYSTEM$PIPE_STATUS('orders_pipe');

-- Load history for this pipe
SELECT file_name, status, row_count, first_error_message, last_loaded_time
FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
  DATE_RANGE_START => DATEADD('hour', -1, CURRENT_TIMESTAMP())
))
WHERE pipe_name = 'ORDERS_PIPE';
```

`PIPE_USAGE_HISTORY` is the Snowflake-native way to see what your
pipe has been doing.

### Pause, resume, refresh

```sql
-- Pause ingestion without dropping the pipe
ALTER PIPE orders_pipe SET PIPE_EXECUTION_PAUSED = TRUE;

-- Resume
ALTER PIPE orders_pipe SET PIPE_EXECUTION_PAUSED = FALSE;

-- Force a refresh — useful after a long bucket pause or to recover
-- from a missed notification
ALTER PIPE orders_pipe REFRESH;
```

`REFRESH` tells Snowflake to re-scan the stage for any files the pipe
should have loaded (within the file retention window) and load them.
It's the "I lost events, please catch up" button.

### Common mistakes

- **Forgetting the file format.** A pipe without a `FILE_FORMAT`
  clause will fail every load with "file format not specified".
- **Wrong schema in the `COPY INTO`.** A column added to the table
  but not to the pipe's stored statement will silently fail.
  Always `DESC PIPE` to see exactly what statement the pipe runs.
- **Permissions.** The role that creates the pipe needs `OWNERSHIP`
  on the pipe, `USAGE` on the database + schema, `USAGE` on the
  stage, and `SELECT`/`INSERT` on the target table.

## Key takeaways

- `CREATE PIPE ... AUTO_INGEST = TRUE AS COPY INTO ...` is the
  whole DDL.
- `DESC PIPE` gives you the `notification_channel` and the stored
  `COPY INTO` — both essential for debugging.
- `ALTER PIPE ... REFRESH` is your catch-up tool when notifications
  get dropped.

## What's next

In **L85 — Configure pipe & notifications** we finish the wiring:
Pub/Sub topic, subscription, and the bucket notification that closes
the loop.
