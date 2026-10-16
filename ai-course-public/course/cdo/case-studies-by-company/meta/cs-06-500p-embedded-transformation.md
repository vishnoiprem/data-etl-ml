# CS-06 (Meta) — Transforming a 500-person embedded data org into a CDO-mandated platform team

> **Mapping:** Original CS-06. Scaled to Meta's 500-person embedded data org.
> **Goal:** 30 minutes. Defend a 3-year transformation to Alex Schultz (CDO), the Family of Apps analytics leads, the Reality Labs data lead, and the MSL data lead.

## The brief

You are the new Director of Data. 500 data people embedded across product pods. Each pod has its own stack, its own metrics, its own tools. The board wants AI; Schultz wants the CDO mandate delivered; the product leads want their pods unblocked.

**State of the org today:**
- 500+ data people, mostly embedded in product pods [CONFIRM]
- 5+ definitions of "engaged user" [CONFIRM]
- Andromeda + GEM in production
- 2026 RIF: ~8,000 jobs cut + 6,000 reqs closed

**Your task:** Design the 3-year transformation. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min).**
- Family of Apps: 500+ data people, embedded in pods, fragmented metrics. The 18-month "almost AI" pattern.
- Reality Labs: $[CONFIRM: $-X B] burn; data plane fragmented.
- MSL: best-in-class training; eval + serving data is the bottleneck.
- The diagnosis: 3 federated data orgs, 1 board mandate for AI, 1 CFO mandate for ROI.

**Target shape (5 min).**
- Y1: Hub-and-spoke. Center (Director of Data + 50-person platform team) sets standards, contracts, semantic layer. Spokes (450 across Family of Apps, Reality Labs, MSL) own delivery.
- Y2: Same shape, deeper federation.
- Y3: Federation — if engineering maturity is there.

**Transformation (10 min):**

| Phase | Theme | Milestones | Quick wins | Off-ramp |
|---|---|---|---|---|
| Y1 | Foundations | Cross-product semantic layer; 1 cross-product AI; org restructure | 1 cross-product metric standardized; Andromeda + GEM sharing a feature | If no cross-product AI by month 12, defer and rebuild |
| Y2 | Scale | All Family of Apps on platform; 5 cross-product AI; Reality Labs consolidated | 2nd cross-product AI; first Reality Labs consolidation | If cross-product adoption <50% by month 18, refocus |
| Y3 | Differentiation | 10+ cross-product AI; Llama-as-a-service; agentic AI | First $XM Llama service revenue; first agentic AI in production | If external revenue <$XM, kill externalization |

**Investment (5 min).**
- Headcount: 500 → `[CONFIRM: 520]`
- Capex: incremental $XM over 3 years
- Stop doing: `[CONFIRM: 3-5 named initiatives]`

**The people (5 min).**
- Hire: 10 platform, 5 governance, 1 chief of staff
- Grow: every senior engineer gets a development plan
- Retain: refresh comp bands; equity refresh for top 10
- Let go: `[CONFIRM: 5-10 underperformers]`

**Q&A — be ready for:**
- "Why not stay embedded?" — Per Opinion 1. Federation is the destination; Y1 is hub-and-spoke.
- "What if a pod lead refuses to share features?" — Escalate to Schultz. The cross-product feature store is the CDO mandate.
- "What about the 2026 RIF?" — The 500 stays. Net hires are repurposed; some roles are eliminated.

## Watch for when you re-listen

- **Did you name each leader in the diagnosis?** If they don't hear their org, they'll tune out.
- **Did you name the stop-doing list?**
- **Did you name the off-ramps?**
- **Did you end on time?**

---

**Source:** Adapted from original CS-06 + Meta case-study brief.