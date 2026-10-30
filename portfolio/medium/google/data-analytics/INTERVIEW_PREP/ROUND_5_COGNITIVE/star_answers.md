# Round 5: STAR Answer Bank
## 15 Complete STAR Stories for Cognitive/Behavioral Round

---

## 📋 STAR Framework Reminder

| Component | What to Include | Time |
|-----------|-----------------|------|
| **Situation** | Context, scale, stakes, your role | 15 sec |
| **Task** | Your specific responsibility, challenge | 10 sec |
| **Action** | What YOU did (not "we"), steps, decisions | 60 sec |
| **Result** | Quantified outcomes, learnings, applied since | 25 sec |

**Total: ~2 minutes per story**

---

## 1️⃣ FAILURE & LEARNING

### STAR 1: Underestimated Data Quality (Technical Failure)
> **S:** Leading a 140TB Teradata→BigQuery migration for a Singapore bank. Assess phase catalogs showed "clean" data per customer documentation.
> **T:** As Lead Architect, I owned the 4-week Pilot validation before 16-week migration phase.
> **A:** Pilot revealed 40% NULL customer_ids in fact tables, 15% duplicate transactions, 8% referential integrity violations. Spent 3 weeks in Pilot fixing source data issues instead of validating migration logic. Delayed Phase 3 start by 3 weeks, partner team idle.
> **R:** Built automated data profiling into Assess phase—Great Expectations suites auto-generated from DBSAT/Atlas output. Runs in 4 hours, produces quality baseline report. Next migration: Pilot passed in 2 weeks, zero quality surprises. **Lesson: Trust but verify with automation. Data quality is a migration risk, not a given.**

### STAR 2: Partner Delivery Gap (Leadership Failure)
> **S:** Managing a $2M migration with strategic SI partner. Their lead architect left mid-engagement; replacement lacked BigQuery optimization experience.
> **T:** As Google Delivery Lead, I owned partner performance and customer outcome.
> **A:** Didn't escalate early enough—hoped they'd ramp. 3 weeks later: pipeline failures, cost overruns, customer frustration. Finally triggered L3 escalation, got partner VP engaged. Replaced architect with certified expert. Implemented weekly architecture reviews (Google-led) going forward.
> **R:** Recovered timeline, but lost 3 weeks and customer trust. **Now: Named resources in SoW with substitution clause. Weekly architecture reviews from Day 1. Auto-escalation if scorecard <3.0 for 2 months. Partner certification gate before SoW sign.**

### STAR 3: Scope Creep Without Change Control (Process Failure)
> **S:** Customer added 8 new requirements during migration execution. Timeline fixed, budget fixed. Partner said yes to everything.
> **T:** Engagement Lead - needed to protect delivery and margin.
> **A:** Initially absorbed scope to "keep customer happy." Result: team burnout, quality issues, margin erosion. Mid-engagement reset: implemented rigorous change control—MoSCoW with customer, impact analysis (timeline/cost/quality), written approval for any scope change. Partner held accountable to original SoW.
> **R:** Delivered core scope on time. 3 of 8 additions deferred to Phase 2 (became $1.5M expansion). **Lesson: Saying "yes" to everything fails the customer. Structured change control protects everyone.**

---

## 2️⃣ INFLUENCE WITHOUT AUTHORITY

### STAR 4: Partner Architecture Alignment (Dataflow vs Kafka)
> **S:** Strategic SI partner proposed self-managed Kafka on GKE for streaming ingestion. I recommended Dataflow (managed, exactly-once, 40% lower TCO).
> **T:** Align on architecture without contractual authority over partner.
> **A:** 1) Ran 2-week proof-of-concept: identical workload on Dataflow vs Kafka/GKE. 2) Shared results transparently: Dataflow 40% lower cost, zero ops burden, exactly-once vs at-least-once, native BQ integration. 3) Framed as "reducing YOUR delivery risk and ops burden" not "Google wins." 4) Offered to co-present to customer as joint recommendation.
> **R:** Partner adopted Dataflow as their standard. They now lead with it in proposals. Co-delivered 3 subsequent migrations. **Lesson: Evidence > opinion. Frame as shared win. Make the partner the hero.**

