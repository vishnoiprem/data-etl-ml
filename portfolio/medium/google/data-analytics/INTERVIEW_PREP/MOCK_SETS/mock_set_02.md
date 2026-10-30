# Mock Interview Set 2 - Technical Deep-Dive Focus
## Round 2 Variations: Architecture, Migration, Streaming, ML, Security

---

## 🎯 Mock Set 2 Overview
**Focus:** Technical depth variations - each mock tests a different technical domain
**Format:** 60-min technical deep-dive with different interviewer personas
**Goal:** Master each domain's "language" and tradeoff discussions

---

## MOCK 2A: BigQuery Optimization Specialist
### Interviewer: BigQuery Performance Engineer
### Focus: Query optimization, slot management, cost control, advanced features

---

### Questions

#### Q1: "A customer's dashboard query scans 5TB but returns 100 rows. It takes 4 minutes and costs $25/query. Fix it."
**Expected Answer Flow:**
1. **Diagnose:** `EXPLAIN ANALYZE` - check partition pruning, clustering, join order, shuffle
2. **Immediate:** Add partition filter (WHERE event_date >=), ensure clustering on filter keys
3. **Structural:** Materialized View for the aggregation, BI Engine reservation
4. **Advanced:** Parameterized queries, authorized views, slot reservation for predictable performance
5. **Governance:** `MAX_BYTES_BILLED` guardrail, cost dashboard alert

**Follow-up:** "What if they can't change the query (vendor BI tool)?"
→ Authorized view with partition/clustering, BI Engine, query rewrite via view.

---

#### Q2: "Explain slot contention. A customer has 2000 baseline slots. Morning 9-11am: 100% utilization, queries queue. Evening: 10% utilization. Solutions?"
**Expected Answer Flow:**
1. **Analyze:** `INFORMATION_SCHEMA.JOBS_TIMELINE` - identify workloads, users, query patterns
2. **Reservation Strategy:** Separate reservations per workload (BI, ETL, Ad-hoc, ML) with slot sharing
3. **Autoscaling:** Enable for burst, but set max to control cost
4. **Fair Scheduling:** Per-project/per-reservation fairness
5. **Workload Shifting:** Move non-urgent ETL to off-peak via Composer scheduling
6. **Query Optimization:** Reduce per-query slot consumption (partition, cluster, MV)

**Follow-up:** "How do you explain slot sharing to a CFO?"
→ "Think of it as a timeshare. You own 2000 slots. When BI isn't using them, ETL borrows them. When BI needs them back, ETL yields. You pay for 2000, get burst capacity free."

---

#### Q3: "Customer wants to migrate 500 complex Teradata stored procedures to BigQuery. Approach?"
**Expected Answer Flow:**
1. **Classify:** Automated inventory (sqlglot) - categorize by complexity
2. **Categories:** Pure SQL→dbt, Procedural→BQ Scripts, Dynamic→macros, DQ→Great Expectations, Obsolete→retire
3. **Validate:** Automated testing against query log golden records
4. **Phase:** Pilot 50 SPs first, measure parity, then scale

**Follow-up:** "What about dynamic SQL with EXECUTE IMMEDIATE?"
→ Refactor to parameterized dbt macros or BQ Scripts with EXECUTE IMMEDIATE (limited support). Document as technical debt.

---

#### Q4: "BigQuery vs Snowflake for a customer with multi-cloud mandate."
**Expected Answer Flow:**
1. **Acknowledge:** Multi-cloud is valid strategy
2. **BigQuery Omni:** Query AWS S3/Azure ADLS from BigQuery - same SQL, same governance
3. **Portability:** dbt models = portable SQL, Dataflow=Beam=portable, Terraform=multi-cloud
4. **Differentiator:** Unified AI (BQML→Vertex), serverless, no cluster mgmt
5. **Honest:** If they're all-in AWS and need zero-GCP, Snowflake makes sense. But for "multi-cloud with GCP as primary" - BigQuery wins.

---

## MOCK 2B: Dataflow Streaming Expert
### Interviewer: Dataflow Product Engineer
### Focus: Streaming patterns, exactly-once, windowing, troubleshooting

---

### Questions

