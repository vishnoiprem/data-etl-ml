# Lesson 8: Enterprise AI strategy

> **Week 2 · Day 8 · 90 min**
> **Deliverable:** An AI portfolio — 5-7 use cases with value, readiness, and decision.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The AI strategy is a portfolio, not a roadmap. The portfolio is the *set of bets* the company is making; the roadmap is the *sequence* in which they're delivered. Confuse the two and you'll either over-commit (you'll never deliver the portfolio) or under-deliver (you'll never start the next bet).

The portfolio has 5-7 use cases. Fewer than 5 means you're not taking the AI opportunity seriously. More than 7 means you're not making hard choices. The use cases span three categories:

1. **Traditional ML** — forecasting, classification, recommendation, churn. Where the data is structured, the model is interpretable, the business case is direct.
2. **GenAI** — content generation, summarization, document intelligence, semantic search. Where the data is unstructured, the model is probabilistic, the business case requires guardrails.
3. **Agentic AI** — multi-step workflows, tool use, autonomous decisioning. Where the value is in orchestration, not generation. Highest upside, highest risk.

For each use case, score four dimensions:

| Dimension | Question | Scale |
|---|---|---|
| Business value | What's the $ or strategic upside? | $ / strategic |
| Data readiness | Do we have the data, the labels, the access? | ready / partial / not ready |
| Build complexity | What's the engineering effort? | weeks / months / quarters |
| Risk profile | What's the worst case if it's wrong? | low / medium / high |

A useful portfolio has 1-2 quick wins (ready + low risk + weeks), 2-3 strategic bets (partial + high value), and 1-2 moonshots (not ready + strategic). The quick wins fund the strategic bets. The strategic bets fund the moonshots.

## 🛠️ Build It

**Spec:** Build a 5-7 use case AI portfolio for a Series-D retailer. Score each. Justify the cuts.

**Acceptance:**
- 5-7 use cases
- Each scored on value, readiness, complexity, risk
- At least 1 quick win, 2 strategic bets, 1 moonshot
- 1-2 use cases explicitly cut (with reason)

**Starter:** Use the candidate's Makro / Lazada domain expertise.

**Solution (5 use cases, abridged):**

| Use case | Category | Value | Readiness | Complexity | Risk | Decision |
|---|---|---|---|---|---|---|
| Demand forecasting | ML | $XM margin | Ready | Weeks | Low | **Invest** (quick win) |
| Customer 360 + next-best-offer | ML | +2-5% retention | Partial | Months | Medium | **Invest** (strategic) |
| Dynamic pricing | ML | +1-3% margin | Partial | Months | Medium | **Invest** (strategic) |
| Document intelligence (RAG) | GenAI | −50% ops cost | Ready | Quarters | Medium | **Invest** (strategic) |
| AI customer support | GenAI | −30% ticket cost | Partial | Quarters | High | **Cut** — automation risk, accuracy <80% |
| Autonomous store replenishment | Agentic | $X stockout reduction | Not ready | Year+ | High | **Defer** — wait for foundation |

## 🏛️ Architect Notes

- **Trade-off:** 5 use cases vs. 20. 5. Force the cuts. The cuts are where the strategy lives.
- **Capacity / cost:** A 5-7 use case portfolio can be resourced by a 10-15 person AI team (ML + data eng + MLOps). More use cases need more headcount.
- **When NOT to use:** Don't start with agentic AI as your first bet. Foundation first (data + ML), then GenAI, then agentic.
- **Production checklist:**
  - [ ] 5-7 use cases
  - [ ] Each scored on the 4 dimensions
  - [ ] At least 1 quick win, 2 strategic, 1 moonshot
  - [ ] 1-2 use cases explicitly cut
  - [ ] The cuts have a reason

## 🌙 Reflect

- Which use case did you want to keep that you cut? Why?
- Which moonshot would the CEO push to start sooner? Pre-write the answer.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 9 — Strategy Execution.