### STAR 5: Customer CTO Cost Objection (Executive Influence)
> **S:** Customer CTO pushed back: "GCP 3x more expensive than Teradata. My team calculated query costs."
> **T:** As Lead Architect, needed to change the conversation from "cost per query" to "TCO."
> **A:** 1) Acknowledged: "Valid concern. Let's look at your calculation together." 2) Decomposed: Showed their calc missed 5 FTE ops ($750k), facilities ($300k), licenses ($700k), downtime risk, refresh cycles. 3) Modeled together: 3-year TCO on-prem $10M vs GCP $5.5M (45% savings). 4) Referenced: "Singapore Bank X had same concern. Pilot proved 95% query cost reduction after optimization." 5) Proposed: 4-week Pilot with cost/query success criteria. Go/No-Go gate.
> **R:** CTO approved Pilot. Pilot exceeded criteria. $3.2M deal closed. **Lesson: Don't defend—deconstruct. Co-create the model. Pilot proves it.**

### STAR 6: Cross-Functional Prioritization (Internal Influence)
> **S:** Migration program: cutover in 2 weeks, security audit findings, partner resource gap, customer executive demo prep. All P0, fixed deadline.
> **T:** Program Lead - needed stakeholder alignment on what NOT to do.
> **A:** Ran 1-hour prioritization workshop with all leads. Used MoSCoW + Impact/Effort matrix on whiteboard. Co-created the plan:
> - Must (Do now): Cutover readiness, security audit (compliance)
> - Should (Schedule): Demo prep (simplified to 3 key dashboards)
> - Could (Delegate): Partner gap (escalated to SI lead with specific ask)
> - Won't (Defer): Nice-to-have optimizations
> Communicated transparently via single Slack channel: "Here's what we're doing, what we're not, why."
> **R:** Cutover succeeded, audit passed, demo delivered (simplified). Stakeholders aligned because they co-owned the decision. **Lesson: Prioritization is a team sport. Make tradeoffs visible and shared.**

---

## 3️⃣ TECHNICAL LEADERSHIP & JUDGMENT

### STAR 7: Major Technical Risk Mitigation (Dataflow Shuffle Skew)
> **S:** Streaming pipeline processing 100K events/sec, 5TB/hour. 40% NULL customer_id from legacy data causing massive shuffle skew. Pipeline OOM after 14 hours.
> **T:** Lead Data Engineer - needed production fix without downtime.
> **A:** 1) Root cause analysis: NULLs → single partition → 5TB shuffle → worker OOM. 2) Designed salting partitioner: distribute NULLs across 100 salt buckets, normal hash for non-NULL. 3) Enabled Dataflow Shuffle Service (managed shuffle). 4) Added pre-aggregation CombinePerKey (reduce 5TB→200GB pre-shuffle). 5) Deployed via Flex Template with canary (10% traffic → 100%).
> **R:** 14hr+OOM → 4hr success, stable for 6 months. Pattern documented in Dataflow Template Library, used in 12 customer engagements. **Lesson: Skew is a data problem, not a config problem. Fix at source with salting + pre-aggregation.**

### STAR 8: 500 Stored Procedure Migration Strategy (Technical Strategy)
> **S:** Customer had 500 Teradata stored procedures with procedural logic, temp tables, dynamic SQL. Manual rewrite = 2+ years.
> **T:** Migration Architect - needed scalable approach for 22-week timeline.
> **A:** 1) Built automated classifier (sqlglot + custom rules) analyzing: LOC, temp tables, dynamic SQL, cursors, control flow, dependencies. 2) Classified 5 categories: Type 1 Pure SQL (36%)→auto-translate to dbt; Type 2 Procedural (24%)→BQ Scripts; Type 3 Dynamic SQL (16%)→dbt macros; Type 4 DQ (14%)→Great Expectations; Type 5 Obsolete (10%)→retire. 3) Built translation pipeline for Type 1. 4) Validated all 500 via automated testing against query logs.
> **R:** All 500 SPs migrated in 8 weeks. Zero logic gaps in UAT. 80% dev time reduction vs manual. Classifier open-sourced internally. **Lesson: Classify before you migrate. Automate the 80% that's patternable. Human expertise on the 20% that's not.**

