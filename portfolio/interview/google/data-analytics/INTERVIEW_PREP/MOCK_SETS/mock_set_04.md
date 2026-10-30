# Mock Interview Set 4 - Presentation Round Focus
## Round 4 Variations: Different Topics, Audiences, Formats

---

## 🎯 Mock Set 4 Overview
**Focus:** Presentation delivery, whiteboarding, storytelling, Q&A composure
**Format:** 30 min presentation + 15 min Q&A with panel
**Goal:** Master the "Google Consulting Presentation Style"

---

## MOCK 4A: Standard Migration Presentation
### Audience: Technical Architect + Practice Lead + Customer-Facing Director
### Topic: "140TB Teradata/Hadoop → BigQuery Migration - Lessons Learned"

---

### Presentation Structure (20 min)

#### Slide 1: Title (30 sec)
> "Enterprise Data Platform Migration: 140TB, 22 Weeks, 62% Cost Reduction"
> Presenter: [Name], Data & Analytics Lead
> Customer: Singapore Bank (MAS-regulated)

#### Slide 2: Business Context (1 min)
> **WHY:** $2.4M/yr OpEx → 6hr batches → 50 users → No AI → MAS-TRM mandate
> **DRIVERS:** CFO: 25% cost cut | CDO: AI-ready by 2024 | CISO: Compliance

#### Slide 3: Current State (1 min) - DRAW LIVE
> Teradata(80TB) + Hadoop(50TB) + Oracle(10TB) + Kafka
> → Informatica(200+) → Tableau/SAS/Python
> **PAIN:** Silos, batch-only, expensive, rigid

#### Slide 4: Target State (2 min) - DRAW LIVE
> Datastream(CDC) + Dataproc(Batch) + Dataflow(Stream)
> → GCS Landing → Curated → BigQuery(Raw/Staging/Serving)
> → Dataplex + Looker + Vertex AI
> **SECURITY:** VPC-SC + CMEK+HSM + Policy Tags

#### Slide 5: Why This Architecture? (1.5 min)
> Decision matrix: BigQuery vs Snowflake/Redshift, Dataflow vs Kafka, etc.
> Principle: Managed > Self-managed, Serverless > Provisioned

#### Slide 6: Migration Approach (2 min)
> 4 Phases: Assess(2w) → Pilot(4w) → Migrate(16w) → Optimize
> Dual-write 14 days, <0.1% discrepancy, 15-min RTO tested 3x

#### Slide 7: Security & Governance (1.5 min)
> VSC perimeter, CMEK+HSM (FIPS L3), Dataplex Policy Tags (47 FinServ), DLP auto-tag, RLS, Column masking

#### Slide 8: Top 3 Challenges (2 min)
> 1. 5TB shuffle skew (NULL=40%) → Salting + Shuffle Service → 14hr→4hr
> 2. 500 SPs → Classification → 60% dbt, 30% BQ Script, 10% retire
> 3. CDC+Batch reconciliation → Idempotent MERGE + watermark alignment

#### Slide 9: Results (1.5 min)
> **Financial:** $2.5M/yr savings (62%), 4.5mo payback
> **Performance:** 45min→2min (95%), 50→500+ users (10x), 6hr→15min (24x)
> **Adoption:** 12→200+ analysts, 150 certified datasets, 12 ML models

#### Slide 10: Reusable IP (1 min)
> Migration Runbook (15 projects), Terraform Module (8 envs), Dataflow Templates (500+), Policy Packs (3 industries)

#### Slide 11: Lessons Learned (1 min)
> 1. Data quality profiling in Assess 2. Partner cert before SoW 3. Business validation automation 4. Cost governance Day 1 5. Docs as code

#### Slides 12-15: Appendix (Q&A prep)
> Timeline, Validation, Cost Detail, Benchmarks, Compliance Mapping

---

### Whiteboard Practice (5 min)
**Draw from memory in 4:30:**
1. 3 columns: SOURCE | INGESTION | TARGET
2. Source boxes: Teradata, Hadoop, Oracle, Kafka
3. Ingestion arrows: Datastream, Dataproc, Dataflow
4. GCS → BQ (Raw/Staging/Serving)
5. Right side: Dataplex, Looker, Vertex AI
6. Security: VPC-SC box, CMEK locks, Policy Tags
7. Labels: Partition/Cluster, Editions, 3yr commitment

---

