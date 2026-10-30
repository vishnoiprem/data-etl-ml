# Top 40 — Final Cramming Pass

## 🎯 How to use this file

Forty questions selected for yield: the ones that come up repeatedly in GCP data engineering interviews and certification exams, and the ones where a wrong answer reveals a gap. Read the bold first line of each answer — if you can produce it from memory, you are ready. If not, read the mechanism, then say the answer out loud in your own words. Use this on the last two days of a study plan, not as your first pass.

Each question cross-references the full treatment in the topic files. The numbering here is independent — Q1 here is not Q1 there.

## Questions

### Q1. What is the GCP resource hierarchy and how does IAM inheritance work?

**Answer.** Organization → folders → projects → resources, with IAM bindings inherited *downward*: a grant on a folder applies to every project in it and every resource in those projects.

**Mechanism.** Evaluation walks the resource's ancestry collecting applicable bindings, then applies explicit DENY > any ALLOW > deny by default. Ancestry steps in *type/name pairs* — `projects/p/buckets/b/objects/o` → `projects/p/buckets/b` → `projects/p` — and there is no scope for "the buckets of a project" separate from the project.

**Trade-off.** One folder grant covers hundreds of projects, which is what makes IAM manageable and what makes a mistake catastrophic. There is no scope that stops inheritance except a conditional binding or an explicit deny.

**In practice.** Grant on the narrowest resource that works. The demo project grants `roles/bigquery.dataEditor` on the project and `roles/storage.objectCreator` on the landing bucket — deliberately not `roles/owner`.

*Full answer: [01-platform-fundamentals.md Q2](01-platform-fundamentals.md)*

---

### Q2. Why is a project-level `roles/owner` grant dangerous?

**Answer.** It grants every permission in the project, and because grants inherit downward, that includes every bucket, dataset and table underneath.

**Mechanism.** `roles/owner` includes the ability to grant IAM to others, so the holder can widen their own access. The blast radius is the project, not the one resource you meant to expose.

**Trade-off.** Convenient and dangerous. `roles/storage.objectViewer` on one bucket is verbose and safe.

**In practice.** Use per-service roles on a service account. If a job needs to grant IAM, it gets `roles/resourcemanager.projectIamAdmin` on its own child projects only.

*Full answer: [01-platform-fundamentals.md Q3](01-platform-fundamentals.md)*

---

### Q3. What are the three service-account questions, and what is the rule about keys?

**Answer.** *Who is it?* What is it allowed to do. *How does it authenticate?* Workload identity, not a downloaded key. *What is the audit trail?* Which principal shows up in Cloud Logging.

**Mechanism.** A service account cannot log in; it acts by being impersonated or attached to a workload. The attachment mechanism determines the authentication story — key file, attached account, or Workload Identity Federation.

**Trade-off.** Keys are portable and simple, and they are long-lived secrets replayable from anywhere. Workload Identity removes the secret and issues short-lived tokens, at the cost of setup.

**In practice.** **No JSON keys in a repository, ever.** Use Workload Identity Federation for GKE and CI. Keys only in Secret Manager, with rotation.

*Full answer: [01-platform-fundamentals.md Q4](01-platform-fundamentals.md)*

---

### Q4. What is the IAM evaluation order?

**Answer.** Collect applicable bindings → discard non-matching principals and unsatisfied conditions → explicit DENY wins → any ALLOW wins → otherwise deny by default.

**Mechanism.** Precedence applies *after* collection, not per level. A DENY at bucket level overrides an ALLOW inherited from the project. A binding whose condition is unsatisfied is discarded, not treated as a deny.

**Trade-off.** Fail-closed by default is correct for security and produces the most common support ticket: a correct role, wrong place. Use `explain_principal()` to see whether the grant was exact or inherited.

**In practice.** Most "I have the role but it says permission denied" cases are a missing condition attribute or a group membership, not a missing role.

*Full answer: [01-platform-fundamentals.md Q6](01-platform-fundamentals.md)*

---

### Q5. What is an organization policy, and how does it differ from IAM?

**Answer.** An org policy constrains *configuration*, not access. IAM says who may do what; org policy says what configurations are allowed at all.

**Mechanism.** Org policies live at the organization or folder level and cascade down. They are not principal-specific — they apply to everyone, including you, unless you file an exemption. Custom constraints use CEL against resource attributes.

**Trade-off.** They are the only way to enforce things IAM cannot express — "no public buckets", "no resources in `europe-west2`". The cost is they can silently break your own automation.

**In practice.** Set `constraints/gcp.resourceLocations` on day one. A misconfigured default region can place EU customer data in `us-central1`, and you cannot undo that afterwards.

*Full answer: [01-platform-fundamentals.md Q9](01-platform-fundamentals.md)*

