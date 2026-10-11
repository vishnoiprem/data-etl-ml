---
l_id: L63
title: "Upload files in S3"
duration: "5:00"
prereqs:
  - L62 (Creating S3 bucket)
---

# L63 — Upload files in S3

> **Section:** 8 — Loading from AWS
> **Duration:** 5:00

## Prereqs

- L62 — Creating S3 bucket

## Key terms

- **`aws s3 cp`** — copies a local file to (or from) S3.
- **`aws s3 sync`** — synchronises a local directory with an
  S3 prefix, only copying changed files.
- **`Content-Type`** — the MIME type of the object. Snowflake
  uses it to pick a parser; for Parquet, `application/octet-stream`
  is fine.
- **Multipart upload** — automatic for files > 8 MB; faster
  and resumable.

## Lecture

Now we put real data in the bucket. We'll upload the
`orders.parquet` and `orders.json` files from the course
`code/` directory. Two CLI commands and you're done.

### Step 1 — upload a single Parquet file

```bash
aws s3 cp \
    code/orders.parquet \
    s3://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.parquet
```

Expected output:

```text
upload: code/orders.parquet to s3://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.parquet
```

### Step 2 — upload a single JSON file

```bash
aws s3 cp \
    code/orders.json \
    s3://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.json
```

### Step 3 — sync a directory

If you have a `code/orders/` directory with multiple files:

```bash
aws s3 sync code/orders/ \
    s3://pv-snowflake-course-2026/raw/orders/2026-10-01/
```

`sync` is the workhorse for recurring loads — it skips files
that haven't changed (compared by size + mtime) and uploads
only the deltas. Use it for daily file drops.

### Step 4 — verify

```bash
aws s3 ls s3://pv-snowflake-course-2026/raw/orders/2026-10-01/ \
    --recursive --human-readable
```

Expected:

```text
2026-10-10 14:32:01    1.2 MiB raw/orders/2026-10-01/orders.parquet
2026-10-10 14:32:02  412.0 KiB raw/orders/2026-10-01/orders.json
```

### Step 5 — check the file's metadata

```bash
aws s3api head-object \
    --bucket pv-snowflake-course-2026 \
    --key raw/orders/2026-10-01/orders.parquet
```

Returns the object's `ContentLength`, `ETag`, `LastModified`,
and `ContentType`. The `ETag` is the MD5 of the object —
useful for verifying upload integrity.

### Multipart upload (automatic)

For files > 8 MB, the AWS CLI uses **multipart upload**:
the file is split into chunks, uploaded in parallel, and
reassembled server-side. If the upload fails halfway, it
resumes from the last completed chunk. You don't need to
do anything; it's automatic.

If you want to confirm, run with `--debug` and look for
"multipart" in the output.

### Storage class

The default upload uses **S3 Standard**. For data that
will be read once and archived, use **S3 Glacier
Instant Retrieval** or **S3 Glacier Flexible Retrieval**
via `--storage-class`:

```bash
aws s3 cp code/orders.parquet \
    s3://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.parquet \
    --storage-class STANDARD_IA
```

`STANDARD_IA` (Infrequent Access) is ~50% cheaper for storage
but charges per retrieval. Use it for source-of-truth files
that you read only when reloading.

### What the file path means for Snowflake

In L65 we'll point a Snowflake stage at
`s3://pv-snowflake-course-2026/raw/orders/`. The `2026-10-01/`
"folder" becomes part of the file URL:

```text
s3://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.parquet
```

The `METADATA$FILENAME` column in the loaded table will
contain exactly that path — useful for filtering "load only
yesterday's files".

### Pre-flight checklist before L64

Before we move on to IAM policies, confirm:

- [ ] The bucket exists in `us-east-1`.
- [ ] `raw/orders/2026-10-01/orders.parquet` is uploaded.
- [ ] `raw/orders/2026-10-01/orders.json` is uploaded.
- [ ] The IAM user `snowflake-demo` has `s3:ListBucket` and
      `s3:GetObject` on the bucket.

The last item is the subject of L64.

## Hands-on

Upload both files. Verify with `aws s3 ls --recursive`.
Confirm the file sizes match your local copies.

## Quiz prep

- What is the difference between `aws s3 cp` and `aws s3 sync`?
- What does S3 Standard vs STANDARD_IA trade off?
- Why does Snowflake care about the file path inside the
  bucket?

## Key takeaways

- `aws s3 cp` for a single file, `aws s3 sync` for a directory.
- The file path (`raw/orders/2026-10-01/orders.parquet`)
  becomes `METADATA$FILENAME` after a `COPY INTO`.
- Use `STANDARD_IA` for source-of-truth files that are
  reloaded rarely.
- Files > 8 MB upload via **multipart** automatically.

## What's next

In **L64 — Creating policy** we write the IAM policy that
grants Snowflake (via a role) the right to list and read the
bucket.