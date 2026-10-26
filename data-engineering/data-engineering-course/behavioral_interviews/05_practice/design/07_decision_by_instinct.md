# Lesson 07 — "Tell me about a decision you made based on your instincts"

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)
>
> **Pattern:** Non-STAR behavioral — tests metacognition, not just outcome.

---

## Why this lesson

The instinct question is the **only** common behavioral prompt that is
*not* STAR-shaped. There is no team, no conflict, no collaboration arc.
The interviewer is asking: "Show me the part of your judgment I can't
get from your résumé." Most candidates answer it with a STAR story
and lose points because the question has a different shape:

- No "we" — it is about *your* judgment.
- No "consequences" — it is about the *deciding moment*.
- No collaboration arc — it is about the gap between what the data
  said and what you chose.

The right answer is **3 components**: the data you had, the data you
*didn't* have, the heuristic you used to act anyway. Total length:
**90-120 seconds** for both Meta and Google.

## The framework (3 layers, not 4)

| Layer | What you say | Why it matters |
|---|---|---|
| **Data you had** | "We had 2 weeks of A/B test data. Variant B won by 1.2% on a noisy metric." | Anchors the decision in evidence. |
| **Data you didn't have** | "We needed 6 weeks of data to call significance, and the launch window closed in 5 days." | Names the gap. Shows you are honest about uncertainty. |
| **Heuristic you used** | "I asked: what is the *cost* of being wrong in each direction? A 1.2% miss costs us a quarter; a 1-week launch delay costs us a holiday window. The asymmetric loss favored shipping." | This is the "instinct" — a named, defensible heuristic. |

## Worked example — ride-share pipeline

> **Situation.** We had built a new driver-routing pipeline that
> recomputed ETAs every 30 seconds. After 3 weeks in shadow mode the
> simulation showed a 6.4% improvement in on-time arrival.
>
> **Data I had.** Three weeks of shadow-mode logs. Matched-pair
> comparison of driver experience vs. control: 6.4% better on-time,
> 2.1% better cancellation rate.
>
> **Data I didn't have.** I had never run this in production under
> traffic spikes (we simulate at 1x peak, not 5x), I had not validated
> that the cost model was correct (each recompute is $0.0003, so the
> "more recomputes = more revenue" claim was cost-dependent), and I
> had no field data on driver trust ("why is my suggested fare
> changing so often?").
>
> **The instinct call.** I shipped to 5% of traffic, with a hard kill
> switch and a 24-hour escalation path. Not because 6.4% wasn't
> compelling — it was. But because the *reversible* version of the
> decision was to ramp slowly and the *irreversible* version (driver
> trust erosion) was to ship fast and apologize later. I picked the
> reversible one.
>
> **Outcome.** The 5% ramp showed a 4.1% improvement (smaller than the
> shadow, as expected) and revealed that on Friday evenings the cost
> model was off by 30%. We held ramp at 5%, fixed the cost bug,
> re-shipped 3 weeks later at 100%.
>
> **The thing I want you to remember about this decision.** It was
> not "trust my gut over the data." It was *"use the data to bound
> the downside, then take the reversible path."* That is the heuristic
> you should be able to name out loud.

## What the interviewer is grading (the bucket signals)

**Google — Datavidhya 2026 / Interview101 2026:**
"Googleyness" includes **comfort with ambiguity**. The instinct
question is the cleanest probe. Grading: did you name the data you
*didn't* have? Did you name the heuristic? Or did you give a
self-aggrandizing story about how you were right?

**Meta — Aced 2026:**
Core Values include **"Be Bold"** and **"Focus on Long-Term Impact"**.
The instinct question is a probe for both. Grading: was the
instinct call *defensible* (not lucky)? Did it account for
reversibility? Did the heuristic ladder up to long-term impact, not
short-term cleverness?

## The 4 common failure modes

1. **"My gut told me…"** — present, past, and the wrong answer. There
   is no "gut." There is a heuristic. Name it.
2. **"I trusted the team…"** — that is a collaboration answer, not an
   instinct answer. The question is about *your* call.
3. **"The data was inconclusive, so I went with my experience…"** —
   "inconclusive" is not the same as "absent." If the data was there
   and inconclusive, the right answer is to *get more data*, not to
   override it.
4. **A 4-minute lead-up before the decision** — the question is about
   the deciding moment. The set-up must be 30 seconds, not 3 minutes.

## Try it — your turn

Write a 90-second answer for each of these three prompts:

1. A senior PM wanted to ship a feature that didn't have usage
   telemetry. You opposed. They overruled you. Two weeks later the
   feature was barely used. What's your instinct story?
2. You were the only on-call during a holiday weekend. The runbook
   said page the manager. The manager was on a flight. The incident
   was a 3-hour delay risk to revenue. What did you do and why?
3. A team-member proposed a redesign that violated an internal
   convention. Your team had a strong convention. Their reasoning was
   sound. You overruled or deferred. What was the instinct call?

For each, time yourself. If you go past 2 minutes, you have too much
setup and not enough decision.

## Pair with

- `01_story_mining.md` — mine 2-3 instinct stories from your past year.
- `03_tightening_delivery.md` — the 90-second target is non-negotiable.
- `13_unclear_requirements_scoping.md` — the cousin question at Google.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
