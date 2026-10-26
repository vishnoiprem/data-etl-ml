# Lesson 13 — "Tell me about a time you worked on a project with unclear requirements. How did you scope it?"

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)
>
> **Pattern:** Verbatim from the 2026 Google DE behavioral bank. The most-asked behavioral question at Google that year.

---

## Why this lesson

This question is verbatim from the **Datavidhya 2026 Google DE
guide**, the most-cited 2026 source for the role:

> *"Tell me about a time you worked on a project with unclear
> requirements. How did you scope it?"*

Three reasons it's the most-asked question of 2026:

1. It is the cleanest probe for the **"comfort with ambiguity"**
   Googleyness pillar.
2. It discriminates between candidates who **resolved the
   ambiguity** (senior) and candidates who **escalated the
   ambiguity** (junior). Note: escalating is *not* always wrong —
   knowing which to do is the test.
3. It has a hidden second question: "How did you scope it?" — the
   scoping answer is the artifact. Most candidates tell the
   *unclear* story and skip the *scoping* story. Wrong.

## The framework — 2 arcs in 1 answer

| Arc | What you say | Length |
|---|---|---|
| **Unclear-requirements arc** | The set-up: who needed what, why the requirements were unclear, who else had conflicting asks. | 30 sec |
| **Scoping arc** | What you did to *unblock* the team: questions, spikes, decision documents, time-boxes. **This is 70% of the answer.** | 90-120 sec |

Total target: **2 minutes** for Google (2-3 min is the median).
For Meta, the same story can run 5 min but the scoping arc still
needs to be the bulk.

## The scoping playbook (5 moves, in order)

| # | Move | Example sentence |
|---|---|---|
| 1 | **Convene the right people** | "I got 30 minutes with the PM, the data science lead, and the platform-eng manager in a single room, before any work started." |
| 2 | **Time-box the spike** | "We agreed: 1 week to write a decision document. No code. No architecture diagrams. Just a written recommendation." |
| 3 | **Write the decision doc** | "I wrote a one-page doc with three options, each costed in dollars and weeks, with the recommended one called out." |
| 4 | **Make the decision explicit** | "The PM owned the call. I owned the technical recommendations. We disagreed on one item; I deferred because their call." |
| 5 | **Time-box the ambiguity** | "We agreed: if the spike didn't resolve the ambiguity by Friday, we escalated to the director." |

## Worked example — ride-share realtime cost attribution

> **The unclear bit.** Marketing wanted per-driver cost attribution
> in realtime. PM wanted per-ride. Finance wanted per-trip-segment.
> All three wanted different things. None of them had a clear
> definition of "cost" — driver acquisition, driver retention, and
> rider subsidy were all on the table.
>
> **What was at stake.** If we shipped the wrong model, we'd
> recalibrate the surge-pricing wrong and lose ~$2M/quarter. If we
> didn't ship at all, marketing couldn't bid on Q4 campaigns.
>
> **What I did (the scoping arc).**
>
> 1. **Convene the right people.** I got 30 minutes with marketing,
>    PM, finance, and a data science lead. No eng in the room —
>    *the problem was the requirements, not the implementation.*
> 2. **Time-box the spike.** We agreed: 1 week. No code. No
>    architecture. The artifact was a written decision document
>    with three options.
> 3. **Write the decision doc.** I owned the doc. Three options:
>    (a) per-ride attribution, 4-week build; (b) per-driver daily
>    attribution, 6-week build; (c) per-trip-segment, 12-week
>    build. The first was 80% of the value at 30% of the cost.
> 4. **Make the decision explicit.** PM owned the call. They
>    picked (a). I deferred; (b) and (c) were rational too, but
>    the launch window favored (a).
> 5. **Time-box the ambiguity.** We said: if the spike hadn't
>    converged by Friday, we escalated to the marketing VP. We
>    converged on Wednesday.
>
> **Outcome.** Per-ride attribution shipped 4 weeks later.
> Marketing used it through Q4. The recouped value was $3.2M in
> attributed bid spend. The 80% recommendation held for the
> next two quarters.
>
> **What I want you to remember.** "Unclear requirements" is not
> the same as "no requirements." It is *multiple*, *conflicting*
> requirements. The job is to *make the conflict explicit* and
> *time-box the resolution*. Nobody teaches this — every senior
> engineer I know learned it by failing at it once.

## What the interviewer is grading

**Google — Datavidhya 2026 verbatim:**
*"Tell me about a time you worked on a project with unclear
requirements. How did you scope it?"* — full quote.

**Graded on:**
- Did you name the *conflict* between stakeholders, not just the
  *absence* of clarity?
- Did you name a *time-box*? Unclear requirements without a
  time-box become *permanent* unclear requirements.
- Did you *escalate* (yes/no)? At L5+, expected behavior is to
  escalate scope-vs-deadline calls, not ambiguity itself.

## The 4 common failure modes

1. **Vague set-up** — "the requirements were unclear." Why? Between
   whom? About what? Name the conflict.
2. **Hero-discovery narrative** — "I figured it out." No. The job
   is *forcing the conversation*, not solving the puzzle alone.
3. **No time-box** — unclear requirements without a time-box are
   just unclear requirements forever.
4. **"I escalated to my manager" as the entire answer** — at L5+,
   "I escalated" is fine, but it must be *one* move in the playbook,
   not the whole playbook.

## Try it — your turn

Pick a project from the last 2 years where 2+ stakeholders wanted
different things. Run through the 5-move scoping playbook:

1. Who did you convene? Did you keep engineering out of the room?
2. What was the time-box? Did the team agree to it explicitly?
3. Did you write a decision document? Who owned the call?
4. Did you defer to a stakeholder on something you disagreed with?
5. Did you have an escalation threshold, in advance?

If any of these is missing, your story isn't really about
*scoping*. Re-frame it.

## Pair with

- `07_decision_by_instinct.md` — the decision-by-instinct cousin.
- `09_complex_program_stakeholders.md` — the matrix is the
  formal version of this conversation.
- `data_modeling/02_requirements/` — the requirements doc is the
  artifact that resolves the ambiguity.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
