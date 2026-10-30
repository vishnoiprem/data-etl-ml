# 2.3 — Cloud SQL

> **Section 2 · Storage & Databases · Lecture 2.3 · 8:00**

## 🎯 What you will learn

- What Cloud SQL actually manages for you, and what it deliberately does not
- The three engines — PostgreSQL, MySQL, SQL Server — and the version compatibility model
- Instance creation end to end, including the settings that are irreversible
- Connecting: the Cloud SQL Auth Proxy, the connectors, and why you never expose a public IP
- Authorized networks vs private IP (Private Service Access) — and why the public IP is a trap
- High availability: the standby instance, the failover mechanism, and what actually fails over
- Backups, point-in-time recovery, and the difference between them
- Import/export: `gcloud sql export` to Cloud Storage, `gcloud sql import` back
- The console's query editor, and the Cloud SQL language connectors for BigQuery
- Pricing: vCPU-hour, storage, egress, and backup retention
- Cloud SQL's role in the reference architecture: an OLTP source feeding a warehouse

---

## 🧠 Concept

### What Cloud SQL is

Cloud SQL is a **managed relational database service**. "Managed" means Google operates the infrastructure beneath the database: the virtual machine(s), the disk, the replication, the failover, the backup schedule, the patching, and the monitoring. It does **not** mean Google operates the database — you still get a full PostgreSQL, MySQL, or SQL Server server with root/superuser access, your own schemas, your own extensions, your own `pg_hba.conf`, and full responsibility for query performance.

The boundary matters. Compare:

| You manage (Cloud SQL) | Google manages (Cloud SQL) | You do **not** manage |
|---|---|---|
| Schema, indexes, queries | The VM and its OS | Failover behaviour |
| Users, grants, extensions | Disk provisioning and IOPS | Backup schedule and retention |
| Replication to read replicas | Point-in-time recovery windows | OS patching and maintenance windows |
| Connection pooling | Monitoring and metrics export | Replica promotion |

The line is: **Cloud SQL manages the substrate, you manage the data.** Compare that with Cloud Spanner (chapter 2.4), where Google also manages the schema's *distribution* — splitting, rebalancing, and cross-region replication are entirely Google's problem. And compare with Compute Engine, where you manage the VM, the disk, the failover and the backup yourself. Cloud SQL sits in the middle, and it is the right default for most OLTP workloads.

### Engines and versions

Cloud SQL supports three engines:

| Engine | Default versions | Notable extension points |
|---|---|---|
| PostgreSQL | 14, 15, 16, 17 | PostGIS, `pgcrypto`, `pg_trgm`, `pgvector`, `postgres_fdw`, `Cloud SQL Auth Proxy` support |
| MySQL | 8.0, 8.4 | MySQL 8 features, `google-cloud-spanner` proxy compatibility |
| SQL Server | 2019, 2022 | `sql-server-analytics` for CDC and Synapse |

The version model is: **you choose a major version at instance creation and can upgrade in place.** Upgrading a major version (PostgreSQL 14 → 16) is a one-way operation that creates a clone, upgrades the clone, and — if it passes validation — makes it the new primary. You cannot downgrade. Upgrading a minor version (14.5 → 14.9) happens automatically during a maintenance window, and is not reversible.

Every Cloud SQL instance also has **flags** — engine-specific configuration parameters — and Cloud SQL ships a set of **supported flags** you can set at creation. Some flags are `RESTART` (take effect on next instance restart), some `DYNAMIC` (take effect immediately). You cannot set arbitrary flags; only the supported list.

### The settings that are irreversible

These are the ones to get right on the first `gcloud sql instances create`, because changing them later means a dump-and-restore migration:

