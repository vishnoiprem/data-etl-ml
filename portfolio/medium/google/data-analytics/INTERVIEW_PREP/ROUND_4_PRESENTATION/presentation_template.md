# Round 4: Presentation Round - Complete Package
## 30 min Presentation + 15 min Q&A | Architecture Diagram + Migration Path + Best Practice Asset

---

## 🎯 Presentation Overview

| Component | Time | Format | Evaluation |
|-----------|------|--------|------------|
| **Presentation** | 20 min | Slides + live whiteboard | Technical depth, storytelling, business outcomes |
| **Live Diagram** | 5 min | Whiteboard drawing | Architecture clarity, GCP services, tradeoffs |
| **Migration Walkthrough** | 5 min | 1-page doc | Phased approach, risk mitigation, validation |
| **Q&A** | 15 min | Verbal | Depth, composure, "I don't know but..." |

---

## 📊 20-Slide Presentation Structure

### SLIDE 1: Title Slide (30 sec)
```
[Customer Name] — Modern Data Platform on GCP
Migration & Transformation | [Year]

Presented by: [Your Name], Data & Analytics Lead
[Your Company] → Google Cloud Consulting

KEY OUTCOMES:
• 100TB+ migrated | 28% cost reduction | 40% query performance gain
• 500+ self-serve users | ML-ready platform | Zero-downtime cutover
```

### SLIDE 2: Business Context (1 min)
```
WHY TRANSFORM?

BEFORE (On-Prem):
├── Teradata (80TB) + Hadoop (50TB) — $2.4M/yr OpEx
├── 6-hour batch SLA → business decisions delayed
├── 50 max concurrent users → self-serve blocked
├── 5 FTE ops team — scaling = 6-month procurement
└── No ML capability — data science = manual extracts

DRIVERS:
💰 Cost: CFO mandate - 25% reduction
⚡ Speed: Marketing needs daily → hourly insights
📈 Scale: 10x user growth planned
🤖 AI: Leadership mandate - "AI-ready by 2024"
🔒 Compliance: MAS-TRM, PDPA requirements
```

### SLIDE 3: Current State Architecture (1 min)
```
[DRAW LIVE ON WHITEBOARD - Practice 3 min]

┌─────────────────────────────────────────────────────────────┐
│                    CURRENT STATE (On-Prem)                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Teradata │  │  Hadoop  │  │ Oracle   │  │  Kafka   │    │
│  │ (80TB)   │  │ (50TB)   │  │ (10TB)   │  │ (Stream) │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │           │
│       └─────────────┼─────────────┼─────────────┘           │
│                     ▼                                         │
│            ┌─────────────────┐                               │
│            │  Informatica    │                               │
│            │  (ETL - 200+)   │                               │
│            └────────┬────────┘                               │
│                     │                                         │
│         ┌───────────┼───────────┐                            │
│         ▼           ▼           ▼                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │ Tableau  │ │  SAS/    │ │  Custom  │                     │
│  │ Server   │ │  R       │ │  Python  │                     │
│  └──────────┘ └──────────┘ └──────────┘                     │
│                                                              │
│  PAIN: Silos, batch-only, no governance, expensive, rigid   │
└─────────────────────────────────────────────────────────────┘
```

