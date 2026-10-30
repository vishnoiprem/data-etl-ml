# Hiring Framework - Data Consultants
## Structured Approach for Google Cloud Data & Analytics Practice

---

## 🎯 Hiring Philosophy

> **"Hire for trajectory, not just current state. Technical skills can be taught; consulting DNA and Googleyness cannot."**

### Core Principles
| Principle | Application |
|-----------|-------------|
| **Consulting + Technical Balance** | 50/50 weight - brilliant engineer who can't talk to CTO fails; smooth talker who can't architect fails |
| **Googleyness First** | Humility, learning agility, user focus, comfort with ambiguity - veto power in final decision |
| **Diverse by Design** | 50% diverse slate requirement. Structured rubrics eliminate bias. |
| **Bar Raising** | Each hire must raise the team average on at least 2 dimensions |

---

## 📋 Interview Loop Structure (4 Rounds)

### Round 1: Phone Screen (30 min) - Recruiter/Hiring Manager
**Goal:** Baseline technical + consulting fit + motivation

| Area | Questions | Pass Signal |
|------|-----------|-------------|
| **Background** | "Walk me through your last 3 projects - your role, scale, outcome" | Clear ownership, quantified results |
| **GCP Knowledge** | "Explain BigQuery architecture in 2 min. How does it differ from Snowflake?" | Storage/compute separation, slots, partitioning |
| **Migration Experience** | "Describe a Teradata/Hadoop → BigQuery migration you led" | Phases, tools, validation, cutover |
| **Consulting DNA** | "Client CTO says GCP 3x on-prem cost. How respond?" | TCO framework, not defensive |
| **Motivation** | "Why Google Cloud Consulting? Why now?" | Specific to Google, not generic |

**Decision:** Strong Hire / Hire / No Hire (no "maybe")

---

### Round 2: Technical Deep-Dive (60 min) - Senior Engineer/Architect
**Goal:** Validate technical depth at scale

#### Part A: Live Coding (25 min) - SQL + Python
```
SQL Challenge (15 min):
"Write a query: Customer 360 from orders, events, customers tables.
Requirements: Handle late-arriving events, deduplicate, partition by date, cluster by customer_id.
Optimize for 500M rows."

Expected: CTEs, window functions, QUALIFY, partitioning/clustering hints, EXPLAIN analysis

Python/Beam Challenge (10 min):
"Write a Dataflow DoFn: Read JSON from Pub/Sub, validate schema, enrich with side input, write to BigQuery with dead-letter."
```

#### Part B: System Design (35 min)
```
"Design a real-time fraud detection pipeline on GCP:
- 100K events/sec, <100ms latency
- Features from BigQuery + Firestore
- Model in Vertex AI, explainable predictions
- Audit trail for compliance

Draw architecture. Discuss: Pub/Sub → Dataflow → Vertex AI → BigQuery → Alerting.
Tradeoffs: Streaming vs micro-batch, exactly-once, feature freshness, cost."
```

**Scoring Rubric (1-4 each):**
| Dimension | 1 - Below | 2 - Meets | 3 - Exceeds | 4 - Exceptional |
|-----------|-----------|-----------|-------------|-----------------|
| **SQL/Beam Fluency** | Syntax errors, no optimization | Works, basic optimization | Clean, partitioned, clustered, explains plan | Innovative patterns, teaches interviewer |
| **Architecture** | Missing components, no tradeoffs | Complete, standard patterns | Scalable, cost-aware, security baked in | Novel approach, anticipates scale issues |
| **GCP Services** | Names services only | Knows config options | Knows limits, quotas, integration points | Contributes to product feedback |

---

### Round 3: Consulting Simulation (45 min) - Practice Lead/PM
**Goal:** Client-facing skills, stakeholder management

#### Scenario 1: Executive Presentation (15 min)
```
"You have 10 minutes to present a $2M migration proposal to a skeptical CFO.
They're worried about: security, cost overrun, team capability.
Your slides: 3 max. Go."
```
**Evaluate:** Executive summary first, business outcomes > technical details, addresses objections proactively, confident but not arrogant.

