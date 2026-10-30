# Architecture Diagrams — Draw from Memory in 5 Minutes
## Google Cloud Data & Analytics Lead Interview Whiteboard Reference

---

## 🎯 Diagram 1: 100TB Migration Architecture (Round 2/3/4)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    100TB TERADATA/HADOOP → GCP MIGRATION                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ON-PREMISE                          GCP (asia-southeast1)                 │
│  ┌─────────────────────┐              ┌─────────────────────────────────┐  │
│  │  TERADATA (50TB)    │              │  SHARED VPC (network-host)      │  │
│  │  HADOOP (50TB)      │              │  ┌─────────┐ ┌─────────┐       │  │
│  │  HIVE METASTORE     │              │  │ MGMT    │ │ DATA    │       │  │
│  │  OOZIE/AIRFLOW      │              │  │ 10.0.0  │ │ 10.0.1  │       │  │
│  └──────────┬──────────┘              │  └────┬────┘ └────┬────┘       │  │
│             │                         │       │        │              │  │
│    ┌────────┴────────┐                │  ┌────┴────┐ ┌──┴────┐        │  │
│    │ ASSESSMENT      │                │  │  PSC    │ │PSC    │        │  │
│    │ • BMS Scan      │                │  │BIGQUERY │ │STORAGE│        │  │
│    │ • Schema Map    │                │  └─────────┘ └───────┘        │  │
│    │ • Dependency    │                │  ┌─────────┐ ┌─────────┐      │  │
│    └────────┬────────┘                │  │ CLOUD   │ │ CLOUD   │      │  │
│             │                         │  │ ARMOR   │ │  NAT    │      │  │
│    ┌────────┴────────┐                │  └─────────┘ └─────────┘      │  │
│    │ PILOT (2 wks)   │                │                                │  │
│    │ • 1TB Sample    │                │  ┌─────────────────────────┐   │  │
│    │ • Validation    │                │  │ DATA PLATFORM PROJECT   │   │  │
│    │ • Performance   │                │  │ ┌──────┐ ┌──────┐      │   │  │
│    └────────┬────────┘                │  │ │ BQ   │ │ DP   │      │   │  │
│             │                         │  │ │(Part.)│ │Proc. │      │   │  │
│    ┌────────┴────────┐                │  │ └──┬───┘ └──┬───┘      │   │  │
│    │ MIGRATE (6 wks) │                │  │    │      │           │   │  │
│    │ Wave 1: Dims    │◀──DMS──────────│  │    ▼      ▼           │   │  │
│    │ Wave 2: Facts   │◀──Transfer Svc │  │  DATAPLEX (Governance)  │   │  │
│    │ Wave 3: History │◀──Dataproc     │  │  ┌─────┐ ┌─────┐      │   │  │
│    │ Wave 4: CDC     │◀──Datastream   │  │  │Lake │ │Quality│      │   │  │
│    └────────┬────────┘                │  │  └─────┘ └─────┘      │   │  │
│             │                         │  └─────────────────────────┘   │  │
│    ┌────────┴────────┐                │  ┌─────────────────────────┐   │  │
│    │ CUTOVER (1 wk)  │                │  │ VERTEX AI PROJECT       │   │  │
│    │ • Dual-write    │                │  │ ┌─────────┐ ┌─────────┐  │   │  │
│    │ • Reconciliation│                │  │ │Feature  │ │Model    │  │   │  │
│    │ • DNS Switch    │                │  │ │Store    │ │Registry │  │   │  │
│    └────────┬────────┘                │  │ └─────────┘ └─────────┘  │   │  │
│             │                         │  └─────────────────────────┘   │  │
│    ┌────────┴────────┐                │  ┌─────────────────────────┐   │  │
│    │ HYPERCARE (4 wk)│                │  │ COMPOSER (Orchestration) │   │  │
│    │ • Monitoring    │                │  │ ┌─────────────────────┐  │   │  │
│    │ • Optimization  │                │  │ │ Deferrable BQ Ops   │  │   │  │
│    │ • Knowledge Xfer│                │  │ └─────────────────────┘  │   │  │
│    └─────────────────┘                │  └─────────────────────────┘   │  │
│                                       └─────────────────────────────────┘  │
│                                                                             │
│  TOOLS: BMS → Dataproc → DMS → Transfer Svc → Datastream → BigQuery        │
│  VALIDATION: Row count ±0.1% | Checksum | Business Reconciliation          │
│  GOVERNANCE: VPC-SC | CMEK | Dataplex Policy Tags | Org Policies           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Draw Order (5 min):**
1. Two boxes: ON-PREM | GCP (Shared VPC)
2. On-prem: Teradata, Hadoop, Hive, Oozie
3. GCP: Shared VPC → subnets (mgmt, data) → PSC endpoints
4. Data Platform project: BigQuery (partitioned), Dataproc, Dataplex, Vertex AI
5. Migration waves with tool arrows (DMS, Transfer, Dataproc, Datastream)
6. Cutover: Dual-write → Reconciliation → DNS Switch
7. Governance layer: VPC-SC, CMEK, Policy Tags, Org Policies