---

### Q6. What does BigQuery actually bill for?

**Answer.** **Bytes scanned**, not the number of queries. $6.25 per TB in `us-central1`.

**Mechanism.** Columnar storage skips blocks it does not need, but billing is at column-block granularity, before row-level filters apply.

**Trade-off.** Wonderful for exploration, terrible for a dashboard running 200 queries an hour over the same data — which is what flat-rate pricing exists for.

**In practice.** A `SELECT COUNT(*)` over a 10 TB unpartitioned table costs **$62.50**. The same query against a day-partitioned table costs roughly **$0.63**. That 100× is why you partition everything.

*Full answer: [03-analytics-and-cost.md Q1](03-analytics-and-cost.md)*

---

### Q7. Explain partitioning and clustering, and how they differ.

**Answer.** Partitioning splits a table by a value — almost always a date — into separate physical partitions. Clustering sorts data by up to four columns so equality and grouping filters read fewer bytes.

**Mechanism.** Partition pruning is a metadata operation: an excluded partition is never opened. Clustering works at block granularity inside a partition, pruning less aggressively but applying to equality and join predicates.

**Trade-off.** Partitioning has a 10,000-partition limit and a minimum partition size, so over-partitioning creates thousands of tiny partitions.

**In practice.** Partition by date, cluster by the two or three columns you filter and group by most. The combination is nearly always right and costs essentially nothing.

*Full answer: [03-analytics-and-cost.md Q3](03-analytics-and-cost.md)* and [Q4](03-analytics-and-cost.md)*

---

### Q8. When do you choose flat-rate BigQuery over on-demand?

**Answer.** When your query volume is predictably and consistently high enough that idle slots would cost more than the scans you avoid.

**Mechanism.** Flat-rate bills per slot-hour ($0.06) and gives a fixed allocation of vCPU and RAM that queries share. Reservations buy that capacity for one or three years at a discount.

**Trade-off.** Flat-rate converts variable cost into fixed cost. Reserve for the average and you queue at the peaks; pay for peak on-demand and you overpay for the peaks.

**In practice.** Look at 90 days of slot usage. If p95 sustained slot-hours exceed the on-demand cost for the same scan volume, reserve. Start with the annual committed-use discount on on-demand before taking on a reservation.

*Full answer: [03-analytics-and-cost.md Q2](03-analytics-and-cost.md)*

---

### Q9. What are the stages of a BigQuery query, and which do you optimise?

**Answer.** Scan → shuffle → aggregate/compute → write results. You optimise the **scan** stage most, because it dominates cost.

**Mechanism.** The shuffle redistributes rows by join or grouping key across workers — where a skewed join explodes. A join against a small dimension table is a broadcast hash join with **no shuffle at all**, which is why dimension tables belong in their own table.

**Trade-off.** Pre-aggregating upstream removes the shuffle but loses the ability to re-slice the data later.

**In practice.** Four questions of any slow query: bytes scanned, was there a shuffle, was the join key skewed, could the dimension table have been broadcast instead?

*Full answer: [03-analytics-and-cost.md Q7](03-analytics-and-cost.md)*

---

### Q10. What does Pub/Sub guarantee, and what does that force you to build?

**Answer.** **At-least-once delivery.** A message can be delivered more than once, and a subscriber that dies mid-processing gets redelivery. You must make the sink idempotent.

**Mechanism.** A message is acknowledged against a delivery attempt; if the subscriber dies before the ack lands, Pub/Sub redelivers after the ack deadline (10 s default, up to 600 s). Message retention (7 days default) bounds how long you can fall behind.

**Trade-off.** Exactly-once is not achievable across a network boundary. Pretending otherwise gets you duplicate rows.

**In practice.** Derive the idempotency key from the *data*, never from arrival time. The course's `dedup_key(event_id, partition)` returns `"20260115:evt-0001"` — a retry produces the same identity, so it is safe.

*Full answer: [04-streaming-and-ingestion.md Q1](04-streaming-and-ingestion.md)*

---

### Q11. What is a Pub/Sub dead-letter topic, and what should you alert on?

**Answer.** Where messages go when a subscriber rejects them or they exceed the maximum delivery attempts.

**Mechanism.** `nack` redelivers immediately and increments the delivery attempt count; after the configured maximum, the message is forwarded to the dead-letter topic.

**Trade-off.** It keeps the pipeline running but creates a second queue. An unmonitored dead-letter topic is where data quietly disappears.

**In practice.** Alert on the **age of the oldest unacked message**, not on the count. 100 dead letters that arrived a minute ago is nothing; 1 dead letter from three hours ago is an outage.

*Full answer: [04-streaming-and-ingestion.md Q2](04-streaming-and-ingestion.md)*

---

