# Migration Strategies - Teradata/Hadoop → BigQuery
## Complete Playbook for 100TB+ Migrations

---

## 🎯 Migration Architecture (Draw This in 5 Minutes)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TERADATA/HADOOP → BIGQUERY MIGRATION                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SOURCE LAYER                    INGESTION LAYER              TARGET LAYER   │
│  ════════════════                ══════════════════           ════════════   │
│  ┌─────────────┐                ┌─────────────────┐           ┌───────────┐  │
│  │ Teradata    │────CDC──────▶│  Database       │──────────▶│  GCS      │  │
│  │ (100TB)     │   (DMS)      │  Migration Svc  │           │  Landing  │  │
│  └─────────────┘                └─────────────────┘           │  Zone     │  │
│  ┌─────────────┐                ┌─────────────────┐           └─────┬─────┘  │
│  │ Hadoop/     │───Batch─────▶│  Dataproc       │                 │        │
│  │ Hive/Spark  │   (DistCp/   │  (Spark ETL)    │                 ▼        │
│  │ (50TB)      │    Sqoop)    │                 │           ┌───────────┐  │
│  └─────────────┘                └─────────────────┘           │  GCS      │  │
│  ┌─────────────┐                ┌─────────────────┐           │  Curated  │  │
│  │ Oracle/     │───CDC──────▶│  Dataflow       │──────────▶│  Zone     │  │
│  │ PostgreSQL  │   (DMS)      │  (Streaming)    │           │ (Parquet) │  │
│  └─────────────┘                └─────────────────┘           └─────┬─────┘  │
│                                                                       │        │
│  ┌─────────────────────────────────────────────────────────────────┘        │
│  ▼                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      BIGQUERY — ENTERPRISE DATA WAREHOUSE           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Raw Layer    │─▶│ Staging      │─▶│ Serving      │              │   │
│  │  │ (Partitioned │  │ (dbt models, │  │ (Partitioned │              │   │
│  │  │  by date,    │  │  tests,      │  │  + Clustered,│              │   │
│  │  │  clustered)  │  │  docs)       │  │  MV, RLS)    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│           ┌────────────────────────┼────────────────────────┐              │
│           ▼                        ▼                        ▼              │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐   │
│  │ GOVERNANCE      │      │ ANALYTICS       │      │ AI / ML         │   │
│  │ (Dataplex)      │      │ (Looker /       │      │ (Vertex AI)     │   │
│  │ • Lineage       │      │  Data Studio)   │      │ • Feature Store │   │
│  │ • Quality       │      │ • Dashboards    │      │ • Training      │   │
│  │ • Policy Tags   │      │ • Self-serve    │      │ • Serving       │   │
│  │ • Glossary      │      │ • Embedded      │      │ • Monitoring    │   │
│  └─────────────────┘      └─────────────────┘      └─────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 4-Phase Migration Playbook

### PHASE 1: ASSESS (Weeks 1-2)
**Goal:** Complete inventory, risk register, cost model, stakeholder alignment

| Activity | Tool/Method | Output |
|----------|-------------|--------|
| **Schema Discovery** | Teradata: DBSAT, BTEQ scripts<br>Hadoop: Apache Atlas, Hive metastore dump | Complete DDL catalog: tables, views, SPs, UDFs, partitions |
| **Workload Profiling** | Query logs (Teradata DBQL, Hive query logs)<br>Analyze: frequency, complexity, SLA tiers | Workload classification: Tier 1 (critical), Tier 2 (daily), Tier 3 (ad-hoc) |
| **Data Profiling** | Row counts, null %, distinct %, min/max, patterns<br>Sample data quality assessment | Data quality baseline, anomaly detection |
| **Cost Modeling** | BigQuery estimator + Composer + Dataflow + Dataproc<br>Compare: On-prem TCO vs GCP 3-yr TCO | Business case with ROI, payback period |
| **Risk Register** | Custom UDFs, proprietary functions, SLA gaps,<br>Regulatory constraints, partner dependencies | Mitigation plans per risk |
| **Stakeholder Workshops** | Business users, DBAs, data engineers, security, compliance | Signed assessment sign-off |