### SLIDE 4: Target State Architecture (2 min)
```
[DRAW LIVE ON WHITEBOARD - Practice 5 min]

┌─────────────────────────────────────────────────────────────┐
│                    TARGET STATE (GCP)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  SOURCE LAYER          INGESTION         STORAGE            │
│  ═════════════         ════════         ════════            │
│  ┌──────────┐  CDC    ┌──────────┐      ┌─────────────┐    │
│  │ Teradata │────────▶│ Datastream│─────▶│ GCS Landing │    │
│  │ Oracle   │         │  (CDC)   │      │  (Avro)     │    │
│  └──────────┘         └──────────┘      └──────┬──────┘    │
│  ┌──────────┐  Batch  ┌──────────┐             │           │
│  │ Hadoop/  │────────▶│ Dataproc │             ▼           │
│  │ Hive     │ (DistCp)│ (Spark)  │      ┌─────────────┐    │
│  └──────────┘         └──────────┘      │ GCS Curated │    │
│  ┌──────────┐  Stream ┌──────────┐      │ (Parquet)   │    │
│  │ Kafka    │────────▶│ Dataflow │─────▶└──────┬──────┘    │
│  └──────────┘         └──────────┘             │           │
│                                                 ▼           │
│                    ┌──────────────────────────────────┐    │
│                    │     BIGQUERY ENTERPRISE DW       │    │
│                    │  ┌─────────┐ ┌─────────┐ ┌─────┐  │    │
│                    │  │  Raw    │▶│ Staging │▶│Serving│  │    │
│                    │  │(Partition│ │ (dbt,   │ │(Part/ │  │    │
│                    │  │ by date)│ │ tests)  │ │Clust) │  │    │
│                    │  └─────────┘ └─────────┘ └─────┘  │    │
│                    └──────────────────────────────────┘    │
│                              │                              │
│        ┌─────────────────────┼─────────────────────┐        │
│        ▼                     ▼                     ▼        │
│ ┌─────────────┐      ┌─────────────┐      ┌─────────────┐  │
│ │ GOVERNANCE  │      │ ANALYTICS   │      │ AI / ML     │  │
│ │ (Dataplex)  │      │ (Looker)    │      │ (Vertex AI) │  │
│ │ • Lineage   │      │ • Dashboards│      │ • Feature   │  │
│ │ • Quality   │      │ • Self-serve│      │   Store     │  │
│ │ • Policy    │      │ • Embedded  │      │ • Training  │  │
│ │   Tags      │      │             │      │ • Serving   │  │
│ └─────────────┘      └─────────────┘      └─────────────┘  │
│                                                              │
│  SECURITY: VPC-SC │ CMEK │ IAM Conditions │ Policy Tags    │
└─────────────────────────────────────────────────────────────┘
```

### SLIDE 5: Why This Architecture? (2 min)
```
DECISION MATRIX: Why GCP Services?

| Requirement | Chosen | Alternatives Considered | Why Not |
|-------------|--------|------------------------|---------|
| Serverless DW | BigQuery | Redshift, Snowflake | True serverless, BQML native, Omni multi-cloud |
| Streaming | Dataflow | Kafka/Kinesis+EC2 | Exactly-once, unified batch/stream, no ops |
| Batch ETL | Dataproc Spark | EMR, Glue | Hive compat, managed metastore, image versioning |
| CDC | Datastream | DMS, custom | Serverless, schema evolution, low latency |
| Governance | Dataplex | Atlas, Purview | Column-level lineage, policy tags, DLP native |
| ML | Vertex AI | SageMaker, Databricks | BQML integration, Feature Store, unified |
| Security | VPC-SC+CMEK | Security Hub, Macie | Data exfiltration prevention, key sovereignty |

KEY PRINCIPLE: Managed > Self-managed. Serverless > Provisioned. Native > Bolt-on.
```

### SLIDE 6: Migration Approach (2 min)
```
4-PHASE MIGRATION: Zero-Downtime Strategy

PHASE 1: ASSESS (Weeks 1-2) ✅
├── DBSAT/Atlas inventory → 1,247 tables cataloged
├── Query log analysis → 3 workload tiers identified
├── TCO model approved → 28% savings projected
└── Risk register: 12 risks, 8 mitigated pre-migration

PHASE 2: PILOT (Weeks 3-6) ✅
├── 5 workloads: Core ETL, BI, ML Features, Ad-hoc, Regulatory
├── Data parity: 100% row counts, checksums match
├── Performance: P99 latency 2min vs 45min on-prem
└── Stakeholder sign-off: Business users validated reports

PHASE 3: MIGRATE (Weeks 7-22) 🔄
├── Historical: Dataproc Spark (parallel by partition)
├── CDC: Datastream → GCS → Dataflow → BQ (continuous)
├── Dual-write: 14-day validation, <0.05% discrepancy
└── Cutover: Read-only flip, DNS switch, 15-min RTO tested

PHASE 4: OPTIMIZE (Ongoing) 📈
├── Partition/clustering review monthly
├── Materialized views for top 20 aggregations
├── BI Engine for executive dashboards
└── Slot reservations: 3-yr commitment = 35% discount
```

