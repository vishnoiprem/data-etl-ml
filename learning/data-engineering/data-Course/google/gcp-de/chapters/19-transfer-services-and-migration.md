# 4.4 — Transfer Services & Migration

> **Section 4 · Streaming & Ingestion · Lecture 4.4 · 8:00**

## 🎯 What you will learn

- The four migration tools on GCP and the boundary between them
- The **Storage Transfer Service**: jobs, agent pools, transfer specifications, scheduling, and when it beats `gsutil`
- The **BigQuery Data Transfer Service**: transfer configs, supported sources, incremental sync, scheduled transfers
- The **Transfer Appliance**: the physical-ship option, its economics, and the crossover point
- The **Database Migration Service**: connection profiles, migration jobs, the promotion process, minimal downtime
- A decision matrix for moving each kind of data
- The cost model for migration: network egress, the free tier, and the traps that make a migration expensive

---

## 🧠 Concept

### The migration toolbox

GCP gives you four migration tools that overlap and confuse. They are distinguished by **what moves** and **how it moves**:

| Tool | Moves | Mechanism | Managed by |
|---|---|---|---|
| **Storage Transfer Service** | Cloud Storage ↔ Cloud Storage, and cloud ↔ on-prem | Network or agent | Google |
| **BigQuery Data Transfer Service** | SaaS/DB → BigQuery | Scheduled pull, incremental | Google |
| **Transfer Appliance** | Bulk data, any source → Cloud Storage | Physical shipping | Google (you own the device) |
| **Database Migration Service** | Databases → Cloud SQL / AlloyDB | Logical replication | Google |

The mental model that resolves most confusion:

- **Storage Transfer Service** moves *files*. It moves object data.
- **BigQuery DTS** moves *tables*. It lands data in BigQuery, from sources Google can poll.
- **Transfer Appliance** moves *files* too, but physically, when the data is too large or the network too slow.
- **DMS** moves *databases*. It replicates schemas and rows, and can promote to a cutover.

Note that the Storage Transfer Service and the Transfer Appliance both move files to Cloud Storage; the difference is the transport (network vs. physical) and the economics.

### Storage Transfer Service: the architecture

The Storage Transfer Service (STS) moves data into Cloud Storage (and, in some configurations, between regions). It has three components:

- A **transfer job** is the unit of work. It references a transfer specification, a schedule, and notification settings. It has a state machine: `ENABLED`/`DISABLED` → `PENDING` → `RUNNING` → `SUCCEEDED`/`FAILED`.
- A **transfer specification** describes *what* to move: source bucket, destination bucket, a `includePrefixes`/`excludePrefixes` filter, and — crucially — **whether to overwrite objects**.
- An **agent pool** is a set of compute resources that perform the transfer when the source is not directly reachable by Google's network. This is the key to understanding when STS is worth using.

**The agent pool is the whole story.** STS has two modes:

**Server-side (no agent pool).** Google moves the data directly, at Google-internal network speed, with no charge for compute. This applies when the source is a Cloud Storage bucket — including in a different region or even a different cloud provider's bucket via the interoperability API (XML API / `gsutil` interoperability). Speed is excellent: hundreds of MB/s to multiple GB/s. Cost is only the egress from the source (free for Google-internal moves) plus the Cloud Storage write charges.

**Agent-pool-based.** You provision agents — Compute Engine VMs with the transfer agent installed — into your source network. They pull data over your own connection and push it to Cloud Storage. This is for on-premises data, or data behind a firewall. You pay for the agents' compute and network egress.

**That is the decision**: use server-side STS for anything in Google Cloud (even cross-region); use agent pools only when the data is genuinely on-premises and the network path is the constraint.

### When to use STS over `gsutil`

`gsutil cp` and `gcloud storage cp` move objects. STS moves them *as a service*. The differences that matter at scale:

| | `gsutil cp` | Storage Transfer Service |
|---|---|---|
| Speed | One process, one connection per object | Parallel, many connections, many workers |
| Resumability | Restart from scratch | Resumes; the job is stateful |
| Filtering | Shell globbing | Native `includePrefixes` / `excludePrefixes` |
| Scheduling | cron | Native schedule (hourly/daily/weekly) |
| Monitoring | Log files | Console, Cloud Monitoring, notifications |
| Failure handling | Manual | Automatic retries per object |
| Parallelism control | Manual flags | Agent pool sizing |

**The concrete guidance:**

- **Small, one-off transfers (a few GB, a handful of files)** → `gcloud storage cp`. STS is overkill and slower to set up.
- **Large Cloud Storage → Cloud Storage moves** (region migration, a bucket restructure, tens of TB and up) → **STS, server-side**. It is dramatically faster because it runs on Google's internal network with massive parallelism, and it costs the same egress (often less, since internal traffic is free or discounted).
- **On-premises → Cloud Storage** → STS with an agent pool, or `gcloud storage transfer` (the CLI wrapper around STS).
- **Recurring transfers on a schedule** → STS with a scheduled job. Cron + `gsutil` works but you build the retry, notification, and resume logic yourself.