#### Q1: "Design a pipeline: Pub/Sub → Dataflow → BigQuery. 100K events/sec. Exactly-once. <5min latency. Handle schema evolution."
**Expected Architecture:**
```
Pub/Sub (partitioned by key) → Dataflow (Fixed 1min windows, 10min allowed lateness)
    → Validate/Enrich (DoFn + side input for reference data)
    → Deduplicate (event_id + timestamp)
    → BigQuery Storage Write API (stream-level exactly-once)
    → Dead Letter Topic (failed validation)
    → Schema Registry (Avro, BACKWARD compat enforced)
```

**Key Configs:**
- `--experiments=shuffle_mode=service`
- `triggering=AfterWatermark.pastEndOfWindow().withEarlyFirings(AfterProcessingTime.pastFirstElementInPane().plusDelayOf(1min)).withLateFirings(AfterWatermark.pastEndOfWindow())`
- Side input refresh: `beam.pvalue.AsDict(reference_view)` with `PeriodicallyRefreshing` pattern

---

#### Q2: "Pipeline OOMs on shuffle. 5TB shuffle, 40% NULL keys. Fix."
**Expected Answer:**
1. **Root Cause:** NULL keys → single partition → skew
2. **Salting Partitioner:** Distribute NULLs across N salt buckets
3. **Pre-aggregation:** CombinePerKey before shuffle
4. **Shuffle Service:** Managed shuffle (no worker disk)
4. **Monitoring:** Shuffle bytes per key metric

---

#### Q3: "CDC from Oracle via Datastream → Dataflow → BigQuery. Dual-write validation for 14 days. Design reconciliation."
**Expected Answer:**
- Idempotency key (transaction_id) + source timestamp
- MERGE with ROW_NUMBER() partition by key, order by source_priority, timestamp
- Daily reconciliation job: row count, checksum, sample diff
- Alert on >0.1% discrepancy
- Watermark alignment between CDC and batch

---

#### Q4: "Batch vs Streaming in Beam - same code really? When does it break?"
**Expected Answer:**
- **Same:** Transform logic, DoFns, PCollection API
- **Different:** Source/sink connectors, windowing (ignored in batch), triggers, allowed lateness, watermarks
- **Breaks:** Side inputs (batch=materialized once, streaming=periodic refresh), stateful DoFns (timers only streaming), exactly-once sinks (different mechanisms)

---

## MOCK 2C: Migration Architect
### Interviewer: Migration Practice Lead
### Focus: End-to-end migration methodology, risk, validation, cutover

---

### Questions

#### Q1: "Walk me through your 4-phase migration methodology. Where do most projects fail?"
**Expected Answer:**
1. **Assess (2w):** Inventory, query analysis, TCO, risk register. FAIL: Incomplete inventory, no data profiling
2. **Pilot (4w):** 3-5 workloads, success criteria, Go/No-Go. FAIL: Pilot too narrow, success criteria vague
3. **Migrate (16w):** Historical (parallel), CDC (continuous), dual-write validation. FAIL: No automated validation, schema drift
4. **Optimize (ongoing):** Partition review, MV, BI Engine, reservations. FAIL: Never done, cost overrun

**Most Common Failure:** Skipping automated data profiling in Assess → Pilot spends weeks fixing source data quality.

---

#### Q2: "Customer has 100TB Teradata. 500 stored procedures. 200 Informatica workflows. 6-week timeline mandate. What do you say?"
**Expected Answer:**
1. **Reality Check:** "6 weeks is impossible for full migration. Here's what IS possible in 6 weeks:"
2. **Option A:** Pilot only (3 workloads) - validate approach, defer full migration
3. **Option B:** Lift-and-shift raw data only (no transformation) - high technical debt
4. **Option C:** Phase 1 = Core DW (50TB, 50 SPs) in 6 weeks. Phase 2 = Rest.
5. **My Recommendation:** Option C with clear scope, risk documented, Phase 2 funded.

---

#### Q3: "Cutover strategy for zero-downtime migration. Walk me through the runbook."
**Expected Answer:**
1. **Pre-cutover (T-7 days):** Final validation, DNS TTL lowered to 60s, rollback tested
2. **Cutover Day:**
   - T-2hr: Freeze schema changes
   - T-30min: Final CDC catch-up (lag < 1 min)
   - T-0: Teradata read-only, DNS flip, smoke tests (10 critical queries)
   - T+15min: Business validation (5 key reports)
   - T+30min: GO LIVE / ROLLBACK decision
3. **Rollback:** DNS flip-back, Teradata read-write, CDC replay (tested 3x)
4. **Hypercare (30 days):** Daily standups, 24/7 on-call, enhanced monitoring

