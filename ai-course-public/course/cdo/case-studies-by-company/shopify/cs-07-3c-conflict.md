# CS-07 (Shopify) — The 3-C conflict: Tobi wants AI everywhere, CFO wants cost discipline, CTO wants platform consolidation

> **Mapping:** Original CS-07. Retargeted to Shopify's leadership cast.
> **Goal:** 30 minutes. Mediate a 3-C conflict between Tobi (CEO), the CFO (Jeff Hoffmeister), and the CTO (Mikhail Parakhin).

## The brief

You are 6 months into the senior data/AI role. Three C-level peers have a conflict that you have to resolve (or escalate). The board is watching.

**The conflict:**
- **Tobi Lütke (CEO):** "Ship Magic v2, ship Sidekick for all merchants, ship the merchant agent. AI is the strategy."
- **CFO (Jeff Hoffmeister):** "Cut the burn growth. $20M data + AI platform is the ceiling. Show me the ROI on every AI dollar."
- **CTO (Mikhail Parakhin):** "Consolidate the platform. Stop the per-BU feature stores. One platform team."

Each C is right. Each C is also wrong.

**Your task:** Mediate. Find a path that:
- Ships visible Magic + Sidekick progress (Tobi's win)
- Cuts burn growth or proves ROI (CFO's win)
- Builds the platform consolidation (CTO's win)
- Doesn't break the BU ML teams

## Solution sketch (do not copy — internalize and re-speak)

**Framing (3 min).** "Three legitimate constraints, not three competing priorities."

**Diagnosis (5 min).**
- Tobi: AI everywhere because the competitive clock is real (Amazon Rufus, Stripe Assistant, every commerce platform is shipping AI). Hidden cost: shipping unprofitable AI features.
- CFO: cost discipline because Wall Street + GMV growth + Logistics capex. Hidden cost: cutting the foundation cuts the AI ROI.
- CTO: platform consolidation because the per-BU feature stores are duplicative. Hidden cost: consolidating without a contract = chaos.

**Proposal (10 min).**

| Constraint | Path |
|---|---|
| **Tobi — visible AI progress** | Ship Magic v2 + Sidekick for all merchants + 1 merchant agent in 12 months; shared eval harness; cap on the cost per AI feature |
| **CFO — burn discipline** | Cut $XM in non-AI capex; defer 1-2 non-AI projects; consolidate 2 internal systems; prove ROI per AI feature |
| **CTO — platform consolidation** | Build the cross-BU platform team (10 FTE) with 5 platform hires, 3 governance, 1 chief of staff, 1-2 data PMs. Pod leads held accountable in scorecards. |

**Trade-offs (7 min).**
- Tobi gives up: open-ended AI cadence → 12-month cap with 3 ships; cost-per-feature cap.
- CFO gives up: $20M ceiling → $XM with the cuts. Some capex growth remains; ROI must prove it.
- CTO gives up: 100% centralization → federated with contract. BU pods retain delivery ownership; the center owns the contract + the feature store.

**Asks (5 min).**
- Tobi: back the 12-month cap; defend the cost-per-feature discipline to the board.
- CFO: approve the capex cuts; back the ROI tracking.
- CTO: own the cross-BU platform team; sign off on the pod scorecards.

**Q&A — be ready for:**
- "What if Tobi wants Magic v3 too?" — We go with 1 merchant agent on top of the cadence. Scope is the trade-off.
- "What if the capex cuts slip?" — Phased plan; first $XM in 6 months, second $XM in 12.
- "What if a pod lead refuses the scorecard?" — Escalate to the CTO. The scorecard is non-negotiable.

## Watch for when you re-listen

- **Did you validate each C first?**
- **Did you reframe as joint problem?**
- **Did you name every trade-off?**
- **Did you end on time?**

---

**Source:** Adapted from original CS-07 + Shopify case-study brief.