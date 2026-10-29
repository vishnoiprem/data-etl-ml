# Round 3: Case Study — Client Engagement & Delivery
## Google Cloud Data & Analytics Lead — Cloud Consulting

---

### 🎯 Round Overview
| Attribute | Details |
|-----------|---------|
| **Duration** | 60 minutes |
| **Format** | Video + Shared Document (given 24-48hr before or live) |
| **Interviewer** | Practice Lead / Delivery Director / Client Partner |
| **Goal** | Assess consulting delivery: scoping, client management, risk, partner coordination, outcomes |
| **Weight** | High — consulting DNA gate |

---

### 📋 What They're Assessing

| Criteria | Minimum Bar | Strong Signal |
|----------|-------------|---------------|
| **Client Empathy** | Understands business problem | Leads with outcomes, not tech |
| **Structured Approach** | Has a methodology | Uses framework consistently |
| **Scoping & Estimation** | Rough sizing | Phased plan with gates, risk-adjusted |
| **Risk Management** | Identifies risks | Mitigation + contingency per risk |
| **Partner Leverage** | Knows SI model | Defines roles, quality gates, escalation |
| **Measurable Outcomes** | Defines success | KPIs, acceptance criteria, value realization |
| **Communication** | Clear, executive-ready | Adapts to audience (technical vs business) |

---

### 🎯 Client Engagement Framework (Use for Every Case)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CLIENT ENGAGEMENT MODEL                          │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│   DISCOVER   │   DESIGN     │   DELIVER    │      OPERATE          │
├──────────────┼──────────────┼──────────────┼───────────────────────┤
│ • Stakeholder│ • Architecture│ • Sprint    │ • Hypercare           │
│   mapping    │   decision    │   execution │ • Knowledge transfer  │
│ • Current    │   records     │ • Quality   │ • Asset contribution  │
│   state      │ • Migration   │   gates     │ • Managed services    │
│   assessment │   wave plan   │ • Validation│   transition          │
│ • Business   │ • Risk/       │ • Cutover   │ • Continuous          │
│   case &     │   mitigation  │ • UAT       │   optimization        │
│   KPIs       │ • Partner     │ • Go-live   │ • Expansion scoping   │
│ • Scope &    │   model       │             │                       │
│   estimate   │ • Pilot design│             │                       │
└──────────────┴──────────────┴──────────────┴───────────────────────┘
```

---

### 📝 Common Case Scenarios (Prepare All)

---

#### **Case 1: Large-Scale Migration Engagement (Core)**
> **"A manufacturing client wants to migrate their 200 TB Teradata/Oracle estate to BigQuery. They have a 9-month deadline driven by contract expiration. They've engaged a System Integrator (SI) for execution. You're the Google Cloud Lead Architect. How do you run this engagement?"**

**Model Response Structure:**

**1. DISCOVER (Weeks 1-3)**
```
Stakeholders:
  • CTO / VP Data — Business sponsor, timeline owner
  • Enterprise Architect — Standards, governance
  • DBA Team (15) — Current state experts, resistant to change
  • BI Team (20) — 500+ reports, Tableau → Looker migration
  • SI Partner (Accenture, 30 ppl) — Execution capacity
  • Security/Compliance — Data residency, encryption requirements

Current State Assessment:
  • Inventory: 2000+ tables, 500+ ETL jobs, 50+ data domains
  • Complexity: 40% simple, 40% medium (stored procs), 20% complex (nested cursors)
  • Technical Debt: No documentation, 30% unused tables, inconsistent naming
  • Skills Gap: Team knows SQL/Teradata; zero GCP/BigQuery experience

Business Drivers:
  • Contract expires in 9 months (hard deadline)
  • Cost target: 50% reduction vs current $2.4M/yr
  • Analytics enablement: Self-service, near-real-time
  • Compliance: SOC2, data residency (US-only)