**The most common use of STS on GCP is a region migration.** Moving a bucket from `us` to `us-central1` because of a data residency requirement. `gcloud storage buckets create gs://new --location=us-central1` then `gcloud storage cp --recursive gs://old gs://new` takes hours; the same move via STS server-side takes minutes.

**STS does not delete the source.** This is a feature and a trap: after a migration, the source bucket still exists, still billing, and still holding a second copy of regulated data. Delete it deliberately.

### BigQuery Data Transfer Service: the architecture

BigQuery DTS moves data into BigQuery from sources Google can poll on your behalf. The unit of work is a **transfer config**:

- A transfer config names a **source connector** (a type), a **schedule**, and a **destination dataset**. It has a state machine of its own: `ENABLED`/`DISABLED` → `PENDING` → `RUNNING` → `SUCCEEDED`/`FAILED`.
- Each connector has a set of **parameters** (source connection details, the tables to copy) and a **schema** (the destination tables and their types).
- Transfers are **incremental** by default: after the initial load, the service tracks a high-water mark per table and only copies new or changed rows.

**Supported connectors** (a representative set):

| Category | Connectors |
|---|---|
| Databases | Cloud SQL for MySQL, Cloud SQL for PostgreSQL, Cloud SQL for SQL Server, AlloyDB |
| SaaS | Salesforce, Google Ads, Google Analytics (GA4), Google Ads, HubSpot, Marketo, Shopify, Stripe, Zendesk, ServiceNow, Workday |
| Files | Google Cloud Storage, Google Drive, Google Sheets, Amazon S3, Azure Blob Storage |
| Apps | Jira, Asana, MongoDB, Teradata, Hortonworks, Elastic, Segment |
| Google-native | Google Ads, Google Analytics, Google Sheets, BigQuery (self-to-self) |

**The schedule.** The available cadences are `every 15 minutes`, `hourly`, `daily`, `weekly`, `monthly`, and `manual`. Critically, **the schedule defines when the transfer *starts*, not how long it takes.** A daily transfer that starts at 02:00 and runs for six hours on a large table finishes at 08:00.

**The incremental mechanism.** This is worth understanding properly, because it determines whether your BigQuery table is a mirror or a snapshot:

- For **append-only sources** (Salesforce, Stripe, GA4), DTS appends new rows and never updates or deletes. Your BigQuery table grows forever and can contain rows that were later changed at the source. You need your own merge logic if you want current state.
- For **database sources**, DTS tracks the source's change-tracking mechanism and copies inserts and updates. Whether deletes propagate depends on the connector and the source.
- For **file sources** (S3, GCS), DTS copies files. Incremental behaviour is based on file modification time or a name pattern.

**DTS and Datastream are the same family with different engines.** Datastream is the CDC/streaming engine — it uses the source's log, gives you before/after images, change metadata, and near-real-time delivery. BigQuery DTS is the batch/scheduled engine — it polls, it copies, it lands in BigQuery tables directly. Choose DTS for scheduled batch loads and SaaS connectors; choose Datastream for low-latency CDC.

**DTS versus a Fivetran-style connector** comes down to the same trade-off as in the previous chapter: DTS keeps the data inside your GCP project and bills at BigQuery ingestion rates. A SaaS connector ships your source data to the vendor's infrastructure and writes back into your project — a compliance decision you should make deliberately.

**The failure mode everybody hits.** A transfer config fails at 02:00 because a credential expired, and nothing notices until someone queries the table three days later and finds stale data. DTS supports **scheduled notifications** (email, Pub/Sub, Cloud Logging) on job completion, and **Cloud Monitoring metrics** (`bigquery_dts_transfer_job_count`, `..._bytes_transferred`). Wire the notification to a real alert. A silent failure on a 15-minute schedule can go unnoticed for weeks.

### Transfer Appliance: the physical option

The Transfer Appliance is a rack-mounted, self-contained server (2U, roughly 4 TB of usable storage) that you plug into your source data center, fill with data, and ship to a Google data center. Google ingests it directly into Cloud Storage.

**The economics.** This is the part that decides everything.

The cost is the appliance's **rental** plus **Google's data handling fee**:

- The appliance is rented per month (historically around $200–$400/month depending on configuration) — a one-time-ish cost if you return it.
- Google charges a **data handling fee per GB** to ingest the appliance — historically around $0.02–$0.045/GB depending on region, which is significantly cheaper than **network egress** ($0.12/GB from us-central1 to the internet).

The comparison that matters:

```text
Network egress:  $0.12 / GB
Appliance:       ~$0.03 / GB  + appliance rental amortised
```

Moving 100 TB over the network at egress prices is $12,000. The same 100 TB via appliance is roughly $3,000 in data handling, plus the rental for the months the appliance is in transit. **The crossover is around a few terabytes over a slow or metered link.**

But the real reason to use an appliance is not price — it is **time**. A 100 Mbps link moves 100 TB in about 92 days. A 1 Gbps link moves it in about 9 days. An appliance ships in a week. If your migration deadline is a quarter-end, or your link is 100 Mbps and your dataset is 50 TB, the appliance is the only option that works.

