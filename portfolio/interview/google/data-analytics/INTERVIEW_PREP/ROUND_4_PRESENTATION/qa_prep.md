# Round 4: Presentation Round - Q&A Preparation
## 15-Minute Q&A | Anticipated Questions + Structured Answers

---

## 🎯 Q&A Strategy

### The "Google Way" of Answering
1. **Listen fully** - Don't interrupt, clarify if needed
2. **Structure** - Framework first, then details (max 2 min)
3. **Evidence** - "In my last migration..." / "Our data shows..."
4. **Tradeoffs** - Show you've considered alternatives
5. **Humility** - "I don't know, but here's how I'd find out"

### Time Management
- **Target: 90-120 seconds per answer**
- **If running long:** "Happy to go deeper on [specific aspect] if useful"
- **If stumped:** "Great question. I haven't faced that exact scenario, but here's my framework..."

---

## 🔟 Top 10 Guaranteed Questions

### Q1: "Why BigQuery over Snowflake/Redshift for this customer?"

**2-Minute Answer Framework:**
> **Technical:** BigQuery's serverless architecture meant zero cluster management for their 5-person ops team. Storage/compute separation with slot reservations gave them predictable costs. BQML native integration eliminated data movement for ML—critical for their AI mandate. BigQuery Omni lets them query data in AWS/Azure without egress.
>
> **Commercial:** Pay-per-query model aligned with their variable workloads. 3-year slot commitment = 35% discount. No upfront hardware, no license renewals.
>
> **Customer Quote:** "BigQuery was the only platform where data + AI were truly unified, not bolted together."

**If Pushed:** "Snowflake's great for multi-cloud, but their AI story requires Snowpark + external compute. Redshift's ML requires Redshift ML + SageMaker. BigQuery: one platform, one bill, one security model."

---

### Q2: "How did you handle 100TB+ initial data load?"

**2-Minute Answer Framework:**
> **Strategy:** Three-track parallel approach based on data velocity:
>
> 1. **Historical/Static (80TB):** Transfer Appliance for physical shipment → GCS → Dataproc Spark parallel load (partition by date, 50 concurrent jobs). Validated with row counts + checksums.
>
> 2. **Incremental/Batch (50TB):** Dataproc DistCp from Hadoop → GCS → Dataflow → BigQuery. Partitioned by event_date, clustered by customer_id.
>
> 3. **CDC/Real-time:** Datastream → Pub/Sub → Dataflow Streaming → BigQuery. Started in Pilot, ran continuously through migration.
>
> **Validation:** Automated reconciliation framework—row counts ±0.1%, checksums exact, sample diff zero. Dual-write for 14 days pre-cutover.

**Key Insight:** "Don't move all data the same way. Match the tool to the data velocity and SLAs."

---

### Q3: "What's your rollback plan if cutover fails?"

**2-Minute Answer Framework:**
> **Tested 3x in Pilot:** 15-minute RTO validated.
>
> **Rollback Procedure:**
> 1. DNS/Connection string flip-back to Teradata (3 min)
> 2. Teradata read-only → read-write (2 min, DBA)
> 3. CDC replay from last checkpoint (Datastream retains 7 days)
> 4. Application smoke tests (5 min)
> 5. **Total: <15 minutes, zero data loss**
>
> **During Hypercare (30 days):** CDC sync maintained in reverse. If any P1, instant rollback capability. Business validated this in Pilot—gave them confidence to proceed.

**Differentiator:** "We don't just document rollback—we *test* it. Three dry runs before production cutover."

---

### Q4: "How do you scale your team for the next 10 migrations?"

**2-Minute Answer Framework:**
> **Three-Lever Model:**
>
> 1. **Reusable IP (60% leverage):** Migration Runbook + Terraform Module + Dataflow Templates + Policy Packs. One consultant runs what took 4. Partners deliver 70% using our IP.
>
> 2. **Partner Enablement (30% leverage):** 3-tier certification (Associate→Professional→Expert). Co-delivery model: Google architects, Partner delivers. 2 partners achieved Specialization last year.
>
> 3. **Customer Co-Delivery (10% leverage):** Customer engineers shadow → pair → lead. 30/60/90 day KT plan. They own BAU; we do transformation.
>
> **Result:** "Same 4 Google architects now oversee 12 concurrent migrations via partners. Pipeline grew from $2M to $12M in 18 months."

---

### Q5: "Customer wants multi-cloud - how does your architecture handle it?"

