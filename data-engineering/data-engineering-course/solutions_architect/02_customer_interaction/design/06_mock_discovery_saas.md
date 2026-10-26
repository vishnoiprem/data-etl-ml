# 06 — Mock Discovery: SaaS Company Onboarding

> **Lesson 6 of 12 — Customer Interaction** · ~15 min

A full 5-minute mock discovery call transcript with analysis.
A 200-person SaaS company evaluating your data pipeline
product. The candidate is playing the SA; the interviewer
is playing the customer's Director of Data.

This is the most common senior SA interview scenario. Read
it twice — once for content, once for the *moves* the
candidate makes. Then run your own mock with a friend.

---

## 1. The setup

- **Candidate:** Sam, 8 years data engineering, current
  Senior DE. Interviewing for Senior SA at a data
  infrastructure vendor.
- **Interviewer:** Jordan, Principal SA at the vendor. Plays
  the role of "Director of Data" at a 200-person SaaS
  company.
- **Round:** 30 minutes total — 5 minutes of setup, 20
  minutes of discovery, 5 minutes of close.
- **Scenario:** The 200-person SaaS company is evaluating
  the vendor's data pipeline product to replace their
  current Airflow + Snowflake + dbt stack.

The transcript below is the 20-minute middle section,
lightly compressed for readability. The opening and close
are condensed.

---

## 2. The transcript

> **Sam:** "Thanks for making the time, Jordan. I'd love
> to use our 30 minutes to understand how your team
> handles analytics today, what you're trying to improve,
> and what your decision-process looks like. Is that OK?"
>
> **Jordan:** "Sure, sounds good."
>
> **Sam:** "Great. To start, tell me about the team —
> how many engineers, what does your analytics stack look
> like, and who's the typical user of the data?"
>
> **Jordan:** "We have 12 data engineers, mostly working
> on internal analytics. Our stack is Airflow for
> orchestration, Snowflake for the warehouse, and dbt
> for transformations. The typical user is a product
> manager or analyst who needs dashboards or ad-hoc
> queries."
>
> **Sam:** "Got it — Airflow + Snowflake + dbt, 12
> engineers, internal analytics. What's the most painful
> part of that workflow today?"
>
> **Jordan:** "Honestly, the dbt model rebuilds. We're
> running hourly batches, but every time the schema
> changes, we have to rebuild 6 hours' worth of models.
> It blocks the team."
>
> **Sam:** "Six hours — what does that block?"
>
> **Jordan:** "Every analytics request from product is
> delayed at least half a day. The data team is constantly
> firefighting instead of shipping new analytics."
>
> **Sam:** "Helpful. Let me make sure I understand — when
> the schema changes, the dbt models that depend on it
> need to be rebuilt, and that takes 6 hours, which
> delays downstream product requests. Is that right?"
>
> **Jordan:** "Exactly."
>
> **Sam:** "How often does the schema change? Is this
> something that happens every week, every day, every
> hour?"
>
> **Jordan:** "Probably every week or two, depending on
> what product is shipping. Some weeks it's daily."
>
> **Sam:** "Got it. And when the schema changes, is the
> downstream impact a half-day delay, or does it cascade
> into multiple days?"
>
> **Jordan:** "It's usually a half-day if the change is
> backward-compatible. But if it's a breaking change —
> which happens maybe once a month — the team spends 2-3
> days on it."
>
> **Sam:** "Helpful. So the pattern is: 90% of the time,
> it's a half-day delay. 10% of the time, it's 2-3 days
> of firefighting. Is that fair?"
>
> **Jordan:** "Yeah, that's about right."
>
> **Sam:** "OK. Let me ask a different question. If the
> schema-change problem disappeared tomorrow, what would
> your team ship that they can't ship today?"
>
> **Jordan:** "We've been sitting on a real-time
> recommendation feature for 9 months. The team's blocked
> because we can't get fresh data into the feature store.
> And the analytics team has 4 product analytics use cases
> queued up that would be more valuable if they were
> real-time instead of hourly."
>
> **Sam:** "So if I heard you correctly, the schema-
> change coupling is blocking two things: a real-time
> recommendation feature that's been waiting 9 months, and
> 4 product analytics use cases that need fresher data.
> Is that the full picture?"
>
> **Jordan:** "Yeah, that captures it."
>
> **Sam:** "Helpful. Let me ask about the decision
> process. Who on your team owns this evaluation, and how
> does the decision get made?"
>
> **Jordan:** "I do, ultimately. But the CTO needs to
> sign off because of the budget. And our platform team
> would evaluate the integration."
>
> **Sam:** "OK — you're the decision-maker, the CTO
> signs off on budget, and the platform team evaluates
> the integration. Three people involved. What's the
> timeline? Are you looking at this quarter, next
> quarter, or later?"
>
> **Jordan:** "We'd love to be in production by end of
> Q2, so about 4 months from now."
>
> **Sam:** "What's driving the timeline? Is there a
> product launch, a board deadline, or something else?"
>
> **Jordan:** "Our board has committed to a 10% lift in
> engagement from recommendations by end of Q2. Without
> real-time recommendations, we won't hit it."
>
> **Sam:** "Got it — a board commitment with a specific
> metric. Two more questions. What's your budget range,
> and are you evaluating other vendors in parallel?"
>
> **Jordan:** "We've budgeted $200-400k for this, and
> we're also talking to [competitor], but I like your
> approach better so far."
>
> **Sam:** "Helpful. Let me make sure I heard you
> correctly. Your team is on Airflow + Snowflake + dbt
> today. The dbt rebuilds are blocking you from shipping
> real-time recommendations, which the board has committed
> to by end of Q2. The decision is yours with CTO
> sign-off and platform team input, and you've budgeted
> $200-400k. You're also talking to [competitor] but
> prefer our approach so far. Is that the picture?"
>
> **Jordan:** "Yeah, that's right."
>
> **Sam:** "Here's what I'd suggest. I'll send you a
> 1-page technical brief on how we typically handle
> schema evolution in this kind of setup by Thursday.
> Does Tuesday at 2pm work for a 60-minute working
> session where we walk through it together? I'd also
> suggest we get the platform team and the CTO on the
> working session, so we can address the integration
> and the budget question in the same call."
>
> **Jordan:** "Tuesday at 2 works. Let me check with the
> platform team and the CTO — I'll get back to you by
> EOD tomorrow."
>
> **Sam:** "Perfect. I'll send a calendar invite for
> Tuesday at 2pm as a placeholder. If anyone can't
> make it, let me know and we'll find a time that
> works for the full group."

