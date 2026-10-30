# Storage and Databases — Interview Questions

## 🎯 How to use this file

Fourteen questions covering Module 2: Cloud Storage and its classes, block and file storage, Cloud SQL, Cloud Spanner, the NoSQL family (Bigtable, Datastore, Firestore, Memorystore), and how to choose between them. These questions are where "just use Postgres" answers get exposed — the trick is knowing which axis of the problem each service optimises for. Say your answer out loud, then check it against the module.

## Questions

### Q1. When would you move data to a colder Cloud Storage class, and what is the catch most people miss?

**Answer.** Move data to Nearline, Coldline or Archive when it is rarely read and you want lower storage cost — but the catch is that **reading it back costs more per GB than the storage savings**, and there is a minimum storage duration.

**Mechanism.** Each class has a per-GB-month storage price and a per-GB *retrieval* price. Standard storage is $0.020/GB-month with free retrieval. Nearline is $0.010/GB-month but $0.010/GB to read. Coldline is $0.004/GB-month but $0.020/GB to read. Archive is $0.0012/GB-month but $0.050/GB to read — more than the entire Standard storage cost.

**Trade-off.** Storage is cheap; retrieval and egress are what surprise people. If you archive data you still read every quarter, you can end up paying more in retrieval than you saved in storage. There is also a minimum retention: 30 days for Nearline, 90 for Coldline, 365 for Archive, and deleting earlier incurs a charge.

**In practice.** The rule I apply: **archive only data you can state a specific access pattern for.** "We might need it someday" is not a reason to move 40 TB to Archive — you are betting against a future read that costs $0.05/GB. For a 40 TB archive read once a year, retrieval is $2,048 and the storage saving is roughly $770/month. Never worth it. For data read many times a year, it can be.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import STORAGE_CLASS_PRICES, STORAGE_RETRIEVAL_PRICES

for klass in ("standard", "nearline", "coldline", "archive"):
    print(f"{klass:<10} store ${STORAGE_CLASS_PRICES[klass]:.4f}/GB-month  "
          f"read ${STORAGE_RETRIEVAL_PRICES[klass]:.4f}/GB")
```

---

### Q2. Explain the difference between Nearline, Coldline and Archive access latency.

**Answer.** Nearline is millisecond access at a higher storage price. Coldline is tens-of-milliseconds access — effectively instant for interactive use. Archive is millisecond access only after an object is **restored**, which takes hours for a large object.

**Mechanism.** Nearline and Coldline objects are readable immediately; the higher price covers the cost of keeping hot indexes. Archive objects are stored in a form that must be rewritten before it can be served, so you request a restore, wait, then read. Single-object restore of a multi-terabyte file can take many hours.

**Trade-off.** Archive saves the most money but adds a workflow step that is easy to forget until someone needs the data urgently at 3am. Nearline's $0.01/GB retrieval is cheap enough that it is usually the right "cold" tier for data that is read occasionally but not restored rarely.

**In practice.** I tier in three steps: Standard for anything queried, Nearline for anything older than 90 days that might be queried, Archive only for data with a legal-hold or an explicit multi-year retention and a named owner who knows the restore takes hours. I write the restore time into the runbook, not just the class name.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

for klass in ("standard", "nearline", "coldline", "archive"):
    result = estimate("cloud-storage", storage_gb=10_000, storage_class=klass,
                      retrieval_gb=1_000, monthly=True)
    print(f"{klass:<10} total ${result.total:,.2f}")
```

---

### Q3. What is object versioning in Cloud Storage, and how do you actually delete a bad version?

**Answer.** Versioning keeps a noncurrent version of an object every time it is overwritten or deleted. To delete a specific version you delete *that version* by its generation number — deleting the "latest" just creates a new noncurrent version.

**Mechanism.** Every object version has a monotonically increasing **generation number**. `gsutil rm gs://bucket/object#1234567890` removes a specific generation. With versioning on, a plain delete marks the current version noncurrent and inserts a delete marker. You can also add a lifecycle rule that permanently deletes noncurrent versions after N days, which is how you bound the cost.