KPIs (Success Criteria):
  1. Migration complete: 9 months, <5% scope creep
  2. Data fidelity: 99.99% row/column/aggregate match
  3. Performance: 80% queries faster, 95% <30 sec
  4. Cost: ≤$1.2M/yr (BigQuery + compute)
  5. Adoption: 90% BI reports migrated, 50% users self-serving in 6 mo
  6. Team enablement: 100% DBA/BI certified on GCP
```

**2. DESIGN (Weeks 3-6)**
```
Architecture Decisions (ADRs):
  1. BigQuery (not Spanner/AlloyDB) — Analytics workload, scale, serverless
  2. Partition by event_date + Cluster by customer_id/region — Query patterns
  3. Dataflow for CDC (Datastream) → Near-real-time sync during cutover
  4. Looker for BI — Semantic layer, governance, embedded analytics
  5. Dataplex for governance — Lineage, quality, catalog

Migration Wave Plan (6 Waves, 6 weeks each, 1-week buffer):
  Wave 1 (Pilot): Low-risk, high-value — Sales fact table (10 TB)
  Wave 2: Customer 360 domain (30 TB)
  Wave 3: Supply Chain (40 TB)
  Wave 4: Finance (50 TB) — Strict reconciliation
  Wave 5: HR/Legal (20 TB) — PII, compliance
  Wave 6: Legacy/Archive (50 TB) — Retire 30%

Risk Register (Top 5):
  | Risk | Likelihood | Impact | Mitigation | Contingency |
  |------|------------|--------|------------|-------------|
  | SI delivery velocity | High | High | Joint sprint planning, weekly velocity tracking, buffer waves | Add Google engineers, extend timeline |
  | Data validation failures | Medium | High | Automated diff tooling, statistical profiling, business UAT | Parallel run 4 weeks |
  | DBA resistance/attrition | High | Medium | Early involvement, certification program, retention bonuses | Contractor backfill |
  | Performance regressions | Medium | High | Query tuning sprint per wave, BI Engine, materialized views | Acceptlist for known gaps |
  | Cost overrun | Low | High | Slot reservations, budget alerts, monthly FinOps review | Cap on-demand spend |
```

**3. DELIVER (Weeks 6-36)**
```
Governance Model:
  • Steering Committee (bi-weekly): CTO, VP Data, SI Lead, Google Lead
  • Technical Sync (weekly): Architects, Tech Leads, SI Delivery Lead
  • Sprint Demo (bi-weekly): Business stakeholders, validation results
  • Risk Review (weekly): Risk register update, new risks, decisions

Quality Gates per Wave:
  1. Code Complete → 2. Automated Validation → 3. Business UAT → 4. Performance Benchmark → 5. Security Scan → 6. Go/No-Go

Partner Management:
  • SI owns: Extraction, transformation code, loading, unit testing
  • Google owns: Architecture, target design, validation framework, performance tuning, security review
  • Shared: Integration testing, UAT support, cutover execution
  • Escalation: Technical → Architect → Practice Lead → Director
```

**4. OPERATE (Weeks 36-40+)**
```
Hypercare (4 weeks):
  • Dedicated support rotation (Google + SI)
  • Daily issue triage, SLA: P1=1hr, P2=4hr, P3=1day
  • Performance monitoring dashboards
  • Cost anomaly detection

Knowledge Transfer:
  • Runbooks: Operations, troubleshooting, scaling
  • Training: 3-day BigQuery/Looker bootcamp for DBA/BI teams
  • Certification: Target 100% Associate Data Engineer cert

Asset Contribution:
  • Migration accelerator: Assessment scripts, validation framework, wave template
  • Teradata→BigQuery SQL transpiler rules (custom)
  • Best practices guide: Partitioning, clustering, cost optimization

Expansion Scoping:
  • ML use cases: Demand forecasting, predictive maintenance
  • Real-time: Pub/Sub + Dataflow for IoT sensor data
  • Data Mesh: Domain-oriented ownership, data products