### STAR 9: Security Architecture for MAS-TRM (Compliance Leadership)
> **S:** Singapore bank required MAS-TRM compliance for cloud migration. No existing GCP reference architecture for MAS-TRM.
> **T:** Lead Architect - design security architecture that passes MAS examination.
> **A:** 1) Mapped MAS-TRM 6.3/7.2/8.1/9.1 to GCP controls. 2) Designed: VPC-SC perimeter (data exfiltration prevention), CMEK+Cloud HSM FIPS 140-2 L3 (key sovereignty), Dataplex policy tags + DLP auto-classify (data protection), Column masking/RLS (access control), Audit Logs→Chronicle (audit trail), Partner scorecards (vendor mgmt). 3) Built evidence pack: automated compliance reports, penetration test results, DR test records. 4) Pre-engaged MAS examiners via customer compliance team.
> **R:** Migration passed MAS examination with zero findings. Architecture now "FinServ Policy Pack" used by 3 banking customers. **Lesson: Compliance isn't a checklist—it's an architecture principle. Build evidence generation in, not on.**

---

## 4️⃣ CUSTOMER OBSESSION & BUSINESS ACUMEN

### STAR 10: Pivot from Migration to AI Enablement (Business Vision)
> **S:** Post-migration, customer asked: "Now what? We're on BigQuery. How do we do AI?"
> **T:** Lead Architect - expand engagement from migration to AI platform.
> **A:** 1) Ran "Art of Possible" workshop: mapped their business problems (churn, fraud, personalization) to Vertex AI capabilities. 2) Built 3 MVPs in 6 weeks: Churn (BQML→Vertex, AUC 0.89), Fraud (Dataflow streaming→Vertex Online Prediction <50ms), Personalization (Feature Store + Vertex). 3) Quantified business value: $40M ARR retention, 23% fewer outages, 34% CTR lift. 4) Co-built Phase 2 proposal ($2.5M) with customer PM and partner.
> **R:** Phase 2 signed. 12 models in production. Customer NPS 4.8/5. **Lesson: Migration is the beginning, not the end. Lead with business problems, not platform features.**

### STAR 11: Saying No to Protect Customer (Integrity)
> **S:** Customer wanted to lift-and-shift 200+ Informatica workflows to Dataflow 1:1. Would cost $2M, take 12 months, recreate technical debt.
> **T:** Lead Architect - customer asked for something that would hurt them.
> **A:** 1) Analyzed: 60% workflows were data quality fixes for bad source data. 2) Proposed alternative: Fix source data (3 months), rewrite as dbt models (4 months), retire 40% unused. 3) Showed TCO: Their ask=$2M/12mo. My approach=$800k/7mo + better quality. 4) Customer initially pushed back ("we paid for Informatica"). 5) Escalated to CTO with data. CTO agreed.
> **R:** Delivered in 7 months, $800k. Data quality improved 10x. Customer later thanked us. **Lesson: Customer isn't always right about *how*. They're right about *what*. Our job is the better how.**

### STAR 12: Knowledge Transfer as Product (Sustainable Delivery)
> **S:** End of 22-week migration. Customer team of 4 engineers needed to own 140TB platform.
> **T:** Engagement Lead - KT can't be a checkbox. It's the product.
> **A:** Designed 30/60/90 day KT plan:
> - **30 days (Shadow):** Customer engineers pair on all ops: monitoring, tuning, incident response, deployments.
> - **60 days (Pair):** Customer leads, Google shadows. Runbooks validated. First independent incident.
> - **90 days (Lead):** Customer owns BAU. Google advisory only. Graduation: customer presents "State of Platform" to their CTO.
> Built runbooks, video library, sandbox environment for practice.
> **R:** 100% KT completion. Zero P1 incidents in first 90 days post-engagement. Customer team promoted internally. **Lesson: KT isn't documentation—it's supervised practice. Measure by customer confidence, not hours delivered.**

---

## 5️⃣ AMBIGUITY & ADAPTABILITY

### STAR 13: Ambiguous Requirements → Pilot Validation (Navigating Uncertainty)
> **S:** Customer wanted "real-time analytics" but couldn't define: latency target, data sources, use cases, volume. Just "like Uber but for banking."
> **T:** Lead Architect - define architecture without clear requirements.
> **A:** 1) Refused to over-engineer. Proposed: "Let's define via Pilot." 2) Co-created Pilot scope with 3 hypotheses: (a) Fraud detection <100ms, (b) Balance updates <5sec, (c) Regulatory dashboards <1min. 3) Built minimal viable pipeline: Kafka→Dataflow→BQ→Looker for each. 4) Measured actual latency, cost, complexity. 5) Customer realized: fraud needed 100ms (Dataflow streaming), balances needed 5sec (CDC + Dataflow), regulatory was fine at 1hr (batch).
> **R:** Pilot defined requirements with data. Architecture right-sized. Saved 6 months of over-engineering. **Lesson: When requirements are ambiguous, build the smallest thing that generates data. Pilot = requirements discovery.**

