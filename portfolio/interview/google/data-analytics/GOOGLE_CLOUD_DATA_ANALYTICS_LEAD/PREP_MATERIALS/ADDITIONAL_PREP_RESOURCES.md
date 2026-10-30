# Additional Interview Prep Resources — Google Cloud Consulting L6/L7
## Dataford, Aced/Exponent, The Data Monk — Quick Reference

---

## 🎯 Resource Quick Comparison

| Resource | Best For | Format | Cost | Authenticity |
|----------|----------|--------|------|--------------|
| **Dataford** | Cloud Consultant + EM questions | Categorized Q bank | ~$30-50/mo | High (candidate reports) |
| **Aced/Exponent** | EM/Leadership behavioral | 70+ Qs with video answers | ~$79/mo | High (verified) |
| **The Data Monk** | Data consulting cases, SQL/BQ | Business cases + stakeholder | ~$49/mo | High (senior data roles) |

---

## 📊 Dataford — Google Cloud Consultant Question Bank

### Categories to Focus On
| Category | Relevance to Your Role | Priority |
|----------|----------------------|----------|
| **Stakeholder Management** | Client CTO/CIO, LOB heads, SI partners | 🔴 Critical |
| **Technical Delivery** | Migration execution, quality gates, cutover | 🔴 Critical |
| **Migration** | 6 R's, tool selection, validation, dual-write | 🔴 Critical |
| **Leadership** | Team building, hiring, partner mgmt, P&L | 🔴 Critical |
| **Behavioral** | Googleyness, lead without authority, conflict | 🟡 High |

### Sample Dataford Questions (Cloud Consultant Track)
```
Stakeholder Management:
- "Client CTO says GCP is 3x on-prem. How do you respond with data?"
- "Sales committed to 3-month timeline. Your team says 6. Walk through the conversation."
- "LOB head refuses Data Mesh adoption. How do you influence without authority?"

Technical Delivery:
- "100TB Teradata → BigQuery. 200 Informatica jobs. 500 Tableau reports. Near-zero downtime. Your plan?"
- "Dataflow streaming job has 2hr backlog. How do you diagnose and recover?"
- "BigQuery query scans 2TB but only needs 50GB. Optimization checklist?"

Migration:
- "Hadoop/Hive → Dataproc + BigQuery. Metastore migration strategy?"
- "Oracle CDC → Datastream → Pub/Sub → Dataflow → BigQuery. Exactly-once how?"
- "Dual-write validation: row count ±0.1%, checksum, business reconciliation. Your framework?"

Leadership:
- "Build hiring plan for 10 consultants in 6 months. Google bar is high. Your framework?"
- "Partner (Accenture) misses 3 milestones. Google Sales protects revenue. Your escalation?"
- "Practice P&L: $2M ARR, 58% utilization. Target $10M, 30% margin, 85% util. Your 18-month plan?"
```

### Dataford Action Items
- [ ] Subscribe 1 month ($30-50)
- [ ] Export **Cloud Consultant** + **Engineering Manager** question sets
- [ ] Map to your MASTER_QUESTION_BANK.md categories
- [ ] Practice top 30 aloud with timer

---

## 🎭 Aced (Exponent) — Engineering Manager / Leadership

### Strengths for Your Role
- **Video explanations** — See how strong candidates structure answers
- **70+ EM questions** — People management, org design, conflict, hiring
- **Google-specific** — Filter by company = Google

### Key Question Buckets
| Bucket | Sample Questions | Your STAR Mapping |
|--------|------------------|-------------------|
| **People Management** | "Low performer turnaround", "Team conflict resolution", "Career coaching framework" | Your 92% retention story |
| **Hiring & Team Building** | "Hiring bar", "Diverse slate", "Ramp to productivity" | Your 41-day fill, 50% diverse |
| **Org Design** | "IC vs Manager track", "Span of control", "Rotation programs" | Your career ladders + rotation |
| **Execution** | "Competing priorities", "Technical debt vs features", "Deadline pressure" | Your migration factory delivery |
| **Influence** | "Disagree with director", "Cross-functional alignment", "Say no to stakeholder" | Your partner escalation + scope creep |

### Aced Action Items
- [ ] Subscribe 1 month ($79) — focus on EM track
- [ ] Watch video answers for: Low performer, Hiring bar, Influence without authority, Technical debt
- [ ] Adapt their STAR structure to your stories
- [ ] Practice: "Tell me about a time you led without authority" (Google favorite)

---

## 📈 The Data Monk — Senior Data Consultant Cases