**Gate Criteria:** ✅ Inventory >95% complete ✅ Cost model approved ✅ Risks mitigated

---

### PHASE 2: PILOT (Weeks 3-6)
**Goal:** Validate approach with 3-5 representative workloads

| Pilot Workload | Selection Criteria | Success Metrics |
|----------------|-------------------|-----------------|
| **Core ETL** | Complex transforms, multiple joins | Data parity 100%, latency < SLA |
| **BI Reporting** | High-concurrency, dashboard queries | Query performance ≤ on-prem |
| **ML Feature Store** | Wide tables, feature engineering | Feature parity, training time |
| **Ad-hoc Analytics** | Unpredictable query patterns | Cost per query within budget |
| **Regulatory Report** | Strict audit requirements | Compliance evidence automated |

**Pilot Activities:**
1. **Schema Translation:** Teradata → BigQuery (data types, partitioning keys, clustering)
2. **Code Translation:** Stored procs → Dataflow SQL / dbt models / BigQuery scripts
3. **Data Validation:** Row counts, checksums, column profiles, sample diffs (Great Expectations)
4. **Performance Baseline:** Slot utilization, bytes scanned, latency vs on-prem
5. **Stakeholder Sign-off:** Business users validate reports match

**Gate Criteria:** ✅ All 5 pilots pass data parity ✅ Performance meets SLA ✅ Cost within model

---

### PHASE 3: MIGRATE (Weeks 7-16)
**Goal:** Production migration with zero-downtime cutover

| Workstream | Approach | Tools |
|------------|----------|-------|
| **Historical Load** | Parallel Dataproc Spark jobs, partition by date | Dataproc, DistCp, Dataflow |
| **CDC Sync** | Continuous replication during migration | Database Migration Service (DMS), Datastream |
| **Code Refactor** | Stored procs → dbt/Dataflow/BigQuery scripts | dbt, Dataflow SQL, BQ Scripts |
| **Dual-Write** | Write to both systems, reconcile | Custom CDC consumers, reconciliation dashboards |
| **Validation** | Automated row-level comparison | Great Expectations, custom validation framework |
| **Cutover** | Read-only → BigQuery, DNS flip, decommission | Planned maintenance window |

**Migration Patterns by Workload:**

| Workload Type | Migration Pattern | Downtime |
|---------------|------------------|----------|
| **Append-only logs** | Historical backfill + CDC sync | Near-zero |
| **Slowly changing dimensions** | Full reload + CDC | Minutes |
| **Transactional (OLTP)** | DMS + dual-write + cutover | <30 min planned |
| **Complex ETL/SPs** | Refactor to dbt/Dataflow, parallel run | Phased |
| **ML Training Data** | Export → GCS → Vertex AI Feature Store | Zero |

---

### PHASE 4: OPTIMIZE (Ongoing)
**Goal:** Continuous cost/performance optimization

| Optimization | Frequency | Impact |
|--------------|-----------|--------|
| Partition/clustering review | Monthly | 40-60% scan reduction |
| Materialized view refresh | Daily/Weekly | 10-100x query speedup |
| BI Engine reservation | Quarterly | Sub-second dashboards |
| Slot reservation tuning | Monthly | 30-50% compute cost save |
| Dataplex policy enforcement | Continuous | Governance at scale |
| Storage lifecycle (GCS) | Quarterly | 60%+ storage cost reduction |

---

## 🛠️ Tool Selection Matrix

| Migration Need | Primary Tool | Alternative | When to Use |
|----------------|--------------|-------------|-------------|
| **Schema Migration** | dbt / Dataflow SQL | Manual DDL | Complex transforms need version control |
| **Bulk Data Transfer** | Dataproc (DistCp/Spark) | Storage Transfer Service | >10TB, custom transform needed |
| **CDC Replication** | Database Migration Service | Datastream + Dataflow | Heterogeneous sources, near-real-time |
| **Hive Metastore** | Dataproc Metastore | Manual HMS export/import | 1000s of tables, ACID tables |
| **Oozie → Composer** | Manual translation | Airflow migration toolkit | Complex DAGs, custom operators |
| **Validation** | Great Expectations | Custom SQL | Standardized, documented expectations |
| **Orchestration** | Composer (Airflow) | Workflows | Complex dependencies, Python operators |

