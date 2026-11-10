# Round 1 RRK — Topic Deep-Dive (15-Year Depth)

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore)
**Purpose:** `ROUND_1_RRK.md` covers the *scenario* questions (Q1–Q35). This file covers the **technology topics** an L7 interviewer will probe, each answered at 15-year depth: trade-off, failure mode, number, and what you would do differently.
**Generic by design:** no personal metrics here, so it is safe in a public repo. Plug your own proof points in from your private notes.

---

## 0. How a 15-Year Answer Differs

Every topic answer climbs five rungs. Stop early and you sound mid-level.

| Rung | Mid-level stops here | Senior (15 yr) keeps going |
|---|---|---|
| 1. What it is | "Pub/Sub is a message queue" | one precise sentence, no marketing |
| 2. When / when not | rarely | "I choose X when…, and I avoid it when…" |
| 3. Trade-off | one pro/con | consistency vs latency vs cost vs ops burden |
| 4. Failure mode | none | "what breaks at 10x, and how you'd notice" |
| 5. Consulting angle | none | adoption, ownership, cost, migration risk, exit |

**Rule:** if you can't name a failure mode, you haven't run it in production. Say so and reason from first principles instead of bluffing.

---

## 1. Topic Coverage Map

| # | Topic | Where covered | Priority |
|---|---|---|---|
| 1 | BigQuery internals, design, optimisation | §2, course ch. 13–14 | 🔴 |
| 2 | Streaming: Pub/Sub, Dataflow, exactly-once | §3, ch. 16–17, 22 | 🔴 |
| 3 | Batch/Spark/Hadoop modernisation | §4, ch. 20–21 | 🟠 |
| 4 | Lakehouse: BigLake, Iceberg, open formats | §5, ch. 15 | 🔴 |
| 5 | Migration (Teradata/Hadoop/Snowflake/Oracle → GCP) | §6, ch. 18–19 | 🔴 |
| 6 | Governance: Dataplex, catalog, lineage, data mesh | §7, ch. 15 | 🟠 |
| 7 | Security: IAM, VPC-SC, CMEK, DLP, residency | §8, ch. 3, 27–28 | 🔴 |
| 8 | Orchestration & transformation: Composer, Dataform | §9, ch. 23–24 | 🟡 |
| 9 | Operational stores: Spanner, Bigtable, Cloud SQL | §10, ch. 8–11 | 🟡 |
| 10 | BI & semantic layer: Looker | §11, ch. 29 | 🟠 |
| 11 | ML/GenAI on data: BQML, Vertex AI, vector search, RAG, agents | §12, ch. 30–33 | 🔴 (2025+ hot) |
| 12 | FinOps | §13 + RRK Q12 | 🔴 |
| 13 | Reliability, DR, observability, data quality | §14 | 🟠 |
| 14 | Whiteboard reference architecture | §15 | 🔴 |
| 15 | Code review | `ROUND_1_RRK_CODE_REVIEW_DRILL.md` | 🔴 |
| 16 | Consulting/practice/people | `ROUND_1_RRK.md` Parts C–D | 🔴 |
| 17 | Competitors, SI partners, hybrid/sovereign | §18–20 | 🟠 |
| 18 | Errors in existing notes | §21 | 🔴 fix first |
| 19 | Ordered pass plan | §22 | 🔴 |

---

## 2. BigQuery

**Core model.** Storage (Colossus, columnar Capacitor) is separated from compute (Dremel slots); shuffle runs on a separate in-memory tier. You pay for bytes scanned (on-demand) or slot capacity (Editions: Standard / Enterprise / Enterprise Plus, with autoscaling and optional baseline commitments).

**Design levers, in the order you should reach for them**
1. **Partition** (time-unit, ingestion-time, integer-range) on the column used in nearly every filter. Set `require_partition_filter`. Limit: 10,000 partitions per table.
2. **Cluster** (up to 4 columns, order matters) on high-cardinality filter/join keys. Free pruning, no partition-count cap, re-clustering is automatic.
3. **Denormalise with nested/repeated fields** (`STRUCT`/`ARRAY`) instead of joining facts to child tables. Joins are shuffles; nesting avoids them.
4. **Materialised views / BI Engine** for repeated aggregate/dashboard patterns; **search indexes** for needle-in-haystack text/log lookups.
5. **Query hygiene:** select only needed columns, filter early, avoid `SELECT *`, avoid cross-joins and skewed joins, use `APPROX_COUNT_DISTINCT` where exactness isn't needed, prefer `QUALIFY` over self-join for top-N.

