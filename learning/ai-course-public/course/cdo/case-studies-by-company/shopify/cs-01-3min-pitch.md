# CS-01 (Shopify) — The 3-minute pitch to Tobi for a senior data/AI role

> **Mapping:** Original CS-01. Retargeted to Shopify's senior data/AI interview.
> **Goal:** 3 minutes. Convince Tobi in 30 seconds, defend in the next 2:30.

## The brief

You are in the final round for a senior data/AI role at Shopify. Tobi walks in. "You have 3 minutes. Tell me why you're the right person. Then I have 10 minutes of follow-ups."

**What you have to do:**
- Open with the answer in 30 seconds
- Defend in the next 2:30 with the *Shopify-native* vocabulary
- Take 2–3 sharp follow-ups

**What you know about Tobi's taste:**
- He values **merchant empathy** above all
- He is **AI-forward** — the right answer makes AI concrete, not aspirational
- He is allergic to **vendor-speak** ("we use Snowflake / dbt / Looker" is not an answer)
- He respects **contrarian bets** and **reversibility** ("are you willing to kill a project if the data says so?")
- He is the founder; he thinks in **5–10-year windows**

## Solution sketch (do not copy — internalize and re-speak)

**The 30-second opener (the only thing that matters).**
> "I'm a builder-operator who's led data + AI at $8B businesses. I'd lead Shopify data around the merchant network loop — more merchants → better Magic, better Capital, better Logistics → more merchants. I'd do that by hiring a small platform team, setting the data contract standard, and shipping one merchant-visible AI product in my first 90 days."

Why this works:
- "Builder-operator" — operator, not consultant
- "$8B business" — sized to Shopify's scale
- "Merchant network loop" — Shopify vocabulary
- "Hiring a small platform team" — names the org shape in 5 words
- "One merchant-visible AI product in 90 days" — measurable, fast, visible

**The 2:30 defense (the supporting math).**

| Loop | What it is | What to ship in Y1 | What to ship in Y2 | What to ship in Y3 |
|---|---|---|---|---|
| **Merchant network loop** | More merchants → better Magic, Capital, Logistics → more merchants | Magic v2 (Sidekick in production for all merchants); semantic search at 175+ country scale; Capital underwriting on the shared feature store | Magic v3 (per-merchant fine-tuning); Capital v2 (real-time); Logistics ML v2 (routing) | Magic v4 (autonomous merchant agents); first $XM Magic-augmented GMV |
| **Plus / SMB loop** | Plus sets the bar → SMB gets the product → SMB upgrade to Plus | Plus data product (custom dashboards); Plus-specific ML (forecasting); Plus merchant copilot | Plus-SMB shared feature store; Plus churn prediction | Plus as a platform (the SaaS for large merchants) |
| **Shop Pay loop** | More Shop Pay users → faster checkout → more conversions → more Shop Pay users | Shop Pay fraud ML v2; Shop Pay rewards ML; cross-network Shop Pay | Shop Pay outside the Shopify network (the network play) | Shop Pay as a wallet (the Apple Pay competitor) |

**The 30-second closer.**
> "I'd hire a 10-person platform team, ship the cross-BU merchant metric model in 6 months, and the first merchant-visible AI product in 12. I'd do that while keeping Magic within `[CONFIRM: latency / cost per query]` SLOs."

**Q&A — be ready for:**
- "Why Shopify?" — Merchant empathy. I've spent my career building for end-users; Shopify is the only major platform that treats merchants as the *customer*, not the product.
- "What's your first 90 days?" — Listen (1:1 with every Magic engineer, the Logistics ML team, the Capital underwriting team, the Plus data lead, the merchant-facing product team). Read (Tobi's last 3 shareholder letters, the last 2 board memos, the Magic roadmap). Ship (one merchant-visible AI product + the data contract standard).
- "How would you org the team?" — Platform (10 FTE) + BU-embedded data leads (federated). Hub-and-spoke Y1, federation Y2 if maturity is there.
- "What's a mistake you'd watch for?" — Building Magic as a research project. Magic is a *merchant* product; if it doesn't make a merchant more money, it's wrong. The right test is "does the merchant keep using it?"
- "Are you willing to kill a project?" — Yes. The 2023 logistics downsizing was the right call. The data should drive the kill.

**The hidden checklist Tobi is scoring against:**

| Signal | What he's looking for |
|---|---|
| Loop vocabulary | Did you say "merchant network loop" unprompted? |
| GMV not revenue | Did you size the business in GMV? |
| Merchant-first | Did you say "merchant" instead of "customer"? |
| Magic + Sidekick | Did you name the AI products? |
| First 90 days | Did you name a *measurable* ship target? |
| Reversibility | Did you say you can kill a project? |

## Watch for when you re-listen

- **Did you open with the answer in 30 seconds?** The opener is the only thing Tobi remembers.
- **Did you name the loops?** "Merchant network loop" is the Shopify answer.
- **Did you say "merchant"?** Tobi counts.
- **Did you end on time?** 3 minutes is 3 minutes.

---

**Source:** Adapted from original CS-01 + Shopify case-study brief.