**The modern alternative that changes the decision:** since 2022 Google has offered **Direct Interconnect** and **Cloud Interconnect** at many sites, plus **Transfer Appliance for the smallest sizes** and, more importantly, **Storage Transfer Service running server-side against other clouds' object stores** (S3, Azure Blob) at near-internal-network speeds for many inter-region paths. If your source is another cloud's object store, STS over the interoperability API is usually better than an appliance unless the volume is very large or the egress is expensive.

**The operational burden of an appliance is real and often underestimated:**

- You are responsible for **racking, cabling, and power** in your data centre.
- You must **fill it and ship it yourself** — often to a specific Google data centre with a scheduled appointment.
- You must **return it**, and you are billed until it is received back.
- **The appliance is single-use per dataset.** Moving a second batch means another appliance or another shipment.
- There is a **minimum dataset size** below which it is not worth it.

**The decision rule:**

- Data on-premises, **less than ~1–2 TB**, or a fast link (≥1 Gbps) → **agent-pool STS over the network**. Cheaper, no hardware.
- Data on-premises, **10–100 TB**, slow link, and a deadline → **appliance**.
- Data in **another cloud's object store** → **server-side STS** first; appliance only at very large scale with expensive egress.
- Data moving **continuously** → **Direct Interconnect** — because a recurring shipment model does not fit a recurring data flow.

### Database Migration Service: the architecture

DMS moves an entire database — schema and data — to Cloud SQL, AlloyDB, or a self-managed destination. It has three components:

- A **connection profile** describes the source database: type, host, port, credentials, and the network path. It is reusable.
- A **migration job** references a connection profile and a destination, and carries a **migration spec** that defines what to migrate: the databases, the tables to include or exclude, and the **CDC** (change data capture) settings.
- The **promotion** step is the cutover.

**The migration job has two phases, and this is the key mental model:**

1. **One-time (full load) phase.** DMS reads the schema and copies the existing data. For a consistent copy of a live database, it uses a technique similar to Datastream's: take a consistent snapshot position and buffer concurrent changes.
2. **Continuous (CDC) phase.** After the initial copy, DMS sets up log-based CDC and replicates every subsequent change to the destination, keeping it continuously in sync.

**The promotion process** is the cutover, and it must be planned:

1. **Stop writes to the source** (or throttle them). This is the downtime window.
2. **Wait for CDC to drain** the remaining changes to the destination.
3. **Promote**: DMS switches the job from replication to promoted state and validates.
4. **Repoint the application** to the destination.
5. Optionally, **demote the source** so you can reverse the cutover if something is wrong — this is a safety net that costs you nothing during the operation but saves you from a bad rollback plan.

The downtime window is roughly the time it takes to drain the CDC lag after writes stop — usually seconds to a couple of minutes for a moderate workload. **The dominant cost of a DMS migration is not the downtime; it is the application cutover.** Your application must reconnect, DNS must change, connection pools must reset, and caches must be invalidated. Plan that as a separate workstream.

**Minimal downtime is a first-class goal.** DMS supports:
- **Near-zero downtime migration** — CDC keeps the destination current until you cut over.
- **Continuous migration** — running for months as a steady-state replication, with promotion whenever you choose.
- **A "test the migration" rehearsal** — run a full migration to a scratch destination, measure the actual CDC lag and the real cutover duration, then delete it and run the real one. **Always do this.** The rehearsal is the only way to know your real downtime.

**The prerequisites that break migrations:**

- The source must have **binary logging / CDC enabled** and the right privileges (`REPLICATION SLAVE`, `REPLICATION CLIENT`, `SELECT` for MySQL; `REPLICATION` for PostgreSQL).
- **The source must be reachable** from the DMS workers — via public IP with allowlisting, Private Service Connect, or the DMS proxy.
- **Foreign keys and triggers complicate the full load.** DMS handles them but the ordering matters; expect to disable triggers and re-enable them if you hit constraint violations.
- **Character set and collation mismatches** cause silent data corruption on non-ASCII text. Verify `utf8mb4` end to end.
- **The destination Cloud SQL instance must have enough disk and IOPS** for the initial load. A 2 TB dataset into a db-n1-standard-1 will take days.

**DMS versus Datastream for a database you are also streaming.** You may want both: DMS for the one-time migration with cutover, and Datastream for the ongoing CDC into your analytics platform. They are complementary, not alternatives. But note that both create replication slots on the source, so check `max_replication_slots` before running both.

### The cost model for migration

Migration cost is dominated by three things, and people reliably forget the third:

1. **Egress from the source.** $0.12/GB from us-central1 to the internet. For a source that is *not* Google Cloud, this is your bill. 50 TB = $6,144.
2. **The destination's ingest and storage.** BigQuery ingestion, Cloud Storage writes, Cloud SQL storage and compute.
3. **The compute to move it.** Agent pools (STS), the Dataflow/Compute job (DMS full load), or the appliance rental.

And one that everybody misses:

4. **The cost of the migration you have to do again.** A failed migration is charged twice. This is the strongest argument for the rehearsal.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import NETWORK_EGRESS_PER_GB

TB = 1024.0
APPLIANCE_PER_GB = 0.03
APPLIANCE_RENTAL = 400.0

for tb in (1, 10, 50, 100):
    gb = tb * TB
    network = gb * NETWORK_EGRESS_PER_GB
    appliance = gb * APPLIANCE_PER_GB + APPLIANCE_RENTAL
    winner = "appliance wins" if appliance < network else "network wins"
    print(f"{tb:>4} TB  network ${network:>10,.0f}   appliance ${appliance:>10,.0f}   {winner}")
```

Expected output:

```text
   1 TB  network $       123   appliance $       431   network wins
  10 TB  network $     1,229   appliance $       707   appliance wins
  50 TB  network $     6,144   appliance $     1,936   appliance wins
 100 TB  network $    12,288   appliance $     3,472   appliance wins
```

This is egress and appliance handling only; add the destination's own ingest and storage charges on top. The crossover is dominated by egress, which is why the appliance wins as soon as the dataset passes a few terabytes.

### The decision matrix

| You want to move | Tool | Why |
|---|---|---|
| A GCS bucket to another region | **STS, server-side** | Free internal network, resumable, scheduled |
| A GCS bucket to another cloud | **STS server-side** over the interoperability API | Cheaper than pulling it down yourself |
| On-prem NAS/SAN → GCS, < 2 TB | **STS + agent pool** | No hardware, no shipping |
| On-prem → GCS, 10–100 TB, slow link, deadline | **Transfer Appliance** | Weeks instead of months |
| Continuous on-prem → GCS at volume | **Direct Interconnect** | A recurring flow is not a shipment |
| SaaS (Salesforce, Stripe, GA4) → BigQuery | **BigQuery DTS** | Incremental, scheduled, no connector to run |
| A database → BigQuery, near-real-time | **Datastream** | Log-based CDC with before/after images |
| A database → BigQuery, scheduled | **BigQuery DTS** | Simpler than Datastream, lands directly |
| A database → Cloud SQL/AlloyDB with cutover | **DMS** | Full load + CDC + promotion |
| A very large one-off on-prem dump → GCS, network too slow | **Transfer Appliance** | Shipping beats waiting |

**The three questions that settle it:**

1. **Is it files or rows?** Files → STS or the appliance. Rows → DTS, Datastream, or DMS.
2. **Can Google reach it directly?** Yes → server-side, no compute to pay for. No → agent pool, or DMS with a proxy.
3. **Does the destination need a cutover, or is a copy fine?** A copy → DTS or STS. A cutover → DMS, because only DMS can promote.

---

## 🛠️ Hands-On

### Lab 1 — Map a migration to the right tool

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service, services_by_category

for service_id in ("cloud-storage", "bigquery", "bigquery-transfer",
                   "database-migration", "storage-transfer"):
    try:
        service = get_service(service_id)
    except KeyError:
        print(f"{service_id}: NOT IN CATALOG")
        continue
    print(f"{service.id}: {service.name}")
    print(f"  summary : {service.summary}")
    print(f"  pricing : {service.pricing_model}")
    print(f"  resources: {', '.join(service.key_resources)}")
    print()
```

Expected output:

```text
cloud-storage: Cloud Storage
  summary : Durable object storage for raw and staged data.
  pricing : Per GB stored per month, plus per-class retrieval.
  resources: Bucket, Object, Lifecycle Rule, IAM Policy

bigquery: BigQuery
  summary : Serverless, columnar analytical warehouse.
  pricing : Per TB scanned, or flat-rate capacity by slot-hour.
  resources: Project, Dataset, Table, View, Materialized View

bigquery-transfer: BigQuery Data Transfer Service
  summary : Scheduled load of external sources into BigQuery.
  pricing : Free; you pay the BigQuery query and storage charges.
  resources: Transfer Config, Transfer Run, Schedule

database-migration: Database Migration Service
  summary : Self-service, low-downtime migration to Cloud SQL.
  pricing : Per connection-hour during the migration only.
  resources: Connection Profile, Migration Job, Source Database

storage-transfer: Storage Transfer Service
  summary : Scheduled bulk transfer of object storage data.
  pricing : Free; you pay the source and destination charges.
  resources: Job, Transfer Job, Agent, Notification
```

### Lab 2 — The egress-versus-appliance crossover

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import NETWORK_EGRESS_PER_GB

APPLIANCE_PER_GB = 0.03
APPLIANCE_RENTAL = 400.0
TB = 1024.0

print(f"{'dataset':>10} {'network egress':>16} {'appliance':>14} {'winner':>10}")
for tb in (0.5, 1, 2, 5, 10, 25, 50, 100):
    gb = tb * TB
    network = gb * NETWORK_EGRESS_PER_GB
    appliance = gb * APPLIANCE_PER_GB + APPLIANCE_RENTAL
    winner = "appliance" if appliance < network else "network"
    print(f"{tb:>9} TB ${network:>10,.0f}   ${appliance:>8,.0f}   {winner:>8}")