### Q12. When do you choose Kafka over Pub/Sub?

**Answer.** Kafka when you need high throughput with per-partition ordering you control, long retention with replay, or an existing Kafka ecosystem. Pub/Sub when you want fully managed, zero-idle-cost operation.

**Mechanism.** Kafka is a log: topics split into partitions, each an ordered append-only log; consumer groups track offsets and rebalance on membership change. Retention is a log-segment property, so you can replay from any offset.

**Trade-off.** Kafka gives control at the cost of operating brokers, partitions, rebalancing and capacity. Pub/Sub gives neither.

**In practice.** Kafka when multiple consumer teams need independent replay from different offsets — a log you cannot replay is a pipeline you cannot rebuild. Pub/Sub for everything else, especially unpredictable or zero consumer counts.

*Full answer: [04-streaming-and-ingestion.md Q4](04-streaming-and-ingestion.md)*

---

### Q13. Explain Kafka consumer groups and why a rebalance is scary.

**Answer.** A consumer group shares the partitions of a topic — each partition goes to exactly one consumer in the group — and each consumer tracks its **offset**.

**Mechanism.** The group coordinator assigns partitions and triggers a **rebalance** when a consumer joins, leaves or fails its heartbeat. Consumption pauses during a rebalance.

**Trade-off.** More consumers than partitions means idle consumers — a real parallelism ceiling. Long rebalances stall the pipeline.

**In practice.** Size the group to the partition count, set `max.poll.interval.ms` above worst-case processing time, use static membership to avoid rebalances on every deploy, and alert on consumer lag per partition.

*Full answer: [04-streaming-and-ingestion.md Q5](04-streaming-and-ingestion.md)*

---

### Q14. What is Datastream, and when is CDC the wrong choice?

**Answer.** Datastream is managed change data capture — it reads a source's binlog or replication stream and publishes row changes to a destination.

**Mechanism.** For Cloud SQL it uses the MySQL binlog or PostgreSQL logical replication; for Oracle the redo log. It reads from Cloud SQL, BigQuery, AlloyDB and many SaaS sources, and writes to BigQuery, Cloud Storage, Bigtable and Pub/Sub.

**Trade-off.** CDC captures *state changes* — including updates to rows you never cared about — while event streaming captures *intent*. CDC also inherits the source's log retention: fall behind past the log's lifetime and you have a gap.

**In practice.** CDC for keeping an operational store and a warehouse in sync. Event streaming where the producer can be changed to emit an event, because a `DELETE` in a log is harder to interpret than a `deleted` event with a reason.

*Full answer: [04-streaming-and-ingestion.md Q6](04-streaming-and-ingestion.md)*

---

### Q15. What are the storage classes, and what is the catch?

**Answer.** Standard ($0.020/GB-month, free retrieval), Nearline ($0.010, $0.010/GB to read), Coldline ($0.004, $0.020/GB), Archive ($0.0012, $0.050/GB — more than Standard storage costs).

**Mechanism.** Each class trades storage price for retrieval price, plus a minimum retention: 30 days Nearline, 90 Coldline, 365 Archive. Archive objects need a **restore** before they can be read, which takes hours for large objects.

**Trade-off.** Storage is cheap; retrieval and egress surprise people. Reading 40 TB from Archive once a year costs $2,048 in retrieval against roughly $770/month saved.

**In practice.** Archive only data you can state a specific access pattern for. "We might need it someday" is not a reason. Put the restore time in the runbook.

*Full answer: [02-storage-and-databases.md Q1](02-storage-and-databases.md)*

---

### Q16. What is the difference between block storage and Filestore?

**Answer.** Persistent Disk and Hyperdisk are **block** storage — a volume attached to instances, seen as `/dev/sdb`, zone-bound. Filestore is **managed NFS** — a network filesystem many instances mount at once.

**Mechanism.** Block storage is bound to one zone, which constrains multi-AZ designs. Filestore provides real POSIX semantics with concurrency, in basic, ZFS and HPC tiers.

**Trade-off.** A POSIX filesystem on a cloud platform is the classic anti-pattern — you pay for a protocol and a compatibility layer over an object store.

**In practice.** Block storage for a single writer (worker disk, scratch). Filestore when the consumer cannot be changed or a Spark job genuinely needs a shared working directory. Otherwise, prefer GCS or BigQuery.

*Full answer: [02-storage-and-databases.md Q4](02-storage-and-databases.md)*

---

### Q17. When is Cloud SQL the wrong answer?

**Answer.** When you need horizontal write scaling, strong consistency across regions, or analytical scans over history. Use Spanner for global relational scale, BigQuery for analytics.

**Mechanism.** Cloud SQL is a single managed database server — primary plus standby. You scale vertically. There is no automatic sharding, so a hot row eventually hits a single-writer ceiling.

