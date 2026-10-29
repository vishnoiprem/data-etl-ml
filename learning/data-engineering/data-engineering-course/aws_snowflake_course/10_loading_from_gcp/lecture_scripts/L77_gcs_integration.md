---
l_id: L77
title: "Create integration object (GCS)"
duration: "8:00"
prereqs:
  - L76 (Create a bucket (GCS))
---

# L77 — Create integration object (GCS)

> **Section:** 10 — Loading from GCP
> **Duration:** 8:00

## Prereqs

- L76 — Create a bucket (GCS)

## Key terms

- **GCP service account** — a non-human identity used
  by services (and Snowflake) to authenticate to GCP
  APIs. Identified by an email address.
- **Service account key** — a JSON file containing the
  credentials. For Snowflake, we use the **email
  address** of the service account, not a key.
- **`Storage Object Viewer`** — the GCP IAM role that
  grants read access to objects in a bucket.
- **Snowflake service account email** — a fixed email
  Snowflake publishes per region. We grant this email
  access to our bucket.

## Lecture

For GCP, the storage integration is a Snowflake object
that references a **GCP service account email** with
**Storage Object Viewer** on the bucket. The service
account authenticates to GCP; Snowflake uses the
credentials transparently. **No key file is exchanged**
— the trust is at the GCP IAM layer.

### Step 1 — create a service account

```bash
gcloud iam service-accounts create snowflake-sf-course \
    --description="Snowflake storage integration" \
    --display-name="Snowflake SF Course" \
    --project=<project-id>
```

Output includes the **service account email**:

```text
snowflake-sf-course@<project-id>.iam.gserviceaccount.com
```

Save this as `GCP_SA_EMAIL`.

### Step 2 — grant `Storage Object Viewer`

```bash
gcloud storage buckets add-iam-policy-binding \
    gs://pv-snowflake-course-2026/ \
    --member="serviceAccount:${GCP_SA_EMAIL}" \
    --role="roles/storage.objectViewer"
```

`Storage Object Viewer` is the least-privilege read role:
`storage.objects.get`, `storage.objects.list`, and
nothing more.

### Step 3 — retrieve the Snowflake service account email

Snowflake publishes a per-region service account email
that GCP must allow on the bucket. For
`SNOWFLAKE_ACCOUNT = xy12345.us-east-1` and the
default region, the email is:

```text
snowflake-snowflake-account-svc-prod-001@gcp-us-east1-9236-prod-001.iam.gserviceaccount.com
```

The exact email depends on the region. The full list is
in the Snowflake docs. We grant this email
`Storage Object Viewer` on the bucket too:

```bash
SNOWFLAKE_SA_EMAIL="snowflake-snowflake-account-svc-prod-001@gcp-us-east1-9236-prod-001.iam.gserviceaccount.com"

gcloud storage buckets add-iam-policy-binding \
    gs://pv-snowflake-course-2026/ \
    --member="serviceAccount:${SNOWFLAKE_SA_EMAIL}" \
    --role="roles/storage.objectViewer"
```

### Step 4 — create the Snowflake storage integration

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE STORAGE INTEGRATION gcs_orders_int
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'GCS'
    ENABLED = TRUE
    STORAGE_ALLOWED_LOCATIONS = (
        'gcs://pv-snowflake-course-2026/raw/orders/'
    );
```

Note: the URL uses `gcs://` (not `gs://` or
`https://`). Snowflake parses the URL to extract the
bucket and path.

### Step 5 — verify the integration

```sql
SHOW INTEGRATIONS LIKE 'gcs_orders_int';
```

Expected: `enabled = true`, `type = EXTERNAL_STAGE`.

If `DESC INTEGRATION` returns additional GCS-specific
fields, check them. For the simple case, the
`STORAGE_ALLOWED_LOCATIONS` is the only one that
matters.

### Step 6 — test the access (BEFORE creating the stage)

Before creating the stage, you can run a smoke test on
the bucket:

```bash
# Test the service account's access
gcloud storage ls gs://pv-snowflake-course-2026/raw/orders/ \
    --recursive --long \
    --impersonate-service-account=$GCP_SA_EMAIL
```

If this lists the files, the IAM binding is correct.
If it errors with `403 Forbidden`, the role wasn't
applied.

### Why no key file?

The IAM binding on the bucket says "any identity with
the role `Storage Object Viewer` can read this
bucket". When Snowflake's GCP service account
authenticates, it presents itself to GCP, which checks
the IAM bindings. The binding grants access — no key
file is needed.

This is the most secure pattern:

- No long-lived secret to rotate.
- No key file to leak.
- All access is logged in GCP's audit logs.

### Comparison: AWS / Azure / GCP integration

| Step | AWS | Azure | GCP |
|---|---|---|---|
| Identity | IAM role | Azure AD app + SP | GCP service account |
| Permission grant | IAM policy | Azure RBAC | GCP IAM |
| Cross-tenant | External ID | Consent URL | None (same project) |
| URL scheme | `s3://` | `azure://` | `gcs://` |
| Bridge object | `STORAGE INTEGRATION` | `STORAGE INTEGRATION` | `STORAGE INTEGRATION` |

The Snowflake `STORAGE INTEGRATION` is identical in
shape across all three providers. Only the
`STORAGE_PROVIDER` value and the URL scheme change.

### Common errors

- **403 Forbidden on `LIST`** — the IAM binding is
  missing or wrong. Re-run step 2.
- **Bucket not in
  `STORAGE_ALLOWED_LOCATIONS`** — the prefix doesn't
  match. Re-create the integration with the right
  prefix.
- **Wrong service account email** — the GCP SA email
  doesn't exist or has been deleted. Re-run step 1.

## Hands-on

Run steps 1–4. Verify the integration with
`SHOW INTEGRATIONS LIKE 'gcs_orders_int';`. The
moment it shows `enabled = true`, the IAM layer is
working.

## Quiz prep

- What is the difference between an IAM role (AWS) /
  Azure AD app (Azure) / GCP service account?
- Why does the GCS integration not require a key file?
- What is the role of `STORAGE_ALLOWED_LOCATIONS`?

## Key takeaways

- A **service account email** is the GCP identity
  Snowflake assumes; no key file is needed.
- Grant **`Storage Object Viewer`** on the bucket.
- The **Snowflake service account email** (per region)
  also needs the same role.
- The `STORAGE INTEGRATION` is identical in shape to
  the S3 and Azure versions.

## What's next

In **L78 — Create stage (GCS)** we create the external
stage pointing at the GCS bucket and verify with
`LIST`.