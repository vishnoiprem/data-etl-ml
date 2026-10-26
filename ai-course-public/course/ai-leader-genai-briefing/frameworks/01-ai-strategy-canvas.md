# The AI Strategy Canvas

> **Section 1 deliverable.** Maps to *Gen AI Strategy Framework* (14:33),
> *AI Strategy for Executives* (20:10), *AI Project Ideation* (21:02).
>
> Fill this in before you approve any AI spend. If a project cannot complete
> this canvas in one page, the project is not ready for a funding decision.

---

## The core claim

Most AI strategies fail not because the technology didn't work, but because
nobody ever wrote down **what problem** it was solving and **how we would know
if it worked**. The canvas is a forcing function for that sentence.

> "If you cannot fill in box 6 honestly, stop. You are not ready to fund this."

---

## The canvas

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. PROBLEM          │ What breaks today, without AI?            │
│    (not the soln)   │ Whose time/money/error? Quantify it.      │
├─────────────────────┼───────────────────────────────────────────┤
│ 2. USER             │ Who touches this output daily?             │
│                     │ Are they the person who feels the pain?   │
├─────────────────────┼───────────────────────────────────────────┤
│ 3. DATA             │ What data exists today, at what quality?  │
│                     │ Who owns it? Can we legally use it?       │
├─────────────────────┼───────────────────────────────────────────┤
│ 4. APPROACH         │ Prompt / RAG / fine-tune / agent / don't. │
│                     │ Justify against the 5 techniques table.   │
├─────────────────────┼───────────────────────────────────────────┤
│ 5. RISK             │ What is the blast radius if it's wrong?   │
│                     │ What's the human-in-the-loop fallback?    │
├─────────────────────┼───────────────────────────────────────────┤
│ 6. MEASUREMENT      │ The number that decides continue/kill.    │
│    ⚠️ THE HARD ONE  │ Baseline today. Target. Review cadence.   │
└─────────────────────┴───────────────────────────────────────────┘
```

---

## Worked example

**Box 1 — Problem.** Our support team handles ~4,200 tickets/week. 61% are
the same 12 questions (password reset, refund policy, shipping status). Median
handle time: 6.4 minutes. Fully-loaded agent cost: $19/hr.

**Box 2 — User.** The support agent, on a 2-person rotation. The person who
feels the pain is the agent — this is a good sign.

**Box 3 — Data.** 3 years of ticket history in Zendesk export. PII present.
Legal has approved redaction of names/emails for training use.

**Box 4 — Approach.** RAG over the ticket archive + a canonical FAQ doc.
**Not** fine-tuning: the FAQ changes monthly, and RAG makes that a doc edit
instead of a retrain. **Not** an agent: the task is single-turn lookup.

**Box 5 — Risk.** Wrong refund policy quoted to a customer. Blast radius is
one support interaction — acceptable with a human escalation path on any
question touching money.

**Box 6 — Measurement.**
- Baseline: 6.4 min median handle time, 4,200 tickets/week.
- Target: 2.5 min median, 3,400 tickets/week (61% deflected).
- Cadence: weekly review; **kill criterion at week 8 if handle time < 3.2 min.**

---

## The three questions that kill proposals

When reviewing any AI project, ask these in order. They surface more than the
entire technical review combined:

1. **"What does a human do today, and how long does it take?"** If they can't
   answer, there's no problem — there's a hobby.
2. **"What happens when it's confidently wrong?"** If the answer is "the user
   will know," ask how. Usually they won't.
3. **"What number do we look at in 90 days to decide this was a mistake?"**
   A project with no kill criterion has no accountability.

---

## Why box 6 is the hard one

Every team fills boxes 1–5 without complaint. Box 6 requires someone to
commit, in writing, to a number that could prove them wrong.

The tell for a project that's not real: the "measurement" is adoption
("500 users signed up"), not outcome ("deflection rate", "resolution time").
Adoption is a vanity metric. It measures enthusiasm, which is not the same as
value.

---

## Common traps

| Trap | Why it fails |
|---|---|
| Starting from the technology | "We have GPT access, what should we do with it?" produces projects with no box 1. |
| Fine-tuning when RAG would do | Fine-tuning bakes in knowledge that changes weekly. RAG is a doc update. |
| Building an agent for a single-turn task | Agents add non-determinism and audit cost for no gain. See Lecture 8. |
| Measuring tickets closed instead of time-to-resolution | Optimises for the metric, not the outcome. |
| No kill criterion | The project never dies, so it never frees budget for the next one. |

---

**Last updated:** 2026-10-21