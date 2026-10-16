# CS-05 (Meta) — A bad Llama 4 eval result goes public during a developer event

> **Mapping:** Original CS-05. Retargeted to Meta's Llama 4 launch scenario.
> **Goal:** 30 minutes. Walk the recovery from a public Llama 4 eval failure during the LlamaCon developer event.

## The brief

You are 10 minutes into LlamaCon. Alexandr Wang (CAIO) is presenting Llama 4. A developer in the room asks: "We ran Llama 4 on `[CONFIRM: a public benchmark like MMLU / HumanEval / GSM8K]` and got `[CONFIRM: a regression / a bias finding]`. How is Meta responding?" Wang defers to the Director of Data. The Director of Data is you.

**You have 30 minutes to:**
- Acknowledge the disclosure (in the room, on stage, in real time)
- Investigate the cause
- Communicate the resolution
- Defend the recovery

## Solution sketch (do not copy — internalize and re-speak)

**Acknowledge (2 min).**
- "Thanks for the question. The benchmark is `[CONFIRM]`. We've seen the report. We're running a full investigation. We'll publish a written response within `[CONFIRM: 48h]`."
- (Do not defend. Do not deflect. Acknowledge and commit.)

**Investigate (8 min).**
- Pull the eval data from the Llama 4 model registry
- Compare the public benchmark to the internal eval
- Find the discrepancy: likely —
  - Eval prompt template drift
  - Pre/post tuning regression
  - Test set contamination
  - Eval harness bug
- Identify the root cause with a single source of truth

**Communicate (5 min).**
- "The correct result is `[X]`. The discrepancy was caused by `[Y]`. Llama 4 `[X.Y]` is `[within SLO / requires re-eval / requires rollback]`."
- "This is my accountability. The eval harness is the data team's responsibility."
- (Do not blame MSL. Do not blame the benchmark authors. Own the eval.)

**Remediate (10 min):**
- **24h:** Publish a public response; brief Wang and Schultz; pause the affected model version if material
- **1 week:** Fix the eval harness; add the benchmark to the CI/CD; rerun the full eval suite
- **1 month:** Implement a model registry with continuous eval; bias + safety checks for every release; quarterly transparency report
- **Quarterly:** Add model evals to the AI leadership committee cadence

**Defend (5 min) — be ready for:**
- "How did this get through?" — the CI/CD had a gap. Fix: continuous eval in CI.
- "Who is accountable?" — me; the eval harness is the data team's responsibility.
- "Is Llama 4 safe to ship?" — the affected capability is `[CONFIRM]`; the rest is within SLO.

## Watch for when you re-listen

- **Did you acknowledge in the first 2 minutes?** Defensiveness kills trust.
- **Did you own it?** "My accountability" — the data team owns the eval.
- **Did you name the root cause, not the symptom?**
- **Did you end on time?**

---

**Source:** Adapted from original CS-05 + Meta case-study brief.