**Trade-off.** Familiar, cheap to start, with the ecosystem you already have. But it has a ceiling, and migrating away from that ceiling is expensive.

**In practice.** Move on a specific trigger, not speculatively: p99 write latency above SLA, primary CPU above 60% sustained, a table past ~50 GB needing an index you cannot get, or a hard multi-region consistency requirement. Stay on boring Postgres so the eventual move is a data copy, not a rewrite.

*Full answer: [02-storage-and-databases.md Q7](02-storage-and-databases.md)*

---

### Q18. What does Spanner buy you over Cloud SQL, and what does it cost?

**Answer.** Horizontal sharding, global replication and **strong consistency across regions** — a transaction can span regions and still be serialisable.

**Mechanism.** Data is split into nodes by key range, splitting and rebalancing automatically. **TrueTime** — a synchronised clock across data centres — assigns commit timestamps and waits out uncertainty, giving global consistency without blocking on a quorum in one place.

**Trade-off.** Strong global consistency costs write latency — every commit touches multiple regions, so latency follows the *highest* path, not the average. Spanner also lacks much of the Postgres feature set.

**In practice.** Choose Spanner when global correctness is a business requirement — a global inventory counter, a payments ledger, seat booking where a double-booking is a business failure. Not for a plain CRUD backend in one region.

*Full answer: [02-storage-and-databases.md Q8](02-storage-and-databases.md)*

---

### Q19. How do you choose a database?

**Answer.** Access pattern first, then consistency, then scale. Analytical scans → BigQuery; key lookups → Firestore/Datastore; time-series ranges → Bigtable; range scans with joins → Cloud SQL; global strong consistency → Spanner.

**Mechanism.** Each service optimises a specific access pattern and pays a specific price for it — Spanner for write latency, BigQuery for TB scanned, Bigtable for node-hours, Firestore for per-document operations.

**Trade-off.** The initial choice is cheap. The *migration* is expensive.

**In practice.** Four columns: read pattern, write volume, consistency need, analytics need. If analytics is one of the answers, the data goes to BigQuery — often *in addition to* the operational store, via CDC. The operational database answers "what is true now"; the warehouse answers "what happened".

*Full answer: [02-storage-and-databases.md Q12](02-storage-and-databases.md)*

---

### Q20. When do you choose Memorystore, and when is a cache the wrong answer?

**Answer.** For read-heavy, latency-sensitive lookups of data you already have elsewhere. Wrong when you use it as a second source of truth.

**Mechanism.** An in-memory key-value store on the network, via VPC peering or direct peering. Redis adds richer types and persistence; Memcached is simpler and has no persistence.

**Trade-off.** A cache is a derived copy, and derived copies go stale. Writing to the cache and the database gives you two sources of truth and a consistency question with no easy answer.

**In practice.** Redis for sessions, rate-limit counters and expensive lookups with an acceptable staleness window. Never for data whose loss would be unacceptable, and never written in the same transaction as the database.

*Full answer: [02-storage-and-databases.md Q11](02-storage-and-databases.md)*

---

### Q21. What is the difference between Data Fusion and Dataprep?

**Answer.** Data Fusion is a general-purpose visual **ETL and integration** tool for connecting systems. Dataprep is a specialised **data preparation and profiling** tool for wrangling data files for analysis.

**Mechanism.** Data Fusion nodes connect sources to sinks and its pipelines can stream. Dataprep works over datasets with recipes, profiling cards and visual diffs, and its output is a cleaned dataset, not a production feed. Both run on Dataproc, which is why they get confused.

**Trade-off.** Overlap is real — both can do a CSV-to-BigQuery load with a filter. The choice follows intent: "connect these systems and keep it running" is Fusion; "profile this file and clean it" is Dataprep.

**In practice.** Installing both and using them for the same job is the worst outcome: two visual pipelines, two Dataproc clusters, no code review. Pick one and standardise.

*Full answer: [05-processing-and-orchestration.md Q14](05-processing-and-orchestration.md)*

---

### Q22. When do you choose Composer over Workflows?

**Answer.** Composer when the orchestration is a DAG with dependencies, backfills and data-aware logic. Workflows when it is a chain of API calls with no branching data logic.

**Mechanism.** Composer is managed Airflow: scheduler, dependency graph, logical dates (and therefore backfills), XComs, a large operator ecosystem. Workflows is a serverless state machine of steps and transitions, billed per transition, with **no idle cost**.

**Trade-off.** Composer is a full orchestrator with a learning curve and a per-node-hour cost ($0.0564). Workflows has no infrastructure but no Python and no complex branching.

**In practice.** Composer for anything with a real dependency graph — backfills are non-negotiable once you are in production. Workflows for glue: a webhook that triggers a job, then a query, then a notification.

