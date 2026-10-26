# On-call rotation — PacificFreight drafter

> **Owner:** Daniel (IT). **Last reviewed:** 2026-10-09. **Re-review:** quarterly, or after any FDE transition.

This is the on-call rotation + escalation policy for the PacificFreight drafter. It defines the 3 lanes, the 4 escalation tiers, and the **5-question "FDE has left" test** that the next FDE can answer in 30 seconds.

---

## The 3 lanes

| Lane | Owner | Hours | What they handle | How to reach |
|---|---|---|---|---|
| **CS lane** | Mei Tanaka | Mon–Fri 09:00–18:00 SGT | In-app errors, draft quality questions, thumbs-down spikes, Mei's "the drafter feels off" gut checks | In-app message → Slack #pf-drafter |
| **Infra lane** | Daniel Ng | 24/7 (paged) | VM, deployment, model choice, cost ceiling, SEV-1, security | PagerDuty → on-call phone |
| **Build lane** | FDE (rotating) | Mon–Fri 09:00–18:00 SGT (during build) / off-rotation (post-handoff) | Eval set regressions, experiment reviews, ADR log, runbook updates | Email (1-week SLA) |

**The CS lane is the first responder for any user-visible issue.** Mei sees the drafter before Daniel does. The infra lane is the first responder for any non-user-visible issue (cost, latency, breaker state). The build lane is a callback lane, not a paging lane — the FDE is not on call after the build ends.

---

## The 4 escalation tiers

A symptom is detected, then routed through the tiers:

| Tier | Symptom | First responder | Escalates to | SLA |
|---|---|---|---|---|
| **Tier 1** | Mei sees an in-app error in the drafter UI | Mei (in-app message) | Tier 2 if it persists 15 min | 15 min |
| **Tier 2** | 3+ thumbs-down in 1 hour; P95 > 4s for 30 min; cost alert at $1/day; /metrics shows degraded quality | Mei (during CS lane) → Daniel (during off-hours) | Tier 3 if the cause is a model or infra issue | 1 hour |
| **Tier 3** | Drafter is down (5xx for 5 min); cost > $4 (80% of ceiling); recurring SEV-2; breaker is OPEN | Daniel (paged) | Tier 4 if recovery fails | 4 hours |
| **Tier 4** | Recurring SEV-1 in a week; root cause unknown; multi-day outage; security incident | FDE callback (1-week SLA) | None — FDE writes the postmortem | 1 week |

