# CS-02 (Stripe) — 3-year Head of Data Platform strategy across Payments / Billing / Connect / Issuing / Treasury / Radar

> **Mapping:** Original CS-02. Retargeted to Stripe's BU structure.
> **Goal:** 30 minutes. Defend a 3-year Head of Data Platform strategy to Emily Sands + the BU data leads.

## The brief

You are 30 days into the Head of Data Platform role. The board wants AI progress; Emily wants the data org mandate delivered; the BU data leads want their pods unblocked. The CFO is the implicit reviewer on every line item.

**State of the org today:**
- `[CONFIRM: ~120-180]` data people across `[CONFIRM: 6+ BU-pods]`
- Sigma is a product; the underlying warehouse is internal
- Radar is the largest ML workload
- Smart-retries (2022) was the last public ML revenue lift (+10.5%)

**Your task:** Design the 3-year strategy. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (5 min).**
- 6+ BU data pods; each has its own metrics, its own pipelines, its own ML
- The ledger is the crown jewel; the Radar ML is the largest production ML
- Sigma is the merchant-facing data product; it is the *only* merchant-visible data surface
- The diagnosis: BU pods are productive, the substrate is fragmented, the merchant data product is under-leveraged

**Target shape (5 min).**
- Y1: Hub-and-spoke. Center (Head of Data Platform + 10-person platform team) sets standards: data contracts, semantic layer, ML feature store. Spokes (110-170 BU data people) own delivery.
- Y2: Same shape, deeper federation. The BUs own their metric models; the center owns the contract.
- Y3: Federation — if engineering maturity is there. BU data pods become product teams with their own P&L.

**3-year plan (10 min):**

| Phase | Theme | Milestones | Quick wins | Off-ramp |
|---|---|---|---|---|
| **Y1** | Foundations | Cross-BU semantic layer; 1 cross-BU data product; Radar feature store online; data contract standard v1 | 1 cross-BU metric (e.g. "merchant lifetime value") standardized; Radar + smart-retries share features | If no cross-BU data product by month 12, defer and rebuild |
| **Y2** | Scale | All BUs on platform contracts; 5 cross-BU data products; Sigma NL→SQL in GA; per-BU ML feature store | 2nd cross-BU data product; first Sigma NL→SQL merchant in production | If cross-BU adoption <50% by month 18, refocus |
| **Y3** | Differentiation | 10+ cross-BU data products; first merchant-facing AI agent; Ledger-as-a-Platform for partners | First $XM merchant-facing AI agent revenue; first partner using Ledger APIs for data | If external revenue <$XM, kill externalization |

**Investment (5 min).**
- Headcount: `[CONFIRM: 120-180]` → `[CONFIRM: 150-200]`
- Capex: incremental $XM over 3 years
- Stop doing: `[CONFIRM: 3-5 named initiatives]` (e.g. legacy ETL systems, manual finance reporting, redundant experimentation platforms)

**The people (5 min).**
- Hire: 5 platform, 3 ML platform, 2 governance, 1 chief of staff, 1-2 data product managers
- Grow: every senior engineer gets a development plan; rotation through BU pods in Y1
- Retain: refresh comp bands for ML + data; equity refresh for top performers (Radar retention is the hardest)
- Let go: `[CONFIRM: 5-10 underperformers]` (especially in BUs where the work can be automated)

**Q&A — be ready for:**
- "Why not stay federated from day 1?" — The contract is the prerequisite. Without the contract, federation is chaos.
- "What if a BU lead refuses to share features?" — Escalate to Emily. The data contract is the platform mandate.
- "What about Radar?" — Radar is its own BU with its own ML platform. The platform team *partners* with Radar; it does not own it. The ML flywheel lives in Radar.
- "What's the merchant-facing AI product?" — Sigma NL→SQL is the wedge. The end state is per-merchant AI agents (cash-flow forecasting, tax, fraud ops).

**The metrics Emily will track:**

| Metric | Y1 target | Y2 target | Y3 target |
|---|---|---|---|
| Cross-BU data contracts in production | 5 | 15 | 30+ |
| Sigma NL→SQL adoption (merchants) | beta | `[CONFIRM: 1K]` | `[CONFIRM: 10K]` |
| Radar false-decline rate | -5 bps | -10 bps | -15 bps |
| Smart-retry revenue lift | +5% | +10% | +15% |
| Data org eNPS | `[CONFIRM: baseline]` | +5 | +10 |

## Watch for when you re-listen

- **Did you name every BU?** If you said "data pods" without naming Payments / Billing / Connect, you lost.
- **Did you treat Radar as a partner, not a target?** Radar is sacred.
- **Did you name the stop-doing list?**
- **Did you name the off-ramps?**

---

**Source:** Adapted from original CS-02 + Stripe case-study brief.
