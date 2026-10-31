# CS-06 (Stripe) — Transforming a small (~150 person) data org into a platform+product team

> **Mapping:** Original CS-06. Scaled to Stripe's ~150 person data org.
> **Goal:** 30 minutes. Defend a 3-year transformation to Emily Sands (Head of Data & AI), the BU data leads (Payments, Billing, Connect, Issuing, Treasury, Radar), and the CFO.

## The brief

You are 90 days into the Head of Data Platform role. ~150 data people across the BUs. Each BU has its own stack, its own metrics, its own tools. The board wants AI; Patrick wants Radar to keep winning; the BU leads want their pods unblocked.

**State of the org today:**
- ~150 data people, mostly embedded in BU pods [CONFIRM exact number]
- 5+ definitions of "active merchant" [CONFIRM]
- Radar in production; smart-retries 2022 published; Sigma is the merchant-facing data product
- Radar ML team is the strongest; Issuing data team is the newest

**Your task:** Design the 3-year transformation. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min).**
- Payments: ~30 data people, deep Radar coupling
- Billing: ~20 data people, focused on subscription metrics + rev rec
- Connect: ~15 data people, multi-party payment analytics
- Issuing: ~15 data people, credit decisioning + spend mgmt (newest)
- Treasury: ~10 data people, bank-partnership analytics (newest)
- Radar: ~30 ML engineers, the largest ML team
- Sigma: ~15 data product people, the merchant-facing data product
- The diagnosis: 7 federated data pods, 1 board mandate for AI, 1 CFO mandate for cost discipline

**Target shape (5 min).**
- Y1: Hub-and-spoke. Center (Head of Data Platform + 10-person platform team) sets standards: data contracts, semantic layer, ML feature store. Spokes (~140 across 7 pods) own delivery.
- Y2: Same shape, deeper federation. BU pods own their metric models; the center owns the contract.
- Y3: Federation — if engineering maturity is there. BU data pods become product teams with their own P&L.

**Transformation (10 min):**

| Phase | Theme | Milestones | Quick wins | Off-ramp |
|---|---|---|---|---|
| **Y1** | Foundations | Cross-BU semantic layer; 1 cross-BU data product; cross-ML feature store online; data contract standard v1 | 1 cross-BU metric standardized; Radar + smart-retries share features; Sigma NL→SQL in beta | If no cross-BU data product by month 12, defer and rebuild |
| **Y2** | Scale | All BUs on platform contracts; 5 cross-BU data products; Sigma NL→SQL in GA; per-BU ML feature store | 2nd cross-BU data product; first Sigma NL→SQL merchant in production | If cross-BU adoption <50% by month 18, refocus |
| **Y3** | Differentiation | 10+ cross-BU data products; first merchant-facing AI agent; Ledger-as-a-Platform for partners | First $XM merchant-facing AI agent revenue; first partner using Ledger APIs for data | If external revenue <$XM, kill externalization |

**Investment (5 min).**
- Headcount: 150 → `[CONFIRM: 165-180]`
- Capex: incremental $XM over 3 years
- Stop doing: `[CONFIRM: 3-5 named initiatives]`

**The people (5 min).**
- Hire: 5 platform, 3 ML platform, 2 governance, 1 chief of staff, 1-2 data product managers
- Grow: every senior engineer gets a development plan; rotation through BU pods in Y1
- Retain: refresh comp bands for ML + data; equity refresh for top performers (Radar retention is the hardest)
- Let go: `[CONFIRM: 5-10 underperformers]`

**Q&A — be ready for:**
- "Why not stay federated from day 1?" — The contract is the prerequisite. Without the contract, federation is chaos.
- "What if a BU lead refuses to share features?" — Escalate to Emily. The data contract is the platform mandate.
- "What about Radar?" — Radar is its own BU with its own ML platform. The platform team *partners* with Radar; it does not own it. The ML flywheel lives in Radar.
- "What about Sigma?" — Sigma is a product, not a platform. The platform team partners with Sigma; the Sigma product team owns delivery.

## Watch for when you re-listen

- **Did you name each BU?** If they don't hear their org, they'll tune out.
- **Did you name the stop-doing list?**
- **Did you name the off-ramps?**
- **Did you end on time?**

---

**Source:** Adapted from original CS-06 + Stripe case-study brief.
