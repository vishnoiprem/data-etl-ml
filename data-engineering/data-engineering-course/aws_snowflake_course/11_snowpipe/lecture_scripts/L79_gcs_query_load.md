---
l_id: L79
title: Query & load data (GCS)
duration: "6:00"
prereqs: ["L78 - Create stage (GCS)"]
---

# L79 — Query & load data (GCS)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 11 — Snowpipe
> **Duration:** 6:00

## Prereqs

You have a GCS bucket, a storage integration, and an external stage
that points at it (L76–L78). You have at least one file (CSV or JSON)
in the bucket. You have a virtual warehouse.

## Lecture

Before we set up Snowpipe on GCS, let's do one more pass on plain
batch loading — but using files we *query* first. The pattern is
"peek at the data, then load it", and it's a good warm-up because
Snowpipe at the end of this section is going to wrap exactly this
`COPY INTO` in a pipe object.

### Step 1 — confirm the stage sees the files

```sql
-- List files in the GCS stage
LIST @my_gcs_stage;

-- Result: one row per file with size, md5, last_modified
```

`LIST @<stage_name>` is the cheapest way to verify the integration,
service account, and bucket prefix are all wired correctly before you
spend compute loading anything.

### Step 2 — peek at the data without loading

```sql
-- Build a temp file format on the fly (or use a named one)
CREATE OR REPLACE FILE FORMAT ff_csv_gcs
  TYPE = CSV
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"';

-- Query a single file directly
SELECT $1, $2, $3
FROM @my_gcs_stage/orders_2024_01.csv
(FILE_FORMAT => 'ff_csv_gcs')
LIMIT 10;
```

Querying staged files is a great habit: you catch schema surprises
(header row, quoting, date format) **before** you commit to a
`COPY INTO` and have to clean up bad rows.

### Step 3 — load the data

```sql
-- Create the target table
CREATE OR REPLACE TABLE raw.orders_gcs (
  order_id    NUMBER,
  customer_id NUMBER,
  order_date  DATE,
  amount      NUMBER(10,2)
);

-- Load
COPY INTO raw.orders_gcs
FROM @my_gcs_stage/orders_2024_01.csv
FILE_FORMAT = (FORMAT_NAME = 'ff_csv_gcs')
ON_ERROR = 'ABORT_STATEMENT';

-- Verify
SELECT COUNT(*), MIN(order_date), MAX(order_date)
FROM raw.orders_gcs;
```

That last `COPY INTO` is exactly what we will hand to Snowpipe in L84
— same statement, same stage, same file format, but the pipe will run
it on every new file the bucket receives.

## Key takeaways

- Always `LIST @<stage>` before loading to confirm visibility.
- Querying staged files with `$1, $2, ...` is a free schema check.
- The `COPY INTO` we just ran is the same one Snowpipe will run
  automatically once we wrap it in a pipe.

## What's next

In **L80 — Unload data** we flip the direction and write Snowflake
query results back out to a GCS bucket with `COPY INTO ... LOCATION=`.
