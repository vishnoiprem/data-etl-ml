# CS-05 (Shopify) — A public Sidekick hallucination incident goes viral on X

> **Mapping:** Original CS-05. Retargeted to Shopify's Sidekick hallucination scenario.
> **Goal:** 30 minutes. Walk the recovery from a public Sidekick hallucination incident that goes viral on X.

## The brief

A merchant tweets a screenshot: "@Shopify Sidekick just told me to delete my entire product database to 'optimize' my store. I lost 3 years of products. Why are you shipping LLM hallucinations to merchants?" The tweet gets 5,000 RTs in 2 hours. The Magic lead is in a board meeting. The senior data/AI lead is you.

**You have 30 minutes to:**
- Acknowledge the disclosure (publicly, in real time)
- Investigate the cause
- Communicate the resolution
- Defend the recovery

## Solution sketch (do not copy — internalize and re-speak)

**Acknowledge (2 min).**
- "Thanks for the report. We've seen the screenshot. We're investigating. We'll publish a written response within `[CONFIRM: 24h]`."
- (Do not defend. Do not deflect. Acknowledge and commit.)
- (Do NOT publicly blame the merchant. The merchant is the *customer*; merchant empathy is the brand.)

**Investigate (8 min).**
- Pull the Sidekick conversation log for the affected merchant
- Compare the model output to the eval harness results
- Find the likely root cause — usually one of:
  - Prompt injection (merchant input had adversarial content)
  - Retrieval hallucination (RAG retrieved a stale internal runbook)
  - Eval harness gap (the scenario wasn't in the eval set)
  - Tool-use failure (Sidekick invoked the wrong Shopify API)
  - Model drift (new model version rolled out 2 days ago)
- Identify the root cause with a single source of truth (Sidekick decision log)

**Communicate (5 min).**
- "The correct response should have been `[a safety refusal + a merchant-success link]`. The likely cause was `[Y]`. Sidekick `[X.Y]` is `[within SLO / requires re-eval / requires rollback]`."
- "This is my accountability. The Sidekick eval harness and the merchant feedback loop are the data team's responsibility."
- (Do not blame the merchant. Do not blame the developer who tweeted. Do not blame the model provider. Own the eval.)

**Remediate (10 min):**

| Timeframe | Action |
|---|---|
| **24h** | Publish a public response; brief Tobi and the Magic lead; pause the affected model version if material; direct outreach to the affected merchant (offer to restore the products from backup) |
| **1 week** | Fix the eval harness; add the scenario to the eval set; rerun the full eval suite; review the last `[CONFIRM: 7 days]` of Sidekick conversations for similar patterns |
| **1 month** | Implement a model registry with continuous eval; brand-voice + adversarial checks for every release; quarterly transparency report; merchant feedback loop v2 (every merchant can flag a Sidekick response) |
| **Quarterly** | Add model evals to the AI leadership committee cadence; publish a "Sidekick accuracy" report |

**Defend (5 min) — be ready for:**
- "How did this get through?" — The CI/CD had a gap. Fix: continuous eval in CI; merchant-feedback as a first-class signal; tool-use sandboxing.
- "Who is accountable?" — Me; the eval harness and the feedback loop are the data team's responsibility.
- "Is Sidekick safe to ship?" — The affected capability is `[CONFIRM]`; the rest is within SLO.
- "What about the merchant who tweeted?" — Public, direct, no-conditions outreach from the data team. Make them a customer of the next Sidekick improvement. *Restore their data first; investigate the legal side second.*
- "What about the 5,000 retweets?" — The reply is *one* high-quality response + one written post, not 5,000 individual replies. The signal is the answer, not the volume.

**The hidden checklist Tobi is scoring:**

| Signal | What Tobi is scoring |
|---|---|
| Acknowledge fast | Did you commit to a written response in 24h? |
| Own it | Did you say "my accountability"? |
| Merchant-first | Did you reach out to the affected merchant directly and offer to restore their data? |
| Root cause | Did you name the cause, not the symptom? |
| Cadence | Did you name the 24h / 1 week / 1 month / quarterly cadence? |

## Watch for when you re-listen

- **Did you acknowledge in the first 2 minutes?** Defensiveness kills trust.
- **Did you own it?** "My accountability" — the data team owns the eval.
- **Did you name the root cause, not the symptom?**
- **Did you say "merchant" not "customer"?** Tobi counts.

---

**Source:** Adapted from original CS-05 + Shopify case-study brief.