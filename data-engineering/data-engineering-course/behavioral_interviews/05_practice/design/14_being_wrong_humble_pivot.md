# Lesson 14 — "Tell me about a time you were wrong. What changed your mind?"

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)
>
> **Pattern:** Verbatim from the 2026 Google DE bank. The #1 "Googleyness" hire signal per both Interview101 2026 and Datavidhya 2026.

---

## Why this lesson

This question is verbatim from the **Datavidhya 2026 Google DE
guide**:

> *"Tell me about a time you were wrong. What changed your mind?"*

It is the **single strongest Googleyness hire signal** of 2026 per
two independent sources:

- **Datavidhya (May 2026):** explicitly lists "Tell me about a time
  you were wrong" as one of the four core Googleyness prompts.
- **Interview101 (2026):** describes "pivot response under new
  constraint" as *the* Googleyness signal: *"candidates who visibly
  recalibrate and engage the new constraint constructively score
  higher than those who defend their original answer."*

The two sources converge on the same competency: **intellectual
humility**. The "wrong" question is the cleanest probe there is.

## The framework — 4 components in 90 seconds

| # | Component | Why |
|---|---|---|
| 1 | **The position you held.** | Concrete. Wrong. Specific. |
| 2 | **The evidence that contradicted it.** | Not "I was persuaded" — *what changed.* |
| 3 | **The moment you changed your mind.** | The pivot has to be *visible*. |
| 4 | **What you do differently now.** | The artifact: a habit, a check, a process. |

Total: **90-120 seconds.** This is shorter than most STAR answers
because the question is narrower.

## The 5-minute cousin: "How do you handle being wrong?"

This is the *framing* question (asked at the start of an interview
block to set the tone). The answer is a 30-second meta-answer:

> "Badly at first. Then I noticed the pattern: the things I was
> surest about were the things I had stopped checking. Now I have
> one rule — *the more confident I am, the more often I ask for
> the dissent before the meeting.* That's the only habit that's
> moved the needle for me."

That meta-answer is what the interviewer is grading. The
*specific* "wrong" story is the artifact.

## Worked example — ride-share pipeline schema

> **Position I held.** For 18 months I had argued that the
> ride-event schema should be *wide* — every event payload in one
> row, ~120 columns, denormalized for query speed.
>
> **The evidence that contradicted it.** Three things, in order:
> (1) A new data science hire ran an analysis showing that 64%
> of the columns were *never queried*. (2) The on-call team's
> paging rate was correlated with the number of schema changes
> per week — they were getting paged because of *our* schema
> churn, not user-facing incidents. (3) When I shadowed an
> analyst for a day, they spent 40% of their time writing
> *the same type of JOIN* to flatten the wide row.
>
> **The moment I changed my mind.** The 40% number. The data
> science finding was a fact. The on-call correlation was
> suggestive. The 40% — watching someone else do the work — was
> *unignorable*. I changed my mind on the train home.
>
> **What I do differently now.** I have three habits.
> (1) Before any schema proposal, I run a usage query: which
> columns are queried, by whom, how often. If 50% are dead, the
> schema is too wide. (2) I sit with an analyst for an hour
> per quarter and just watch them work. The patterns I see are
> the things I *should* have asked about. (3) I write dissent
> paragraphs in my own design docs — "this is what I'm
> missing" — to force myself to argue against my own position.
>
> **The thing I want you to remember.** Being wrong is not the
> problem. *Staying* wrong is the problem. The signal of
> seniority is not the absence of being wrong; it is the speed
> of the pivot.

## What the interviewer is grading

**Google — Datavidhya 2026 verbatim:** "Tell me about a time you
were wrong. What changed your mind?"

**Google — Interview101 2026:** pivot under new constraint.

**Four Googleyness pillars (Datavidhya 2026):**
1. Intellectual humility ← *the entire question*
2. Comfort with ambiguity
3. Conscientiousness
4. Collaboration

**Meta — Aced 2026:** Core Value "**Be Open**": *openness to
different perspectives, willingness to change your mind based on
new information.* Same competency, different vocabulary.

## The 5 common failure modes

1. **Wrong-but-lucky framing** — "I was wrong about X but it turned
   out fine." No. The point is the *pivot*, not the outcome.
2. **Defense-by-self-deprecation** — "Oh, I'm always wrong." Bad
   signal. The point is *naming the specific position* and changing
   it visibly.
3. **No visible pivot moment** — the story has to *show* the moment
   you changed your mind. Watching the analyst. Reading the data.
   Hearing the question.
4. **No artifact** — "I changed my mind" without "and now I do X
   differently" leaves the story hanging.
5. **Hero-of-the-story framing** — "I convinced my team we were
   wrong." No. The story is *you* being wrong, not somebody else.

## Try it — your turn

Write a 90-second version and a 30-second meta-version.

- **90-second version:** tell the position, the evidence, the
  pivot moment, the new habit.
- **30-second meta-version:** "How do you handle being wrong?"
  Generic, but tested — answer in 2-3 sentences.

If the 30-second version sounds defensive, rewrite the 90-second
version until the 30-second version sounds honest. The two are
correlated.

## Pair with

- `07_decision_by_instinct.md` — the flip side of the same coin.
- `08_difficult_team_members.md` — recalibration is the same beat.
- `11_influence_without_authority.md` — influence under new
  constraint is the same competency.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
