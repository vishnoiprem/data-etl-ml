# Section 10 — Loading from GCP

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L73–L78
> **Duration:** ~37 min

This section wraps up the Azure work with a CSV and
gzipped-JSON ingest, then switches the source of truth
to **Google Cloud Storage**. We sign up for the GCP
free trial, create a GCS bucket, register a service
account, grant it `Storage Object Viewer`, and create
the **`STORAGE INTEGRATION`** that ties GCS to
Snowflake.

By the end of this section you should be able to
explain the differences between the three cloud
providers' identity models (IAM role / Azure AD app /
GCP service account), the three URL schemes
(`s3://` / `azure://` / `gcs://`), and run the **same**
downstream `COPY INTO` SQL against any of them.

| L# | Title | Min |
|---|---|---|
| L73 | Load CSV file (Azure) | 6:00 |
| L74 | Load JSON file (Azure) | 6:00 |
| L75 | Sign up for free trial (GCP) | 5:00 |
| L76 | Create a bucket (GCS) | 6:00 |
| L77 | Create integration object (GCS) | 8:00 |
| L78 | Create stage (GCS) | 6:00 |

## Key concepts you'll need later

- **`STORAGE INTEGRATION`** is the only Snowflake
  abstraction that ties S3, Azure, and GCS together.
- The downstream `COPY INTO` is **identical** across
  providers — only the stage changes.
- A multi-cloud pipeline is **three storage
  integrations, three stages, one curated table**.
- Each cloud has a different identity model
  (IAM role, Azure AD app + SP, GCP service account)
  but the Snowflake bridge is the same.

## What comes next

Section 11 is **Snowpipe** — the auto-ingest service
that turns "new file in S3" into "new rows in
Snowflake" without a manual `COPY INTO` call.