# Mock Interview Set 5 - Cognitive/Behavioral Deep-Dive
## Round 5 Variations: Googleyness, Leadership, Singapore, Technical, Objections

---

## 🎯 Mock Set 5 Overview
**Focus:** Pure behavioral/cognitive - no technical deep-dive, no presentation
**Format:** 60 min with cross-functional panel (Director, HR, Peer, Partner Lead)
**Goal:** Demonstrate Googleyness, leadership maturity, cultural add

---

## MOCK 5A: Googleyness & Values (Core)
### Interviewers: Director + HR Business Partner
### Focus: 4 Google Attributes - Humility, User Focus, Ambiguity, Influence

---

### Questions & STAR Mapping

#### Q1: "Tell me about a time you were wrong. Technically wrong. How did you handle it?"
**STAR:** STAR 1 (Data Quality) or STAR 7 (Shuffle Skew)
**Signals:** Ownership, specific learning, systemic fix, applied since
**Follow-up:** "What did you change in your process?" → Automated profiling in Assess phase

#### Q2: "Describe a situation where you had to deliver bad news to a customer executive."
**STAR:** STAR 15 (Cutover Crisis) or STAR 3 (Scope Creep)
**Signals:** Direct but empathetic, data-driven, options presented, owned the outcome
**Follow-up:** "How did the relationship change?" → Strengthened through transparency

#### Q3: "How do you handle a situation where you don't know the answer, but the customer expects you to?"
**STAR:** STAR 2 (CTO Cost Objection) + Protocol
**Signals:** "I don't know, but here's my plan and timeline" - never fake, always follow through
**Follow-up:** "Give me a real example." → BQ slot millisecond formula - followed up in 4 hours

#### Q4: "Tell me about a time you pushed back on a customer request because it wasn't right for them."
**STAR:** STAR 11 (Say No to Lift-and-Shift)
**Signals:** Customer outcome > revenue, data-driven alternative, preserved relationship
**Follow-up:** "What if they insisted?" → Escalate to sponsor with data, "I'd rather lose the deal than deliver wrong"

#### Q5: "Describe a time you influenced a decision without formal authority."
**STAR:** STAR 4 (Dataflow vs Kafka) or STAR 5 (CTO Objection) or STAR 6 (Prioritization)
**Signals:** Evidence-based, framed as shared win, built coalition, documented decision
**Follow-up:** "What if they still disagreed?" → Pilot both, data decides, ADR documents

#### Q6: "How do you prioritize when everything is urgent and resources are fixed?"
**STAR:** STAR 6 (MoSCoW + Impact/Effort workshop)
**Signals:** Framework (not gut), transparent communication, stakeholder co-ownership
**Follow-up:** "What did you explicitly say NO to?" → Nice-to-have optimizations, documented why

#### Q7: "What does 'Focus on the User' mean in your consulting practice?"
**Answer:** See star_answers.md Q5
**Signals:** Outcomes > utilization, sustainable delivery, long-term > short-term, saying no when needed
**Follow-up:** "When did you last say no to a customer?" → STAR 11

---

## MOCK 5B: Leadership & Strategy
### Interviewers: Managing Director + Practice Lead
### Focus: Team building, P&L, partner scaling, hiring, practice strategy

---

### Questions

#### Q1: "You're taking over a practice with flat revenue, declining margin, 20% attrition. 90-day plan?"
**STAR:** MOCK 3A Q1 (extended)
**Signals:** Assess→Stabilize→Build→Scale, specific metrics, quick wins + structural fixes
**Follow-up:** "What's the first metric you'd fix?" → Utilization (bench cost killing margin)

#### Q2: "How do you decide between investing in reusable IP vs. custom delivery for a strategic account?"
**STAR:** MOCK 3D Q2 (Build vs Buy vs Partner)
**Signals:** Framework (differentiation, reuse, margin), not binary, portfolio approach
**Follow-up:** "When would you NOT build IP?" → One-off use case, no pattern, time-critical

#### Q3: "Your top performer wants to be a People Manager. They're a brilliant IC. Advice?"
**STAR:** MOCK 3C Q4 (Dual Career Ladder)
**Signals:** Dual ladder exists, IC path = same prestige/comp, management = different skills, not promotion
**Follow-up:** "How do you evaluate management potential?" → Mentoring track record, conflict resolution, team outcomes

