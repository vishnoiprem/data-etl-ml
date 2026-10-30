# My Case Study: Enterprise Data Platform Migration
## Singapore Financial Services Customer | 140TB | 22 Weeks | $2.5M/yr Savings

---

## 🎯 Case Study Overview

| Dimension | Detail |
|-----------|--------|
| **Customer** | Leading Singapore Bank (MAS-regulated) |
| **Industry** | Financial Services / Retail Banking |
| **Role** | Lead Data Architect (Google Cloud Consulting) |
| **Duration** | 22 Weeks (Feb–Jul 2024) |
| **Team** | 4 Google + 8 Partner (Accenture) + 4 Customer SMEs |
| **Scope** | Teradata 80TB + Hadoop 50TB + Oracle 10TB → BigQuery + Dataflow + Vertex AI |
| **Outcome** | 62% cost reduction, 95% faster queries, 10x concurrency, 12 ML models in production |

---

## 📖 STAR Narrative (2-Minute Version)

> **Situation:** A major Singapore bank needed to migrate 140TB from Teradata/Hadoop/Oracle to GCP. They faced $2.4M/yr OpEx, 6-hour batch SLAs, 50-user concurrency limit, and a MAS-TRM compliance mandate. The CFO mandated 25% cost reduction; the CDO mandated AI-ready platform by year-end.
>
> **Task:** As Lead Data Architect, I owned the end-to-end architecture, migration strategy, partner governance, and technical delivery for a 16-person team across Google, Accenture, and the bank.
>
> **Action:** I designed a 4-phase migration (Assess→Pilot→Migrate→Optimize) with dual-write validation, built a reusable Migration Runbook and Terraform module adopted by 3 partner firms, architected VPC-SC/CMEK/Dataplex governance for MAS-TRM compliance, and established a Cost Governance Dashboard saving 15% in month one.
>
> **Result:** Migrated 140TB in 16 weeks with zero data loss. Achieved 62% cost reduction ($2.5M/yr savings), 95% query performance improvement (45min→2min), 10x concurrency (50→500+), 24x data freshness (6hr→15min), and enabled 12 ML models in production (churn, fraud, personalization). The engagement expanded to a $2.5M Phase 2 for real-time analytics and GenAI.

---

## 📊 Detailed Results (Metrics That Matter)

### Financial Impact
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Infrastructure Cost/yr | $2.4M | $900k | **-62% ($1.5M saved)** |
| Software Licenses/yr | $700k | $0 | **-100% ($700k saved)** |
| Operations FTE | 5 | 1 | **-80% ($600k saved)** |
| **Total Annual Savings** | — | — | **$2.8M/yr** |
| Professional Services | $0 | $1.2M (one-time) | Payback: **4.5 months** |

### Performance Impact
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Query P99 Latency | 45 min | 2 min | **95% faster** |
| Concurrent Users | 50 | 500+ | **10x scale** |
| Batch Data Freshness | 6 hours | 15 min | **24x faster** |
| Streaming Latency | N/A | <30 sec | **New capability** |
| Dashboard Load Time | 30 sec | 2 sec | **15x faster** (BI Engine) |

### Adoption & Innovation Impact
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Self-serve Analysts | 12 | 200+ | **16x** |
| Certified Datasets | 0 | 150 | **Data trust established** |
| ML Models in Production | 0 | 12 | **AI enabled** |
| Customer NPS | N/A | 4.8/5 | **Best-in-class** |
| Phase 2 Expansion | $0 | $2.5M | **Pipeline growth** |

---

## 🏗️ Technical Architecture Delivered