---

## 🎯 Diagram 2: Batch Pipeline (Round 2/4)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BATCH PIPELINE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SOURCE                    INGEST                    PROCESS                  │
│  ┌─────────┐              ┌─────────┐              ┌─────────────────┐     │
│  │ GCS     │─────────────▶│ DATAFLOW│─────────────▶│ BIGQUERY        │     │
│  │ Landing │   (CSV/     │ Validate│   (Normalize │ │ Partitioned     │     │
│  │ Bucket  │    Parquet) │ + Norm  │    + Enrich) │ │ Clustered       │     │
│  └─────────┘              └────┬────┘              └────────┬────────┘     │
│                                 │                            │             │
│                                 ▼                            ▼             │
│                        ┌─────────────────┐         ┌─────────────────┐     │
│                        │ DLQ (Pub/Sub)   │         │ MERGE (Upsert)  │     │
│                        │ Categorized by  │         │ dedup_key =     │     │
│                        │ reject reason   │         │ partition:event │     │
│                        └─────────────────┘         └─────────────────┘     │
│                                                                             │
│  ORCHESTRATION                                                        ┌─────┐
│  ┌─────────────────────────────────────────────────────────────────────┐  │     │
│  │ COMPOSER (Airflow) DAG                                              │  │     │
│  │ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │  │     │
│  │ │Extract  │─▶│Transform│─▶│ Load    │─▶│ Quality │─▶│ Alert   │   │  │     │
│  │ │(GCS)    │  │(Dataflow)│ │(BQ)     │ │(Dataplex)│ │(DLQ)    │   │  │     │
│  │ └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │  │     │
│  │    Retry: 3x exponential backoff  |  Idempotent: MERGE on key       │  │     │
│  └─────────────────────────────────────────────────────────────────────┘  └─────┘
│                                                                             │
│  KEY PATTERNS:                                                             │
│  ✅ Partition key = event_dt (DATE) — 100x query savings                   │
│  ✅ Clustering = customer_id, event_type — colocation + sort               │
│  ✅ Dedup key = partition:event_id — exactly-once, retry-safe              │
│  ✅ DLQ categorized — alert on reject_counts by reason                     │
│  ✅ Currency enrichment via side input (BigQuery FX table)                 │
│  ✅ Deferrable BQ operator — releases worker slot during long jobs        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Draw Order (3 min):**
1. Left to right: GCS → Dataflow → BigQuery
2. Dataflow: Validate + Normalize (side input for FX)
3. BigQuery: Partitioned (event_dt) + Clustered (customer_id, event_type)
4. DLQ branch from Dataflow: categorized reject reasons
5. MERGE upsert with dedup_key
6. Composer DAG below: Extract → Transform → Load → Quality → Alert
7. Annotate key patterns in box on right