#### Q4: "Partner wants to co-create IP. You want to keep it Google-owned. Negotiation?"
**STAR:** MOCK 3D Q2 (Co-creation model)
**Signals:** Core = Google, Industry variants = Co-created, clear IP terms, 12-month exclusivity
**Follow-up:** "What if they walk?" → "We'd rather lose the co-creation than lose control of core IP"

#### Q5: "How do you measure a consultant's 'consulting ability' vs 'technical ability'?"
**Answer:** 50/50 weight in hiring. Consulting sim round (Round 3). Values veto. Promotion criteria: both.
**Signals:** Structured assessment, not gut, consulting = learnable but not optional

---

## MOCK 5C: Singapore & APAC Context
### Interviewers: APAC Practice Lead + Singapore Customer-Facing Lead
### Focus: MAS-TRM, PDPA, data residency, partner ecosystem, cultural nuance

---

### Questions

#### Q1: "Walk me through MAS-TRM 6.3, 7.2, 8.1, 9.1 and your GCP control mappings."
**Answer:** See singapore_context.md - cold, specific, evidence-ready
**Signals:** Cold knowledge, control-by-control, evidence pack awareness, auditor perspective
**Follow-up:** "What's the hardest control to satisfy?" → 9.1 Vendor mgmt (partner scorecards + contractual)

#### Q2: "Customer in Singapore, but data processing in India team. PDPA compliant?"
**Answer:** Organization Policy = asia-southeast1 only. India team accesses via VPC-SC, no data egress. DLP prevents PII export. Audit logs show access patterns.
**Signals:** Technical enforcement > policy, VPC-SC as data boundary, not just network
**Follow-up:** "What if India team needs production data for debugging?" → Synthetic data, sampled anonymized, time-boxed access with approval

#### Q3: "Singapore bank acquiring Malaysian bank. Data residency requirements differ. Architecture?"
**Answer:** Hub (Singapore) + Spoke (Malaysia). Hub: Core DW, Governance, ML. Spoke: Local landing zone, ingestion, serving. BigQuery Omni for cross-region query. Org Policy per country.
**Signals:** Hub-spoke pattern, Omni for federation, Org Policy enforcement, not just "multi-region"

#### Q4: "How do you build trust with Singapore government/FinServ stakeholders?"
**Answer:** Relationship-first (coffee chats), hierarchy-aware (include seniors), face-saving (never public contradict), compliance-native (security=baseline), multi-lingual awareness.
**Signals:** Cultural intelligence, not just technical, specific behaviors not stereotypes
**Follow-up:** "Mistake you made culturally?" → Too direct in first meeting with senior regulator. Learned: "Yes, and..." framing.

#### Q5: "Partner ecosystem in Singapore - who are the Strategic vs Select vs Boutique?"
**Answer:** See singapore_context.md partner table
**Signals:** Market knowledge, tier differentiation, engagement model per tier
**Follow-up:** "Which partner would you choose for a GovTech Smart Nation project?" → NCS (GovTech spinout, SingPass, public sector creds)

---

## MOCK 5D: Technical Fundamentals (Rapid-Fire)
### Interviewers: Senior Architect + Principal Engineer
### Focus: Speed, accuracy, depth, "I don't know but..." protocol

---

### Format: 20 Questions × 90 seconds each = 30 min, then 15 min deep-dive on 2

---

### Rapid-Fire Questions (Answer in ≤90 sec)

| # | Question | Target Answer Time |
|---|----------|-------------------|
| 1 | BigQuery architecture - storage vs compute | 45 sec |
| 2 | Partition vs Cluster - when each? | 45 sec |
| 3 | Slot contention - diagnosis + 3 solutions | 60 sec |
| 4 | Streaming Write API vs legacy insertAll | 45 sec |
| 5 | BQML → Vertex promotion steps | 60 sec |
| 6 | Dataflow exactly-once - 3 layers | 60 sec |
| 7 | Windowing: Fixed vs Session vs Sliding | 60 sec |
| 8 | Shuffle skew - salting + pre-aggregation | 60 sec |
| 9 | Dataproc vs Dataflow - decision criteria | 60 sec |
| 10 | Composer 2 vs 1 - key differences | 45 sec |
| 11 | Vertex Feature Store - online vs offline | 60 sec |
| 12 | VPC-SC - how prevents exfiltration | 60 sec |
| 13 | CMEK vs CMEK+HSM vs CSEK | 45 sec |
| 14 | Dataplex Policy Tags → Masking/RLS | 60 sec |
| 15 | Org Policy for data residency | 45 sec |
| 16 | BigQuery Omni - how it works | 45 sec |
| 17 | Dataflow Flex Template vs Classic | 45 sec |
| 18 | MERGE for CDC idempotency | 60 sec |
| 19 | Cost optimization: 5 specific techniques | 60 sec |
| 20 | "I don't know" - your protocol | 30 sec |