### Target State (What We Built)
```
┌─────────────────────────────────────────────────────────────────────┐
│                    GCP DATA PLATFORM (PRODUCTION)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INGESTION                                                          │
│  ├── Datastream (CDC) → Pub/Sub → Dataflow → BigQuery  [Real-time] │
│  ├── Dataproc Spark (Batch) → GCS → BigQuery          [Historical] │
│  └── Dataflow Streaming (Kafka) → BigQuery              [Events]   │
│                                                                      │
│  STORAGE & COMPUTE                                                  │
│  ├── BigQuery Enterprise Edition (2000 baseline slots, 3yr CUD)    │
│  ├── GCS Multi-region (Raw/Curated zones, lifecycle policies)      │
│  ├── BI Engine (100GB reserved) for executive dashboards           │
│  └── Materialized Views (20 top aggregations, auto-refresh)        │
│                                                                      │
│  GOVERNANCE & SECURITY                                              │
│  ├── VPC-SC Perimeter (all data projects enclosed)                 │
│  ├── CMEK + Cloud HSM (FIPS 140-2 L3, 90-day rotation)            │
│  ├── Dataplex Lake (Raw Zone + Curated Zone, 1,247 assets)         │
│  ├── Policy Tags (47 FinServ tags: PII, Financial, Restricted)     │
│  ├── Column Masking (SSN, CC, Account) + Row-Level Security        │
│  ├── DLP Auto-classification (daily scans, auto-tag)               │
│  └── Column Lineage (Source → BQ → Looker → Vertex AI)             │
│                                                                      │
│  ANALYTICS & AI                                                     │
│  ├── Looker (500+ users, 200 dashboards, embedded analytics)       │
│  ├── BigQuery ML (3 models: churn, LTV, next-best-action)          │
│  ├── Vertex AI Feature Store (200+ features, point-in-time)        │
│  ├── Vertex AI Training (distributed XGBoost on 50TB)              │
│  ├── Vertex AI Online Prediction (<50ms p99, autoscaling)          │
│  └── Model Monitoring (drift detection, bias alerts, retrain)      │
│                                                                      │
│  ORCHESTRATION & OPERATIONS                                         │
│  ├── Composer 2 (Airflow 2.8, 15 DAGs, TaskGroups, SLAs)          │
│  ├── Cloud Monitoring (custom dashboards, SLO-based alerts)        │
│  ├── Cost Governance Dashboard (Looker, real-time + forecast)      │
│  └── Runbooks (migration, cutover, incident, optimization)         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Technical Decisions & Tradeoffs

| Decision | Options Considered | Chosen | Rationale |
|----------|-------------------|--------|-----------|
| **DW Platform** | BigQuery vs Snowflake vs Redshift | BigQuery Enterprise | Serverless, BQML native, Omni multi-cloud, pay-per-query |
| **Streaming** | Dataflow vs Kafka on GKE vs Kinesis | Dataflow | Exactly-once, unified batch/stream, no ops, BQ integration |
| **Batch ETL** | Dataproc vs Databricks vs Glue | Dataproc Spark | Hive metastore compat, managed images, cost (Spot VMs) |
| **CDC** | Datastream vs DMS vs Custom | Datastream | Serverless, schema evolution, low latency, BQ native |
| **Governance** | Dataplex vs Atlas vs Purview | Dataplex | Column-level lineage, policy tags, DLP native, BQ integration |
| **ML Platform** | Vertex AI vs SageMaker vs Databricks | Vertex AI | BQML→Vertex promotion, Feature Store, unified MLOps |
| **Security** | VPC-SC + CMEK vs Perimeter-only | VPC-SC + CMEK + HSM | Data exfiltration prevention, key sovereignty (MAS-TRM) |
| **Orchestration** | Composer vs MWAA vs Self-managed | Composer 2 | Serverless Airflow, BQ/Dataflow native operators, IAM integration |

---

## ⚠️ Top 3 Challenges & How We Solved Them

### Challenge 1: 5TB Dataflow Shuffle OOM (user_id=NULL = 40% of data)
**Context:** Streaming pipeline processing 100K events/sec. 40% had NULL customer_id from legacy data, causing massive shuffle skew. Pipeline OOM after 14 hours.

**Root Cause Analysis:**
```
Data Profile:
- Total events: 50M/hr
- user_id NULL: 20M (40%) → all routed to single shuffle partition
- Skew ratio: 40:1 (NULL partition vs avg partition)
- Shuffle bytes: 5TB → single worker OOM
```

**Solution Implemented:**
```python
# Custom partitioner with salting
class SaltedPartitioner(beam.Partition):
    def __init__(self, num_partitions, salt_buckets=100):
        self.num_partitions = num_partitions
        self.salt_buckets = salt_buckets
    
    def partition_for(self, element, num_partitions):
        user_id = element.get('user_id')
        if user_id is None:
            # Distribute NULLs across salt buckets
            salt = hash(element['event_id']) % self.salt_buckets
            return (salt * num_partitions // self.salt_buckets)
        else:
            # Normal hash partition for non-NULL
            return hash(user_id) % num_partitions

# Pipeline usage
valid_events | 'Partition' >> beam.Partition(
    SaltedPartitioner(num_partitions=200, salt_buckets=100).partition_for,
    200
)
```

**Additional Fixes:**
- Enabled Dataflow Shuffle Service (managed shuffle, no worker disk)
- Added `experiments=['shuffle_mode=service']`
- Pre-aggregation CombinePerKey before shuffle (reduce 5TB → 200GB)

**Result:** 14hr+OOM → 4hr success. Pattern documented in Dataflow Template Library.

---

### Challenge 2: 500 Teradata Stored Procedures → BigQuery
**Context:** 500 SPs with procedural logic, temp tables, dynamic SQL, cursors. Manual rewrite = 2+ years.

**Solution: Classification-Based Migration Strategy**

| Category | Count | Approach | Tool |
|----------|-------|----------|------|
| **Type 1: Pure SQL** | 180 (36%) | Direct translation → dbt models | sqlglot + custom rules |
| **Type 2: Procedural (loops, vars)** | 120 (24%) | Rewrite as BQ Scripts/Procedures | Manual + semi-auto |
| **Type 3: Dynamic SQL** | 80 (16%) | Refactor to parameterized dbt macros | Manual |
| **Type 4: Data Quality/Cleansing** | 70 (14%) | Push to Dataflow/DBT tests | Great Expectations |
| **Type 5: Obsolete/Unused** | 50 (10%) | **Retire** (validated via query logs) | N/A |

**Automation Built:**
```python
# sp_classifier.py - Classifies SP complexity
def classify_stored_proc(sp_code: str) -> dict:
    metrics = {
        'loc': count_lines(sp_code),
        'temp_tables': count_temp_tables(sp_code),
        'dynamic_sql': has_dynamic_sql(sp_code),
        'cursors': count_cursors(sp_code),
        'control_flow': count_control_flow(sp_code),
        'dependencies': extract_dependencies(sp_code),
    }
    
    if metrics['dynamic_sql'] and metrics['control_flow'] > 5:
        return {'type': 3, 'effort': 'high', 'approach': 'manual_refactor'}
    elif metrics['temp_tables'] > 3 or metrics['cursors'] > 0:
        return {'type': 2, 'effort': 'medium', 'approach': 'bq_script'}
    elif metrics['loc'] < 100 and not metrics['control_flow']:
        return {'type': 1, 'effort': 'low', 'approach': 'auto_translate'}
    else:
        return {'type': 4, 'effort': 'medium', 'approach': 'dq_pushdown'}

# Results: 60% auto-translated, 30% BQ Scripts, 10% retired
# Zero logic gaps found in UAT. 80% dev time reduction vs manual.
```

**Result:** All 500 SPs migrated in 8 weeks. Zero logic gaps in UAT. 80% dev time reduction.

---

### Challenge 3: Real-time CDC + Batch Reconciliation
**Context:** Dual-write for 14 days. CDC (Datastream→Dataflow) + Batch (Dataproc) writing to same tables. Need <0.1% discrepancy.

**Root Cause:** Eventual consistency, duplicate events, out-of-order delivery, schema drift.

**Solution: Idempotent MERGE with Watermark Alignment**

```sql
-- BigQuery MERGE with idempotency key + watermark
MERGE `project.serving.transactions` T
USING (
  SELECT 
    *,
    ROW_NUMBER() OVER (
      PARTITION BY transaction_id  -- Idempotency key
      ORDER BY 
        CASE WHEN _metadata.source = 'CDC' THEN 1 ELSE 2 END,  -- CDC wins
        _metadata.timestamp DESC
    ) AS rn
  FROM `project.staging.transactions_cdc_batch_union`
  WHERE _metadata.timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY)
) S
ON T.transaction_id = S.transaction_id AND S.rn = 1
WHEN MATCHED AND S._metadata.timestamp > T.last_updated_ts THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...
```

**Reconciliation Framework:**
```python
# daily_reconciliation.py
def reconcile_cdc_batch(cdc_table, batch_table, serving_table, date):
    checks = {
        'row_count': {
            'cdc': count(cdc_table, date),
            'batch': count(batch_table, date),
            'serving': count(serving_table, date),
            'threshold': 0.001  # 0.1%
        },
        'checksum': {
            'cdc': checksum(cdc_table, date),
            'batch': checksum(batch_table, date),
            'serving': checksum(serving_table, date),
            'threshold': 0  # Exact
        },
        'sample_diff': {
            'method': 'random_sample_1000',
            'compare': 'value_level_diff',
            'threshold': 0
        }
    }
    
    results = run_checks(checks)
    if any(r.failed for r in results):
        alert_pagerduty(f"Reconciliation failed for {date}: {results}")
        create_jira_ticket(results)
    return results
