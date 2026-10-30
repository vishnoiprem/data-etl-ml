# Round 5: Cognitive & Behavioral Assessment
## Googleyness, Leadership, Singapore Context, Technical Fundamentals, Objection Handling

---

## 🎯 Round 5 Overview

| Component | Format | Duration | Focus |
|-----------|--------|----------|-------|
| **Googleyness/Values** | Behavioral interview | 30 min | Humility, learning agility, user focus, comfort with ambiguity |
| **Leadership/Strategy** | Case discussion | 30 min | Team building, partner mgmt, P&L, hiring, culture |
| **Singapore/APAC Context** | Scenario-based | 15 min | MAS-TRM, PDPA, data residency, partner ecosystem |
| **Technical Fundamentals** | Rapid-fire Q&A | 15 min | Core GCP services, architecture principles, tradeoffs |
| **Objection Handling** | Roleplay | 15 min | Customer pushback on cost, security, lock-in, timeline |

---

## 🧠 Googleyness & Values (Core Assessment)

### Google's 4 Core Attributes (from hiring docs)
| Attribute | What It Means in Consulting | Interview Signals |
|-----------|----------------------------|-------------------|
| **Humility & Learning Agility** | "I don't know, but here's how I'll find out" + applies learning fast | Admits gaps, shares specific learnings, asks clarifying questions |
| **User Focus** | Customer outcomes > utilization, long-term > short-term | Frames technical decisions in business impact, pushes back on scope creep that hurts customer |
| **Comfort with Ambiguity** | Operates without perfect info, makes reversible decisions | Describes navigating unclear requirements, uses pilots to validate |
| **Influence Without Authority** | Builds coalitions, shares credit, aligns incentives | Gives examples of cross-functional alignment, partner/customer negotiation |

### Values Interview Questions & STAR Answers

#### Q1: "Tell me about a time you failed. What did you learn?"
**STAR Answer:**
> **S:** Leading a Teradata→BigQuery migration, I underestimated source data quality. Assess phase catalogs said "clean."
> **T:** Needed to validate migration approach in 4-week Pilot.
> **A:** Pilot revealed 40% NULL customer_ids, duplicate transactions, RI violations. Spent 3 weeks fixing source data instead of validating migration. Delayed Phase 3 by 3 weeks.
> **R:** Built automated data profiling into Assess phase (Great Expectations suites from DBSAT). Next migration: Pilot passed in 2 weeks, zero quality surprises. **Lesson: Validate assumptions with data, not documentation. Automate early.**

#### Q2: "How do you handle a situation where you don't know the answer?"
**STAR Answer:**
> **S:** Customer CTO asked about BigQuery slot millisecond calculation for DML during architecture review.
> **T:** Needed to maintain credibility while being accurate.
> **A:** "I don't have the exact formula memorized, but I know it's bytes processed + slot time. Let me check the pricing doc section 4.2, run a test with EXPLAIN ANALYZE, and confirm with our BQ specialist. I'll follow up by EOD." Sent detailed answer with test results in 4 hours.
> **R:** CTO appreciated the rigor. Became our standard protocol: "I don't know, but here's my plan and timeline."

#### Q3: "Describe a time you influenced without authority."
**STAR Answer:**
> **S:** Partner SI wanted to use self-managed Kafka on GKE for streaming. I recommended Dataflow (managed, exactly-once, lower TCO).
> **T:** Align on architecture without contractual leverage.
> **A:** 1) Ran proof-of-concept: Dataflow vs Kafka on GKE for their workload. 2) Shared results: 40% lower cost, zero ops, exactly-once vs at-least-once. 3) Framed as "reducing their delivery risk" not "Google wins." 4) Offered to co-present to customer.
> **R:** Partner adopted Dataflow. Became their standard. They now lead with it in proposals. **Lesson: Evidence > opinion. Frame as shared win.**