---

## 🎯 Diagram 3: Streaming Pipeline (Round 2/4)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STREAMING PIPELINE ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SOURCE              INGEST & WINDOW              ENRICH & SINK             │
│  ┌─────────┐         ┌──────────────────┐       ┌─────────────────┐        │
│  │ PUBSUB  │────────▶│ DATAFLOW         │──────▶│ BIGQUERY        │        │
│  │ Topic   │  (1M    │ • Fixed Windows  │       │ Streaming       │        │
│  │ events/ │   eps)  │   (5 min)        │       │ Inserts         │        │
│  └─────────┘         │ • Watermarks     │       │ Partitioned by  │        │
│                      │ • Allowed Late   │       │ event_dt        │        │
│                      │   (10 min)       │       │ Clustered by    │        │
│                      │ • Stateful Dedup │       │ customer_id     │        │
│                      └────────┬─────────┘       └────────┬────────┘        │
│                               │                          │                 │
│                      ┌────────┴────────┐         ┌───────┴────────┐        │
│                      │ SIDE INPUT      │         │ DLQ            │        │
│                      │ Customer Cache  │         │ (Pub/Sub)      │        │
│                      │ (Vertex AI      │         │ Categorized    │        │
│                      │  Feature Store) │         │ + Retry Topic  │        │
│                      └─────────────────┘         └────────────────┘        │
│                                                                             │
│  EXACTLY-ONCE SEMANTICS:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Deterministic Key: event_id + window_start                       │   │
│  │ 2. BagState stores processed keys per window                        │   │
│  │ 3. Timer fires at window.end + allowed_lateness → clears state      │   │
│  │ 4. Late data (within 10 min) processed in same window, dedup works  │   │
│  │ 5. Pub/Sub message ID + Dataflow bundle ID = end-to-end deduplication│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MONITORING:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Backlog (Pub/Sub) > 10K → Alert                                    │   │
│  │ • Latency p99 > 5s → Alert                                           │   │
│  │ • DLQ rate > 1% → Alert                                              │   │
│  │ • Worker CPU > 80% → Autoscale                                       │   │
│  │ • System lag (watermark) > 2 min → Alert                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Draw Order (3 min):**
1. Pub/Sub → Dataflow → BigQuery (streaming inserts)
2. Dataflow internals: Fixed windows (5min), Watermarks, Allowed lateness (10min)
3. Stateful dedup box: BagState + Timer
4. Side input: Customer cache (Vertex AI Feature Store)
4. DLQ branch: Categorized + retry topic
5. Exactly-once box: 5-step logic
6. Monitoring alerts box

---

