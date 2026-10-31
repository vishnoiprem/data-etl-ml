# Lesson 12: Data and AI business cases

> **Week 3 · Day 12 · 90 min**
> **Deliverable:** A business case template you can defend in 5 minutes.

## 🎯 Architect Level
Senior.

## 🧠 Concept

A business case is not a slide deck. It is a structured argument with five components:

1. **The decision.** What are you asking for? ($XM, Y people, Z timeline.)
2. **The problem.** What is the cost of inaction? (Baseline + counterfactual.)
3. **The investment.** What are you spending? (Capex + opex + headcount + opportunity cost.)
5. **The return.** What do you get? (Cost-out + revenue-up + risk-down, quantified.)
5. **The risk.** What could go wrong? (Technical, business, organizational.)

The most common failure is **no counterfactual**. "We will save $5M" is half a story. "We will save $5M vs. doing nothing, vs. status quo, vs. a cheaper alternative" is the full story. The CFO buys the counterfactual, not the saving.

The second most common failure is **no baseline**. "We will reduce churn by 2 points" is not a business case if churn is currently 5% and the industry is 3%. The starting point determines whether the claim is credible.

The third most common failure is **no owner**. "The team will deliver X" — which team? When? If it slips, who answers for it? A business case without an owner is a wish.

## 🛠️ Build It

**Spec:** Build a business case for a demand-forecasting ML system at the retailer.

**Acceptance:**
- 5 sections (decision, problem, investment, return, risk)
- Quantified baseline and counterfactual
- ROI with payback period
- Named owner per component
- 1 page total — the CFO must be able to read it in 5 minutes

**Starter:** Start with the counterfactual. Without the ML system, what happens?

**Solution (Demand forecasting business case):**

**The decision.** $1.2M one-time + $400K/year run-rate. 3 data engineers + 2 ML engineers + 1 product manager for 9 months build, then 2 FTEs to run.

**The problem.** The retailer carries ~$XM in fresh and grocery inventory [CONFIRM: specific number]. Stockouts cost ~$Y/year in lost margin; overstocks cost ~$Z/year in markdowns. Current forecasting accuracy (MAPE) is 18% on fresh, 12% on grocery [CONFIRM: get real numbers].

**The investment.**
- Headcount: 6 FTE × 9 months build, 2 FTE steady-state
- Infrastructure: $80K/year (compute, storage, observability)
- Vendor / SaaS: $120K one-time (if buying vs. building)
- Opportunity cost: 6 engineers not on other bets

**The return.**
- Stockout reduction: target -30% × $Y margin = $A/year
- Markdown reduction: target -20% × $Z markdown = $B/year
- Working capital release: target -5% × $X inventory = $C one-time
- Total run-rate: $A + $B = ~$D/year
- Payback: 18-24 months

**The risk.**
- Technical: data quality below threshold → mitigation: data contracts first
- Business: forecast is right but operations can't act → mitigation: change mgmt + pilot
- Organizational: BU refuses to use → mitigation: BU co-ownership of the model

**Owner:** VP Merchandising (business), Head of Data (delivery).

If the CFO reads this in 5 minutes and asks one question, you've passed. If they ask five questions, you haven't.

## 🏛️ Architect Notes

- **Trade-off:** Comprehensiveness vs. brevity. Default to 1 page. If the CFO asks for more, you've earned the right to show page 2.
- **Capacity / cost:** A 1-page business case takes 2-4 hours to build well. The first one takes a day. Build 5 before you need them.
- **When NOT to use:** Don't present a business case without knowing the baseline. "We'll save money" without "we currently spend $X" is a non-starter.
- **Production checklist:**
  - [ ] 5 sections (decision, problem, investment, return, risk)
  - [ ] Baseline with source or [CONFIRM]
  - [ ] Counterfactual named
  - [ ] Quantified ROI with payback
  - [ ] Owner per component
  - [ ] 1 page

## 🌙 Reflect

- Which of your existing projects could be re-cast as a business case with a counterfactual?
- Which number is most likely to be challenged by the CFO? Pre-write the answer.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 13 — Business models and industry economics.