### SLIDE 7: Security & Governance (1.5 min)
```
SECURITY BY DESIGN (Not Bolted On)

NETWORK:
✅ VPC-SC Perimeter: All data projects enclosed
✅ Private Service Connect: BQ, Dataflow, Vertex AI - no public IPs
✅ DNS: Private zones, no internet egress

ENCRYPTION:
✅ CMEK + Cloud HSM (FIPS 140-2 L3): Key sovereignty
✅ 90-day auto-rotation, separate key rings per region
✅ CSEK option for customer-controlled keys

DATA-LEVEL:
✅ Dataplex Policy Tags → DLP auto-classification
✅ Column masking: SSN → ***-**-1234, Email → u***@domain.com
✅ Row-level security: tenant_id = SESSION_USER()

GOVERNANCE:
✅ Column-level lineage: Source → BQ → Looker → Vertex AI
✅ Daily quality scans (Great Expectations in Dataplex)
✅ Business glossary: 500+ terms, owner, steward
✅ Audit: Cloud Audit Logs → Chronicle SIEM, automated evidence

COMPLIANCE: MAS-TRM ✅ | PDPA ✅ | PCI-DSS ✅
```

### SLIDE 8: Technical Challenges & Solutions (2 min)
```
TOP 3 CHALLENGES & HOW WE SOLVED

CHALLENGE 1: 5TB Dataflow Shuffle Skew (user_id=NULL = 40%)
├── Root cause: Legacy data quality, NULL customer_id
├── Solution: Salting + custom partitioner + Shuffle Service
├── Result: 14hr+OOM → 4hr success, pattern in best practices repo

CHALLENGE 2: 500 Teradata Stored Procedures → BigQuery
├── Root cause: Procedural logic, temp tables, dynamic SQL
├── Solution: Classification → 60% dbt models, 30% BQ Scripts, 10% retired
├── Result: 0 logic gaps, automated testing, 80% dev time reduction

CHALLENGE 3: Real-time CDC + Batch Reconciliation
├── Root cause: Eventual consistency, duplicate detection
├── Solution: Idempotency keys, watermark alignment, MERGE not APPEND
├── Result: Zero data loss, <0.01% discrepancy, automated alerts
```

### SLIDE 9: Results & Metrics (1.5 min)
```
QUANTIFIED OUTCOMES

FINANCIAL:
├── Infrastructure: $2.4M/yr → $900k/yr = **62% reduction** ($1.5M/yr saved)
├── Operations: 5 FTE → 1 FTE = **80% reduction** ($600k/yr saved)
├── License elimination: Teradata, Informatica, Tableau Server = **$400k/yr saved**
└── TOTAL ANNUAL SAVINGS: **$2.5M** (Payback: 4 months)

PERFORMANCE:
├── Query P99: 45 min → 2 min = **95% faster**
├── Concurrent users: 50 → 500+ = **10x scale**
├── Data freshness: 6 hours → 15 min = **24x faster**
├── Dashboard load: 30 sec → 2 sec = **15x faster** (BI Engine)

ADOPTION:
├── Self-serve analysts: 12 → 200+ = **16x**
├── Certified datasets: 0 → 150 = **Data trust established**
├── ML models in production: 0 → 12 = **AI enabled**
└── Customer NPS: N/A → **4.8/5**

EXPANSION:
├── Phase 2 signed: $2.5M (ML platform + real-time)
├── Reference for: 3 prospects, 2 Google Cloud Next talks
└── Best practices adopted: 3 partner firms, 15 projects
```

### SLIDE 10: AI Enablement (1.5 min)
```
PLATFORM → AI: From Migration to Innovation

VERTEX AI INTEGRATION:
├── Feature Store: 200+ features, point-in-time correctness
├── BQML → Vertex: Seamless model promotion (no data movement)
├── AutoML: 3 models in production (churn, LTV, next-best-action)
├── Custom Training: Distributed XGBoost on 50TB features
├── Online Prediction: <50ms p99, autoscaling endpoints
├── Model Monitoring: Drift detection, bias alerts, retraining triggers

USE CASES DELIVERED:
1. CHURN PREDICTION: AUC 0.89 → 15% retention lift = $40M ARR
2. NETWORK OPTIMIZATION: 23% fewer outage minutes
3. PERSONALIZATION: 34% CTR improvement on recommendations
4. FRAUD DETECTION: Real-time scoring, 99.2% precision

ROADMAP:
├── GenAI: Vertex AI Search + Conversation for customer support
├── MLOps: Kubeflow Pipelines → Vertex AI Pipelines migration
├── Feature Store v2: Embedding-based similarity search
```