## 🎯 Diagram 4: Security Layers (Round 2/3/5)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEFENSE IN DEPTH — GCP SECURITY                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 1: NETWORK PERIMETER                                          │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ VPC SERVICE CONTROLS (Perimeter)                                │ │   │
│  │ │ • Restricts: BigQuery, Storage, Pub/Sub, Dataproc, Vertex AI   │ │   │
│  │ │ • Egress: Only to approved projects (via access levels)         │ │   │
│  │ │ • Private Service Connect: All API access via PSC (no internet) │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ SHARED VPC (Hub-Spoke)                                          │ │   │
│  │ │ • Host: network-host (subnets: mgmt, data, dmz)                │ │   │
│  │ │ • Interconnect: 2×10Gbps Dedicated (HA) → On-prem DC1/DC2      │ │   │
│  │ │ • Cloud Armor: WAF, Geo-block, Rate limiting                   │ │   │
│  │ │ • Cloud NAT: No public IPs on workloads                        │ │   │
│  │ │ • Firewall: Default DENY, allow by tag + IAP                   │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 2: IDENTITY & ACCESS                                          │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ WORKFORCE IDENTITY FEDERATION (Okta/Azure AD → GCP)             │ │   │
│  │ │ • No SA keys (org policy: disableServiceAccountKeyCreation)     │ │   │
│  │ │ • MFA enforced, Context-Aware Access (device, location, IP)     │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ LEAST PRIVILEGE IAM                                             │ │   │
│  │ │ • Custom Roles: DataEngineer, DataScientist, DataAnalyst, Admin│ │   │
│  │ │ • IAM Conditions: time-bound, resource-tag, IP-based           │ │   │
│  │ │ • Principal Access Boundary: Limit scope of credentials        │ │   │
│  │ │ • Privileged Access Manager: Break-glass with approval         │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 3: DATA PROTECTION                                            │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ CMEK (Customer Managed Encryption Keys)                         │ │   │
│  │ │ • Cloud KMS: 90-day auto-rotation, key destruction = data loss │ │   │
│  │ │ • Per-service keys: BQ, Storage, Dataproc, Vertex AI, Pub/Sub  │ │   │
│  │ │ • DR key ring in asia-south1 (manual failover)                 │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ DATA CLASSIFICATION & GOVERNANCE (Dataplex)                     │ │   │
│  │ │ • Policy Tags: PII, PCI, SOX, MAS-TRM → enforced via IAM       │ │   │
│  │ │ • DLP API: Automated PII detection, de-identification          │ │   │
│  │ │ • Column-level lineage: Datastream → BQ → Looker               │ │   │
│  │ │ • Quality scans: Daily, 50+ rules (completeness, validity...)  │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ ROW-LEVEL SECURITY (BigQuery)                                   │ │   │
│  │ │ • Security policies: FILTER USING (region = session_user())    │ │   │
│  │ │ • Dynamic masking: SESSION_USER() for PII columns              │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 4: APPLICATION & WORKLOAD                                     │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ SHIELDED VMs: vTPM, Integrity Monitoring, Secure Boot          │ │   │
│  │ │ CONFIDENTIAL COMPUTING: AMD SEV / Intel TDX (encrypted memory) │ │   │
│  │ │ BINARY AUTHORIZATION: Attestation required for deploy          │ │   │
│  │ │ SECRET MANAGER: Auto-rotation, CMEK, no plaintext in code      │ │   │
│  │ │ WORKLOAD IDENTITY: GKE pods → GCP SA (no keys)                 │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MAS-TRM MAPPING:                                                          │
│  7.1 Network → VPC-SC, PSC, Interconnect, Cloud Armor                     │
│  7.2 Endpoint → Shielded VM, Confidential Computing, Binary Auth          │
│  7.3 IAM → WIF, Custom Roles, Conditions, PAM                            │
│  7.4 Data → CMEK, Dataplex Policy Tags, DLP, RLS                         │
│  7.5 App → Secret Manager, Binary Auth, Shielded VM                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Draw Order (4 min):**
1. Four horizontal layers (Network → Identity → Data → Workload)
2. Layer 1: VPC-SC perimeter box + Shared VPC details
3. Layer 2: WIF box + Custom Roles + IAM Conditions + PAM
4. Layer 3: CMEK box + Dataplex Policy Tags + DLP + RLS
5. Layer 4: Shielded VM, Confidential Computing, Binary Auth, Secret Manager
6. MAS-TRM mapping table at bottom

---