#### Q4: "How do you prioritize when everything is urgent?"
**STAR Answer:**
> **S:** Migration program: cutover in 2 weeks, security audit findings, partner resource gap, customer executive demo prep.
> **T:** All P0, fixed deadline, limited team.
> **A:** Used **MoSCoW + Impact/Effort matrix** with stakeholders:
> - **Must (Do now):** Cutover readiness, security audit (compliance)
> - **Should (Schedule):** Demo prep (simplified scope)
> - **Could (Delegate):** Partner gap (escalated to SI lead with specific ask)
> - **Won't (Defer):** Nice-to-have optimizations
> Communicated transparently: "Here's what we're doing, what we're not, why."
> **R:** Cutover succeeded, audit passed, demo delivered (simplified). Stakeholders aligned because they co-owned the prioritization.

#### Q5: "What does 'focus on the user' mean in consulting?"
**Answer Framework:**
> **Not:** Maximizing billable hours or using coolest tech.
>
> **Is:** 
> 1. **Outcome-first:** "What business problem are we solving?" before "Which GCP service?"
> 2. **Sustainable delivery:** Customer owns the platform post-engagement. KT isn't a checkbox—it's the product.
> 3. **Long-term > short-term:** Recommending 3-year slot commitment even if it reduces current engagement revenue, because it's right for customer.
> 4. **Saying no:** Pushing back on scope that creates technical debt or security risk, even if customer wants it.
> 5. **Measuring customer success:** NPS, adoption, business metrics—not just "we delivered the scope."

---

## 👥 Leadership & Strategy (Practice Lead Level)

### Key Discussion Topics (Prepare 3-min Perspectives)

#### 1. Building a High-Performing Data Consulting Team
> **My Philosophy:** "Hire for trajectory, not current state. 50/50 consulting+technical balance. Googleyness veto power. Diverse by design (50% slate). Bar raising: each hire raises team average on 2+ dimensions."
>
> **Execution:** Structured 4-round loop (Phone → Technical → Consulting Sim → Values). Quarterly calibration. 92% retention, 45-day fill, 50% diverse hires.

#### 2. Scaling Delivery Through Partners
> **Model:** "Google = Architecture + Quality Gates + KT (30%). Partner = Delivery (60%). Customer = Domain + UAT (10%)."
> **Governance:** Monthly scorecards (Delivery 40%, Technical 20%, Commercial 20%, KT 10%, Relationship 10%). 4-level escalation. Joint account planning quarterly.
> **Enablement:** 3-tier certification, hands-on labs, co-delivery shadowing. 2 partners achieved Specialization last year.
> **Results:** 4 Google architects oversee 12 concurrent migrations. Pipeline $2M→$12M in 18 months.

#### 3. Practice P&L Ownership
> **Metrics I Track:** Revenue, margin (>35%), utilization (75% billable), pipeline coverage (3x), NPS (>4.5), KT completion (100%), asset creation (reusable IP per engagement).
> **Investment Decisions:** Build reusable IP (Runbook, Terraform, Templates) vs. custom delivery. IP pays back in 3 engagements. Partners deliver IP, we govern quality.

#### 4. Hiring & Developing Consultants
> **Framework in hiring_framework.md** - 4 rounds, structured rubrics, values veto, calibration.
> **Development:** 30/60/90 day plans. Shadow→Pair→Lead. Technical mentorship + consulting apprenticeship. Quarterly skill assessments. Promotion criteria: technical depth + consulting impact + values embodiment.

---

## 🇸🇬 Singapore & APAC Context (Critical for This Role)

### Regulatory Landscape (Must Know Cold)

| Regulation | Scope | Key Requirements | GCP Mapping |
|------------|-------|------------------|-------------|
| **MAS-TRM** (Technology Risk Management) | All FIs in Singapore | 6.3: Data protection, 7.2: System resilience, 8.1: Audit trails, 9.1: Vendor mgmt | VPC-SC, CMEK+HSM, Dataplex lineage, Audit Logs→Chronicle, Partner scorecards |
| **PDPA** (Personal Data Protection Act) | All orgs processing personal data | Consent, purpose limitation, access/correction, retention, transfer limitation | Policy tags (PII), Column masking, DLP auto-classify, Data residency (asia-southeast1), Consent management |
| **Cybersecurity Act** | Critical Info Infrastructure (CII) | CII designation, incident reporting, audits, codes of practice | VPC-SC, Private Service Connect, Security Command Center, Mandiant integration |
| **Banking Act / SFA** | Banks, Capital Markets | Data localization (some), audit access, outsourcing guidelines | Data residency controls, Customer-managed keys, Audit log export, Partner due diligence |