**Trade-off.** Versioning protects against accidental overwrite and ransomware — which is exactly the scenario where an attacker with `storage.objects.delete` cannot destroy data — but it also means `delete` is not really delete. Storage bills for every retained version, so an unbounded versioning bucket can cost several times what you expected.

**In practice.** I enable versioning on every landing bucket and add a lifecycle rule to permanently delete noncurrent versions after 30 days. That gives a 30-day window for a mistaken overwrite without letting the version history grow without bound.

**Failure story.** A pipeline had `storage.objects.delete` on the curated bucket and a bug that truncated the daily table, then wrote an empty file over it. Versioning was off. The previous day's partition was gone. It was recoverable only from the raw landing zone — which is precisely the argument for keeping the raw bucket immutable and versioning the curated one.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

print(SERVICES["cloud-storage"].key_resources)
print(SERVICES["cloud-storage"].pricing_model)
```

---

### Q4. What is the difference between Persistent Disk, Hyperdisk, and Filestore?

**Answer.** Persistent Disk and Hyperdisk are **block** storage — a volume attached to one or more Compute Engine instances that the OS sees as `/dev/sdb`. Filestore is **managed NFS** — a network filesystem that many instances mount simultaneously.

**Mechanism.** Block storage is attached to an instance over the same fabric as the instance's own disk, formatted with a filesystem, and is bound to one zone (so it cannot be attached to an instance in another zone). Filestore is a POSIX NFS service with its own performance tiers — basic, ZFS and HPC — and it is mounted by many clients at once across zones in a region.

**Trade-off.** Block storage is fast and cheap for a single writer, but the zone affinity is a real constraint for a multi-AZ deployment. Filestore solves multi-writer but costs more per GB and, in the ZFS tier, is the fastest NFS in the cloud.

**In practice.** Choose block storage when a single writer owns the data — a Dataflow worker disk, a Dataproc node's scratch space. Choose Filestore when many nodes need the same working set — a Spark shuffle directory shared by a cluster, or a shared model directory. If the data does not need to be on a POSIX filesystem, prefer GCS or BigQuery and skip the filesystem entirely.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES, services_by_category

for service in services_by_category("Storage"):
    print(f"{service.name:<24} {service.data_role:<28} {service.key_resources}")
```

---

### Q5. When would you use Filestore instead of putting the data in Cloud Storage?

**Answer.** Filestore when a legacy application needs a real POSIX filesystem, when many machines need concurrent read-write access to the same files, or when a tool insists on a mount point.

**Mechanism.** GCS is an object store with a flat key namespace — no partial reads, no in-place modification, no file locking, no random writes. Filestore provides a real filesystem with those semantics, so anything that works on NFS works.

**Trade-off.** A POSIX filesystem on a cloud platform is the classic anti-pattern: you are paying for a protocol and a compatibility layer over an object store. Filestore costs more per GB than GCS, needs a lifecycle plan for its own growth, and does not give you the object-store semantics your modern code is written against.

**In practice.** My rule: use Filestore when the consumer *cannot* be changed — a licensed application, a mainframe interface, a vendor tool that demands a mount. Otherwise, refactor to read from GCS. The exception I always make: a shared working directory for a Spark job, where the shuffle pattern genuinely needs a filesystem.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

