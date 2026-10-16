# CS-01 (Stripe) — The 3-minute pitch to Emily Sands for Head of Data & AI

> **Mapping:** Original CS-01. Retargeted to Stripe's Head of Data & AI interview.
> **Goal:** 3 minutes. Convince Emily Sands in 30 seconds, defend in the next 2:30.

## The brief

You are in the final round for **Head of Data & AI at Stripe**. Emily Sands (current Head of Data & AI) walks you to a whiteboard. "You have 3 minutes. Tell me why you're the right person to lead data at Stripe. Then I have 10 minutes of follow-ups."

**What you have to do:**
- Open with the answer in 30 seconds
- Defend in the next 2:30 with the *Stripe-native* vocabulary
- Take 2–3 sharp follow-ups

**What you know about Emily's taste:**
- She came from marketing leadership; she values **clarity** and **commercial instinct** over jargon
- Stripe is a *written* culture; she'll want to see you can write
- She values **rigor** (financial systems; decimal drift kills)
- She is allergic to vendor-speak ("we use Snowflake / Databricks / Looker" is not an answer)
- She is the first Head of Data & AI to combine data + AI — she wants both

## Solution sketch (do not copy — internalize and re-speak)

**The 30-second opener (the only thing that matters).**
> "I'm a builder-operator who's led data + AI at $8B businesses. I'd lead Stripe data around three loops — the Radar ML flywheel, the platform flywheel, and the merchant-data-product loop. I'd do that by hiring a small platform team, setting the data contract standard, and shipping one merchant-visible AI product in my first 90 days."

Why this works:
- "Builder-operator" — operator, not consultant
- "$8B business" — sized to Stripe's scale (not "20 years of data")
- "Three loops" — Stripe vocabulary
- "Hiring a small platform team" — names the org shape in 5 words
- "One merchant-visible AI product in 90 days" — measurable, fast, visible

**The 2:30 defense (the supporting math).**

| Loops | What it is | What to ship in Y1 | What to ship in Y2 | What to ship in Y3 |
|---|---|---|---|---|
| **Radar ML flywheel** | More TPV → better fraud model → higher approvals → more TPV | Sub-50ms Radar decision on a refreshed feature store; reduce false-decline by `[CONFIRM: 5-10] bps` | ML-feature online store shared with smart-retries; +5% smart-retry revenue | Adaptive ML that learns per-merchant; first adversarial-robustness audit |
| **Platform flywheel** | More BUs on one substrate → more wallet share → more merchants | Data contracts across Payments/Billing/Connect/Issuing/Treasury/Radar; one metric model | Cross-BU merchant 360 in Sigma; first cross-BU data product (e.g. revenue + cash-flow in one view) | Embedded analytics SDK for merchant-facing dashboards |
| **Merchant data product loop** | Sigma + LLMs → merchants self-serve → lower CAC → more merchants | Sigma NL→SQL in beta; Stripe Assistant v1; first public-facing data product | Sigma 2.0 (NL→SQL is a feature, not the product); per-merchant anomaly detection | Merchant-facing AI agents (tax, fraud ops, cash-flow) |

**The 30-second closer.**
> "I'd hire a 10-person platform team, ship the cross-BU metric model in 6 months, and the first Stripe-owned data product in 12. I'd do that while keeping Radar within `[CONFIRM: sub-100ms / 99.9% availability]` SLO."

**Q&A — be ready for:**
- "Why Head of Data *and* AI?" — Because Radar IS data + AI. The boundary is artificial. The mandate is real.
- "What's your first 90 days?" — Listen (1:1 with each BU data lead, every Radar ML engineer, the ledger team, Emily herself). Read (the last 3 board memos, the Radar incident log, the Sigma roadmap). Ship (one merchant-visible AI product + the data contract standard).
- "How would you org the team?" — Platform (10 FTE) + BU-embedded data leads (federated). Hub-and-spoke Y1, federation Y2 if maturity is there.
- "What's a mistake you'd watch for?" — Trying to centralize too fast. The ledger team, the Radar team, and the Issuing team are not interchangeable. The platform team sets the contract; the BUs own delivery.
- "Show me a doc." — Bring a one-pager. Emily will read it. Written culture is a Stripe signal.

**The hidden checklist Emily is scoring against:**

| Signal | What she's looking for |
|---|---|
| Loop vocabulary | Did you say "flywheel" or "network effect" unprompted? |
| TPV not revenue | Did you size the business in TPV? |
| BU names | Did you name Payments / Billing / Connect? |
| Radar respect | Did you treat Radar as the crown jewel, not a side project? |
| First 90 days | Did you name a *measurable* ship target? |
| Written culture | Did you offer a doc? |

## Watch for when you re-listen

- **Did you open with the answer in 30 seconds?** The opener is the only thing Emily remembers.
- **Did you name the loops?** "Three loops" is the Stripe answer; "data strategy" is not.
- **Did you write the doc?** Bring a one-pager to the in-person. Emily will read it.
- **Did you end on time?** 3 minutes is 3 minutes. If you run over, the next question becomes a hostage.

---

**Source:** Adapted from original CS-01 + Stripe case-study brief.
