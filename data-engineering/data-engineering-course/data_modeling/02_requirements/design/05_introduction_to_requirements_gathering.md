# Introduction to Gathering Business Requirements

## Why this lesson

This is the gateway lesson for Module 02 and arguably for the entire data modeling interview. Interviewers are not testing your ability to draw a star schema — they are testing your ability to *discover* the right star schema. The first 5–8 minutes of the round, spent gathering requirements, are the most leveraged 5 minutes in the round. This lesson explains *why* requirements come first, what it costs to skip them, and the three visible signals a senior candidate emits when they're doing it right. If you only internalize one thing from this module, internalize this: discovery before design.

---

## The cost of skipping requirements

It is tempting to start drawing tables the moment the prompt is read.
The candidate reasons: "the prompt already names a product, so the
entities are obvious." This is correct about 30% of the time and
catastrophically wrong the other 70%.

The cost of skipping requirements is not "I drew the wrong schema
once." It is:

1. **Redo time.** A wrong schema takes ~15 minutes to draw and
   another ~10 minutes to redo. The candidate who skipped
   requirements has now spent 25 of 45 minutes on the same question
   and has no time for the depth dive.
2. **Rubric penalty.** The discovery bucket (Lesson 03) is the
   highest-weighted bucket on the rubric. Skipping it caps the
   candidate at 3/4 no matter how good the rest of the round is.
3. **Wrong-grain trap.** Without requirements, the candidate picks
   a grain by intuition, not by the question. The grain turns out
   to be wrong, the fact table has to be re-designed mid-round, and
   the interviewer has watched the candidate self-correct for 20
   minutes.
4. **Lost depth dive.** The depth dive is *driven by the
   requirements*. If you don't know what the consumer wants to
   measure, the interviewer can't ask a meaningful follow-up. The
   round devolves into a quiz on dimensional modeling trivia.

---

## The three signals of a candidate who's doing it right

A senior candidate gathers requirements visibly. There are three
signals the interviewer watches for:

### Signal 1 — Asks 5–8 specific questions

Not "any scale requirements?" — that's a generic question. The
candidate asks things like:

> "How do you define 'engagement' here — daily active users, sessions
> per user, workouts per user?"

The question is *specific* to the prompt. It demonstrates the
candidate is thinking about the *metric*, not just the *schema*.

### Signal 2 — Writes a requirements doc

A 5–10 line doc, on the whiteboard or in the chat, with: consumers,
use cases, sources, volume, freshness, retention. The doc is the
*artifact*. The interviewer can refer back to it ("you said the
freshness was hourly — how does that affect the partition
strategy?").

### Signal 3 — Repeats the grain back to the interviewer

After discovery, the candidate restates the grain in their own
words:

> "OK, so to make sure I have this right: the grain of the fact
> table is one row per workout session, with `duration_minutes`
> and `calories_burned` as measures, and `dim_users` (SCD 2)
> joined on user_id. Correct?"

This is the *commitment* step. The candidate has absorbed the
requirements and is now stating the design. The interviewer can
correct any misunderstanding *before* the schema is drawn. This
saves 10 minutes of redraw.

---

## The "act of clarification" as a meta-skill

A clarification is not just a question — it is a *demonstration* of
how the candidate works. The interviewer learns:

- How does the candidate handle ambiguity? (Calmly, with a list of
  options?)
- How does the candidate prioritize? (Asks the 3 most important
  questions first?)
- How does the candidate communicate? (Specific, not generic?
  Numbered, not ramble?)

These are the same signals a hiring manager looks for in the
behavioral round. The data modeling round is, in some sense, a
*behavioral* round disguised as a technical one.

---

## The 5-minute cost

Discovery takes 5 minutes. Skipping discovery costs 15–25 minutes
of redo. The math is clear. Every senior candidate knows this; many
mid-level candidates don't.

If you only have time to internalize one thing from this module,
internalize this: **the first 5 minutes of the round are the most
important 5 minutes.**

---

## Try it

Practice the 5W+H framework on a problem you know nothing about.
Pick a random product from this list: Robinhood, Calendly, Notion,
Stripe, Figma, Headspace. Spend 5 minutes writing 5–8 discovery
questions. Then spend 5 minutes writing a requirements doc. Then
spend 10 minutes drawing the star schema. Time yourself.

Do this three times. By the third iteration, the discovery step
will feel natural.

---

## In the interview, you would say...

> "Before I draw a single table, I'm going to spend about 5
> minutes gathering requirements. I'll ask 5–8 specific questions
> about consumers, use cases, freshness, volume, and grain — then
> I'll write a short requirements doc and read the grain back to
> you. This 5-minute investment saves 15–25 minutes of redraw and
> earns the highest-weighted bucket on the rubric."

---

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