---

#### Q4: "How do you handle schema evolution during 6-month migration?"
**Expected Answer:**
1. **Schema Registry:** Avro/Protobuf, BACKWARD compatibility enforced in CI/CD
2. **Pipeline Resilience:** Dataflow templates handle new fields (nullable), ignore deleted (alert), validate type changes
3. **Governance:** Dataplex policy tags, DLP re-scan on schema change, approval workflow
4. **Dual-Write Catches Drift:** Daily reconciliation compares schemas, alerts on mismatch

---

## MOCK 2D: ML/Vertex AI Integration
### Interviewer: Vertex AI Specialist
### Focus: BQML→Vertex, Feature Store, MLOps, serving

---

### Questions

#### Q1: "Customer has churn model in BQML (AUC 0.87). Wants real-time serving <50ms. Path to production?"
**Expected Answer:**
1. **Export:** `EXPORT MODEL` to GCS (SavedModel format)
2. **Upload:** `Model.upload()` to Vertex AI Model Registry
3. **Deploy:** Endpoint with `machine_type=n1-standard-4`, `min_replica_count=2`, `max_replica_count=20`
4. **Monitor:** Model Monitoring (drift, bias, feature attribution)
5. **CI/CD:** Vertex AI Pipelines for retraining (trigger: drift alert or schedule)

**Latency Optimization:** Feature Store online serving (<10ms), co-locate endpoint in same region, warm pool.

---

#### Q2: "Design Feature Store for real-time fraud. 200 features. Point-in-time correctness required."
**Expected Answer:**
- **Entity Types:** Customer, Transaction, Merchant
- **Feature Views:** Online (serving) + Offline (training) per entity
- **Sync:** Dataflow batch (daily) for offline, streaming (Pub/Sub→Dataflow) for online
- **Point-in-Time:** `get_feature_values(entity_ids, timestamp)` - returns feature values AS OF that timestamp
- **TTL:** Online store TTL 30 days, offline 2 years
- **Monitoring:** Feature distribution drift, missing value rate, staleness

---

#### Q3: "BQML vs Vertex AI AutoML vs Custom Training. Decision framework?"
**Expected Answer:**
| Use Case | Recommendation |
|----------|----------------|
| Tabular, structured, SQL team | BQML (linear, XGBoost, ARIMA) - no data movement |
| Tabular, want best accuracy, low code | Vertex AutoML Tables |
| Custom architecture, NLP, CV, complex | Custom Training (TensorFlow/PyTorch/JAX) |
| Distributed training, hyperparameter tuning | Custom Training + Vertex AI Vizier |
| Need Feature Store, MLOps, monitoring | Vertex AI (any path promotes to Vertex) |

**Key Insight:** Start with BQML. Promote to Vertex when need: online serving, Feature Store, MLOps, custom models.

---

#### Q4: "Model drift detected in production. Walk me through the response."
**Expected Answer:**
1. **Alert:** Model Monitoring → Pub/Sub → Cloud Function → Slack/PagerDuty
2. **Diagnose:** Drill down - feature drift? target drift? prediction drift? segment-specific?
3. **Immediate:** Canary rollback to previous model version (Endpoint traffic split)
4. **Root Cause:** Data quality? Concept drift? Seasonal? Upstream schema change?
5. **Remediate:** Retrain (Vertex AI Pipeline), validate (champion/challenger), promote
6. **Prevent:** Lower drift thresholds, add feature monitoring, data quality gates

---

## MOCK 2E: Security/Governance Architect
### Interviewer: Security Practice Lead
### Focus: VPC-SC, CMEK, Dataplex, compliance, data protection

---

### Questions

#### Q1: "Design VPC-SC perimeter for a FinServ data platform. Projects: Data Platform, ML Platform, Analytics, Shared Services. Requirements: No data exfiltration, MAS-TRM compliant."
**Expected Answer:**
```
PERIMETER DESIGN:
├── Perimeter 1: Data Projects (Data Platform, ML Platform, Analytics)
│   ├── Resources: BigQuery, GCS, Dataflow, Vertex AI, Dataplex, Composer
│   ├── Access Levels: Corporate IPs only (for dev), Service Accounts only (for prod)
│   └── Ingress/Egress: DENY ALL by default
│
├── Perimeter 2: Shared Services (DNS, Monitoring, Logging, KMS)
│   ├── Resources: Cloud DNS, Cloud Monitoring, Cloud Logging, Cloud KMS
│   └── Bridged to Perimeter 1 for: Monitoring, Logging, KMS
│
├── Private Service Connect: BigQuery, Dataflow, Vertex AI, Dataplex - no public IPs
├── DNS: Private zones (bq.dataplex.googleapis.com, etc.)
├── Egress Control: Cloud NAT for OS patching only, no data egress
└── Dry Run: 30 days before enforce, log violations to Chronicle
```