*Full answer: [05-processing-and-orchestration.md Q7](05-processing-and-orchestration.md)*

---

### Q23. What is a logical date, and why is it the most important concept in Airflow?

**Answer.** The label of a DAG run, representing the **data interval** it processes — not the moment it ran.

**Mechanism.** The schedule interval defines the data window and its parameters interpolate it into the task commands, so a query filters `event_date = '{{ ds }}'`. Because the label is stable, any historical date can be re-run for the same result.

**Trade-off.** It gives reproducibility and backfills, at the cost of a mental model that trips up newcomers — a daily DAG has a logical date of *yesterday* at midnight.

**In practice.** **Never use `now()` in a task; always use the logical date.** A task using `CURRENT_DATE()` produces wrong data on a backfill, silently and retroactively.

*Full answer: [05-processing-and-orchestration.md Q8](05-processing-and-orchestration.md)*

---

### Q24. Why use Dataform instead of plain SQL?

**Answer.** Version-controlled, tested, dependency-aware SQL — `ref()` and `source()` instead of hand-maintained table names, with generated lineage and reviewable pull requests.

**Mechanism**. A repository is a set of `.sqlx` files with `config()` blocks declaring type, description, tags and tests. `ref('stg_events')` resolves the full table name *and* creates a DAG edge, so Dataform builds the dependency graph and runs models in topological order. **Assertions** (`unique`, `not_null`, `relationships`) fail the run when data is wrong.

**Trade-off.** A layer over SQL: templating syntax, config blocks, a compilation model. Overhead for a handful of ad-hoc queries.

**In practice.** Use it once you have more than about five interdependent models — that is exactly when hand-maintained SQL starts to break at 3am. The tests are the real value.

*Full answer: [05-processing-and-orchestration.md Q10](05-processing-and-orchestration.md)*

---

### Q25. What is the MapReduce shuffle and why is it the expensive part?

**Answer.** The phase where each mapper's intermediate key-value pairs are partitioned by key and shipped across the network to the reducers, where they are sorted and merged.

**Mechanism.** Partition, spill to local disk, merge, network transfer to the reducer's partition. The network transfer and disk I/O dominate elapsed time — compute is often a small fraction.

**Trade-off.** Moving data is slower than moving compute, but keeping data local is not free: local disks are limited and replicating to avoid the shuffle costs more than the shuffle.

**In practice.** The question behind every performance investigation: *can this shuffle be avoided?* A map-side join against a small in-memory dimension eliminates the reduce-side shuffle entirely.

*Full answer: [05-processing-and-orchestration.md Q2](05-processing-and-orchestration.md)*

---

### Q26. When would you use Spark on Dataproc versus Dataflow batch?

**Answer.** Dataproc when the codebase is already Spark or you need Spark-specific features (MLlib, GraphX, Spark SQL). Dataflow batch when you want one pipeline to run as batch today and streaming tomorrow, with managed autoscaling and no cluster admin.

**Mechanism.** Dataproc runs a Spark cluster, long-lived or **Serverless** (spin up for the job, tear down after). Dataflow runs Apache Beam, so the same code executes in batch or streaming mode and autoscales workers.

**Trade-off.** Dataproc is cheaper per vCPU-hour ($0.0476 vs $0.0595) and can keep a warm cluster — but a warm cluster is a warm bill. Dataflow's higher unit price is repaid by batch/streaming symmetry within a few months.

**In practice.** New work with no legacy constraint goes to Dataflow. Existing Spark goes to Dataproc Serverless — keep the code, stop paying for an idle cluster.

*Full answer: [05-processing-and-orchestration.md Q3](05-processing-and-orchestration.md)*

---

### Q27. What is a watermark in Beam, and what happens to late data?

**Answer.** The pipeline's declaration that no more events will arrive with a timestamp at or before it. Events arriving after that are **late data**.

**Mechanism.** A streaming `GroupByKey` fires when the watermark passes the end of the window. Later data goes to a **side output**, or is dropped if you define none.

**Trade-off.** Too aggressive a watermark drops data you needed; too conservative holds windows open, increasing state, latency and cost.

**In practice.** Set the watermark from the *observed lateness distribution* — if 99.9% of events arrive within 90 seconds, the watermark sits at 90 seconds. Always define a side output for late data, because silently dropped late data is a wrong number with no trace.

*Full answer: [05-processing-and-orchestration.md Q5](05-processing-and-orchestration.md)*

---

### Q28. What is event time versus processing time, and why does it matter?

**Answer.** Processing time is when your system handles the event; event time is when it happened. Windowing on the wrong one produces answers that look right and are wrong.

