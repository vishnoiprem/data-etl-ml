---
l_id: L62
title: "Creating S3 bucket"
duration: "6:00"
prereqs:
  - L61 (Sign up for free trial (S3))
---

# L62 — Creating S3 bucket

> **Section:** 8 — Loading from AWS
> **Duration:** 6:00

## Prereqs

- L61 — Sign up for free trial (S3)

## Key terms

- **S3 bucket** — a globally-unique namespace in S3. The
  bucket name forms part of the URL (`s3://bucket-name/key`).
- **Region** — the AWS region where the bucket lives. Pick
  the same region as your Snowflake account for low
  egress.
- **Block public access** — the default. Disabling it is
  almost never necessary for a Snowflake integration.
- **Versioning** — keeps every prior version of every
  object. Useful for audit; costs more.
- **Lifecycle policy** — moves objects to cheaper storage
  classes after N days.

## Lecture

Now we create the **S3 bucket** that will hold our orders
data. The bucket is the source-of-truth file store;
Snowflake will read from it via a storage integration in L65.

### Step 1 — choose a bucket name

The bucket name must be **globally unique** across all AWS
accounts. A good pattern:

```text
<your-initials>-snowflake-course-<year>
```

Example: `pv-snowflake-course-2026`. Lowercase, no
underscores, no dots (some services treat dots in bucket
names as subdomain wildcards).

### Step 2 — pick a region

Pick the **same region** as your Snowflake account. For the
free trial that's usually `us-east-1` or `us-west-2`. The
egress cost across regions is non-trivial; same-region
reads are free.

In the AWS console:
**S3 → Create bucket → Region: us-east-1**.

### Step 3 — default settings

Keep the defaults except:

- **Block all public access** — leave this **on**. We will
  not need public access; the Snowflake integration uses
  an IAM role.
- **Bucket versioning** — leave off for this course to save
  cost. Enable in production for audit.

### Step 4 — create the bucket

**Create**. You'll see the empty bucket in the S3 dashboard.

### Step 5 — create a folder structure

The convention we use for this course:

```text
s3://pv-snowflake-course-2026/
    raw/
        orders/
            2026-10-01/orders.parquet
            2026-10-02/orders.parquet
        customers/...
    curated/
        orders/...
    logs/
```

The `raw/<dataset>/<date>/` convention makes it easy to
ingest "yesterday's files" with a path filter on the stage.

### Step 6 — create the folder via the CLI

```bash
aws s3api put-object --bucket pv-snowflake-course-2026 \
    --key raw/orders/2026-10-01/

# equivalent recursive mkdir
aws s3api put-object --bucket pv-snowflake-course-2026 \
    --key raw/orders/2026-10-01/.keep
```

The `.keep` file is a workaround — S3 has no folders, only
keys with `/` in the name. The `.keep` ensures the "folder"
exists in the console.

### Step 7 — verify the bucket

```bash
aws s3 ls s3://pv-snowflake-course-2026/ --recursive
```

Empty list — correct, we haven't uploaded anything yet.

### Bucket policies vs IAM policies — what's the difference

Two policy layers in S3:

- **IAM policies** — attached to a user or role. "What can
  this identity do?"
- **Bucket policies** — attached to the bucket. "Who can
  access this bucket, and how?"

For Snowflake, the **storage integration** (L65) uses an IAM
role. The role has an IAM policy that grants
`s3:GetObject` / `s3:GetObjectVersion` / `s3:ListBucket` on
the bucket. We don't need a bucket policy for the integration
to work.

Bucket policies are useful when you want to share the bucket
with another AWS account (e.g. a partner) — not our use case
here.

### Lifecycle policy (optional, but good practice)

A lifecycle policy can move objects to **Glacier** after N
days, or delete them after M days. For our course:

```json
{
  "Rules": [
    {
      "ID": "ArchiveRawAfter30Days",
      "Status": "Enabled",
      "Filter": { "Prefix": "raw/" },
      "Transitions": [
        { "Days": 30, "StorageClass": "GLACIER" }
      ]
    }
  ]
}
```

Save as `lifecycle.json` and apply:

```bash
aws s3api put-bucket-lifecycle-configuration \
    --bucket pv-snowflake-course-2026 \
    --lifecycle-configuration file://lifecycle.json
```

For the free tier this is a no-op; for production it cuts
storage cost dramatically.

## Hands-on

Create the bucket via the console. Create the `raw/orders/`
"folder" via the CLI. Verify with `aws s3 ls --recursive`.

## Quiz prep

- Why should the bucket region match the Snowflake account
  region?
- What is the difference between an IAM policy and a bucket
  policy?
- What does the `.keep` file do?

## Key takeaways

- Bucket names are **globally unique**; pick a region that
  matches your Snowflake account.
- **Block public access** stays on; we use an IAM role, not
  a public URL.
- The `raw/<dataset>/<date>/` convention makes incremental
  loads easy.
- Lifecycle policies move cold data to cheaper storage.

## What's next

In **L63 — Upload files in S3** we upload the
`orders.parquet` and `orders.json` files to the bucket so
Snowflake has something to read.