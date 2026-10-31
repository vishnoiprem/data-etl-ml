# Lesson 7: Enterprise Data Operating Model

> **Week 2 · Day 7 · 90 min**
> **Deliverable:** An org diagram for the operating model.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The operating model answers: who decides what, who builds what, who owns what. The three dominant shapes are:

| Model | Decision rights | Build | Own | When it works |
|---|---|---|---|---|
| **Centralized** | One team | One team | One team | Company is too small to support multiple data teams |
| **Hub-and-spoke** | Center sets standards; spokes execute | Spokes | Spokes (data); Center (foundation) | Most enterprises — recommended default |
| **Federated / Data mesh** | Domains own their data products | Domains | Domains | Large, mature companies with strong domain engineering culture |
| **Center of Excellence (CoE)** | CoE sets standards, advises | Spokes | Spokes | When the spokes already exist and you need alignment without disruption |

The single biggest mistake is to **adopt a model without naming the decision rights**. *"We have a data mesh"* means nothing if the domains can't actually say no to a request from the center.

The second biggest mistake is to **start federated before the company is ready**. Data mesh requires strong domain engineering, a working semantic layer, and a governance framework. Most companies don't have any of those at the start. The default should be hub-and-spoke for the first 2-3 years, then move toward federated.

The third biggest mistake is to **underestimate the platform team**. A platform team of 5 people supporting 30+ domain engineers is not a platform team — it's a ticket queue. The platform team should be sized to the complexity of the foundation: contracts, lineage, semantic layer, governance, security, FinOps. Plan for 10-15% of the total data org.

## 🛠️ Build It

**Spec:** Draw the org diagram for a 50-person data organization at a Series-D retailer. Justify the shape.

**Acceptance:**
- Names every team (platform, governance, analytics, ML, AI)
- Names the headcount per team
- Names the decision rights
- Names the foundation capabilities (contracts, lineage, semantic layer, security, FinOps)
- 0 jargon, 0 hand-waving

**Starter:** Use the hub-and-spoke model as the default. Override only with a reason.

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
- Platform & Reliability: technology choices, SLAs, FinOps targets
- Governance & Security: data contracts, access policies, retention
- Data Engineering / Analytics / ML: delivery commitments to BU
- CDO: portfolio, investment trade-offs, board reporting

**Foundation capabilities (run by Platform + Governance):**
- Data contracts (every source system)
- Lineage and observability
- Semantic layer (the single source of metric truth)
- IAM and access control
- Audit and compliance
- FinOps dashboard per team

## 🏛️ Architect Notes

- **Trade-off:** Centralized vs. federated. Default: hub-and-spoke. Move toward federated when the company has the engineering maturity.
- **Capacity / cost:** Platform team is 10-15% of the total data org. Below that, the platform becomes a bottleneck.
- **When NOT to use:** Don't use data mesh for a Series-A or Series-B company. The engineering culture isn't ready.
- **Production checklist:**
  - [ ] Every team has a name and a headcount
  - [ ] Decision rights are explicit
  - [ ] Foundation capabilities are named
  - [ ] CDO is at the same level as CFO and CTO (peer, not report)

## 🌙 Reflect

- Which of the 5 teams would the CEO question? Pre-write the answer.
- What headcount would you cut in a 30% budget reduction? (See Q47.)
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 8 — Enterprise AI Strategy.
