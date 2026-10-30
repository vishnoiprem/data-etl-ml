# Presales Methodology - Discovery to Delivery
## Structured Approach for Google Cloud Data & Analytics Engagements

---

## 🎯 Presales Philosophy

> **"Presales isn't selling - it's co-discovering the right solution and proving we can deliver it."**

### Core Principles
| Principle | Practice |
|-----------|----------|
| **Outcome-First** | Start with customer business outcomes, not GCP services |
| **Evidence-Based** | Every claim backed by reference, pilot, or calculation |
| **Risk-Transparent** | Lead with risks and mitigations, not just benefits |
| **Partner-Inclusive** | SI as co-architect, not subcontractor |
| **Delivery-Aligned** | What we sell = what we deliver (no handoff surprises) |

---

## 📋 3-Phase Discovery Framework

### Phase 1: Discovery (Week 1-2) - "Understand Before Solve"

#### Stakeholder Mapping
```
STAKEHOLDER MAP: [Customer]

| Role | Name | Influence | Interest | Pain Points | Success Metrics | Relationship |
|------|------|-----------|----------|-------------|-----------------|--------------|
| Executive Sponsor | | High | High | | | |
| Technical Lead | | High | High | | | |
| Data Engineering Mgr | | Med | High | | | |
| Business Analyst | | Low | High | | | |
| Security/Compliance | | High | Med | | | |
| Procurement/Legal | | Med | Low | | | |
| End Users | | Low | High | | | |

RELATIONSHIP STATUS: 🟢 Champion  🟡 Neutral  🟠 Skeptic  🔴 Blocker
```

#### Current State Assessment
```
CURRENT STATE ASSESSMENT CHECKLIST

DATA LANDSCAPE:
□ Data sources cataloged (DBs, warehouses, lakes, SaaS, files)
□ Volume: _____ TB total, _____ TB/day ingest, _____ TB/query
□ Velocity: Batch / Micro-batch / Streaming / Real-time
□ Variety: Structured _____% / Semi-structured _____% / Unstructured _____%
□ Quality: Known issues _______________

TECHNOLOGY STACK:
□ On-prem: Teradata _____ / Oracle _____ / Hadoop _____ / SQL Server _____ / Other _____
□ Cloud: AWS _____ / Azure _____ / GCP _____ / Multi-cloud _____
□ Tools: ETL _____ / BI _____ / ML _____ / Orchestration _____ / Catalog _____

WORKLOADS:
□ ETL/ELT: _____ jobs, _____ TB/day, SLA _____
□ BI/Reporting: _____ concurrent users, _____ dashboards, refresh _____
□ ML/AI: _____ models, _____ predictions/day, training freq _____
□ Ad-hoc: _____ analysts, _____ queries/day, avg runtime _____

PAIN POINTS (Ranked):
1. _______________ (Impact: $_____/yr, Urgency: _____)
2. _______________ (Impact: $_____/yr, Urgency: _____)
3. _______________ (Impact: $_____/yr, Urgency: _____)

SUCCESS METRICS (Customer-Defined):
□ Cost reduction: _____% or $_____/yr
□ Performance: _____x faster, _____ min → _____ sec
□ Scale: _____x concurrent, _____ TB → _____ PB
□ Agility: _____ weeks → _____ days for new use case
□ Compliance: _____ audit findings → 0
□ Innovation: _____ ML use cases enabled
```

#### Art of Possible Workshop (2 hours)
```
AGENDA: ART OF POSSIBLE (2 hours)

1. GCP Data Platform Vision (20 min)
   - BigQuery: Serverless, petabyte-scale, ML-built-in
   - Dataflow: Unified batch/stream, exactly-once
   - Dataplex: Governance at metadata level
   - Vertex AI: Unified ML platform

2. Industry-Specific Art of Possible (30 min)
   - [FinServ]: Real-time fraud, regulatory reporting, customer 360
   - [Retail]: Inventory optimization, personalization, supply chain
   - [Telco]: Network analytics, churn prediction, edge processing
   - [Healthcare]: Patient 360, clinical trials, FHIR interoperability

3. Customer Use Case Mapping (40 min)
   | Customer Pain | GCP Capability | Quick Win? | Strategic? | Effort |
   |---------------|----------------|------------|------------|--------|
   |               |                |            |            |        |

4. Prioritization & Next Steps (30 min)
   - Quick wins (4-8 weeks): _______________
   - Strategic initiatives (3-6 months): _______________
   - Transformation (6-18 months): _______________
```

---

### Phase 2: Sizing & Solution Design (Week 2-3)