- **Engine and version.** Cannot change the engine. Cannot downgrade the version.
- **Region.** Cannot change the region. Moving means dump → restore into a new instance.
- **Zone / zone placement.** With HA, you pick a primary zone in the region; the standby goes in another zone.
- **Private IP vs public IP.** Whether the instance has a private IP address is fixed at creation. You can add a public IP later, and you can delete a public IP later, but an instance created *with* a public IPv4 address always has one unless you remove it.
- **Backup configuration.** You can enable backups later, but you cannot retroactively recover the period before backups started.
- **Data disk size and type.** You can grow the disk (up to the engine's max) but you cannot shrink it. You can change the disk type between PD-SSD and PD-HDD.

### Connecting: the Auth Proxy

Three connection paths exist, and you should be able to say which to use for what:

1. **Unix socket (Cloud SQL Auth Proxy)** — the proxy runs on the client machine, listens on a local port, and forwards to the instance over a secure channel. The application connects to `127.0.0.1:5432` with the proxy's ephemeral credentials. This is the recommended path for anything running on a VM, in Cloud Shell, or on your laptop.
2. **Private IP (Private Service Access)** — the instance has an internal address reachable over the VPC. You still connect through the Auth Proxy, but the proxy uses the private path. This is the production path for GKE, GCE, and anything inside the VPC.
3. **Public IP** — the instance is exposed to the internet with authorised networks. You still connect through the Auth Proxy. This is for when you genuinely have no VPC path (a laptop on a home network, a partner).

The critical point: **the Auth Proxy is not just a convenience, it is the security boundary.** The proxy handles IAM-based authentication (via Application Default Credentials), TLS termination, and connection encryption. When you use the proxy, the database user in your connection string can be a plain `postgres` user and the *identity* is the IAM principal, not the database password. That is how Cloud SQL Auth integrates with IAM: you grant `roles/cloudsql.client` to a service account and connect as that service account's email with no password at all.

```text
Application ──► Auth Proxy (127.0.0.1:5432) ──► Cloud SQL instance
                  │
                  └── authenticates with IAM using ADC
```

The mechanism is worth understanding because it explains several behaviours:

- The proxy must be running before the application starts. In Kubernetes that is a sidecar container.
- The proxy re-authenticates when its credentials refresh; a long-lived proxy keeps working across token rotations.
- The proxy chooses the IP family (IPv4 or IPv6) automatically, so it is the mechanism that makes IPv6-only clients work.
- If the proxy cannot reach the instance, the application sees a connection refused on localhost — **not** a database error. This is why "connection refused on 127.0.0.1" almost always means "the proxy is not running", not "the database is down".

### Authorized networks vs private IP

Two mechanisms control who can reach the instance.

**Authorized networks** are a list of CIDR ranges. A connection from an address inside an authorised range may proceed. This is the public-IP access control. The default is `0.0.0.0/0` — **all IPv4 addresses on the internet** — with the caveat that the instance still requires a valid credential. That default is a terrible idea and you should change it on day one.

**Private Service Access (PSA)** gives the instance an internal IP from a reserved range in your VPC, via a VPC peering. The instance is then unreachable from the internet at all. This is the production answer for anything in the VPC.

The relationship is: **private IP does not use authorised networks at all.** The authorised-networks list only governs the public IP path. Setting an authorised network of `0.0.0.0/0` on a private-IP instance has no effect on the private path.

### High availability

Cloud SQL HA means **a standby instance in a different zone of the same region**, kept in synchronous replication, with automatic failover.

The mechanism:

- The primary runs in zone A (or the region for a regional HA setup). The standby runs in zone B.
- Google controls the replication between them. The replication is **synchronous to the standby** — this is why HA has a write-latency penalty: every acknowledged commit has reached the standby.
- When the primary becomes unavailable, Cloud SQL promotes the standby. The promotion is automatic.
- The old primary, when it comes back, is demoted and re-cloned from the new primary (not merged) — it is a replica, not a peer.

Two flavours:

| Configuration | Layout | Behaviour |
|---|---|---|
| Regional HA | Standby in another zone of the same region | Fast failover (tens of seconds), survives a zone outage |
| Multi-region HA | Standby in another region, asynchronous | Survives a regional outage; failover is slower and can lose the last few transactions |

The write-latency penalty of regional HA is usually 1–2 ms of added latency per commit. For an OLTP database doing thousands of writes per second, that is a real cost. It is still almost always worth it: the alternative is an outage.

**Read replicas** are a separate thing: additional read-only instances, in the same or another region, asynchronously replicated. They scale read throughput (reporting queries, read-your-writes offload) and are the usual answer for "the analytics workload is hurting the OLTP workload".

### Backups versus point-in-time recovery

These are two different recovery mechanisms and people conflate them constantly.

**Automated backups** are full backups taken on a schedule (daily by default, retained 7 backups by default, configurable up to 365 backups). They can be **on-demand** (manual, "create backup") and support **transaction log archiving** for continuous recovery. A backup is a restorable copy of the instance at a point in time.

**Point-in-time recovery (PITR)** is not a backup at all. It is the **continuous archiving of transaction logs**, which means you can restore the instance to *any* moment within the retention window — not just to a backup boundary. PITR granularity is effectively the transaction.

That difference matters for RPO. With daily backups and no log archiving, your worst-case data loss on a restore is 24 hours. With transaction log archiving enabled, your worst-case data loss is the last transaction.

The backup retention window also determines how far back PITR can go. Setting the retention to 7 days gives you 7 days of PITR. Backups and PITR share the window.

There is a third option for large instances: **export-based recovery**, where you take a dump to Cloud Storage and restore from it. That is slower but survives region loss.

### Import and export

```text
gcloud sql export sql my-instance gs://bucket/backup.sql.gz --database=orders
gcloud sql import sql my-instance gs://bucket/backup.sql.gz --database=orders
```

The export runs a `pg_dump`/`mysqldump`/`sqlpackage` inside the instance and streams the result to Cloud Storage. Key facts:

- The export is **asynchronous** and can take hours on a large instance. You poll it.
- The file is **not encrypted by Cloud Storage's CMEK** unless you configure that on the bucket. Treat a dump as sensitive: it contains everything, including PII.
- The export **includes** everything in the database: schemas, data, and (for PostgreSQL) most roles are not included — roles and grants live in the instance, not the database, and must be recreated manually. This trips people up during migrations.
- Importing into an existing instance with objects present will fail on conflicts.
- The instance must have the Cloud SQL Admin API enabled and the calling identity needs `roles/cloudsql.admin` plus write access to the bucket.

### The Cloud SQL language connectors

Cloud SQL ships **language connectors** — a `pg`/`mysql2` driver extension that talks to BigQuery, Cloud Storage, and Cloud Spanner *through the Cloud SQL instance's network path*, with IAM authentication and no external IP required.

The pattern is remarkable when you first see it: the connector is installed as a database extension, and BigQuery becomes a **foreign table** in your PostgreSQL database.

```sql
CREATE EXTENSION google_cloud_bigquery;
CREATE FOREIGN TABLE orders_ext
  SERVER bigquery
  OPTIONS (
    dataset 'curated.orders',
    project 'YOUR_PROJECT_ID',
    location 'US'
  );

SELECT region, count(*) AS n
FROM orders_ext
GROUP BY region;
```

Why this matters for a data engineer: it lets a BI tool or a reporting service that already speaks PostgreSQL query BigQuery through the same connection, with the same IAM principal and the same network path, with no separate BigQuery credential handling. The same trick works for Cloud Storage (`google_cloud_storage` extension) and Cloud Spanner (`google_cloud_spanner`).

### Cloud SQL in the reference architecture

Cloud SQL is the **OLTP source** in the reference data platform:

```text
Application ──writes──► Cloud SQL (PostgreSQL, HA, PITR)
                              │
                              ├── Datastream CDC ──► Pub/Sub ──► Dataflow ──► BigQuery
                              │
                              └── read replica ──► reporting queries
```

Three patterns matter:

1. **CDC via Datastream.** Rather than batch-polling the source database, Datastream reads the transaction log and streams changes to Pub/Sub, then Dataflow lands them in BigQuery. This gives near-real-time replication without touching the source's write path. (Chapter 4.4 covers CDC in detail.)
2. **Batch extraction with `EXPORT DATA`.** Simpler, and for a nightly load, entirely adequate:
   ```sql
   EXPORT DATA OPTIONS (
     uri 'gs://YOUR_BUCKET/exports/orders-*.csv',
     format 'CSV',
     overwrite true
   );
   ```
3. **The warehouse as the analytical store, never the source of truth.** Cloud SQL is where the transactional invariants live (balances, inventory counts, order state machines). BigQuery is where the analysis happens. This split exists because the two workloads want opposite things: OLTP wants small, indexed, transactional, row-store semantics; OLAP wants large, columnar, scan-everything semantics. Trying to do both in one database is the most common architecture mistake in the field.

### Pricing

Cloud SQL bills:

| Component | Basis | Notes |
|---|---|---|
| Compute | vCPU-hour, by machine tier and region | Custom tier: you choose vCPUs and memory. Shared-core: burstable, for low-traffic dev instances |
| Storage | GB-month, by PD type and region | SSD is the default and the right choice for OLTP |
| Storage auto-resize | Same as storage | Adds up to 25% headroom automatically |
| Backups | GB-month of stored backups | Retained backups are billed at storage rates |
| Egress | Per GB out | Backups exported to a bucket in another region incur egress |
| High availability | The standby's vCPU and storage | Roughly doubles the compute and storage line |

The HA cost is the one that surprises people: **a regional HA instance costs roughly 2× a single-zone instance of the same size.** That is correct and intended — you are paying for a second always-on copy.

The course's model reflects this: `estimate("cloud-sql", vcpu_hours=..., gb_months=...)` uses `CLOUD_SQL_PER_VCPU_HOUR = 0.205` and `CLOUD_SQL_PER_GB_STORAGE = 0.17`.

---

## 🛠️ Hands-On

### 1. Create the instance

```text
gcloud sql instances create orders-db \
    --project=YOUR_PROJECT_ID \
    --region=us-central1 \
    --database-version=POSTGRES_16 \
    --tier=db-custom-2-7680 \
    --region=us-central1 \
    --storage-size=100GB \
    --storage-type=PD_SSD \
    --availability-type=REGIONAL \
    --backup-start-time=03:00 \
    --backup-retention-settings=retentionPeriodInDays=14 \
    --enable-point-in-time-recovery \
    --enable-bin-log \
    --no-assign-ip \
    --no-assign-public-ip \
    --network=projects/YOUR_PROJECT_ID/global/networks/default \
    --enable-private-service-access \
    --maintenance-version=POSTGRES_16_LATEST \
    --database-flags="log_checkpoints=on,log_min_duration_statement=1000"
```

What each flag is doing:

- `--availability-type=REGIONAL` — regional HA. A standby in another zone, synchronous replication, automatic failover. This roughly doubles the price; it is the right default for anything production.
- `--enable-point-in-time-recovery` — continuous transaction log archiving. This is what lets you recover to any moment, not just to a nightly backup boundary.
- `--enable-bin-log` — replication and read replicas. Needed for logical replication and for the `postgres` logical-decoding output that CDC tools consume.
- `--no-assign-public-ip` — no internet-facing address. Combined with `--enable-private-service-access`, the instance is reachable only from inside the VPC.
- `--enable-private-service-access` — allocates the internal address range (a one-time, per-VPC operation).
- `--database-flags` — `log_min_duration_statement=1000` logs any statement taking over a second. In a managed database this is one of the few knobs that gives you visibility into slow queries without a third-party agent.

Check what you got:

```text
gcloud sql instances list
gcloud sql instances describe orders-db --format="yaml(settings)"
```

### 2. Create the database and a least-privilege user

```text
gcloud sql databases create orders --instance=orders-db
gcloud sql users create app_user --instance=orders-db --password=NOT_A_REAL_PASSWORD
```

Do not connect as the built-in `postgres` superuser from the application. Create a role with only the permissions it needs:

```sql
CREATE ROLE etl_reader LOGIN PASSWORD 'NOT_A_REAL_PASSWORD';
GRANT CONNECT ON DATABASE orders TO etl_reader;
GRANT USAGE ON SCHEMA public TO etl_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO etl_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO etl_reader;
```

And a separate role for the CDC connection, which needs replication privileges:

```sql
CREATE ROLE cdc_user LOGIN REPLICATION PASSWORD 'NOT_A_REAL_PASSWORD';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cdc_user;
```

### 3. Connect with the Auth Proxy

```text
gcloud sql connect orders-db --user=app_user --prompt-for-password
```

The `gcloud sql connect` command starts the Auth Proxy for you. For anything else, run the proxy explicitly:

```text
gcloud sql connect orders-db --tcp-port=5432 --auto-iam-authn
```

```text
Listening on port 5432.
```

That is the proxy running. From another terminal:

```text
psql -h 127.0.0.1 -p 5432 -U app_user -d orders
```

Note the `-h 127.0.0.1`. If your application is configured with the instance's private IP instead of the proxy's local port, you bypass IAM authentication and need password auth instead — and you have also lost the automatic TLS.

For Python, use the connector library, which manages the proxy lifecycle for you:

```python
import os
import subprocess
import time

import psycopg2
from psycopg2 import OperationalError


def start_proxy(instance: str, port: int = 5432) -> subprocess.Popen:
    """Start the Cloud SQL Auth Proxy and wait for it to listen.

    Args:
        instance: The instance connection name.
        port: The local port to bind.

    Returns:
        The proxy process.
    """
    process = subprocess.Popen(
        [
            "gcloud",
            "sql",
            "connect",
            instance,
            f"--tcp-port={port}",
            "--auto-iam-authn",
            "--quiet",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        time.sleep(1)
        try:
            connection = psycopg2.connect(
                host="127.0.0.1",
                port=port,
                user="app_user",
                dbname="orders",
                connect_timeout=2,
            )
            connection.close()
            return process
        except OperationalError:
            continue
    process.terminate()
    raise RuntimeError("Auth Proxy did not become ready in 30 seconds")


def query_summary(instance: str = "YOUR_PROJECT_ID:us-central1:orders-db") -> list[tuple]:
    """Query the instance through the proxy and return the result rows.

    Args:
        instance: The instance connection name.

    Returns:
        A list of (region, order_count) tuples.
    """
    proxy = start_proxy(instance)
    try:
        connection = psycopg2.connect(
            host="127.0.0.1",
            port=5432,
            user="app_user",
            dbname="orders",
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT region, count(*) FROM orders GROUP BY region ORDER BY region"
                )
                return cursor.fetchall()
        finally:
            connection.close()
    finally:
        proxy.terminate()


if __name__ == "__main__":
    for region, count in query_summary():
        print(f"{region}: {count}")
```

The `start_proxy` helper encodes the operational rule: **poll the port, do not sleep a fixed time.** A fixed `sleep 5` is a race that fails on a cold start and wastes five seconds on a warm one.

### 4. Backups, PITR, and a restore

```text
gcloud sql backups list --instance=orders-db
gcloud sql backups create my-backup --instance=orders-db
gcloud sql backups describe my-backup --instance=orders-db
```

Restoring into a **new** instance — always a new instance, never over the production one:

```text
gcloud sql instances create orders-db-restore \
    --project=YOUR_PROJECT_ID \
    --region=us-central1 \
    --database-version=POSTGRES_16 \
    --tier=db-custom-2-7680 \
    --no-assign-ip \
    --network=projects/YOUR_PROJECT_ID/global/networks/default \
    --enable-private-service-access

gcloud sql backups restore <BACKUP_ID> \
    --instance=orders-db-restore \
    --project=YOUR_PROJECT_ID
```

Restore from a **point in time** instead:

```text
gcloud sql backups restore <BACKUP_ID> \
    --instance=orders-db-restore \
    --project=YOUR_PROJECT_ID \
    --restore-point-time="2026-01-15T09:30:00Z"
```

That last flag is the payoff of `--enable-point-in-time-recovery`. You can restore to any second within the retention window, not just to a backup boundary.

### 5. Export and import

```text
gcloud sql export sql orders-db gs://YOUR_PROJECT_ID-exports/orders-20260115.sql.gz \
    --database=orders \
    --project=YOUR_PROJECT_ID

gcloud sql operations list --instance=orders-db --limit=5
```

The export is asynchronous; poll the operation until it reports `done: true`. Then import into a scratch instance:

```text
gcloud sql import sql orders-db-scratch gs://YOUR_PROJECT_ID-exports/orders-20260115.sql.gz \
    --database=orders \
    --project=YOUR_PROJECT_ID
```

### 6. Query BigQuery from the database with a language connector

```text
gcloud sql instances patch orders-db \
    --database-flags="cloudsql.enable_google_cloud_bigquery=true"
```

Then, connected to the instance:

```sql
CREATE EXTENSION IF NOT EXISTS google_cloud_bigquery;

CREATE FOREIGN TABLE curated_events
  SERVER bigquery
  OPTIONS (
    dataset 'curated.events',
    project 'YOUR_PROJECT_ID',
    location 'US'
  );

SELECT region, count(*) AS event_count, sum(amount_eur) AS revenue_eur
FROM curated_events
WHERE event_dt >= '2026-01-15'
GROUP BY region
ORDER BY region;
```

The result matches the course's expected summary exactly — 1,238 events in AMER, 1,159 in APAC, 1,176 in EMEA, 1,227 in LATAM, totalling 4,800 — because the BigQuery table was loaded from the same `summary.csv` that `pipeline_logic.render_summary_csv()` produces. That is the point of the exercise: **the same logical data, reached from two different engines, with one IAM principal.**

### 7. Price the instance with the course's model

```python
import sys

sys.path.insert(0, "project/core")

from cost_model import estimate

HOURS_PER_MONTH = 730


def price_instance(
    vcpus: int,
    memory_gb: int,
    storage_gb: int,
    *,
    ha: bool,
    backups_retained_gb: float = 0.0,
) -> dict[str, float]:
    """Price a Cloud SQL instance, with and without high availability.

    Args:
        vcpus: The number of vCPUs.
        memory_gb: The memory in GB.
        storage_gb: The provisioned storage in GB.
        ha: Whether regional HA is enabled.
        backups_retained_gb: The GB of retained backups.

    Returns:
        A dict of cost breakdown lines.
    """
    multiplier = 2.0 if ha else 1.0
    compute = estimate(
        "cloud-sql",
        vcpu_hours=vcpus * HOURS_PER_MONTH * multiplier,
        gb_months=storage_gb * multiplier,
        monthly=True,
        apply_free_tier=False,
    )
    lines = {line.label: line.cost for line in compute.lines}
    backup_cost = backups_retained_gb * 0.17
    lines["Backups"] = round(backup_cost, 4)
    lines["TOTAL"] = round(sum(lines.values()), 4)
    return lines


if __name__ == "__main__":
    for ha in (False, True):
        label = "REGIONAL HA" if ha else "single zone"
        result = price_instance(
            2, 8, 100, ha=ha, backups_retained_gb=200
        )
        print(f"{label}:")
        for name, cost in result.items():
            print(f"  {name:<10} ${cost:>10.2f}")
        print()
```

The output shows the thing to internalise: **HA roughly doubles the bill** — the standby is a full second instance, not a cheap replica.

---

## 🛠️ Common Errors and Fixes

### 1. `409` when creating an instance — the name is taken

```text
ERROR: (gcloud.sql.instances.create) HTTPError: 409: The Cloud SQL instance already exists: your-project:us-central1:orders-db.
```

Cloud SQL instance names are unique **per project and per region**. The same name can exist in `us-central1` and `europe-west4`. To reuse a name you must delete the old instance first, and deletion is asynchronous — it can take several minutes and leaves the name reserved until it completes.

```text
gcloud sql instances delete orders-db --quiet
gcloud sql instances list --filter="name:orders-db"
```

Wait for the instance to disappear from the list before recreating it, or the create fails with the same 409.

### 2. `403` connecting from Cloud Run / GKE — no authorised network entry

```text
ERROR: (gcloud.sql.connect) HTTPError: 400: The Cloud SQL instance does not have a public IP address, so it cannot be reached from outside its VPC.
```

or, with a public IP:

```text
ERROR: (gcloud.sql.connect) HTTPError: 403: Your IP address is not in an authorized network for this instance.
```

For a public-IP instance, the connecting address must fall inside an authorised network range:

```text
gcloud sql instances patch orders-db --authorized-networks=10.0.0.0/8
```

For a private-IP instance, the real fix is to connect over the private path, not to add an authorised network — authorised networks do not apply to private IP at all. Make sure:

```text
gcloud sql instances describe orders-db --format="value(ipAddresses)"
```

returns an address in the `10.x` range, and that your workload's VPC peering to the PSA range is in place.

### 3. `Access denied for user 'app_user'@'1.2.3.4'`

```text
psql: error: connection to server at "35.192.10.5", port 5432 failed: FATAL:  password authentication failed for user "app_user"
```

Note the IP in the message: a public address means the connection came in over the internet path. Common causes:

- **The password was set with a shell variable that expanded to nothing.** `gcloud sql users create app_user --password=$PASSWORD` inside a script where `PASSWORD` is unset creates the user with an empty password. Use `--prompt-for-password`, or pass the password through an environment variable you actually set.
- **The password was changed after the user was created** and the client is caching an old credential.
- **IAM authentication was attempted but the user does not exist as a database user.** With `--auto-iam-authn`, the connecting principal must be granted `roles/cloudsql.client` *and* there must be a matching database user.

Check what actually happened:

```text
gcloud sql users list --instance=orders-db
gcloud projects get-iam-policy YOUR_PROJECT_ID --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:pipeline-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

### 4. `connection refused` on `127.0.0.1:5432`

```text
psql: error: connection to server at "127.0.0.1", port 5432 failed: Connection refused
```

This is **not** a database error. The Cloud SQL instance is fine. The Auth Proxy is not running, or it exited. Check:

```text
ps aux | grep cloud-sql-proxy
gcloud sql connect YOUR_PROJECT_ID:us-central1:orders-db --tcp-port=5432
```

Common causes:

- The proxy was started in one terminal and the application in another, and the first terminal was closed.
- The proxy exited because the instance name was wrong (`Your project:region:instance` vs `project-region:instance`) and the `--quiet` flag suppressed the error.
- The proxy needs Application Default Credentials and there are none. Run `gcloud auth application-default login` or set `GOOGLE_APPLICATION_CREDENTIALS`.

The generalised lesson: **when you connect through the proxy, a connection error is a proxy error until proven otherwise.** Diagnose the proxy first; it is a local process and it is five seconds to check.

### 5. `ERROR: (gcloud.sql.instances.patch) HTTPError: 400: Invalid database flag`

```text
ERROR: (gcloud.sql.instances.patch) HTTPError: 400: Invalid database flag: log_min_duration_statement
```

Cloud SQL only accepts a curated list of flags, and the list differs by engine and version. Also note the second class of failure: a flag that is *valid* but whose change requires a restart.

```text
gcloud sql instances patch orders-db --database-flags="log_min_duration_statement=1000" --restart
```

For PostgreSQL, `cloudsql.enable_google_cloud_bigquery` and the other `cloudsql.enable_google_cloud_*` flags must be set **before** you create the extension, and a restart is required.

### 6. Export fails or hangs partway through

```text
ERROR: (gcloud.sql.export.sql) HTTPError: 400: Export to this GCS location is not supported.
```

or a partial file appears in the bucket and the operation reports `FAILED`.

Causes and fixes:

- **The bucket is in a different region or is a multi-region the instance cannot reach.** Export requires the bucket to be in the same region as the instance (or in the `us` multi-region). Use a bucket in `us-central1`.
- **The instance cannot write to the bucket.** The exporting identity needs `roles/storage.objectCreator` on the bucket, and the Cloud SQL service agent needs it too:
  ```text
  gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
      --member="serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-cloud-sql.iam.gserviceaccount.com" \
      --role="roles/storage.objectAdmin"
  ```
- **The export is still running.** It is asynchronous and can take hours. Poll `gcloud sql operations list` rather than re-running it. Re-running creates a second export writing the same path, and the second one fails with `PreconditionFailed` or corrupts the first.

---

## 💡 Production Notes

- **Never use the public IP path in production.** Create the instance with `--no-assign-public-ip` and `--enable-private-service-access`. The default authorised network of `0.0.0.0/0` means your database is reachable from every address on the internet; credential failure is the only thing between an attacker and your data.
- **Turn on `--enable-point-in-time-recovery` at creation, not later.** Backups cannot be retroactively enabled for the period before they started. PITR turns your worst-case data loss from 24 hours into one transaction.
- **Run the Auth Proxy as a sidecar, never as a shared bastion.** The proxy holds credentials and terminates TLS for whoever connects to it. A shared proxy is a shared credential. In Kubernetes, use the Cloud SQL Auth Proxy sidecar or the Cloud SQL connectors (Cloud Run, Cloud Functions).
- **Size the instance from measured workload, and use the memory ratio your engine wants.** PostgreSQL wants roughly 4× the working-set size in RAM; MySQL is more forgiving. Set `--tier=db-custom-<vcpus>-<memory-mb>` rather than accepting the default, and remember `db-f1-micro` and `db-g1-small` are shared-core burstable — fine for staging, terrible for a production OLTP workload with latency SLOs.
- **Use read replicas to protect OLTP latency from reporting.** The standard pattern is: the application writes to the primary; the BI tool and the ETL extraction read from a replica. This is cheaper than scaling the primary and removes the most common cause of "the database got slow" incidents.
- **Put the export bucket next to the instance and treat dumps as PII.** An export contains every row, unencrypted unless you configured CMEK on the bucket. Restrict the bucket, enable versioning and soft delete, and set a lifecycle rule that deletes exports after 30 days.
- **Do not grant `roles/cloudsql.admin` to the application.** It can create instances, take backups, and export data. The application needs `roles/cloudsql.client` (to connect) and, for the exporter, `roles/cloudsql.instanceUser` plus write on the bucket. The Cloud SQL service agent needs the storage role; the app does not.
- **Monitor the right metrics.** `cloudsql.googleapis.com/database/cpu/utilization` for saturation, `.../instance/network/connectivity` for connection storms, `.../database/rows/returned` and `.../database/bytes_sent` for queries that pull too much, and the disk's `cloudsql.googleapis.com/instance/disk/write_count` for write pressure. Alert on CPU sustained above 70% and on disk usage above 80%.
- **Test the failover.** `gcloud sql instances failover orders-db` triggers a planned failover in a controlled way. Do it during a change window, on a schedule, and after every engine upgrade. A failover you have never rehearsed is an outage with extra steps.

---

## 🔑 Key Takeaways

- Cloud SQL manages the **substrate** (VM, disk, replication, failover, backups, patching); you manage the **data** (schema, queries, users, extensions). That boundary is exactly why it is the right default for OLTP.
- Engine version, region, private/public IP, and backup configuration are effectively **set at creation**. Get them right the first time; changing them means a dump-and-restore migration.
- The **Auth Proxy is the security boundary**, not just a convenience. It handles IAM authentication, TLS termination, and IP-family selection. "Connection refused on 127.0.0.1" means the proxy is down, not that the database is.
- **Authorised networks only govern the public path.** A private-IP instance ignores them entirely. Never run production on a public IP with `0.0.0.0/0` authorised.
- **Regional HA means a full second instance**: synchronous replication, automatic promotion, roughly double the cost. It is worth it for anything with an availability SLO.
- **Backups and PITR are different mechanisms.** Backups are periodic restorable snapshots; PITR is continuous log archiving that lets you recover to any moment in the retention window. Only PITR gives you a transaction-level RPO.
- **Exports are asynchronous and can run for hours.** Poll the operation, do not re-run it. A dump contains everything, so treat the export bucket as a PII store.
- The **language connectors** let BigQuery appear as a foreign table inside your PostgreSQL database — same connection, same IAM principal, same network path. It is a genuinely useful pattern for reporting tools.
- Cloud SQL's role in the platform: **the OLTP source of truth**, replicated to the warehouse by CDC, never the analytical engine.

---

## 📚 Practice Exercises

1. **Model the CDC-fed warehouse.** Write a Python function that prices the complete source-to-warehouse path for the course pipeline: Cloud SQL (2 vCPU, HA, 200 GB) + Datastream (4800 rows/day, 25M rows/month) + Pub/Sub + BigQuery (1 TB scanned/month). Use `estimate()` from `project/core/cost_model.py` for each service. Then compare it with the alternative of a batch `EXPORT DATA` every night (no Datastream, no Pub/Sub, and a BigQuery load of 1 TB/month). Explain which wins for a nightly pipeline and which wins for a pipeline with a 5-minute freshness requirement.
2. **Write the failover runbook.** Produce a runbook for a regional failover of `orders-db`: the manual failover command, what clients must do (nothing — the proxy reconnects), how to verify the new primary, how to check for split-brain, and the post-failback procedure. Include the two commands that show which instance is primary and the current `settings.failoverReplica` state. Then state, in one paragraph, why you would *not* run a manual failover at 3am to "test it" without a change window.
3. **Build the least-privilege role set.** Write the SQL for three roles — `app_rw`, `etl_reader`, `cdc_user` — against a schema modelled on the course's event shape (`event_id`, `user_id`, `event_ts`, `event_type`, `region`, `channel`, `currency`, `amount`, from `pipeline_logic.EVENT_FIELDS`). Grant only what each needs, including `ALTER DEFAULT PRIVILEGES` so new tables are covered. Explain in prose why `etl_reader` should not have `SELECT` on a table of PII columns even though it needs the revenue column.
4. **Implement the PITR calculation.** Write `worst_case_rpo(config)` in a new module under `project/core/` that takes a config with `backup_interval_hours`, `pitr_enabled`, `pitr_retention_days`, and returns the worst-case data loss in minutes and the maximum recoverable point in time. Test it against three configurations: daily backups only, backups plus PITR with 7-day retention, and PITR with 30-day retention. Tie the answer to the RPO/RTO discussion in chapter 2.6.
5. **Reproduce the summary through two engines.** Load the course's summary into a Cloud SQL PostgreSQL instance and into BigQuery, then produce the identical `region,event_count,revenue_eur` output from both. Verify that the numbers match `pipeline_logic.EXPECTED_SUMMARY` exactly: AMER 1238 / 464848.02, APAC 1159 / 421049.85, EMEA 1176 / 432544.17, LATAM 1227 / 445554.36. Then explain in a paragraph what the difference in *latency* and *scan cost* tells you about which engine the dashboard should query.
6. **Diagnose the connection failure.** Given the four error messages in the Common Errors section, write a `diagnose_connection_error(message)` function that returns a structured diagnosis: the likely cause, the check to run, and the fix. Cover "password authentication failed", "not in an authorized network", "connection refused on 127.0.0.1", and "invalid database flag". Then write a troubleshooting script that runs the right `gcloud` command for each diagnosis.
7. **Compare instance shapes.** Using `estimate("cloud-sql", ...)`, price the same workload (a PostgreSQL instance serving 2,000 writes/second, 100 GB of data, 30 days of backup retention) at `db-custom-2-7680`, `db-custom-4-15360`, and `db-custom-8-30720`, with and without HA. Then write the recommendation for a team whose current instance is under-provisioned, with the reasoning about memory-to-working-set ratio and write latency under synchronous replication.

---

## 📖 Further Reading

- [Cloud SQL overview](https://cloud.google.com/sql/docs/mysql/overview) — the managed-service model and its boundaries
- [Cloud SQL instance creation](https://cloud.google.com/sql/docs/mysql/create-instance) — the full flag reference
- [Connecting to Cloud SQL](https://cloud.google.com/sql/docs/mysql/connect) — the Auth Proxy, connectors, and the client libraries
- [Private Service Access for Cloud SQL](https://cloud.google.com/sql/docs/mysql/private-ip) — private IP setup and peering
- [High availability and failover](https://cloud.google.com/sql/docs/mysql/high-availability) — how regional HA works and what it costs
- [Backups and PITR](https://cloud.google.com/sql/docs/mysql/backup-recovery/backups) — the difference between the two, in the docs
- [Import and export](https://cloud.google.com/sql/docs/mysql/import-export) — the `gcloud sql export`/`import` reference
- [Cloud SQL language connectors](https://cloud.google.com/sql/docs/postgres/ql-databases) — BigQuery and Cloud Storage as foreign tables