**Mechanism.** The course's `bucket_by_window` derives the window from the **event timestamp**, never arrival time. Skip the re-stamping step and every event collapses into one window — the totals stay right, which is exactly why the bug is easy to miss. The dataset spans 24 hours and produces exactly 24 hourly windows.

**Trade-off.** Event-time windowing is correct but requires handling late data. Processing-time windowing avoids that and produces results nobody can reconcile with the source.

**In practice.** Use event time with a watermark that declares how late is late enough. Events past the watermark go to a side output for reprocessing.

*Full answer: [05-processing-and-ingestion.md Q12](04-streaming-and-ingestion.md)*

---

### Q29. What does Sensitive Data Protection do, and where does it belong in a pipeline?

**Answer.** It discovers sensitive data and either inspects it (classifies and reports) or de-identifies it (redacts, masks, tokenises, formats).

**Mechanism.** A **template** names **info types** — built-in detectors (email, credit card, phone, name, address) or custom ones. An inspect job returns findings; a de-identify job transforms the data. DLP is character-aware, which matters: a loose digit pattern will not flag a real card number.

**Trade-off.** Billed per inspected byte ($0.10/GB in the model) after a free allowance. Regex is free and far less accurate.

**In practice.** Detection on ingest as a filter, de-identification on publish as the control. I put DLP in the curated layer, so raw keeps fidelity and curated is safe to share.

*Full answer: [06-governance-security-and-ml.md Q1](06-governance-security-and-ml.md)*

---

### Q30. What are the de-identification techniques, and which one keeps joins working?

**Answer.** Redaction, masking, tokenisation and format-preserving encryption. **Tokenisation** is the one that keeps joins working.

**Mechanism.** Redaction removes the value. Masking keeps the shape, not the value. Tokenisation replaces it with a deterministic surrogate — the same input always yields the same token, so referential integrity survives. Format-preserving encryption keeps shape *and* reversibility.

**Trade-off.** Every technique is a one-way door. Tokenisation needs a token vault protected as carefully as the data.

**In practice.** Tokenise identifiers you must join on; mask fields where only the format matters; redact only fields with no analytical value. Keep the mapping in a separate, tighter project.

*Full answer: [06-governance-security-and-ml.md Q3](06-governance-security-and-ml.md)*

---

### Q31. How do you enforce data residency on GCP?

**Answer.** Three layers: location choice, org policy on permitted locations, and IAM scoped so nobody reads across the boundary.

**Mechanism.** Locations are largely immutable — you cannot move a bucket between regions. `constraints/gcp.resourceLocations` prevents creation outside the approved list. And a global `roles/bigquery.dataViewer` on the project would still let a US-based engineer read EU data.

**Trade-off.** Residency constrains the architecture. A global multi-region analytics dataset may be legally impossible; a single-region warehouse means latency for distant users or a replica subject to the same rules.

**In practice.** Treat residency as a project design constraint, not a setting: separate projects per jurisdiction, an org policy that makes the wrong thing impossible, and IAM that genuinely prevents cross-region reads.

*Full answer: [06-governance-security-and-ml.md Q4](06-governance-security-and-ml.md)*

---

### Q32. What is CMEK, and what breaks when you adopt it?

**Answer.** Customer-Managed Encryption Keys: you create the key in Cloud KMS and point a service at it, so the key's lifecycle, rotation and revocation are yours. What breaks is that you now own availability.

**Mechanism.** Grant the *service's service account* the `cloudkms.cryptoKeyEncrypterDecrypter` role on the key. Disabling or destroying the key version makes the data permanently unreadable — the point, and the hazard.

**Trade-off.** CMEK is the only way to revoke access to data already stored. It also makes a KMS outage a data outage and a mistaken key disable into data loss.

**In practice.** Keep the key ring in a dedicated security project, separate key admin from data admin, and **test the revocation procedure on a non-critical bucket first**. Alert on key version state. Rotation and destruction are different operations and need different approvals.

*Full answer: [06-governance-security-and-ml.md Q7](06-governance-security-and-ml.md)*

---

### Q33. What is the shared responsibility model, and where do audits actually bite?

**Answer.** Google secures the physical infrastructure, hypervisor, networking and facilities. You secure the OS, middleware, application, data — and the IAM configuration that gives access to it.

**Mechanism.** Certifications evidence Google's controls. They say nothing about your configuration. A SOC 2 report on Google Cloud says nothing about whether your Cloud SQL instance has a weak password and public IPs.

**Trade-off.** A certification is about the provider; an audit is about your project. Both matter and they are different artifacts.

**In practice.** Use Audit Logs — Admin Activity, Data Access, System Event, Policy Denied — exported to a locked sink in a separate project, plus a configuration audit against CIS benchmarks. "Show me who read this table in March" is answered by a log export, not a screenshot.

*Full answer: [06-governance-security-and-ml.md Q8](06-governance-security-and-ml.md)*

