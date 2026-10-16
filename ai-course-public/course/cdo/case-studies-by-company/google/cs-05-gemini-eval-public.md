# CS-05 (Google) — A bad Gemini eval result goes public during quarterly earnings

> **Mapping:** Original CS-05 (margin incident). Retargeted to a model-failure public-disclosure scenario.
> **Goal:** 30 minutes. Walk the recovery from a public Gemini eval failure during Alphabet's Q3 earnings call.

## The brief

You are 10 minutes into Alphabet's Q3 earnings call. The CFO is presenting. A reporter on the call asks: "We saw `[CONFIRM: a public benchmark / a customer report / a paper]` showing Gemini 2.5 `[CONFIRM: failed / regressed / was biased]` on `[CONFIRM: specific test]`. How is Google responding?" Pichai defers to the Head of Data. The Head of Data is you.

**You have 30 minutes to:**
- Acknowledge the disclosure (in the room, in real time, on the call)
- Investigate the cause
- Communicate the resolution
- Defend the recovery

## The structure (30 min)

| Section | Time | What to say |
|---|---|---|
| Acknowledge | 2 min | On the call, immediately |
| Investigate | 8 min | Pull the eval data; find the discrepancy; identify the cause |
| Communicate | 5 min | What the right eval result is, why it was wrong, who's accountable |
| Remediate | 10 min | What you'll do in the next 24h, 1 week, 1 month |
| Defend | 5 min | Take questions from Pichai / Kurian / Hassabis / the reporter |

## Solution sketch (do not copy — internalize and re-speak)

**Acknowledge (2 min).**
- "Thanks for the question. The benchmark is `[CONFIRM]`. We've seen the report. We are running a full investigation. I'll come back with a written response within `[CONFIRM: 48h / 1 week]`."
- (Do not defend. Do not deflect. Acknowledge and commit.)

**Investigate (8 min).**
- Pull the eval data from the Vertex Model Registry
- Compare the public benchmark to the internal eval
- Find the discrepancy: likely one of —
  - Eval prompt template drift (the public benchmark used a template the model wasn't trained on)
  - Pre/post tuning regression (Gemini 2.5 tuning improved one benchmark, regressed another)
  - Test set contamination (the benchmark is in the training data; the score is inflated)
  - Eval harness bug (the scoring code has an error)
- Identify the root cause with a single source of truth

**Communicate (5 min).**
- Return to the call / publish a blog post within 24h
- "The correct result is `[X]`. The discrepancy was caused by `[Y]`. The model is `[within SLO / requires re-eval / requires rollback]`."
- "This is my accountability. The eval harness is the data team's responsibility. The cause is `[root cause]`."
- (Do not blame DeepMind. Do not blame the benchmark authors. Own the eval.)

**Remediate (10 min):**
- **24h:** Publish a public response; brief Pichai and Kurian; pause the affected model version if material
- **1 week:** Fix the eval harness; add the benchmark to the CI/CD; rerun the full eval suite
- **1 month:** Implement a model registry with continuous eval; add bias + safety checks for every release; quarterly transparency report
- **Quarterly:** Add model evals to the board reporting cadence

**Defend (5 min) — be ready for:**
- "How did this get through?" — the CI/CD had a gap. Fix: continuous eval in CI.
- "Who is accountable?" — me; the eval harness is the data team's responsibility.
- "How do we prevent this from happening again?" — model registry + continuous eval + transparency report.
- "Is Gemini 2.5 safe to ship?" — the affected capability is `[CONFIRM]`; the rest of the model is within SLO. We're rolling forward with the unaffected capabilities and re-evaluating the affected one.

## Watch for when you re-listen

- **Did you acknowledge in the first 2 minutes?** Defensiveness kills trust. The room is watching.
- **Did you own it?** "My accountability" — the data team owns the eval.
- **Did you name the root cause, not the symptom?** "The eval harness had a bug" is a symptom. "The eval harness had a bug because the CI/CD didn't include the benchmark template" is a root cause.
- **Did you end on time?** Running over signals you can't manage a crisis.

---

**Source:** Adapted from original CS-05 + Google case-study brief.