# CS-05 (Amazon) — A public Q hallucination incident goes viral on X during re:Invent

> **Mapping:** Original CS-05. Retargeted to Amazon's Q hallucination scenario during re:Invent.
> **Goal:** 30 minutes. Walk the recovery from a public Q hallucination incident that goes viral on X during re:Invent.

## The brief

You are 10 minutes into a re:Invent keynote. Adam Selipsky (or Matt Garman) is presenting Q for Business. A developer in the room tweets: "@AWS Q just told me to delete my production S3 bucket to 'optimize costs.' Why is AWS shipping LLM hallucinations to enterprise customers?" The tweet gets 8,000 RTs in 30 minutes. The Q lead is backstage. The senior data/AI lead is you.

**You have 30 minutes to:**
- Acknowledge the disclosure (publicly, in real time)
- Investigate the cause
- Communicate the resolution
- Defend the recovery

## Solution sketch (do not copy — internalize and re-speak)

**Acknowledge (2 min).**
- "Thanks for the report. We've seen the screenshot. We're investigating. We'll publish a written response within `[CONFIRM: 24h]`."
- (Do not defend. Do not deflect. Acknowledge and commit.)
- (Do NOT publicly blame the developer. The developer is a *customer*; customer obsession is the brand.)

**Investigate (8 min).**
- Pull the Q conversation log for the affected developer
- Compare the model output to the eval harness results
- Find the likely root cause — usually one of:
  - Prompt injection (developer input had adversarial content)
  - Retrieval hallucination (RAG retrieved a stale AWS runbook)
  - Eval harness gap (the scenario wasn't in the eval set)
  - Tool-use failure (Q invoked the wrong AWS API)
  - Model drift (new model version rolled out 2 days ago)
- Identify the root cause with a single source of truth (Q decision log)

**Communicate (5 min).**
- "The correct response should have been `[a safety refusal + a docs link]`. The likely cause was `[Y]`. Q `[X.Y]` is `[within SLO / requires re-eval / requires rollback]`."
- "This is my accountability. The Q eval harness and the customer feedback loop are the data team's responsibility."
- (Do not blame the developer. Do not blame the model provider (Anthropic). Do not blame the model. Own the eval.)

**Remediate (10 min):**

| Timeframe | Action |
|---|---|
| **24h** | Publish a public response; brief Andy and the Q lead; pause the affected model version if material; direct outreach to the affected developer (offer to walk them through the correct docs) |
| **1 week** | Fix the eval harness; add the scenario to the eval set; rerun the full eval suite; review the last `[CONFIRM: 7 days]` of Q conversations for similar patterns |
| **1 month** | Implement a model registry with continuous eval; brand-voice + adversarial checks for every release; quarterly transparency report; customer feedback loop v2 (every customer can flag a Q response) |
| **Quarterly** | Add model evals to the AI leadership committee cadence; publish a "Q accuracy" report |

**Defend (5 min) — be ready for:**
- "How did this get through?" — The CI/CD had a gap. Fix: continuous eval in CI; customer-feedback as a first-class signal; tool-use sandboxing.
- "Who is accountable?" — Me; the eval harness and the feedback loop are the data team's responsibility. (LP: Ownership)
- "Is Q safe to ship?" — The affected capability is `[CONFIRM]`; the rest is within SLO.
- "What about the developer who tweeted?" — Public, direct, no-conditions outreach from the data team. Make them a customer of the next Q improvement. (LP: Customer Obsession + Earn Trust)
- "What about the 8,000 retweets?" — The reply is *one* high-quality response + one written post, not 8,000 individual replies. The signal is the answer, not the volume. (LP: Bias for Action)
- "What about the Anthropic partnership?" — The model is one input; the eval harness is the data team's responsibility. The Anthropic partnership does not change the accountability. (LP: Ownership + Have Backbone)

**The hidden checklist Andy (or the Bar Raiser) is scoring:**

| LP | What they're scoring |
|---|---|
| **Customer Obsession** | Did you reach out to the affected developer directly? |
| **Ownership** | Did you say "my accountability"? |
| **Dive Deep** | Did you name the root cause, not the symptom? |
| **Bias for Action** | Did you name the 24h / 1 week / 1 month cadence? |
| **Have Backbone** | Did you push back on the "blame the model" narrative? |
| **Earn Trust** | Did you name a self-critical moment? |
| **Insist on the Highest Standards** | Did you name the eval harness fix? |

## Watch for when you re-listen

- **Did you acknowledge in the first 2 minutes?** Defensiveness kills trust.
- **Did you own it?** "My accountability" — the data team owns the eval.
- **Did you name the root cause, not the symptom?**
- **Did you say "Dive Deep" or "Ownership"?** These are the cultural answers.

---

**Source:** Adapted from original CS-05 + Amazon case-study brief.