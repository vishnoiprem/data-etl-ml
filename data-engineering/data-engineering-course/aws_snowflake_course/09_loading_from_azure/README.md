# Section 9 — Loading from Azure

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L66–L72
> **Duration:** ~44 min

This section wraps up the S3 work with a CSV-and-JSON
ingest and then switches the source of truth to **Azure
Blob Storage**. We sign up for the Azure free trial,
create a storage account and a container, register an
Azure AD application, grant it `Storage Blob Data
Reader`, and create the **`STORAGE INTEGRATION`** that
ties Azure to Snowflake.

By the end of this section you should be able to
explain the S3 → Azure differences (IAM role vs Azure
AD service principal, `s3://` vs `azure://`), and run the
**same** downstream `COPY INTO` SQL against either
provider.

| L# | Title | Min |
|---|---|---|
| L66 | Loading from S3 | 7:00 |
| L67 | Handle JSON (S3) | 7:00 |
| L68 | Sign up for free trial (Azure) | 5:00 |
| L69 | Create a storage account | 6:00 |
| L70 | Create a container | 5:00 |
| L71 | Create integration object (Azure) | 8:00 |
| L72 | Create stage & test connection (Azure) | 6:00 |

## Key concepts you'll need later

- **Storage account** is the unit of Azure storage
  billing. It contains containers, which contain blobs.
- **Azure AD application + service principal** is the
  identity Snowflake assumes.
- **`Storage Blob Data Reader`** is the least-privilege
  RBAC role.
- **Consent URL** must be approved once by an Azure AD
  admin.
- The downstream `COPY INTO` is **identical** for S3 and
  Azure — only the stage changes.

## What comes next

Section 10 is **Loading from GCP** — the third cloud
provider in our multi-cloud pipeline. We sign up for
the GCP free trial, create a GCS bucket, register a
service account, grant it `Storage Object Viewer`, and
create the `STORAGE INTEGRATION` for GCS.