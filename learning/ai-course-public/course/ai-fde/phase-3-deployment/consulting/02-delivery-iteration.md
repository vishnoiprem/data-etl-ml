# Lesson 05 — Delivery planning and iteration cycles (Phase 3 C2)

> **Mei needs to see a release every Friday or she stops trusting the drafter.** 30 minutes. No new code. One artifact: an `iteration-cadence.md` the next FDE can follow without your tribal knowledge.

By the end of this lesson you can stand up the **weekly iteration cadence** that turns "we built it" into "they're using it and it gets better every week." You have the experiment template (hypothesis → change → measurement → success criterion), the 4-week Phase 3 plan with milestones, and the ADR-trail pattern that captures every shipped change in a one-line log. The artifact: a 1-page `iteration-cadence.md` the next FDE inherits.

The PacificFreight scenario: it's Week 5 of the pilot. Mei has been using the drafter for 4 weeks. The thumbs-up rate is 79.8% — close to the 80% Phase 3 sign-off bar but not over it. Sarah asks "when does it cross 80%?" The honest answer is "I don't know — we need a cadence." The cadence is the answer.

---

## 🎯 Outcome

You produce **one artifact**:

- `iteration-cadence.md` — a 1-page markdown with the weekly rhythm (Mon review → Tue experiment pick → Wed-Thu implement → Fri ship), the experiment template, and the 4-week Phase 3 plan.

When you finish, you can answer in 60 seconds: "what did we ship last Friday?" and "what's the next experiment?"

## 🧠 Mindset

A production LLM system is not "shipped." It is **continuously improved**. The trap is to think of Phase 3 as a single delivery ("we built the drafter") and then disappear. The truth is that the drafter Mei uses on Week 5 is not the drafter Mei used on Week 1 — it has had 4 weekly experiments land. The cadence is the difference.

Three principles:

1. **Shipping is a habit, not an event.** Mei's trust in the drafter is renewed every Friday when a new version lands. If you skip a Friday, the trust erodes. The cadence is the mechanism: the FDE shows up, ships something small, and Mei sees the drafter getting better.
2. **One experiment per week, not five.** The temptation is to bundle 5 changes into a "big release." This makes attribution impossible. If the thumbs-up rate jumps, was it the prompt change, the eval-set addition, the new context, the redaction, or the rate-limit tuning? **One experiment per week. The change is small enough to attribute. The cadence is the forcing function.**
3. **The eval set is the spec, the iteration report is the test.** The eval set (Phase 2) says "this is what 'good' means." The iteration report (T2) says "here's how we're tracking against it." Together they form a closed loop: the eval set is the hypothesis, the report is the experiment result, the next week's eval-set additions are the new hypothesis.

The trap:

1. **The "big-bang release" trap.** Bundle 5 changes into a Friday release. Mei notices the quality shift but can't tell which change caused it. Attribution lost. Roll back? Ship forward? **One change per week. The cadence is the attribution mechanism.**
2. **The "Friday night deploy" trap.** Friday afternoon is when the FDE is tired. Mei is wrapping up. The deploy fails. Nobody notices until Monday. **Deploy Friday morning. The Friday afternoon standup is the moment the new version is verified.**
3. **The "no experiments, just maintenance" trap.** Some weeks there's no obvious experiment. **This is a sign the eval set is stale.** Add 5 new rows from Mei's recent thumbs-down notes. Now you have a hypothesis: "if the eval set covers refund policy, the next prompt change can be measured." The cadence forces the eval set to grow.

> **FDE rule:** the cadence is weekly. The experiment is small. The release is Friday. The eval set grows. The artifact that survives the FDE's exit is the last 4 weeks of iteration reports + the experiment log (the ADR trail).

## 🛠️ Practice — the weekly cadence

### The 5-day rhythm (Mon–Fri)

| Day | Block | What happens | Output |
|---|---|---|---|
| **Monday** | 09:00–09:30 | FDE reads the iteration report (`render_iteration_report`); writes the top 3 action items | A short bullet list of "what we learned this week" |
| **Tuesday** | 09:00–09:30 | FDE picks ONE experiment; writes the experiment card (see template below) | One `experiment-NNN.md` file with hypothesis, change, measurement, success criterion |
| **Wednesday** | all day | FDE implements the change in a feature branch; runs the eval set locally; confirms no regression | A green CI run + a draft PR |
| **Thursday** | 09:00–09:30 | FDE reviews the PR with Daniel (or a peer); merges if green | A merged PR + a 1-line ADR (e.g., `ADR-0017: move style-guide#4 to position 1 in system prompt`) |
| **Friday** | 10:00 | FDE deploys; Mei is notified; the FDE watches `/metrics` and `/circuit/state` for 30 min | A new version running, no SEV-1, the next iteration report will show whether the experiment worked |

Total FDE time: ~6 hours/week. The cadence is sustainable; this is not a 60-hour week.

### The experiment template

Every experiment is a 4-line file in `experiments/`:

```markdown
# Experiment 0017 — move style-guide#4 to position 1 in system prompt
**Date:** 2026-10-08 (Wed implement, Fri ship)
**Author:** FDE

## Hypothesis
If I move the Hard rules chunk (style-guide#4) to position 1 in the
system prompt, the refund-escalation rate will improve from 90% to 99%.

## Change
Edit `service/rag.py::build_rag_prompt` to put `style-guide#4` first in
the contexts list.

