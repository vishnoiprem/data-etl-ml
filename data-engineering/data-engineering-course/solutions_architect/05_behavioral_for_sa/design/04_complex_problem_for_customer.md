# 04 — Solving a Complex Problem For a Customer

> **Lesson 4 of 11 — Behavioral for SAs** · ~15 min

The most-asked SA behavioral question: "Tell me about a
time you solved a complex problem for a customer." A
worked STAR story, with 2 alternatives, plus the
"anchor story" version you can pull from your own
experience.

---

## 1. The question

> *"Tell me about a time you solved a complex problem
> for a customer."*

This question tests 4 signals:

- **Technical depth.** Did you understand the problem
  deeply enough to solve it?
- **Customer focus.** Was the customer the protagonist?
- **Persistence.** Did you push through complications?
- **Communication.** Did you explain the problem and the
  solution to the customer clearly?

The senior SA move is to anchor on the customer's
problem, not on your technical skills. The story is
about *their* outcome, not *your* brilliance.

---

## 2. The worked STAR story (Sam, Sr. SA at AWS)

> **Situation (12 sec):** "A Fortune 500 healthcare
> customer — anonymized due to NDA — was migrating
> their patient records system to a cloud data lake.
> The migration had stalled because their existing
> ETL pipeline couldn't handle the volume of incoming
> clinical data — they were 6 weeks behind on the
> ingestion of new patient records, which meant
> clinicians were working with stale data and the
> customer's compliance team was escalating."
>
> **Task (8 sec):** "I was the technical SA on the
> engagement. I was accountable for getting the
> customer's ingestion pipeline unblocked and the
> migration back on schedule within 8 weeks."
>
> **Action (55 sec):** "The first thing I did was
> spend 3 full days with the customer's data
> engineering team, observing their existing pipeline
> and the actual clinical data flowing through. I
> confirmed what the customer had told me, but I also
> found two things they hadn't: their schema was
> evolving 10x faster than their pipeline was
> designed for, and their upstream clinical systems
> were emitting duplicate events at a rate they hadn't
> measured.
>
> I worked with the customer's principal engineer to
> redesign the ingestion pipeline with a schema-registry-
> aware approach and a deduplication layer. The redesign
> cut the schema-evolution problem from a 6-week manual
> cycle to a 1-day automated cycle, and the deduplication
> layer caught the duplicate events without data loss.
>
> Throughout the 8 weeks, I held a weekly 30-minute
> working session with the customer's data engineering
> team and their compliance team to track progress.
> The compliance team became a stakeholder I'd
> underestimated — they cared more about audit trail
> than I'd assumed."
>
> **Result (15 sec):** "The customer's ingestion
> pipeline was unblocked in 7 weeks. They caught up
> the 6-week backlog within the following 4 weeks.
> The patient's records were fresh for clinicians
> again, and the compliance team's audit trail was
> complete. The customer went on to expand the
> engagement to 3 additional data domains, adding
> $1.5M/year to the deal."
>
> **Reflection (10 sec):** "The transferable lesson:
> when a customer says their pipeline is slow, the
> real problem is usually 2-3 specific things they
> haven't measured. Spending 3 days observing the
> pipeline (not just asking questions) is what
> surfaces the real problems. I now insist on
> spending at least 1-2 days observing the customer's
> workflow before designing anything, on every
> engagement."

---

## 3. The 3 signals the story hits

The story signals 3 things to the interviewer:

1. **Technical depth.** The candidate understood
   schema evolution and deduplication enough to
   redesign the pipeline. The redesign was
   *specific*, not generic.
2. **Customer focus.** The customer is the protagonist.
   The compliance team is named as an underestimated
   stakeholder. The customer outcome (fresh records,
   audit trail, expansion) is the lead.
3. **Listening and humility.** The candidate spent 3
   days *observing* before designing. The candidate
   underestimated the compliance team initially.
   Both are senior-SA moves — the candidate listens
   before pitching.

The story is a 4/4.

---

## 4. The 2 alternatives for your own story

Two variations that work for different angles:

### Variation A: Focus on the technical learning

Same story, reframed around the technology:

> "...The technical learning for me was that schema
> evolution in healthcare is qualitatively different
> from other industries — clinical data systems add
> new measurement types and new lab codes monthly,
> and the schema has to evolve without breaking
> downstream models. I had worked on schema evolution
> before but never at this rate..."

This variation answers "Tell me about a time you had
to learn a new technology quickly" — the focus is on
the technical learning.

### Variation B: Focus on the cross-functional
collaboration

Same story, reframed around the stakeholders:

> "...The 3 most important stakeholders were the
> customer's data engineering team (who owned the
> pipeline), their compliance team (who needed the
> audit trail), and our AWS account team (who needed
> the deal to close). I had to keep all three aligned
> with weekly checkpoints, separate communication
> channels, and a shared document. The compliance
> team's buy-in was actually the hardest — they were
> initially skeptical..."

This variation answers "Tell me about a time you
worked across multiple stakeholders" — the focus is
on the cross-functional collaboration.

---

## 5. The 5-step process for your own story

Step-by-step for writing your own "complex problem for
a customer" story:

1. **Identify a real customer-facing project with
   material impact.** Not a small project — the story
   needs to have stakes.
2. **Write the raw story from memory.** Don't filter;
   just write everything you remember.
3. **Identify the customer.** Name them or anonymize
   specifically.
4. **Reframe in SA-flavored STAR.** Apply the 4
   differences from Lesson 03.
5. **Time yourself out loud.** Adjust until it's 90-120
   seconds.

The 5-step process is the *spine* for every story in
your bank.

---

## 6. The 3 common failure modes for this question

### Failure mode 1: Internal-engineering story

You tell a story about how you fixed a bug in your
team's pipeline. The customer is not mentioned. The
interviewer reads this as "I haven't done customer-
facing work at the SA level."

**Fix:** Reframe with the customer. If the bug fix
benefited a customer, name the customer. If not, pick
a different story — this question is asking for a
*customer-facing* complex problem.

### Failure mode 2: The story is about the customer's
problem, not your work

You tell a story about how the customer had a hard
problem and they eventually solved it themselves.
You're a minor character, not the protagonist. The
interviewer reads this as "I didn't actually solve
the problem."

**Fix:** Reframe around *your* actions. The customer's
problem is the context; *your* actions are the story.
Even if many people were involved, *your* specific
contributions are the lead.

### Failure mode 3: The story is about a teammate's
work

You tell a story about how your colleague did the hard
work and you supported them. The colleague is the
protagonist; you're a supporting character. The
interviewer reads this as "I take a back seat."

**Fix:** Reframe around *your* work. Even if a
colleague contributed, focus on the parts *you*
specifically did. The story is yours, not theirs.

---

## Try it

Write your own "complex problem for a customer" story
using the 5-step process. Aim for 90-120 seconds.

Then write the 2 variations (focus on technical learning;
focus on cross-functional collaboration). These are 3
stories from 1 experience, which is the senior SA
move.

Re-tell each out loud. Record yourself. Listen back.
The first time you listen back, you'll hear 5 things to
fix. The second time, 3. By the third time, the story
will be tight.

If you can produce all 3 variations cleanly, you have
1 anchor story that covers 3 of the 12 most-asked
questions. That's leverage.
