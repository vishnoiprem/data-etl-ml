# 02 — Introduction to Engineering Behavioral Interviews

> **Lesson 2 of 8 — Fast Track** · ~15 min

What the behavioral round actually is, who runs it, what they're
grading, and how it slots into the overall interview loop.

---

## 1. What the round is

A 45-60 minute conversation, usually 1:1 (sometimes 2:1) with a hiring
manager, peer engineer, or trained "bar-raiser" (at Meta/Amazon).
The interviewer asks 4-6 questions about your past experience. You
answer in 2-3 minutes each. They score you on a rubric.

The format is intentionally **conversational**, not interrogative.
The interviewer is not trying to trick you. They are trying to
*simulate* working with you. If after 45 minutes of conversation they
think "I would happily put this person on my team and trust them with
a hard call," you've passed — regardless of which specific questions
you got.

A few things to internalize:

- **You have more control than you think.** The interviewer is
  looking for *one good story* per question. You get to pick which
  story. You get to pick what to emphasize. You get to leave out the
  parts that don't help you.
- **Vague is bad. Specific is good.** "I improved the system" is
  vague. "I cut p99 latency from 2.4s to 380ms by switching to a
  write-through cache" is specific. Specific is what scores.
- **The interviewer is rooting for you.** They are not paid to
  reject people. They are paid to find good people. The whole
  structure of the round is "give the candidate a chance to show
  their best work."

---

## 2. Who runs it

Three flavors:

| Interviewer | What they care about | Style |
|---|---|---|
| **Hiring manager** | Can this person be a peer I trust? Will they grow into more scope? | Conversational, often shares their own stories. |
| **Peer engineer** | Would I want this person on my team day-to-day? | Direct, often probes technical depth inside the story. |
| **Bar-raiser / trained interviewer** | Is this person above the bar for the level? | Structured, sticks to the rubric, less chatty. |

Each type has its own tells. Hiring managers want to hear about
*judgment* — the calls you made, the people you worked with. Peer
engineers want to hear about *craft* — the actual technical decisions,
the tradeoffs, what you'd do differently. Bar-raisers want to hear
*signal* — evidence that maps to a specific rubric row.

The lesson: **don't deliver the same answer to all three.** When
the interviewer opens with "tell me about your current role" and then
goes silent, listen to *how* they ask the next question. Are they
probing people ("who did you convince?")? Craft ("what was the
architecture?")? Outcomes ("what was the metric?")? Mirror their
probes.

---

## 3. The rubric (what they're actually scoring)

Every company has a slightly different rubric, but they all test the
same five things. Memorize this:

| Dimension | What "hire" looks like |
|---|---|
| **Ownership** | You drove outcomes, not just outputs. You finished what you started. |
| **Judgment** | You made calls under ambiguity and can defend them in retrospect. |
| **Collaboration** | You can disagree without being disagreeable. You bring others along. |
| **Growth** | You learn from failure. You don't blame. You don't repeat mistakes. |
| **Communication** | You can be specific, structured, and concise under pressure. |

Everything in the rubric is a *proxy* for "will this person be
trustworthy when I'm not in the room." If you walk out of the
interview and the interviewer says "I trust them" — you passed.
If they say "I don't have a clear signal" — you didn't, regardless
of how smart your stories were.

See `02_theory/04_signal_vs_noise.md` for the deeper breakdown.

---

## 4. How it fits in the loop

The behavioral round is **the round that swings offers**, not the
round that screens candidates. By the time you get to it, the
company has decided you're technically credible. The question now is
*"do we want to work with this person?"*

That means two things:

1. **The bar is "do I want to work with you," not "are you
   impressive."** Impressive is what got you in the room. Likable,
   trustworthy, and clear is what gets you the offer.
2. **You cannot game the round with one good story.** A single
   "I shipped a thing to N million users" story won't save you if
   the other four stories are vague, blame-y, or rambling. The
   interviewer is looking for *consistency*. They want to see that
   your judgment, ownership, and collaboration are stable across
   contexts.

In other words: the round is not a highlights reel. It's a *vibe
check*, backed by evidence.

---

## 5. A concrete example

Bad answer (heard this many times):

> *"So I was working on this project and my manager wanted me to do
> it a certain way but I didn't really agree, and I sort of pushed
> back, and then we ended up doing it my way and it worked out."*

What's missing: who, what, when, why, how, what happened, what was
the impact. This is a 1/4 on the rubric.

Good answer:

> *"I was leading the migration of our analytics pipeline from
> nightly batches to a streaming architecture. My EM wanted to do
> a big-bang cutover in a single weekend. I pushed back with a
> written risk doc — main concern was silent data loss during
> the dual-write window. We agreed on a 3-week shadow mode where
> the new pipeline ran in parallel and we diffed the outputs.
> Caught 14 silent schema mismatches that the big-bang would have
> shipped to production. Cutover happened on a Tuesday morning,
> zero incidents. The pattern became the default for the next two
> pipeline migrations on the team."*

Same person, same event, same underlying judgment. The difference
is specificity, structure, and impact.

---

## Try it

Pick one of these questions and answer it out loud, in 2 minutes
flat, with no notes:

1. "Tell me about a time you disagreed with your manager."
2. "Tell me about the hardest technical problem you've worked on
   in the last year."
3. "Tell me about a project that didn't go as planned."

Record yourself. Listen back. Ask: *did I mention a specific
decision, a specific number, and a specific takeaway?* If yes,
you're already in the top quartile. If no, keep practicing.