---

#### Q2: "CMEK vs CMEK+HSM vs CSEK. When to use each for MAS-TRM?"
**Expected Answer:**
| Option | Key Control | Rotation | FIPS 140-2 | MAS-TRM Fit | Cost |
|--------|-------------|----------|------------|-------------|------|
| **Google-managed** | Google | Auto (90d) | No | Baseline only | Free |
| **CMEK** | Customer (KMS) | Auto (90d) | Software | Good | $0.06/key/mo |
| **CMEK+HSM** | Customer (HSM) | Auto (90d) | **L3** | **Required for sensitive** | $1/key/mo + ops |
| **CSEK** | Customer (external) | Manual | Customer | Maximum control | Complex |

**MAS-TRM Recommendation:** CMEK+HSM for all PII/Financial data. CMEK for analytics. Separate key rings per data domain.

---

#### Q3: "Dataplex Policy Tags for column-level security. Design taxonomy for PCI-DSS + MAS-TRM."
**Expected Answer:**
```
TAXONOMY: projects/123/locations/asia-southeast1/taxonomies/finserv

POLICY TAGS (Hierarchical):
├── PII
│   ├── SSN (DLP: US_SSN, Mask: HASH_SHA256)
│   ├── Email (DLP: EMAIL, Mask: PARTIAL)
│   ├── Phone (DLP: PHONE, Mask: PARTIAL)
│   └── Name (DLP: PERSON_NAME, Mask: PARTIAL)
├── FINANCIAL
│   ├── Credit_Card (DLP: CREDIT_CARD, Mask: LAST4)
│   ├── Account_Number (Mask: LAST4)
│   ├── Salary (Mask: HASH)
│   └── Transaction_Amount (No mask, RLS by tenant)
├── HEALTH (if applicable)
│   ├── Patient_ID
│   └── Diagnosis_Code
└── RESTRICTED (PII + FINANCIAL combined)
    ├── Full_Customer_Profile
    └── Transaction_Detail_With_PII

ENFORCEMENT:
├── Column Masking: Automatic via policy tag
├── Row-Level Security: tenant_id = SESSION_USER()
├── DLP Auto-Classification: Daily scan → apply tags
└── Lineage: Column-level Source → BQ → Looker → Vertex
```

---

#### Q4: "Customer asks: 'How do I prove to auditors that no one accessed PII columns?'"
**Expected Answer:**
1. **Audit Logs:** BigQuery Data Read logs → filter by `authorizationInfo.permission=bigquery.tables.getData` + `policyTags` in schema
2. **Dataplex Lineage:** Column-level access tracking
3. **Policy Tag Reports:** Automated report: who accessed which tag, when, how many rows
4. **Chronicle SIEM:** Alert on anomalous access patterns (volume, time, user)
5. **Evidence Pack:** Monthly automated report for auditors

---

## Mock Set 2 Scoring

Each mock (2A-2E) scored independently:
| Dimension | Weight |
|-----------|--------|
| Technical Accuracy | 40% |
| Tradeoff Articulation | 30% |
| Production Reality (limits, quotas, ops) | 20% |
| Communication/Structure | 10% |

**Pass: ≥3.5/4.0 average across all 5 mocks**

---

## Practice Schedule (Mock Set 2)
| Day | Mock | Focus | Debrief Time |
|-----|------|-------|--------------|
| Day 1 | 2A | BigQuery Optimization | 30 min |
| Day 2 | 2B | Dataflow Streaming | 30 min |
| Day 3 | 2C | Migration Architecture | 30 min |
| Day 4 | 2D | ML/Vertex AI | 30 min |
| Day 5 | 2E | Security/Governance | 30 min |
| Day 6 | **Full 2A-2E Rotation** | Random order, timed | 60 min |

---

*Master each domain's vocabulary. The interviewer speaks "BigQuery" or "Dataflow" - you must be fluent in their dialect.*