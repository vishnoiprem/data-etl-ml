---
l_id: L72
title: "Create stage & test connection (Azure)"
duration: "6:00"
prereqs:
  - L71 (Create integration object (Azure))
---

# L72 — Create stage & test connection (Azure)

> **Section:** 9 — Loading from Azure
> **Duration:** 6:00

## Prereqs

- L71 — Create integration object (Azure)

## Key terms

- **External stage (Azure)** — a Snowflake stage that points
  at an Azure Blob container via a storage integration.
- **`LIST @stage`** — list the files visible to the stage.
  The fastest smoke test for a storage integration.
- **URL form `azure://`** — Snowflake's URL scheme for
  Azure Blob Storage. Replaces `https://` from the portal.

## Lecture

Last lecture we created the integration. This lecture
creates the **external stage** that points at the Azure
container and tests the connection with a `LIST`.

### Step 1 — create the stage

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE STAGE stg_orders_azure
    STORAGE_INTEGRATION = azure_orders_int
    URL = 'azure://pvsfcourse2026.blob.core.windows.net/orders/raw/orders/'
    FILE_FORMAT = (FORMAT_NAME = ff_parquet);
```

Two things to notice:

- `STORAGE_INTEGRATION = azure_orders_int` — same
  parameter as the S3 stage, but pointing at a different
  integration.
- `URL = 'azure://…'` — the URL scheme is `azure://`, not
  `https://`. Snowflake parses this to identify the
  storage account, container, and path.

### Step 2 — list the files

```sql
LIST @stg_orders_azure;
```

Expected:

```text
azure://pvsfcourse2026.blob.core.windows.net/orders/raw/orders/2026-10-01/orders.parquet   1.2 MiB
azure://pvsfcourse2026.blob.core.windows.net/orders/raw/orders/2026-10-01/orders.json      412 KiB
```

If `LIST` returns nothing or errors:

- `403 Forbidden` → the consent URL was not approved, or
  the `Storage Blob Data Reader` role wasn't granted.
- `404 Not Found` → the container name or path is wrong.
- `Integration not found` → the storage integration
  wasn't enabled, or you used a role without privilege.

### Step 3 — peek at the data without loading

```sql
SELECT
    $1:order_id::STRING                       AS order_id,
    $1:customer.name::STRING                  AS customer_name,
    $1:total::NUMBER(10, 2)                   AS total
FROM @stg_orders_azure
LIMIT 5;
```

Same `$1:col` syntax as the S3 Parquet query from L50.
Snowflake's Parquet reader is storage-agnostic — the same
SQL works against any cloud.

### Step 4 — load the Parquet file

```sql
USE WAREHOUSE loading_wh;

COPY INTO raw_orders_parquet (raw, filename, row_number)
FROM (
    SELECT
        $1                          AS raw,
        METADATA$FILENAME           AS filename,
        METADATA$FILE_ROW_NUMBER    AS row_number
    FROM @stg_orders_azure
)
FILE_FORMAT = (FORMAT_NAME = ff_parquet)
ON_ERROR    = CONTINUE;
```

**Identical** to the S3 `COPY INTO` from L66. The only
change is the stage name.

### Step 5 — load the JSON file

```sql
CREATE OR REPLACE STAGE stg_orders_azure_json
    STORAGE_INTEGRATION = azure_orders_int
    URL = 'azure://pvsfcourse2026.blob.core.windows.net/orders/raw/orders/'
    FILE_FORMAT = (FORMAT_NAME = ff_json);

COPY INTO raw_orders (raw, filename, row_number)
FROM (
    SELECT $1, METADATA$FILENAME, METADATA$FILE_ROW_NUMBER
    FROM @stg_orders_azure_json
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

You should see both the Azure and the S3 files (if you
kept the S3 raw table). The `filename` is the full Azure
URL.

### Pattern: storage-agnostic pipelines

With one storage integration per cloud, the rest of the
pipeline is **identical**:

- `raw_orders` table — same DDL.
- `curated_orders` table — same DDL.
- `LATERAL FLATTEN` parsing — same SQL.
- `INSERT INTO curated` watermark — same SQL.

Only the **stage** changes between clouds. This is the
magic of the storage integration: you can build a
multi-cloud pipeline without rewriting any SQL.

### Cross-cloud data sharing

A common production pattern: load raw data from S3
(producer in AWS) into Snowflake, then **share** the
curated data with a Snowflake account on Azure
(consumer). The storage integration is per-account; the
data sharing is the cross-account bridge.

### Cost tracking for Azure loads

| Component | Billed by | Approx cost |
|---|---|---|
| Blob storage (Hot) | Azure | ~$0.018/GB/mo |
| Read operations | Azure | ~$0.004 per 10k |
| Snowflake compute (loading_wh) | Snowflake | per-second credits |

For a 1 GB daily load, the Azure-side cost is pennies.

## Hands-on

Run the `LIST`, the `$1:order_id` preview, the Parquet
`COPY INTO`, and the JSON `COPY INTO`. Confirm the
`raw_orders` table has rows from both Azure and (if
loaded earlier) S3.

## Quiz prep

- What is the URL scheme for an Azure external stage?
- Why is the rest of the pipeline unchanged when
  switching from S3 to Azure?
- What is the right Azure RBAC role to grant the
  Snowflake service principal?

## Key takeaways

- The Azure stage uses `azure://` URLs and
  `STORAGE_INTEGRATION = azure_orders_int`.
- `LIST @stg_orders_azure` is the smoke test.
- The downstream `COPY INTO` is **identical** to the S3
  version — only the stage changes.
- Storage integrations give you a
  **storage-agnostic pipeline**.

## What's next

In **Section 10 — Loading from GCP** we'll do the same
exercise for GCS: GCP free trial, GCS bucket, service
account, and the `STORAGE INTEGRATION` for GCS.