**Loading and DML**
- Batch load from GCS is free; streaming has a cost. Prefer the **Storage Write API** (committed type, offsets for exactly-once) over legacy `insertAll` (best-effort dedup via `insertId` only).
- DML is not OLTP: many tiny `UPDATE`/`MERGE` statements are slow and expensive. Batch them; use `MERGE` on partition-aligned keys.
- Recovery: **time travel** (default 7 days, configurable 2–7), then **fail-safe** (a further 7 days, Google-managed), plus table **snapshots** and **clones** for deliberate restore points.

**Governance inside BQ:** authorised views/datasets, row-level security, column-level security via policy tags, dynamic data masking, CMEK, `INFORMATION_SCHEMA` for audit and cost.

**Senior trade-offs**
- *On-demand vs Editions:* on-demand is simple and punishes bad queries; reservations give predictable cost and workload isolation (separate reservations for ETL vs BI vs ad hoc, so a runaway query can't starve dashboards). Choose reservations once spend is steady and attributable; keep on-demand for spiky/exploratory.
- *Logical vs physical storage billing:* physical wins on highly compressible data; check it per dataset, don't flip globally.
- *Multi-region vs region:* multi-region (US/EU) gives resilience and simplicity; a single region gives residency control and lower latency to co-located services. Residency law usually decides.

**Failure modes you should name:** partition-filter missing → full scans; skewed join key → one slot straggles; slot starvation in a shared reservation; schema drift breaking `SELECT *` views; runaway cross-join cost (guard with `maximum_bytes_billed`).

**One-liner to close:** *"BigQuery is cheap to start and expensive to leave ungoverned, so I attach cost controls, partitioning standards and reservations to the platform on day one."*

---

## 3. Streaming: Pub/Sub + Dataflow (Apache Beam)

**Pub/Sub:** global, serverless, **at-least-once** delivery; ordering via **ordering keys** (per-key, within a region); **exactly-once delivery** is available for pull subscriptions (regional); **dead-letter topics**, retry policy, **snapshots/seek** for replay; retention up to 7 days on subscriptions, up to 31 on topics; **BigQuery subscriptions** for direct write with no pipeline; Cloud Storage subscriptions for archive.

**Dataflow/Beam:** unified batch+stream model. The four questions: *what* (transforms), *where* (windows: fixed, sliding, session), *when* (triggers), *how* (accumulation mode). **Watermark** = system's estimate of event-time completeness; **allowed lateness** decides how long late data still updates a window; late data past that is dropped or side-output.

**Exactly-once, honestly.** Dataflow guarantees exactly-once *processing* inside the pipeline; end-to-end exactly-once is only as strong as the **sink**. Make the sink idempotent: Storage Write API offsets, `MERGE` on a deterministic business key, or dedup on `(event_id)` within a bounded window. State the assumption: duplicates come from producer retries *and* Pub/Sub redelivery, so dedup on a producer-assigned ID, not on Pub/Sub's message ID.

**Late/out-of-order design (a classic question):**
1. Use **event time**, not processing time.
2. Set a watermark and allowed lateness from observed lateness distribution (p99, not a guess).
3. Emit early/on-time/late panes; downstream tables tolerate **upserts** keyed by `(window, key)`.
4. Route too-late events to a **side-output / dead-letter** table and reconcile in a daily batch correction job.

**Operational knobs:** Streaming Engine + autoscaling (watch backlog age, not CPU), Flex Templates for repeatable deploys, `update`/drain for rollouts, FlexRS for batch cost, regional endpoints for residency.

**Flink/Kafka vs managed:** Kafka+Flink wins for sub-second stateful processing, custom connectors and portability; Pub/Sub+Dataflow wins for ops simplicity and elasticity. *Honest rule:* choose managed unless a hard latency/portability requirement forces self-managed, because engineer-hours on cluster ops are the hidden cost.

**Failure modes:** hot key stalls a stage; unbounded state growth from missing windows/TTL; poison messages blocking a subscription (fix: DLQ + max delivery attempts); backlog growth masked by healthy CPU.

---

## 4. Batch, Spark, Hadoop Modernisation

- **Dataproc** (managed Hadoop/Spark): choose for existing Spark/Hive code, ML libraries, or when rewrite cost exceeds run cost. Use **ephemeral job-scoped clusters**, **Dataproc Serverless** for Spark without cluster management, **Spot** secondary workers (never for masters / HDFS), autoscaling policies, and GCS (not HDFS) as the persistence layer so compute is disposable.
- **Dataflow vs Dataproc:** Dataflow for new pipelines and streaming; Dataproc to **lift existing Spark/Hive** with minimal rewrite. Don't rewrite 2,000 jobs for fashion.
- **BigQuery SQL over Spark:** if the logic is relational, push it into BigQuery (ELT) and delete the cluster. Keep Spark for non-SQL logic (complex ML, graph, unstructured).
- **Spark tuning checklist:** partition count vs cores, skew (salting/AQE), broadcast joins, avoid wide shuffles, columnar formats (Parquet/ORC), small-files compaction.
- **Hadoop exit path:** HDFS → GCS (Storage Transfer / `distcp`), Hive metastore → Dataproc Metastore/BigLake, Oozie → Composer, Ranger → IAM + policy tags.

---

## 5. Lakehouse: BigLake, Iceberg, Open Formats

**Why it's asked:** enterprises won't commit to one engine. Open table formats are the exit-cost answer.

- **BigLake:** unified fine-grained security (row/column) over data in GCS (and other clouds via Omni) accessed by BigQuery, Spark, Trino, etc.
- **Apache Iceberg** (also Delta, Hudi): ACID tables, schema evolution, hidden partitioning, time travel on object storage. BigQuery supports Iceberg via BigLake external tables and managed Iceberg tables.
- **When lakehouse over warehouse:** multi-engine access, very large cold data, regulatory need to keep data in a customer-controlled bucket, ML needing raw files. **When warehouse wins:** BI latency, concurrency, simplicity, governance out of the box.
- **Medallion layout** (bronze raw → silver conformed → gold served) is a *convention*, not an architecture. Defend it by what each layer guarantees (immutability, quality contract, SLA), not by name.
- **Trade-off to state:** open formats cost you some managed-engine optimisations (clustering, caching) in exchange for portability. Say which you'd pick *for this customer* and why.

---

## 6. Migration to GCP (very high probability)

**Frame:** `Assess → Plan → Migrate → Validate → Optimise`, executed per **wave**, not big-bang.

| Phase | Output |
|---|---|
| Assess | Inventory (jobs, tables, lineage, users, SLAs); usage-based dead-asset pruning (often 20–40% unused); complexity score per workload |
| Plan | Waves by business domain; target architecture; 6 Rs per workload (retire, retain, rehost, replatform, refactor, replace); cost/TCO baseline |
| Migrate | Schema + SQL translation (**BigQuery Migration Service** batch and interactive translators), data transfer (Transfer Service, Storage Transfer, Transfer Appliance, Datastream/CDC for live sources), pipeline port |
| Validate | **Parallel run** with automated reconciliation: row counts, per-column checksums/aggregates, sampled row diffs, business KPI parity |
| Optimise | Partition/cluster, cost controls, decommission source |

**Choices to defend**
- **Lift Hive/Spark first vs refactor to BigQuery:** lift-and-shift buys speed and de-risks the data-centre exit; refactor buys long-run cost. Sequence them: lift the exit-critical, refactor the high-value.
- **CDC (Datastream) vs batch:** CDC when downstream needs freshness or you need zero-downtime cutover; batch when the source can't tolerate load or the SLA is daily.
- **Cutover:** run old and new in parallel until KPI parity holds for N cycles (including a month-end), then flip consumers by domain, keep a rollback window, only then decommission.

**What actually kills migrations** (say this; it's the L7 insight): undocumented consumers, SQL dialect edge cases (implicit casts, NULL ordering, date semantics), data quality that was previously hidden, and **no decommission date** — so you pay for two stacks indefinitely. Always put a hard decommission milestone and owner in the plan.

---

## 7. Governance, Catalog, Lineage, Data Mesh

- **Dataplex** (Universal Catalog): discovery, metadata, **data quality scans**, profiling, **lineage** (BigQuery, Composer, Dataflow, Dataproc integrations), business glossary, data products.
- **Data mesh** = four ideas: domain ownership, data as a product, self-serve platform, federated computational governance. It is an **operating-model change**, not a tool. Don't recommend it to an org without domain teams that can own pipelines. Recommend a **hub-and-spoke** platform with shared standards first.
- **Data contracts:** producer-owned schema + semantics + SLA + owner, checked in CI; breaking changes need a version bump and consumer sign-off. This is the highest-leverage fix for silent-wrong-numbers (RRK Q9).
- **Policy tags + tag-based access** scale better than per-table IAM. Classify once (DLP), enforce everywhere.
- **Maturity ladder to propose:** inventory → ownership → quality SLOs → contracts → self-serve products.

---

## 8. Security, Compliance, Residency

**Layers (outside in):**
1. **Org & identity:** resource hierarchy, **org policies** (e.g. resource-location restriction for residency, disable SA key creation), least-privilege IAM, groups not users, IAM conditions, **Workload Identity Federation** instead of long-lived keys.
2. **Network/perimeter:** **VPC Service Controls** (exfiltration perimeter around BigQuery/GCS), Private Google Access / **Private Service Connect**, no public IPs on workers.
3. **Data:** **CMEK** (Cloud KMS; EKM when keys must live outside Google), column/row security, **Sensitive Data Protection (DLP)** for discovery, masking, tokenisation, de-identification.
4. **Assurance:** Cloud Audit Logs (Data Access logs on), Access Transparency/Approval, **Assured Workloads** for regulated regimes.

**APAC lens:** Singapore PDPA + MAS TRM/outsourcing guidelines (FSI), Thailand PDPA, Vietnam data-localisation decree, Indonesia PDP/GR71, GDPR for EU subjects. Principle: **classify → localise → minimise → log**. Where law restricts cross-border flow, keep raw/PII in-country, send only de-identified or aggregate data to a central region.

**Common trap:** "encrypted at rest" is table stakes (always on). The real question is **who can read it, from where, and can it be exfiltrated** — answer with IAM + VPC-SC + audit, not with encryption alone.

---

## 9. Orchestration & Transformation

- **Cloud Composer (Airflow):** DAG-per-domain, idempotent tasks, retries with backoff, SLAs/alerts, pools for concurrency, sensors sparingly (use deferrable operators), no heavy compute in the scheduler (trigger BigQuery/Dataflow/Dataproc instead). Version-control DAGs, test them (DAG integrity tests).
- **Dataform / dbt:** SQL transformations as code: dependency graph, assertions (uniqueness, non-null, row conditions), incremental models, environments, CI. Prefer for ELT inside BigQuery.
- **Workflows / Cloud Scheduler:** lightweight service orchestration; don't use Composer for a single cron.
- **Principles:** every task idempotent and re-runnable by partition; backfill is a first-class capability; one owner per DAG.

---

## 10. Operational Stores (pick the right database)

| Need | Choice | Why / watch-out |
|---|---|---|
| Global relational, strong consistency, scale-out | **Spanner** | TrueTime external consistency, up to 99.999% multi-region SLA; costs more, schema/key design matters |
| Familiar relational, moderate scale | **Cloud SQL / AlloyDB** | AlloyDB for Postgres + analytic acceleration; vertical scale limits |
| Huge key-value/time-series, low-latency | **Bigtable** | Row-key design is everything; avoid hotspotting (no sequential keys, use salting/reversed timestamps) |
| Document, mobile/web | **Firestore** | Offline sync, simple scaling |
| Cache | **Memorystore** | Redis/Valkey/Memcached |
| Analytics | **BigQuery** | Not for OLTP |

**Test:** *"Do you need joins and transactions (Spanner/SQL), or key lookups at massive scale (Bigtable), or scans/aggregations (BigQuery)?"* Say the access pattern before the product.

---

## 11. BI & Semantic Layer

- **Looker (LookML):** governed semantic layer in git, reusable measures/dimensions, one definition of "revenue" used everywhere; row-level access via user attributes; PDTs/aggregate awareness for performance; embedding for data products.
- **Looker Studio:** lightweight/self-service; weaker governance.
- **Why a semantic layer matters:** it's the answer to "two dashboards show different revenue." Metric definitions live in code with an owner, not in each analyst's SQL.
- **Performance:** push down to BigQuery, use BI Engine/materialised views, limit `SELECT *` explores, cache policies.
- **Adoption** is the real KPI: weekly active users, % of decisions made from governed metrics, number of shadow spreadsheets retired.

---

## 12. ML & GenAI on the Data Platform

**Predictive ML**
- **BigQuery ML:** train/predict in SQL (linear/logistic, boosted trees, k-means, ARIMA_PLUS, imported/remote models). Best for fast, governed, in-warehouse models and analyst-led use cases.
- **Vertex AI:** custom training, pipelines, Feature Store, Model Registry, endpoints, monitoring (skew/drift). Choose when you need custom frameworks, GPUs, online low-latency serving, or MLOps rigour.
- **MLOps basics to cite:** training-serving skew, feature reuse, versioned data + model + code, automated evaluation gates, canary rollout, drift monitoring, rollback.

**GenAI / agentic**
- **Gemini in BigQuery / BigQuery ML remote models:** call Gemini and embedding models from SQL (e.g. `ML.GENERATE_TEXT`, `ML.GENERATE_EMBEDDING`); **vector search** (`VECTOR_SEARCH`, vector indexes) in BigQuery; Vertex AI Vector Search for large-scale/low-latency retrieval.
- **RAG pattern:** ingest → chunk → embed → index → retrieve (hybrid keyword+vector) → rerank → ground the prompt → generate → cite. Quality lives in **chunking, retrieval and evaluation**, not in the model choice.
- **Data-platform angle (the consulting insight):** GenAI projects fail on **data readiness** — ungoverned sources, no lineage, PII leakage into prompts, no evaluation set. The Data & Analytics Lead's job is the governed, quality-checked, access-controlled corpus behind the model.
- **Guardrails:** PII redaction (DLP) before indexing, row/column security carried through to retrieval, prompt-injection defences, Model Armor/safety filters, audit logs of prompts/responses, human-in-the-loop for high-risk actions.
- **Evaluation:** golden question set, groundedness/faithfulness, retrieval recall@k, latency and cost per query; regression-test every prompt/model change.
- **Agents:** tool-using agents (Agent Development Kit / Agent Builder) over governed data tools; least-privilege tool scopes, idempotent tools, step/time/budget limits, full traces.
- **Honest trade-off:** buy/managed (Gemini Enterprise, Agent Builder) for speed vs build for control; start managed, build where differentiation is.

---

## 13. FinOps (pairs with RRK Q12)

**Visibility before optimisation:** billing export to BigQuery, **labels** on every resource, project-per-env/domain, `INFORMATION_SCHEMA.JOBS` cost by user/query/label, unit economics (cost per query, per TB served, per dashboard user).

| Lever | Saving mechanism |
|---|---|
| Partition/cluster + `require_partition_filter` | Cut bytes scanned |
| Reservations/Editions + autoscaling | Predictable spend, isolate workloads, committed-use discounts |
| `maximum_bytes_billed` / custom quotas | Hard cap on runaway queries |
| Storage: long-term pricing (auto after 90 days idle), physical billing where compressible, table expiry, GCS lifecycle/Autoclass | Cut storage |
| Dataproc ephemeral + Spot, Dataflow FlexRS, right-sizing | Cut compute |
| Delete unused tables/dashboards/pipelines | Often the largest single win |
| Committed-use / flex commitments | Rate discounts once usage is stable |

**Making savings stick:** chargeback/showback by domain, budgets + alerts, a weekly cost review with owners, and **guardrails in CI** (a lint that rejects unpartitioned tables). Without the guardrail, costs creep back in a quarter.

---

## 14. Reliability, DR, Observability, Data Quality

- **SLOs for data:** freshness, completeness, accuracy, availability. Define per data product, alert on **freshness breach**, not job failure alone (a job can "succeed" and load nothing).
- **Data quality tests:** schema, null/uniqueness, referential integrity, row-count deltas, distribution/anomaly checks, reconciliation to source, business-rule assertions. Gate promotion (bronze→silver→gold) on them; quarantine failures rather than blocking the whole run.
- **Observability stack:** Cloud Monitoring/Logging, lineage for blast-radius analysis, runbooks, on-call, error budgets, postmortems without blame.
- **DR:** define **RPO/RTO** per tier; BigQuery cross-region dataset replication / managed DR (Enterprise Plus), GCS dual/multi-region, infrastructure as code (Terraform) so the platform is reproducible, tested restore drills. Untested backups are not backups.
- **Change safety:** schema-change review, backward-compatible evolution, canary pipelines, feature flags, rollback plan in every change record.

---

## 15. Whiteboard Reference Architecture (draw this in 5 minutes)

```
 SOURCES                INGEST             STORE / PROCESS             SERVE / USE
 ────────               ──────             ───────────────             ───────────
 OLTP DBs  ──Datastream CDC──▶ ┐
 SaaS/APIs ──Transfer/Fusion─▶ ├─▶ GCS raw (bronze) ──▶ BigQuery silver ──▶ BigQuery gold ──▶ Looker (semantic)
 Files     ──Storage Transfer▶ ┤        │  Dataflow/Dataform/Spark          │                 ├─▶ ML: BQML / Vertex AI
 Events    ──Pub/Sub─▶ Dataflow ┘        ▼                                   ▼                 └─▶ GenAI: vector search / RAG / agents
                                   Dataplex: catalog · lineage · DQ · policy tags
 ───────────────────────────────────────────────────────────────────────────────────────────
 CROSS-CUTTING: IAM + VPC-SC + CMEK + DLP │ Composer orchestration │ Monitoring/SLOs │ FinOps labels │ Terraform + CI/CD
```

**How to narrate it (90 seconds):** requirements first (volume, latency, residency, consumers, SLAs) → ingestion by source type → layered storage with a quality contract per layer → serve via a governed semantic layer → cross-cutting security, governance, cost, reliability → **then** the trade-offs you made and what you'd revisit at 10x. End by naming the **operating model**: who owns each layer, how change is approved, how adoption is measured.

**Always state:** assumptions, what you deliberately left out, the biggest risk, and the first thing you'd build.

---

## 16. Rapid-Fire Drill (answer each in ≤45 seconds)

1. Partitioning vs clustering — when each, and when both?
2. How do you get exactly-once into BigQuery from Pub/Sub?
3. Late data arrives 6 hours after the window closed. What now?
4. Dataflow, Dataproc or BigQuery SQL for a nightly 5 TB transformation?
5. Design a Bigtable row key for IoT readings. What goes wrong with a timestamp prefix?
6. Spanner or Cloud SQL — what decides it?
7. How do you stop a `SELECT *` on a 200 TB table at 3 a.m.?
8. Hive metastore migration path to GCP?
9. What does VPC-SC protect against that IAM doesn't?
10. How do you keep PII out of an LLM prompt?
11. Two dashboards, two revenue numbers — root cause and permanent fix?
12. How do you prove a migrated warehouse is correct?
13. When is data mesh the wrong answer?
14. BigQuery reservations: how many, how split, how do you avoid noisy neighbours?
15. What is your rollback plan for a bad schema change?

**Self-grade:** each answer needs a choice, a reason, a failure mode. Missing one → redo it.

---

## 17. Study Schedule (7 days)

| Day | Focus | Output |
|---|---|---|
| 1 | §2 BigQuery + FinOps §13 | Explain partition/cluster/reservation choices aloud, 10 min |
| 2 | §3 Streaming | Draw late-data + dedup design from memory |
| 3 | §5–6 Lakehouse + Migration | Narrate a 5-wave migration plan with cutover and decommission |
| 4 | §7–8 Governance + Security | Draw the security layers; recite the APAC residency stance |
| 5 | §12 ML/GenAI | Whiteboard a governed RAG system incl. guardrails + eval |
| 6 | §15 Whiteboard + §16 drill | Two timed full architecture drills |
| 7 | `ROUND_1_RRK_CODE_REVIEW_DRILL.md` + RRK Parts C–D | One mock, recorded; review against the pass signals |

---

## 17A. Correctness Playbook (named explicitly in the recruiter's brief)

The brief lists these by name, so have a 45-second answer for each.

| Topic | Answer in one breath |
|---|---|
| **Idempotency / dedup** | Every write keyed by a deterministic business or event ID; re-running the same input yields identical output. Sink-side `MERGE`/upsert, not "hope for exactly-once." |
| **Late / out-of-order** | Event time + watermark + allowed lateness from the measured p99; upserts keyed by `(window, key)`; too-late data to a side output, reconciled in batch. |
| **Ordering** | Order only where it matters (per entity, via ordering key); otherwise carry a version/sequence number and let the sink keep the highest. Never rely on arrival order. |
| **Update/delete semantics** | CDC carries operation type + a monotonic source position (LSN/SCN). Apply as `MERGE` ordered by position; deletes are **tombstones/soft-deletes** first, hard-deleted on a retention schedule (needed for GDPR/PDPA erasure; must propagate to every derived table, backup and ML feature set). |
| **Schema evolution** | Additive/optional changes are compatible; type narrowing, renames, removed columns are breaking. Check in CI against a registry/contract; breaking change = new version + consumer sign-off + dual-publish window. |
| **Backfill** | Partition-scoped, idempotent, throttled, run in a separate lane from live traffic; write to a shadow table, reconcile, then swap. Never backfill in place. |
| **Restartability** | Checkpoints or partition watermarks; a killed job resumes with identical output; tested by killing it mid-run. |
| **Atomic publication** | Consumers never see half a load. Write to a staging table/partition, validate (counts, nulls, reconciliation), then publish in one step: partition swap / `CREATE OR REPLACE` / view repoint / write-audit-publish. Failed validation leaves the previous version live. |
| **Reversible cutover** | Dual-run, consumers switched by domain behind a flag/view, rollback = repoint, source kept read-only until N clean cycles including a month-end; decommission only after sign-off. |
| **Write-path security** | Validate and schema-check inputs, least-privilege service account per pipeline, no PII in logs, audit logging on, CMEK, no keys in code. |
| **Safe rollout** | Canary on one partition/domain, shadow comparison, feature flag, automated rollback trigger on a quality SLO breach. |

**Write-Audit-Publish (WAP)** is the phrase to use for atomic publication: *write* to staging, *audit* with assertions, *publish* atomically. It is also your answer to "silently wrong numbers."

---

## 17B. Executive Influence and Leadership Philosophy (brief sections d and f)

**Challenging an executive's unrealistic assumption (keeping trust):** separate the **outcome** from their **solution** → ask what decision this enables and by when → show the evidence (a one-page comparison with their option, an alternative, cost/risk/time) → give them a decision with a recommendation, not a veto → agree decision rights and a checkpoint → if overruled, document the risk, commit fully, and set an early-warning metric. Line: *"I can get you the date you asked for or the scope you asked for; here's what each costs and my recommendation."*

**Escalation (incl. GSI/partner and customer engineering leads):** escalate on **impact × reversibility × decision-right**, early, with options and a recommendation, never as a surprise. Raise with the peer first, then the sponsor, with facts not blame.

**Leadership philosophy (prepare a 3-sentence version in your own words):** 1) *Set a clear bar and context, then get out of the way.* 2) *Stay hands-on enough to be credible: read the design, review the code, hold the architecture line.* 3) *Measure the practice by what customers adopt and what the team can do without me.* Support each with one real example from your history.