### Data Residency Requirements
```
SINGAPORE DATA RESIDENCY STRATEGY

MANDATORY RESIDENCY (MAS-regulated):
├── Core banking data → asia-southeast1 (Singapore) ONLY
├── Customer PII → asia-southeast1 ONLY
├── Transaction logs → asia-southeast1 ONLY
└── Audit trails → asia-southeast1 ONLY

FLEXIBLE RESIDENCY:
├── Analytics/ML features → asia-southeast1 + asia-northeast1 (Tokyo) for compute
├── Training datasets → Multi-region ASIA (Singapore + Tokyo + Hong Kong)
└── Non-PII reference data → Any region

IMPLEMENTATION:
├── Organization Policy: constraints/gcp.resourceLocations = "asia-southeast1"
├── BigQuery: Dataset location = asia-southeast1
├── GCS: Bucket location = asia-southeast1 (dual-region for HA)
├── Dataflow: Regional endpoint = asia-southeast1
├── Vertex AI: Regional endpoint = asia-southeast1
└── Dataplex: Lake location = asia-southeast1
```

### Partner Ecosystem (Singapore/APAC)
| Partner Tier | Key Singapore Partners | Specialization |
|--------------|------------------------|----------------|
| **Strategic** | Accenture, Deloitte, TCS | Data & Analytics, FinServ, Migration |
| **Select** | NCS, ST Engineering, GovTech | Public sector, Telco, Smart Nation |
| **Boutique** | Various | Industry-specific (Insurance, Wealth Mgmt) |

**Key Insight:** Singapore government (GovTech, Smart Nation) is a major driver. Partners with public sector creds win. MAS-TRM compliance is table stakes for FinServ.

### Cultural Nuances
- **Relationship-first:** Build trust before technical discussions. Coffee chats matter.
- **Hierarchy-aware:** Decisions escalate up. Include senior stakeholders early.
- **Face-saving:** Never publicly contradict customer/partner. "Yes, and..." not "No, but..."
- **Compliance-native:** Security/governance isn't a feature—it's the baseline.
- **Multi-lingual teams:** English + Mandarin + Malay + Tamil common. Document in English.

---

## ⚙️ Technical Fundamentals (Rapid-Fire Prep)

### BigQuery (Must Answer in <30 sec each)

| Question | 30-Second Answer |
|----------|------------------|
| **Architecture?** | Serverless, storage/compute separation. Colossus (storage), Dremel (query), Borg (compute). Slots = compute capacity. |
| **Partition vs Cluster?** | Partition = prune data (date, ingestion time, integer range). Cluster = sort within partition (high-cardinality keys). Use both. |
| **Slot contention?** | Monitor `slots_assigned` vs `slots_available`. Solutions: Reservations, fair scheduling, query optimization, BI Engine for dashboards. |
| **Streaming inserts?** | Storage Write API (exactly-once, default). Legacy `tabledata.insertAll` (at-least-once). Use partitioned tables, clustered. |
| **BQML vs Vertex AI?** | BQML: In-database, SQL interface, good for linear/XGBoost/ARIMA. Vertex: Custom training, distributed, Feature Store, online serving, MLOps. Promote BQML→Vertex seamlessly. |
| **Cost control?** | Reservations (3yr=35% off), Partition pruning, Clustering, Materialized Views, BI Engine, Query result cache (24hr free), `MAX_BYTES_BILLED`. |
| **Multi-cloud?** | BigQuery Omni: Query AWS S3 / Azure ADLS from BQ. Same SQL, same governance. No data movement. |
| **Security?** | VPC-SC, CMEK/CMEK+HSM, IAM Conditions, Column-level security (Policy Tags), Row-level security, Data Catalog tags, Audit Logs. |

### Dataflow (Must Answer in <30 sec each)