---

### Deep-Dive Topics (Pick 2 based on weak areas)

#### Deep-Dive 1: BigQuery Internals
- Colossus, Dremel, Borg, Capacitor format
- Slot scheduling (fair, capacity, autoscaling)
- Metadata cache, BI Engine, materialized view refresh
- Storage Write API protocol, exactly-once semantics

#### Deep-Dive 2: Dataflow Streaming Internals
- Windmill/Bundle-based processing
- Watermark propagation, Garbage collection
- Shuffle service architecture
- Stateful processing, Timers, State API
- Autoscaling algorithms, Worker lifecycle

#### Deep-Dive 3: Security Internals
- VPC-SC implementation (VPC peering, PSC, DNS)
- Cloud KMS + Cloud HSM key hierarchy
- IAM Conditions evaluation, Deny Policies precedence
- Binary Authorization, Container Analysis

---

## MOCK 5E: Objection Handling (Roleplay)
### Interviewers: Customer-Facing Director + Sales Lead
### Focus: Composure, structure, evidence, "Googleyness" under pressure

---

### Format: 4 Scenarios × 10 min each

---

### Scenario 1: "Your TCO is fiction. My team says BigQuery costs 3x Teradata."
**Persona:** Skeptical CFO, has spreadsheet
**Your Response:** A.C.E. (Acknowledge, Clarify, Evidence)
**Trap:** Getting defensive, arguing with their numbers
**Win:** "Let's model together. Your inputs. 3-year view. Pilot proves it."

### Scenario 2: "MAS-TRM says data on-prem. Cloud = non-compliant."
**Persona:** CISO, auditor background
**Your Response:** Control mapping, evidence pack, 3 bank references
**Trap:** "But the regulation says..."
**Win:** "Here's the MAS examination result on this architecture. Zero findings."

### Scenario 3: "We'll never leave GCP if we use BigQuery/Dataflow/Vertex. Lock-in is unacceptable."
**Persona:** Chief Architect, multi-cloud mandate
**Your Response:** Data vs Compute lock-in, Omni, Beam, dbt, Terraform
**Trap:** Arguing "you're wrong"
**Win:** "Let's map your 5-year portability requirements to architecture decisions."

### Scenario 4: "Your partner's architects don't know BigQuery. We need Google engineers."
**Persona:** Technical Lead, been burned by SI before
**Your Response:** Named resources, quality gates, substitution clause, Google accountability
**Trap:** "Just give us Google engineers"
**Win:** "Google-only = 3x cost, 6-month wait. Co-delivery = best of both. Interview our named architects."

---

## Mock Set 5 Scoring

| Mock | Weight | Pass Criteria |
|------|--------|---------------|
| 5A: Googleyness | 30% | All STARs structured, values evident, no "we" for own actions |
| 5B: Leadership | 25% | Strategic frameworks, specific metrics, dual ladder philosophy |
| 5C: Singapore | 20% | Cold regulatory knowledge, cultural intelligence, partner map |
| 5D: Technical | 15% | ≥16/20 rapid-fire correct, deep-dive shows expertise |
| 5E: Objections | 10% | Composure, A.C.E. structure, evidence, pilot close |

**Overall Pass: No values veto, ≥3.5/4.0 weighted average**

---

## Practice Schedule (Mock Set 5)
| Day | Mock | Format | Partner |
|-----|------|--------|---------|
| Day 1 | 5A | 60 min STAR-only | HR-experienced peer |
| Day 2 | 5B | 45 min + debrief | Director-level peer |
| Day 3 | 5C | 45 min cold Q&A | Singapore-experienced peer |
| Day 4 | 5D | 30 min rapid + 15 deep | Principal Engineer peer |
| Day 5 | 5E | 4×10 min roleplay | Sales/Customer-facing peer |
| Day 6 | **Full 5A-5E Rotation** | Random, timed | Different partner each |

---

*Round 5 is the "gut check" - they're deciding: "Can this person represent Google in front of our biggest customers?" Every answer must ladder to: Customer outcome, Practice scaling, Google values.*