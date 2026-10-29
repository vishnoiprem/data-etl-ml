# Round 2: Technical Architecture Screen
## Google Cloud Data & Analytics Lead — Cloud Consulting

---

### 🎯 Round Overview
| Attribute | Details |
|-----------|---------|
| **Duration** | 45-60 minutes |
| **Format** | Video + Shared Whiteboard (Google Docs / Excalidraw / Jamboard) |
| **Interviewer** | Senior Data Architect / Staff Engineer / Practice Lead |
| **Goal** | Validate technical depth, architecture judgment, GCP expertise, migration patterns |
| **Weight** | High — technical credibility gate |

---

### 📋 What They're Assessing

| Criteria | Minimum Bar | Strong Signal |
|----------|-------------|---------------|
| **Architecture Breadth** | Designs end-to-end data platforms | Connects ingestion → processing → serving → governance → ML |
| **GCP Data Services** | Knows BigQuery, Dataflow, Dataproc | Deep on partitioning, streaming, autoscaling, cost optimization |
| **Migration Patterns** | Knows 6 R's conceptually | Applies patterns with trade-offs, automation, validation |
| **Distributed Systems** | Understands Spark/Hadoop internals | Tuning, skew handling, checkpointing, exactly-once |
| **Decision Making** | Lists pros/cons | Uses ADR framework, quantifies trade-offs |
| **Scale & Cost** | Mentions optimization | Gives concrete numbers (TB, $, latency, slots) |

---

### 🖊️ Whiteboard Scenarios (Prepare All 5)

#### **Scenario 1: Enterprise Data Lake Migration (Most Likely)**
> **"A retail client has 500 TB on-prem Hadoop (HDFS, Hive, Spark, Impala). They want to move to GCP in 6 months. Walk me through your architecture."**

**Expected Structure:**
```
1. ASSESS (Week 1-2)
   ├── Inventory: pipelines, tables, users, SLAs, dependencies
   ├── Categorize: 6 R's (Rehost/Replatform/Refactor/Repurchase/Retire/Retain)
   ├── Risk: compliance, downtime tolerance, skill gaps
   └── Output: Migration Wave Plan + Effort Estimate

2. ARCHITECTURE DESIGN
   ┌─────────────────────────────────────────────────────────────┐
   │                    TARGET STATE (GCP)                       │
   ├──────────────┬──────────────┬──────────────┬────────────────┤
   │   INGEST     │  PROCESSING  │   SERVING    │  GOVERNANCE    │
   ├──────────────┼──────────────┼──────────────┼────────────────┤
   │ Cloud Storage│  Dataproc    │  BigQuery    │  Dataplex      │
   │ (landing)    │  (Spark)     │  (partition/ │  (lineage,     │
   │ Pub/Sub      │  Dataflow    │   cluster)   │   quality,     │
   │ Transfer Appl│  (streaming) │  Looker      │   catalog)     │
   │ iance        │  Composer    │              │  IAM/ACLs      │
   └──────────────┴──────────────┴──────────────┴────────────────┘

3. MIGRATION PATTERNS BY WORKLOAD
   ├── Batch ETL (Hive/Spark) → Dataproc (Replatform) → Validate row counts/checksums
   ├── Interactive SQL (Impala) → BigQuery (Refactor) → BI Engine for concurrency
   ├── Streaming (Kafka/Spark) → Dataflow (Refactor) → Exactly-once, windowing
   ├── ML Feature Pipelines → Vertex AI Feature Store + Dataflow
   └── Reporting (Tableau/PowerBI) → Looker (Repurchase) → Semantic layer

4. VALIDATION & CUTOVER
   ├── Dual-write / Shadow mode → Data diff (row, column, aggregate)
   ├── Reconciliation reports → Business user UAT
   ├── Cutover checklist → Rollback plan
   └── Hypercare (2 weeks) → Decommission

5. OPTIMIZATION (Post-Migration)
   ├── BigQuery: Partition/cluster, materialized views, slots
   ├── Dataproc: Autoscaling, preemptible VMs, shuffle optimization
   └── Cost: Labels, budgets, recommendations API
```

**Key Talking Points:**
- **Why Dataproc vs Dataflow?** "Batch/portable → Dataproc. Streaming/low-latency/managed → Dataflow."
- **Hive Metastore?** "Dataproc Metastore (managed) or self-managed on Cloud SQL — sync strategy critical."
- **Data Validation?** "Automated: row counts, checksums, schema, sample diff, statistical profiling."
- **Cost Control?** "BigQuery slots reservation, Dataproc preemptibles, Storage lifecycle policies."
- **Security?** "CMEK, VPC-SC, IAM conditions, column-level security, data masking."

---

#### **Scenario 2: Real-Time Analytics Platform**
> **"Design a real-time fraud detection pipeline: 1M events/sec, <100ms latency, ML scoring, audit trail."**

**Architecture:**
```
Pub/Sub (ingest, ordering keys) 
    → Dataflow (enrichment, windowing, feature engineering)
    → Vertex AI (online prediction, <50ms)
    → BigQuery (streaming inserts, partitioned by event_time)
    → Looker / Custom Dashboard (real-time)
    → Cloud Logging / Audit Logs (compliance)
```

**Deep Dive Areas:**
- **Dataflow:** Side inputs for reference data, stateful processing, custom windowing
- **Vertex AI:** Endpoint autoscaling, model monitoring, drift detection
- **BigQuery Streaming:** Buffer, partition decorators, _PARTITIONTIME
- **Exactly-once:** Pub/Sub exactly-once + Dataflow + BigQuery streaming = end-to-end

