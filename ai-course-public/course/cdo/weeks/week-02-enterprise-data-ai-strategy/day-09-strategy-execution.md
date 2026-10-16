# Lesson 9: Strategy execution

> **Week 2 · Day 9 · 90 min**
> **Deliverable:** A 1-year and 3-year roadmap.

## 🎯 Architect Level
Staff.

## 🧠 Concept

A strategy without an execution plan is a wish. The execution plan has three layers:

1. **1-year roadmap** — the quarters, the milestones, the headcount, the budget, the dependencies.
2. **3-year roadmap** — the year-by-year direction: foundations, scale, differentiation.
3. **Quarterly OKRs** — the 3-5 objectives the team will commit to this quarter.

The most common failure is to **over-commit in the 1-year plan**. The plan has 47 items, the team can deliver 8, and the CEO concludes the team is slow. The right plan has 6-8 items per quarter, 24-32 per year, and the team actually delivers.

The second most common failure is to **under-specify the 3-year plan**. The 3-year plan is directional, but it should still name the year-by-year theme:

- **Year 1: Foundations.** Reliability, governance, semantic layer, KPI standardization, basic ML.
- **Year 2: Scale.** Real-time, ML at production, GenAI in production, multi-BU data products.
- **Year 3: Differentiation.** Agentic AI, data products, new revenue, board-level reporting.

The third most common failure is to **not name the dependencies**. *"We'll deliver the AI portfolio in Q3"* means nothing if you don't say: depends on the data contracts (Q1), the semantic layer (Q2), the feature store (Q2). Dependencies make the plan legible to the CEO.

## 🛠️ Build It

**Spec:** Build a 1-year and 3-year roadmap for a Series-D retailer with $2B revenue, 5 BUs.

**Acceptance:**
- 1-year plan: 4 quarters, 6-8 items per quarter, named dependencies
- 3-year plan: year-by-year theme, 3-5 milestones per year
- Quarterly OKRs: 3-5 objectives with measurable key results
- Headcount and budget per year

**Starter:** Use Story 1 as the reference (the Makro 4-wave replatform is the canonical enterprise data migration shape).

**Solution (1-year, abridged):**

| Q | Theme | Items | Deps |
|---|---|---|---|
| Q1 | Foundations | Data contracts with top 5 sources; semantic layer MVP; FinOps dashboard; exec sponsor committee | Exec sign-off on KPI standards |
| Q2 | Reliability | Incident review process; on-call rotation; observability; data quality scorecards | Q1 contracts |
| Q3 | First wave | Replatform BU1 (highest margin) to lakehouse; deploy first ML model in production | Q2 reliability |
| Q4 | First measurable win | Month-end close <1 day; one AI use case in production with revenue impact | Q3 replatform |

**Solution (3-year, abridged):**

| Year | Theme | Milestones |
|---|---|---|
| Y1 | Foundations | All sources under contract; semantic layer in production; 1 AI use case with revenue; 30% cloud cost reduction |
| Y2 | Scale | All 5 BUs on lakehouse; 5 AI use cases in production; data products shipped to business; CDO in board reporting |
| Y3 | Differentiation | 10+ AI use cases; 1-2 data products externalized; agentic AI in production; CDO at peer of CFO and CTO |

## 🏛️ Architect Notes

- **Trade-off:** Detailed 1-year plan vs. directional 3-year plan. Both. The 1-year is the contract; the 3-year is the direction.
- **Capacity / cost:** A 1-year plan with 6-8 items per quarter is realistic for a 50-person data org. More items = over-commit.
- **When NOT to use:** Don't present a 3-year plan to a board without the 1-year plan underneath. Boards approve the 1-year; they endorse the 3-year.
- **Production checklist:**
  - [ ] 1-year: 4 quarters, 6-8 items per quarter
  - [ ] Dependencies named
  - [ ] 3-year: year-by-year theme
  - [ ] Headcount and budget per year
  - [ ] Quarterly OKRs

## 🌙 Reflect

- Which item in your 1-year plan are you most worried about? What's the risk?
- Which milestone in year 3 would the CEO push to year 2? Pre-write the answer.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 10 — First 90 Days as Head of Data.
