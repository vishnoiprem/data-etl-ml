# 02 — Discovery Interviews

> **Lesson 2 of 12 — Customer Interaction** · ~20 min

The most important customer-interaction round. Discovery is
where the deal is won or lost, where the customer's real
pain surfaces (or doesn't), and where 80% of senior SA
hires fail the round.

This lesson covers the 5-question framework, pain-point
mining, and the 5 phases of a discovery call. Lessons 06
and 07 are the worked mocks.

---

## 1. Why discovery is the highest-leverage round

A well-run discovery call surfaces the customer's actual
pain, qualifies the deal, and sets up the next 3-6 months
of the sales cycle. A poorly-run discovery call mis-diagnoses
the pain, builds false alignment, and burns time on a deal
that won't close.

The interview-round stakes are similar: a well-run
discovery mock signals "this candidate can run the kind of
call that wins deals"; a poorly-run one signals "this
candidate will lose deals they shouldn't lose." Companies
would rather have a technically weaker SA who can run a
discovery call than a technically stronger SA who can't.

This is why senior engineering candidates fail the
discovery round: they treat it like an architecture review
(*here's the solution; validate my design*) instead of
what it is (*let me understand your problem; we'll talk
solution after*).

---

## 2. The 5-question framework

The frame for almost every good discovery question. Five
question types, each with a specific purpose:

| # | Question type | Purpose | Example |
|---|---|---|---|
| 1 | **Context** | Set the scene. What does the customer's world look like today? | "Tell me about how your team handles analytics today." |
| 2 | **Problem** | Surface the pain. What's not working? | "What's the part of the workflow that's most painful?" |
| 3 | **Impact** | Quantify the pain. What's the cost of the status quo? | "What does that cost you — in time, in dollars, in missed opportunities?" |
| 4 | **Decision** | Understand the path forward. How does the customer decide? | "What does the decision-process look like on your side?" |
| 5 | **Vision** | Anchor the future. What does good look like? | "If we solved this perfectly, what's the outcome 6 months from now?" |

The 5 questions are *not* a script. They're a mental model.
You don't ask all 5 in order; you adapt to what the customer
says. But every good discovery call covers all 5 by the end.

---

## 3. The 5 phases of a discovery call

A 30-minute discovery call has 5 phases. Each phase has a
different *mode* (the SA's behavior) and a different *mode-
switch trigger* (what tells you to move on).

| Phase | Duration | SA's mode | Mode-switch trigger |
|---|---|---|---|
| **1. Frame** | 2-3 min | Set the agenda. Ask permission to take notes. | Customer agrees. |
| **2. Listen** | 5-7 min | Listen to the customer talk. Nod, take notes, ask *only* clarifying questions. | Customer pauses and looks at you expectantly. |
| **3. Dig** | 7-10 min | Ask the second question. Mine for the underlying pain. | Customer has named the underlying pain, with specifics. |
| **4. Qualify** | 5-7 min | Ask about decision-process, timeline, budget, decision-maker. | Customer has answered 4 of 5 qualification questions. |
| **5. Close** | 3-5 min | Summarize. Set expectations. Propose next steps. | Customer agrees to the next step. |

The phases flow in order, but the dig phase often loops
back into the listen phase (you ask a clarifying question,
the customer talks more, you listen again). The close
phase is the most-skipped; that's the failure.

---

## 4. Pain-point mining: the 3 levels

The 3 levels of customer pain. Most SA candidates stop at
level 1.

| Level | Definition | Example |
|---|---|---|
| **1. Surface pain** | What the customer says is wrong. | "Our pipelines are slow." |
| **2. Underlying pain** | The actual workflow problem behind the surface pain. | "Our pipelines are slow because we're running hourly batches when our users want real-time, and we can't get engineering to prioritize it." |
| **3. Aspirational pain** | What the customer wishes they could do, if the pain were solved. | "If our pipelines were real-time, we could ship an early-fraud-detection product that's been on the roadmap for 18 months." |

The "solution" the customer proposes (level 1) is often
*not* the right answer. The right answer is the workflow
fix (level 2) that unlocks the aspirational outcome
(level 3). A great SA sells the level-3 outcome, not the
level-1 fix.

A worked example:

> **Customer:** "Our pipelines are slow."
>
> **Junior SA:** "Got it, we have a faster streaming
> product. Want to see a demo?"
>
> **Senior SA:** "When you say pipelines are slow — what
> does 'slow' look like for your users? What's the
> workflow today, and what's the workflow they want?"
>
> The senior SA just opened the door to level 2 and 3.

---

## 5. The qualification questions

The 5 questions every SA should be able to answer about
the deal before they leave the call:

1. **Who** is the decision-maker? (Title, not just name.)
2. **What** is the decision-process? (How many people,
   how many steps, what's the timeline?)
3. **When** is the decision? (Specific date or quarter,
   not "later this year.")
4. **Why now?** (What's driving the urgency — new project,
   regulatory deadline, competitor pressure, internal
   mandate?)
5. **What does success look like?** (Specific outcome the
   customer will measure.)

The 5 questions are sometimes called "BANT" (Budget,
Authority, Need, Timeline) in older sales literature. The
modern version is the 5 questions above.

A "disqualifying" answer to any of the 5 is a flag:

- **No clear decision-maker** — the deal will stall.
- **No specific timeline** — the deal will become a
  science project.
- **No clear why-now** — the deal will lose to other
  priorities.
- **No specific success metric** — the deal will lose to
  internal politics at renewal.

If the customer gives you a disqualifying answer to one of
these, your job in the rest of the call is to *uncover the
underlying dis-qualifier*. Sometimes the customer can
clarify. Sometimes you have to politely disqualify and
move on.

---

## 6. The "tell me more" pattern

One pattern that signals senior SA on every call: the
"tell me more" follow-up. When the customer says something
specific (a system, a workflow, a constraint, a name), the
senior SA asks "tell me more about that," and waits.

Why this works:

- It signals listening more than any other move.
- It surfaces the *underlying* pain (the customer's first
  answer is usually surface-level).
- It builds the customer's trust ("this person actually
  cares").
- It defers the SA's pitch to a moment where the customer
  has revealed more, so the pitch is more accurate.

The junior SA cannot help but pitch after the customer's
first sentence. The senior SA asks "tell me more" 3-5
times before pitching.

A worked example:

> **Customer:** "We tried Snowflake, but the cost was
> untenable."
>
> **Junior SA:** "Ours is cheaper than Snowflake. Want a
> demo?"
>
> **Senior SA:** "Tell me more about that. What was the
> spend, and where did it bite you — was it the storage
> cost, the compute cost, or the per-user cost?"
>
> The senior SA learned something specific. The pitch,
> when it comes, will be tailored to the actual cost
> driver.

---

## 7. The close: 3 components

The most-skipped phase. Every good discovery call ends with
3 things:

1. **Summary.** "Let me make sure I heard you correctly:
   you're saying [problem], it's costing you [impact], and
   you're looking to solve it by [timeline]."
2. **Next step.** "I'll send you a 1-page technical brief
   by [date]. Does [date/time] work for a 60-minute
   working session next week?"
3. **Backup next step.** "If we don't end up needing the
   technical brief, are there other folks on your team I
   should meet to keep this moving?"

The 3 components turn the call into an *agreement*. Without
them, the call is a conversation that's easy to forget.

---

## 8. A worked example: 5-question discovery call

The scenario: a 200-person SaaS company evaluating your
data pipeline product. Their engineering team has 12
people. They currently use Airflow + Snowflake + dbt. The
SA you're playing is interviewing at the company you're
interviewing at.

The call (30 minutes):

> **SA:** "Thanks for making the time. I'd love to use our
> 30 minutes to understand how your team handles analytics
> today, what you're trying to improve, and what your
> decision-process looks like. Is that OK?"
>
> **Customer:** "Sure."
>
> **SA:** "Great. Tell me about the team — how many
> engineers, what does the analytics stack look like today,
> who's the typical user of the data?"
>
> *(Listen phase: 5-7 minutes. Customer describes their
> stack, their team, their users.)*
>
> **SA:** "What's the most painful part of that workflow
> today?"
>
> **Customer:** "Honestly, the dbt model rebuilds. We're
> running hourly batches but every time the schema changes,
> we have to rebuild 6 hours' worth of models. It blocks
> the team."
>
> **SA:** "Six hours — what does that block?"
>
> **Customer:** "Every analytics request from product is
> delayed at least half a day. The data team is constantly
> firefighting."
>
> *(Dig phase: 7-10 minutes. SA asks about the schema-
> change frequency, the cost of the delay, the impact on
> product velocity.)*
>
> **SA:** "If you could wave a magic wand and the schema-
> change problem disappeared, what would you ship?"
>
> **Customer:** "We've been sitting on a real-time
> recommendation feature for 9 months. The team's blocked
> because we can't get fresh data into the feature store."
>
> *(SA now knows: surface pain is dbt rebuilds; underlying
> pain is schema-change coupling; aspirational outcome is
> real-time recommendations. The pitch, when it comes, is
> about real-time feature stores, NOT about dbt rebuilds.)*
>
> **SA:** "Helpful — real-time recommendations for your
> product, blocked by the feature-store freshness. Let me
> ask about the decision process. Who on your team owns
> this evaluation, and how does the decision get made?"
>
> *(Qualify phase: 5-7 minutes. SA identifies the decision-
> maker — typically the Director of Data — and the
> decision-process — POC + CTO sign-off.)*
>
> **SA:** "And what's the timeline? Is this something
> you're looking at this quarter or next?"
>
> **Customer:** "We'd love to be in production by end of
> Q2."
>
> **SA:** "Got it — about 4 months from now. Two follow-
> ups. First, what's driving the timeline? Is there a
> product launch, a board deadline, or something else?"
>
> **Customer:** "Our board wants to see a 10% lift in
> engagement from recommendations by end of Q2."
>
> *(SA now knows the why-now: a board commitment with a
> specific metric.)*
>
> **SA:** "Helpful, last set of questions. What's your
> budget range for this, and is there a competing
> evaluation happening in parallel?"
>
> **Customer:** "We've budgeted $200-400k, and we're also
> talking to a competitor, but we like your approach
> better so far."
>
> *(Qualify phase concludes. SA knows: budget $200-400k,
> one competitor in the mix, customer prefers your
> approach.)*
>
> **SA:** "Let me make sure I heard you correctly. Your
> team is on Airflow + Snowflake + dbt, today. The dbt
> rebuilds are blocking you from shipping real-time
> recommendations, which the board has committed to by
> end of Q2. You're evaluating us alongside a competitor,
> with a budget of $200-400k. That's right?"
>
> **Customer:** "Yeah."
>
> **SA:** "Here's what I'd like to do. I'll send you a
> 1-page technical brief on how we typically handle this
> architecture by Thursday. Does Tuesday at 2pm work for a
> 60-minute working session to walk through it together?"
>
> **Customer:** "Tuesday at 2 works."
>
> **SA:** "Perfect. I'll send a calendar invite. If there's
> anyone else on your team who should be in that
> conversation, let me know."

That's a 4/4 discovery call. The SA:

- Asked the second question ("six hours — what does that
  block?")
- Identified the underlying pain (schema-change coupling),
  not just the surface pain (slow rebuilds).
- Reframed the problem around the customer's customer
  (the end-user of the real-time recommendations).
- Qualified all 5 (decision-maker, process, timeline,
  budget, why-now).
- Closed with a specific summary, a specific next step,
  and a backup.

A junior SA, by contrast, would have started pitching at
minute 5: "we have incremental dbt models that solve this."
That's the wrong move — the customer would say "we've
already tried that" or "that's not actually our problem."

---

## Try it

Pick a scenario in your specialty. Run a 30-minute mock
discovery call, with a friend playing the customer or by
yourself in front of a mirror (it works, awkwardly).

Hit all 5 phases. Use the 5-question framework. Ask the
second question. Get to the level-3 pain. Qualify all 5.
Close with a specific summary and a specific next step.

Record it. Listen back. The first time you listen back you
will cringe. The second time you'll see what worked. The
third time you'll hear the small things — pauses,
affirmations, follow-ups — that made it feel like a real
conversation.

Do this once a week for 4 weeks. By the 4th week, you'll
be able to do it without notes, on any scenario. That's
the bar.
