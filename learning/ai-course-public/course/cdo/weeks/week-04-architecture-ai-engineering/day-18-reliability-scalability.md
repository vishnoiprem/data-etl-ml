# Lesson 18: Reliability and scalability

> **Week 4 · Day 18 · 90 min**
> **Deliverable:** SLAs, SLOs, and error budgets for each layer of the platform.

## 🎯 Architect Level
Staff.

## 🧠 Concept

Reliability is not a feature. It is a property of the architecture. The CDO is on the hook for it.

The three concepts to internalize:

| Concept | Definition | Example |
|---|---|---|
| **SLA** (Service Level Agreement) | The contract with the customer (business) | "Ingestion will be available 99.9% of the month" |
| **SLO** (Service Level Objective) | The internal target the team commits to | "Ingestion availability target: 99.95%" |
| **Error budget** | The allowed failure (1 - SLO) | 0.05% of the month = 21 minutes/month of downtime |

The SLO should be stricter than the SLA. The error budget is the freedom the team has to take risks. When the error budget is burned, the team shifts from features to reliability.

For each layer, you must name:

| Layer | SLA | SLO | Error budget |
|---|---|---|---|
| Ingestion | 99.9% monthly | 99.95% | 21 min/month |
| Storage | 99.99% durability | 99.999999% (11 9s) | Provider-managed |
| Transformation | 99.5% (data quality) | 99.9% | 0.1% bad rows |
| Semantic | 99.9% (query availability) | 99.95% | 21 min/month |
| Consumption | 99.9% (BI availability) | 99.95% | 21 min/month |

The single biggest mistake is to **not measure the SLA**. A team that doesn't measure is a team that doesn't know.

The second biggest mistake is to **set the SLA at 100%**. 100% is unachievable and burns the team out. Set the SLA at the level the business needs, not the level the business wishes for.

The third biggest mistake is to **not have an on-call rotation**. Reliability is not a job, it's a practice. The team that gets paged at 3am is the team that builds reliable systems.

## 🛠️ Build It

**Spec:** For the 5-layer platform, name the SLA, SLO, and error budget per layer. Name the on-call rotation shape.

**Acceptance:**
- 5 layers × SLA + SLO + error budget
- On-call rotation: who, when, escalation
- Observability stack named
- Incident review process named

**Starter:** Start from the business need. "How much downtime can the business tolerate?" Work backward to the SLO.

**Solution (reliability plan, abridged):**

| Layer | SLA | SLO | Error budget | On-call |
|---|---|---|---|---|
| Ingestion | 99.9% | 99.95% | 21 min/month | Data eng on-call (24/7) |
| Storage | 99.99% durability | 99.999999% | Provider-managed | n/a |
| Transformation | 99.5% data quality | 99.9% | 0.1% bad rows | Data eng on-call |
| Semantic | 99.9% query | 99.95% | 21 min/month | Platform on-call |
| Consumption | 99.9% BI | 99.95% | 21 min/month | Platform on-call |

**On-call rotation:** 8 people, 1 week on, 8-week cycle. Pager rotation. Incident commander = most senior on-call. Post-incident review within 48h. Blameless. Action items with owners.

**Observability stack:** OpenTelemetry traces, Monte Carlo for data quality, DataHub for lineage, custom dashboards for SLIs.

## 🏛️ Architect Notes

- **Trade-off:** Cost vs. reliability. 99.99% costs 10× 99.9%. Default: 99.9% SLA, 99.95% SLO, measure the gap.
- **Capacity / cost:** On-call rotations need 8+ people to be sustainable. Below that, burnout. Pay on-call stipends.
- **When NOT to use:** Don't set SLAs you can't measure. A team that promises 99.99% but measures 99.5% is a team that's lost trust.
- **Production checklist:**
  - [ ] 5 layers × SLA + SLO + error budget
  - [ ] On-call rotation named
  - [ ] Observability stack named
  - [ ] Incident review process named
  - [ ] Blameless culture stated

## 🌙 Reflect

- Which SLA is most likely to be breached in year 1? Pre-write the answer.
- What would you do if the error budget is burned by month 6?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 19 — ML architecture.