**Staying technically current (brief says certification expected):** name the target certification (e.g. Professional Data Engineer or Professional Cloud Architect), a booked date, and the hands-on project you're building in the repo's GCP course. Dated beats vague.

**Practice tool:** run Google's *Interview Warmup* (grow.google/certificates/interview-warmup) for spoken-answer practice, and the *Architecture Framework / Cloud Architecture Center* data-analytics and AI/ML reference architectures for vocabulary.

---

## 18. Competitor One-Pager (open outstanding item — Q23)

Say where Google is **weaker**; that is the credibility marker. Pick by customer need, not by loyalty.

| Rival | Where it genuinely wins | Where Google wins | Your line |
|---|---|---|---|
| **Snowflake** | Mature multi-cloud data sharing/marketplace, simple ops, strong concurrency isolation story | Serverless BigQuery (no warehouse sizing), native ML/GenAI integration, streaming (Pub/Sub/Dataflow), price/perf at scale, open-format BigLake | "If the customer is multi-cloud and share-centric, Snowflake is a fair choice; if analytics + AI + streaming on one governed platform matters, BigQuery." |
| **Databricks** | Spark/Delta lakehouse depth, data-science workflow, notebook culture, strong open-source mindshare | Serverless SQL warehouse, tighter BI (Looker), lower ops, Vertex/Gemini; BigLake + Iceberg narrows the openness gap | "They're often **complementary**: Databricks for heavy Spark/ML, BigQuery for serving. Avoid a religious war." |
| **AWS (Redshift/EMR/Glue/Athena)** | Breadth of services, largest installed base, deep ecosystem | Cleaner serverless warehouse, global networking, data+AI integration | "Where the customer is already all-in on AWS, minimise friction: BigQuery Omni / open formats before forcing a move." |
| **Microsoft (Fabric/Synapse/Power BI)** | Power BI dominance, Microsoft 365/Entra integration, enterprise relationships | Scale-out analytics, openness, Looker semantic layer | "Power BI can stay as the front end on top of BigQuery." |

