# Lesson 04 — Stakeholder alignment (Phase 3 C1)

> **The GO/NO-GO gate at Week 4 needs a stakeholder map, not a meeting.** 30 minutes. No new code. One artifact: a `stakeholder-map.md` the next FDE can read in 5 minutes.

By the end of this lesson you can name the **3 + 1 audiences** for a PacificFreight-style AI deployment, draw the decision-rights matrix that decides who signs off on prompt changes vs deployment vs cost overages, and write the GO/NO-GO criteria that the Week 4 sign-off hinges on. The artifact: a 1-page `stakeholder-map.md` that survives FDE turnover — the next FDE reads it on day 1 and knows who to email about what.

The PacificFreight scenario: it's the end of Phase 2. Mei (CS lead) is using the drafter daily; 150 emails/day flow through it. Sarah (ops manager) reviews the weekly metrics. Daniel (IT) owns the VM. The drafter works. **Now the customer asks "should we sign off on the pilot?" and the FDE realizes nobody agreed on the criteria.** The Week-4 GO/NO-GO decision needs to be made *before* it's needed, not during. This lesson is the document that pre-commits the criteria.

---

## 🎯 Outcome

You produce **one artifact**:

- `stakeholder-map.md` — a 1-page markdown with the 3+1 audience map, the decision-rights matrix (who can decide what), and the GO/NO-GO criteria for the Week-4 sign-off.

When you finish, you can answer in 60 seconds: "who do I email when the drafter hallucinates?" and "what does the customer need to see to sign off?"

## 🧠 Mindset

Phase 1's 5-question framework (lesson 02) identified **one** user. Phase 2's 10-question deck (consulting lesson 01) probed the system. Phase 3's stakeholder map names the **3 + 1 audiences** that share ownership of a deployed AI service:

| Audience | Role | Cadence | What they care about |
|---|---|---|---|
| **Mei (CS lead)** | Daily user | Hourly | "Does the draft sound right? Can I send it?" |
| **Sarah (ops manager)** | Success-metric reviewer | Weekly | "Is the pilot moving the success metric (CS handle time, response latency)?" |
| **Daniel (IT)** | Infra + security owner | Monthly | "Is the bill under $5/mo? Is PII not leaking? Is the VM patched?" |
| **The end customer** (implicit 4th) | The recipient of Mei's drafts | Never in the room | "Did I get a clear, accurate answer in my language?" |

The trap:

1. **The "Mei is the customer" trap.** Mei is the **operator**. The end customer is who Mei serves. Optimizing for Mei's "this looks fine" is not the same as optimizing for the customer's "I got my answer." **The implicit 4th audience is the one the FDE has to model from Mei's feedback.**
2. **The "weekly sync" trap.** A 30-min weekly sync is **not** a stakeholder map. A map is a document the next FDE can read in 5 minutes. A sync is an event that disappears when the FDE leaves.
3. **The "everyone agreed" trap.** "Everyone agreed in the meeting" is not a decision-right. A decision-right is a name attached to an artifact. **The next FDE needs to know who has the pen on the prompt, who has the pen on the eval set, and who has the pen on the cost ceiling.**

> **FDE rule:** write the stakeholder map on day 1 of Phase 3, not day 28. The map is most useful when the FDE is still around to defend it.

## 🛠️ Practice — the stakeholder map

### The 3 + 1 audience map

For PacificFreight, the map is:

**Mei (CS lead) — the operator**
- Daily: drafts 150 emails through the drafter; clicks 👍 / 👎 / 😐 in the CS tool (Phase 4)
- Cares about: tone, accuracy of facts, the customer's language
- Email cadence: async; she'll respond when she has a moment
- Decision rights: prompt wording (style/voice), which draft variant to send

**Sarah (ops manager) — the success-metric reviewer**
- Weekly: reviews the iteration report (T2) at Monday's standup
- Cares about: CS handle time (minutes/email), response latency, customer-satisfaction survey trend
- Email cadence: weekly email + monthly review
- Decision rights: success metric definition, GO/NO-GO sign-off on the pilot, scope expansion (e.g., "should we add Mandarin?")

**Daniel (IT) — the infra + security owner**
- Monthly: reviews the `/circuit/state` snapshot, the cost report, the security log
- Cares about: cost ceiling ($5/mo), PII hygiene, VM uptime, dependency patches
- Email cadence: monthly review + SEV-1 paging
- Decision rights: deployment (when to push), cost ceiling (whether to alert at $4 or $4.50), model choice (which provider), security policy

**The end customer — the implicit 4th**
- Never in the room. Modeled from Mei's thumbs-down notes.
- Cares about: did I get a clear, accurate answer in my language? Was my problem solved?
- The FDE's job: keep this audience in mind even when nobody's asking about them.

### The decision-rights matrix

This is the artifact that survives turnover. For each decision, who has the pen?

