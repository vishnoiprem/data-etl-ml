# Case Study 2: Retailer 3-year data and AI strategy

> **Week 2 · Case Study · 90 min**
> **Deliverable:** A 3-year strategy deck for a fragmented retailer under AI pressure.

## The brief

You are the new Head of Data at a Series-D retailer with $2B revenue, 5 BUs (grocery, general merchandise, online, B2B, fresh), 1,200 stores, and 4M monthly active customers. The CEO has hired you because the board is asking for an AI strategy and the BU heads are asking for a data strategy. The two are not aligned.

**State of the company today:**
- 5 BU heads each run their own data team (avg 8 people, total 40)
- 3 different data warehouses (Snowflake, BigQuery, Redshift)
- 6 different BI tools (Looker, Tableau, PowerBI, Metabase, custom)
- No data contracts with any source system
- 4 different definitions of "active customer" across BUs
- 1 data science team of 6 with no production deployments in 18 months
- A board mandate to "ship AI in production by year-end" (i.e., 9 months)

**Your task:** Build a 3-year data and AI strategy. Defend it in front of the CEO and the 5 BU heads. You have 30 minutes. They will challenge every choice.

## The structure (PDCA, 30 minutes total)

| Section | Time | What to say |
|---|---|---|
| The diagnosis | 5 min | What the state of the company is, in their language |
| The strategy | 5 min | The 3-year theme, year by year |
| The roadmap | 5 min | Year 1 in detail, years 2-3 directional |
| The investment | 5 min | Headcount, budget, what you stop doing |
| The 90-day plan | 5 min | What you'll do in the first 90 days |
| Q&A | 5 min | Defend every choice |

## The scoring rubric (out of 100)

| Competency | Weight | What "great" looks like |
|---|---|---|
| Strategic and business thinking | 25% | The CEO nods at the diagnosis; the BU heads feel heard |
| Leadership and executive influence | 20% | The 5 BU heads sign off; the CFO sees the cost discipline |
| Technical judgment and architecture | 20% | The 3 warehouses have a story; the AI mandate has a path |
| Commercial and financial understanding | 15% | The investment is named; the ROI is named; the "stop doing" is named |
| Communication and structure | 10% | 30 minutes, no overrun, the 5 BU heads don't check their phone |
| Ownership and measurable impact | 10% | Year 1 has 3-5 measurable outcomes |

A score below 90 means Week 2 is not done. Re-record.

## Acceptance criteria

- 30 minutes, no overrun
- 0 acronyms in the opening 2 minutes
- 5 BU heads heard by name in the diagnosis
- 3-year theme is year-by-year
- Year 1 has 3-5 measurable outcomes
- "Stop doing" list is explicit
- 90-day plan has a quick win and a foundational investment
- Q&A: every choice can be defended in 60 seconds

## Starter

Use Story 1 (Unified Data Platform transformation) and Story 2 (KPI standardization) as the reference shapes. The 90-day plan from Day 10 is the template.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min):**
- 5 BUs, 5 data teams, 3 warehouses, 6 BI tools → no single source of metric truth
- 4 definitions of "active customer" → 4 different numbers in the board deck
- 1 data science team of 6 with 0 production deployments in 18 months → AI mandate will fail without foundation
- 1,200 stores, 4M MAU, $2B revenue → scale is real, the opportunity is real
- The diagnosis is not "we need AI." The diagnosis is "we need foundations before AI."

**Strategy (5 min):**
- **Year 1: Foundations.** Single semantic layer, data contracts, lakehouse on one warehouse, AI in production for one use case.
- **Year 2: Scale.** All 5 BUs on the platform. 5 AI use cases. Data products shipped to business.
- **Year 3: Differentiation.** Agentic AI, new revenue from data products, board-level reporting.

**Roadmap (5 min):**
- Year 1 in detail (per Day 9)
- Years 2-3 directional

**Investment (5 min):**
- Headcount: 40 → 55 (don't double, sequence)
- Budget: $XM (consolidate 3 warehouses into 1 saves $X)
- **Stop doing:** the 4 legacy BI tools, the 3 legacy warehouses, the ad-hoc pipelines from the BU teams

**90-day plan (5 min):**
- Per Day 10
- Quick win: month-end close 5d → 2h
- Foundational investment: data contracts with top 5 source systems

**Q&A (5 min):**
- Be ready for: "Why not data mesh?" "Why not Snowflake?" "Why not LLM-first?" "What's the cost?" "What if a BU head refuses to consolidate?"

## What to watch for when you re-listen

- **Did you name every BU head?** If a BU head doesn't hear their name in the diagnosis, they'll tune out.
- **Did you name the "stop doing" list?** A strategy without cuts is a wish list.
- **Did you defend the rejected alternatives?** If the CEO asks "why not Snowflake?" and you don't have an answer, you've lost the room.
- **Did you end on time?** If you run over, the CEO concludes you can't prioritize.

## Re-record until you score ≥ 90

A CDO who can't defend a 3-year strategy in 30 minutes is not a CDO. The 30-minute defense is the single most important artifact in the interview loop.

---

**Next:** Week 3, Day 11 — Business Finance Fundamentals.
