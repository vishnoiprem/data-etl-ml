# Migration Path Document
## Teradata/Hadoop → BigQuery | 1-Page Executive Handout

---

## 📋 Migration Overview

| Attribute | Detail |
|-----------|--------|
| **Customer** | [Enterprise Customer - Singapore] |
| **Source Systems** | Teradata (80TB), Hadoop/Hive (50TB), Oracle (10TB), Kafka (Streaming) |
| **Target Platform** | Google Cloud BigQuery Enterprise + Dataflow + Dataproc + Vertex AI |
| **Total Data Volume** | 140TB initial + 5TB/day incremental |
| **Timeline** | 22 Weeks (Assess 2w, Pilot 4w, Migrate 16w, Optimize ongoing) |
| **Team** | 4 Google + 8 Partner + 4 Customer SMEs = 16 FTE |
| **Investment** | $1.2M Professional Services | **3-Year TCO Savings: $2.5M/yr (62%)** |

---

## 🗓️ Phased Migration Timeline

```
WEEK:    1-2      3-6       7-14      15-22      23+
         ▼        ▼         ▼         ▼          ▼
        ┌─────┐ ┌─────┐ ┌───────────┐ ┌───────┐ ┌────────┐
        │ASSESS│ │PILOT│ │  MIGRATE  │ │CUTOVER│ │OPTIMIZE│
        └─────┘ └─────┘ └───────────┘ └───────┘ └────────┘
         │      │       │            │         │
    Inventory  5 WL    Hist Load   Dual-Write  Partition
    Query Log  Parity  CDC Sync    14-day      Review
    TCO Model  Perf    Validation  Cutover     MV/BI Eng
    Risk Reg   Sign-off                RTO 15m   Reservations
```

### Phase 1: Assess (Weeks 1-2) ✅ **COMPLETE**
| Activity | Tool/Method | Output |
|----------|-------------|--------|
| Schema Inventory | DBSAT, Atlas, custom scripts | 1,247 tables cataloged, 2.3M columns |
| Query Log Analysis | Teradata DBQL, Hive query logs | 3 workload tiers, 847 unique queries |
| Data Profiling | Great Expectations, Dataplex DQ | Quality baseline, NULL rates, cardinality |
| TCO Modeling | Google TCO Calculator + custom | $2.4M on-prem → $900k GCP (62% savings) |
| Risk Register | Workshop + template | 12 risks identified, 8 pre-mitigated |

**Gate Criteria:** ✅ Stakeholder sign-off on scope, timeline, budget

---

### Phase 2: Pilot (Weeks 3-6) ✅ **COMPLETE**
| Pilot Workload | Source | Volume | Validation Result |
|----------------|--------|--------|-------------------|
| Core ETL (daily) | Teradata | 5TB/day | Row count ±0.01%, Checksum match, 45min→2min |
| Executive BI | Teradata | 200 dashboards | Visual parity, 30s→2s (BI Engine) |
| ML Feature Store | Hadoop | 10TB | Feature parity, training AUC match |
| Ad-hoc Analytics | Teradata | 50 concurrent | 500+ concurrent, <5s P99 |
| Regulatory Reporting | Oracle | 500 reports | 100% reconciliation, audit trail intact |

**Gate Criteria:** ✅ All 5 workloads pass data parity, performance, cost, security

---

### Phase 3: Migrate (Weeks 7-22) 🔄 **IN PROGRESS**

#### Wave 1: Historical Load (Weeks 7-14)
| Batch | Tables | Volume | Tool | Duration | Validation |
|-------|--------|--------|------|----------|------------|
| Wave 1A | Core_dims (50) | 2TB | Dataproc Spark | 6 hrs | ✅ |
| Wave 1B | Fact_sales (200) | 40TB | Dataproc Spark | 48 hrs | ✅ |
| Wave 1C | Fact_events (500) | 80TB | Dataproc Spark | 72 hrs | 🔄 |
| Wave 1D | Oracle (150) | 10TB | Dataproc Spark | 12 hrs | ⏳ |

**Parallelization Strategy:** Partition by date → 50 parallel Spark jobs per wave
**Validation:** Automated row counts + checksums + sample data diff per table