| Decision | Primary (signs off) | Consulted | Informed |
|---|---|---|---|
| Prompt wording (style/voice) | Mei | Sarah | Daniel |
| Eval set rows (what to test) | FDE → Mei (post-handoff) | Sarah | Daniel |
| Model choice (which provider) | Daniel | FDE, Sarah | Mei |
| Cost ceiling ($5/mo) | Daniel | Sarah | Mei |
| Deployment (when to push) | Daniel | FDE | Mei, Sarah |
| GO/NO-GO on the pilot | Sarah | Mei, Daniel, FDE | — |
| Security policy (PII, retention) | Daniel | FDE | Mei, Sarah |
| Scope expansion (new language, new region) | Sarah | Mei, Daniel | FDE |

**R = Responsible** (does the work), **A = Accountable** (signs off), **C = Consulted**, **I = Informed**. The matrix above is the Responsible+Accountable column. The full matrix lives in `consulting/05-raci.md` (the C3 artifact).

### The GO/NO-GO criteria (pre-committed, not negotiated)

The Week-4 sign-off is decided against **criteria set on day 1**, not criteria the customer invents on day 28. For PacificFreight:

| Criterion | Threshold | Measurement |
|---|---|---|
| **Thumbs-up rate** | ≥ 80% over 4 weeks | `usage.jsonl` aggregated by `render_iteration_report` |
| **Hallucination rate** | < 1% on the 30-row eval set | `service/eval.py eval` weekly; flag if delta > 0.05 |
| **P95 latency** | < 4.0s | `pf_draft_latency_seconds` histogram |
| **Cost** | < $5/month | Sum of `cost_usd` from `usage.jsonl` |
| **SEV-1 incidents** | 0 unresolved | Runbook (consulting/04-runbook.md) log |
| **Mei self-report** | "I would recommend this to a peer CS team" | Monthly 5-min survey |

**A PIVOT** is a third option. If the criteria are met on thumbs-up and cost but P95 latency is 6s, the answer is not GO and not NO-GO — it's PIVOT: ship to Mei's team only, fix the latency over the next 2 weeks, re-evaluate.

> **FDE rule:** the GO/NO-GO criteria are written on day 1 of Phase 3 and emailed to Sarah. If the criteria change mid-pilot, the new criteria are also emailed. The artifact is the email trail, not the meeting.

### The "the FDE has left" test for C1

When the FDE exits, the next FDE can verify the alignment with 2 questions:

1. **"Who do I email when I want to change the prompt?"** — answer: Mei (primary), Sarah (consulted), Daniel (informed). The next FDE finds this in the decision-rights matrix above.
2. **"What's the success metric for the pilot?"** — answer: thumbs-up rate ≥ 80% over 4 weeks. The next FDE finds this in the GO/NO-GO table.

If either question doesn't have a one-name answer, the stakeholder map is incomplete and the FDE has not finished the handoff.

## 🏛️ FDE Lens — alignment is the artifact, not the meeting

The temptation is to schedule a stakeholder workshop and call it "alignment." It is not. Alignment is a **document**:

- The 3+1 audience map (who exists, what they care about, how to reach them)
- The decision-rights matrix (who has the pen on which artifact)
- The GO/NO-GO criteria (what "done" looks like, pre-committed)

These three documents, written on day 1 and updated when reality changes, are what the next FDE inherits. The workshops are how you *write* the documents; the documents are the artifact.

> **FDE rule:** if a stakeholder asks "did you align with Sarah?" and you answer "yes, we had a great meeting," you have not aligned. You have socialized. Alignment is when Sarah can answer the question without you in the room.

## 🌙 Reflect

Write 3-5 sentences:

1. The stakeholder map names 3 audiences (Mei, Sarah, Daniel) and 1 implicit (the end customer). Mei asks "why is the customer on the list — they're not in the room?" What do you say?
2. The decision-rights matrix says Mei signs off on the prompt. Daniel says "no, the IT team should review any prompt change for security." How do you resolve this without escalating to the CEO?
3. The GO/NO-GO criteria include "Mei self-report: I would recommend this to a peer CS team." Mei is worried this is "too soft." What do you say?
4. The matrix says Daniel has the pen on the model choice. The model goes down for 10 minutes. Mei is blocked. **Who is accountable for the 10-min outage? (Hint: accountability for a SEV-1 is different from the decision-right for choosing the model.)**
5. The FDE has left. The next FDE emails Sarah asking "what's the success metric?" Sarah doesn't answer for 3 days. **What does this tell you about the stakeholder map?**

**What's next — C2** writes the iteration cadence: the Monday-review → Friday-ship weekly rhythm that keeps the drafter improving without the FDE in the room. The artifact: a 1-page `iteration-cadence.md` + the experiment template (hypothesis → change → measurement → success criterion).