| Question | 30-Second Answer |
|----------|------------------|
| **Batch vs Streaming?** | Same SDK (Apache Beam). Batch: bounded PCollection. Streaming: unbounded + windows + watermarks. Runner chooses execution. |
| **Exactly-once?** | Source: idempotent keys + dedup. Processing: deterministic DoFns. Sink: BigQuery Storage Write API (stream-level exactly-once) or transactional sinks. |
| **Windowing types?** | Fixed (tumbling), Sliding, Session (gap-based), Custom. Trigger: watermark + allowed lateness + early/late firings. |
| **Shuffle optimization?** | Salting for skew, CombinePerKey pre-aggregation, Shuffle Service (managed), right-sizing workers, `--experiments=shuffle_mode=service`. |
| **Late data handling?** | Allowed lateness (default 0), side outputs for late events, `withAllowedLateness()`, watermark alignment for CDC+batch reconciliation. |
| **Monitoring?** | Job metrics: lag, throughput, errors, memory/CPU. Business metrics: custom counters. Alerting: Cloud Monitoring → PagerDuty/Slack. |
| **Templates?** | Classic (parameterized at launch) vs Flex (parameterized at runtime, any SDK version). Use Flex for production. |

### Dataproc (Must Answer in <30 sec each)

| Question | 30-Second Answer |
|----------|------------------|
| **When Dataproc vs Dataflow?** | Dataproc: Spark/Hive compatibility, existing code, complex DAGs, interactive. Dataflow: Beam native, serverless, streaming, exactly-once, no cluster mgmt. |
| **Cost optimization?** | Spot VMs (60-90% off) for workers, preemptible for batch, autoscaling policies, image versioning, shutdown idle clusters. |
| **Metastore?** | Dataproc Metastore (managed Hive metastore), external MySQL/Postgres, or BigQuery as metastore (Hive-BQ connector). |
| **Migration from Hadoop?** | DistCp for data, Hive→BQ schema translation, Spark code → Dataproc (minimal changes), Ranger policies → Dataplex/IAM. |

### Composer / Airflow (Must Answer in <30 sec each)

| Question | 30-Second Answer |
|----------|------------------|
| **Composer 1 vs 2?** | Composer 2: Airflow 2.x, Cloud Build CI/CD, Private IP, smaller envs (micro), faster startup, lower cost. |
| **Best practices?** | TaskGroups for UI, XCom for small data only, sensors with poke_interval, SLAs + callbacks, secrets in Secret Manager, version-controlled DAGs. |
| **Dataflow operator?** | `DataflowStartFlexTemplateOperator` for Flex templates. Async execution, sensor for completion. Pass runtime params via `dataflow_config`. |

### Vertex AI (Must Answer in <30 sec each)

| Question | 30-Second Answer |
|----------|------------------|
| **Feature Store?** | Online (low-latency serving) + Offline (training). Point-in-time correctness. Entity + Feature View. Sync from BQ/Dataflow. |
| **MLOps?** | Vertex AI Pipelines (Kubeflow), Model Registry (versioning), Endpoints (A/B, canary), Model Monitoring (drift, bias, feature attribution). |
| **BQML → Vertex?** | `EXPORT MODEL` to GCS → `Model.upload()` → Register → Deploy. No data movement. Seamless promotion. |

---

## 🛡️ Objection Handling (Roleplay Scenarios)

### Scenario 1: "GCP is 3x more expensive than on-prem"
> **Customer CTO:** "Your TCO shows savings, but my team says GCP queries cost 3x our Teradata CPU hours."
>
> **Response Framework:**
> 1. **Validate:** "That's a real concern. Let's look at the specific workloads."
> 2. **Decompose:** "Teradata: fixed cost (hardware, licenses, 5 FTE ops). BigQuery: variable (bytes scanned). Different models."
> 3. **Optimize:** "Your top 20 queries scan 50TB but return 1GB. Partition + Cluster + MV = 99% reduction. Let's prove it in Pilot."
> 4. **Reference:** "Singapore Bank X: same concern. Pilot showed 95% query cost reduction after optimization."
> 5. **Commit:** "4-week Pilot. Success criteria: cost/query ≤ on-prem. Go/No-Go gate. Your risk: 4 weeks."