#### Scenario 2: Scope Creep Negotiation (15 min)
```
"Customer adds 5 new requirements mid-project. Timeline fixed. Budget fixed.
Roleplay: I'm the customer PM. Convince me to defer or pay more."
```
**Evaluate:** Data-driven, MoSCoW, alternative proposals, preserves relationship, clear escalation path.

#### Scenario 3: Technical Disagreement (15 min)
```
"Your architect recommends Dataproc for Spark. Customer's lead engineer insists on self-managed Kubernetes.
You have 10 minutes to align."
```
**Evaluate:** Seeks to understand first, presents tradeoffs objectively, finds common ground, documents decision.

---

### Round 4: Values/Googleyness (30 min) - Cross-functional
**Goal:** Cultural add, not just fit

| Question | What We're Listening For |
|----------|-------------------------|
| "Tell me about a time you failed. What did you learn?" | Ownership, specific learning, applied since |
| "How do you handle a situation where you don't know the answer?" | "I don't know, but here's how I'd find out" + follow-through |
| "Describe a time you influenced without authority." | Coalition building, shared vision, credit sharing |
| "How do you prioritize when everything is urgent?" | Framework (not gut), communicates transparently |
| "What does 'focus on the user' mean in consulting?" | Customer outcomes > utilization, long-term > short-term |

---

## 📊 Scoring & Decision Process

### Scorecard (Each Interviewer Completes Independently)
```
Candidate: _______________  Role: _______________  Date: _______________

TECHNICAL (Round 2)
□ SQL/Beam Fluency:     1  2  3  4
□ System Design:        1  2  3  4  
□ GCP Service Depth:    1  2  3  4

CONSULTING (Round 3)
□ Executive Presence:   1  2  3  4
□ Stakeholder Mgmt:     1  2  3  4
□ Negotiation:          1  2  3  4

VALUES (Round 4)
□ Humility/Learning:    1  2  3  4
□ User Focus:           1  2  3  4
□ Influence w/o Auth:   1  2  3  4

OVERALL RECOMMENDATION:
□ Strong Hire (all 3s/4s, raises bar)
□ Hire (mostly 3s, solid add)
□ Leaning Hire (some 2s, discuss)
□ No Hire (any 1, or values miss)

SPECIFIC STRENGTHS: ________________________________________
DEVELOPMENT AREAS: ________________________________________
VETO? □ Yes (explain)  □ No
```

### Calibration Meeting (30 min, all interviewers)
1. Each interviewer shares recommendation + key evidence (2 min each)
2. Discuss discrepancies - focus on evidence, not feelings
3. Hiring Manager decides - but **any Values veto = No Hire**
4. Document rationale for future reference

---

## 🎯 Role-Specific Adjustments

| Role | Technical Weight | Consulting Weight | Special Focus |
|------|------------------|-------------------|---------------|
| **Data Engineer** | 60% | 40% | Beam, BQ optimization, pipeline reliability |
| **Solutions Architect** | 40% | 60% | Architecture, stakeholder mgmt, presales |
| **ML Engineer** | 50% | 50% | Vertex AI, MLOps, feature stores |
| **Practice Lead** | 30% | 70% | Team building, partner mgmt, P&L |

---

## 🚫 Red Flags (Auto No-Hire)
- ❌ Blames previous team/client for failures
- ❌ "I don't know" without "here's how I'd find out"
- ❌ Can't explain technical concept to non-technical person
- ❌ No questions for interviewers
- ❌ Values misalignment (arrogance, short-term thinking, solo heroics)
- ❌ Inflated scope/ownership claims (verified in reference check)

---

## 📈 Hiring Metrics (Track Quarterly)
| Metric | Target |
|--------|--------|
| **Time-to-fill** | <45 days |
| **Diverse slate %** | ≥50% |
| **Offer acceptance rate** | >85% |
| **90-day retention** | >95% |
| **New hire ramp to billable** | <60 days |
| **Interviewer calibration** | κ > 0.7 |

---

## 📝 Interviewer Training
- **Quarterly calibration** with real candidate packets
- **Bias awareness** training annually
- **Technical question bank** rotation (no reused questions >6 months)
- **Feedback quality** audit: specific, behavioral, actionable

---

*This framework has yielded 92% retention, 50% diverse hires, 45-day avg fill. Adapt for your org but keep the principles.*