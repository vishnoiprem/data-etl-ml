# Lesson 17: Cloud migration and multi-cloud

> **Week 4 · Day 17 · 90 min**
> **Deliverable:** A migration playbook with the 6 R's, phases, and risk per phase.

## 🎯 Architect Level
Staff.

## 🧠 Concept

Cloud migration is not "lift and shift." The 6 R's are the menu:

| R | What it is | When to use | Risk |
|---|---|---|---|
| **Rehost** | Lift and shift to new infra | Quick exit from data center | Low short-term, high long-term |
| **Replatform** | Move with minor changes (managed DB, PaaS) | 80% of typical migrations | Medium |
| **Refactor** | Re-architect for cloud-native | When the app can't scale otherwise | High |
| **Repurchase** | Move to SaaS (e.g., Snowflake, Salesforce) | When the legacy is unfixable | Medium |
| **Retire** | Decommission the workload | When the workload is dead | Low |
| **Retain** | Keep on-prem for now | When the migration ROI is negative | Low (defer) |

The most common failure is to **rehost everything**. "We moved to the cloud" = "we have the same architecture with bigger bills." The CFO will see the bill; the CEO will see the lack of elasticity. Rehost buys time, not transformation.

The second most common failure is to **refactor everything**. "We re-architected the monolith into 47 microservices" = "we shipped nothing for 18 months." Refactor is high risk; it should be <20% of the portfolio.

The right portfolio is **70% replatform, 20% repurchase, 10% refactor**. The replatform gets you 80% of the value at 30% of the risk. The repurchase is where the SaaS win lives. The refactor is reserved for the workload that can't scale.

For data specifically, the migration shape is:
1. **Land** the raw data in object storage (S3, GCS, ADLS)
2. **Organize** with an open table format (Iceberg, Delta)
3. **Transform** with dbt (SQL) or Spark (heavy)
4. **Serve** via warehouse (Snowflake, BigQuery) or directly via lakehouse
5. **Govern** with contracts, lineage, IAM, audit

This is the "lakehouse" pattern. It's not the only one, but it's the dominant one in 2024-2026.

## 🛠️ Build It

**Spec:** Build a 3-year migration plan for a retailer with 3 warehouses (Snowflake, BigQuery, Redshift), 5 BUs, and a goal of "one platform."

**Acceptance:**
- 6 R's applied to each workload
- Phased plan with named milestones
- Risk per phase
- Cost trajectory (current → target)
- 1-2 "retain" decisions justified

**Starter:** Inventory the workloads by BU. Tag each with the 6 R's.

**Solution (3-year migration, abridged):**

| Phase | Theme | Workloads | R | Risk |
|---|---|---|---|---|
| Y1 Q1-Q2 | Land | All 3 warehouses → 1 object storage + Iceberg | Replatform | Medium |
| Y1 Q3-Q4 | Organize | Top 20 datasets on the new table format | Replatform | Low |
| Y2 Q1-Q2 | Replatform | Snowflake + BigQuery workloads → warehouse | Replatform / Repurchase | Medium |
| Y2 Q3-Q4 | Repurchase | Redshift workloads → BigQuery or Snowflake | Repurchase | Medium |
| Y3 Q1-Q2 | Refactor | 2 legacy monoliths → decomposed services | Refactor | High |
| Y3 Q3-Q4 | Retire | 12 legacy systems | Retire | Low |
| Retain | On-prem SAP for finance | Y2-Q3 reassess | Retain | Low |

Cost trajectory: $X (3 warehouses) → $0.7X (1 platform) in 18 months. [CONFIRM: get real cost numbers from the interviewer.]

## 🏛️ Architect Notes

- **Trade-off:** Speed vs. transformation. Rehost is fast but expensive long-term. Refactor is slow and risky. Default: replatform 70%, repurchase 20%, refactor 10%.
- **Capacity / cost:** A 3-year migration costs $XM in infra + 5-10 FTE for the program. Below that, the migration slips.
- **When NOT to use:** Don't migrate during a re-org. The org change absorbs all the oxygen. Sequence: org stable → migrate.
- **Production checklist:**
  - [ ] 6 R's applied per workload
  - [ ] Phased plan with milestones
  - [ ] Risk per phase
  - [ ] Cost trajectory
  - [ ] Retain decisions justified

## 🌙 Reflect

- Which R is most over-used in your industry? Pre-write the answer.
- Which workload would you retain? Why?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 18 — Reliability and scalability.