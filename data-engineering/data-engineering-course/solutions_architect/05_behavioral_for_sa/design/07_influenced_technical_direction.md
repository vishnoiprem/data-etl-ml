# 07 — Tell Me about a Time You Influenced a Customer's Technical Direction

> **Lesson 7 of 11 — Behavioral for SAs** · ~12 min

The senior SA move: influence the customer's technical
direction *with* the customer, not *on* the customer.
A worked STAR story, with 2 variations.

---

## 1. The question

> *"Tell me about a time you influenced a customer's
> technical direction."*

This question tests 4 signals:

- **Customer focus.** Did the customer come along, or
  were they pushed?
- **Technical judgment.** Did your influence improve
  the customer's outcome?
- **Influence without authority.** You don't have
  authority over the customer's team — how did you
  influence anyway?
- **Communication.** Did you explain the tradeoffs
  clearly enough for the customer to choose?

The senior SA move is to *frame the influence as
service*. The SA doesn't push the customer; the SA
*helps the customer see* the right answer. The
customer feels ownership of the final choice.

---

## 2. The worked STAR story (Priya, Sr. SA at Snowflake)

> **Situation (12 sec):** "A Fortune 500 financial-
> services customer — anonymized due to NDA — was
> building a real-time fraud-detection pipeline. Their
> initial design used a streaming database plus a
> batch-loaded feature store. They were 4 months into
> the project and the architecture was creating
> bottlenecks — the feature store was 15 minutes
> stale, which meant the fraud model was operating
> on data that was 15 minutes old."
>
> **Task (8 sec):** "I was the technical SA on the
> engagement. I was accountable for the customer's
> real-time feature store architecture standing up
> to the CISO's review and the fraud model's
> accuracy requirement."
>
> **Action (55 sec):** "I had a 90-minute working
> session with the customer's data engineering team
> and their principal ML engineer. I came prepared
> with 3 alternative architectures, each with a
> tradeoff analysis: cost, latency, operational
> burden. I also came with a recommendation — a
> streaming feature store with sub-second freshness
> — and a clear rationale for why I thought it was
> the right answer.
>
> The session went well, but the customer's principal
> ML engineer pushed back on the streaming feature
> store. They were concerned about the operational
> complexity — they had limited SRE capacity.
>
> I shifted the conversation: instead of pushing the
> streaming feature store as the only answer, I asked
> the customer to map their actual freshness
> requirements to each option. We spent 30 minutes
> walking through the fraud-detection workflow at
> the per-transaction level. The customer realized
> that sub-second freshness was required for 70% of
> the use cases, but 30% could tolerate minute-level
> freshness with a different architecture.
>
> I proposed a hybrid: streaming feature store for
> the 70% (the high-value use cases), batch-loaded
> feature store for the 30% (the lower-value use
> cases). The hybrid cut the operational complexity
> by half while meeting the freshness requirements
> for all use cases."
>
> **Result (15 sec):** "The customer adopted the
> hybrid architecture. The fraud model's accuracy
> improved by 18% (the 70% use cases got sub-second
> data), the operational complexity was manageable
> (the 30% stayed on the batch-loaded store), and
> the project went live on schedule 3 months later.
> The customer cited the architecture working
> session as the moment the project turned around."
>
> **Reflection (10 sec):** "The transferable lesson:
> influence is not pushing. The right move when
> you disagree with a customer's technical direction
> is to *help them see* the tradeoffs, not to
> prescribe the answer. The customer will find a
> better answer than you would, because they know
> their workflow better than you do. My role is to
> structure the conversation so the right answer
> surfaces. I now go into every architecture
> conversation with 3 options and a 'help them
> see' framing, not a 'convince them' framing."

---

## 3. The 4 signals the story hits

1. **Customer focus.** The customer adopted the hybrid
   architecture because they understood the tradeoffs.
   Priya *helped* the customer see, not *pushed* the
   answer.
2. **Technical judgment.** The 3 options with tradeoff
   analysis is the senior SA move. The hybrid
   architecture is the *senior SA* answer — neither
   pure streaming nor pure batch.
3. **Influence without authority.** Priya is the SA;
   the customer's team owns the architecture. The
   influence was through *framing the conversation*,
   not authority.
4. **Communication.** The 3 options, the tradeoff
   analysis, the per-transaction walk-through — all
   are communication moves that surface the right
   answer.

The story is a 4/4.

---

## 4. The 2 variations for your own story

### Variation A: Focus on the cross-functional aspect

Same story, reframed around the stakeholders:

> "...There were 3 stakeholders who needed to
> align: the data engineering team (who owned the
> pipeline), the principal ML engineer (who owned
> the model), and the CISO (who needed to approve
> the security architecture). The breakthrough came
> when we did a 90-minute working session with all
> three in the room..."

This variation emphasizes the multi-stakeholder
aspect.

### Variation B: Focus on the customer's customer

Same story, reframed around the end-user:

> "...The fraud model's accuracy was 18% better
> with the hybrid architecture. That 18% translated
> to $12M/year in additional fraud caught, based on
> the customer's average fraud-loss rate. The
> architecture wasn't just technically better — it
> served the customer *and* the customer's
> customer (the end-consumer whose transactions
> were being protected)..."

This variation emphasizes the customer's customer.

---

## 5. The "3 options" framework

The single most useful pattern for "influence a
customer" stories. The pattern:

- **Bring 3 options.** Not 1 (too pushy), not 5 (too
  many). 3 is the right number — it gives the customer
  choice without overwhelming.
- **Each option has a tradeoff analysis.** Cost,
  latency, operational burden, scalability. The
  tradeoffs are the *substance* of the conversation.
- **Bring a recommendation.** "If I were in your
  shoes, I'd pick option B. Here's why." The
  recommendation is *your* view; the customer can
  accept or reject.
- **Let the customer choose.** After the conversation,
  the customer owns the decision. The SA's role is to
  *help them see*, not to *make* the decision.

The 3-options pattern is the senior SA move. The
junior SA either brings 1 option (pushy) or 5 options
(overwhelming). The senior SA brings 3, with
tradeoffs, and a recommendation.

---

## 6. The 3 anti-patterns for this question

### Anti-pattern 1: "I told them what to do"

You tell the story as "I convinced the customer to
use our product / approach." The interviewer reads this
as "I'm a vendor, not a partner."

**Fix:** Reframe as "I helped the customer see the
tradeoffs so they could choose." The customer owns
the decision.

### Anti-pattern 2: No customer input

The story is about your technical brilliance. The
customer's input is absent. The interviewer reads
this as "I don't listen."

**Fix:** The customer's input is the lead. The
customer's workflow, the customer's constraints, the
customer's choice. The SA's role is to structure the
conversation.

### Anti-pattern 3: Vague technical change

The "influence" is unclear. "I helped them think
differently about their architecture" is too vague.
The interviewer reads this as "I didn't actually
influence anything specific."

**Fix:** Name the specific change. "The customer
adopted a streaming feature store, replacing their
batch-loaded store." The change is concrete and
*measurable*.

---

## Try it

Identify a real customer engagement where you
influenced the technical direction. Use the 5-step
process from Lesson 04. Write the STAR story in
90-120 seconds.

Then write the 2 variations. The variations are how
you get 3 stories from 1 experience.

Re-tell out loud. Record. Listen back. The first
time, you'll notice the moments where you sound
pushy or where the customer is missing. Reframe
those. By the 3rd time, the story will be clean.

If you can produce all 3 variations cleanly, you have
1 anchor story that covers 3 of the 12 most-asked
questions. That's leverage.
