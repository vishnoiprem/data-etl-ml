# Round 2: Technical Screen - All Questions by Topic
## Google Cloud Data & Analytics Lead, Cloud Consulting (Singapore)
### Duration: 60 minutes | Format: Whiteboard + Live Coding

---

## 📋 Topic Coverage & Weight

| Topic | Questions | Weight | Time |
|-------|-----------|--------|------|
| Migration Strategy | 4-5 | 25% | 15 min |
| Pipeline Design (Batch/Stream) | 3-4 | 20% | 12 min |
| BigQuery Mastery | 4-5 | 20% | 12 min |
| Data Quality & Governance | 2-3 | 10% | 6 min |
| Security & Compliance | 2-3 | 10% | 6 min |
| Database/Storage Decisions | 2 | 5% | 4 min |
| SQL & Programming | 3-4 | 10% | 5 min |

---

## 🔄 A. Migration Strategy (CRITICAL - Appears in ALL Mocks)

### Q1: Migrate 100TB on-premise Teradata/Hadoop to GCP - strategy & key services
**Expected:** Phased approach (Assess→Pilot→Migrate→Optimize), tools per phase, validation, cutover

### Q2: 500-node Cloudera with Hive metastore, Oozie → Dataproc + BigQuery + Composer - cutover plan with dry runs
**Expected:** Metastore migration, Oozie→Composer translation, dry run strategy, rollback

### Q3: Customer: 100TB Teradata + Hadoop - tools (BMS, Data Transfer Service, Dataproc)
**Expected:** Tool selection matrix, when each, limitations

### Q4: Migration phases: Assess→Pilot→Migrate→Optimize - your playbook
**Expected:** Detailed activities, timelines, gates, stakeholder per phase

---

## 🔧 B. Pipeline Design

### Q5: Design batch pipeline: GCS landing → Dataflow validation → BigQuery partitioned/clustered → Composer orchestration
**Expected:** Architecture diagram, Dataflow patterns, partitioning strategy, Composer DAG structure

### Q6: Design streaming pipeline: Pub/Sub → Dataflow → BigQuery - handle late data, duplicates, event-time vs processing-time
**Expected:** Windowing, watermarks, allowed lateness, deduplication, exactly-once

### Q7: Streaming vs batch tradeoffs - Lambda vs Kappa architecture
**Expected:** When each, complexity, latency, cost, your recommendation

### Q8: How orchestrate and monitor data workflows on GCP? (Composer, retries, idempotency, audit)
**Expected:** Composer vs Workflows, DAG best practices, monitoring stack

---

## ⚡ C. BigQuery Mastery (CRITICAL)

### Q9: Optimize slow/expensive BigQuery query scanning 2TB → 90GB
**Expected:** Partition pruning, clustering, column pruning, materialized views, BI Engine, slot estimation, caching

### Q10: BigQuery architecture - storage vs compute separation, slots, BI Engine
**Expected:** Colossus, Borg, slot mechanics, reservation models, BI Engine use cases

### Q11: Partitioning vs clustering - when to use each, max 4 clustering columns
**Expected:** Decision matrix, examples, anti-patterns

### Q12: BigQuery optimization: skew handling (one store 40% data), slot estimation, caching
**Expected:** Salting, custom partitioning, skew detection, query plan analysis

### Q13: Explain BigQuery pricing - on-demand vs editions vs reservations
**Expected:** $6.25/TB scanned, slot pricing, committed use discounts, cost control

---

## 🛡️ D. Data Quality & Governance

### Q14: Data quality handling - dead-letter, audit table, versioned contracts, Great Expectations
**Expected:** Multi-layer validation, DLQ pattern, schema registry, GE integration

### Q15: Schema evolution - backward compatibility, Avro/Protobuf, Schema Registry
**Expected:** Compatibility rules, migration strategy, producer/consumer coordination

### Q16: Data governance with Dataplex - lineage, quality scans, policy tags, glossary
**Expected:** Dataplex architecture, lake/zones/assets, policy tag taxonomy, DLP integration

---

## 🔐 E. Security & Compliance

### Q17: Secure data in GCP - IAM least privilege, VPC-SC, CMEK, policy tags, row-level security
**Expected:** Defense in depth, each layer purpose, implementation details

### Q18: Finance use case: MAS compliance - VPC-SC perimeter, CMEK, audit logs
**Expected:** MAS-TRM controls mapping, evidence automation, audit readiness

### Q19: Data storage location significance for MNCs - privacy laws, latency, DR
**Expected:** Data sovereignty, dual-region, org policies, cross-border transfer

---

## 🗄️ F. Database & Storage Decisions

### Q20: Design HA scalable database for global e-commerce: Cloud SQL vs Spanner vs Bigtable - decision matrix
**Expected:** Consistency, scale, latency, cost, SQL vs NoSQL, your decision framework

### Q21: When to use Cloud Storage vs BigQuery vs Bigtable vs Firestore
**Expected:** Access patterns, data model, scale, cost per service

---