### SLIDE 11: Best Practices Created (1 min)
```
REUSABLE ASSETS (Scaling Expertise)

1. MIGRATION RUNBOOK (Open-sourced internally)
   ├── 50-page playbook: Assess → Pilot → Migrate → Optimize
   ├── Checklists, runbooks, rollback procedures
   ├── Adopted by: 3 partner firms, 15 projects, 60% faster delivery

2. TERRAFORM MODULE: "GCP Data Foundation"
   ├── VPC, IAM, BQ, Dataplex, Composer, Monitoring
   ├── 15 configs → 1 module, 10 min environment spin-up
   ├── Used in: 8 customer engagements

3. DATAFLOW TEMPLATE LIBRARY
   ├── Ingest → Validate → Transform → Load patterns
   ├── Dead-letter, schema evolution, monitoring baked in
   ├── 12 templates, 500+ pipeline deployments

4. DATAPLEX POLICY PACKS
   ├── FinServ: PCI, MAS-TRM, SOX mappings
   ├── Healthcare: HIPAA, FHIR, de-identification
   ├── Retail: PCI, PII, customer 360 governance
   ├── Auto-applied via Terraform

ADOPTION METRICS:
├── 50+ consultants trained
├── 80% reduction in "how do I..." questions
├── 3 partner firms certified on assets
```

### SLIDE 12: Lessons Learned (1 min)
```
WHAT I'D DO DIFFERENTLY

1. INVEST EARLIER IN DATA QUALITY BASELINE
   - Spent 3 weeks in Pilot fixing source data issues
   - Next time: Automated profiling in Assess phase

2. PARTNER ENABLEMENT BEFORE ENGAGEMENT
   - SI ramp took 6 weeks → delayed Phase 3 start
   - Next time: Certification gate before SoW sign

3. BUSINESS USER VALIDATION AUTOMATION
   - Manual report comparison → slow, error-prone
   - Next time: Automated diff tooling in Pilot

4. COST GOVERNANCE FROM DAY 1
   - Slot reservations added in Month 6
   - Next time: Budget alerts + reservations in Pilot

5. DOCUMENTATION AS CODE
   - Wiki drift → stale docs
   - Next time: dbt docs + Data Catalog auto-sync
```

### SLIDE 13-20: Appendix Slides (Q&A Prep)
```
APPENDIX: DEEP-DIVE SLIDES (Have Ready)

SLIDE 13: Detailed Migration Timeline (Gantt)
SLIDE 14: Data Validation Framework (Great Expectations suites)
SLIDE 15: Cost Breakdown by Service (Monthly trends)
SLIDE 16: Performance Benchmarks (Before/After per workload)
SLIDE 17: Security Control Mapping (MAS-TRM, PCI, PDPA)
SLIDE 18: Partner Enablement Program Details
SLIDE 19: Team Structure & RACI
SLIDE 20: Future Roadmap (GenAI, Real-time, Multi-cloud)
```

---

## 🎨 Whiteboard Diagram Practice

### Must-Draw in 5 Minutes (Practice Until Automatic)

```
TARGET ARCHITECTURE - 5 MINUTE DRAW

Step 1 (30s): Draw 3 columns - SOURCE | INGESTION | TARGET
Step 2 (1min): Source boxes - Teradata, Hadoop, Oracle, Kafka
Step 3 (1min): Ingestion arrows - Datastream(CDC), Dataproc(Batch), Dataflow(Stream)
Step 4 (1min): GCS Landing → Curated → BigQuery (3 layers: Raw/Staging/Serving)
Step 5 (1min): Right side - Dataplex, Looker, Vertex AI
Step 6 (30s): Security callouts - VPC-SC box around all, CMEK lock icons, Policy Tags
Step 7 (30s): Labels - Partition by date, Cluster by customer_id, Edition commitment

PRACTICE: Draw from memory 5x. Time yourself. Get under 4 min.
```

---

## 📋 Migration Path Document (1-Page Handout)

