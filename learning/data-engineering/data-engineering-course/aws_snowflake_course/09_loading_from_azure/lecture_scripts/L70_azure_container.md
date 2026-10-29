---
l_id: L70
title: "Create a container"
duration: "5:00"
prereqs:
  - L69 (Create a storage account)
---

# L70 — Create a container

> **Section:** 9 — Loading from Azure
> **Duration:** 5:00

## Prereqs

- L69 — Create a storage account

## Key terms

- **Container** — a flat namespace inside a storage
  account, holding blobs. Roughly equivalent to an S3
  bucket.
- **Blob** — a single object (file) in a container.
- **Access tier** — `Hot`, `Cool`, `Cold`, or `Archive`.
  `Hot` for frequently-read; `Cool` for backups.
- **Public access level** — `Private` (default), `Blob`,
  `Container`. We keep it `Private` and use a SAS or
  service principal.

## Lecture

A container is the Azure equivalent of an S3 bucket.
It holds blobs (files) in a flat namespace; the
"folders" you see in the portal are just key prefixes
with `/` in the name.

### Step 1 — create the container

```bash
az storage container create \
    --name orders \
    --account-name pvsfcourse2026 \
    --public-access off
```

`--public-access off` is the safe default. We'll use a
storage integration to grant Snowflake access; we don't
need public URLs.

### Step 2 — verify the container

```bash
az storage container list \
    --account-name pvsfcourse2026 \
    --query "[].{name:name, publicAccess:properties.publicAccess}" \
    --output table
```

Expected: a single row with `name = orders` and
`publicAccess = off`.

### Step 3 — upload files

```bash
az storage blob upload \
    --container-name orders \
    --file code/orders.parquet \
    --name raw/orders/2026-10-01/orders.parquet \
    --account-name pvsfcourse2026 \
    --overwrite

az storage blob upload \
    --container-name orders \
    --file code/orders.json \
    --name raw/orders/2026-10-01/orders.json \
    --account-name pvsfcourse2026 \
    --overwrite
```

`--name raw/orders/2026-10-01/orders.parquet` is the
**blob name**, not a path. Azure flattens the "folders"
— they're really just key prefixes.

### Step 4 — verify the upload

```bash
az storage blob list \
    --container-name orders \
    --account-name pvsfcourse2026 \
    --query "[].{name:name, size:properties.contentLength, type:properties.contentType}" \
    --output table
```

Expected: two rows for the two files, sizes matching
your local copies.

### Step 5 — generate a SAS for ad-hoc testing

A **SAS (Shared Access Signature)** is a time-limited URL
that grants scoped access. For the Snowflake integration
we use a service principal (L71), but for quick
verification a SAS is convenient:

```bash
az storage blob generate-sas \
    --container-name orders \
    --name raw/orders/2026-10-01/orders.parquet \
    --account-name pvsfcourse2026 \
    --permissions r \
    --expiry 2026-12-31T00:00:00Z \
    --https-only \
    --output tsv
```

The result is a query-string you can append to the blob
URL to grant read access until the expiry.

We will **not** use a SAS for the production storage
integration; we use an Azure AD service principal.

### Container naming rules

- 3–63 characters
- Lowercase letters, digits, hyphens
- Cannot start or end with a hyphen
- Cannot have two consecutive hyphens

`orders` is fine. `raw-orders-2026` is fine. `Raw_Orders`
is **not** (uppercase / underscore).

### The Azure blob URL format

The full URL to a blob is:

```text
https://<account>.blob.core.windows.net/<container>/<blob>
```

Example:

```text
https://pvsfcourse2026.blob.core.windows.net/orders/raw/orders/2026-10-01/orders.parquet
```

This is the URL Snowflake's external stage will point at
(L72).

### Container vs bucket — mental model

| Azure | AWS S3 |
|---|---|
| Storage account | Account |
| Container | Bucket |
| Blob | Object |
| Blob name with `/` | Key with `/` |

The most important difference: in Azure, the **storage
account** is the unit of billing. In AWS, the **bucket**
is. Don't confuse the two when reading docs.

### Cost of a container

Containers themselves are **free** — you pay for the
blobs inside them and the operations on them. For our
1 GB of orders data:

- Storage: 1 GB × $0.0184/GB/month ≈ $0.02/month.
- Operations: a few cents for the loads.

Effectively free on the free tier.

## Hands-on

Run steps 1–4. Confirm the two files are listed in the
container with the right sizes.

## Quiz prep

- What is the difference between a container and a blob?
- What is the URL format for an Azure blob?
- Why do we keep the container's public access off?

## Key takeaways

- A **container** is Azure's equivalent of an S3 bucket.
- `public-access off` is the safe default.
- Blob URLs look like
  `https://<account>.blob.core.windows.net/<container>/<blob>`.
- We will use an Azure AD service principal, not a SAS,
  for the production integration.

## What's next

In **L71 — Create integration object (Azure)** we create
the Azure AD app, the service principal, and the
`STORAGE INTEGRATION` in Snowflake that bridges the two.