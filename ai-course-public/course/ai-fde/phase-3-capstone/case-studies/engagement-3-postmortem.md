# Case Study 3 — Postmortem: the week-11 hallucination incident

> **TL;DR (1 page).** On a Wednesday at 14:23 SGT, the PacificFreight
> drafter emitted 4 hallucinated drafts in 12 minutes. Mei reverted
> all 4. I rolled back the deploy within 22 minutes. The cause was
> a prompt change that bypassed the circuit breaker. The fix was
> a CI gate that runs the eval set on every PR. **The lesson:**
> incidents are inevitable. The recovery time is what matters.
> The eval-driven iteration cadence is what makes recovery cheap.

---

## Timeline (all times SGT)

- **14:23** — Mei reports "draft for PF-1002 says it's delivered in
  HCMC; the customer says it's still in Singapore." She reverts
  the draft and pings Daniel.
- **14:25** — Daniel opens the eval set, runs it against the
  current deploy. **Faithfulness is 0.61** (down from 0.94 on
  Monday's iteration report).
- **14:31** — Daniel reverts the deploy to the previous version
  (the one that ran at 09:00 today).
- **14:33** — Eval re-run shows faithfulness back to 0.94.
  Daniel confirms with Mei: "the bad drafts are gone."
- **14:38** — Mei reports 3 more hallucinations in the past 12
  minutes (drafts PF-1004, PF-1006, PF-1008 all said the
  shipments were "in HCMC" when they were actually in Singapore).
- **14:45** — I (the FDE) am paged. I look at the deploy diff:
  the only change was a 12-character prompt edit ("in HCMC" →
  "in Ho Chi Minh City").
- **14:50** — Root cause identified: the prompt change bypassed
  the circuit breaker. The breaker was tripped for 2 minutes
  during the deploy (normal), but the new prompt went live before
  the breaker recovered. The hallucinated drafts were generated
  by the old model with the new prompt — a combination that
  hadn't been tested.
- **14:53** — Hotfix: revert the prompt, re-run the eval set,
  re-deploy.
- **15:01** — Eval green. Mei confirms no more hallucinations.

**Total recovery time: 38 minutes.** Total customer impact: 4
drafts, all reverted by Mei before sending.

## Root cause

The deploy pipeline was:

```
PR merged → CI runs unit tests → build image → deploy to VM
            ↳ (eval set NOT run here)
```

The eval set was run **manually** every Monday at 09:00 SGT as
part of the iteration cadence. The deploy pipeline didn't
include it.

On Wednesday at 14:20, I merged a PR that changed the prompt
("in HCMC" → "in Ho Chi Minh City" — a copy edit I was making
for Mei because she prefers the longer form). The change
passed the unit tests (the drafter's tests don't exercise the
prompt). The image was built and deployed.

The new prompt + the old model + the bypassed breaker = the
hallucinations. The "in Ho Chi Minh City" string confused the
model's entity linking: it started treating "Singapore" as a
fallback destination for any shipment whose actual destination
was unclear. (4 shipments had unclear destinations that day
because of a customs system outage that Daniel wasn't aware
of yet.)

## What went well

- **Mei noticed within 2 minutes.** She'd been trained to
  re-read every draft before sending; the re-read caught the
  hallucination.
- **Daniel had the eval set ready to run.** The eval set is
  the spec; without it, the rollback would have been a guess.
- **The rollback took 22 minutes** (from Mei's report to
  the deploy being reverted). That's well under the 60-minute
  SLO in the runbook.

## What went poorly

- **The eval set wasn't in the CI pipeline.** If it had been,
  the PR would have failed CI before merge. The hallucination
  wouldn't have happened.
- **The bypassed circuit breaker was the mechanism.** The
  breaker is supposed to catch quality drops. It didn't,
  because it was tripped during the deploy and recovered
  before the new prompt was actually exercised.
- **The customer impact was 4 drafts.** Even though all 4
  were reverted, the customer (Mei) lost 12 minutes of trust.
  She's still a little more cautious about the drafter than
  she was before.

## Action items

| Owner | Action | Deadline |
|---|---|---|
| FDE | Move the eval set into CI (run on every PR, fail if any metric drops > 0.05) | EOW (Friday) |
| FDE | Add a "deploy window" check (don't deploy between 14:00-16:00 SGT, Mei's peak) | EOW |
| Daniel | Add a breaker-exercised-after-deploy hook (force 1 draft through after each deploy, log the faithfulness) | EONM (next Monday) |
| Mei | Re-read the runbook, refresh the rollback procedure | EOM |
| FDE | Write a public postmortem (this document) | Today |

## The fix (the eval set in CI)

```yaml
# .github/workflows/eval.yml
name: eval-set
on: [pull_request]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r service/requirements.txt
      - run: cd service && python3 eval.py --set ../shared/eval_set.jsonl --report eval_report.md
      - uses: actions/upload-artifact@v4
        with: { name: eval-report, path: service/eval_report.md }
      - run: |
          # Fail if any metric dropped by > 0.05 vs the baseline
          python3 eval.py --set ../shared/eval_set.jsonl \
                         --baseline ../shared/baseline.jsonl \
                         --threshold 0.05 \
                         --report eval_report.md
```

After this PR, every PR that touches the prompt fails CI if the
eval metrics regress. The deploy pipeline is gated by the eval.

## Lessons

1. **The eval set is the gate.** Every change that affects the
   prompt, the retriever, or the model must pass the eval set
   before merging. A unit test that doesn't exercise the prompt
   is not enough.
2. **The breaker is a backstop, not the primary defense.** The
   breaker catches failures, but it can be bypassed during
   deploys. The eval set in CI catches them earlier.
3. **Incidents are inevitable.** Mei will see a hallucination
   again. The recovery time (38 minutes in this case) is what
   matters. The eval set + the runbook + the rollback procedure
   are what make recovery cheap.
4. **The postmortem is a public artifact.** This document is
   published internally (PacificFreight) and externally
   (in the case studies folder of this curriculum). The point
   is not to assign blame — the prompt change was correct, the
   "in Ho Chi Minh City" string is what Mei prefers — but to
   teach the team how to respond.

## Closing

This postmortem is what the eval-driven iteration cadence looks
like when it fails. The cadence runs every Monday at 09:00 SGT;
on a Wednesday at 14:23, the cadence caught a regression that
should have been caught at the PR. The fix is mechanical: move
the eval set into CI, fail the PR on regression.

The customer impact was 4 drafts, all reverted, with 38 minutes
of recovery time. That's the operational boundary: hallucinations
happen, and the system's job is to catch them fast and recover
cleanly. **The eval set is the spec; the runbook is the contract;
the recovery time is the score.**