The tier is set by the **symptom severity**, not by the lane. A thumbs-down spike at 2am is still Tier 2 (it doesn't page Daniel; Mei sees it Monday morning). A SEV-1 at 2am is Tier 3 (Daniel pages).

---

## The weekly schedule

The CS lane is Mei, Mon–Fri. The infra lane is Daniel, 24/7. The build lane is the FDE, Mon–Fri during the build.

| Day | CS lane (Mei) | Infra lane (Daniel) | Build lane (FDE) |
|---|---|---|---|
| **Mon** | 09:00 standup: review iteration report. Flag thumbs-down spikes. | 09:30 standup: review /circuit/state, cost report. | 09:00 standup: pick this week's experiment. |
| **Tue** | Handle in-app issues. | On-call (paged). | 09:00: experiment card review. |
| **Wed** | Handle in-app issues. | On-call. | Implement the experiment. |
| **Thu** | Handle in-app issues. | On-call. | 09:00: PR review with Daniel. Merge. |
| **Fri** | 10:00 deploy watch: are drafts going through? | Deploy. Watch /metrics for 30 min. | 10:00 deploy. 14:00 verification. |
| **Sat–Sun** | Off. | On-call (paged for SEV-1 only). | Off. |

The cadence (C2) and the rotation are interlocked: the Friday deploy is the moment the FDE and Daniel both watch the system.

---

## The paging policy

Daniel pages when:

1. The circuit breaker is OPEN for > 5 minutes.
2. `/metrics` shows `pf_drafts_total{outcome="error"}` rate > 0.5/s for 5 min.
3. Cost alert fires (daily cost > $1).
4. `/health` returns non-200.
5. Mei pages: "the drafter is broken."

Daniel does NOT page when:

1. Mei reports a single thumbs-down (Tier 1, Mei handles).
2. P95 latency is 3.5s (under the 4s threshold).
3. Cost is $0.50 for the day (under the $1 alert).

**The paging policy is the difference between Daniel sleeping through the night and Daniel waking up for nothing.** The runbook SEV definitions are the policy; this rotation is the implementation.

---

## The post-handoff rotation

When the FDE exits, the build lane becomes **off-rotation**. The CS lane and the infra lane continue. The FDE column in the RACI matrix becomes empty until a new FDE is assigned.

The post-handoff escalation changes:

- Tier 1, 2, 3: Same as during the build. Mei and Daniel handle.
- Tier 4: The FDE callback becomes **the next FDE** (when assigned), or **Sarah** (in the interim). Sarah can approve rollback to a previous version, but cannot approve new experiments.

The new FDE inherits the rotation by:

1. Reading this document on day 1.
2. Reading the runbook (`consulting/04-runbook.md`).
3. Reading the RACI matrix (`consulting/05-raci.md`).
4. Running the fire-drill with Daniel within 1 week.
5. Passing the 5-question "FDE has left" test below.

---

## The 5-question "FDE has left" test

The next FDE (or Sarah, in a fire-drill) should answer these 5 questions in 30 seconds each. If they can't, the handoff is incomplete.

```
1. Where does the prompt live?
   → service/rag.py::build_rag_prompt
   → Mei has the pen (RACI row 1: A=Mei, R=Mei).
   → To change it: edit the file, run the eval set, deploy Friday.

2. Who changes the eval set?
   → FDE during build; Mei post-handoff (RACI row 2: A=Sarah, R=Mei).
   → Rows are in shared/eval_set.jsonl.
   → To add a row: append a JSONL line, run the eval, update the baseline.

3. What's the cost ceiling?
   → $5/month (RACI row 6: A=Daniel, R=Daniel).
   → Daniel pages at $4 (80% of ceiling).
   → To check: awk -F'"cost_usd":' '{print $2}' usage.jsonl | awk -F',' '{sum+=$1} END {print sum}'

4. Who pages when the drafter hallucinates?
   → Tier 2: Mei (CS lane) → Daniel (infra lane) if Mei is off-hours.
   → Tier 3 if it's a model issue. See runbook SEV-2 (consulting/04-runbook.md).
   → Tier 4 (FDE callback, 1-week SLA) if recurring.

5. What does the runbook say for SEV-1?
   → See consulting/04-runbook.md, page 1 (the 1-page quick-reference card).
   → First step: check GET /circuit/state. If state=open, wait 30s for HALF_OPEN.
   → If state=closed, check VM health. If unknown, page FDE.
```

If the next FDE takes > 30 seconds on any question, the FDE updates the runbook before they leave. **The test is not a quiz — it's a measurement of the handoff's clarity.**

---

## The fire-drill protocol

The FDE runs the fire-drill in the week before they exit. The protocol:

1. **Monday:** FDE writes the 3 documents + the 5-question test.
2. **Tuesday:** FDE walks Daniel through SEV-1 end-to-end. Daniel plays the on-call engineer. FDE plays the SEV-1.
3. **Wednesday:** Daniel runs the SEV-1 fire-drill solo. FDE observes. Daniel pages correctly? If not, the runbook is unclear — fix it.
4. **Thursday:** FDE walks Mei through a SEV-2 hallucination. Mei plays the operator. FDE plays the hallucination.
5. **Friday:** Mei runs the SEV-2 fire-drill solo. FDE observes. Mei pages correctly? If not, the rotation is unclear — fix it.

**The handoff is complete when both Daniel and Mei pass their fire-drill.** The documents are necessary but not sufficient; the fire-drill is the test.

---

## Re-review schedule

- **Quarterly:** Daniel re-reads the rotation + the runbook + the RACI. Confirms the lanes are still right.
- **On FDE transition:** The incoming FDE runs the fire-drill within 1 week. The FDE column is updated.
- **After any SEV-1 or recurring SEV-2:** Daniel updates the rotation based on what he learned. Specifically: did the paging policy fire correctly? Did the escalation tier match the symptom?
