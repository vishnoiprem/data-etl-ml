# CS-03 (Amazon) — Allocating a $100M annual data + AI budget across BUs

> **Mapping:** Original CS-03. Retargeted to Amazon's BU structure and ~$100M scale.
> **Goal:** 30 minutes. Defend the $100M allocation to the CFO (Brian Olsavsky) + Andy + the BU ML leads (Rufus, Bedrock, Q, Alexa, Ads, Supply Chain).

## The brief

You are 60 days into the senior data/AI role. The CFO walks in: "We have $100M for data + AI platform in FY26. Show me the allocation, the ROI, and the trade-offs. Andy wants Bedrock + Q + Rufus to win; the BU leads want their pods unblocked. I need this by Friday."

**What you know:**
- Amazon is public; the CFO is accountable to Wall Street
- AWS is the engine; Bedrock is the AI platform
- Retail is the scale; Rufus is the consumer-AI wedge
- Anthropic is the model partner; Trainium is the silicon
- The CFO respects rigor; the right answer is *defensible math*, not narrative
- The CFO has a $77B capex number on his desk; $100M is incremental *platform*, not the full AI infra capex

**Your task:** Allocate $100M. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**The 10-number dashboard (5 min).**

| # | Metric | Amazon target / current | Why it matters |
|---|---|---|---|
| 1 | Revenue 2024 | $638B | The business size |
| 2 | AWS revenue 2024 | $107.6B | The AWS engine |
| 3 | Capex 2024 | $77.7B (~$50B+ on AWS AI) | The AI investment |
| 4 | Rufus adoption | `[CONFIRM]` | The consumer-AI penetration |
| 5 | Bedrock customers | `[CONFIRM]` | The enterprise-AI penetration |
| 6 | Q adoption | `[CONFIRM]` | The enterprise-assistant penetration |
| 7 | Cross-segment data contracts | 0 today | The platform maturity |
| 8 | Data + ML headcount | `[CONFIRM: ~500-1,500]` | The org size |
| 9 | AI cost per query | `[CONFIRM]` | The AI unit-economics SLO |
| 10 | Anthropic model share on Bedrock | `[CONFIRM]` | The model-strategy signal |

**The allocation (10 min).**

| Bucket | $M | % | What it buys | The ROI |
|---|---|---|---|---|
| **Bedrock + Anthropic** | 30 | 30% | Bedrock FM marketplace; Anthropic partnership deepening; model eval harness | `[CONFIRM: +X% Bedrock customers; +X% AWS revenue]` |
| **Q (for Business / Developer / QuickSight)** | 20 | 20% | Q in production; Q eval harness; Q v2 (enterprise) | `[CONFIRM: +X enterprise customers; +X% AWS attach]` |
| **Rufus (consumer AI)** | 15 | 15% | Rufus v2 (purchase intent); Rufus v3 (conversational shopping) | `[CONFIRM: +X% retail conversion; +X% retail revenue]` |
| **Cross-segment ML feature store** | 10 | 10% | Shared feature store, online + offline, data contracts | 3 segments × 7+ BUs unblocked; 1 engineer week saved per pod per quarter |
| **Ads ML** | 5 | 5% | Sponsored products, sponsored brands, DSP ML v2 | `[CONFIRM: +X% ads revenue]` |
| **Supply chain + logistics ML** | 5 | 5% | Demand forecasting, inventory placement, last-mile routing | `[CONFIRM: -X% logistics cost per order]` |
| **Alexa LLM** | 5 | 5% | Next-gen Alexa; consumer-device ML | `[CONFIRM: +X% Alexa engagement]` |
| **AI platform (LLM, RAG, agents, Trainium)** | 5 | 5% | Trainium + Inferentia; LLM serving; RAG infra; agent runtime | `[CONFIRM: 1-2 customer-visible AI products in Y1]` |
| **Governance, security, privacy** | 3 | 3% | SOC2, FedRAMP, model risk, data quality scorecard | Risk reduction |
| **Engineering productivity** | 2 | 2% | DevEx, CI/CD for data, FinOps dashboards | `[CONFIRM: 20% reduction in data engineer toil]` |

**Total: $100M.**

**The trade-offs (7 min).**
- **Trade-off 1:** Bedrock + Anthropic gets the largest single bucket because the enterprise-AI flywheel is the AWS engine. But Bedrock is a *product*; the $30M is for the *platform* underneath, not the product itself.
- **Trade-off 2:** Q gets $20M, not $30M, because Q is the enterprise assistant; the *unit economics* are already strong. The $20M is for Q v2 enterprise + the eval harness.
- **Trade-off 3:** Rufus gets $15M, not $25M, because Rufus is the consumer wedge; the *unit economics* are still being proven. The $15M is for Rufus v2 (purchase intent) + the eval harness.
- **Trade-off 4:** Supply chain + logistics gets $5M, not $10M, because the supply chain ML is mature; the $5M is for last-mile routing + Scout.
- **Trade-off 5:** Alexa gets $5M, not $10M, because Alexa is the long-term bet; the 2023 downsizing was the right call. The $5M is for next-gen Alexa LLM, not for headcount.
- **Trade-off 6:** AI platform gets $5M, not $10M, because Amazon is not a foundation-model play (Anthropic is the partner). The $5M is for Trainium + Inferentia + LLM serving.

**The ROI math (5 min).**
- Bedrock +X% customers × `[CONFIRM: $X ARPU]` = `[CONFIRM: $Y]M AWS revenue`
- Q +X enterprise customers × `[CONFIRM: $X ARPU]` = `[CONFIRM: $Y]M AWS revenue`
- Rufus +X% retail conversion × `[CONFIRM: $Z retail revenue]` = `[CONFIRM: $W]M retail revenue`
- Ads +X% revenue × `[CONFIRM: $A ads revenue]` = `[CONFIRM: $B]M`
- Cross-segment feature store: soft savings = `[CONFIRM: 1 engineer week saved per pod per quarter]`
- Total: $100M in, `[CONFIRM: $XM]` in *measurable* revenue in Y1

**Q&A — be ready for:**
- "Why is Bedrock + Anthropic 30%?" — Because the enterprise-AI flywheel is the AWS engine. A +X% Bedrock customer count is `[CONFIRM: $Y]M`. The math is the math.
- "Why is Alexa only 5% after the 2023 downsizing?" — Because Alexa is the long-term bet; the 2023 call was the right call. The $5M is for next-gen Alexa LLM, not for headcount.
- "What if Anthropic goes to Microsoft?" — Then the $30M drops to $15M in Y2; the model-strategy shifts. The Bedrock marketplace is the hedge.
- "What if a BU cuts its headcount?" — The cross-segment data contract is the prerequisite; if a BU cuts data headcount, the BU also cuts its feature velocity. The platform team picks up the slack; the BU loses velocity.
- "What gets cut if the budget is $75M?" — Alexa and supply chain get cut first. Bedrock + Q stay.

**The CFO's hidden checklist:**

| Signal | What the CFO is scoring |
|---|---|
| Flywheel math | Did you size in flywheels? |
| ROI per $ | Did you defend every $10M with a number? |
| Trade-offs named | Did you say "we cut X to fund Y"? |
| Bedrock respected | Did you treat Bedrock as the moat? |
| Off-ramp | Did you name what gets cut if the budget shrinks? |

## Watch for when you re-listen

- **Did you open with the 10-number dashboard?** Numbers first, allocation second.
- **Did you defend every bucket with math?**
- **Did you name the cuts if the budget shrinks?**
- **Did you end on time?** The CFO is busy.

---

**Source:** Adapted from original CS-03 + Amazon case-study brief.