# CS-03 (Shopify) — Allocating a $20M annual data + AI budget across BUs

> **Mapping:** Original CS-03. Retargeted to Shopify's BU structure and ~$20M scale.
> **Goal:** 30 minutes. Defend the $20M allocation to the CFO (Jeff Hoffmeister) + Tobi + the BU ML leads.

## The brief

You are 60 days into the senior data/AI role. The CFO walks in: "We have $20M for data + AI platform in FY26. Show me the allocation, the ROI, and the trade-offs. Tobi wants Magic to win; the BU leads want their pods unblocked. I need this by Friday."

**What you know:**
- Shopify is public; the CFO is accountable to Wall Street
- Magic is the merchant-facing AI product; the brand
- Logistics + Capital are growth bets
- Shop Pay is the consumer trust surface
- The CFO respects rigor; the right answer is *defensible math*, not narrative

**Your task:** Allocate $20M. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**The 10-number dashboard (5 min).**

| # | Metric | Shopify target / current | Why it matters |
|---|---|---|---|
| 1 | GMV 2024 | $292B | The merchant-network size |
| 2 | Magic adoption | `[CONFIRM]` | The merchant-AI penetration |
| 3 | Capital underwriting accuracy | `[CONFIRM]` | The lending-ML ROI |
| 4 | Logistics cost per order | `[CONFIRM]` | The SFN ROI |
| 5 | Shop Pay fraud rate | `[CONFIRM]` | The consumer-trust SLO |
| 6 | Plus merchant count | `[CONFIRM]` | The enterprise growth |
| 7 | Cross-BU data contracts | 0 today | The platform maturity |
| 8 | Data + ML headcount | `[CONFIRM: ~150-250]` | The org size |
| 9 | Cloud spend as % revenue | `[CONFIRM]` | The FinOps signal |
| 10 | Magic cost per query | `[CONFIRM]` | The AI unit-economics SLO |

**The allocation (10 min).**

| Bucket | $M | % | What it buys | The ROI |
|---|---|---|---|---|
| **Magic AI platform** | 6 | 30% | Sidekick in production, semantic search, merchant agent runtime, Magic eval harness | `[CONFIRM: 50% merchant adoption; +X% GMV]` |
| **Cross-BU ML feature store** | 4 | 20% | Shared feature store, online + offline, data contracts | 6 BUs unblocked; 1 engineer week saved per pod per quarter |
| **Logistics ML** | 2.5 | 12.5% | SFN routing, inventory placement, demand forecasting | `[CONFIRM: -X% logistics cost per order]` |
| **Capital ML** | 1.5 | 7.5% | Merchant underwriting v2, real-time decisioning | `[CONFIRM: -X% default rate; +X% originations]` |
| **Shop Pay fraud + rewards** | 2 | 10% | Shop Pay fraud ML v2, Shop Pay rewards ML | `[CONFIRM: -X bps fraud; +X% Shop Pay adoption]` |
| **AI platform (LLM, RAG, agents)** | 2 | 10% | LLM serving, RAG infra, agent runtime, eval harness | `[CONFIRM: 1-2 merchant-facing AI products in Y1]` |
| **Governance, security, privacy** | 1.5 | 7.5% | SOC2, PCI-DSS, model risk, data quality scorecard | Risk reduction |
| **Engineering productivity** | 0.5 | 2.5% | DevEx, CI/CD for data, FinOps dashboards | `[CONFIRM: 20% reduction in data engineer toil]` |

**Total: $20M.**

**The trade-offs (7 min).**
- **Trade-off 1:** Magic gets the largest single bucket because the merchant network loop is the moat. But Magic's existing team is strong; the $6M is *incremental* platform investment, not headcount.
- **Trade-off 2:** Logistics gets $2.5M despite the 2023 downsizing because the SFN ML is a *prerequisite* for the SFN business to scale. The data team is small; the investment is targeted.
- **Trade-off 3:** Capital gets $1.5M, not $3M, because the Capital ML team is small and the *unit economics* are already strong. The $1.5M is for real-time underwriting, not for headcount.
- **Trade-off 4:** Shop Pay gets $2M, not $4M, because Shop Pay fraud is in production and the marginal ML investment is small. The $2M is for Shop Pay rewards + the consumer-network play.
- **Trade-off 5:** AI platform gets $2M, not $5M, because Shopify is not a foundation-model play. The right answer is "we use providers + we build the eval harness + we build the merchant-facing products." $5M would be vendor lock-in.

**The ROI math (5 min).**
- Magic 50% adoption × `[CONFIRM: 2M merchants]` × `[CONFIRM: +X% GMV]` = `[CONFIRM: $X]M GMV`
- Logistics -X% cost per order × `[CONFIRM: $Y orders]` = `[CONFIRM: $Z]M`
- Capital -X% default rate × `[CONFIRM: $A originations]` = `[CONFIRM: $B]M`
- Shop Pay -X bps fraud × `[CONFIRM: $C TPV]` = `[CONFIRM: $D]M`
- Cross-BU feature store: soft savings = `[CONFIRM: 1 engineer week saved per pod per quarter]`
- Total: $20M in, `[CONFIRM: $XM]` in *measurable* GMV / cost / fraud savings in Y1

**Q&A — be ready for:**
- "Why is Magic 30%?" — Because the merchant network loop is the moat. A 50% Magic adoption is `[CONFIRM: $X]M GMV`. The math is the math.
- "Why is Logistics 12.5% after the 2023 downsizing?" — Because the SFN ML is a *prerequisite* for the SFN business to scale. The 2023 call was about the *fulfillment operations*, not the ML.
- "What if Magic adoption is below 50%?" — Then the $6M drops to $3M in Y2; the budget is not sacred.
- "What if a BU cuts its headcount?" — The cross-BU data contract is the prerequisite; if a BU cuts data headcount, the BU also cuts its feature velocity. The platform team picks up the slack; the BU loses velocity.
- "What gets cut if the budget is $15M?" — AI platform and Capital get cut first. Magic and cross-BU stay.

**The CFO's hidden checklist:**

| Signal | What the CFO is scoring |
|---|---|
| GMV math | Did you size in GMV? |
| ROI per $ | Did you defend every $1M with a number? |
| Trade-offs named | Did you say "we cut X to fund Y"? |
| Magic respected | Did you treat Magic as the moat? |
| Off-ramp | Did you name what gets cut if the budget shrinks? |

## Watch for when you re-listen

- **Did you open with the 10-number dashboard?** Numbers first, allocation second.
- **Did you defend every bucket with math?**
- **Did you name the cuts if the budget shrinks?**
- **Did you end on time?** The CFO is busy.

---

**Source:** Adapted from original CS-03 + Shopify case-study brief.