**Honest Google weak spots to concede:** smaller enterprise sales/partner footprint in some markets, perceived product churn (rename/deprecation risk), fewer in-region skilled engineers than AWS/Azure, and a historically more engineer-led than relationship-led motion. Counter with: the roadmap commitment, open formats (low lock-in), and the partner/PSO delivery model.

---

## 19. SI Partner Model (HOW_TO_PASS differentiator #2)

**Roles:** Google Cloud Consulting (PSO) owns **architecture, quality bar, accelerators, and adoption**; the **SI partner** supplies delivery scale (the "migration factory"); the **customer** owns data, decisions and run.
- **Engage when:** volume exceeds what a small PSO team can staff, the work is repeatable (hundreds of pipelines), or run/managed-service is needed.
- **Governance:** shared definition of done, quality gates (design review, code review, reconciliation sign-off), weekly burn-down, escalation path, SLAs on defects and rework, acceptance by outcome (validated waves) not by hours.
- **Risks to name:** partner juniors replacing seniors after sign-off, scope creep via change requests, knowledge not transferring to the customer, partner incentives diverging from cost optimisation.
- **Honest framing if you lack direct partner management:** "I've run large vendor/contractor delivery with SLAs and acceptance criteria; the partner model is the same discipline with a three-way commercial structure, and here's how I'd set it up."