### Scenario 2: "We can't put customer data in the cloud (MAS-TRM)"
> **Customer CISO:** "MAS requires data on-prem. Cloud is non-compliant."
>
> **Response Framework:**
> 1. **Validate:** "MAS-TRM 6.3/7.2/8.1 are exactly why we architect VPC-SC + CMEK+HSM + Dataplex."
> 2. **Evidence:** "3 Singapore banks on this architecture. MAS examiners reviewed. Zero findings."
> 3. **Control Mapping:** "Here's our MAS-TRM control matrix: VPC-SC=6.3, CMEK+HSM=6.3, Audit Logs=8.1, DR=7.2."
> 4. **Data Residency:** "Organization Policy enforces asia-southeast1 only. No data leaves Singapore."
> 5. **Offer:** "Bring your compliance team. We'll walk through the architecture and evidence pack."

### Scenario 3: "Vendor lock-in is unacceptable"
> **Customer Architect:** "BigQuery proprietary SQL, Dataflow proprietary runner. We can't leave."
>
> **Response Framework:**
> 1. **Validate:** "Lock-in is real. Let's distinguish: *data* lock-in vs *compute* lock-in."
> 2. **Data Portability:** "Your data in GCS (Parquet/Avro/ORC) + BQ (open formats). Export anytime. dbt models = portable SQL."
> 3. **Compute Portability:** "Dataflow = Apache Beam (runs on Flink/Spark). Vertex AI = Kubeflow pipelines exportable. Terraform = multi-cloud."
> 4. **Omni:** "BigQuery Omni queries AWS/Azure data in place. Multi-cloud by design."
> 5. **Contractual:** "No egress fees for migration out. 90-day notice. We help you leave if needed (has happened 0 times)."

### Scenario 4: "Timeline is too aggressive / We need more time"
> **Customer PM:** "22 weeks is impossible. Our team is at capacity. Need 6 months minimum."
>
> **Response Framework:**
> 1. **Validate:** "Capacity constraints are real. Let's look at what drives timeline."
> 2. **Decompose:** "22 weeks = 2w Assess + 4w Pilot + 16w Migrate. Migrate is parallelizable (50 concurrent Spark jobs)."
> 3. **Tradeoff:** "Options: (a) Extend to 30 weeks, same scope. (b) Keep 22 weeks, reduce scope (defer ML, keep BI). (c) Add 4 Partner engineers (cost: $X), keep 22 weeks."
> 4. **Risk:** "Extending increases dual-write complexity, CDC lag risk, stakeholder fatigue."
> 5. **Decide Together:** "You choose. I'll give you the data to decide."

### Scenario 5: "Your partner SI isn't technical enough"
> **Customer Tech Lead:** "The SI architects you proposed don't know BigQuery internals. We need Google engineers."
>
> **Response Framework:**
> 1. **Validate:** "Technical depth is non-negotiable. Let's assess."
> 2. **Evidence:** "Here are the 3 named architects: certifications, 5+ BQ migrations, code samples. Interview them."
> 3. **Governance:** "Google Lead Architect owns quality gates (weekly architecture reviews, code reviews, performance benchmarks). SI delivers, we verify."
> 4. **Escalation:** "If gap found: substitution clause in SoW (5-day replacement). Google backup engineers on retainer."
> 5. **Commitment:** "I personally own the architecture. My reputation is on every delivery."

---

## 🎯 Round 5 Preparation Checklist

- [ ] **Googleyness:** 5 STAR stories memorized (failure, learning, influence, prioritization, user focus)
- [ ] **Leadership:** 3-min perspectives on team building, partner scaling, P&L, hiring
- [ ] **Singapore Context:** MAS-TRM/PDPA control mappings cold, data residency strategy, partner landscape
- [ ] **Technical Fundamentals:** 20+ rapid-fire answers <30 sec each (BQ, Dataflow, Dataproc, Composer, Vertex AI)
- [ ] **Objection Handling:** 5 roleplay scenarios practiced with colleague
- [ ] **Questions for Them:** 3 strategic questions prepared

---

## 💡 Final Interview Wisdom

> **"They're not hiring a technical expert. They're hiring a Lead Consultant who happens to have deep technical expertise.**
>
> **Show:** Business judgment > technical cleverness. Customer outcomes > architectural purity. Team success > individual heroics. Reusable IP > custom solutions. Humility > certainty.**
>
> **Every answer should ladder to:** 'How does this help the customer succeed? How does this scale the practice? How does this embody Google's values?'"

---

*Round 5 is where they decide: "Can this person represent Google in front of our biggest customers?" Be that person.*