#### Wave 2: CDC Synchronization (Weeks 10-20, Overlapping)
| Source | Tool | Latency | Method | Validation |
|--------|------|---------|--------|------------|
| Teradata | Datastream → Dataflow | <5 min | CDC + MERGE | Dual-write reconciliation |
| Oracle | Datastream → Dataflow | <5 min | CDC + MERGE | Dual-write reconciliation |
| Kafka | Dataflow Streaming | <30 sec | Exactly-once | Event count reconciliation |

**Dual-Write Architecture:**
```
Source DB → Application → [Teradata + BigQuery simultaneously]
                    ↓
            Reconciliation Job (Daily)
            - Row counts per table
            - Checksums per partition  
            - Sample value comparison
            - Alert if discrepancy >0.1%
```

---

### Phase 4: Cutover (Week 21-22)

#### Cutover Runbook (15-minute RTO)
| Step | Action | Owner | Duration | Rollback Trigger |
|------|--------|-------|----------|------------------|
| 1 | Freeze Teradata writes (read-only) | Customer DBA | 2 min | N/A |
| 2 | Final CDC catch-up (verify lag=0) | Partner Eng | 5 min | Lag > 1 min |
| 3 | DNS/Connection string switch | Customer NetEng | 3 min | Connection failures |
| 4 | Smoke tests (10 critical queries) | Google Arch | 3 min | Any query fails |
| 5 | Business validation (5 key reports) | Business Users | 2 min | Data mismatch |
| 6 | **GO LIVE** | All | - | - |
| 7 | Monitor 30 min hypercare | All | 30 min | Any P1 alert |

#### Rollback Plan (Tested 3x in Pilot)
- **Trigger:** Any P1 during hypercare or business rejection
- **Action:** Flip DNS back → Teradata read-write → Resume CDC
- **RTO:** 15 minutes (validated)
- **Data Loss:** Zero (CDC replay from last checkpoint)

---

## ✅ Validation Framework (Every Phase)

### Automated Validation Suite
```python
# Pseudo-code: validation_framework.py
VALIDATION_CHECKS = {
    "row_count": {"threshold": 0.001, "action": "alert"},      # ±0.1%
    "checksum": {"threshold": 0, "action": "block"},           # Exact match
    "null_rate": {"threshold": 0.05, "action": "warn"},        # ±5% baseline
    "distribution": {"threshold": 0.02, "action": "warn"},     # KS test p>0.02
    "referential": {"threshold": 0, "action": "block"},        # FK integrity
    "freshness": {"threshold": "SLA", "action": "alert"},      # Per workload SLA
}
```

### Business Validation (UAT)
- **Report Comparison:** Automated pixel-diff + value-diff for 200 dashboards
- **Self-serve Testing:** 20 business analysts, 50 test scenarios each
- **Performance Benchmark:** 847 queries from query log, compare P50/P99
- **Sign-off:** Business stakeholder + Data Engineering Lead + Security

---

## ⚠️ Risk Register & Mitigations

| # | Risk | Likelihood | Impact | Score | Mitigation | Status |
|---|------|------------|--------|-------|------------|--------|
| 1 | Custom Teradata UDFs not portable | High | High | 9 | Inventory 500 SPs → 60% dbt, 30% BQ Script, 10% retire | 🟢 Mitigated |
| 2 | Data quality worse than profiled | Med | High | 6 | Pilot validates; dual-write catches drift; automated DQ scans | 🟢 Mitigated |
| 3 | Customer SME availability | High | Med | 6 | Contract: 2 dedicated SMEs 50%; escalation to VP | 🟡 Monitoring |
| 4 | SI resource gaps (certified) | Med | High | 6 | Named resources in SoW; bench clause; Google backup | 🟢 Mitigated |
| 5 | Network latency (on-prem ↔ GCP) | Low | High | 3 | Dedicated Interconnect 10Gbps; tested 2ms latency | 🟢 Mitigated |
| 6 | Regulatory approval delay (MAS) | Low | High | 3 | Early engagement Month 1; parallel prep; legal review | 🟢 Mitigated |
| 7 | Cost overrun | Med | Med | 4 | Fixed-price milestones; monthly reviews; budget alerts at 80% | 🟢 Mitigated |
| 8 | Schema evolution during migration | Med | Med | 4 | Schema registry (Avro); backward compatibility enforced | 🟢 Mitigated |
| 9 | Performance regression post-cutover | Low | High | 3 | BI Engine + MVs pre-warmed; slot reservation; 30-day hypercare | 🟡 Monitoring |
| 10 | Knowledge transfer incomplete | Med | Med | 4 | KT plan in SoW; shadow/pair/lead model; 30/60/90 day gates | 🟡 Monitoring |

