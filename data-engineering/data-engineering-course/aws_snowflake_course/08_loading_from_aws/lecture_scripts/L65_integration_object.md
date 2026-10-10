---
l_id: L65
title: "Creating integration object"
duration: "8:00"
prereqs:
  - L64 (Creating policy)
---

# L65 — Creating integration object

> **Section:** 8 — Loading from AWS
> **Duration:** 8:00

## Prereqs

- L64 — Creating policy

## Key terms

- **`STORAGE INTEGRATION`** — a Snowflake object that bundles
  the cloud-storage credentials. The integration knows the
  IAM role ARN and the allowed bucket.
- **`STORAGE_AWS_IAM_USER_ARN`** — the AWS user that
  Snowflake uses to assume the role. This is the value you
  put in the trust policy.
- **`STORAGE_AWS_EXTERNAL_ID`** — a Snowflake-managed external
  ID. Adds a second factor to the trust relationship.
- **External stage** — a stage that points at a cloud-storage
  location via a storage integration.

## Lecture

The storage integration is the **bridge** between Snowflake
and S3. It encapsulates the role ARN, the bucket, and any
optional encryption config. Once it exists, a Snowflake
**stage** can point at S3 without any AWS keys in the SQL.

### Step 1 — create the integration

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE STORAGE INTEGRATION s3_orders_int
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'S3'
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/SnowflakeS3IntegrationRole'
    STORAGE_ALLOWED_LOCATIONS = (
        's3://pv-snowflake-course-2026/raw/orders/',
        's3://pv-snowflake-course-2026/raw/customers/'
    );
```

`STORAGE_ALLOWED_LOCATIONS` is a **whitelist** of bucket paths
the integration is allowed to read. Anything outside this list
cannot be loaded through this integration — even if the IAM
role has broader permissions. Defence in depth.

### Step 2 — retrieve the Snowflake AWS principal

```sql
DESC INTEGRATION s3_orders_int;
```

Output (truncated):

| property | property_value |
|---|---|
| `STORAGE_AWS_IAM_USER_ARN` | `arn:aws:iam::777788889999:user/vj4g-aabc...` |
| `STORAGE_AWS_EXTERNAL_ID` | `abc123...` |

These are the values we need to update the IAM role's trust
policy.

### Step 3 — update the trust policy

```bash
cat > trust.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::777788889999:user/vj4g-aabc..."
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "abc123..."
        }
      }
    }
  ]
}
EOF

aws iam update-assume-role-policy \
    --role-name SnowflakeS3IntegrationRole \
    --policy-document file://trust.json
```

Two important fields in the trust policy:

- `Principal.AWS` — the Snowflake AWS user ARN.
- `Condition.sts:ExternalId` — the external ID from
  `DESC INTEGRATION`. Without the external ID, anyone with
  the Snowflake AWS principal could assume the role.

### Step 4 — create the external stage

```sql
CREATE OR REPLACE STAGE stg_orders_s3
    STORAGE_INTEGRATION = s3_orders_int
    URL = 's3://pv-snowflake-course-2026/raw/orders/'
    FILE_FORMAT = (FORMAT_NAME = ff_parquet);
```

`STORAGE_INTEGRATION = s3_orders_int` — the stage uses the
integration's credentials. No AWS keys in the SQL.

`URL = 's3://…'` — the bucket path. Must be a prefix of one
of the `STORAGE_ALLOWED_LOCATIONS` of the integration.

### Step 5 — verify the connection

```sql
LIST @stg_orders_s3;
```

Expected:

```text
s3://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.parquet   1.2 MiB
s3://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.json      412 KiB
```

If `LIST` returns nothing or errors:

- `AccessDenied` → check the trust policy.
- `Integration not found` → check the role used to create
  the integration; only `ACCOUNTADMIN` (or a role with the
  `CREATE INTEGRATION` privilege) can do this.
- Bucket not in the integration's `STORAGE_ALLOWED_LOCATIONS`
  → add the prefix to the integration.

### Step 6 — load data through the integration

```sql
COPY INTO raw_orders_parquet (raw, filename, row_number)
FROM (
    SELECT
        $1                          AS raw,
        METADATA$FILENAME           AS filename,
        METADATA$FILE_ROW_NUMBER    AS row_number
    FROM @stg_orders_s3
)
FILE_FORMAT = (FORMAT_NAME = ff_parquet)
ON_ERROR    = CONTINUE;
```

Same `COPY INTO` pattern as L51. The only difference: the
stage is now an **external** stage pointing at S3, not an
internal one. Snowflake uses the storage integration's
credentials transparently.

### Why this is the production pattern

- **No AWS keys in SQL.** The credentials never leave the
  storage integration.
- **Least-privilege.** The integration's
  `STORAGE_ALLOWED_LOCATIONS` is a whitelist.
- **Auditable.** Every load from this stage is logged in
  `COPY_HISTORY` and `ACCESS_HISTORY`.
- **Rotatable.** If the AWS keys need to change, you update
  the IAM role in AWS; the Snowflake integration is unchanged.

### Common errors

- **Trust policy still has the placeholder.** Update it with
  the values from `DESC INTEGRATION`.
- **`STORAGE_ALLOWED_LOCATIONS` doesn't include the path.**
  Add the prefix and re-run.
- **Bucket region mismatch.** The bucket must be in the
  same region as the Snowflake account (or close — some
  cross-region reads work with extra latency).

## Hands-on

Run steps 1–6 above. The moment `LIST @stg_orders_s3` returns
the two files, your Snowflake-to-S3 bridge is live.

## Quiz prep

- What is a `STORAGE INTEGRATION`?
- Why do you need to update the IAM role's trust policy after
  creating the integration?
- What is the role of `STORAGE_ALLOWED_LOCATIONS`?

## Key takeaways

- `STORAGE INTEGRATION` bundles the AWS role and the allowed
  buckets.
- `DESC INTEGRATION` returns the `STORAGE_AWS_IAM_USER_ARN`
  and `STORAGE_AWS_EXTERNAL_ID` for the trust policy.
- The external stage points at S3 with no AWS keys in SQL.
- `STORAGE_ALLOWED_LOCATIONS` is a **whitelist** — defence in
  depth.

## What's next

In **Section 9 — Loading from Azure** we'll do the same
exercise for Azure Blob Storage: storage account, container,
Azure AD app, and the `STORAGE INTEGRATION` for Azure.