## Measurement
- Add 5 refund rows to the eval set (from Mei's thumbs-down notes).
- Re-run `service/eval.py eval`; expect `context_precision` to lift 0.05.
- Re-run next Monday's iteration report; expect thumbs-up rate to cross 80%.

## Success criterion
Eval set's refund rows: ≥ 95% pass. Iteration report thumbs-up: ≥ 80%.

## Result (filled in next Monday)
- [ ] Eval set: ___/5 pass
- [ ] Thumbs-up: ___% (target 80%)
- [ ] Decision: ship | revert | iterate
```

The 4-line structure forces clarity. **If you can't fill in "Success criterion" in 1 sentence, the experiment is too vague — pick a different one.**

### The 4-week Phase 3 plan

| Week | Milestone | Eval set rows | Iteration report focus |
|---|---|---|---|
| **Week 1** | Stand up `/feedback`, `/metrics`, `/draft/stream`; first iteration report | 30 (Phase 2) | Baseline: thumbs-up, P95, cost |
| **Week 2** | First experiment (likely: prompt wording for refund policy) | 32 (+2 refund) | Thumbs-up delta vs Week 1 |
| **Week 3** | Second experiment (likely: add 5 Vietnamese emails to eval set) | 37 (+5 Vietnamese) | Context_precision delta on Vietnamese subset |
| **Week 4** | GO/NO-GO review with Sarah | 40 (frozen for sign-off) | Final sign-off report |

The 4-week plan is **not** a Gantt chart. It's a hypothesis about what the iteration cadence will surface. The FDE updates the plan every Monday based on the iteration report.

### The ADR trail (the artifact that survives)

Every shipped change gets a one-line ADR (Architecture Decision Record) entry. The ADR log is the next FDE's tribal knowledge. For PacificFreight:

```
ADR-0014  2026-09-21  Stand up /feedback endpoint. Closes Phase 2 commitment #3.
ADR-0015  2026-09-28  Add 5 refund rows to eval set. Mei's thumbs-down notes.
ADR-0016  2026-10-02  Move style-guide#4 to position 1. Refund escalation +9pp.
ADR-0017  2026-10-08  Wire /circuit/state. Daniel can now see the breaker at 2am.
```

**The next FDE reads the ADR log on day 1 and knows what's been tried.** The log is the institutional memory; the FDE is the temporary steward.

### The "Friday afternoon" verification

The deploy is Friday morning. The Friday afternoon standup is the verification:

- 10:00 — FDE deploys. The eval set runs in CI.
- 10:15 — FDE watches `/metrics`: `pf_drafts_total{outcome="ok"}` is incrementing.
- 10:30 — FDE watches `/circuit/state`: `state=closed`, no recent transitions.
- 11:00 — FDE checks `usage.jsonl` for the new `request_id`s: the log lines have the new prompt version.
- 14:00 — Mei's first draft of the afternoon. If she sends a thumbs-up on a row the eval set would have failed pre-change, the experiment worked.

**The Friday afternoon standup is the moment the FDE knows the experiment shipped clean.** If anything looks off, the FDE has 4 hours to revert before the weekend.

## 🏛️ FDE Lens — when the cadence lies

The cadence is correct in the steady state. It lies at the edges:

1. **The "every week is a new experiment" lie.** Some weeks the eval set is already at 1.0 on a metric. The right move is not to invent an experiment — it's to **add a harder row to the eval set** that exposes the next failure mode. The cadence is not "ship something every week"; it's "make the eval set harder every week."
2. **The "Mei is the only signal" lie.** Mei's thumbs are the qualitative signal. The eval set is the quantitative signal. The metrics are the liveness signal. **A week where Mei gives 100% thumbs-up but P95 latency jumps to 8s is a bad week.** The iteration report catches this; the FDE reads the report, not the thumbs.
3. **The "Friday deploy is fine" lie.** Friday deploys are fine when the eval set is green. They are not fine when the eval set has been red for 3 weeks and the FDE is "shipping anyway." **If the eval set is red, the deploy is blocked.** The cadence is not a forcing function for shipping; it's a forcing function for fixing the eval set first.

> **FDE rule:** the cadence is the rhythm; the eval set is the spec; the ADR log is the memory; the iteration report is the test. If any of the four is missing, the next FDE inherits a system they don't understand.

## 🌙 Reflect

Write 3-5 sentences:

1. The cadence is one experiment per week. Mei asks "why not five?" What do you say? (Hint: think about what happens when a release goes wrong — which of the 5 changes do you revert?)
2. The experiment template has a "Success criterion" field. A junior FDE writes "the drafter is better." **What's wrong with this, and how do you fix it in 1 sentence?**
3. The 4-week plan says Week 4 is the GO/NO-GO review. The eval set is at 0.78 context precision, the thumbs-up is at 79%. **What's the call — GO, NO-GO, or PIVOT? What do you tell Sarah?**
4. The ADR log says ADR-0016 "moved style-guide#4 to position 1." The next FDE asks "why?" **Where is the answer — the ADR log, the eval set, the iteration report, or the experiment card? (All of the above — but which one is the one-line summary?)**
5. The cadence says "Friday deploy." Daniel says "no, deploy Tuesday — I want to be around if it breaks." **How do you resolve this without making the cadence weekly-bimonthly?**

**What's next — C3** is the ownership handoff: the runbook + RACI + on-call rotation that turn "the FDE built it" into "the team runs it." The artifact: `runbook.md` (4 SEV levels), `raci.md` (12 artifacts × 4 stakeholders), `on-call-rotation.md` (weekly rotation + escalation tiers), and the "FDE has left" 5-question test.