---

## 💰 Financial Summary

### 3-Year TCO Comparison

| Category | On-Prem (3yr) | GCP (3yr) | Savings |
|----------|---------------|-----------|---------|
| Hardware (Depreciation) | $3.6M | $0 | $3.6M |
| Software Licenses | $2.1M | $0 | $2.1M |
| Support Contracts | $1.2M | $0.6M (Premium) | $0.6M |
| Facilities (Power/Cool/Rack) | $0.9M | $0 | $0.9M |
| FTE Operations (5 FTE) | $2.25M | $0.45M (1 FTE) | $1.8M |
| **GCP Consumption** | $0 | $3.24M | -$3.24M |
| **Professional Services** | $0 | $1.2M | -$1.2M |
| **TOTAL** | **$10.05M** | **$5.49M** | **$4.56M (45%)** |

### Annual Run Rate (Post-Migration)
| Component | Monthly | Annual |
|-----------|---------|--------|
| BigQuery (Storage + Compute + Reservations) | $45,000 | $540,000 |
| Dataflow (Streaming + Batch) | $18,000 | $216,000 |
| Dataproc (Batch windows) | $8,000 | $96,000 |
| Composer (Orchestration) | $3,000 | $36,000 |
| Storage (GCS Multi-region) | $5,000 | $60,000 |
| Network/Egress | $3,000 | $36,000 |
| Support (Premium) | $8,333 | $100,000 |
| **TOTAL MONTHLY** | **$90,333** | **$1,084,000** |

**vs On-Prem $2.4M/yr = 55% reduction** (62% including eliminated licenses)

---

## 🎯 Success Metrics & KPIs

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Query Performance (P99)** | 45 min | < 2 min | Query log analysis |
| **Concurrent Users** | 50 | 500+ | Looker/BI Engine metrics |
| **Data Freshness (Batch)** | 6 hours | 15 min | Pipeline timestamps |
| **Data Freshness (Stream)** | N/A | < 30 sec | Dataflow watermark |
| **Infrastructure Cost/yr** | $2.4M | $900k | Billing export |
| **Operational FTE** | 5 | 1 | Headcount |
| **Self-serve Analysts** | 12 | 200+ | Looker user count |
| **ML Models in Prod** | 0 | 12 | Vertex AI deployments |
| **Customer NPS** | N/A | > 4.5/5 | Quarterly survey |
| **Security Findings (Critical)** | 3/yr | 0 | Audit reports |

---

## 📞 Contacts & Escalation

| Role | Name | Contact | Escalation Level |
|------|------|---------|------------------|
| **Google Architecture Lead** | [Your Name] | [email/phone] | L3/L4 |
| **Google Delivery Lead** | [Name] | [email/phone] | L2 |
| **Partner Delivery Lead** | [Name] | [email/phone] | L2 |
| **Customer Technical Lead** | [Name] | [email/phone] | L1/L2 |
| **Customer Executive Sponsor** | [Name] | [email/phone] | L4 |
| **Security/Compliance** | [Name] | [email/phone] | L2/L3 |

---

## 📎 Appendix References
1. Detailed Workload Assessment (50 pages)
2. Pilot Validation Results (Evidence Pack)
3. Security Control Mapping (MAS-TRM, PDPA, PCI-DSS)
4. Terraform Infrastructure as Code (GitHub)
5. Dataflow Template Library (12 patterns)
6. Dataplex Policy Packs (FinServ/Healthcare/Retail)
7. Cost Model Assumptions & Sensitivity Analysis
8. Rollback Test Results (3 dry runs)

---

*Document Version: 1.0 | Classification: Confidential | Prepared for: [Customer] Executive Review*