# Time-to-migrate, the reason the appliance exists at all.
DATASET_TB = 50
bytes_total = DATASET_TB * TB * 1024 * 1024 * 1024
for mbps in (100, 1000, 10000):
    seconds = (bytes_total * 8) / (mbps * 1_000_000)
    print(f"{DATASET_TB} TB over {mbps:>5} Mbps: {seconds / 86400:>6.1f} days")
print(f"{DATASET_TB} TB via appliance: ~7 days (ship + ingest)")
```

Expected output:

```text
   dataset   network egress      appliance     winner
      0.5 TB $        61   $     415    network
        1 TB $       123   $     431    network
        2 TB $       246   $     461    network
        5 TB $       614   $     554   appliance
       10 TB $     1,229   $     707   appliance
       25 TB $     3,072   $   1,168   appliance
       50 TB $     6,144   $   1,936   appliance
      100 TB $    12,288   $   3,472   appliance
50 TB over   100 Mbps:   50.9 days
50 TB over  1000 Mbps:    5.1 days
50 TB over 10000 Mbps:    0.5 days
50 TB via appliance: ~7 days (ship + ingest)
```

Note the crossover lands between 2 and 5 TB, and the network at 100 Mbps would take 51 days — which is *why* the appliance is chosen, independent of price.

### Lab 3 — Model the BigQuery DTS incremental schedule

```python
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class TransferRun:
    started: datetime
    finished: datetime
    rows: int
    bytes_: int
    status: str

    @property
    def duration_minutes(self) -> int:
        return int((self.finished - self.started).total_seconds() // 60)


def run_dts_daily(start: datetime, table_rows: int, minutes_per_million: float) -> list[TransferRun]:
    """A daily incremental copy: only new rows after the first run."""
    runs: list[TransferRun] = []
    high_water = 0
    for day in range(5):
        # A growing table: 1M new rows per day after the initial load.
        new_rows = table_rows if day == 0 else 1_000_000
        duration = int(new_rows / 1_000_000 * minutes_per_million)
        finished = start + timedelta(days=day, minutes=duration)
        runs.append(TransferRun(start + timedelta(days=day), finished, new_rows,
                                new_rows * 250, "SUCCEEDED"))
        high_water += new_rows
    return runs


runs = run_dts_daily(datetime(2026, 1, 15, 2, 0), table_rows=10_000_000, minutes_per_million=4.0)
total_rows = 0
for run in runs:
    total_rows += run.rows
    print(f"{run.started:%Y-%m-%d %H:%M} start -> {run.finished:%H:%M} finish "
          f"({run.duration_minutes:>3} min, {run.rows:>10,} rows, {run.bytes_ / 1e9:>6.2f} GB)")

print(f"\ntotal rows copied: {total_rows:,}")
print("day 1 = full load; days 2-5 = incremental (1M new rows each)")
```

Expected output:

```text
2026-01-15 02:00 start -> 02:40 finish ( 40 min, 10,000,000 rows,   2.50 GB)
2026-01-16 02:00 start -> 02:04 finish (  4 min,  1,000,000 rows,   0.25 GB)
2026-01-17 02:00 start -> 02:04 finish (  4 min,  1,000,000 rows,   0.25 GB)
2026-01-18 02:00 start -> 02:04 finish (  4 min,  1,000,000 rows,   0.25 GB)
2026-01-19 02:00 start -> 02:04 finish (  4 min,  1,000,000 rows,   0.25 GB)

total rows copied: 14,000,000
day 1 = full load; days 2-5 = incremental (1M new rows each)
```

The important property: **the schedule fixes the start time, not the finish time**. A 15-minute schedule on a table that takes 40 minutes to copy will overlap itself.

### Lab 4 — Model the DMS cutover window

```python
from dataclasses import dataclass


@dataclass
class Migration:
    table_rows: int
    cdc_rows_per_second: int
    writes_at_cutover: int  # writes that land between "stop writes" and "drain"


def cutover_downtime(rows: int, cdc_rate: int) -> float:
    """Seconds of downtime once writes are stopped."""
    return rows / cdc_rate


def total_migration_hours(table_rows: int, load_rows_per_second: int,
                           cdc_rate: int, lag_at_stop: int) -> float:
    full_load_hours = table_rows / load_rows_per_second / 3600
    downtime = cutover_downtime(lag_at_stop, cdc_rate)
    return full_load_hours + downtime / 3600


print(f"{'table rows':>12} {'load hours':>11} {'downtime (s)':>14}")
for rows in (100_000, 1_000_000, 10_000_000, 100_000_000):
    load = rows / 50_000          # full load at 50k rows/s
    lag = 20_000                  # 20k changes pending when writes stop
    print(f"{rows:>12,} {load / 3600:>10.2f}h {cutover_downtime(lag, cdc_rate=2000):>13.1f}s")

print()
print("Downtime is set by CDC LAG AT THE MOMENT WRITES STOP, not table size.")
print("A 100M-row table can have a 10-second cutover if CDC is caught up.")
```

Expected output:

```text
  table rows  load hours   downtime (s)
     100,000       0.00h          10.0s
   1,000,000       0.01h          10.0s
  10,000,000       0.06h          10.0s
 100,000,000       0.56h          10.0s

Downtime is set by CDC LAG AT THE MOMENT WRITES STOP, not table size.
A 100M-row table can have a 10-second cutover if CDC is caught up.
```

This is the key insight: the full load time is hours or days, but the **downtime** is only the drain of the CDC lag — often seconds. That is the whole point of DMS.

### Lab 5 — Price the whole platform after a migration

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate

# After migrating 20 TB into Cloud Storage and 500 GB into BigQuery.
storage_gb = 20 * 1024

ingest = estimate("bigquery", scanned_tb=0.5, monthly=False, apply_free_tier=False)
storage = estimate("cloud-storage", storage_gb=storage_gb, monthly=True,
                   apply_free_tier=False)

print("One-time migration costs:")
print(f"  BigQuery ingest (500 GB): ${ingest.total:,.2f}")
print()
print("Recurring costs after the migration:")
for line in storage.lines:
    print(f"  {line.label:<22} {line.quantity:>12,.0f} {line.unit:<10} ${line.cost:>10,.2f}")
print(f"  {'TOTAL / month':<22} {'':>12} {'':<10} ${storage.total:>10,.2f}")
print()
print("The recurring cost dwarfs the one-time ingest. Storage dominates, not the move.")
```

Expected output:

```text
One-time migration costs:
  BigQuery ingest (500 GB): $3.12

Recurring costs after the migration:
  Storage                      20,480 GB-month   $    409.60
  TOTAL / month                                  $    409.60

The recurring cost dwarfs the one-time ingest. Storage dominates, not the move.
```

### Lab 6 — Check the transfer-service availability

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import REGIONS, get_service, regions_for

for service_id in ("storage-transfer", "bigquery-transfer", "database-migration"):
    service = get_service(service_id)
    available = regions_for(service_id)
    print(f"{service.name}: {len(available)}/{len(REGIONS)} regions")
    missing = [r for r in REGIONS if r not in available]
    if missing:
        print(f"  not in: {', '.join(missing)}")
    print()
```

Expected output:

```text
Storage Transfer Service: 12/12 regions

BigQuery Data Transfer Service: 12/12 regions

Database Migration Service: 12/12 regions
```

All three are available in all twelve course regions, which is why the chapter's examples do not need region-specific handling.

---

## 🛠️ Common Errors and Fixes

### 1. STS job fails with `PERMISSION_DENIED` writing to the destination bucket

```text
ERROR: (gcloud.storage.transfer.jobs.create) INVALID_ARGUMENT:
Access denied to destination bucket gs://target-bucket. The caller
does not have storage.buckets.get permission.
```

**Cause:** the service account creating the transfer job lacks the Storage roles on the destination bucket. STS needs `storage.objects.create`, `storage.objects.delete` (if deleting source objects), and `storage.buckets.get`.

**Fix:** grant `roles/storage.objectAdmin` on the destination bucket (scoped, not project-wide).

```bash
gcloud storage buckets add-iam-policy-binding gs://target-bucket \
  --member=serviceAccount:sts-runner@my-project.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

### 2. `INVALID_ARGUMENT: The source and destination objects have the same name and generation` / `PreconditionFailed`

```text
ERROR: (gcloud.storage.transfer.jobs.create) INVALID_ARGUMENT:
Invalid transfer specification: `overwriteObjectsWhenFull` is set to
true but the source object already exists in the destination.
```

**Cause:** the transfer specification sets `overwriteObjectsWhenFull: true` and the destination already contains objects with the same names. The STS precondition check fails for objects that already exist with the same generation.

**Fix:** choose the behaviour deliberately. For a fresh migration, set `overwriteObjectsWhenFull: false` so existing objects are skipped. For a re-sync, keep it true and use a distinct destination prefix.

```bash
gcloud storage transfer jobs create my-job \
  --source-bucket=gs://source-bucket \
  --dest-bucket=gs://target-bucket \
  --include-prefixes=raw/ \
  --overwrite-objects-when-full=NEVER
```

### 3. BigQuery DTS: `Could not fetch source schema`

```text
ERROR: (gcloud bigquery data-transfers create) INVALID_ARGUMENT:
Could not fetch source schema: Table 'shop.orders' does not exist or
the credentials do not have permission to read it.
```

**Cause:** the BigQuery DTS service account cannot reach or read the source. For Cloud SQL sources, the service account needs the Cloud SQL Client role and a private IP path; for SaaS sources, the OAuth refresh token has expired or lacks the required scopes.

**Fix:** grant the source-side permissions and verify network reachability. For Cloud SQL, the DTS service agent needs `roles/cloudsql.client` and a connection over Private Service Connect or public IP with allowlisting.

```bash
gcloud projects add-iam-policy-binding my-project \
  --member=serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-bigquerydatatransfer.iam.gserviceaccount.com \
  --role=roles/cloudsql.client
```

### 4. BigQuery DTS job fails with `Invalid credentials` / `401 Unauthorized`

```text
ERROR: (gcloud bigquery data-transfers update) INVALID_ARGUMENT:
Invalid refresh token.
```

**Cause:** the OAuth token for a SaaS connector has expired or been revoked. This is the single most common BigQuery DTS failure, and it happens silently until the next scheduled run.

**Fix:** re-authenticate the source connection and, critically, **alert on job failure** so you find out before a stakeholder queries stale data.

```bash
gcloud bigquery data-transfers update TRANSFER_CONFIG_ID \
  --refresh-token="<new-token>" \
  --project=my-project

# Wire the failure notification
gcloud bigquery data-transfers update TRANSFER_CONFIG_ID \
  --notification-config \
    --send-push \
    --email-address=data-ops@example.com
```

### 5. DMS: `Failed to connect to the source database` / `Public Key Authentication failed`

```text
ERROR: (gcloud database-migration migration-jobs create) INVALID_ARGUMENT:
Failed to connect to the source database: could not connect to server:
Connection refused (publickey authentication failed).
```

**Cause:** the source requires public-key authentication and the connection profile has no public key; or the source is not allowlisted for the DMS workers' IP addresses; or the source's CDC prerequisites (binary logging, replication privileges) are not met.

**Fix:** provide the public key in the connection profile, allowlist the DMS worker IPs, and verify the source's replication settings before creating the job.

```bash
gcloud database-migration connection-profiles describe my-cp \
  --region=us-central1 --format="yaml"
```

```sql
-- MySQL prerequisites
SHOW VARIABLES LIKE 'log_bin';
SHOW VARIABLES LIKE 'binlog_format';        -- must be ROW
SHOW VARIABLES LIKE 'binlog_row_image';     -- must be FULL
GRANT REPLICATION SLAVE, REPLICATION CLIENT, SELECT ON *.* TO 'dms_user'@'%';
```

### 6. DMS full load fails with foreign key constraint violations

```text
ERROR: (gcloud database-migration migration-jobs describe) FAILED:
Table 'shop.order_items' failed to load. Cannot add or update a child
row: a foreign key constraint fails (`shop`.`orders`, CONSTRAINT
`fk_order_items_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`))
```

**Cause:** DMS loads tables in a dependency order that does not satisfy your foreign keys, often because the referenced table was loaded with fewer rows (data still in the CDC phase) or because a table was excluded from the migration spec.

**Fix:** exclude the child tables from the full load and let CDC populate them, or ensure the parent tables are fully loaded first. Also check for tables excluded from the migration spec that the child depends on.

```bash
gcloud database-migration migration-jobs describe my-job \
  --region=us-central1 --format="value(migrationSpec.sourceObjects)"
```

### 7. Transfer Appliance: `Device not recognized` / shipment rejected at intake

**Cause:** the appliance was not properly decommissioned, the device seal was broken, or it arrived outside the scheduled intake window at the assigned data centre.

**Fix:** follow the decommissioning procedure exactly (ship the appliance with the return label, erase the drives, include the signed form), and confirm the intake appointment. Google charges for the appliance rental **until the device is received and processed**, so a rejected shipment keeps billing.

---

## 💡 Production Notes

- **Use server-side STS for anything already in Google Cloud**, even across regions or clouds. It runs on Google's internal network with massive parallelism, is resumable, and costs less than pulling the data down through your own network. The crossover versus `gsutil` is at a few GB and a few hundred objects.

- **The Storage Transfer Service does not delete the source.** After a migration, you have two copies of regulated data, two storage bills, and two sets of access-control obligations. Delete the source deliberately, and verify the bucket is actually empty first.

- **Size the agent pool for the link, not for the data.** An agent pool that saturates your 1 Gbps uplink will degrade every other system on the same network. Measure the available bandwidth, divide by the per-agent throughput, and cap the pool.

- **Alert on BigQuery DTS job failures.** Expired OAuth tokens are the most common DTS failure and they are silent. Wire the scheduled notification and a Cloud Monitoring alert on `bigquery_dts_transfer_job_count` filtered to `failed`. A stale table nobody noticed is worse than a failed job everyone saw.

- **Remember that DTS schedules fix the start time, not the finish time.** A 15-minute schedule on a table that takes 40 minutes to copy will overlap itself. Measure your real copy duration and set the schedule above it.

- **Always rehearse a DMS migration against a scratch destination.** The rehearsal is the only way to learn your real CDC lag and real cutover duration. It also confirms the privileges, the character set, and the downstream application behaviour before you point production at it.

- **DMS downtime is CDC drain time, not table size.** Stop writes, drain the lag, promote, repoint. Measure the lag at the moment writes stop — that is your downtime budget. The application cutover, not the data copy, is what actually takes time.

- **Use the demote-then-promote path for a reversible cutover.** Keeping the source demoted for a defined window gives you a rollback that costs nothing during the operation. Decide the rollback criteria and the deadline in advance, before the cutover starts.

- **Price the steady state, not just the move.** A 20 TB migration that lands in Cloud Storage Standard costs $409.60/month forever, which dwarfs the one-time ingest cost. Apply a lifecycle rule on day one, and check whether the data needs a colder class after the migration settles.

---

## 🔑 Key Takeaways

- Four tools, one boundary: **STS and the Appliance move files; BigQuery DTS and Datastream move rows; DMS moves whole databases.**
- **Server-side STS is the default for anything in Google Cloud** — internal network speed, resumable, cheaper than your own egress. Agent pools are for genuinely on-premises sources.
- **The agent pool exists for network reachability, not for speed.** Use it when Google cannot reach the source, not because you want more parallelism.
- **STS never deletes the source.** After a migration, delete the source bucket deliberately.
- **BigQuery DTS is scheduled and incremental.** The schedule fixes the start time; copies take as long as they take. SaaS connectors append without updating, so current state needs your own merge logic.
- **BigQuery DTS keeps your data in-project**; a Fivetran-style connector ships it to a third party and back — a compliance decision before a technical one.
- **The Transfer Appliance wins on time, not just price.** The crossover is around 3–5 TB over a metered link, but the deciding factor is that 50 TB over 100 Mbps takes 47 days and ships in a week.
- **DMS downtime is CDC drain time, not table size.** The full load takes hours; the cutover takes seconds. The application repoint is the real work.
- **Rehearse every DMS migration.** Expired credentials, wrong privileges, character-set mismatches, and foreign keys all surface in the rehearsal instead of at 02:00 on cutover night.
- **The recurring cost of where the data lands dwarfs the cost of moving it.** 20 TB in Cloud Storage Standard is $409.60/month — 130× the one-time BigQuery ingest. Apply lifecycle rules on day one.

---

## 📚 Practice Exercises

1. **Tool selection.** For each scenario, name the tool and justify it against at least two alternatives: (a) a 30 TB on-prem backup archive that must land in `us-central1` within three weeks over a 200 Mbps link, (b) a nightly copy of a self-hosted PostgreSQL into BigQuery, (c) a 60 TB bucket moving from `us` to `us-central1` for residency, (d) a Salesforce instance synced hourly into BigQuery, (e) a 500 GB MySQL server moving to Cloud SQL with a 5-minute downtime budget.

2. **STS vs `gsutil` benchmark.** Write a script that times the same transfer using `gcloud storage cp --recursive` and (conceptually) an STS job, for datasets of 1 GB, 50 GB, and 1 TB, accounting for object count. Predict where the crossover is and explain why the gap widens with object count rather than byte count.

3. **Agent pool sizing.** Given a 1 Gbps uplink, an agent sustaining 200 Mbps, and a requirement to complete a 10 TB transfer in 48 hours, compute the required agent count. Then explain what happens to your production network when 20 agents saturate the link, and propose a throttle strategy.

4. **DTS schedule design.** Using the Lab 3 model, determine the minimum safe schedule interval for a table growing by 2M rows/day where a copy takes 35 minutes at the observed rate. Show the overlap if the schedule is 15 minutes, and specify the configuration that avoids it.

5. **DTS failure-mode matrix.** List every way a BigQuery DTS job can fail (expired token, schema drift, source unavailable, quota, deleted source table). For each, specify the detection mechanism (metric, notification, or query) and the remediation.

6. **DMS rehearsal plan.** Write a rehearsal runbook for a 2 TB PostgreSQL → Cloud SQL for PostgreSQL migration: pre-flight checks, prerequisites to verify, the migration commands, the validation queries, the measured cutover duration, and the rollback procedure.

7. **Appliance economics.** Model 30 TB in three scenarios — 500 Mbps link, 1 Gbps link, and a link with $0.08/GB transit egress. Compute total cost and elapsed time for the appliance versus the agent-pool network transfer, and produce a recommendation with the assumptions stated.

8. **Migration cost model.** Use `cost_model` to build a full migration budget for: 50 TB → Cloud Storage, 500 GB → BigQuery, and a one-month BigQuery DTS run, including egress, storage, ingest, and the DTS compute. Then model the same migration repeated twice (a failed attempt plus a successful one) and show the multiplier on the total.

---

## 📖 Further Reading

- [Storage Transfer Service Documentation](https://docs.cloud.google.com/storage-transfer/docs)
- [Storage Transfer Service — Agent Pools](https://docs.cloud.google.com/storage-transfer/docs/on-prem-agent-pools)
- [BigQuery Data Transfer Service Documentation](https://docs.cloud.google.com/bigquery/docs/dts-introduction)
- [BigQuery DTS — Supported Sources and Connectors](https://docs.cloud.google.com/bigquery/docs/dts-data-sources-intro)
- [Transfer Appliance Documentation](https://docs.cloud.google.com/transfer-appliance/docs)
- [Database Migration Service Documentation](https://docs.cloud.google.com/database-migration/docs)
- [DMS — Managing Migration Jobs](https://docs.cloud.google.com/database-migration/docs/manage-jobs)
- [Direct Interconnect Documentation](https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/overview)
