# Section 8 — Loading from AWS

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L59–L65
> **Duration:** ~46 min

This section switches the source of truth from Snowflake's
internal stages to **AWS S3**. We start with **clustering**
(the theory of micro-partition pruning and when to use it),
then walk through the AWS account setup, S3 bucket creation,
IAM policy and role, and the **`STORAGE INTEGRATION` object**
that ties S3 to Snowflake without any AWS keys in SQL.

By the end of this section you should be able to cluster a
large table, sign up for an AWS free trial, create an S3
bucket, write the least-privilege IAM policy, and create a
Snowflake storage integration that reads from S3.

| L# | Title | Min |
|---|---|---|
| L59 | Clustering — Theory | 7:00 |
| L60 | Clustering — Practice | 8:00 |
| L61 | Sign up for free trial (S3) | 5:00 |
| L62 | Creating S3 bucket | 6:00 |
| L63 | Upload files in S3 | 5:00 |
| L64 | Creating policy | 7:00 |
| L65 | Creating integration object | 8:00 |

## Key concepts you'll need later

- **Clustering** — physical sort of micro-partitions.
  Most tables don't need it; large tables with selective
  queries benefit.
- **S3 bucket** — globally-unique name, region-scoped,
  `Block all public access` on by default.
- **IAM role** = permission policy + trust policy.
  The trust policy locks the role to a specific principal.
- **`STORAGE INTEGRATION`** — Snowflake's bridge to S3.
  Encapsulates the role ARN, the allowed buckets, and
  encryption config. No AWS keys in SQL.

## What comes next

Section 9 is **Loading from Azure** — the same pattern,
with Azure Blob Storage, an Azure AD app, and the
`STORAGE INTEGRATION` for Azure.