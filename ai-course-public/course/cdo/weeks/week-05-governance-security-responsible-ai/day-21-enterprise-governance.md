# Lesson 21: Enterprise data governance

> **Week 5 · Day 21 · 90 min**
> **Deliverable:** The 6 pillars of data governance + the operating model that runs them.

## 🎯 Architect Level
Staff.

## 🧠 Concept

Data governance is the system of policies, processes, and technologies that ensure data is **findable, accessible, interoperable, reusable, and protected** — the FAIR + P principles. It is not a single team. It is a discipline that runs across the data org, the BUs, and the security org.

The 6 pillars:

| Pillar | What it answers | Tooling | Owner |
|---|---|---|---|
| **1. Catalog** | What data exists? Where? Who owns it? | DataHub, Atlan, Unity Catalog | Data governance |
| **2. Lineage** | Where did this column come from? Where does it flow? | DataHub, OpenLineage, Marquez | Data governance + platform |
| **3. Access (IAM)** | Who can read/write which data, under what conditions? | Unity Catalog, IAM, RBAC + ABAC | Security + governance |
| **4. Quality** | Is this data accurate, complete, fresh, consistent? | Monte Carlo, Great Expectations, Soda | Data engineering |
| **5. Contracts** | What does the source system promise to deliver? | In-house framework, data.mesh, Open Data Contract Standard | Data engineering + source owners |
| **6. Retention + audit** | How long do we keep it? Who accessed it? Why? | Object lifecycle, audit logs, immutability | Security + legal + governance |

The single biggest mistake is to **treat governance as a separate org that blocks**. The right model: governance is embedded in the platform team (catalog, lineage, access, quality) and the source-system owners (contracts). It is not a gate at the end of the pipeline.

The second biggest mistake is to **buy a governance tool and call it done**. A catalog without contracts is a tombstone. A lineage tool without enforcement is a diagram. Governance is a practice, not a product.

The third biggest mistake is to **not name the data owners**. Every dataset must have a named owner (typically a BU head or a domain lead). Without owners, there is no accountability, and accountability is the point of governance.

## 🛠️ Build It

**Spec:** Design the governance operating model for the retailer. Name the 6 pillars, the tooling, the owner, and the cadence.

**Acceptance:**
- 6 pillars, each with 1-2 tools, 1 owner, 1 cadence
- Operating model: who runs what, who decides what
- Data council: who sits on it, what it decides
- 1 paragraph on the trade-off (centralized vs. federated)

**Starter:** Use the hub-and-spoke operating model from Day 7. Governance sits in the hub.

**Solution (governance operating model, abridged):**

| Pillar | Tooling | Owner | Cadence |
|---|---|---|---|
| Catalog | DataHub | Data governance | Weekly new entries |
| Lineage | DataHub + OpenLineage | Data governance + platform | Real-time |
| Access | Unity Catalog + IAM | Security + governance | Real-time |
| Quality | Monte Carlo + dbt tests | Data engineering | Daily scorecard |
| Contracts | Open Data Contract Standard | Source-system owners | Per source change |
| Retention + audit | Object lifecycle + audit logs | Security + legal | Continuous |

**Operating model:** Hub-and-spoke. The hub (data governance team) sets the standards; the spokes (BU data teams) execute. The data council (CDO + 5 BU heads + CISO + legal) meets monthly to set policy and resolve escalations.

**Trade-off:** Centralized vs. federated. Default: hub-and-spoke. Federated works only when the spokes have the engineering maturity.

## 🏛️ Architect Notes

- **Trade-off:** Tool vs. practice. Tools are 30% of governance. Practice is 70%. The CDO who over-invests in tools under-invests in practice.
- **Capacity / cost:** A governance team of 4-6 (catalog, lineage, contracts, audit) for a 50-person data org. Below that, governance is a wish.
- **When NOT to use:** Don't set up a data council without executive sponsorship. A council that the BU heads ignore is worse than no council.
- **Production checklist:**
  - [ ] 6 pillars named
  - [ ] 1-2 tools per pillar
  - [ ] 1 owner per pillar
  - [ ] 1 cadence per pillar
  - [ ] Operating model named
  - [ ] Data council named

## 🌙 Reflect

- Which pillar is the weakest in the company you're interviewing for? Pre-write the answer.
- Who would you put on the data council first? Why?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 22 — Data quality.