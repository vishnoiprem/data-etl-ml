---
l_id: L21
title: Data storage & transfer cost
duration: "7:00"
prereqs: ["L20"]
downloads: []
---

# L21 — Data Storage & Transfer Cost

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — Snowflake Architecture
> **Duration:** ~7:00

## Prereqs

L20 — Snowflake pricing. This lecture zooms in on storage and
data transfer billing.

## Key terms

- **Database storage** — storage of all table data, billed
  per compressed TB per month.
- **Stage storage** — files in **internal** (Snowflake-
  managed) stages. Billed separately.
- **Fail-safe storage** — included in database storage; not
  billed separately.
- **Data transfer** — Snowflake-to-non-Snowflake data egress
  (e.g. JDBC results, Snowflake unloading to S3 in another
  region). Billed by the cloud provider.
- **Cross-region / cross-cloud** — Snowflake's internal data
  sharing across regions / clouds does not bill data transfer;
  external transfers do.

## Lecture

Storage is the slower-growing but more predictable of the two
main cost drivers. This lecture covers how storage is metered,
how stage storage is billed, and how to monitor and control
your storage bill.

### What's billed as "storage"

Three categories:

1. **Active database storage** — all table data currently
   active. Billed per average compressed TB per month.
2. **Time Travel storage** — the additional storage for
   historical versions of rows. Billed separately, but only
   when Time Travel is enabled beyond the default 1 day.
3. **Fail-safe storage** — the 7-day disaster-recovery
   window. **Not billed separately** — included in the active
   storage line.

> On-demand pricing example (US, Standard edition):
> - Active storage: ~$23 / compressed TB / month
> - Time Travel beyond 1 day: ~$23 / TB / month

### Stage storage

Internal stages (created with `CREATE STAGE ... DIRECTORY =
(ENABLE = TRUE)`) use Snowflake-managed storage. Files in an
internal stage are billed at the same per-TB rate as database
storage.

External stages (S3, ADLS, GCS) **do not** bill Snowflake
storage — the files live in your cloud account and you pay the
cloud provider directly.

> **Rule.** For large files you'll process repeatedly, use an
> external stage (you already pay for the S3 bucket). For
> small one-off files, an internal stage is fine.

### How compression affects your bill

Snowflake achieves typical compression ratios:

- **Structured CSV** — 5–10×
- **JSON** — 2–4×
- **Parquet** — already compressed; ~1–2× additional
- **Avro** — 1.5–2×

The compression is automatic. A 1 TB CSV loaded into Snowflake
is typically stored at 100–200 GB. Your bill is on the
**compressed** size, not the raw input size.

> **Practical tip.** When estimating storage, divide your raw
> input by 5 (for CSV) to get the rough Snowflake footprint.

### Data transfer costs

Snowflake-to-Snowflake (within the same region) is **free**.
Cross-region or cross-cloud data transfer is billed by the
underlying cloud provider at the cloud's egress rates.

| Transfer | Billed by | Rate (rough) |
|---|---|---|
| Same region, same cloud | Free | $0 |
| Cross-region, same cloud | Cloud provider | $0.02–0.09 / GB |
| Cross-cloud | Cloud provider | $0.05–0.12 / GB |
| Snowflake → external (e.g. JDBC) | Cloud provider | Cloud egress rate |

> **Practical tip.** Place your Snowflake account in the same
> region as your S3 / ADLS / GCS bucket. Cross-region is
> expensive at scale.

### Monitoring storage

```sql
-- Per-database storage usage over the last 30 days
SELECT usage_date,
       database_name,
       average_database_bytes / 1024 / 1024 / 1024 AS avg_gb
FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY
ORDER BY usage_date DESC, database_name;
```

```sql
-- Stage storage usage
SELECT usage_date,
       average_stage_bytes / 1024 / 1024 / 1024 AS avg_gb
FROM SNOWFLAKE.ACCOUNT_USAGE.STAGE_STORAGE_USAGE_HISTORY
ORDER BY usage_date DESC;
```

### Reducing storage cost

1. **Drop unused tables** — `DROP TABLE` is the simplest win.
2. **Shorten Time Travel retention** — set
   `DATA_RETENTION_TIME_IN_DAYS = 1` on tables that don't
   need 90 days.
3. **Convert to transient tables** — transient tables don't
   have Fail-safe (saves 7 days of storage).
4. **Use external stages** for large file archives.
5. **Compress before loading** — load Parquet instead of CSV.

## Hands-on

```sql
-- Total active storage in your account
SELECT SUM(average_database_bytes) / 1024 / 1024 / 1024 AS total_gb
FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY
WHERE usage_date = CURRENT_DATE() - 1;
```

## Quiz prep

- Is Fail-safe storage billed separately? (No — included in
  active storage)
- Where do files in an internal stage live? (Snowflake-
  managed storage; billed at the same rate as database
  storage)
- Is cross-region data transfer free? (No — billed by the
  cloud provider at standard egress rates)

## What's next

Next up is **L22 — Monitor Usage**, where we look at the
account_usage views in detail and build a cost-monitoring
dashboard.