---

#### **Scenario 3: Lakehouse Governance (Dataplex Focus)**
> **"Client has 50+ data domains, 2000+ tables, needs unified governance, lineage, quality. How do you implement?"**

**Architecture:**
```
Dataplex Lake → Zones (Raw/Curated/Consumed) → Assets (BigQuery, Cloud Storage, Dataproc)
    → Data Catalog (technical + business metadata)
    → Data Quality (automated scans, rules, thresholds)
    → Data Lineage (column-level, cross-system)
    → IAM: Lake/Zone/Asset level, data stewards per domain
    → Policy Tags → Column-level access control
```

**Key:** Domain-oriented ownership, automated onboarding, measurable quality SLAs.

---

#### **Scenario 4: Cost Optimization Deep Dive**
> **"BigQuery costs exploded from $5K to $50K/month. Diagnose and fix."**

**Diagnosis Framework:**
```
1. IDENTIFY DRIVERS
   ├── INFORMATION_SCHEMA.JOBS_BY_PROJECT → Top queries by bytes billed
   ├── Slot utilization → Reservation vs. on-demand
   ├── Storage → Active vs. long-term (time travel, fail-safe)
   └── BI Engine / Materialized view costs

2. TOP FIXES (Priority Order)
   ├── Partition + Clustering (high cardinality filter columns)
   ├── Materialized Views (repeated aggregations)
   ├── Slot Reservations (predictable workloads, 40-60% savings)
   ├── Query Rewrites (SELECT *, JOIN order, CTE materialization)
   ├── Storage Tiering (long-term pricing, expiration policies)
   └── BI Engine (dashboards, 10x faster, fixed cost)

3. GOVERNANCE
   ├── Custom quotas per project/team
   ├── Budget alerts + Pub/Sub → Slack
   ├── Labels for chargeback
   └── Monthly optimization review
```

---

#### **Scenario 5: Multi-Cloud / Hybrid Architecture**
> **"Client keeps some data on-prem (sovereignty) but wants GCP for ML. Design hybrid."**

**Architecture:**
```
On-Prem: Private Cloud / Anthos / Edge
    ↔ Interconnect / VPN (dedicated, encrypted)
GCP: BigQuery Omni (query on-prem), Dataproc on Bare Metal, Vertex AI
    → Data sync: Datastream (CDC), Transfer Service
    → Governance: Dataplex across environments
    → Identity: Workforce Identity Federation
```

---

### 🛠️ Architecture Decision Record (ADR) Framework
**Use for EVERY technical answer:**

```
## ADR: [Decision Title]
**Status:** Proposed / Accepted / Superseded
**Context:** [Business/technical problem, constraints]
**Decision:** [What we chose]
**Alternatives Considered:**
  1. [Option A] — Pros / Cons / Cost / Risk
  2. [Option B] — Pros / Cons / Cost / Risk
**Consequences:**
  - Positive: [Benefits]
  - Negative: [Trade-offs, mitigation]
  - Risks: [Open risks, mitigation]
**Metrics:** [How we'll measure success]
**Rollback Plan:** [If wrong, how to revert]
```

**Example ADR:** "Choosing Dataflow over Dataproc for streaming ETL"
- Context: 1M events/sec, <5min latency, team knows Spark
- Decision: Dataflow (managed, autoscaling, exactly-once)
- Alt: Dataproc Structured Streaming — more control, but ops burden
- Consequence: Higher per-unit cost, less tuning — but faster delivery, lower risk

---

### ❓ Rapid-Fire Technical Questions (Be Ready)

| Topic | Example Questions |
|-------|-------------------|
| **BigQuery** | Partition vs cluster? Slot contention? Nested/repeated fields? BI Engine? |
| **Dataflow** | Batch vs streaming model? Watermarks/triggering? Side inputs? Flex templates? |
| **Dataproc** | Spark tuning (shuffle, skew, memory)? Init actions? Metastore options? |
| **Dataplex** | Lake/Zone/Asset hierarchy? Lineage granularity? Quality rule types? |
| **Composer** | Dynamic task mapping? Sensors vs deferrable operators? XCom limits? |
| **Pub/Sub** | Ordering keys? Dead letter topics? Exactly-once? Schema registry? |
| **Vertex AI** | Feature store (online/offline)? Pipeline components? Model monitoring? |
| **Security** | VPC-SC? CMEK? Column-level security? Data masking? IAM conditions? |
| **Migration** | 6 R's? Dual-write validation? CDC tools (Datastream, Striim)? Cutover? |

---

### ✅ Pass Checklist (During Interview)

- [ ] **Draw architecture** — clear layers, data flow, GCP services labeled
- [ ] **Explain trade-offs** — every choice has a reason + alternative considered
- [ ] **Quantify** — TB, events/sec, latency, $ cost, timeline, team size
- [ ] **Migrateatterns** — name 6 R's, apply to scenario
- [ ] **Governance** — lineage, quality, security, cost — not afterthought
- [ ] **Partner lens** — "Here's what SI team owns vs. what we own"
- [ ] **Ask clarifying questions** — "What's their downtime tolerance?" "Team skills?"

---

### 🔴 Red Flags

- ❌ "I'd just use BigQuery for everything"
- ❌ Can't explain Dataflow watermarks/triggers
- ❌ No migration validation strategy
- ❌ Ignores cost until asked
- ❌ No SI partner experience mentioned
- ❌ "Spark is better than Dataflow" (no nuance)

---

*Next: ROUND_3_CASE_STUDY.md*