filestore_like = estimate("cloud-storage", storage_gb=1_000, monthly=True)
print("GCS standard 1 TB-month:", filestore_like.total)
```

---

### Q6. What are Cloud SQL's HA options, and what does a failover actually cost you?

**Answer.** Cloud SQL offers regional HA (a standby instance in another zone in the same region) and cross-region replicas (with automatic or manual failover). A regional failover typically takes 30–90 seconds; a cross-region promotion is longer and can be minutes.

**Mechanism.** The primary replicates synchronously to a standby in another zone within the region, so a zonal failure is handled automatically. Cross-region replicas are asynchronous, so they can lose a small amount of committed data — the replication lag is the trade-off for surviving a regional failure.

**Trade-off.** Synchronous replication costs write latency and roughly doubles the compute bill (you pay for the standby). Asynchronous cross-region replication is cheaper to write but means the failover target may be behind. Any design that must survive a regional outage has to accept that.

**In practice.** For a data platform's metadata database, I use regional HA in the same region as the pipeline, with automated backups and PITR enabled. Cross-region replicas only where there is a stated availability requirement, and I document the accepted RPO as the observed replication lag rather than claiming zero.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

primary = estimate("cloud-sql", vcpu_hours=730 * 4, gb_months=500, monthly=True)
print("Cloud SQL 4 vCPU + 500 GB-month:", primary)
```

---

### Q7. When is Cloud SQL the wrong answer, and what is the right one?

**Answer.** Cloud SQL is the wrong answer when you need horizontal write scaling, strong consistency across regions, or you are doing analytical scans over historical data. The right answers are Cloud Spanner for global relational scale, BigQuery for analytics, or a NoSQL store for key-value access patterns.

**Mechanism.** Cloud SQL is a managed instance of a single database server, with a primary and a standby. You scale it vertically — bigger machine types, more disk, read replicas. There is no automatic sharding, so a hot row or a write-heavy workload eventually hits a single-writer ceiling.

**Trade-off.** Cloud SQL is familiar, cheap to start, and it is a managed Postgres/MySQL/SQL Server with the ecosystem you already have. It has a ceiling, and the migration away from that ceiling is expensive.

**In practice.** I start on Cloud SQL and move when I hit a specific trigger, not speculatively: p99 write latency above the SLA, a primary CPU above 60% sustained, a table past ~50 GB that needs indexing you cannot get, or a hard requirement for multi-region strong consistency. The migration path matters — I want to be on Postgres with a boring schema so the eventual move to Spanner or BigQuery is a data copy, not a rewrite.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES, services_by_category

for service in services_by_category("Databases"):
    print(f"{service.name:<16} {service.data_role:<12} {service.pricing_model}")
```

---

### Q8. What does Cloud Spanner buy you over Cloud SQL, and what does it cost?

**Answer.** Spanner gives you a relational model with horizontal sharding, global replication and **strong consistency across regions** — a transaction can span regions and still be serialisable. It costs more and it has a different operational model.

**Mechanism.** Spanner splits data across nodes by key range, splitting and rebalancing automatically as you scale. It uses TrueTime — a synchronised clock across the data-centres — to assign commit timestamps and wait out uncertainty, which is how it keeps global consistency without blocking on a quorum in one place.

**Trade-off.** The price of strong global consistency is latency: every commit touches multiple regions, so write latency is the highest-latency path, not the average. Spanner also does not give you the full Postgres feature set — no PostGIS, fewer extensions, and a different query dialect.

**In practice.** I choose Spanner when the requirement is *global correctness* — a global inventory counter, a payments ledger, a seat-booking system where a double-booking is a business failure. I do not choose it for a plain CRUD backend that will live in one region, because you are paying multi-region pricing for a problem you do not have.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

spanner = estimate("cloud-spanner", nodes=3, processing_units=1_000, monthly=True)
sql = estimate("cloud-sql", vcpu_hours=730 * 4, gb_months=500, monthly=True)
print("Spanner:", spanner.total)
print("Cloud SQL:", sql.total)
```

---

### Q9. Explain Bigtable's data model and when it beats a relational database.

**Answer.** Bigtable is a wide-column store: a table is a sparse, sorted map from a row key to column families of versioned cells. It wins when you have very large tables, high write throughput, and a sparse or time-series access pattern.

