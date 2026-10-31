# Case Study 6: The 50-Person Transformation

> **Week 6 · Case Study · 90 min**
> **Deliverable:** Transform a 50-person fragmented data org in 30 minutes.

## The brief

You are the new CDO at a Series-D retailer with a 50-person data org spread across 5 BUs. The state:

- 5 BU data teams (avg 10 people) — each with its own stack, its own tools, its own metrics
- 1 central data team of 10 — under-resourced, no platform, no governance
- 3 different warehouses (Snowflake, BigQuery, Redshift)
- 4 different BI tools (Looker, Tableau, PowerBI, Metabase)
- 4 definitions of "active customer"
- 18-month attrition rate: 25% [CONFIRM: get real number]
- 0 AI in production; 1 data science team of 6 with no production deployments
- CEO mandate: "ship AI by year-end"
- BU heads: "give us our own data team and stop the central bottleneck"
- CFO: "the data bill is $X, prove the ROI"

**Your task:** Design the 3-year transformation. Defend it in 30 minutes to the CEO, CFO, and 5 BU heads.

## The structure (30 minutes total)

| Section | Time | What to say |
|---|---|---|
| The diagnosis | 5 min | The state of the org, in their language |
| The target shape | 5 min | The hub-and-spoke org, year by year |
| The transformation | 10 min | The 3 phases, with quick wins and off-ramps |
| The investment | 5 min | Headcount, budget, what you stop doing |
| The people | 5 min | Hire, grow, retain, let go |

## The scoring rubric (out of 100)

| Competency | Weight | What "great" looks like |
|---|---|---|
| Leadership and executive influence | 35% | The 5 BU heads sign off; the team rallies |
| Strategic and business thinking | 20% | The org design supports the strategy |
| Commercial and financial understanding | 15% | The headcount and vendor spend are credible |
| Ownership and measurable impact | 15% | The transformation has named milestones |
| Communication and structure | 15% | 30 minutes, no overrun, the BU heads don't check their phone |

A score below 90 means Week 6 is not done. Re-record.

## Acceptance criteria

- 30 minutes, no overrun
- 0 acronyms in the opening 2 minutes
- 5 BU heads heard by name
- 3-year shape named
- 3 phases with quick wins and off-ramps
- Headcount and budget per year
- "Stop doing" list explicit
- "What if a BU head refuses?" answered

## Starter

Use Day 7's operating model. Use Day 26's 5 shapes. Use Day 29's 3 phases. Use Day 27's people playbook. Synthesize.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min):**
- 5 BU data teams, 3 warehouses, 4 BI tools, 4 "active customer" definitions → fragmentation tax is real
- 25% attrition → losing the institutional knowledge; can't build a platform if the team turns over
- 0 AI in production, 1 data science team of 6 with 18 months of "almost" → AI mandate will fail without foundation
- 1,200 stores, $2B revenue, 4M MAU → the opportunity is real
- The diagnosis is "we have 5 data teams, not 1 data org. The fragmentation is the problem."

**Target shape (5 min):**
- Y1: Hub-and-spoke. Platform + Governance + 5 BU spokes (embedded)
- Y2: Same shape, deeper federation. BUs own delivery; center owns platform
- Y3: Move toward data mesh — but only if the engineering maturity is there

**Transformation (10 min):**

| Phase | Theme | Milestones | Quick wins | Off-ramp |
|---|---|---|---|---|
| Y1 | Foundations | Contracts on top 5; semantic layer MVP; 1 AI in production; org restructure; reduce attrition to 12% | Month-end close 5d → 2h; single source of truth for revenue; first AI in production | If no AI by month 12, defer AI and rebuild |
| Y2 | Scale | All 5 BUs on platform; 5 AI in production; data products to business; CDO in board reporting | 2nd AI; first externalized data product; FinOps dashboard | If BU adoption <50% by month 18, refocus |
| Y3 | Differentiation | 10+ AI in production; 1-2 external data products; agentic AI; CDO peer of CFO/CTO | First $XM in data product revenue; first agentic AI in production | If external revenue <$XM, kill externalization |

**Investment (5 min):**
- Headcount: 50 → 55 (don't double, sequence); 5 hires in platform, 2 in governance, 1 in chief of staff
- Budget: $XM, growing to $YM by Y3
- **Stop doing:** the 4 legacy BI tools (migrate to Looker); 2 of 3 warehouses (migrate to 1); ad-hoc pipelines from BU teams; the "we'll do AI" without a foundation

**People (5 min):**
- Hire: 5 platform engineers, 2 governance, 1 chief of staff
- Grow: every senior engineer gets a development plan; 5 top performers get stretch assignments
- Retain: refresh comp bands; equity refresh for top 5; "stay interviews" for flight risks
- Let go: 3-5 underperformers in Y1; PIP with off-ramp; communicated with dignity

**Q&A — be ready for:**
- "Why not data mesh?" (engineering maturity isn't there; hub-and-spoke first)
- "Why not give each BU its own platform?" (you'd duplicate the platform team 5×; the consolidation saves $XM)
- "What if a BU head refuses?" (escalate to CEO; the consolidation is non-negotiable; we'll co-own delivery with the BU)
- "What if attrition gets worse?" (we'll fix the root cause — mission, growth, comp — not the symptom)

## What to watch for when you re-listen

- **Did you name every BU head?** If a BU head doesn't hear their name, they'll tune out.
- **Did you name the "stop doing" list?** A transformation without cuts is a wish list.
- **Did you name the off-ramps?** A transformation without off-ramps is a sunk-cost trap.
- **Did you end on time?** If you run over, the CEO concludes you can't prioritize.

## Re-record until you score ≥ 90

A CDO who can't transform a 50-person org in 30 minutes is not a CDO. The transformation is the most-tested executive question.

---

**Next:** Week 7, Day 31 — CEO Interview.