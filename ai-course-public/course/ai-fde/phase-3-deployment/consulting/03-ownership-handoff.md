# Lesson 06 — Ownership handoff (Phase 3 C3)

> **The FDE's job is to make themselves unnecessary.** 35 minutes. No new code. Three artifacts: `04-runbook.md`, `05-raci.md`, `06-on-call-rotation.md`. Plus the 5-question "FDE has left" test.

By the end of this lesson you can write the **runbook** that tells the on-call engineer what to do at 2am, the **RACI matrix** that tells the next FDE who signs off on what, and the **on-call rotation** that escalates correctly across Mei / Sarah / Daniel. The artifact that survives: the 3 documents + the 5-question "FDE has left" test that verifies the handoff is complete.

The PacificFreight scenario: it's Week 6 of the pilot. The thumbs-up rate is 82%. The eval set is at 0.85 context precision. Cost is $0.50/week — under Daniel's $5 ceiling. **The drafter is a success.** The FDE's next engagement starts in 2 weeks. Sarah asks "who runs this when you're gone?" The FDE has 2 weeks to write the runbook, the RACI, the on-call rotation, and the 5-question test. **This lesson is what the FDE writes in those 2 weeks.**

---

## 🎯 Outcome

You produce **three artifacts + one test**:

- `04-runbook.md` — 5-step runbook for 4 SEV levels (SEV-1 drafter down / SEV-2 hallucination spike / SEV-3 latency P95 > 4s / SEV-4 cost overage). Each step is: detect → diagnose → mitigate → recover → postmortem template.
- `05-raci.md` — RACI matrix across 12 artifacts (prompt, eval set, baseline, RAG index, model choice, cost ceiling, VM, deployment, monitoring, runbook, ADR log, style guide) × 4 stakeholders (Mei, Sarah, Daniel, FDE).
- `06-on-call-rotation.md` — Weekly rotation (Mei = business hours CS, Daniel = 24/7 infra, FDE = build-period shadow), escalation tiers (Tier 1 → in-app error, Tier 2 → Mei, Tier 3 → Daniel, Tier 4 → FDE callback).
- The 5-question "FDE has left" test at the bottom of `06-on-call-rotation.md`.

When you finish, the next FDE can answer the 5 questions in 30 seconds, and Daniel can page correctly when the drafter hallucinates at 2am.

## 🧠 Mindset

The FDE's job is not to build the drafter. The FDE's job is to **make the team able to run the drafter without the FDE**. The test is not "did the code work?" — the test is "did the next FDE find everything they need in 30 seconds?"

The trap:

1. **The "code is documentation" trap.** The next FDE can read the code in 30 minutes. They cannot read the *reasoning* behind the code in 30 minutes. **Why is the eval set 30 rows? Why is the cost ceiling $5? Why is Mei the one who changes the prompt?** The reasoning lives in documents, not in code.
2. **The "Daniel will figure it out" trap.** Daniel is the IT owner, not an LLM expert. He knows "the service is down" and "the bill is high." He does not know "the eval set is regressed by 0.05." **The runbook tells Daniel what to look for, in his language, with his tools.**
3. **The "we'll document it after launch" trap.** Documentation after launch is fiction. By the time the FDE writes the runbook, the SEV-1 has happened twice and the runbook is a postmortem, not a prevention. **The runbook is written on day 1, updated on every SEV, and tested in a fire-drill before the FDE leaves.**

> **FDE rule:** the FDE has succeeded when the team runs the drafter for 4 weeks without paging the FDE. The FDE has failed when the team pages the FDE 3 times in the first week after exit. The artifacts in this lesson are how the FDE measures their own success.

## 🛠️ Practice — the 3 documents + the test

### Document 1: `04-runbook.md` (5 steps × 4 SEV levels)

The runbook has 4 SEV levels, calibrated to PacificFreight's reality:

