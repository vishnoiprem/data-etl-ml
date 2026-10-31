# Lesson 11: Business finance fundamentals

> **Week 3 · Day 11 · 90 min**
> **Deliverable:** The 10 numbers a CDO must know cold for any business they interview for.

## 🎯 Architect Level
Senior.

## 🧠 Concept

The CDO who can't read a P&L gets managed by the CFO. The CDO who can read a P&L gets a seat at the table.

There are 10 numbers every executive must know cold for the business they serve. They are not "the 10 financial ratios." They are the 10 **business outcomes** that the data and AI investments must move.

| # | Number | What it tells you | Where it lives |
|---|---|---|---|
| 1 | Revenue (top line) | The size of the prize | P&L |
| 2 | Gross margin | The unit economics of the core business | P&L |
| 3 | EBITDA / operating margin | The profit after operating costs | P&L |
| 4 | Customer Acquisition Cost (CAC) | The cost to win one customer | P&L + cohort |
| 5 | Customer Lifetime Value (CLV / LTV) | The revenue one customer returns over life | Cohort |
| 6 | CAC payback period | Months to recoup the acquisition cost | Derived |
| 7 | Net Revenue Retention (NRR) | The expansion minus churn in existing customers | Cohort |
| 8 | Working capital / cash conversion cycle | How much cash is tied up in operations | Balance sheet |
| 9 | Cash from operations | The cash the business actually generates | Cash flow |
| 10 | Burn / runway (if growth) | Months of cash left at current spend | Cash flow |

For each, you must know:
- The current value (and the trajectory — up, down, flat)
- The benchmark for the industry
- The single biggest lever that moves it
- The data and AI investments that could move that lever

The CDO interview is not "tell me about data architecture." It is "if you took this job, which of these 10 numbers would move in year 1, and how?" If you don't know the 10 numbers, you can't answer.

## 🛠️ Build It

**Spec:** For a Series-D retailer with $2B revenue, 1,200 stores, 4M MAU, build the 10-number dashboard.

**Acceptance:**
- All 10 numbers named
- Current value (with `[CONFIRM: source]` if estimated)
- Industry benchmark
- Single biggest lever
- 1 data/AI investment that could move the lever
- 1 trade-off (cost vs. speed)

**Starter:** Start with the retail benchmark — gross margin for grocery is 20-25%, for general merchandise 30-40%, for fresh 30-45%. Pick the segments and compute the blended.

**Solution (10 numbers, retailer):**

| # | Number | Current | Benchmark | Lever | Data/AI investment |
|---|---|---|---|---|---|
| 1 | Revenue | $2B | n/a | Same-store sales + new format | Customer 360 + personalization |
| 2 | Gross margin | ~25% blended | 28-32% top quartile | Private label mix + markdown optimization | Demand forecasting + dynamic pricing |
| 3 | EBITDA margin | ~6% | 8-10% top quartile | SG&A leverage | Back-office automation + FinOps |
| 4 | CAC (online) | $X [CONFIRM] | Industry varies | Channel mix + retention | Attribution + LTV scoring |
| 5 | CLV (online) | $X [CONFIRM] | 3-5x CAC | Repeat rate | Recommendation + next-best-offer |
| 6 | CAC payback | $X months | <12 months | Conversion + retention | ML personalization |
| 7 | NRR (B2B) | $X% | >110% top quartile | Account expansion | Account 360 + propensity |
| 8 | Working capital | $X | Sector specific | Inventory turn | Inventory optimization + DSO |
| 9 | Cash from operations | $X | n/a | WC + EBITDA | All of the above |
| 10 | Burn / runway | n/a (profitable) | n/a | n/a | n/a |

The point is not the specific numbers (those depend on the company). The point is the **shape** — every row has a number, a benchmark, a lever, and an investment. The CDO who can fill in this table in 30 minutes for any business they interview for is the CDO who gets hired.

## 🏛️ Architect Notes

- **Trade-off:** Depth vs. breadth. Know all 10 broadly, know 2-3 deeply (the ones the role most moves).
- **Capacity / cost:** Zero cost to learn; this is a knowledge artifact. Time: 2-3 hours per industry.
- **When NOT to use:** Don't quote numbers you don't have. Use "[CONFIRM: source]" markers and ask the interviewer.
- **Production checklist:**
  - [ ] 10 numbers named
  - [ ] Current value with source or [CONFIRM]
  - [ ] Industry benchmark
  - [ ] Single biggest lever
  - [ ] Data/AI investment per lever
  - [ ] 1 trade-off named

## 🌙 Reflect

- Which of the 10 numbers do you know cold for the business you're interviewing for?
- Which one would the CFO challenge first? Pre-write the answer.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 12 — Data and AI business cases.