### STAR 14: Mid-Engagement Pivot (Adaptability)
> **S:** 8 weeks into migration, customer acquired a competitor. New requirement: integrate their 20TB Oracle warehouse in 4 weeks (original plan: 16 weeks later).
> **T:** Program Lead - absorb unplanned scope without derailing main migration.
> **A:** 1) Assessed: Oracle schema compatible, data quality good, team had Oracle expertise. 2) Proposed: Fast-track as separate workstream. Google architect + 2 Partner engineers. Parallel to main migration. 3) Used existing Terraform module (10-min env), Dataflow CDC template, FinServ Policy Pack. 4) Negotiated: Customer funds incremental cost. Partner provides 2 engineers from bench. 5) Delivered in 3.5 weeks.
> **R:** Acquisition integrated before main cutover. Main migration on track. Customer: "You saved the deal." **Lesson: Reusable IP (Terraform, Templates, Packs) enables speed. Modular architecture absorbs change.**

### STAR 15: Leading Through Crisis (Composure)
> **S:** Day before production cutover, customer DBA found 2TB data discrepancy in reconciliation. Cutover go/no-go in 24 hours.
> **T:** Engagement Lead - decide: delay (business impact) or proceed (data risk).
> **A:** 1) War room: Google Arch + Partner Lead + Customer DBA + Business Sponsor. 2) Root cause in 2 hours: Dual-write MERGE logic error for specific partition range. 3) Fix: Corrected MERGE, backfilled 2TB via Dataflow (4 hours). 4) Re-ran full reconciliation: zero discrepancies. 5) Communicated: "Here's what happened, here's the fix, here's the validation. We're GO."
> **R:** Cutover proceeded on schedule. Zero data loss. Customer Sponsor: "Transparency and speed gave us confidence." **Lesson: Crisis reveals character. Transparent, data-driven, fast. Don't hide—lead.**

---

## 🎯 STAR Mapping to Google Attributes

| STAR Story | Humility/Learning | User Focus | Ambiguity | Influence w/o Authority |
|------------|-------------------|------------|-----------|------------------------|
| 1: Data Quality | ✅ | ✅ | | |
| 2: Partner Gap | ✅ | ✅ | | ✅ |
| 3: Scope Creep | ✅ | ✅ | | ✅ |
| 4: Dataflow vs Kafka | | ✅ | | ✅ |
| 5: CTO Cost Objection | | ✅ | | ✅ |
| 6: Prioritization | | ✅ | ✅ | ✅ |
| 7: Shuffle Skew | ✅ | ✅ | | |
| 8: SP Migration | ✅ | ✅ | | |
| 9: MAS-TRM Security | | ✅ | ✅ | |
| 10: AI Pivot | | ✅ | ✅ | ✅ |
| 11: Say No | ✅ | ✅ | | ✅ |
| 12: KT as Product | | ✅ | | |
| 13: Ambiguous Requirements | | ✅ | ✅ | |
| 14: Mid-Engagement Pivot | | ✅ | ✅ | ✅ |
| 15: Cutover Crisis | ✅ | ✅ | ✅ | |

---

## 🎪 Delivery Tips

1. **Practice aloud** - 2 minutes exactly. Record yourself.
2. **Use "I" not "we"** - They're hiring YOU.
3. **Quantify everything** - "$2.5M savings," "95% faster," "3 weeks → 2 weeks."
4. **End with "Lesson applied"** - Shows learning agility.
5. **Have 2-3 backup STARs** per category in case they ask follow-ups.

---

## 🔄 STAR Rotation Strategy

| Interviewer Type | Lead With | Have Ready |
|------------------|-----------|------------|
| **Technical Lead** | 7, 8, 9 | 1, 13 |
| **Practice Lead** | 2, 3, 12 | 4, 6, 14 |
| **Customer-Facing** | 5, 10, 11 | 4, 12, 15 |
| **Values/Googleyness** | 1, 3, 11 | 2, 6, 12 |

---

*STAR stories are your evidence. Make them vivid, specific, and yours. The details convince.*