---

## 20. Hybrid / Sovereign Architecture (Round 2 Scenario 5, refined)

- **Principle:** data stays where law requires; **compute and intelligence move to the data** where possible.
- **Options:** (1) **BigQuery Omni / BigLake** to query data in place on other clouds; (2) **Google Distributed Cloud** for on-prem/air-gapped with local residency; (3) replicate only **de-identified or aggregated** data to GCP, with raw PII kept in-country; (4) sovereign controls: **Assured Workloads**, EKM (keys held by the customer), partner-operated sovereign regions.
- **Connectivity:** Dedicated/Partner **Interconnect** (+ HA VPN as backup), Private Service Connect, consistent identity via Workforce Identity Federation.
- **Trade-off:** each in-place/hybrid choice adds latency, ops complexity and cost; choose the minimal hybrid surface that satisfies the legal requirement, and say what you'd simplify if the law changes.

---

## 21. Corrections to Existing Notes (Fix Before You Rehearse)

Sourced from cross-reading `ROUND_2_TECHNICAL_ARCHITECTURE.md` and the HOW_TO_PASS docs:

1. **"Pub/Sub exactly-once + Dataflow + BigQuery streaming = end-to-end"** (Round 2, Scenario 2) is too simple. End-to-end exactly-once depends on an **idempotent sink**; use the Storage Write API with offsets, or `MERGE` on a deterministic key. Say that (see §3).
2. **"BigQuery streaming inserts, `_PARTITIONTIME`"** is legacy phrasing. Prefer the Storage Write API and partition on **event time** (a real column), not ingestion pseudo-columns.
3. **"Slot reservations, 40–60% savings"** in `ROUND_2_TECHNICAL_ARCHITECTURE.md` is a rule of thumb, not a fact. Say "typically meaningful for steady workloads; I'd model it from the customer's actual slot-usage history before promising a number."
4. **"Preemptible VMs"** are now **Spot VMs**; say Spot.
5. **"Dataplex Lake/Zone/Asset"** is the older model; Dataplex now emphasises Universal Catalog, data products, quality scans and lineage. Know both vocabularies.
6. **Aspirational corpus figures** ("$2.1M → $12.3M ARR practice", "$2.5M / 120TB migration", "500TB FSI programme", "$5.4M revenue / 35% margin") are **not yours**. `ROUND_1_RRK.md` and `HOW_TO_PASS.md` already warn about these — keep that warning, and never borrow them as history. Overclaiming under challenge is the one hard fail.
7. **Fixed:** the "Migrateatterns" typo in `ROUND_2_TECHNICAL_ARCHITECTURE.md` is corrected — the checklist now reads "Migration patterns".

