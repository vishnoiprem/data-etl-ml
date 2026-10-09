# Lesson 06 — Discovery Questions: Who, What, When, Where, Why, How

> **What you'll learn:** a bank of 50+ discovery questions grouped by
> category. By the end of this lesson you'll know which 5–8 to ask
> for any given prompt.

---

## The 5W+H framework

The interview classics — who, what, when, where, why, how — apply
directly to data modeling. Each maps to a different bucket of
questions:

| W | Bucket | What it tells you |
|---|---|---|
| **Who** | Consumers | Which teams, which tools, which skills. |
| **What** | Use cases | The 3–5 questions the warehouse must answer. |
| **When** | Time | Freshness, late-arriving data, timezones, retention. |
| **Where** | Sources | OLTP, events, third-party, file drops, PII. |
| **Why** | Priority | What changed, what's at stake, who's accountable. |
| **How** | Metric definitions | Exact semantics: DAU, revenue, churn, attribution. |
| (extra) | **Scale** | Volume, concurrency, storage budget. |
| (extra) | **Historical** | SCD strategy, point-in-time correctness. |
| (extra) | **Edge cases** | Duplicates, late events, deletes, downtime. |

The full bank is in
[`code/discovery_questions.py`](../code/discovery_questions.py) — 50+
questions across 9 categories. The skill is not knowing all 50; the
skill is knowing which 5–8 to ask for the prompt in front of you.

---

## The 5–8 selection rule

You will never have time to ask all 50. The rule of thumb:

- **Always ask 1 "Who"** — to confirm the audience.
- **Always ask 2 "What"** — to pin down the use cases.
- **Always ask 1 "How"** — to nail the metric definition.
- **Always ask 1 "When"** — freshness is a non-negotiable.
- **Always ask "what's the grain?"** — this is the meta-question.
- **Fill the rest with the categories the prompt most implies.**

For example, for a healthcare prompt, fill the rest with "Where"
(PII / HIPAA constraints). For a real-time bidding prompt, fill the
rest with "When" (latency, freshness) and "Edge cases" (out-of-order
events).

---

## Worked example — selecting questions for a fitness app

> "Design a data warehouse for a fitness app so the analytics team
> can report on monthly engagement."

The candidate's 5–8 questions:

1. **Who** — "Is the analytics team the only consumer, or do we
   also need to support data science for retention modeling?"
2. **What (1)** — "What does 'engagement' mean here — daily active
   users, sessions per user, or workouts per user?"
3. **What (2)** — "Do we need cohort analysis — i.e., how do users
   who signed up in March compare to users who signed up in
   April?"
4. **When** — "What's the freshness? Daily batch, hourly, or
   real-time?"
5. **How** — "How is a 'workout' defined — does it have to be
   started, or just opened in the app?"
6. **Grain** — "What should the grain of the fact table be — one
   row per workout, one row per session, or one row per
   user-day?"
7. **Historical** — "Do we need to track the user's fitness level
   over time, or is the current value enough?"

That's 7 questions, including the meta-grain question. The
candidate has covered all 5 Ws and "How," plus a category specific
to the prompt (Historical, for the SCD choice).

---

## Worked example — selecting questions for an OLTP hospital system

> "Design a schema for a hospital patient records system."

The candidate's 5–8 questions (note the change in emphasis):

1. **What (1)** — "What's the system of record — appointments,
   diagnoses, prescriptions, or all of the above?"
2. **What (2)** — "Are we designing the OLTP schema (the live
   patient record) or the OLAP warehouse (analytics on
   aggregates)?"
3. **Where** — "Are there regulatory constraints — HIPAA, GDPR,
   regional data residency?"
4. **How (1)** — "How are records linked — by patient ID, by
   encounter, or by both?"
5. **How (2)** — "Are diagnoses coded (ICD-10, SNOMED), free
   text, or both?"
6. **Historical** — "How do we handle a patient changing their
   name or address — overwrite, or keep history?"
7. **Edge** — "What happens when a patient is admitted under
   one identity and later merged with a duplicate record?"

Notice: the **What** is the system of record (not engagement), the
**Where** is regulatory, and the **Edge** is identity resolution.
The categories the candidate emphasizes change with the prompt.

---

## Anti-patterns — what *not* to ask

A few question types actively *hurt* your score:

- **Generic scale questions.** "How many users do you have?" without
  a follow-up is filler. Either you need the number (ask why) or
  you don't (don't ask).
- **"Is this OLTP or OLAP?"** without context. The candidate is
  punting the central decision back to the interviewer. Make an
  assumption and say it out loud.
- **Re-stating the prompt.** "So you want me to design a fitness
  app schema?" wastes 30 seconds. The interviewer has already
  given you the prompt.
- **Asking the interviewer to design it for you.** "What do you
  think the right grain is?" The interviewer is testing *your*
  judgment. Make a call.

---

## Try it

Pick any of the canonical modeling questions from
[`docs/reference/de_interview_canonical_questions.md`](../../../docs/reference/de_interview_canonical_questions.md#data-modeling-questions).
Without looking at the worked example, write 5–8 discovery questions
for it. Time yourself: 5 minutes.

Then look at the worked example (in the next three lessons) and
compare. Did you cover all 5 Ws? Did you ask the meta-grain
question? Did you avoid the anti-patterns?

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