```

---

#### **Case 2: Failed Migration Recovery**
> **"Client's previous migration (by another partner) failed — data quality issues, 6-month delay, business lost trust. They're hesitant to re-engage. How do you approach?"**

**Key Elements:**
- **Trust rebuild:** Acknowledge failure, root cause analysis, transparent plan
- **Quick win:** Pilot 1 high-value, low-risk domain in 4 weeks
- **Governance:** Independent validation, business UAT gates, executive visibility
- **Team:** Embed client SMEs, joint ownership, no "throw over wall"
- **Commercial:** Risk-sharing model, milestone-based payments

---

#### **Case 3: Greenfield Data + AI Platform**
> **"Retail client wants to build a Customer 360 + Real-time Personalization platform on GCP from scratch. Budget: $3M, Timeline: 12 months. They have strong engineering but no cloud experience."**

**Key Elements:**
- **Phased MVP:** Batch → Streaming → ML → Real-time serving
- **Team model:** Google architects + Client engineers (pair programming)
- **Platform approach:** Reusable components, self-service, governance by design
- **Skills transfer:** Certification targets, architecture review board
- **Value milestones:** Month 3 = Unified profile, Month 6 = Batch personalization, Month 12 = Real-time

---

#### **Case 4: Cost Crisis**
> **"Client's GCP data platform costs 3x estimate ($150K vs $50K/month). CFO demands 40% reduction in 60 days. You're brought in to fix."**

**Key Elements:**
- **Rapid diagnosis:** INFORMATION_SCHEMA, slot utilization, storage audit (Days 1-3)
- **Quick wins:** Partition/clustering, materialized views, slot reservations, query rewrites (Days 4-14)
- **Governance:** Quotas, budgets, chargeback labels, monthly reviews (Days 15-30)
- **Culture:** FinOps practice, engineering ownership, optimization sprints (Days 30-60)
- **Stakeholder comms:** Weekly CFO updates, engineering buy-in, celebration of wins

---

### 🎯 Case Study Presentation Format (15 min + 10 min Q&A)

```
SLIDE 1: Title — Client, Challenge, Your Role
SLIDE 2: Business Context — Drivers, Constraints, Success Metrics
SLIDE 3: Current State — Architecture, Pain Points, Gaps
SLIDE 4: Target Architecture — Diagram + Key Decisions (ADRs)
SLIDE 5: Migration/Delivery Plan — Waves, Timeline, Dependencies
SLIDE 6: Risk Register — Top 5 Risks + Mitigations
SLIDE 7: Partner Model — Roles, Quality Gates, Escalation
SLIDE 8: Success Metrics & Value Realization — KPIs, Timeline
SLIDE 9: First 30/60/90 Days — Concrete Actions
SLIDE 10: Questions for Client — Show strategic thinking
```

---

### ✅ Pass Checklist

- [ ] **Leads with business outcomes** — not technology
- [ ] **Uses framework** — Discover/Design/Deliver/Operate visibly
- [ ] **Quantifies everything** — TB, $, weeks, %, people, risks
- [ ] **Addresses people change** — Skills, resistance, enablement
- [ ] **Defines partner model** — Clear roles, gates, escalation
- [ ] **Risk register** — Specific, mitigated, contingent
- [ ] **Measurable KPIs** — Fidelity, performance, cost, adoption, team
- [ ] **Executive presence** — Concise, confident, handles pushback
- [ ] **Asks great questions** — Shows you're already thinking as partner

---

### 🔴 Red Flags

- ❌ Jumps straight to architecture diagram
- ❌ No risk register or "we'll figure it out"
- ❌ "SI handles delivery, we do architecture" (no governance)
- ❌ No validation strategy
- ❌ Ignores team enablement/change management
- ❌ Can't estimate effort/timeline
- ❌ Single-threaded plan (no phases, no pilot)

---

*Next: ROUND_4_LEADERSHIP.md*