**2-Minute Answer Framework:**
> **Architecture is Portable by Design:**
>
> 1. **BigQuery Omni:** Query data in AWS S3 / Azure ADLS from BigQuery console. No data movement. Same SQL, same governance.
>
> 2. **Terraform Module:** Same IaC deploys to GCP/AWS/Azure (provider abstraction). VPC, IAM, networking patterns portable.
>
> 3. **dbt + Dataflow Templates:** Logic is platform-agnostic. dbt models run on BigQuery/Snowflake/Redshift. Dataflow templates → Beam portable runner.
>
> 4. **Vertex AI → Kubeflow:** ML pipelines exportable. Feature Store data in open format (Parquet/Avro).
>
> **Customer Reality:** "This bank runs core on GCP, but keeps DR in AWS. Omni lets them query DR data without replication. Architecture supports their strategy, not ours."

---

### Q6: "How do you measure 'delivery excellence'?"

**2-Minute Answer Framework:**
> **Five KPIs, Tracked Weekly:**
>
> | KPI | Target | Measurement |
> |-----|--------|-------------|
> | **Customer NPS** | >4.5/5 | Quarterly survey + post-milestone pulse |
> | **On-Time Delivery** | >90% | Milestone dates vs plan (not just final) |
> | **Quality Gate Pass** | >95% | Automated validation + architecture review |
> | **Knowledge Transfer** | 100% | 30/60/90 day gates, customer sign-off |
> | **Engagement Margin** | >35% | Revenue - (Google + Partner + T&E) / Revenue |
>
> **Governance:** Weekly PMO review, monthly steering committee, quarterly business review with executive sponsor. "Excellence isn't delivery—it's *sustainable* delivery the customer can own."

---

### Q7: "Biggest technical mistake in your last migration?"

**2-Minute Answer (Honest + Growth):**
> **Mistake:** Underestimated source data quality. Assess phase showed "clean" data per catalogs. Pilot revealed: 40% NULL customer_ids, 15% duplicate transactions, 8% referential integrity violations. Spent 3 weeks in Pilot fixing instead of validating.
>
> **Fix:** Built automated data profiling into Assess phase. Now: Great Expectations suites auto-generated from DBSAT/Atlas output. Runs in 4 hours, produces quality baseline report. Pilot now validates *migration logic*, not *source data*.
>
> **Result:** Next migration—Pilot passed in 2 weeks. Quality surprises = 0.

**Why This Works:** Shows ownership, specific learning, systemic fix, measurable improvement.

---

### Q8: "How do you handle schema evolution post-migration?"

**2-Minute Answer Framework:**
> **Three-Layer Defense:**
>
> 1. **Schema Registry (Source of Truth):** Avro/Protobuf schemas in Confluent Schema Registry / Apicurio. BACKWARD compatibility enforced—producers can't break consumers.
>
> 2. **Pipeline Resilience:** Dataflow templates handle evolution:
>    - New fields: Auto-added (nullable, default)
>    - Deleted fields: Ignored (with alert)
>    - Type changes: Validated against compatibility rules
>
> 3. **Governance Enforcement:** Dataplex policy tags on columns. Schema change → DLP re-scan → policy tag review → approval workflow. Column lineage tracks every change.
>
> **Cutover Specific:** Dual-write period catches schema drift. Reconciliation job compares schemas daily. Alert on any mismatch.

---

### Q9: "Team composition for a $2M migration delivery?"

**2-Minute Answer Framework:**
> **Right-Sized, Not One-Size:**
>
> | Role | Count | Source | Responsibility |
> |------|-------|--------|----------------|
> | **Engagement Lead** | 1 | Google | P&L, client exec, escalation |
> | **Lead Architect** | 1 | Google | Architecture, quality gates, KT |
> | **Data Engineers** | 4 | Partner (2) + Google (2) | Pipeline build, optimization |
> | **ML Engineers** | 2 | Partner | Vertex AI, Feature Store, models |
> | **Security/Compliance** | 1 | Google | VPC-SC, CMEK, policy tags, audit |
> | **PM/Scrum Master** | 1 | Partner | Delivery, cadence, risk |
> | **Customer SMEs** | 3 | Customer | Domain knowledge, UAT, cutover |
> | **DBAs/Infra** | 2 | Customer | Source access, network, DNS |
>
> **Total: 15 people** | **Cost: ~$1.2M over 6 months**
>
> **Model:** Google = Architecture + Quality + KT (30%). Partner = Delivery (60%). Customer = Domain + UAT + Cutover (10%).

---

### Q10: "How do you handle a customer CTO who says 'GCP is 3x more expensive than on-prem'?"