### Q&A Scenarios (15 min)
1. "Why not Snowflake?" → Technical + Commercial + Customer quote
2. "100TB initial load?" → 3-track: Appliance, DistCp, Datastream
3. "Rollback plan?" → 15-min tested, CDC replay, zero data loss
4. "Scale team for 10 migrations?" → IP + Partner enablement + Co-delivery
5. "Biggest mistake?" → Data quality underestimation → Automated profiling

---

## MOCK 4B: Architecture Review Presentation
### Audience: Customer CTO + Chief Architect + Google Practice Lead
### Topic: "Proposed Target Architecture for Your Data Platform Migration"

---

### Format Differences
- **More interactive:** "Stop me if questions"
- **Decision-focused:** "We recommend X because Y. Do you agree?"
- **Risk-transparent:** "Here's what could go wrong and how we mitigate"
- **Customer-specific:** Use THEIR system names, THEIR volumes, THEIR pain points

---

### Key Slides (Customer-Specific)

#### Slide 1: Your Current State (Validated)
> "Based on our Assess phase: 87TB Teradata, 23TB Hive, 5TB Oracle, 12K tables, 342 Informatica workflows"
> "Top pain: 8hr batch SLA, 30 concurrent users, $1.8M/yr, no streaming"

#### Slide 2: Recommended Target Architecture
> **Tailored to THEIR workloads:** Show THEIR specific migration patterns
> **Phased:** Phase 1 = Core DW + BI (their priority), Phase 2 = Streaming + ML

#### Slide 3: Migration Plan - YOUR Timeline
> "24 weeks total. Your constraints: Frozen period Nov-Jan, DR test Q2"
> Show Gantt with THEIR blackout dates

#### Slide 4: Risk Register - YOUR Risks
> "Top 5 risks for YOUR environment: [Specific to their tech stack]"
> Each with: Owner, Mitigation, Trigger, Contingency

#### Slide 5: Team - YOUR Team
> "Google: [Names]. Partner: [Named resources]. Customer: [Named SMEs]"
> "We co-interviewed your SMEs - they approved the team"

#### Slide 6: Commercial - YOUR Model
> "Fixed-price milestones. Your budget: $X. Our model: [Details]"
> "Go/No-Go at Pilot. You only commit to Phase 2 after Pilot success."

---

### Q&A Focus (Customer-facing)
1. "Our team has no GCP skills" → KT plan (30/60/90), sandbox, certifications
2. "We can't freeze for cutover" → Dual-write, blue-green, phased cutover
3. "Partner X burned us before" → Our governance model, named resources, substitution
4. "What if costs exceed model?" → Fixed-price, budget alerts, reservation strategy
5. "Regulatory approval timeline?" → Parallel prep, evidence pack, pre-engagement

---

## MOCK 4C: Internal Practice Presentation
### Audience: Practice Leadership + Peers
### Topic: "New Reusable Asset: FinServ Policy Pack - Adoption Plan"

---

### Format Differences
- **Peer review:** "Tear this apart"
- **Metrics-driven:** "Here's the adoption data from 3 pilots"
- **Scaling focus:** "How do we get 50 consultants using this?"
- **Investment ask:** "Need 2 engineers for 3 months to generalize"

---

### Key Slides

#### Slide 1: The Asset
> "FinServ Policy Pack: 47 Policy Tags, 23 DQ Rules, 8 DLP Templates, MAS-TRM/PCI mapping"
> "Auto-applies via Terraform. DLP auto-classifies → tags → masking/RLS enforced"

#### Slide 2: Pilot Results (3 engagements)
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Governance Setup | 4 weeks | 2 days | 95% faster |
| Audit Prep | 3 weeks | 2 days | 90% faster |
| Manual Tagging | 100% | 15% | 85% reduction |
| Compliance Findings | 3/engagement | 0 | 100% clean |

#### Slide 3: Adoption Plan
| Quarter | Target | Tactics |
|---------|--------|---------|
| Q1 | 10 consultants certified | Training + sandbox + first project |
| Q2 | 30 consultants using | Mandatory for FinServ engagements |
| Q3 | 50 consultants | Partner enablement (3 SIs) |
| Q4 | 80% adoption | Incentives: asset royalties, recognition |

#### Slide 4: Investment Ask
> 2 Engineers × 3 Months = Generalize for Healthcare + Retail packs
> ROI: 5 engagements × 2 weeks saved = 10 weeks = $400k value