---

### Q34. What is a BI semantic layer, and why does it matter?

**Answer.** A governed definition of your business metrics, sitting between raw data and dashboards, so "monthly active customers" means exactly one thing everywhere.

**Mechanism.** In Looker, a **model** defines tables and relationships, an **explore** exposes curated fields. In dbt or Dataform, modelled tables with documented definitions and tests. Either way the metric is computed once, in version-controlled code, and every consumer reads the same definition.

**Trade-off.** It costs engineering time up front and adds a layer consumers must learn.

**In practice.** Insist on it as soon as two dashboards exist. The failure it prevents is worse than the cost: two teams presenting different revenue numbers to the same executive in the same meeting. The course's `EXPECTED_SUMMARY` is the smallest version of this idea — one place defines the aggregate, everything else reads it.

*Full answer: [06-governance-security-and-ml.md Q10](06-governance-security-and-ml.md)*

---

### Q35. Explain supervised versus unsupervised learning.

**Answer.** Supervised learns a mapping from labelled examples; unsupervised finds structure in unlabelled data without being told what to look for.

**Mechanism.** Supervised needs labelled data, features, a loss function and an optimiser. Unsupervised optimises something like within-cluster variance or reconstruction error.

**Trade-off.** Supervised gives you a testable metric against a held-out set. Unsupervised gives structure but **no ground truth** — you cannot measure whether the clusters are meaningful, only whether they are stable.

**In practice.** The pipeline's job is a trustworthy training set with no leakage. Supervised fits fraud, churn and forecasting. The most common failure is **skew**: features computed from data that did not exist at prediction time — temporal leakage — which works offline and fails in production.

*Full answer: [06-governance-security-and-ml.md Q11](06-governance-security-and-ml.md)*

---

### Q36. When do you use a prebuilt or AutoML model instead of training your own?

**Answer.** Prebuilt when the task is one Google already solved well (vision, speech, translation, moderation). AutoML when you have labelled data but do not want to tune hyperparameters yourself.

**Mechanism.** Pre-trained models are served APIs with no training. AutoML takes your labelled dataset, searches the model space, and exports the winner to Cloud Storage or deploys it to an endpoint.

**Trade-off.** Prebuilt gives a quality baseline in an afternoon and a black box you cannot change. AutoML fits your data but spends real money on the search, and often only beats a good baseline slightly.

**In practice.** Start with the prebuilt model to get a baseline and a working pipeline, then decide if the delta is worth it. The real work is the **evaluation set** and the **serving path** — a model with no evaluation set is not deployed.

*Full answer: [06-governance-security-and-ml.md Q12](06-governance-security-and-ml.md)*

---

### Q37. What does custom training on Vertex AI involve, and how do you operationalise a model?

**Answer.** Running your own training code on managed infrastructure, plus everything needed to run it in production.

**Mechanism.** A **pipeline** is a DAG of preprocessing, training, evaluation, registration and deployment. Models go to the **Model Registry**; **endpoints** serve them with versioning and traffic splitting.

**Trade-off.** Full control, and real money — $3.67 per training node-hour. Managed operations (retraining pipeline, endpoint, monitoring) become your responsibility once you leave the prebuilt path.

**In practice.** Three things decide whether a model is in production: a **feature pipeline** producing identical features at training and serving time, a **drift and skew monitor**, and a **retraining trigger** with an evaluation gate. Without the feature pipeline, training-serving skew silently destroys the model.

*Full answer: [06-governance-security-and-ml.md Q13](06-governance-security-and-ml.md)*

---

### Q38. What is BigQuery ML, and when is it right?

**Answer.** Train and serve models with SQL inside the warehouse — `CREATE MODEL`, `SELECT * FROM ML.PREDICT(...)` — with no data movement.

**Mechanism.** `CREATE MODEL` names the model type (`LOGISTIC_REGRESSION`, `KMEANS`, `DNN_CLASSIFIER`, …), features, label and training options. Inference is a query, and you can create a **remote model** over a Bigtable endpoint for online serving.

**Trade-off.** Excellent for the model classes it supports and for tabular data already in BigQuery — the whole path is one SQL statement. But it is not a general ML platform: no custom training code, no custom architectures, no serious hyperparameter search, and inference is billed as a query.

**In practice.** Use it for baseline models and simple production predictors — propensity, demand forecast, churn. Move to Vertex AI when you need custom features, custom loss, or a deep architecture. Always compare against a trivial baseline: if a linear model over two features does not beat "predict the mean", the model is not earning its complexity.

*Full answer: [06-governance-security-and-ml.md Q14](06-governance-security-and-ml.md)*

---

### Q39. A team says "BigQuery is too expensive." What do you ask?

