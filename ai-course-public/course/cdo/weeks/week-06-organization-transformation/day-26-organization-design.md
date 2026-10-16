# Lesson 26: Organization design

> **Week 6 · Day 26 · 90 min**
> **Deliverable:** The 5 shapes of a data org; the headcount and decision rights for each.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The org shape is the answer to "who does what, who decides what, who owns what." Get the shape wrong and no amount of tooling or process fixes it. Get the shape right and the team will self-organize.

The 5 dominant shapes:

| Shape | Decision rights | Best for | Worst for |
|---|---|---|---|
| **1. Centralized** | One team | <200 people, single BU | Multi-BU, scale |
| **2. Hub-and-spoke** | Center sets standards; spokes execute | Most enterprises (default) | Highly federated orgs |
| **3. Federated (data mesh)** | Domains own their data products | Mature engineering, strong domains | Immature engineering, fragmented |
| **4. Center of Excellence (CoE)** | CoE advises; spokes own | When spokes already exist and need alignment | Greenfield, single BU |
| **5. Embedded** | Data people sit in BU teams | When the BU is the customer | Cross-BU data products |

The single biggest mistake is to **adopt a shape without naming the decision rights**. "We have a data mesh" means nothing if the domains can't say no to the center.

The second biggest mistake is to **start federated before the company is ready**. Data mesh requires strong domain engineering, a working semantic layer, and a governance framework. Most companies don't have any of those at the start. The default should be hub-and-spoke for the first 2-3 years, then move toward federated.

The third biggest mistake is to **underestimate the platform team**. A platform team of 5 people supporting 30+ domain engineers is a ticket queue. The platform team should be 10-15% of the total data org, sized to the complexity of the foundation.

## 🛠️ Build It

**Spec:** Design the org shape for a 50-person data organization at a Series-D retailer. Name the teams, headcount, decision rights.

**Acceptance:**
- 5 shapes compared
- Chosen shape with rationale
- 5-7 teams named with headcount
- Decision rights per team
- Foundation capabilities named
- 1 paragraph on the trade-off

**Starter:** Default: hub-and-spoke. Override only with a reason.

**Solution (50-person org, hub-and-spoke):**

```
CDO
├── Chief of Staff (1)
├── Platform & Reliability (8)         — ingestion, semantic layer, observability, FinOps
├── Governance & Security (4)          — contracts, lineage, IAM, audit
├── Data Engineering (12)              — spoke teams, embedded with BU
├── Analytics & BI (10)                — spoke teams, embedded with BU
├── ML & AI Engineering (10)           — feature store, model serving, RAG/agent platform
├── Product & Program (3)              — intake, prioritization, comms
└── Operations (2)                      — vendor, budget, recruiting
```

**Decision rights:**
- Platform & Reliability: tech choices, SLAs, FinOps targets
- Governance & Security: data contracts, access, retention
- Data Eng / Analytics / ML: delivery commitments to BU
- CDO: portfolio, investment trade-offs, board reporting

**Foundation capabilities:** contracts, lineage, semantic layer, IAM, audit, FinOps — run by Platform + Governance.

## 🏛️ Architect Notes

- **Trade-off:** Centralized vs. federated. Default: hub-and-spoke. Move toward federated when the company has the engineering maturity.
- **Capacity / cost:** Platform team is 10-15% of the total data org. Below that, the platform becomes the bottleneck.
- **When NOT to use:** Don't use data mesh for a Series-A or Series-B company. The engineering culture isn't ready.
- **Production checklist:**
  - [ ] 5 shapes compared
  - [ ] Chosen shape with rationale
  - [ ] 5-7 teams named with headcount
  - [ ] Decision rights per team
  - [ ] Foundation capabilities named
  - [ ] Trade-off paragraph

## 🌙 Reflect

- Which shape fits the company you're interviewing for? Why?
- Which team would the CEO question? Pre-write the answer.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 27 — People leadership.