## 💻 G. SQL & Programming

### Q22: Write Dataflow pipeline in Python for JSON logs processing
**Expected:** Beam SDK, DoFn, windowing, side inputs, testing

### Q23: SQL subquery vs CTE - when use which?
**Expected:** Readability, performance, materialization, recursive CTEs

### Q24: Normalization in SQL (1NF, 2NF, 3NF, BCNF) - tradeoffs for analytics
**Expected:** Definitions, denormalization for analytics, BigQuery STRUCT/ARRAY

### Q25: Common joins - INNER, LEFT, RIGHT, FULL, CROSS, SEMI, ANTI - when each
**Expected:** Venn diagrams, performance, BigQuery broadcast hints

### Q26: Programming: Java/Python/Go/C++ - data processing code example
**Expected:** Real code you've written, explain design choices

### Q27: Python vs Go for data engineering - decision criteria
**Expected:** Ecosystem, performance, team skills, deployment model

---

## 🏗️ H. Differentiation & Architecture

### Q28: Differentiate BigQuery vs Redshift vs Snowflake - serverless, BQML, pricing, multi-cloud
**Expected:** Comparison table, your talking points, customer conversation

### Q29: Modern data platform for retailer: GCS + Dataproc + BigQuery + Vertex AI (real-time + AI)
**Expected:** End-to-end architecture, AI integration points, Vertex AI Feature Store

### Q30: Integrate Vertex AI into BigQuery ML pipeline - feature store, training, serving
**Expected:** BQML → Vertex AI workflow, feature store, model registry, online/batch prediction

### Q31: Implement large-scale cloud project in corporate environment - steps
**Expected:** Landing zone, org policies, CI/CD, security review, stakeholder management

---

## 📊 I. Operations & Monitoring

### Q32: Backfill strategy - replay raw files, MERGE not APPEND, idempotency keys
**Expected:** Idempotency design, MERGE patterns, partition-level replay

### Q33: Monitoring - Cloud Monitoring alerts for freshness, row counts, data quality
**Expected:** SLIs/SLOs, alerting policies, notification channels, runbooks

### Q34: Pipeline failure RCA - Dataflow + Composer troubleshooting
**Expected:** Dataflow UI, worker logs, shuffle metrics, Composer task inspection

---

## 🎯 Whiteboard Expectations

### You MUST Draw (Practice 5-min each):
1. **100TB Migration Architecture** - Source → Ingest → Transform → Store → Govern → Serve
2. **Batch Pipeline** - GCS → Dataflow → BQ with partitioning/clustering
3. **Streaming Pipeline** - Pub/Sub → Dataflow (windows/watermarks) → BQ
4. **Security Layers** - VPC-SC → CMEK → IAM → Policy Tags → RLS
5. **Database Decision Tree** - Requirements → Cloud SQL/Spanner/Bigtable

### Code You MUST Write (Practice 10-min each):
1. **Dataflow Batch** - Read Parquet → Validate → Transform → Write BQ (partitioned/clustered)
2. **Dataflow Streaming** - Pub/Sub → Window → Dedupe → Write BQ
3. **Composer DAG** - Extract → Transform → Load → Quality → Alert
4. **BigQuery Optimization SQL** - Before/after with EXPLAIN output

---

## 📝 Mock Set Technical Focus

| Mock Set | Technical Emphasis |
|----------|-------------------|
| Set 1 | Hadoop→BigQuery migration, batch pipeline, BQ optimization |
| Set 2 | Streaming pipeline, lambda architecture, data quality, cost |
| Set 3 | BigQuery vs competitors, security, Composer vs Workflows |
| Set 4 | BQ architecture, Dataflow Python, Dataplex governance |
| Set 5 | Modern platform + AI, Vertex AI integration, large-scale impl |
| Set 6 | Global DB design, data cleaning, joins |
| Set 7 | Finance compliance, MAS-TRM, mean age N/A, subquery vs CTE |
| Set 8 | Data quality framework, backfill, monitoring, RCA |
| Set 9 | 500-node Cloudera migration, BQ skew, Pub/Sub backlog |
| Set 10 | Singapore retailer real-time, BQ partitioning vs clustering, Python vs Go |

---

## ✅ Technical Screen Scorecard
| Dimension | Weight | Pass Bar |
|-----------|--------|----------|
| Architecture Design | 25% | Complete, scalable, GCP-native, tradeoffs explained |
| BigQuery Expertise | 20% | Optimization checklist, architecture, pricing |
| Dataflow/Beam | 15% | Batch + streaming patterns, windowing, exactly-once |
| Migration Experience | 15% | 100TB+ real experience, tool mastery, cutover |
| Security/Governance | 10% | VPC-SC, CMEK, Dataplex, compliance mapping |
| Coding Ability | 10% | Clean Python/Beam, error handling, testing mindset |
| Communication | 5% | Clear diagrams, structured thinking, "I don't know but..." |

---

*Study each topic. Practice whiteboard drawings. Write code from memory. Target: 60 min full technical screen simulation.*