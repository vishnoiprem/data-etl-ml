# CS-02 (Meta) — 3-year Director-of-Data strategy across Family of Apps + Reality Labs + MSL

> **Mapping:** Original CS-02. Retargeted to Meta's federated product orgs.
> **Goal:** 30 minutes. Defend a 3-year data + AI strategy to Alex Schultz (CDO), the Family of Apps analytics leads, the Reality Labs data lead, and the MSL data lead.

## The brief

You are the new Director of Data. 500 data people across Family of Apps (FB, IG, WhatsApp, Threads), Reality Labs, and Meta Superintelligence Labs (MSL). Each org has its own data plane, tools, metrics. The board wants AI; the CFO wants ROI; the product leads want their pods unblocked.

**State of the company today:**
- 500+ data people, mostly embedded in product pods
- 5+ definitions of "engaged user" [CONFIRM]
- Andromeda + GEM in production; Llama 4 shipped; Meta AI in WhatsApp/IG/FB
- $70-72B 2025 capex; 2026 capex "notably larger"
- 2026 RIF: ~8,000 jobs cut + 6,000 reqs closed

**Your task:** Build a 3-year strategy. Year by year. Defend in 30 minutes to the 4 leaders.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min).**
- Family of Apps: 5+ definitions of "engaged user" [CONFIRM]. Andromeda + GEM shipping is the AI proof point; the data plane is the next ceiling.
- Reality Labs: $[CONFIRM: $-X B]/year burn; the data plane for Quest / Ray-Ban is `[CONFIRM: fragmented]`.
- MSL: best-in-class training data; eval + serving data is the bottleneck for the Llama cadence.
- The diagnosis: 3 federated data orgs, 1 board mandate for AI, 1 CFO mandate for ROI.

**Strategy (5 min).**
- **Year 1: Foundations.** One cross-product semantic layer; contracts on top 5 cross-product source systems; 1 cross-product AI in production (suggest: cross-product feature store serving Andromeda + GEM). The Meta AI eval harness shared with MSL.
- **Year 2: Scale.** All Family of Apps on the cross-product platform. 5 cross-product AI. Reality Labs data plane consolidated. MSL eval harness in production. CDO in board reporting.
- **Year 3: Differentiation.** 10+ cross-product AI. Externalized data products (Llama-as-a-service revenue line). Agentic AI in production. CDO peer of CFO and CPO.

**Roadmap (5 min).** Y1 in detail. Y2-Y3 directional.

**Investment (5 min).**
- Headcount: 500 → `[CONFIRM: 520]` (don't double, sequence); 10 platform hires, 5 governance, 1 chief of staff
- Capex: incremental `[CONFIRM: $XM]` over 3 years
- Stop doing: `[CONFIRM: 3-5 named Meta initiatives]`

**90-day plan (5 min).**
- Days 1-30: 1:1 with every analytics lead, PM lead, ML lead
- Days 31-60: contracts on top 3 cross-product sources; semantic layer MVP; 1 cross-product metric standardized
- Days 61-90: 1 cross-product AI in production with named revenue impact; 1-year roadmap signed off

**Q&A — be ready for:**
- "Why not product-pod-embedded?" — Per Opinion 1. Federation is the destination; Y1 is hub-and-spoke.
- "Why is MSL in this?" — Joint ownership. MSL owns the model layer; CDO owns the data + feature + eval layer.
- "What about the 2026 RIF?" — The 500 stays at 500. The new hires are net; some current roles are repurposed.

## Watch for when you re-listen

- **Did you name each leader's org in their language?** "DAP," "Andromeda," "Llama," "Reality Labs" — not "data platform."
- **Did you name the stop-doing list?** A 3-year plan without cuts is a wish.
- **Did you defend the federated shape?** Per Opinion 1.
- **Did you end on time?** If you run over, the leaders conclude you can't prioritize.

---

**Source:** Adapted from original CS-02 + Meta case-study brief.