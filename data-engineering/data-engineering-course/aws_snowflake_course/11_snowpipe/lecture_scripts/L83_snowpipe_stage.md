---
l_id: L83
title: Creating stage (Snowpipe)
duration: "7:00"
prereqs: ["L82 - High-level steps (Snowpipe)"]
---

# L83 — Creating stage (Snowpipe)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 11 — Snowpipe
> **Duration:** 7:00

## Prereqs

You have a GCS bucket and a storage integration that lets Snowflake
read from it (L76–L78).

## Lecture

The stage for Snowpipe looks identical to the stage for a batch
`COPY INTO`. The pipe doesn't care about the *type* of stage — it
only cares that the stage can be the `FROM` clause of a `COPY INTO`.
That said, there are a couple of choices that are Snowpipe-specific.

### The basic stage

```sql
USE SCHEMA raw;

CREATE OR REPLACE STAGE my_gcs_stage
  STORAGE_INTEGRATION = gcs_int
  URL = 'gcs://my-snowflake-demo-bucket/orders/'
  FILE_FORMAT = ff_csv_gcs;
```

Same syntax as L78. The `URL` can be a prefix — Snowpipe will only
load files that match it, which is a cheap way to scope one bucket
across multiple tables.

### Why a named stage is better than the URL inline

You can write the pipe with the URL inline:

```sql
CREATE PIPE p AS
COPY INTO raw.orders_gcs
FROM 'gcs://my-snowflake-demo-bucket/orders/'
FILE_FORMAT = (FORMAT_NAME = 'ff_csv_gcs');
```

…but you lose the ability to `ALTER PIPE` and redirect at a
later date. **Always use a named stage** so you can repoint the
pipe without recreating it.

### Restrict the stage to a sub-path

The stage's `URL` can include a prefix. Two pipes pointing at
different prefixes of the same bucket will get different
notification channels and won't step on each other:

```sql
CREATE STAGE orders_stage   URL = 'gcs://bucket/orders/';
CREATE STAGE returns_stage  URL = 'gcs://bucket/returns/';
```

### Decide who owns the file format

You can either:

1. Reference a **named file format** (`FILE_FORMAT = ff_csv_gcs`).
2. Inline it in the `COPY INTO` (`FILE_FORMAT = (TYPE = CSV
   FIELD_DELIMITER = ',' SKIP_HEADER = 1)`).

For Snowpipe specifically, prefer the named file format. If you ever
need to tweak `SKIP_HEADER` or `FIELD_OPTIONALLY_ENCLOSED_BY`, you
change the file format object once and every pipe pointing at it
picks up the change on the next event.

### Confirm the stage is healthy

```sql
LIST @raw.my_gcs_stage;
-- expect to see any files you already uploaded

DESC STAGE raw.my_gcs_stage;
-- confirm STORAGE_INTEGRATION, URL, FILE_FORMAT
```

If `LIST` returns rows, the integration, service account, IAM
binding, and bucket prefix are all correct. If it returns zero rows
or errors with a permissions message, fix the cloud side **before**
you create the pipe.

## Key takeaways

- Snowpipe uses the same stage syntax as batch `COPY INTO`.
- Always use a named stage and a named file format for pipes —
  easier to repoint and easier to evolve.
- The stage URL prefix scopes the pipe to a sub-path of the
  bucket.

## What's next

In **L84 — Create & configure pipe** we finally create the pipe
object and look at the notification channel Snowflake generates.
