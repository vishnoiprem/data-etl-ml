# Consulting Track — AI FDE Phase 3

> **From "the service works" to "the team owns it."** Three lessons + three ops artifacts. ~1.5 hours total.

This track teaches the **documents and artifacts** the FDE writes when a Phase 2 service enters production and the FDE's engagement is winding down. Where Phase 2's consulting lessons produced the discovery deck, the PRD, and the ADRs, Phase 3's lessons produce the **stakeholder map**, the **iteration cadence**, the **ownership handoff**, and three **ops artifacts** (runbook, RACI, on-call rotation) that survive the FDE's exit.

---

## Lesson map

| # | Lesson | What you produce | Time |
|---|---|---|---|
| 01 | [Stakeholder alignment](./consulting/01-stakeholder-alignment.md) | A `stakeholder-map.md` — 3 + 1 audiences (Mei/Sarah/Daniel + exec sponsor), decision-rights matrix, GO/NO-GO criteria. The artifact that unblocks the Week-4 sign-off. | 30 min |
| 02 | [Delivery planning and iteration cycles](./consulting/02-delivery-iteration.md) | An `iteration-cadence.md` — the 3-loop daily/weekly/monthly rhythm. The artifact that keeps the drafter fresh. | 30 min |
| 03 | [Ownership handoff](./consulting/03-ownership-handoff.md) | The 5-question "FDE has left" test + the artifacts that make it pass: `runbook.md`, `raci.md`, `on-call-rotation.md`. The artifact that makes the FDE replaceable. | 35 min |

After C3, the consulting-track deliverable is the trio of artifacts that lets a new FDE pick up the engagement on day 1: the **stakeholder map** (who decides what), the **iteration cadence** (when things change), and the **ownership handoff** (what to do at 2am).

---

## The 3 ops artifacts (produced alongside the lessons)

These live in `consulting/` next to the lesson .md files:

| Artifact | Owner | What it answers | When it's used |
|---|---|---|---|
| `runbook.md` | Daniel (IT) | "What do I do at 2am when the drafter is down?" | Every SEV-1, SEV-2 |
| `raci.md` | Sarah (ops) | "Who decides whether we change the prompt / model / capacity?" | Every change request |
| `on-call-rotation.md` | Daniel (IT) | "Whose phone is ringing this week?" | Every business day |

These are **not** lessons. They are the artifacts. The lessons teach the FDE how to write them; the artifacts are the output.

---

## The 5-question "FDE has left" test (C3 closer)

C3 ends with a 5-question test that a new FDE must pass on day 1. If they can answer all 5 correctly, the FDE's job is done — the system is owned by the customer, not the FDE.

1. **Who owns the drafter when it breaks at 2am?** (Daniel. The on-call rotation says so.)
2. **Who decides whether we change the prompt?** (Mei proposes; Sarah approves; Daniel is informed.)
3. **How do I know if the drafter is drifting?** (The Monday iteration report shows the eval_score trend over 4 weeks.)
4. **What's the cost ceiling?** ($5/month. The 3-loop monthly review checks it.)
5. **Where do I find the 30-row eval set?** (`../phase-2-core-build/shared/eval_set.jsonl`. The runbook says so.)

If the new FDE can't answer all 5, the FDE has not finished their job. The handover is incomplete.

---

## How this track closes the engagement

```
Phase 1 consulting:    1-pager, solution outline           (the why)
Phase 2 consulting:    discovery deck, PRD, design doc, ADRs (the what + how)
Phase 3 consulting:    stakeholder map, iteration cadence, runbook, RACI, on-call
                                                            (the who + when + what-if)
```

At the end of Phase 3 the engagement has a complete paper trail. The customer can fire the FDE tomorrow and the system runs without them. **That is the definition of an FDE job well done.**

---

## What "Phase 3 consulting" is NOT

- It is **not** a sales process. The customer has signed the Phase 2 PRD; we're inside the engagement.
- It is **not** a project plan. The 4-week build plan lives in the Phase 2 design doc; Phase 3 tracks ownership, not dates.
- It is **not** legal. Contracts are a different document with a different audience.
- It is **not** re-doing Phase 2. Each Phase 3 lesson **extends** a Phase 2 artifact: C1 extends the stakeholder map; C2 extends the delivery cadence; C3 introduces new artifacts (runbook, RACI, on-call).

---

## What's next

- The **Technical Track** — the production-grade service that these docs describe.
- **Phase 4 (Capstone)** — `../phase-4-capstone/` — where the consulting story extends to case studies, a portfolio narrative, and a capstone presentation.
- **`course/practice/level-5-agents/`** — when you want the multi-agent patterns that go with the stakeholder map (Phase 4 Project 2 builds on these).

---

**Last updated:** 2026-10-09
**Phase:** 3 of 4 (Deployment & Reliability)
**Prerequisite:** [Phase 2 — Core Build](../phase-2-core-build/)