#### Slide 5: Risks
> 1. Consultant adoption resistance → Incentives + mandate
> 2. DLP false positives → Tuning period + feedback loop
> 3. Partner version drift → Governance gate + version pinning

---

## MOCK 4D: Conference-Style Talk
### Audience: Mixed (Technical + Business), 30 min slot
### Topic: "From Migration to AI: How One Bank Unlocked $40M ARR"

---

### Format Differences
- **Story-first:** "Meet Sarah, CDO of Bank X..."
- **Less technical detail:** "We used Dataflow" not "Dataflow with 5-min fixed windows..."
- **Business outcomes:** Lead with $40M ARR, 15% retention lift
- **Inspirational:** "This is what's possible when data + AI unite"

---

### Structure (TED-style)

#### Opening (2 min): The Hook
> "18 months ago, Bank X had 140TB of data trapped in Teradata. Today, they predict churn before it happens, detect fraud in milliseconds, and personalize every customer interaction. The difference? Not just cloud. A platform where data and AI are one."

#### Act 1: The Trap (4 min)
> Legacy architecture pain. Business impact. "They couldn't answer 'who's leaving tomorrow?'"

#### Act 2: The Journey (8 min)
> Migration (condensed). Platform capabilities. "The moment data hit BigQuery, the art of possible changed."

#### Act 3: The Breakthrough (10 min)
> 3 use cases with numbers: Churn ($40M), Fraud (23% fewer outages), Personalization (34% CTR)
> "The platform didn't just store data. It became the innovation engine."

#### Act 4: The Pattern (4 min)
> "This isn't magic. It's a repeatable pattern: Migrate → Govern → Activate → Innovate."
> Show the 4-phase framework.

#### Closing (2 min): The Challenge
> "Your data is waiting. The platform exists. The question: What will you build?"

---

## MOCK 4E: Crisis Presentation
### Audience: Customer Executive Sponsor + Google VP
### Topic: "Cutover Risk - 2TB Discrepancy Found 24 Hours Before Go-Live"

---

### Format Differences
- **High stakes:** Career-defining moment
- **Transparent:** "Here's the problem. Here's the fix. Here's the validation."
- **Decisive:** "We recommend GO. Here's why."
- **No slides:** Whiteboard + conversation

---

### Structure (15 min + 15 Q&A)

#### The Situation (3 min)
> "Yesterday 6pm: Reconciliation job found 2TB discrepancy in transactions table. Root cause: Dual-write MERGE logic error for partition range 2024-01-15 to 2024-01-20."

#### The Fix (5 min)
> 1. Isolated: Single partition range, identifiable cause
> 2. Fixed: Corrected MERGE logic (idempotency key + source priority)
> 3. Backfilled: Dataflow job, 4 hours, validated row-by-row
> 4. Re-validated: Full reconciliation suite - ZERO discrepancies

#### The Decision (2 min)
> "Data is clean. Risk is understood and mitigated. We recommend GO on schedule."
> "Rollback tested 3x. 15-min RTO. CDC replay capability validated."

#### The Ask (1 min)
> "We need your sign-off to proceed. We'll own the hypercare 30 days. Daily standups. 24/7 on-call."

---

## Mock Set 4 Scoring

| Mock | Weight | Key Differentiator |
|------|--------|-------------------|
| 4A: Standard | 25% | Structure, whiteboard, metrics |
| 4B: Customer Review | 25% | Tailoring, interactivity, risk transparency |
| 4C: Internal | 20% | Metrics, scaling, investment logic |
| 4D: Conference | 15% | Storytelling, inspiration, simplicity |
| 4E: Crisis | 15% | Composure, transparency, decisiveness |

**Pass: ≥3.5/4.0 each, whiteboard <4:30, Q&A structured**

---

## Practice Schedule (Mock Set 4)
| Day | Mock | Format | Audience (Simulated) |
|-----|------|--------|---------------------|
| Day 1 | 4A | Full 30+15 | 3-panel (record) |
| Day 2 | 4B | 20+20 interactive | 2-panel (customer persona) |
| Day 3 | 4C | 20+10 | Peers (tear apart) |
| Day 4 | 4D | 30 min talk | Mixed (record, watch) |
| Day 5 | 4E | 15+15 crisis | VP + Sponsor personas |
| Day 6 | **Whiteboard Drills** | 5x architecture draws | Timed, self-critique |

---

*Presentation is not a talent - it's a practiced skill. The best presenters practice 20+ hours for a 30-min talk. You're not "winging it" - you're performing a rehearsed craft.*