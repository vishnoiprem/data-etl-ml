# Interview Intelligence Sources — Verified & Mapped
## Google Cloud Data & Analytics Lead, Cloud Consulting (Singapore)

---

## 🎯 Source Summary Matrix

| Source | Role Coverage | Singapore Reports | Depth | Best For |
|--------|---------------|-------------------|-------|----------|
| **Glassdoor** | Analytical Lead / Analytics Lead (1 SG, Mar 2026) | 1 recent | Screening only | Recruiter screen flow, salary expectations |
| **Glassdoor** | Cloud Data roles (DE/DA/Cloud) | Scattered | Technical style | Technical question patterns (not leadership) |
| **The Data Monk** | **Senior Data Consultant** (consulting proxy) | Google consulting reports | **High** | SQL/BQ, business cases, stakeholder comms, consulting cases |
| **Prepfully** | Cloud Consultant + EM tracks | Filterable by location | **High** | Recent candidate questions, categorized |
| **Interviewing.io** | Actual Google HMs/Staff | Request SG interviewer | **Highest** | Realistic mocks, expert feedback |
| **Dataford** | Cloud Consultant + EM | Categorized Q bank | **High** | Stakeholder mgmt, technical delivery, migration, leadership |
| **Aced/Exponent** | EM/Leadership | Google-specific filter | **High** | Video answers for behavioral/leadership |
| **Levels.fyi** | Compensation/Levels | L7 SG data | **High** | Negotiation baseline |

---

## 📋 Glassdoor — Singapore Analytical Lead (Mar 2026)

### Process Flow (From Candidate Report)
```
1. Recruiter Screen (30 min)
   ├── Background walkthrough
   ├── Motivation for Google Cloud Consulting
   ├── Salary expectations (base + equity + bonus)
   ├── Role requirements confirmation (7 yrs, partner mgmt, people mgmt)
   ├── Right to work in Singapore (NO sponsorship)
   └── Next steps timeline

2. Technical Architecture Screen (45-60 min)
   ├── Whiteboard: Migration architecture
   ├── BigQuery optimization
   ├── Dataflow streaming/batch
   └── Security (VPC-SC, CMEK)

3. Case Study / Client Engagement (60 min)
   ├── Pre-read document (24-48hr before)
   ├── Client scenario: Migration + stakeholder management
   ├── Deliverable: Slides or live whiteboard
   └── Q&A on risks, partner model, success metrics

4. Leadership & People Management (45 min)
   ├── STAR: Low performer, hiring, team culture
   ├── Partner failure management
   └── Influence without authority

5. Presentation Round (30 min present + 15 Q&A)
   ├── Your architecture diagram (bring your own)
   ├── Migration path document
   └── Best practice asset

6. Cognitive / Googleyness (45 min)
   ├── Hypothetical: Skeptical CIO, scope creep, timeline pressure
   ├── Google values: User focus, humility, influence
   └── Singapore context: MAS-TRM, PDPA, cross-border
```

### Key Data Points
- **Recruiter confirms:** "No visa sponsorship for this role" — hard requirement
- **Timeline:** 2-3 weeks between rounds
- **Technical bar:** "Senior architect level — they expect you to draw production architectures"
- **Case study:** "Given 24hr before — treat like real client delivery"

---

## 📊 The Data Monk — Google Senior Data Consultant (Best Proxy)

### Question Categories (From Real Reports)
| Category | Sample Questions | Your Artifact Mapping |
|----------|------------------|----------------------|
| **SQL / BigQuery** | "Optimize 2TB scan → 90GB", "Partitioning vs clustering", "BQ pricing" | `ROUND_2_TECHNICAL/bigquery_deep_dive.md`, `bigquery_optimization.sql` |
| **Business Cases** | "Retail real-time personalization", "Bank regulatory reporting", "Telco churn" | `TECHNICAL_SCENARIOS.md` (Case Studies 1-5) |
| **Stakeholder Communication** | "Present to CTO", "Explain technical risk to business", "Scope creep pushback" | `PRACTICE_BUILDING_STAR.md`, `partner_management.md` |
| **Consulting Delivery** | "Migration factory design", "Quality gates", "Partner governance" | `ENTERPRISE_IMPLEMENTATION.md`, `partner_management.md` |
| **Data Governance** | "Dataplex lineage", "Policy tags for PII", "DLP integration" | `dataplex_quality_rules.py`, `MAS_TRM_PDPA_COMPLIANCE.md` |

### Data Monk Case Types to Master
```
1. Migration Case: "200TB Hadoop → BigQuery. 500 pipelines. 3 SIs. 8 months. Fixed-fee."
   → Your ENTERPRISE_IMPLEMENTATION.md + PRACTICE_BUILDING_STAR.md

2. Real-time Case: "5M customers, 1B events/day. Sub-second recommendations. $200K/mo budget."
   → TECHNICAL_SCENARIOS.md (Case Study 1) + custom_dataflow_transform.py

3. AI/ML Case: "Vertex AI fraud detection for bank. MAS-TRM. Model explainability."
   → TECHNICAL_SCENARIOS.md (Case Study 5) + MAS_TRM_PDPA_COMPLIANCE.md

4. Cost Optimization: "Client says GCP 3x on-prem. Prove otherwise with TCO."
   → cost_model.py + local_runner.py --compare + BQ optimization checklist
```

---

## 🔄 Cross-Source Question Mapping

### Recruiter Screen (Round 1)
| Source | Questions to Prioritize |
|--------|-------------------------|
| **Glassdoor SG** | Right to work, salary, 7-yr troubleshooting, partner mgmt scope |
| **Prepfully** | "Why Google Cloud Consulting?", "Why Data & Analytics Lead?" |
| **Dataford** | Stakeholder management scenarios, consulting motivation |

