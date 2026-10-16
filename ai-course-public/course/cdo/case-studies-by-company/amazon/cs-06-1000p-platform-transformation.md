# CS-06 (Amazon) — Transforming a 1,000-person data org into a platform+product team across the 3 segments

> **Mapping:** Original CS-06. Scaled to Amazon's ~1,000-person data + ML org.
> **Goal:** 30 minutes. Defend a 3-year transformation to Andy Jassy + the BU ML leads (Rufus, Bedrock, Q, Alexa, Ads, Supply Chain) + the CFO.

## The brief

You are 90 days into the senior data/AI role. ~1,000 data + ML people across the 3 segments. Each segment has its own stack, its own metrics, its own tools. The board wants AI; Andy wants Bedrock + Q + Rufus to win; the BU leads want their pods unblocked.

**State of the org today:**
- ~1,000 data + ML people, mostly embedded in segment + BU pods [CONFIRM exact number]
- 5+ definitions of "active customer" across segments [CONFIRM]
- Bedrock in production; Q in production; Rufus in production
- Retail recommendation + supply chain + ads ML in production
- Alexa LLM in production (post-2023)

**Your task:** Design the 3-year transformation. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min).**
- North America: ~300 data + ML people, retail recommendation + supply chain + ads
- International: ~200 data + ML people, regional retail + payments + localization
- AWS: ~500 data + ML people, Bedrock + Q + SageMaker + custom silicon
- The diagnosis: 3 segments × 7+ BU-pods, 1 board mandate for AI, 1 CFO mandate for cost discipline

**Target shape (5 min).**
- Y1: Hub-and-spoke. Center (senior data/AI lead + 10-person platform team) sets standards: data contracts, semantic layer, ML feature store, Bedrock + Q eval harness. Spokes (~1,000 across 3 segments × 7+ pods) own delivery.
- Y2: Same shape, deeper federation. Segment + BU pods own their feature stores; the center owns the contract + the cross-segment metric model.
- Y3: Federation — if engineering maturity is there. Segment + BU ML teams become product teams with their own P&L.

**Transformation (10 min):**

| Phase | Theme | Milestones | Quick wins | Off-ramp |
|---|---|---|---|---|
| **Y1** | Foundations | Cross-segment semantic layer; 1 cross-segment data product; shared ML feature store online; Bedrock + Q eval harness v1; data contract standard v1; Anthropic partnership deepened | 1 cross-segment metric (e.g. "customer lifetime value across retail + AWS + Prime") standardized; Bedrock + Q share features; Trainium v2 in production | If no cross-segment data product by month 12, defer and rebuild |
| **Y2** | Scale | All BUs on platform contracts; 5 cross-segment data products; Bedrock v2 (multi-agent); Q v2 (enterprise); Trainium v3; Inferentia v3 | 2nd cross-segment data product; first multi-agent Bedrock app in production | If cross-segment adoption <50% by month 18, refocus |
| **Y3** | Differentiation | 10+ cross-segment data products; first $XM AI revenue from Bedrock; first autonomous retail AI (auto-pricing + auto-inventory); AI flywheel as the 5th engine | First autonomous retail AI in production; first $XM AI revenue from Bedrock | If AI revenue <$XM by month 24, refocus on AWS |

**Investment (5 min).**
- Headcount: 1,000 → `[CONFIRM: 1,200-1,500]`
- Capex: incremental $XM over 3 years
- Stop doing: `[CONFIRM: 3-5 named initiatives]`

**The people (5 min).**
- Hire: 5 platform, 3 ML platform, 2 governance, 1 chief of staff, 1-2 data product managers
- Grow: every senior engineer gets a development plan; rotation through segments in Y1
- Retain: refresh comp bands for ML + data; equity refresh for top performers (Bedrock + Q retention is the hardest)
- Let go: `[CONFIRM: 5-10 underperformers]`

**Q&A — be ready for:**
- "Why not stay federated from day 1?" — The contract is the prerequisite. Without the contract, federation is chaos.
- "What if a BU lead refuses to share features?" — Escalate to Andy. The data contract is the platform mandate.
- "What about Bedrock?" — Bedrock is a product, not a platform. The platform team *partners* with Bedrock; it does not own it. The Bedrock product team owns the model marketplace.
- "What about the Anthropic partnership?" — Anthropic is the primary model partner; Bedrock is the marketplace; Trainium is the silicon. The right answer is "Anthropic + Bedrock + Trainium, not Anthropic alone."
- "What about the 2023 Alexa downsizing?" — The 2023 call was the right call. The data should drive the kill. Y1 includes a "kill-or-scale" review for every project.

## Watch for when you re-listen

- **Did you name each segment?** If they don't hear their segment, they'll tune out.
- **Did you name the stop-doing list?**
- **Did you name the off-ramps?**
- **Did you end on time?**

---

**Source:** Adapted from original CS-06 + Amazon case-study brief.