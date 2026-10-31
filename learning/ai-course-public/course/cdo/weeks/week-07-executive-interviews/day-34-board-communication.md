# Lesson 34: Board communication

> **Week 7 · Day 34 · 90 min**
> **Deliverable:** A 10-slide board deck outline + the 5 most-asked board questions.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The board is the highest-stakes room. The board has 4 jobs: governance, risk, strategy, and talent. The CDO's board update is the single most important artifact for the year. It is also the most-tested executive moment.

The board deck has 10 slides:

| # | Slide | Content |
|---|---|---|
| 1 | Cover | Date, audience, "Data & AI Quarterly Review" |
| 2 | Executive summary | 3-5 headlines, 1 paragraph, the asks |
| 3 | Strategy on a page | The 3-year plan, year-by-year, current year in detail |
| 4 | KPIs | 3-5 KPIs with trend (reliability, adoption, AI in production, ROI, cost) |
| 5 | AI portfolio | 5-7 use cases, status, ROI, risks |
| 6 | Major initiatives | 3-5 initiatives, status, milestones, risks |
| 7 | Risk and governance | 5 risks, 5 controls, status |
| 8 | Financials | Budget vs. actual, forecast, savings |
| 9 | People | Headcount, hiring, attrition, key roles |
| 10 | Asks | What the board needs to do, decide, or unblock |

The 5 most-asked board questions:

1. **"Are we winning on AI?"** (Honest assessment; not a pitch.)
2. **"What's the biggest risk?"** (The risk, the mitigation, the residual.)
3. **"Where are we on the strategy?"** (Year-by-year, on track / at risk / off track.)
4. **"What's the ROI we've delivered so far?"** (Numbers, not narratives.)
5. **"What do you need from the board?"** (Specific asks, not "support.")

The single biggest mistake is to **bury the bad news**. The board member who discovers a problem you didn't disclose stops trusting everything else. Disclose the bad news; lead with the mitigation.

The second biggest mistake is to **talk about technology**. The board doesn't care about the architecture. The board cares about the outcome. Translate: "we shipped the feature store" → "we can now deploy an AI model in 2 weeks instead of 6 months."

The third biggest mistake is to **not have an ask**. The board update without an ask is a status report. The board update with an ask is a call to action. Always have 1-2 asks.

## 🛠️ Build It

**Spec:** Build the 10-slide board deck outline + the 5 board answers.

**Acceptance:**
- 10 slides outlined
- 5 questions, 5 answers
- Each answer: 60 seconds, honest, named ask
- 1 paragraph on the trade-off (transparency vs. reassurance)

**Starter:** Use Week 2's strategy, Week 3's ROI, Week 4's architecture, Week 5's governance. Synthesize.

**Solution (5 board answers, abridged):**

**Q1: Are we winning on AI?**
> "Honest answer: we are at the start, not the middle. We have 1 AI in production. The peer set has 3-5. We are on the path — Y1 foundations, Y2 scale. The risk is we over-promise and under-deliver. The plan is conservative: 1 AI in Y1, 5 in Y2, 10+ in Y3. The board should expect the Y1 commitment to hold; Y2 and Y3 depend on Y1."

**Q2: What's the biggest risk?**
> "Three risks. One, doing AI before foundations — the 18-month 'almost AI' failure. Mitigation: 1 AI in Y1 with foundations, not 5. Two, regulatory exposure — the AI Act classifies some of our use cases as high-risk. Mitigation: model registry, conformity assessment, human oversight, quarterly review. Three, talent — we can't hire fast enough. Mitigation: 2-3 senior hires in Y1; partner with universities; remote-friendly policy."

**Q3: Where are we on the strategy?**
> "Year 1, month X. Foundations on track: data contracts on 5 sources, semantic layer MVP, 1 AI in production. The at-risk item is adoption — the BUs are slower than the platform team. Mitigation: co-ownership with the BUs, named data champions, BU scorecards."

**Q4: What's the ROI we've delivered so far?**
> "Two numbers. Month-end close: 5 days → 2 hours, saving $X/year in finance team time. First AI: $Y revenue / $Z margin in the first quarter. Forecast: $A-$B run-rate by EOY, $C-$D by EOY2. The risk-adjusted is 60% of the forecast."

**Q5: What do you need from the board?**
> "Three asks. One, the board to back the consolidation of 3 warehouses to 1 — there will be BU pushback, the board endorsement is the difference between 18 months and 36 months. Two, the board to approve the $XM Y2 budget. Three, the board to hold the BU heads accountable for data quality and adoption in their scorecards."

**Trade-off (transparency vs. reassurance):** Lead with the bad news; close with the mitigation. The board that hears the bad news and the mitigation trusts the next update. The board that hears only the good news stops trusting the next one.

## 🏛️ Architect Notes

- **Trade-off:** Detail vs. brevity. The board has 30 minutes. Use 10 minutes for the deck, 20 for Q&A. The deck is the headline; the Q&A is the depth.
- **Capacity / cost:** A board deck takes 2-3 days to build well. Plan the time. Don't wing it.
- **When NOT to use:** Don't bring a deck with a typo to the board. The board notices.
- **Production checklist:**
  - [ ] 10 slides outlined
  - [ ] 5 questions, 5 answers
  - [ ] 60 seconds per answer
  - [ ] Honest assessment
  - [ ] Named ask
  - [ ] Trade-off paragraph

## 🌙 Reflect

- Which slide is your weakest? Re-build.
- Which board question would your actual board chair ask first? Pre-write.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 35 — Difficult Questions.