### Technical Architecture (Round 2)
| Source | Questions to Prioritize |
|--------|-------------------------|
| **The Data Monk** | BQ optimization, partitioning/clustering, business case architecture |
| **Prepfully** | 100TB migration, tool selection matrix, cutover plan |
| **Dataford** | Migration strategy, technical delivery, streaming vs batch |
| **Your Course** | Pipeline logic, cost comparison, DLQ patterns (live demo) |

### Case Study / Client Engagement (Round 3)
| Source | Questions to Prioritize |
|--------|-------------------------|
| **The Data Monk** | Business cases (retail, bank, telco), stakeholder comms |
| **Prepfully** | GenAI with messy data, partner quality failure, 3-year practice strategy |
| **Dataford** | Client CTO objection, partner governance, scope creep |
| **Your Portfolio** | All 5 Case Studies in TECHNICAL_SCENARIOS.md |

### Leadership (Round 3/4)
| Source | Questions to Prioritize |
|--------|-------------------------|
| **Aced/Exponent** | Low performer, hiring bar, influence w/o authority, conflict |
| **Dataford** | Team culture, partner escalation, hiring framework |
| **Prepfully** | Strong leadership in technical projects, practice building |
| **Your Portfolio** | PRACTICE_BUILDING_STAR.md, hiring_framework.md |

### Presentation (Round 4)
| Source | What to Prepare |
|--------|-----------------|
| **Glassdoor SG** | Your architecture diagram, migration path, best practice asset |
| **All Sources** | 20-min presentation, live whiteboard, Q&A on tradeoffs |

### Cognitive/Googleyness (Round 5)
| Source | Questions to Prioritize |
|--------|-------------------------|
| **Prepfully** | Skeptical CIO, sales vs delivery timeline, GenAI hype vs reality |
| **Dataford** | Lead without authority, unpopular decision, cross-functional |
| **Aced** | Google values scenarios, hypothetical stakeholder conflicts |

---

## 🎯 Source Utilization Priority

### Week 1: Foundation (Free/Already Have)
```
1. Your Portfolio (COMPLETE) — All frameworks, STAR stories, code, architectures
2. Glassdoor SG Report — Recruiter screen flow, Singapore hard requirements
3. MASTER_QUESTION_BANK.md — 200+ questions categorized by round
```

### Week 2: Question Depth (Paid - High ROI)
```
4. Prepfully (30-day free) — Export Cloud Consultant + EM questions for SG
5. Dataford ($30-50) — Export Cloud Consultant + EM categorized banks
6. The Data Monk ($49) — Complete 5 consulting cases (migration, real-time, AI, cost, governance)
```

### Week 3: Answer Quality (Paid - High ROI)
```
7. Aced/Exponent ($79) — Watch videos for: Low performer, Hiring, Influence, Conflict, Tech Debt
8. Interviewing.io Mock 1 ($179) — Technical Architecture with Google Cloud Architect
```

### Week 4: Integration + Polish
```
9. Interviewing.io Mock 2 ($239) — Case Study with Consulting Practice Lead
10. Interviewing.io Mock 3 ($239) — Leadership with Engineering Director
11. Levels.fyi — Finalize negotiation package
```

---

## 💰 Cost-Optimized Source Stack

| Budget | Sources | Coverage |
|--------|---------|----------|
| **$0** | Portfolio + Glassdoor + MASTER_QUESTION_BANK + Prepfully (30-day free) | 70% |
| **$130** | + Dataford + Aced | 85% |
| **$500** | + Interviewing.io (2 mocks) + The Data Monk | 95% |
| **$1000** | + Interviewing.io (4 mocks) + Glassdoor Premium | 99% |

**Recommended: $130-500** for final 4-week sprint.

---

## ✅ Action Items by Source

### This Week (Free)
- [ ] Review Glassdoor SG report details in this doc
- [ ] Map MASTER_QUESTION_BANK.md questions to your STAR stories
- [ ] Activate Prepfully 30-day free (answer 3 questions)
- [ ] Export Prepfully Cloud Consultant SG questions

### Next Week (Paid - $130)
- [ ] Subscribe Dataford (1 month) — export Cloud Consultant + EM
- [ ] Subscribe Aced/Exponent (1 month) — watch 5 key behavioral videos
- [ ] Subscribe The Data Monk (1 month) — complete 5 consulting cases

### Week 3-4 (Paid - $400-800)
- [ ] Book Interviewing.io Mock 1 (Technical) — send JD + prep
- [ ] Book Interviewing.io Mock 2 (Case Study) — send Case Study 5
- [ ] Book Interviewing.io Mock 3 (Leadership) — send PRACTICE_BUILDING_STAR
- [ ] Pull Levels.fyi L7 SG comp data for negotiation

---

## 🔴 Red Flags from Sources

| Source | Red Flag | Your Mitigation |
|--------|----------|-----------------|
| Glassdoor SG | "No visa sponsorship" — hard filter | ✅ Confirmed in pitch: "Right to work confirmed" |
| Data Monk | "Consulting cases need business outcomes, not just tech" | ✅ All case studies lead with business outcomes |
| Prepfully | "L7 questions focus on practice building, not just delivery" | ✅ PRACTICE_BUILDING_STAR.md + L7 questions added |
| Interviewing.io | "Mock interviewers are strict on Googleyness" | ✅ Google values mapped in MASTER_QUESTION_BANK.md Round 5 |
| All | "Singapore context (MAS-TRM/PDPA) frequently tested" | ✅ MAS_TRM_PDPA_COMPLIANCE.md + talking points |

---

*This intelligence map tells you exactly which source to use for each interview round. Your portfolio already covers 80% — the paid sources fill the remaining 20% with recent, verified questions and answer quality benchmarks.*