```

**Result:** 14-day dual-write, <0.05% discrepancy. Zero data loss. Automated alerts caught 3 schema drift issues pre-cutover.

---

## 🎓 Lessons Learned (What I'd Do Differently)

| # | Lesson | Applied in Next Engagement |
|---|--------|---------------------------|
| 1 | **Invest earlier in data quality baseline** | Automated profiling in Assess phase (Great Expectations suites generated from DBSAT) |
| 2 | **Partner enablement before engagement** | SI certification gate before SoW sign; named resources in contract |
| 3 | **Business user validation automation** | Built automated report diff tooling (pixel + value) in Pilot phase |
| 4 | **Cost governance from Day 1** | Slot reservations + budget alerts in Pilot; not Month 6 |
| 5 | **Documentation as code** | dbt docs + Data Catalog auto-sync; no more wiki drift |
| 6 | **Schema registry enforcement** | Avro/Protobuf in Schema Registry; BACKWARD compat enforced in CI/CD |
| 7 | **Hypercare metrics defined upfront** | P99 latency, error rate, freshness, cost/day dashboards ready at cutover |
| 8 | **Rollback tested, not documented** | 3 dry runs minimum; CDC replay capability validated |

---

## 📈 Business Value Delivered Beyond Migration

### Use Cases Enabled Post-Migration
| Use Case | Business Value | Technical Implementation |
|----------|----------------|-------------------------|
| **Churn Prediction** | 15% retention lift = $40M ARR | BQML XGBoost → Vertex AI, daily scoring |
| **Real-time Fraud Detection** | 23% fewer outage minutes | Dataflow streaming → Vertex AI Online Prediction (<50ms) |
| **Personalization Engine** | 34% CTR improvement | Feature Store + Vertex AI, real-time recommendations |
| **Regulatory Reporting** | 80% reduction in prep time | Certified datasets + Looker + automated evidence |
| **Network Optimization** | $12M OpEx savings | IoT sensor data → BigQuery GIS + Vertex AI |

### Assets Created & Reused
1. **Migration Runbook** → Used in 15 subsequent engagements
2. **Terraform GCP Data Foundation** → 8 customer environments
3. **Dataflow Template Library** → 500+ pipeline deployments
4. **FinServ Policy Pack** → 3 banking customers, MAS-TRM ready
5. **Cost Governance Dashboard** → 12 customers, 15% avg savings

---

## 🎤 Interview Presentation Tips

### If Asked: "Walk me through your most complex migration"
→ Use this case study. 2-min STAR, then offer deep-dive on any dimension.

### If Asked: "How do you handle technical risk?"
→ Reference the 3 challenges above. Show risk register, mitigation, validation.

### If Asked: "How do you scale your expertise?"
→ Reference the 5 reusable assets. Show adoption metrics.

### If Asked: "What's your biggest failure?"
→ Honest: "Underestimated data quality in Assess. Spent 3 weeks in Pilot fixing source issues. Fixed by automating profiling in Assess phase." Shows learning agility.

### If Asked: "How do you work with SI partners?"
→ "Co-architect model. Joint account planning, monthly scorecards, 4-level escalation. Partner delivers 70%, Google owns architecture/quality/KT. This engagement: Accenture delivered 8 FTEs, we governed quality."

### If Asked: "How do you handle security/compliance?"
→ "VPC-SC + CMEK + HSM + Dataplex policy tags + DLP auto-classify + column masking + RLS. MAS-TRM, PDPA, PCI-DSS all mapped to controls. Audit evidence auto-generated."

---

## 📎 Supporting Artifacts (Have Ready)
- [ ] Architecture diagram (Mermaid - can draw live)
- [ ] Migration timeline Gantt (1-page)
- [ ] Risk register (top 10 with mitigations)
- [ ] TCO model (3-year, sensitivity analysis)
- [ ] Validation framework code (GitHub)
- [ ] Cost dashboard screenshot (Looker)
- [ ] Partner scorecard template
- [ ] KT plan (30/60/90 day)

---

*This case study demonstrates: Technical depth at scale + Consulting delivery + Partner governance + Business outcomes + Reusable IP creation. All dimensions the Google Cloud Data & Analytics Lead role requires.*