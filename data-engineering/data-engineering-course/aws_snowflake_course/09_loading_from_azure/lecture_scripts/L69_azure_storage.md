---
l_id: L69
title: "Create a storage account"
duration: "6:00"
prereqs:
  - L68 (Sign up for free trial (Azure))
---

# L69 — Create a storage account

> **Section:** 9 — Loading from Azure
> **Duration:** 6:00

## Prereqs

- L68 — Sign up for free trial (Azure)

## Key terms

- **Storage account** — a uniquely-named namespace in Azure
  for all your storage (Blob, File, Queue, Table). The
  account name forms part of the URL.
- **Resource group** — a logical container for Azure
  resources. Storage accounts live in a resource group.
- **Performance tier** — `Standard` (HDD-backed, cheap) or
  `Premium` (SSD-backed, expensive). Use `Standard` for
  analytics workloads.
- **Replication** — `LRS` (locally redundant, 3 copies in
  one region), `GRS` (geo-redundant, 6 copies across
  regions), `ZRS` (zone-redundant, 3 zones).
- **Access tier** — `Hot`, `Cool`, `Cold`, `Archive`. Hot
  for frequently-read data; cool/cold for backups.

## Lecture

The storage account is the Azure equivalent of an S3
bucket-with-everything-attached. It contains **all** your
storage — Blob containers, file shares, queues, tables —
in one namespace.

### Step 1 — create a resource group

```bash
az group create \
    --name snowflake-course-rg \
    --location eastus
```

A resource group is a logical container. Deleting the
group deletes every resource inside; that's the easiest
cleanup at the end of the course.

### Step 2 — create the storage account

```bash
az storage account create \
    --name pvsfcourse2026 \
    --resource-group snowflake-course-rg \
    --location eastus \
    --sku Standard_LRS \
    --kind StorageV2
```

Field-by-field:

- `name` — globally unique, like S3. Lowercase, no
  hyphens, 3–24 characters. (Used to be hyphens allowed,
  but Microsoft removed them.)
- `resource-group` — the group from step 1.
- `sku` — `Standard_LRS` is the cheapest. `Standard_GRS`
  for cross-region backup. For free tier: `Standard_LRS`.
- `kind` — `StorageV2` is the modern account type. Use
  this.

### Step 3 — retrieve the connection string

```bash
az storage account show-connection-string \
    --name pvsfcourse2026 \
    --resource-group snowflake-course-rg
```

Returns a JSON object with the **connection string** —
the equivalent of an AWS access key. We'll use this in
L70 to create a container.

```text
"connectionString": "DefaultEndpointsProtocol=https;AccountName=pvsfcourse2026;AccountKey=…;EndpointSuffix=core.windows.net"
```

### Step 4 — configure firewall and networking

By default, the storage account is reachable from any
network. For the course we'll **leave it open**; for
production, restrict to your VNet.

```bash
az storage account update \
    --name pvsfcourse2026 \
    --resource-group snowflake-course-rg \
    --default-action Allow
```

The "DefaultAction: Allow" is the **least-secure** option
but easiest for the free trial. In production, use
`Deny` + a `network-rule` allowing only your Snowflake
subnet.

### Step 5 — create a shared-key credential

For the Azure CLI to talk to the storage account, set
the `AZURE_STORAGE_CONNECTION_STRING` env var:

```bash
export AZURE_STORAGE_CONNECTION_STRING="$(az storage account show-connection-string \
    --name pvsfcourse2026 \
    --resource-group snowflake-course-rg \
    --query connectionString \
    --output tsv)"
```

Add this line to your `~/.bashrc` or `~/.zshrc` so it
persists across shell sessions.

### Step 6 — verify

```bash
az storage account show \
    --name pvsfcourse2026 \
    --resource-group snowflake-course-rg \
    --query "{name:name, location:location, sku:sku.name, kind:kind}"
```

Expected: name `pvsfcourse2026`, location `eastus`, sku
`Standard_LRS`, kind `StorageV2`.

### Naming the storage account

The name becomes part of the URL:

```text
https://pvsfcourse2026.blob.core.windows.net/<container>/<blob>
```

Pick a name that is:

- **Lowercase** (Azure enforces this).
- **Globally unique** across all Azure customers.
- **Memorable** (you'll type it often).
- **Descriptive** (e.g. `pvsfcourse2026` rather than
  `asdf1234`).

A good pattern: `<your-initials><purpose><year>` →
`pvsfcourse2026`.

### Cost in the free tier

- **Storage**: first 5 GB / month free for 12 months.
- **Operations**: 20 000 read + 10 000 write operations
  free / month.
- **Bandwidth**: 100 GB egress / month free.

For our 1 GB orders file and a handful of loads, the
free tier easily covers section 9.

### Common mistakes

- **Wrong region** — re-create the storage account in
  the right region; you can't move it.
- **Premium SKU** — `Premium_LRS` is for high-IOPS
  workloads. Use `Standard_LRS` for analytics.
- **Picking a name with hyphens** — Azure no longer
  allows hyphens; pick a name with letters and digits
  only.

## Hands-on

Run steps 1–6. Confirm the output of step 6 has
`Standard_LRS` and `StorageV2`. Save the connection string
in your shell's environment file.

## Quiz prep

- What is the difference between a resource group and a
  storage account?
- What does `Standard_LRS` mean?
- Why is the storage account name part of the URL?

## Key takeaways

- A storage account is a namespace for all your Azure
  storage (Blob, File, Queue, Table).
- Use `Standard_LRS` and `StorageV2` for analytics
  workloads.
- Set `AZURE_STORAGE_CONNECTION_STRING` to use the
  Azure CLI.
- Resource groups are the cleanup unit — delete the
  group, all resources go with it.

## What's next

In **L70 — Create a container** we create the Blob
container inside the storage account and upload our
orders files.