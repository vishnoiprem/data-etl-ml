# Lesson 15: Investment prioritization

> **Week 3 · Day 15 · 90 min**
> **Deliverable:** A prioritization framework that cuts a 20-item wish list to 7 funded bets.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The hardest part of the CDO job is not picking what to invest in. It is **picking what to stop**. Every team has a wish list of 20 items. The budget covers 7. The cuts are where the strategy lives.

The prioritization framework has four dimensions, weighted:

| Dimension | Weight | Question |
|---|---|---|
| Strategic value | 30% | Does it move a unit economic lever? |
| Business readiness | 25% | Will the business use it? (Owner, adoption path, change mgmt.) |
| Data readiness | 25% | Do we have the data, the labels, the access? |
| Delivery readiness | 20% | Can we ship in 12 months with current team? |

Score each wish-list item 1-5 on each dimension. Multiply by weight. Sort by total. The top 7 are funded. The next 13 are cut (with reason) or deferred to year 2.

The most common failure is to **fund everything**. "It's all high priority" means nothing is. The point of the exercise is the cuts.

The second most common failure is to **ignore business readiness**. A model that the business won't use is not a return — it's a write-off. Always co-fund with the business.

The third most common failure is to **fund only quick wins**. Quick wins fund strategic bets. A portfolio of only quick wins is a portfolio of low ceiling.

## 🛠️ Build It

**Spec:** Take a 20-item wish list and cut it to 7 funded bets.

**Acceptance:**
- 4-dimension scoring per item
- Weighted total per item
- Top 7 funded, next 13 cut with reason
- 1-2 quick wins, 3-5 strategic bets, 1 moonshot in the funded set

**Starter:** Use the AI portfolio from Day 8 and the commercial patterns from Day 14.

**Solution (prioritization, abridged):**

| Item | Strategic (30%) | Business (25%) | Data (25%) | Delivery (20%) | Total | Decision |
|---|---|---|---|---|---|---|
| Demand forecasting | 5 | 5 | 5 | 5 | 5.00 | **Fund** (quick win) |
| Customer 360 / NBO | 5 | 4 | 3 | 3 | 3.85 | **Fund** (strategic) |
| Dynamic pricing | 4 | 3 | 4 | 4 | 3.75 | **Fund** (strategic) |
| Document intelligence (RAG) | 4 | 4 | 4 | 3 | 3.80 | **Fund** (strategic) |
| Churn / retention | 4 | 4 | 3 | 3 | 3.55 | **Fund** (strategic) |
| Ops forecasting | 3 | 5 | 5 | 5 | 4.40 | **Fund** (quick win) |
| AI customer support | 3 | 3 | 2 | 2 | 2.55 | **Cut** — risk > return at current maturity |
| Autonomous store replenishment | 5 | 2 | 1 | 1 | 2.40 | **Defer** — Y2/Y3, not Y1 |

Plus 12 more cuts. The funded set is 6 strategic + 1 quick win. That's a portfolio with a ceiling.

## 🏛️ Architect Notes

- **Trade-off:** Strategic vs. quick wins. Default: 1-2 quick wins, 3-5 strategic, 1 moonshot. All quick wins = low ceiling. All moonshots = no delivery.
- **Capacity / cost:** A 7-bet portfolio at $5M total budget = ~$700K per bet. Below $500K per bet, the team can't deliver.
- **When NOT to use:** Don't apply the framework to compliance / regulatory bets. Those are non-discretionary and don't compete for the discretionary pool.
- **Production checklist:**
  - [ ] 4-dimension scoring
  - [ ] Weighted total per item
  - [ ] Top 7 funded
  - [ ] Next 13 cut with reason
  - [ ] 1-2 quick wins, 3-5 strategic, 1 moonshot

## 🌙 Reflect

- Which item on your wish list would the CFO cut first? Pre-write the answer.
- Which item did you want to fund that you cut? Why?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Case Study 3 — The $5M Budget Allocation.