#### Workload Classification Matrix
```
WORKLOAD CLASSIFICATION

| Workload | Type | Volume | Complexity | Custom Code | Integrations | Compliance | Priority |
|----------|------|--------|------------|-------------|--------------|------------|----------|
| EDW Migration | Migration | 100 TB | High | 500 SPs | 10 systems | PCI | P0 |
| Real-time Analytics | Modernization | 50K eps | Med | 50 transforms | 3 systems | - | P1 |
| ML Feature Store | New Build | 10 TB | High | Custom | 5 systems | GDPR | P2 |
| Ad-hoc Analytics | Migration | 5 TB | Low | 200 views | 2 systems | - | P3 |
```

#### Effort Estimation Model
```
EFFORT ESTIMATION (Person-Weeks)

BASE EFFORT DRIVERS:
├── Data Volume (TB)
│   ├── <10: 1x
│   ├── 10-100: 2x
│   ├── 100-500: 3x
│   └── >500: 5x
├── Complexity
│   ├── Low (lift-shift): 1x
│   ├── Medium (refactor): 2x
│   ├── High (re-architect): 3x
│   └── Custom SP/UDF translation: +50% per 100
├── Integrations (per system): +0.5x
├── Compliance (per framework): +0.5x
└── Team Ramp (if new): +1.5x

TEAM MODEL:
├── Google: Architecture (10%), Quality Gates (15%), Knowledge Transfer (15%)
├── Partner: Delivery (60%), Documentation (10%)
└── Customer: SME (20%), UAT (10%), Cutover (10%)

EXAMPLE: 100TB Teradata, High Complexity, 5 Integrations, PCI
Base: 20 pw × 3x (volume) × 3x (complexity) × 1.5x (integrations) × 1.5x (PCI) = 405 pw
Team: 4 Google + 8 Partner + 4 Customer = 16 FTE
Duration: 405 / 16 = ~25 weeks (6 months)
```

#### Risk Assessment
```
RISK REGISTER

| Risk | Likelihood | Impact | Score | Mitigation | Owner |
|------|------------|--------|-------|------------|-------|
| Custom UDFs not portable | High | High | 9 | Inventory + rewrite plan in Assess | Google Arch |
| Data quality worse than profiled | Med | High | 6 | Pilot validates, dual-write reconciliation | Partner PM |
| Customer SME availability | High | Med | 6 | Dedicated 50% SME in contract | Customer |
| SI resource gaps | Med | High | 6 | Certified names in SoW, bench clause | Google PDM |
| Regulatory approval delays | Low | High | 3 | Early engagement, parallel prep | Legal |
| Cost overrun | Med | Med | 4 | Fixed-price milestones, monthly reviews | All |
```

---

### Phase 3: Validation & Proposal (Week 3-4)

#### Pilot/POC Scope
```
PILOT SCOPE DEFINITION

OBJECTIVE: Validate technical approach, performance, cost for [Top 3 Workloads]

SCOPE:
├── Workload 1: _______________ (Reason: _______________)
├── Workload 2: _______________ (Reason: _______________)
├── Workload 3: _______________ (Reason: _______________)

SUCCESS CRITERIA (All Must Pass):
□ Data parity: Row counts ±0.1%, checksums match
□ Performance: Query latency ≤ on-prem (or ≤ SLA)
□ Cost: Per-query cost within model (±20%)
□ Functionality: All required features work
□ Security: VPC-SC, CMEK, RLS validated
□ Operational: Monitoring, alerting, runbooks work

TIMELINE: 4 weeks
├── Week 1: Environment setup, data ingest
├── Week 2-3: Pipeline build, validation
├── Week 4: Performance tuning, stakeholder demo

RESOURCES: 1 Google Arch + 2 Partner Eng + 1 Customer SME
BUDGET: $_____ (Google credits + Partner T&M)
GO/NO-GO GATE: All success criteria + Customer sign-off
```