**Mechanism.** The row key defines both distribution and sort order. Rows are split into **tablets**, which are the unit of distribution and rebalancing. Column families are stored separately, so a wide table with many rarely-read columns does not pay to read the ones you skipped. Each cell can hold multiple versions with configurable TTL.

**Trade-off.** You give up joins, secondary indexes (outside the limited indexing support), and the general-purpose query language of Postgres. You get throughput and scale that a relational primary cannot reach without sharding it yourself.

**In practice.** I use Bigtable for time-series and high-volume operational data — telemetry, clickstreams, audit logs — where the access pattern is "give me the row key range for this hour" and the volume is millions of writes per second. For a 50 GB table that needs three joins, Postgres is the right answer and Bigtable is a downgrade.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES
from cost_model import estimate

print(SERVICES["bigtable"].key_resources)
print(estimate("bigtable", node_gb=10_000, monthly=True))
```

---

### Q10. When do you use Datastore, when Firestore, and when Bigtable?

**Answer.** Firestore for client-facing, mobile and web applications with server-side sync. Datastore for server-side application entities at scale with a simpler, flatter model. Bigtable for very large wide-column and time-series workloads.

**Mechanism.** Datastore and Firestore are both document databases — entities/documents with key-value and indexed properties — but they are different products with different APIs, pricing and consistency models. Firestore optimises for client synchronisation with a local cache and offline write queue. Datastore has a longer GCP heritage and a mode called Datastore in Firestore mode for gradual migration.

**Trade-off.** Documents are convenient — schema flexibility, no migrations for new fields — and they give up joins, cross-document transactions beyond a limited scope, and efficient range scans. Bigtable gives up the document model entirely but scales to far more data.

**In practice.** My decision is driven by *who writes*. If a mobile client writes directly, Firestore — it has the offline sync and the security rules for client-side access. If only your backend writes, Datastore or even Postgres, and you avoid exposing a sync surface you do not need. If the volume is in the terabytes and the access is by range, Bigtable.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

for service_id in ("datastore", "firestore", "bigtable"):
    service = SERVICES[service_id]
    print(f"{service.name:<12} regions={len(service.availability.available)} "
          f"preview={service.availability.preview} restricted={service.availability.restricted}")
```

---

### Q11. What is Memorystore for, and when is a cache the wrong answer?

**Answer.** Memorystore is a managed Redis or Memcached. It is the right answer for read-heavy, latency-sensitive lookups of data you already have elsewhere; it is the wrong answer when you are using it as a second source of truth.

**Mechanism.** It is an in-memory key-value store on the network, typically on a VPC peering or a direct peering. Redis gives you richer types — strings, hashes, lists, sets, sorted sets — plus persistence, replication and pub/sub. Memcached is a simpler, faster, no-persistence cache.

**Trade-off.** A cache is a derived copy, and derived copies go stale. The moment you write to the cache and the system of record, you have two sources of truth and a consistency question with no easy answer. It also adds a network hop and a new thing to monitor.

**In practice.** I use Redis for session storage, for rate-limit counters, and for caching expensive lookups where the source of truth is clearly elsewhere and the staleness window is acceptable. I never use it to hold data whose loss would be unacceptable, and I never write to it in the same transaction that writes to the database.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

cache = estimate("memorystore", gb_months=8 * 730, monthly=True)
print("8 GB Redis for a month:", cache)
```

---

### Q12. What is your framework for choosing a database?

**Answer.** Start from the access pattern, then the consistency requirement, then the scale. Query pattern first: analytical scans → BigQuery; key lookups → Firestore/Datastore; time-series ranges → Bigtable; range scans with joins → Cloud SQL; global strong consistency → Spanner.

**Mechanism.** Each service optimises a specific access pattern and pays a specific price for it. Spanner's price is write latency. BigQuery's is per-TB scanned. Bigtable's is node-hours. Cloud SQL's is vCPU-hours with a single-writer ceiling. Firestore's is per document operation.

**Trade-off.** The expensive part is not the initial choice — it is the migration. A datastore modelling decision you regret in year two means a dual-write and backfill.

**In practice.** I use a decision table with four columns: read pattern, write volume, consistency need, and analytics need. If analytics is one of the answers, the data goes to BigQuery — possibly *in addition to* the operational store, via CDC. The rule is that the operational database answers "what is true now for this entity" and the warehouse answers "what happened" — and you usually need both.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import DATA_ENG_ROLE, data_role_index

index = data_role_index()
for role, service_ids in index.items():
    print(f"{role:<14} {DATA_ENG_ROLE[role]:<44} {service_ids}")
```

