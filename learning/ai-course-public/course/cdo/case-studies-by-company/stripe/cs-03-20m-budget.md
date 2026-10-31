# CS-03 (Stripe) — Allocating a $20M annual data platform budget across BUs

> **Mapping:** Original CS-03. Retargeted to Stripe's BU structure and ~$20M scale.
> **Goal:** 30 minutes. Defend the $20M allocation to the CFO + Emily + the BU data leads.

## The brief

You are 60 days into the Head of Data Platform role. The CFO walks in: "We have $20M for data platform in FY26. Show me the allocation, the ROI, and the trade-offs. The board wants AI; Patrick wants Radar to keep winning; the BU leads want their pods unblocked. I need this by Friday."

**What you know:**
- Stripe is private; the CFO is the only budget gate
- Radar ML is the single largest ML revenue lever
- Sigma is the merchant-facing data product
- Issuing + Treasury are growth bets; Payments is the cash cow
- The CFO respects rigor; the right answer is *defensible math*, not narrative

**Your task:** Allocate $20M. Defend in 30 minutes.

## Solution sketch (do not copy — internalize and re-speak)

**The 10-number dashboard (5 min).**

| # | Metric | Stripe target / current | Why it matters |
|---|---|---|---|
| 1 | TPV 2024 | $1.4T | The size of the business |
| 2 | Radar false-decline rate | `[CONFIRM: current bps]` | Every 1 bp = 10s of $M |
| 3 | Smart-retry revenue lift | +10.5% (2022 baseline) | The ML revenue lever |
| 4 | Sigma NL→SQL adoption | `[CONFIRM]` | The merchant data product wedge |
| 5 | Issuing + Treasury GMV | `[CONFIRM]` | The growth bets |
| 6 | Cross-BU data contracts | 0 today | The platform maturity |
| 7 | Data headcount | `[CONFIRM: ~120-180]` | The org size |
| 8 | Cloud spend as % revenue | `[CONFIRM]` | The FinOps signal |
| 9 | Ledger availability | 99.99%+ (assumed) | The crown jewel SLO |
| 10 | Radar decision latency | sub-100ms | The real-time ML SLO |

**The allocation (10 min).**

| Bucket | $M | % | What it buys | The ROI |
|---|---|---|---|---|
| **Radar ML platform** | 6 | 30% | Online feature store, model registry, eval harness, adversarial-robustness tooling | False-decline -5 bps = `[CONFIRM: $X]M revenue saved` |
| **Cross-BU data platform** | 4 | 20% | Data contracts, semantic layer, lineage, observability | 5 BUs unblocked; 1 engineer week saved per pod per quarter |
| **Sigma + merchant data product** | 3 | 15% | Sigma NL→SQL in GA, per-merchant anomaly detection, Stripe Assistant v1 | `[CONFIRM: 1K → 10K] merchants; CAC reduction` |
| **Issuing + Treasury data** | 2 | 10% | Issuing ML (credit decisioning, spend mgmt), Treasury analytics, Financial Connections data | Growth bet ROI; `[CONFIRM: 18-24 month payback]` |
| **AI platform (LLM, RAG, agents)** | 2 | 10% | LLM serving, RAG infra, agent runtime, eval harness | `[CONFIRM: 1-2 merchant-facing AI products in Y1]` |
| **Governance, security, privacy** | 1.5 | 7.5% | SOC2, PCI-DSS, BSA/AML data, model risk, data quality scorecard | Risk reduction; `[CONFIRM: 30% reduction in audit findings]` |
| **Engineering productivity** | 1 | 5% | DevEx, CI/CD for data, FinOps dashboards | `[CONFIRM: 20% reduction in data engineer toil]` |
| **Buffer / hiring lag** | 0.5 | 2.5% | Reserve for 2-3 senior hires | Strategic optionality |

**Total: $20M.**

**The trade-offs (7 min).**
- **Trade-off 1:** Radar gets the largest single bucket because the ML revenue lever is the largest. But Radar's existing team is strong; the $6M is *incremental* platform investment, not headcount.
- **Trade-off 2:** Issuing + Treasury get $2M despite being growth bets because the data product for Issuing (credit decisioning) and Treasury (cash-flow analytics) is a *prerequisite* for the BU to scale.
- **Trade-off 3:** Sigma gets $3M, not $5M, because Sigma is a product, not a platform; the platform work is in the cross-BU bucket. The $3M is for product, not infrastructure.
- **Trade-off 4:** AI platform gets $2M, not $5M, because Stripe is not a foundation-model play. The right answer is "we use providers + we build the eval harness + we build the merchant-facing products." $5M would be vendor lock-in.
- **Trade-off 5:** Governance gets $1.5M, not $3M, because the *Radar model risk* is in the Radar bucket, not governance. Governance owns the *framework*; the BU owns the *implementation*.

**The ROI math (5 min).**
- Radar -5 bps false-decline × $1.4T TPV × `[CONFIRM: take rate ~2.9%]` = `[CONFIRM: $X]M revenue`
- Sigma +1K merchants × `[CONFIRM: $XM ARPU]` = `[CONFIRM: $YM]M revenue`
- Issuing + Treasury data product = `[CONFIRM: 18-24 month payback]`
- Cross-BU data contracts: `[CONFIRM: 1 engineer week saved per pod per quarter]` = `[CONFIRM: 5 pods × 1 week × $X]` = soft savings
- Total: $20M in, `[CONFIRM: $XM]` in *measurable* revenue + soft savings in Y1

**Q&A — be ready for:**
- "Why is Radar 30%?" — Because the ML flywheel is the moat. A 5 bp false-decline reduction is `[CONFIRM: $X]M`. The math is the math.
- "Why is Sigma only 15%?" — Sigma is a product, not a platform. The platform work is in cross-BU. $3M is product headcount + NL→SQL.
- "What if Radar's ML plateaus?" — Then the $6M drops to $3M in Y2; the budget is not sacred.
- "What if a BU cuts its headcount?" — The cross-BU data contract is the prerequisite; if a BU cuts data headcount, the BU also cuts its feature velocity. The platform team picks up the slack; the BU loses velocity.
- "What gets cut if the budget is $15M?" — AI platform and Issuing + Treasury data get cut first. Radar and cross-BU stay.

**The CFO's hidden checklist:**

| Signal | What the CFO is scoring |
|---|---|
| TPV math | Did you size in TPV? |
| ROI per $ | Did you defend every $1M with a number? |
| Trade-offs named | Did you say "we cut X to fund Y"? |
| Radar respected | Did you treat Radar as the moat? |
| Off-ramp | Did you name what gets cut if the budget shrinks? |

## Watch for when you re-listen

- **Did you open with the 10-number dashboard?** Numbers first, allocation second.
- **Did you defend every bucket with math?**
- **Did you name the cuts if the budget shrinks?**
- **Did you end on time?** The CFO is busy.

---

**Source:** Adapted from original CS-03 + Stripe case-study brief.