**Answer.** How many bytes did the query scan, how many times was the same data scanned, who ran it, and what is the storage-versus-scan split. The answer is usually redundant scanning.

**Mechanism.** `compare_architectures` shows the shape: a 1 TB unpartitioned scan is $6.25; the same query pruned to 1% is $0.0625 — a 100× reduction from table layout alone, with no change to the query.

**Trade-off.** The fix is not "partition everything" — a one-off ad-hoc query over a small table is genuinely cheap. Target the queries that run constantly.

**In practice.** Pull the billing export, join it to `jobs` metadata, rank by total bytes billed. Usually the top three are a dashboard, a nightly aggregation, and a `SELECT COUNT(*)` someone left in a view. Partition the tables, materialise the dashboard, and add `maximumBytesBilled` so the next regression fails instead of billing.

*Full answer: [03-analytics-and-cost.md Q12](03-analytics-and-cost.md)*

---

### Q40. How do you make a data pipeline production-ready?

**Answer.** Deterministic idempotency, a bounded retry, a dead-letter path, cost controls in the deployment template, and tests at every layer.

**Mechanism.** The course's design is the answer: all business rules live in pure Python with no cloud imports, so `pytest` runs in under a second with no credentials. `validate_event` is the single source of truth, so a rule cannot be enforced in one place and forgotten in another. The exact figures — 4800 events, 12 malformed rows, the per-region revenue totals, 24 hourly windows — are assertable precisely because the logic is deterministic.

**Trade-off.** Pure-function testing needs the discipline to keep business rules out of deployment scripts. The alternative — testing only by running the pipeline — needs a live project, so the suite becomes slow, people stop running it, and the pipeline ships untested.

**In practice.** Idempotency key from data (`dedup_key` = `"<partition>:<event_id>"`), ack after write, `maximumBytesBilled` on every job, partitioned-and-clustered tables from the template, and a data-quality gate that compares output to expected invariants and fails the job when they do not match.

*Full answer: [05-processing-and-orchestration.md Q16](05-processing-and-orchestration.md)*

---

## 📚 Related chapters

- [1.1 — Introduction to Cloud Computing](../chapters/01-introduction-to-cloud-computing.md)
- [1.2 — Regions, Zones & the Resource Hierarchy](../chapters/02-regions-zones-and-resource-hierarchy.md)
- [1.3 — Identity & Access Management](../chapters/03-identity-and-access-management.md)
- [1.4 — Organization Policies, Networking & Compute](../chapters/04-org-policies-networking-and-compute.md)
- [1.5 — Proposing a Data Processing Strategy](../chapters/05-proposing-a-data-processing-strategy.md)
- [2.6 — Selecting a Database](../chapters/11-selecting-a-database.md)
- [3.3 — BigQuery Query Optimization](../chapters/14-bigquery-query-optimization.md)
- [4.2 — Pub/Sub](../chapters/17-pubsub.md)
- [4.3 — Datastream & CDC](../chapters/18-datastream-and-cdc.md)
- [5.2 — Apache Spark & Cloud Dataproc](../chapters/21-apache-spark-and-dataproc.md)
- [5.3 — Apache Beam & Cloud Dataflow](../chapters/22-apache-beam-and-dataflow.md)
- [5.4 — Airflow, Composer & Workflows](../chapters/23-airflow-composer-and-workflows.md)
- [5.5 — Dataform & the Transformation Layer](../chapters/24-dataform-and-the-transformation-layer.md)
- [6.1 — Cloud Data Fusion](../chapters/25-cloud-data-fusion.md)
- [6.2 — Cloud Dataprep](../chapters/26-cloud-dataprep.md)
- [7.1 — Sensitive Data Protection](../chapters/27-sensitive-data-protection.md)
- [7.2 — Compliance, Residency & Encryption](../chapters/28-compliance-residency-and-encryption.md)
- [7.3 — Looker Studio & BI](../chapters/29-looker-studio-and-bi.md)
- [8.1 — ML Foundations on GCP](../chapters/30-machine-learning-foundations.md)
- [8.3 — Custom Training & Vertex AI](../chapters/32-custom-training-and-vertex-ai.md)
- [8.4 — BigQuery ML](../chapters/33-bigquery-ml.md)
- [8.5 — End-to-End Capstone](../chapters/34-end-to-end-capstone.md)

## 📖 Further Reading

- [GCP documentation hub](https://cloud.google.com/docs)
- [Google Cloud Architecture Center](https://cloud.google.com/architecture)
- [Google Cloud Skills Boost](https://cloud.google.com/learn/training)
- [BigQuery best practices for cost control](https://cloud.google.com/bigquery/docs/best-practices-cost-control)
- [Vertex AI documentation](https://cloud.google.com/vertex-ai/docs)
