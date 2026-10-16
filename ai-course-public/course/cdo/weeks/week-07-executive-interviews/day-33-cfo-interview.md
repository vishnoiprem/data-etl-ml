# Lesson 33: CFO interview

> **Week 7 · Day 33 · 90 min**
> **Deliverable:** The 5 most-asked CFO questions, each with a 60-second answer skeleton.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The CFO interview is a numbers interview. The CFO is asking: "will this person spend my money like it's their own?" The bar is financial discipline, ROI thinking, and cost awareness.

The 5 most-asked CFO questions:

1. **"What's the ROI on your $5M data and AI budget?"** (Quantified, with payback.)
2. **"Where can you cut 20% without losing capability?"** (Named cuts, with reasons.)
3. **"How do you measure the value of data quality?"** (The framework, with examples.)
4. **"What's the cost of a bad data decision?"** (Concrete example with $.)
5. **"How do you prioritize investment across the portfolio?"** (Framework, not gut feel.)

The single biggest mistake is to **answer in narrative, not numbers**. "We expect significant value from our AI investments" is not an answer. "We expect $6.5-16M run-rate, 9-15 month payback" is an answer.

The second biggest mistake is to **not name the cuts**. The CFO is allergic to "everything is high priority." A budget without cuts is a budget that will balloon.

The third biggest mistake is to **not have a cost-of-bad-data story**. "We have a data quality scorecard" is a tool. "Last quarter, a bad customer ID cost us $X in support tickets and lost NRR" is a story. The CFO remembers the story.

## 🛠️ Build It

**Spec:** Build the 5 CFO answers, each in 60 seconds, each with a number, a cut, and a follow-up defense.

**Acceptance:**
- 5 questions, 5 answers
- Each answer: 60 seconds, named number, named cut, named framework
- Each answer: 1 follow-up defense (60 seconds)
- 1 paragraph on the trade-off (precision vs. humility)

**Starter:** Use Day 12's business case template. Use Day 15's prioritization. Use Day 30's FinOps.

**Solution (5 CFO answers, abridged):**

**Q1: What's the ROI on your $5M budget?**
> "$5M budget, $6.5-16M run-rate, 9-15 month payback. Risk-adjusted at 60% realization: $4-10M. The portfolio is 2 quick wins, 4 strategic, 1 deferred. Quick wins fund strategic; strategic funds moonshots. Working capital release: $1-3M one-time."

**Q2: Where can you cut 20%?**
> "$1M cuts. The list: AI customer support (defer to Y2 — risk > return at current maturity); autonomous store replenishment (defer to Y3 — data not ready); 2 of 3 warehouses (consolidate — saves $X); 4 legacy BI tools (migrate — saves $Y). The remaining $4M still delivers $5-12M run-rate."

**Q3: How do you measure data quality value?**
> "Three numbers: cost of bad data (re-work, support tickets, lost NRR); cost of prevention (DQ tooling, contracts, governance); ratio. Target: prevention is <30% of bad-data cost. Example: a bad customer ID at $X cost in support tickets; a contract on the source system costs $Y/year to maintain. 5× ROI on prevention."

**Q4: What's the cost of a bad data decision?**
> "Concrete example: the Q2 margin incident. A semantic layer change wasn't propagated to the board deck. The board saw a 2-point gap. The cost: a re-statement, a 14-day investigation, a 2-week delay on a capital raise. The fix: pre-board validation, DQ scorecard, sign-off. The cost of the fix: $X/year. The cost of the incident: $XM. 50× ROI on the fix."

**Q5: How do you prioritize investment?**
> "Four-dimension framework: strategic value (30%), business readiness (25%), data readiness (25%), delivery readiness (20%). Score 1-5 per dimension, weighted total, sort. Top 7 funded, next 13 cut with reason. The cuts are where the strategy lives."

**Trade-off (precision vs. humility):** Give a number with a range, not a point estimate. "$6.5-16M" is credible. "$10M" is not. The CFO respects the range; the CFO disrespects the point estimate.

## 🏛️ Architect Notes

- **Trade-off:** ROI precision vs. strategic value. Some investments don't have a clean ROI (data quality, governance). The CFO who demands ROI on everything under-invests in foundations. The CDO has to defend the "no clean ROI" investments.
- **Capacity / cost:** 5 answers × 60 seconds = 5 minutes. The numbers are what get you the offer.
- **When NOT to use:** Don't quote numbers you can't defend. "$10M in year 1" is a trap. The CFO will dig. Use ranges and [CONFIRM] markers.
- **Production checklist:**
  - [ ] 5 questions, 5 answers
  - [ ] 60 seconds per answer
  - [ ] Named number with range
  - [ ] Named cut
  - [ ] Named framework
  - [ ] 1 follow-up defense per answer

## 🌙 Reflect

- Which answer is your weakest? Re-record.
- Which number would the CFO in your actual interview challenge first? Pre-write.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 34 — Board Communication.