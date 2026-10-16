# Lesson 30: Vendor and financial management

> **Week 6 · Day 30 · 90 min**
> **Deliverable:** The vendor strategy + the FinOps framework.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The CDO is responsible for $XM/year in vendor spend (cloud, SaaS, models, data). The CFO will ask: "is every dollar driving ROI? can we cut 20% without losing capability?" The CDO who can't answer is the CDO who loses the budget.

The vendor strategy has 3 layers:

1. **Strategic** — 1-2 vendors per category with deep partnership (preferred pricing, roadmap influence)
2. **Tactical** — 3-5 vendors per category with active contracts
3. **Transactional** — long tail of small contracts, managed by procurement

For data and AI, the categories are: cloud, warehouse/lakehouse, BI, observability, governance, lineage, orchestration, feature store, LLM provider, vector store, eval, guardrail, integration. That's 12+ categories. You can't have 1 strategic vendor in each. Pick the 2-3 that are highest-spend or highest-risk: cloud, warehouse, LLM provider.

The FinOps framework has 3 layers:

1. **Visibility** — dashboards per team, per project, per workload
2. **Optimization** — rightsizing, reserved instances, spot, schedule-based shutdown
3. **Governance** — showback/chargeback, budgets, alerts, approval workflows

The single biggest mistake is to **negotiate only at the start of the contract**. Cloud and SaaS vendors have annual price reductions; the CDO who doesn't re-negotiate annually leaves 20-30% on the table.

The second biggest mistake is to **not have a showback/chargeback model**. A team that doesn't see its bill doesn't optimize its bill. The FinOps dashboard per team is the single biggest cost lever.

The third biggest mistake is to **optimize the wrong workload**. The 80/20 rule: 20% of workloads drive 80% of cost. Find the 20%, optimize the 20%. Don't spread the effort across the long tail.

## 🛠️ Build It

**Spec:** Build the vendor strategy and FinOps framework for a $5M/year data + AI spend at the retailer.

**Acceptance:**
- Vendor strategy: 3 layers, 2-3 strategic vendors named
- FinOps framework: 3 layers, dashboards named
- 3 cost optimization moves (with $ range)
- Vendor re-negotiation cadence
- 1 paragraph on the trade-off (single-vendor discount vs. multi-vendor resilience)

**Starter:** Use the architecture from Week 4. The vendors follow the architecture.

**Solution (vendor + FinOps, abridged):**

**Vendor strategy:**

| Category | Strategic | Tactical |
|---|---|---|
| Cloud | AWS (1 of 3 multi-cloud) | GCP, Azure |
| Warehouse | Snowflake | BigQuery, Redshift (migrating off) |
| LLM | OpenAI + Anthropic (multi-model) | Cohere, OSS |
| Observability | Monte Carlo | Soda, Great Expectations |
| Lineage | DataHub | Unity Catalog |
| BI | Looker | Tableau, PowerBI (migrating off) |

**Strategic vendor terms:** committed spend discount; co-sell; roadmap influence; exec sponsor; quarterly business review.

**FinOps framework:**
- Visibility: dashboard per team, per project, per workload; cost trend; forecast
- Optimization: rightsizing (weekly); reserved instances (annual); spot (batch); schedule-based shutdown (non-prod)
- Governance: showback per BU; chargeback to P&L; budgets; alerts; approval for new workloads

**3 cost optimization moves:**
1. Reserved instances / committed spend: -20-30% on steady-state
2. Rightsizing + schedule shutdown: -10-15% on dev/test
3. Workload consolidation (3 warehouses → 1): -30-40% on storage + compute

**Re-negotiation cadence:** annual, 90 days before renewal; quarterly business review with strategic vendors.

## 🏛️ Architect Notes

- **Trade-off:** Single-vendor discount vs. multi-vendor resilience. Default: multi-vendor for resilience, with committed-spend discounts on the top 1-2.
- **Capacity / cost:** FinOps team of 2-3 for a $5M/year data + AI spend. Below that, the team can't see the spend.
- **When NOT to use:** Don't consolidate to a single cloud for cost. The resilience loss (and the bargaining-chip loss) outweighs the discount.
- **Production checklist:**
  - [ ] Vendor strategy: 3 layers
  - [ ] 2-3 strategic vendors named
  - [ ] FinOps framework: 3 layers
  - [ ] 3 cost optimization moves with $ range
  - [ ] Re-negotiation cadence
  - [ ] Trade-off paragraph

## 🌙 Reflect

- Which vendor is the most over-priced for the role you're interviewing for? Pre-write the answer.
- Which workload is the biggest cost driver? What would you do about it?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Case Study 6 — The 50-Person Transformation.