---

## 22. Pass Plan — Do In This Order

| # | Action | Time | Closes |
|---|---|---|---|
| 1 | Resolve the remaining `[TODO]`s in `ROUND_1_RRK.md` with real memory (baselines, attribution, stories) | 45 min | credibility probes |
| 2 | Say the **GCP-gap statement** aloud: *"My production depth is Spark/Kafka/Flink/Databricks; my Google Cloud work has been architect-level. Here is my dated 60-day plan."* | 10 min | biggest risk |
| 3 | Drill §2, §3, §6, §8, §12 until each answers in 45 s (use §16) | 2 days | technical depth |
| 4 | Whiteboard §15 and Round 2 Scenarios 1, 2, 4 timed, recorded | 1 day | Round 2 |
| 5 | Three timed code reviews (`ROUND_1_RRK_CODE_REVIEW_DRILL.md`) | 1 hr | Q15 |
| 6 | Write and rehearse the **"I was wrong"** story | 45 min | Googleyness |
| 7 | Rehearse Parts C + D of `ROUND_1_RRK.md` aloud | 2 hrs | level judgment |
| 8 | One 60-min mock, no notes, recorded | 1 hr | integration |

**Honesty rule (non-negotiable):** every number you say must have a baseline, a measurement method, and a reason it was you. When you don't know, say so, then reason it out.

---

## 23. The One Sentence

> *"The round asks whether you can already operate as a practice lead who is still technically credible. Prove scale and production judgment, be honest about the GCP and consulting-P&L gaps, and show a dated plan to close them."*

---

## 24. Closing Line For Each Technical Answer

*"I don't recommend a product, I recommend an operating model: the right service for each access pattern, governed and cost-controlled from day one, with an owner, an SLO and a decommission date for everything we build or retire."*

*"I don't recommend a product, I recommend an operating model: the right service for each access pattern, governed and cost-controlled from day one, with an owner, an SLO and a decommission date for everything we build or retire."*
