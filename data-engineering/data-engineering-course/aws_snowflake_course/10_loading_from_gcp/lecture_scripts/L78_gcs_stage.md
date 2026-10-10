---
l_id: L78
title: "Create stage (GCS)"
duration: "6:00"
prereqs:
  - L77 (Create integration object (GCS))
---

# L78 — Create stage (GCS)

> **Section:** 10 — Loading from GCP
> **Duration:** 6:00

## Prereqs

- L77 — Create integration object (GCS)

## Key terms

- **External stage (GCS)** — a Snowflake stage that
  points at a GCS bucket via a storage integration.
- **`gcs://`** — Snowflake's URL scheme for Google
  Cloud Storage. Replaces `gs://` from the CLI.
- **`LIST @stage`** — list the files visible to the
  stage. The smoke test for any storage integration.

## Lecture

Last lecture we created the integration. This lecture
creates the **external stage** that points at the GCS
bucket and tests the connection.

### Step 1 — create the stage

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE STAGE stg_orders_gcs
    STORAGE_INTEGRATION = gcs_orders_int
    URL = 'gcs://pv-snowflake-course-2026/raw/orders/'
    FILE_FORMAT = (FORMAT_NAME = ff_parquet);
```

Two things to notice:

- `STORAGE_INTEGRATION = gcs_orders_int` — the same
  parameter as the S3 and Azure stages, but pointing
  at a different integration.
- `URL = 'gcs://…'` — the URL scheme is `gcs://`, not
  `gs://` (CLI) or `https://` (browser).

### Step 2 — list the files

```sql
LIST @stg_orders_gcs;
```

Expected:

```text
gcs://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.parquet   1.2 MiB
gcs://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.json      412 KiB
```

If `LIST` returns nothing or errors:

- `403 Forbidden` → the IAM binding on the bucket is
  missing. Re-run step 2 of L77.
- `404 Not Found` → the bucket name or path is wrong.
- `Integration not found` → the storage integration
  wasn't enabled, or you used a role without the
  `CREATE STAGE` privilege on the schema.

### Step 3 — peek at the data

```sql
SELECT
    $1:order_id::STRING                       AS order_id,
    $1:customer.name::STRING                  AS customer_name,
    $1:total::NUMBER(10, 2)                   AS total
FROM @stg_orders_gcs
LIMIT 5;
```

Same `$1:col` syntax as S3 and Azure. Snowflake's
Parquet reader is storage-agnostic.

### Step 4 — load the Parquet file

```sql
USE WAREHOUSE loading_wh;

COPY INTO raw_orders_parquet (raw, filename, row_number)
FROM (
    SELECT
        $1                          AS raw,
        METADATA$FILENAME           AS filename,
        METADATA$FILE_ROW_NUMBER    AS row_number
    FROM @stg_orders_gcs
)
FILE_FORMAT = (FORMAT_NAME = ff_parquet)
ON_ERROR    = CONTINUE;
```

**Identical** to the S3 `COPY INTO` from L66 and the
Azure `COPY INTO` from L72. The only change is the
stage name.

### Step 5 — load the JSON file

```sql
CREATE OR REPLACE STAGE stg_orders_gcs_json
    STORAGE_INTEGRATION = gcs_orders_int
    URL = 'gcs://pv-snowflake-course-2026/raw/orders/'
    FILE_FORMAT = (FORMAT_NAME = ff_json);

COPY INTO raw_orders (raw, filename, row_number)
FROM (
    SELECT $1, METADATA$FILENAME, METADATA$FILE_ROW_NUMBER
    FROM @stg_orders_gcs_json
)
FILE_FORMAT = (FORMAT_NAME = ff_json)
ON_ERROR    = CONTINUE;
```

### Step 6 — verify

```sql
SELECT
    filename,
    COUNT(*) AS n_rows
FROM raw_orders
GROUP BY filename;
```

You should see rows from all three providers now (S3,
Azure, GCS) — if you loaded the same orders.json in
all three.

### The multi-cloud pipeline

At this point in the course you have a pipeline that
ingests from **all three** cloud providers. The
downstream `raw_orders` and `curated_*` tables are
**identical**:

```text
S3      →  stg_orders_s3        ─┐
Azure   →  stg_orders_azure     ─┼─►  raw_orders (VARIANT)  ─►  curated_*
GCS     →  stg_orders_gcs       ─┘
```

Three storage integrations, three external stages,
one set of curated tables. The `INSERT INTO
curated_orders` from L49 doesn't change.

### Pattern: cloud-portable pipelines

If you're building a new pipeline in 2026, design it
to be **cloud-portable**:

1. **Stages are per-cloud** — one stage per provider.
2. **Raw and curated tables are provider-agnostic** —
   the same DDL.
3. **ETL SQL is provider-agnostic** — same `LATERAL
   FLATTEN`, same `INSERT … SELECT`.
4. **Switching clouds is a stage change** — not a
   rewrite.

This is the practical payoff of the storage
integration abstraction.

### Cost tracking for GCS loads

| Component | Billed by | Approx cost |
|---|---|---|
| GCS Standard storage | GCP | ~$0.020/GB/mo |
| Class A operations (LIST) | GCP | ~$0.05 per 10k |
| Class B operations (GET) | GCP | ~$0.004 per 10k |
| Snowflake compute (loading_wh) | Snowflake | per-second credits |

For a 1 GB daily load, the GCS-side cost is pennies.

### Section 10 recap

You have now built the **same pipeline three times**,
once per cloud:

- S3 (section 8) — IAM role + `s3://`.
- Azure (section 9) — Azure AD app + `azure://`.
- GCS (section 10) — GCP service account + `gcs://`.

The Snowflake `STORAGE INTEGRATION` is the only
**abstraction** that ties them together. The rest of
the course (Snowpipe, Cortex, Time Travel, etc.) is
provider-agnostic.

## Hands-on

Run the `LIST`, the `$1:order_id` preview, the Parquet
`COPY INTO`, and the JSON `COPY INTO`. Confirm the
`raw_orders` table has rows from all three providers.

## Quiz prep

- What is the URL scheme for a GCS external stage?
- Why is the rest of the pipeline unchanged when
  switching clouds?
- What is the least-privilege GCP IAM role for a
  Snowflake storage integration?

## Key takeaways

- The GCS stage uses `gcs://` URLs and
  `STORAGE_INTEGRATION = gcs_orders_int`.
- `LIST @stg_orders_gcs` is the smoke test.
- The downstream `COPY INTO` is **identical** to the
  S3 and Azure versions.
- A multi-cloud pipeline is **three storage
  integrations and three stages**, with the rest of
  the SQL unchanged.

## What's next

In **Section 11 — Snowpipe** we'll automate the
`COPY INTO` so that **new files in S3/Azure/GCS
trigger Snowflake loads** without a manual
`COPY INTO` call.