**2-Minute Answer Framework:**
> **Don't Get Defensive. Use TCO Framework.**
>
> **Step 1: Acknowledge** - "That's a common perception. Let's look at the full picture."
>
> **Step 2: Decompose** - "On-prem costs you're seeing: hardware depreciation. What about: 5 FTE ops ($750k), facilities ($300k), licenses ($700k), downtime risk, refresh cycles, opportunity cost of 6-hour batches?"
>
> **Step 3: Model Together** - "Here's our TCO calculator. Your inputs. 3-year view. On-prem: $10M. GCP: $5.5M. 45% savings. Payback: 4.5 months."
>
> **Step 4: Reference** - "Similar bank in Singapore: 62% reduction. Happy to connect you."
>
> **Step 5: Pilot** - "Let's prove it. 4-week pilot on your top 3 workloads. Success criteria: performance, cost, functionality. Go/No-Go gate."
>
> **Result:** "62% win rate on contested deals. Data wins arguments."

---

## 🎭 Role-Specific Follow-Ups

### If Interviewer is **Technical Lead**:
- Deep-dive on Dataflow shuffle optimization
- BigQuery slot contention patterns
- Dataplex lineage implementation details
- Vertex AI Feature Store point-in-time correctness

### If Interviewer is **Practice Lead / Director**:
- Pipeline growth metrics
- Partner enablement ROI
- Asset reuse rate across engagements
- Hiring/ramp strategy for consultants

### If Interviewer is **Customer-Facing / Sales**:
- Deal qualification framework
- Competitive displacement stories
- Executive presentation approach
- Objection handling (security, cost, lock-in)

### If Interviewer is **Security/Compliance**:
- VPC-SC perimeter design
- CMEK + HSM key hierarchy
- Policy tag taxonomy for MAS-TRM/PDPA
- Audit evidence automation

---

## 🚫 Trap Questions & How to Handle

| Trap Question | Don't Say | Do Say |
|---------------|-----------|--------|
| "What's your weakness?" | "I work too hard" | "I used to over-engineer. Now I ask: 'What's the simplest thing that delivers the outcome?'" |
| "Why leave current role?" | Complaints | "I've built the migration practice. Ready to scale it at Google with broader impact." |
| "Where do you see yourself in 5 years?" | "Your job" | "Leading a practice that defines how enterprises migrate to AI-ready platforms" |
| "Rate yourself 1-10 on BigQuery" | "10" | "8 on optimization, 9 on architecture, still learning on new ML features. Here's my learning plan..." |
| "What if you're wrong?" | "I'm not" | "I validate assumptions early. Pilot phase exists to prove/disprove. If wrong, we pivot with data." |

---

## 🎪 "I Don't Know" Protocol

**Never say just "I don't know." Always:**
> "I don't know the exact answer, but here's how I'd find out:
> 1. Check [specific doc/source: BigQuery quotas page, Dataflow monitoring guide]
> 2. Run a quick test in my sandbox project
> 3. Ask [specific expert: our BigQuery specialist, the Dataflow PM]
> 4. Get back to you by [specific time: end of day, tomorrow morning]"

**Example in Action:**
> Q: "What's the exact slot millisecond calculation for a DML statement?"
> A: "I don't have the formula memorized, but I know it's based on bytes processed + slot time. I'd check the BigQuery pricing doc section 4.2, run a test query with EXPLAIN ANALYZE, and confirm with our BQ specialist. Can I follow up by EOD?"

---

## 📋 Q&A Prep Checklist

- [ ] Practice all 10 guaranteed answers aloud (target: 90 sec each)
- [ ] Prepare 3 "deep-dive" artifacts (architecture diagram, migration timeline, risk register)
- [ ] Review your case study metrics cold (no notes)
- [ ] Prepare 2 questions for *them* (shows engagement)
- [ ] Water, backup clicker, PDF of slides on phone
- [ ] "I don't know but..." protocol memorized
- [ ] STAR stories for behavioral follow-ups (see star_answers.md)

---

## 🎯 Questions to Ask Them (Choose 2)

1. **Strategic:** "How does the Data & Analytics practice measure success beyond revenue—customer outcomes, partner enablement, asset creation?"
2. **Technical:** "What's the biggest technical challenge the team is solving right now in BigQuery/Dataflow/Vertex AI?"
3. **Cultural:** "How does the team balance Google's 'bottom-up innovation' with consulting's 'structured delivery'?"
4. **Growth:** "What does the career trajectory look like for a Lead Consultant who wants to stay technical vs. go management?"

---

*Q&A is not a test—it's a conversation. They want to see how you think, not just what you know. Be the consultant you'd want to hire.*