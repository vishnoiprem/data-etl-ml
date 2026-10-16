# CS-05 (Stripe) — A public Radar false-decline incident hits Twitter during a Stripe Sessions keynote

> **Mapping:** Original CS-05. Retargeted to Stripe's Radar fraud ML + a Stripe Sessions keynote scenario.
> **Goal:** 30 minutes. Walk the recovery from a public Radar false-decline incident that trends on Twitter during a Stripe Sessions talk.

## The brief

You are 10 minutes into Stripe Sessions. Patrick is on stage presenting "the future of payments." A developer in the room tweets: "@stripe Radar just declined my $5K payment for a 3-year customer with 200 prior successful transactions. False decline. Why are you letting ML kill my conversion?" The tweet gets 2,000 RTs in 15 minutes. The Radar lead is backstage. The Head of Data & AI is you.

**You have 30 minutes to:**
- Acknowledge the disclosure (on stage, in real time)
- Investigate the cause
- Communicate the resolution
- Defend the recovery

## Solution sketch (do not copy — internalize and re-speak)

**Acknowledge (2 min).**
- "Thanks for the report. We've seen the tweet. We're investigating. We'll publish a written response within `[CONFIRM: 24h]`."
- (Do not defend. Do not deflect. Acknowledge and commit.)
- (Do NOT go on stage and argue with the customer. Patrick should say: "Our data team owns this. Emily and team are on it.")

**Investigate (8 min).**
- Pull the Radar decision for the specific transaction (BIN, amount, IP, device, merchant history)
- Compare to the customer's prior 200 transactions (which features changed?)
- Find the likely root cause — usually one of:
  - BIN-level rule change (new BIN, low history)
  - Device fingerprint anomaly (new device, new IP, no 3DS history)
  - Velocity rule triggered (3 attempts in 10 min)
  - Model drift (Radar model rolled out 2 days ago)
  - Merchant-level rule that the merchant forgot they enabled
- Identify the root cause with a single source of truth (Radar decision log)

**Communicate (5 min).**
- "The correct decision should have been `[approved / reviewed]`. The likely cause was `[Y]`. Radar `[X.Y]` is `[within SLO / requires re-eval / requires rollback]`."
- "This is my accountability. The Radar model and the merchant feedback loop are the data team's responsibility."
- (Do not blame the merchant. Do not blame the developer who tweeted. Do not blame the BIN. Own the model.)

**Remediate (10 min):**

| Timeframe | Action |
|---|---|
| **24h** | Publish a public response; brief Patrick and Emily; pause the affected model version if material; direct outreach to the affected merchant |
| **1 week** | Fix the model; add the scenario to the eval harness; rerun the full eval suite; merchant-level review of the last `[CONFIRM: 7 days]` of declines |
| **1 month** | Implement a model registry with continuous eval; bias + adversarial checks for every release; quarterly transparency report; merchant feedback loop v2 (every decline is a data point the merchant can label) |
| **Quarterly** | Add model evals to the AI leadership committee cadence; publish a "Radar accuracy" report |

**Defend (5 min) — be ready for:**
- "How did this get through?" — The CI/CD had a gap. Fix: continuous eval in CI; merchant-feedback as a first-class signal.
- "Who is accountable?" — Me; the Radar model and the feedback loop are the data team's responsibility.
- "Is Radar safe to ship?" — The affected capability is `[CONFIRM]`; the rest is within SLO.
- "What about the developer who tweeted?" — Public, direct, no-conditions outreach from the data team. Make them a customer of the next Radar improvement.
- "What about the 2,000 retweets?" — The reply is *one* high-quality response + one written post, not 2,000 individual replies. The signal is the answer, not the volume.

**The hidden checklist Patrick is scoring:**

| Signal | What Patrick is scoring |
|---|---|
| Acknowledge fast | Did you commit to a written response in 24h? |
| Own it | Did you say "my accountability"? |
| Root cause | Did you name the cause, not the symptom? |
| Merchant-first | Did you reach out to the affected merchant directly? |
| Cadence | Did you name the 24h / 1 week / 1 month / quarterly cadence? |

## Watch for when you re-listen

- **Did you acknowledge in the first 2 minutes?** Defensiveness kills trust.
- **Did you own it?** "My accountability" — the data team owns the model.
- **Did you name the root cause, not the symptom?**
- **Did you end on time?**

---

**Source:** Adapted from original CS-05 + Stripe case-study brief.