---

## ✂️ Cutover Strategy (The "Make or Break" Moment)

### Pre-Cutover Checklist (T-7 days)
- [ ] Dual-write running 14+ days with <0.1% discrepancy
- [ ] All validation suites passing (Great Expectations)
- [ ] Business user UAT sign-off on all critical reports
- [ ] Rollback plan tested (DNS flip back, CDC replay)
- [ ] Support team trained on BigQuery debugging
- [ ] Cost alerts configured (50/75/90% thresholds)
- [ ] On-call rotation updated for GCP services

### Cutover Day Runbook
```
T-4 hours:  Freeze schema changes on source
T-2 hours:  Final CDC sync validation (row counts, checksums)
T-1 hour:   Switch read traffic to BigQuery (read replica / view)
T-0:        DNS flip / connection string update
T+15 min:   Validate critical dashboards loading
T+30 min:   Validate key API responses
T+1 hour:   Declare success / initiate rollback if needed
T+4 hours:  Decommission source read access
T+24 hours: Full decommission approval
```

### Rollback Triggers
- >1% data discrepancy in critical tables
- P99 query latency > 2x on-prem baseline
- Critical dashboard failures > 5 min
- Security/compliance audit failure

---

## 💰 Real Migration Metrics (Your Talking Points)

| Metric | Before (On-Prem) | After (GCP) | Improvement |
|--------|------------------|-------------|-------------|
| **Storage Cost** | $120k/mo (Teradata) | $25k/mo (BQ + GCS) | **79% reduction** |
| **Compute Cost** | $80k/mo (fixed cluster) | $45k/mo (slots + Dataflow) | **44% reduction** |
| **Query Latency (P99)** | 45 min | 2 min | **95% faster** |
| **Concurrent Users** | 50 | 500+ | **10x scale** |
| **Time to Insight** | 6 hours (batch) | 15 min (streaming) | **24x faster** |
| **Ops FTE** | 5 DBAs | 1 Cloud Engineer | **80% reduction** |
| **ML Readiness** | Manual exports | Vertex AI native | **Enabled** |

---

## 🎯 Interview Talking Points

### "Walk me through 100TB Teradata migration strategy"
1. **Assess (2 weeks):** DBSAT inventory, query log analysis, cost model, risk register
2. **Pilot (4 weeks):** 5 workloads covering ETL, BI, ML, ad-hoc, regulatory
3. **Migrate (10 weeks):** Dataproc for bulk, DMS for CDC, dual-write reconciliation
4. **Optimize:** Partition/clustering, MVs, BI Engine, slot reservations
5. **Governance:** Dataplex policies, lineage, quality scans from day 1

**Key differentiator:** "I run dual-write with automated reconciliation dashboards - business validates in real-time, not after cutover."

### "How do you handle custom Teradata UDFs?"
1. **Inventory:** Catalog all UDFs, classify (portable / rewrite / retire)
2. **Portable:** SQL UDFs → BigQuery UDFs (JavaScript or SQL)
3. **Rewrite:** Procedural → Dataflow Python / dbt macros / BQ Scripts
4. **Retire:** Push logic upstream (source) or downstream (BI layer)
5. **Validate:** Golden dataset comparison for each migrated UDF

### "What's your cutover risk mitigation?"
- **Dry runs:** 3 full dress rehearsals with production-scale data
- **Parallel run:** 14 days minimum dual-write with automated alerts
- **Rollback tested:** DNS flip-back rehearsed, <30 min RTO
- **Business validation:** Self-serve comparison tool for stakeholders

---

## 📝 Related Files
- `code/migration_validation.py` - Validation framework
- `notebooks/migration_validation.ipynb` - Interactive validation demo
- `bigquery_deep_dive.md` - BQ optimization for migrated tables
- `dataflow_patterns.md` - Migration pipeline patterns

---

*Last Updated: 2026-01-15 | For: Google Cloud Data & Analytics Lead Technical Screen*