```
MIGRATION PATH: TERADATA/HADOOP → BIGQUERY

CUSTOMER: [Name] | SCALE: 130TB | TIMELINE: 22 WEEKS

PHASE | WEEKS | WORKLOADS | TOOLS | KEY RISKS | MITIGATIONS
------|-------|-----------|-------|-----------|------------
ASSESS | 1-2 | Inventory (1,247 tables) | DBSAT, Atlas, Query logs | Incomplete docs | Stakeholder workshops
PILOT  | 3-6 | 5 workloads (ETL, BI, ML, Ad-hoc, Reg) | Dataproc, Dataflow, BQ | Custom UDFs | Rewrite prioritization
MIGRATE| 7-22| All workloads (phased) | Dataproc, Datastream, Dataflow | Data validation | Dual-write + reconciliation
OPTIMIZE| 22+| Ongoing | BQ partitioning, MVs, BI Engine, Reservations | Cost overrun | Budget alerts + CUDs

CUTOVER STRATEGY:
├── Dual-write: 14 days minimum, <0.1% discrepancy
├── Read-only flip: Teradata read-only → BQ primary
├── DNS switch: Connection string update, 15-min RTO
├── Rollback: CDC replay capability, tested 3x
└── Hypercare: 30 days, daily standups, 24/7 on-call

VALIDATION GATES (Each Phase):
✅ Row counts ±0.1% | ✅ Checksums match | ✅ Performance ≤ SLA
✅ Cost within model | ✅ Security scan clean | ✅ Business UAT sign-off
```

---

## 🏆 Best Practice Asset Catalog (Choose ONE to Present)

| Asset | Description | Adoption | Your Role |
|-------|-------------|----------|-----------|
| **Migration Runbook** | 50-page playbook + checklists | 3 partners, 15 projects | Author & maintainer |
| **Terraform: GCP Data Foundation** | VPC/IAM/BQ/Dataplex/Composer module | 8 engagements | Architect |
| **Dataflow Template Library** | 12 patterns (ingest/validate/load) | 500+ deployments | Lead developer |
| **Dataplex Policy Packs** | FinServ/Healthcare/Retail governance | 3 industries | Product owner |
| **Cost Governance Dashboard** | Real-time + forecast + optimization | 12 customers | Designer |

---

## ❓ Anticipated Q&A (Prepare 2-min Answers)

| Question | Your 2-Min Answer Framework |
|----------|----------------------------|
| **Why not Snowflake/Redshift?** | Technical: serverless, BQML, Omni. Commercial: pay-per-query, no cluster ops. Customer: "Only platform where data+AI unified." |
| **How handle 100TB initial load?** | Transfer Appliance for TBs, Storage Transfer for PBs, parallel Dataflow for transformation. Validated with pilot. |
| **Rollback plan if cutover fails?** | Dual-write CDC sync maintained. DNS flip-back <15 min. Teradata read-only mode. Tested 3 dry runs. |
| **How scale team for next 10 migrations?** | Runbook + Terraform + Template library = 1 consultant runs 3. Partner enablement = they deliver 70%. |
| **What if customer wants multi-cloud?** | BigQuery Omni (AWS/Azure), Anthos for compute, portable architecture (Terraform + dbt). |
| **How measure "delivery excellence"?** | KPIs: NPS >4.5, On-time >90%, Quality gate pass >95%, KT completion 100%, Margin >35%. |
| **Biggest technical mistake?** | [Honest answer] Underestimated data quality. Fixed: Automated profiling in Assess phase. |
| **How handle schema evolution post-migration?** | Avro/Protobuf schemas in Schema Registry. BACKWARD compatibility enforced. Dataplex policy tags for governance. |
| **Team composition for delivery?** | 1 Google Arch + 2 Partner Eng + 1 Customer SME per workstream. PMO oversees. |
| **Knowledge transfer approach?** | Shadow → Pair → Lead. 30/60/90 day plan. Customer engineers co-deliver Phase 2. |

---

## ✅ Presentation Day Checklist

- [ ] Slides final, version controlled, PDF backup on USB
- [ ] Whiteboard markers (black, blue, red, green) tested
- [ ] Architecture diagram drawn from memory <4 min
- [ ] Migration path doc printed (A3, color)
- [ ] Best practice asset demo ready (GitHub/Terraform/Notebook)
- [ ] Appendix slides hidden but accessible
- [ ] Water, clicker, adapter, charger packed
- [ ] 3-min elevator pitch memorized
- [ ] "I don't know, but here's how I'd find out" practiced

---

*Total prep: 20 hours (10 slides × 1hr + 5 whiteboard × 2hr + Q&A 5hr). Practice until fluent.*