---

## 3. The analysis

### What Sam did well

- **Set the agenda in the first 30 seconds.** Sam
  explicitly named the 3 goals (understand the team's
  workflow, understand the pain, understand the
  decision-process) and asked permission. The customer
  knew what to expect.
- **Asked the second question.** When Jordan said
  "6-hour rebuilds," Sam asked "6 hours — what does
  that block?" The question surfaced the real pain
  (delayed product requests), not the surface pain
  (slow rebuilds).
- **Quantified the pain.** Sam asked "how often does
  this happen?" and "is the downstream impact a half-
  day or multiple days?" — which surfaced the 90/10
  pattern (half-day most of the time, 2-3 days 10%
  of the time). The quantification is what makes the
  pain concrete.
- **Reached the level-3 pain.** When Sam asked "if the
  schema-change problem disappeared, what would you
  ship?", Jordan revealed the real goal: real-time
  recommendations. The pitch, when it comes, will be
  about real-time feature stores, not dbt rebuilds.
- **Qualified all 5 (decision-maker, process, timeline,
  why-now, budget).** Sam explicitly asked about each.
  The qualification is what makes the call an
  *agreement*, not a conversation.
- **Closed with a specific next step.** Sam proposed a
  1-page technical brief by Thursday, a 60-minute
  working session Tuesday at 2pm, and a placeholder
  calendar invite. The customer knows exactly what
  happens next.

### What Sam could have done better

- **Asked about the customer's customer.** Sam
  anchored on the data team's pain (delayed product
  requests) but didn't go further to the *end-user*
  of the real-time recommendations. A senior SA move
  would be: "when the recommendations are real-time,
  what does that look like for your end-users?"
  Anchoring on the customer's customer deepens the
  trust.
- **Asked about the competitor more.** Jordan mentioned
  a competitor in passing; Sam didn't dig in. A
  senior SA move would be: "what's [competitor] doing
  well that you like, and what would you want us to
  do better?" This both clarifies the competitive
  position and surfaces unstated objections.
- **The "backup" close.** Sam's close was strong, but
  he didn't have a backup if Tuesday at 2pm didn't
  work. A 4/4 close would: "if Tuesday at 2 doesn't
  work for the full group, can we set a separate
  working session with you and the platform team
  first, and then the full group later?"

### The rubric score

| Signal | Score |
|---|---|
| **Active listening** | 4/4 — summarizing, asking clarifying questions, asking the second question |
| **Pain-point discovery** | 4/4 — reached level 3 (real-time recommendations) |
| **Qualification** | 3.5/4 — all 5 covered, but "the platform team" was loose; could have asked for names |
| **Customer's customer** | 2.5/4 — didn't anchor on the end-user |
| **Closing the call** | 4/4 — specific summary, specific next step, calendar placeholder |

**Overall: 3.6/4.** A strong "hire" with one area to grow
(customer's customer anchoring).

---

## 4. The 6 moves to borrow

If you're going to steal 6 moves from Sam's transcript,
steal these:

1. **"I'd love to use our 30 minutes to [goal 1], [goal
   2], [goal 3]. Is that OK?"** — the agenda-setting
   opening.
2. **"What does that block?"** — the second-question
   pattern.
3. **"How often does that happen?"** — the quantification
   pattern.
4. **"If the problem disappeared, what would you ship?"**
   — the level-3 pain question.
5. **"Who's the decision-maker, what's the process,
   what's the timeline, what's the why-now, what's the
   budget?"** — the 5-question qualification.
6. **"Let me make sure I heard you correctly."** — the
   summary pattern that closes the call.

The 6 moves are the spine of a 4/4 discovery call. The
rest is adapting to what the customer says.

---

## Try it

Run the same scenario with a friend. Have your friend
play "Director of Data at a 200-person SaaS company,"
using Jordan's script above (or improvising a different
spin).

You play Sam. Hit the 6 moves. Record it. Listen back.

If you do this 3 times, you'll have the 6 moves in your
muscle memory. By the 3rd time, you'll find yourself
using them in other conversations (with real customers,
with your manager, with your team) — which is the sign
that you've internalized them.

Do the 3 mocks in the next 2 weeks, before your next
interview. The investment is 90 minutes; the return is
the discovery round.