### Strengths for Your Role
- **Business cases** — Not just SQL, but "client wants X, data is Y, recommend Z"
- **Stakeholder communication** — How to present to C-level vs technical
- **BigQuery/SQL focus** — Realistic complexity (partitioning, clustering, optimization)
- **Consulting lens** — Scope, estimation, delivery, change management

### Sample Case Types
```
Case 1: Retail Client - Real-time Personalization
- "Client has 5M customers, 1B events/day. Wants real-time recommendations.
  Current: Batch nightly. Budget: $200K/month. Design end-to-end."
  
Case 2: Bank - Regulatory Reporting (MAS-TRM)
- "100TB transaction data. MAS 600-second reporting SLA. 
  Current: Oracle Exadata. Design GCP architecture with compliance."

Case 3: Telco - Churn Prediction at Scale
- "50M subscribers. 500 features. Model retrain weekly. 
  Vertex AI + BigQuery ML. Feature store design. Cost optimization."

Case 4: Migration - Hadoop to BigQuery (Consulting Delivery)
- "200TB, 500 pipelines, 3 SIs. 8 months. Fixed-fee milestones. 
  Risk register, quality gates, partner governance."
```

### The Data Monk Action Items
- [ ] Subscribe 1 month ($49)
- [ ] Complete 5-7 cases focused on: Migration, Real-time, ML Platform, Compliance
- [ ] Practice presenting to "CTO" (3-min executive summary)
- [ ] Extract SQL/BQ patterns to your optimization checklist

---

## 🔄 Integrated Resource Strategy

### Week 1: Question Volume (Dataford)
```
Day 1-2: Dataford Cloud Consultant questions → MASTER_QUESTION_BANK.md
Day 3-4: Dataford EM questions → MASTER_QUESTION_BANK.md (Leadership section)
Day 5:   Categorize all, identify gaps in your STAR stories
```

### Week 2: Answer Quality (Aced/Exponent)
```
Day 1-2: Watch Aced videos for your weak areas (hiring, influence, conflict)
Day 3-4: Refine your STAR stories using their structure
Day 5:   Record yourself answering top 10 behavioral questions
```

### Week 3: Case Fluency (The Data Monk)
```
Day 1-3: Complete 5 cases (Migration, Real-time, ML, Compliance, Cost)
Day 4:   Practice whiteboard + executive summary for each
Day 5:   Get peer feedback on case presentations
```

### Week 4: Integration + Mocks
```
Combine all: Your frameworks + their questions + your stories
Mock interviews (Interviewing.io) using this integrated prep
```

---

## 💰 Cost-Optimized Approach

| Strategy | Cost | Coverage |
|----------|------|----------|
| **All 3 (1 month each)** | ~$180 | Maximum coverage, best for final 4 weeks |
| **Dataford + Aced only** | ~$130 | Questions + answer quality (skip cases if strong) |
| **Dataford only** | ~$40 | Questions only (if you have strong STAR stories) |
| **Free alternatives** | $0 | Prepfully (30-day free) + Glassdoor + your portfolio |

**Recommendation:** **Dataford + Aced** ($130) — covers question breadth + answer quality. The Data Monk cases are nice-to-have if you need consulting case practice.

---

## 📋 Cross-Reference with Your Portfolio

| Your Artifact | Dataford Category | Aced Category | Data Monk Case |
|---------------|-------------------|---------------|----------------|
| Migration Factory | Migration, Technical Delivery | Execution | Case 4 |
| Partner Scorecard | Stakeholder Mgmt, Leadership | Influence, Execution | Case 4 |
| MAS-TRM Architecture | Technical Delivery, Migration | Execution | Case 2 |
| AI Platform Strategy | Technical Delivery, Leadership | Org Design | Case 3 |
| P&L / Practice Building | Leadership | People Mgmt, Org Design | — |
| Hiring Framework | Leadership, Behavioral | Hiring & Team Building | — |
| Certification Program | Leadership | People Mgmt | — |

---

## ✅ This Week's Actions

- [ ] **Dataford:** Subscribe, export Cloud Consultant + EM questions (2 hours)
- [ ] **Aced:** Subscribe, watch 5 key videos (Low performer, Hiring, Influence, Conflict, Tech Debt) (3 hours)
- [ ] **The Data Monk:** Optional — if consulting cases are weak area, do 3 cases (4 hours)
- [ ] **Integrate:** Add all new questions to MASTER_QUESTION_BANK.md with source tags
- [ ] **Practice:** Top 20 questions aloud, timed, recorded (2 hours)

---

*These 3 resources complement your portfolio perfectly: Dataford (question volume), Aced (answer quality), Data Monk (case fluency). Total ~$130-180 for 1 month = best ROI for final prep sprint.*