## 🎯 Diagram 5: Database Decision Tree (Round 2/5)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE SELECTION DECISION TREE                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  START: What are the requirements?                                          │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────┐                                                    │
│  │ Need horizontal     │──NO──▶ Cloud SQL (PostgreSQL/MySQL)               │
│  │ write scale >10K    │       • Vertical scale                             │
│  │ QPS?                │       • Regional HA (99.95%)                       │
│  └────────┬────────────┘       • SQL, ACID, familiar                       │
│       YES │                • Cost: $/vCPU-hour                              │
│       ▼                     │                                                │
│  ┌─────────────────────┐                                                    │
│  │ Need global         │──NO──▶ Spanner                                     │
│  │ distribution        │       • Horizontal scale (reads+writes)            │
│  │ (multi-region       │       • Global consistency (external)              │
│  │  strong consistency)?│       • SQL, ACID, auto-sharding                 │
│  └────────┬────────────┘       • 99.999% HA                                │
│       YES │                • Cost: $/node-hour + storage                   │
│       ▼                     │                                                │
│  ┌─────────────────────┐                                                    │
│  │ Time-series /       │──YES──▶ Bigtable                                   │
│  │ IoT / Wide rows?    │       • Massive scale (PB, millions QPS)           │
│  └────────┬────────────┘       • Single-row transactions                   │
│       NO  │                • No SQL, no secondary indexes                  │
│       ▼                     • Cost: $/node-hour + storage                  │
│                                                                             │
│  ┌─────────────────────┐                                                    │
│  │ Analytics /         │──YES──▶ BigQuery                                   │
│  │ Data Warehouse?     │       • Serverless, separation storage/compute     │
│  └────────┬────────────┘       • SQL, ANSI compliant                       │
│       NO  │                • Partition + Cluster = 100x savings            │
│       ▼                     • ML built-in (BQML), BI Engine                │
│                                                                             │
│  ┌─────────────────────┐                                                    │
│  │ Document /          │──YES──▶ Firestore                                  │
│  │ Flexible schema?    │       • Auto-scaling, real-time sync             │
│  └────────┬────────────┘       • Strong consistency (Datastore mode)      │
│       NO  │                • Cost: $/ops + storage                         │
│       ▼                     │                                                │
│  ┌─────────────────────┐                                                    │
│  │ Key-Value /         │──YES──▶ Memorystore (Redis/Valkey)               │
│  │ Cache / Session?    │       • Sub-ms latency                           │
│  └────────┬────────────┘       • HA, TTL, Pub/Sub                        │
│       NO  │                • Cost: $/GB-hour                              │
│       ▼                     │                                                │
│  DEFAULT: Cloud SQL (PostgreSQL) — safe default for most apps             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Draw Order (2 min):**
1. Start diamond → 5 decision diamonds in vertical flow
2. Each NO branches to service box with 3-4 bullet points
3. Default at bottom: Cloud SQL

---

## 🎯 Practice Regimen

### Daily (5 min each)
```
Mon: Migration Architecture (5 min)
Tue: Batch Pipeline (3 min)
Wed: Streaming Pipeline (3 min)
Thu: Security Layers (4 min)
Fri: Database Decision Tree (2 min)
```

### Weekly (Full Loop)
```
Saturday: All 5 diagrams sequentially (17 min total)
Sunday: Annotate each with talking points (10 min)
```

### Interview Simulation
```
1. Interviewer: "Design 100TB migration" → Draw Diagram 1 (5 min) → Explain (5 min)
2. Interviewer: "Batch pipeline for daily loads" → Draw Diagram 2 (3 min) → Explain (3 min)
3. Interviewer: "Streaming 1M eps" → Draw Diagram 3 (3 min) → Explain (3 min)
4. Interviewer: "Secure for MAS-TRM" → Draw Diagram 4 (4 min) → Explain (4 min)
5. Interviewer: "Global e-commerce DB" → Draw Diagram 5 (2 min) → Explain (2 min)
```

---

## 🎨 Drawing Tips

| Tip | Why |
|-----|-----|
| **Box → Arrow → Box** | Shows flow, not just components |
| **Label every arrow** | Tool name (DMS, Datastream, Transfer Svc) |
| **Annotation boxes** | Key patterns (exactly-once, partition pruning, 100x savings) |
| **Color code** (if pen): Green=GCP, Blue=On-prem, Red=Security, Orange=Data | Visual separation |
| **Number the steps** | 1. Assess 2. Pilot 3. Migrate 4. Cutover 5. Hypercare |
| **Practice on whiteboard** | Not paper — different muscle memory |

---

*Print this. Practice daily. In interview: draw clean, label everything, annotate with business outcomes (cost savings, compliance, latency).*