#### TCO Model (3-Year)
```
TOTAL COST OF OWNERSHIP: ON-PREM vs GCP (3 Years)

ON-PREM (Current State):
├── Hardware (Depreciation 5-yr): $_____/yr × 3 = $_____
├── Software Licenses: $_____/yr × 3 = $_____
├── Support Contracts: $_____/yr × 3 = $_____
├── Facilities (Power/Cooling/Rack): $_____/yr × 3 = $_____
├── FTE Operations (5 FTE × $150k): $750k/yr × 3 = $2.25M
├── Downtime Cost (est.): $_____/yr × 3 = $_____
├── Refresh Cycles (Year 3): $_____
└── TOTAL ON-PREM: $_____

GCP (Target State):
├── BigQuery (Storage + Compute): $_____/mo × 36 = $_____
├── Dataflow: $_____/mo × 36 = $_____
├── Dataproc: $_____/mo × 36 = $_____
├── Composer: $_____/mo × 36 = $_____
├── Storage (GCS): $_____/mo × 36 = $_____
├── Network/Egress: $_____/mo × 36 = $_____
├── Support (Premium): $_____/yr × 3 = $_____
├── Professional Services (Migration): $_____ (one-time)
├── Professional Services (Ongoing): $_____/yr × 3 = $_____
└── TOTAL GCP: $_____

SAVINGS: $_____ (____% reduction)
PAYBACK: _____ months
NPV (3yr, 8%): $_____

SENSITIVITY:
├── +20% data growth: $_____ savings
├── -20% data growth: $_____ savings
├── Reserved slots (3yr): Additional $_____ savings
└── Spot VMs (Dataproc): Additional $_____ savings
```

#### Proposal Structure
```
PROPOSAL OUTLINE

1. EXECUTIVE SUMMARY (1 page)
   - Business problem, recommended solution, investment, ROI, timeline

2. CURRENT STATE & PAIN POINTS (2 pages)
   - Assessment findings, quantified impact, risk of inaction

3. TARGET ARCHITECTURE (3 pages)
   - Diagram, design principles, GCP services, security/governance

4. MIGRATION APPROACH (3 pages)
   - 4-phase plan, timeline, milestones, risks, mitigations

5. TEAM & DELIVERY MODEL (2 pages)
   - Org chart, RACI, Google/Partner/Customer roles, governance

6. COMMERCIAL (2 pages)
   - TCO, pricing model (T&M / Fixed / Hybrid), payment schedule
   - Assumptions, exclusions, change control

7. SUCCESS METRICS & GOVERNANCE (1 page)
   - KPIs, reporting cadence, escalation path, quality gates

8. APPENDICES
   - Detailed workload assessment, pilot results, reference customers
   - Team bios, certifications, case studies
   - Security/compliance mappings, insurance, MSA terms
```

---

## 💰 Pricing Models

### Time & Materials (Default for Discovery/Pilot)
- **Google**: Architect $300/hr, Engineer $200/hr, PM $250/hr
- **Partner**: Per certified resource rate card
- **Cap**: Not-to-exceed with monthly ceilings
- **Best for**: Uncertain scope, exploration, pilot

### Fixed-Price Milestones (Migration Execution)
```
MILESTONE PAYMENT SCHEDULE

| Milestone | Deliverable | % of Fee | Payment Trigger |
|-----------|-------------|----------|-----------------|
| M1: Assess Complete | Assessment report, risk register, plan | 15% | Sign-off |
| M2: Pilot Complete | Pilot validation, Go/No-Go | 15% | Sign-off |
| M3: Historical Load | 100% data migrated, validated | 25% | Automated validation pass |
| M4: CDC Sync Stable | 14 days dual-write <0.1% diff | 20% | Monitoring dashboard |
| M5: Cutover | Production on GCP, on-prem read-only | 15% | Customer acceptance |
| M6: Hypercare Complete | 30 days stable, knowledge transfer | 10% | Sign-off |
```

### Outcome-Based (Strategic Engagements)
- **Base fee** (covers costs) + **Success bonus** (tied to customer metrics)
- Example: Base $500k + $200k if "query latency <5s for 95% queries" + $100k if "cost < $X/mo"
- Aligns incentives, requires mature measurement

---

## 📊 Presales Metrics (Track Monthly)
| Metric | Target |
|--------|--------|
| **Discovery → Pilot conversion** | >60% |
| **Pilot → Deal conversion** | >75% |
| **Average deal size** | >$500k |
| **Sales cycle (qualified → close)** | <90 days |
| **Estimation accuracy** | ±15% actual vs estimate |
| **Scope creep (post-contract)** | <10% of contract value |
| **Reference customer willingness** | >80% |

---

## 🎯 Interview Talking Points

### "How do you estimate customer outcomes accurately?"
1. **Discovery Framework**: Stakeholder map, current state, pain quantification, success metrics
2. **Sizing Model**: Volume × Complexity × Integrations × Compliance × Team ramp
3. **Validation**: Pilot with success criteria, reference customers, TCO model
4. **Risk Buffers**: 20% for unknown, fixed-price milestones, monthly reviews
5. **Result**: "62% win rate, ±15% estimation accuracy, $12M qualified pipeline"

### "Walk me through a presales-to-delivery success story"
→ Use STAR story from star_answers.md (Phased alternative, quick win, data-driven pushback, $3.2M deal)

---

*This methodology has closed $12M+ pipeline with 62% win rate. Adapt phases to deal size but keep the principles.*