---
l_id: L76
title: "Create a bucket (GCS)"
duration: "6:00"
prereqs:
  - L75 (Sign up for free trial (GCP))
---

# L76 — Create a bucket (GCS)

> **Section:** 10 — Loading from GCP
> **Duration:** 6:00

## Prereqs

- L75 — Sign up for free trial (GCP)

## Key terms

- **GCS bucket** — a globally-unique namespace in GCS.
  Bucket names form part of the URL.
- **Storage class** — `Standard`, `Nearline`, `Coldline`,
  `Archive`. Pick `Standard` for active analytics
  workloads.
- **Location type** — `Region`, `Dual-region`,
  `Multi-region`. `Region` is the cheapest; `Multi-region`
  adds redundancy.
- **Uniform bucket-level access** — the modern access
  model. Disables legacy per-object ACLs.
- **Lifecycle policy** — moves objects to cheaper storage
  classes after N days.

## Lecture

Now we create the **GCS bucket** that will hold our
GCP-side orders data. The bucket is the source-of-truth
file store; Snowflake will read from it via a storage
integration in L77.

### Step 1 — choose a bucket name

The bucket name must be **globally unique** across all
GCP customers. A good pattern:

```text
<your-initials>-snowflake-course-<year>
```

Example: `pv-snowflake-course-2026`. Lowercase, no
underscores, no dots.

### Step 2 — create the bucket

```bash
gcloud storage buckets create \
    gs://pv-snowflake-course-2026/ \
    --project=<project-id> \
    --location=us-central1 \
    --uniform-bucket-level-access
```

Field-by-field:

- `gs://pv-snowflake-course-2026/` — the bucket URL.
- `--project` — your GCP project ID.
- `--location=us-central1` — match the Snowflake account
  region.
- `--uniform-bucket-level-access` — modern access model;
  required for the storage integration to work cleanly.

### Step 3 — verify the bucket

```bash
gcloud storage buckets list --project=<project-id>
```

Expected: one row with the bucket name and location.

### Step 4 — upload files

```bash
gcloud storage cp code/orders.parquet \
    gs://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.parquet

gcloud storage cp code/orders.json \
    gs://pv-snowflake-course-2026/raw/orders/2026-10-01/orders.json
```

`gcloud storage cp` is the new unified command
(equivalent to `gsutil cp`).

### Step 5 — verify the upload

```bash
gcloud storage ls gs://pv-snowflake-course-2026/raw/orders/2026-10-01/ \
    --recursive --long
```

Expected: the two files with their sizes and update
times.

### Step 6 — set a lifecycle policy (optional, recommended)

A lifecycle policy moves cold data to cheaper storage
classes:

```bash
cat > lifecycle.json <<'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": { "type": "SetStorageClass", "storageClass": "NEARLINE" },
        "condition": { "age": 30 }
      }
    ]
  }
}
EOF

gcloud storage buckets update \
    gs://pv-snowflake-course-2026/ \
    --lifecycle-file=lifecycle.json
```

After 30 days, objects move from `Standard` to
`Nearline` (~50% cheaper). The transition is free.

### Storage classes

| Class | Cost per GB/month | Retrieval cost | Use case |
|---|---|---|---|
| Standard | $0.020 | Free | Active analytics |
| Nearline | $0.010 | $0.01/GB | 30-day backups |
| Coldline | $0.004 | $0.02/GB | 90-day backups |
| Archive | $0.0012 | $0.05/GB | Long-term archive |

For our 1 GB of orders data, `Standard` is fine.

### Uniform bucket-level access

`--uniform-bucket-level-access` disables the legacy
per-object ACL model. With uniform access, **all**
permission decisions go through IAM. This is the
recommended setting for new buckets.

The downside: if you have older tools that rely on
per-object ACLs, they won't work. For a new bucket
and a Snowflake integration, this is the right choice.

### What we did NOT enable

Three things you might expect but we left off:

- **Versioning** — keeps every prior version. Useful
  for audit; costs more. Enable in production.
- **Public access prevention** — GCS buckets are
  private by default. We don't need public access.
- **Requester pays** — the requester pays the egress.
  Useful for distributing data publicly; not our case.

### Common mistakes

- **Picking the wrong location.** The location is set
  at bucket creation; you can't change it. Re-create
  in the right location if you picked wrong.
- **Forgetting `--uniform-bucket-level-access`.** Old
  per-object ACLs cause integration issues.
- **Picking a non-unique name.** GCP rejects the
  creation; try a different name.

## Hands-on

Run steps 1–5. Confirm with `gcloud storage ls` that
the two files are present.

## Quiz prep

- What is the difference between GCS `Standard` and
  `Nearline`?
- Why do we enable `--uniform-bucket-level-access`?
- What is the GCS equivalent of an S3 bucket name's
  global uniqueness?

## Key takeaways

- GCS bucket names are **globally unique**, like S3.
- Use `--uniform-bucket-level-access` for new buckets.
- Pick the same location as your Snowflake account.
- Lifecycle policies move cold data to cheaper storage
  classes automatically.

## What's next

In **L77 — Create integration object (GCS)** we register
a service account, grant it `Storage Object Viewer`, and
create the `STORAGE INTEGRATION` in Snowflake.