| SEV | Definition | Page in | First responder | Time to mitigate |
|---|---|---|---|---|
| **SEV-1** | Drafter is down (Mei can't send drafts) | 0 min | Daniel (paged) | 5 min |
| **SEV-2** | Hallucination spike (eval set regresses, or Mei reports 3+ thumbs-down/hour) | 15 min | FDE (during build) / Daniel (post-handoff) | 1 hour |
| **SEV-3** | P95 latency > 4s (Mei is on slow wifi, or the LLM is degraded) | 1 hour | Mei (in-app) → Daniel (if not transient) | 4 hours |
| **SEV-4** | Cost > $5/month (rate limit was bypassed, or a loop is running) | 24 hours | Daniel (monthly review) | 1 week |

Each SEV has a 5-step runbook: **detect → diagnose → mitigate → recover → postmortem**. The full runbook is in `consulting/04-runbook.md`. The SEV-1 quick-reference card is at the top: a 1-page list Daniel can read in 30 seconds while paging.

### Document 2: `05-raci.md` (12 artifacts × 4 stakeholders)

The RACI matrix is the decision-rights expansion of the C1 stakeholder map. For each artifact, who is Responsible, Accountable, Consulted, Informed?

| Artifact | Mei | Sarah | Daniel | FDE |
|---|---|---|---|---|
| Prompt (style/voice) | R, A | C | I | C |
| Eval set rows | C | A | I | R |
| Baseline.jsonl | I | A | I | R |
| RAG index (corpus) | C | I | A | R |
| Model choice | I | C | A, R | C |
| Cost ceiling | I | C | A, R | I |
| VM | I | I | A, R | I |
| Deployment (CI/CD) | I | I | A, R | C |
| Monitoring (`/metrics` dashboard) | C | C | A, R | I |
| Runbook (this doc) | C | C | A, R | R (during build) |
| ADR log | C | C | I | R, A |
| Style guide (source of truth) | R, A | I | I | C |

**R = Responsible** (does the work), **A = Accountable** (signs off — exactly one A per row), **C = Consulted** (asked before the change), **I = Informed** (told after the change).

The matrix has **exactly one A per row**. If a row has 0 A's or 2 A's, the decision-right is ambiguous and the runbook will fail.

### Document 3: `06-on-call-rotation.md` (weekly rotation + escalation tiers)

The rotation has 3 lanes:

| Lane | Owner | Hours | What they handle |
|---|---|---|---|
| **CS lane** | Mei | Mon–Fri 09:00–18:00 SGT | In-app errors, draft quality questions, thumbs-down spikes |
| **Infra lane** | Daniel | 24/7 (paged) | VM, deployment, model choice, cost, SEV-1 |
| **Build lane** | FDE | Mon–Fri 09:00–18:00 SGT (during build) / off-rotation (post-handoff) | Eval set regressions, experiment reviews, ADR log |

The escalation tiers map a symptom to a lane:

| Symptom | Tier | First responder | Escalation |
|---|---|---|---|
| Mei sees an in-app error | Tier 1 | Mei (in-app message) | → Tier 2 if it persists 15 min |
| 3+ thumbs-down in an hour | Tier 2 | Mei → Daniel | → Tier 3 if it's a model issue |
| `/metrics` shows P95 > 4s for 30 min | Tier 2 | Daniel | → Tier 3 if Mei is blocked |
| `usage.jsonl` shows cost > $1 in a day | Tier 2 | Daniel | → Tier 3 if the cause is unknown |
| Drafter is down (5xx for 5 min) | Tier 3 | Daniel (paged) | → Tier 4 (FDE callback) if recovery fails |
| Recurring SEV-1 in a week | Tier 4 | FDE callback (1-week SLA) | FDE writes a postmortem + ADR |

The full rotation + escalation matrix is in `consulting/06-on-call-rotation.md`.

### The 5-question "FDE has left" test

At the bottom of `06-on-call-rotation.md`, the FDE writes a 5-question test. The next FDE (or Sarah, in a fire-drill) should be able to answer all 5 in 30 seconds. If they can't, the handoff is incomplete.

```
The 5-question "FDE has left" test
-----------------------------------
1. Where does the prompt live?
   → service/rag.py::build_rag_prompt; Mei has the pen (RACI A).
2. Who changes the eval set?
   → FDE during build; Mei post-handoff (RACI A). Rows are in shared/eval_set.jsonl.
3. What's the cost ceiling?
   → $5/month. Daniel pages at $4. Check usage.jsonl sum of cost_usd.
4. Who pages when the drafter hallucinates?
   → Tier 2: Mei → Daniel. Tier 3 if model issue. See runbook SEV-2.
5. What does the runbook say for SEV-1?
   → See consulting/04-runbook.md, page 1 (1-page quick-reference).
     First step: check GET /circuit/state. If state=open, wait 30s for HALF_OPEN.
```

The next FDE walks through these 5 questions on day 1. If any answer takes more than 30 seconds, the FDE updates the runbook before they leave.

## 🏛️ FDE Lens — the handoff is a fire-drill, not a doc review

The handoff is not "the FDE writes 3 documents and exits." The handoff is **a fire-drill the FDE runs in the week before they leave**:

1. **Monday:** FDE writes the 3 documents + the 5-question test.
2. **Tuesday:** FDE walks Daniel through the runbook end-to-end. Daniel plays the on-call engineer. FDE plays the SEV-1.
3. **Wednesday:** Daniel runs the fire-drill solo. FDE observes. Daniel pages correctly? If not, the runbook is unclear — fix it.
4. **Thursday:** FDE walks Mei through the thumbs-down escalation. Mei plays the operator. FDE plays the hallucination.
5. **Friday:** Mei runs the fire-drill solo. FDE observes. Mei pages correctly? If not, the rotation is unclear — fix it.

The handoff is complete when Daniel and Mei can each run their fire-drill in 30 seconds without the FDE in the room. **The 3 documents are the rehearsal script; the fire-drills are the proof.**

> **FDE rule:** the FDE has not handed off until Daniel and Mei have each passed the fire-drill. The documents are necessary but not sufficient. The fire-drill is the test.

## 🌙 Reflect

Write 3-5 sentences:

1. The runbook has 4 SEV levels. Daniel asks "why not just 2 — 'working' and 'broken'?" What do you say? (Hint: think about the cost of treating SEV-3 latency like SEV-1 drafter-down.)
2. The RACI matrix has exactly one A per row. Sarah says "Daniel and I should both be Accountable for the cost ceiling." What do you say? (Hint: who pages when the cost is over? If both, who actually pages?)
3. The on-call rotation has 3 lanes (Mei, Daniel, FDE). The FDE is "off-rotation post-handoff." But Mei asks "what if I need the FDE for a hallucination?" Where does the FDE live in the escalation? (Hint: Tier 4, with a 1-week SLA — not Tier 1.)
4. The 5-question test is "30 seconds each, 30 seconds total = 2.5 minutes." The next FDE takes 5 minutes. **What does this tell you about the documents?**
5. The FDE runs a fire-drill on Tuesday. Daniel fails. The FDE updates the runbook. **What is the failure mode the FDE should look for in the runbook? (Hint: the runbook tells Daniel to "check `/circuit/state`" — but Daniel doesn't know what `state=open` means.)**

**What's next — Phase 4 / handoff.** The 3 documents + the fire-drill are the handoff. The FDE exits. The team runs the drafter. The iteration cadence (C2) continues. The 3-loop report (T2) continues. The 3 failure-mode primitives (T3) keep the service up. The next FDE inherits the artifacts, the cadence, and the 4-week sign-off.
