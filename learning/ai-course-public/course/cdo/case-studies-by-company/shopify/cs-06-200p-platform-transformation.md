# CS-06 (Shopify) — Transforming a 200-person data org into a platform+product team

> **Mapping:** Original CS-06. Scaled to Shopify's 200-person data + ML org.
> **Goal:** 30 minutes. Defend a 3-year transformation to Tobi + the BU ML leads (Magic, Logistics, Capital, Shop Pay, Plus) + the CFO.

## The brief

You are 90 days into the senior data/AI role. ~200 data + ML people across the BUs. Each BU has its own stack, its own metrics, its own tools. The board wants AI; Tobi wants Magic to win; the BU leads want their pods unblocked.

**State of the org today:**
- ~200 data + ML people, mostly embedded in BU pods [CONFIRM exact number]
- 5+ definitions of "active merchant" [CONFIRM]
- Magic in production; Sidekick in beta
- Logistics ML in production; Capital ML in production; Shop Pay fraud ML in production
- Plus data product in production

**Your task:** Design the 3-year transformation. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min).**
- Magic: ~50 ML engineers, the largest AI team; the merchant-facing AI surface
- Logistics: ~30 ML engineers, SFN routing + Deliverr integration
- Capital: ~20 ML engineers, merchant underwriting
- Shop Pay: ~25 ML engineers, fraud + rewards
- Plus: ~30 data people, enterprise merchant analytics
- SMB / Core: ~30 data people, the long tail
- The diagnosis: 6 federated data + ML pods, 1 board mandate for AI, 1 CFO mandate for cost discipline

**Target shape (5 min).**
- Y1: Hub-and-spoke. Center (senior data/AI lead + 10-person platform team) sets standards: data contracts, semantic layer, ML feature store, Magic eval harness. Spokes (~190 across 6 pods) own delivery.
- Y2: Same shape, deeper federation. BU pods own their feature stores; the center owns the contract + the cross-BU metric model.
- Y3: Federation — if engineering maturity is there. BU ML teams become product teams with their own P&L.

**Transformation (10 min):**

| Phase | Theme | Milestones | Quick wins | Off-ramp |
|---|---|---|---|---|
| **Y1** | Foundations | Cross-BU semantic layer; 1 cross-BU data product; shared ML feature store online; Magic eval harness v1; data contract standard v1 | 1 cross-BU metric (e.g. "merchant lifetime value") standardized; Magic + Capital share features; Sidekick in production for all merchants | If no cross-BU data product by month 12, defer and rebuild |
| **Y2** | Scale | All BUs on platform contracts; 5 cross-BU data products; Magic v3 (per-merchant fine-tuning); Capital v2 (real-time) | 2nd cross-BU data product; first per-merchant Magic fine-tune in production | If cross-BU adoption <50% by month 18, refocus |
| **Y3** | Differentiation | 10+ cross-BU data products; Magic v4 (autonomous merchant agents); first $XM Magic-augmented GMV | First autonomous Magic agent in production; first $XM Magic-augmented GMV | If Magic adoption <50% of merchants by month 24, refocus on Plus |

**Investment (5 min).**
- Headcount: 200 → `[CONFIRM: 220-260]`
- Capex: incremental $XM over 3 years
- Stop doing: `[CONFIRM: 3-5 named initiatives]`

**The people (5 min).**
- Hire: 5 platform, 3 ML platform, 2 governance, 1 chief of staff, 1-2 data product managers
- Grow: every senior engineer gets a development plan; rotation through BU pods in Y1
- Retain: refresh comp bands for ML + data; equity refresh for top performers (Magic retention is the hardest)
- Let go: `[CONFIRM: 5-10 underperformers]`

**Q&A — be ready for:**
- "Why not stay federated from day 1?" — The contract is the prerequisite. Without the contract, federation is chaos.
- "What if a BU lead refuses to share features?" — Escalate to Tobi. The data contract is the platform mandate.
- "What about Magic?" — Magic is a product, not a platform. The platform team *partners* with Magic; it does not own it. The Magic product team owns the merchant experience.
- "What about the 2023 logistics downsizing?" — The 2023 call was the right call. The data should drive the kill. Y1 includes a "kill-or-scale" review for every project.

## Watch for when you re-listen

- **Did you name each BU?** If they don't hear their org, they'll tune out.
- **Did you name the stop-doing list?**
- **Did you name the off-ramps?**
- **Did you end on time?**

---

**Source:** Adapted from original CS-06 + Shopify case-study brief.