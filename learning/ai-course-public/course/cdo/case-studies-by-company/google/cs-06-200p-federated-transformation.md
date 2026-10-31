# CS-06 (Google) — Transforming a 200-person federated data org into a unified platform team

> **Mapping:** Original CS-06 (50-person transformation). Scaled to a federated 200-person data org across Search, Cloud, DeepMind.
> **Goal:** 30 minutes. Defend a 3-year transformation to Prabhakar (K&I), Kurian (Cloud), and Hassabis (DeepMind).

## The brief

You are the new Head of Data for Alphabet. 200 data people spread across 3 federated orgs (K&I, Cloud, DeepMind). Each org has its own data plane, its own tools, its own metrics. The board wants unified AI; the BU heads want their own teams; the CFO wants cost discipline.

**State of the org today:**
- K&I: `[CONFIRM: N]` data engineers + analysts, on `[CONFIRM: stack]`
- Cloud: `[CONFIRM: N]` data engineers + analysts, on BigQuery + Vertex
- DeepMind: `[CONFIRM: N]` research engineers + eval specialists, on `[CONFIRM: stack]`
- 4-5 different definitions of "engaged user" across BUs [CONFIRM]
- 0 cross-plane AI in production
- $52.5B FY24 capex; 2025 guide $75B

**Your task:** Design the 3-year transformation. Defend in 30 minutes.

## The structure (30 min)

| Section | Time | What to say |
|---|---|---|
| Diagnosis | 5 min | The state of the org, in each leader's language |
| Target shape | 5 min | The hub-and-spoke org, year by year |
| Transformation | 10 min | The 3 phases, with quick wins and off-ramps |
| Investment | 5 min | Headcount, budget, what you stop doing |
| The people | 5 min | Hire, grow, retain, let go |

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min).**
- K&I: 200 data people across `[N]` BUs. The data plane is `[CONFIRM]`. 4 definitions of "engaged user." The 18-month "almost AI" pattern.
- Cloud: `[N]` data people on BigQuery + Vertex. Best-in-class publicly; internally `[CONFIRM: same fragmentation?]`.
- DeepMind: `[N]` research engineers. Best-in-class training data; eval data is the bottleneck.
- The diagnosis: we have 3 data orgs, not 1. The fragmentation is the ceiling on cross-plane AI.

**Target shape (5 min).**
- Y1: Hub-and-spoke. Center (Head of Data + 30-person platform team) sets standards, contracts, semantic layer. Spokes (170 across K&I, Cloud, DeepMind) own delivery.
- Y2: Same shape, deeper federation. BUs own delivery; center owns platform.
- Y3: Move toward federation — but only if engineering maturity is there.

**Transformation (10 min):**

| Phase | Theme | Milestones | Quick wins | Off-ramp |
|---|---|---|---|---|
| Y1 | Foundations | Contracts on top 5 cross-plane sources; semantic layer MVP; 1 cross-plane AI in production; org restructure | `[CONFIRM: 1-2 quick wins — e.g., unified engaged-user metric; AI Overviews eval harness]` | If no cross-plane AI by month 12, defer and rebuild |
| Y2 | Scale | All 3 planes on platform; 5 cross-plane AI in production; data products to Cloud customers; CDO in board reporting | 2nd cross-plane AI; first Cloud data product | If cross-plane adoption <50% by month 18, refocus |
| Y3 | Differentiation | 10+ cross-plane AI in production; 1-2 externalized data products; agentic AI; CDO peer of CFO/CTO | First $XM Cloud data product revenue; first agentic AI in production | If external revenue <$XM, kill externalization |

**Investment (5 min).**
- Headcount: 200 → 220 (don't double, sequence); 10 platform hires, 5 governance, 1 chief of staff
- Capex: $XM incremental, growing to $YM by Y3
- **Stop doing:** `[CONFIRM: 3-5 named internal systems or projects]`

**The people (5 min).**
- Hire: 10 platform engineers, 5 governance, 1 chief of staff
- Grow: every senior engineer gets a development plan; top 5 get stretch assignments
- Retain: refresh comp bands; equity refresh for top 10; "stay interviews" for flight risks
- Let go: `[CONFIRM: 5-10 underperformers in Y1; PIP with off-ramp]`

**Q&A — be ready for:**
- "Why not data mesh?" — Per Opinion 1. Engineering maturity isn't there; hub-and-spoke first.
- "Why not give each BU its own platform?" — You'd duplicate the platform team 3×. The consolidation saves $X.
- "What if Prabhakar refuses?" — Escalate to Pichai. The consolidation is non-negotiable; co-own delivery with each BU.
- "What if attrition gets worse?" — Fix the root cause — mission, growth, comp — not the symptom.

## Watch for when you re-listen

- **Did you name each leader in the diagnosis?** If they don't hear their org, they'll tune out.
- **Did you name the stop-doing list?** A transformation without cuts is a wish list.
- **Did you name the off-ramps?** A transformation without off-ramps is a sunk-cost trap.
- **Did you end on time?** If you run over, Pichai concludes you can't prioritize.

---

**Source:** Adapted from original CS-06 + Google case-study brief.