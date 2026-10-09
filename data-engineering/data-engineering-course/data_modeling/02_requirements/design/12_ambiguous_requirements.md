# Lesson 12 — When Requirements Are Ambiguous (and what to do)

> **What you'll learn:** the single most useful skill in a data
> modeling interview — what to do when the interviewer is vague,
> silent, or actively contradictory. By the end of this lesson
> you'll have a playbook for the four most common ambiguity
> scenarios.

---

## The four ambiguity scenarios

The interviewer is rarely as clear as the worked examples in
Lessons 07–09. In real interviews you will encounter four
ambiguity patterns:

1. **Vague prompt** — "design a data model for our product."
2. **Silent interviewer** — you ask a question and they say
   "whatever you think is right."
3. **Active contradiction** — the interviewer's answers
   contradict each other.
4. **Moving target** — the interviewer changes the requirements
   mid-round.

Each has a different playbook. The default in all four is the
same: **make a defensible assumption, say it out loud, move on.**

---

## Scenario 1 — Vague prompt

> Interviewer: "Design a data model for our product."

The product is a B2B SaaS, a marketplace, a consumer app, a
hardware company — you don't know. The prompt gives you
nothing.

### Playbook

Pick the most common reading of the prompt and commit:

> "I'm going to assume this is a B2B SaaS product with a
> subscription billing model, since 'data model' is most often
> asked in that context. If it's a marketplace or a consumer
> app, the schema would look very different — let me know if
> I'm off track and I'll redo it."

Then ask 2–3 narrow discovery questions to confirm the
assumption:

> "Before I draw, can I confirm: is this OLTP (the system of
> record) or OLAP (the warehouse)? And is the headline metric
> something like MRR / active accounts, or something like
> transactions / GMV?"

The candidate has done three things:

1. **Made a defensible assumption** ("B2B SaaS with
   subscription billing").
2. **Acknowledged the alternative** ("if it's a marketplace,
   the schema would look different").
3. **Asked narrow follow-ups** (OLTP vs OLAP; MRR vs GMV).

This is the 4/4 move. The interviewer can correct the
assumption in 10 seconds, and the candidate has the right
schema in their head already.

### Anti-pattern

> "What do you want me to design?"

This puts the burden back on the interviewer. The senior
candidate is paid to make calls, not to delegate them.

---

## Scenario 2 — Silent interviewer

> Candidate: "How is revenue defined — gross, net of refunds,
> or recognized at shipment time?"
>
> Interviewer: "Whatever you think is right."

The interviewer is testing whether you can make a call under
ambiguity. This happens more often than you'd think — about
20% of the time in real interviews.

### Playbook

Pick the most common answer in the industry, say it out loud,
and move on:

> "OK — I'll go with **net of refunds, recognized at shipment
> time** — that's the most common reading for an e-commerce
> warehouse, and it matches the headline metric of 'monthly
> net revenue.' If we discover mid-round that finance uses
> ASC 606, I'll add a `fact_recognized_revenue` table on top."

The candidate has:

1. **Made a call.**
2. **Justified it** (industry default).
3. **Acknowledged the alternative** (ASC 606).
4. **Promised a follow-up** (separate fact table if needed).

This is the same playbook as Scenario 1, applied to a
specific question. The pattern is identical: **call, justify,
acknowledge, move on**.

### Anti-pattern

> "Could you clarify what you mean by revenue?"

Asking the same question again, in different words, is a
weakness signal. The interviewer has *signaled* that you
should make the call. Make it.

---

## Scenario 3 — Active contradiction

> Candidate: "How is churn defined — voluntary cancel only,
> or all cancellations including non-payment?"
>
> Interviewer: "All cancellations. Voluntary, non-payment,
> account deletion — all of it."
>
> ... 10 minutes later ...
>
> Interviewer: "Wait, actually, let's not include
> non-payment. That's a billing issue, not a churn issue."

The interviewer has changed their mind. This happens. The
right move is to update the requirements doc in real time
and acknowledge the change.

### Playbook

> "Got it — updating the requirements: churn is now
> voluntary cancel + account deletion, but not non-payment.
> The `fact_churn_events` table will filter on
> `churn_reason != 'non_payment'`. Let me make sure the
> measures I named earlier still hold..."

The candidate has:

1. **Restated the new requirement** in their own words.
2. **Updated the artifact** (the requirements doc).
3. **Checked downstream consistency** (do the measures still
   work?).

This is the *iterative* nature of the requirements doc. It
is not a write-once-and-forget artifact. It is a living
document that updates as the interviewer's understanding
clarifies.

### Anti-pattern

Quietly ignoring the contradiction. The candidate who
proceeds with the original definition will have a wrong
schema and a confused interviewer.

---

## Scenario 4 — Moving target

> Interviewer (round 1): "Focus on the analytics team."
>
> Interviewer (round 2, depth dive): "Now show me how the
> data science team would build a churn model off this."

The interviewer is *expanding* the scope, not contradicting
themselves. This is normal — depth-dive questions test
whether your schema supports unforeseen use cases.

### Playbook

> "Great question. For churn modeling, the data science team
> would need:
> - A `target` column on the customer dim: `churned_within_30_days`
>   (refreshed daily).
> - Features derived from `fact_subscription_events`: tenure,
>   plan changes, support tickets.
> - The grain of the training set is **one row per customer**
>   (the customer-month grain doesn't work for individual
>   prediction).
>
> To support this, I'd add a `fact_customer_features_monthly`
> table at the customer-month grain, materialized daily, with
> the features the DS team needs. The training set is then a
> simple SELECT from this table with a target join."

The candidate has:

1. **Accepted the new requirement** without complaining.
2. **Named the specific additions** (target column, feature
   table).
3. **Specified the grain** (customer-month) for the new
   table.
4. **Connected it to the existing schema** (materialized
   from `fact_subscription_events`).

This is the *extension* move. The schema you drew in step 4
of the playbook (Lesson 02) needs to be extensible. Star
schemas are — that's why we use them.

### Anti-pattern

> "But you said the analytics team was the only consumer..."

The candidate who complains about scope creep loses points
fast. The interviewer is testing flexibility, not
adherence.

---

## The meta-skill: "make the call"

The through-line of all four scenarios is the same: **make
the call**. The candidate who makes ten defensible
assumptions and says each one out loud scores higher than
the candidate who asks twenty questions and never commits.

The math: ten good assumptions + ten "I'll go with X" lines
= a 4/4 candidate. Twenty clarifying questions + zero
schema = a 1/4 candidate.

This is the single most important meta-skill in the data
modeling round. It is also, incidentally, the single most
important meta-skill in being a senior engineer.

---

## Try it

Pick any of the canonical modeling questions. Time yourself:
5 minutes to design. Do not ask the interviewer any
questions. Make every assumption, say it out loud, and
design the schema. Compare your output to the worked
example in Lessons 07–09. Note where you would have asked
and whether the assumption you made was defensible.

Do this three times. The first time will be hard. The third
time, you'll notice you have a *default position* on every
ambiguity. That's the skill.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