---

### Q13. How do you decide between a single-region and a multi-region database, and what does that choice cost in latency?

**Answer.** Single region when your users and your writes are in one geography, or when you can tolerate a regional outage for the recovery time. Multi-region when the availability requirement demands surviving a regional failure, or when read latency across geographies is unacceptable.

**Mechanism.** Multi-region replication is asynchronous, so reads are served from the nearest replica (low latency) but the replicas lag the primary. Writes go to one primary region, so write latency is the distance to that region no matter where the user is.

**Trade-off.** Multi-region improves read latency and availability, and it worsens write latency and makes the lag a permanent part of your correctness story. Cross-region read-your-writes is not automatic.

**In practice.** I default to single region plus tested failover, and only go multi-region when there is a contractual availability target that single region cannot meet. When I do go multi-region, I decide explicitly which behaviours break under lag — and I never let the application assume read-your-writes without a token or a version check.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import REGIONS, zones_in

for region in ("us-central1", "europe-west1", "asia-southeast1"):
    print(region, REGIONS[region], zones_in(region))
```

---

### Q14. Your pipeline writes to Cloud Storage and queries it with BigQuery. What are the security and residency pitfalls?

**Answer.** The pitfalls are: a bucket with public access, a bucket in the wrong region, a storage path that BigQuery must read cross-region, and uniform-vs-object-level access confusion.

**Mechanism.** BigQuery reads GCS through a service account that needs `storage.objects.get` on the bucket (or the storage object viewer role), and the read path is a network path — if the bucket is in `europe-west1` and the BigQuery job runs in `us-central1`, you are paying egress and adding latency on every query. Object-level ACLs are ignored when the bucket has uniform bucket-level access enabled.

**Trade-off.** Uniform access is simpler and removes a whole class of ACL confusion bugs, but it means you cannot grant access to a single object. Per-object ACLs give fine granularity and are much harder to audit.

**In practice.** I enable uniform bucket-level access on every bucket, enforce public access prevention, and — where residency matters — apply an org policy on resource locations so no bucket can be created outside the approved regions. I put the raw and curated data in the same region as the BigQuery dataset and the Dataflow jobs, precisely to avoid the cross-region read.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from platform_sim import build_demo_project, format_resource_tree

project = build_demo_project()
print(format_resource_tree(project))
```

---

## 📚 Related chapters

- [2.1 — Cloud Storage](../chapters/06-cloud-storage.md)
- [2.2 — Block & File Storage](../chapters/07-block-and-file-storage.md)
- [2.3 — Cloud SQL](../chapters/08-cloud-sql.md)
- [2.4 — Cloud Spanner](../chapters/09-cloud-spanner.md)
- [2.5 — NoSQL: Bigtable, Datastore, Firestore, Memorystore](../chapters/10-nosql-bigtable-datastore-firestore-memorystore.md)
- [2.6 — Selecting a Database](../chapters/11-selecting-a-database.md)

## 📖 Further Reading

- [Cloud Storage documentation](https://cloud.google.com/storage/docs)
- [Cloud Storage cost and pricing model](https://cloud.google.com/storage/pricing)
- [Cloud SQL documentation](https://cloud.google.com/sql/docs)
- [Cloud Spanner documentation](https://cloud.google.com/spanner/docs)
- [Selecting a database for your workload](https://cloud.google.com/architecture/selecting-a-database)
