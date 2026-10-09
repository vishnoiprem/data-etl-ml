# 17 — Working with PM and Design

> **Lesson 17 of 21 — Cross-functional Collaboration** · ~20 min

How to disagree with a PM without blocking, the "data tells
us X, what do you think" script, and the EM-as-translator
pattern. The PM/Design partnership is the EM's most-frequent
cross-functional relationship — and the one where most
engineers have the least training.

---

## 1. The PM/EM relationship is a partnership

The PM owns the *what* and the *why*. The EM owns the *how*
and the *who*. The senior move is to **respect the split**
and to **negotiate the overlaps explicitly**.

The 4 areas of overlap:

| Area | PM's perspective | EM's perspective | How to resolve |
|---|---|---|---|
| **Scope** | What's in, what's out | What's realistic to ship | The "definition of done" doc (Lesson 05) |
| **Timeline** | When the customer needs it | When we can ship it | The sprint plan (Lesson 11) with explicit tradeoffs |
| **Quality** | What's good enough for the customer | What's good enough for the codebase | Explicit quality bar at kickoff |
| **Prioritization** | What we do next | What we defer to next quarter | The quarterly roadmap (Lesson 11) |

The mistake new EMs make: **defaulting to the PM's answer on
the overlaps**. The PM has more practice at the relationship,
and the EM ends up rubber-stamping scope and timeline. The
senior move is to **push back on the overlaps** with specific
tradeoffs, in writing.

The other mistake: **never disagreeing with the PM**. The
EM who never says "this scope is too big" is the EM whose team
burns out. The senior move is to disagree specifically,
constructively, and with a proposed alternative.

---

## 2. The "data tells us X, what do you think" script

The most useful script for disagreeing with a PM is to **lead
with the data, not the opinion**. The PM is trained to
discount opinions ("you're just being conservative"). The PM
is not trained to discount data.

The script:

> *"I want to surface a concern about [X]. The data tells
> us [specific finding]: [1-2 sentences on the data, with
> numbers]. The implication I'm drawing is [specific
> implication, with reasoning]. I'm not sure that's the
> right read — what do you think?"*

The senior move is the last sentence. The PM might have a
context you're missing (a customer conversation, a strategy
shift). The data is the substrate for the conversation; the
PM's context is the substrate for the decision. Both are
needed.

The mistake: presenting the data as a conclusion instead of
a starting point. The PM who feels lectured is the PM who
pushes back hard. The PM who's asked to weigh in is the PM
who collaborates.

---

## 3. The Design partnership

The Design partnership has a different shape. The PM owns
the *what*; the Designer owns the *how it feels*; the EM
owns the *how it works*. The senior move is to **involve
Design early** — at the kickoff of the project, not after
the engineering work has started.

The 3 things the EM owns with Design:

1. **The technical feasibility conversation.** When the
   designer proposes an interaction pattern, the EM (or
   a delegated engineer) assesses the technical cost.
   The senior move is to **be specific about the cost** —
   "this adds 2 weeks of work for 1 engineer because of
   X," not "this is hard."
2. **The design review.** The designer should review the
   shipped product before it goes to the customer. The
   EM's job is to make sure the engineering work doesn't
   ship without the design review.
3. **The post-launch feedback.** The EM should share
   customer feedback with the designer, especially the
   feedback that's about the *interaction* (not the
   *functionality*). Designers can't iterate without
   feedback.

---

## 4. The EM-as-translator pattern

The EM is the translator between the technical team and
the PM/Design team. The 3 translations the EM does:

1. **Engineering → PM/Design.** The engineer says "we can't
   ship this in 2 weeks because of [technical detail]." The
   EM translates to "this scope is bigger than we estimated,
   here's the tradeoff — either we cut [X] or we extend by
   [Y]." The PM can act on the second; not the first.
2. **PM/Design → Engineering.** The PM says "the customer
   needs [Z]." The EM translates to "the customer
   requirement is [Z], the technical implication is
   [W], here's what the team is going to need to make
   that work." The engineer can act on the second; not
   the first.
3. **Constraints → Solutions.** Both sides come to the EM
   with constraints ("we can't add 2 weeks," "we can't
   cut the feature"). The EM's job is to find the third
   option that neither side saw.

The mistake new EMs make: doing the translation silently
and presenting the output as their own. The senior move is
to **make the translation visible** — "the PM said X, I
translated to Y, here's what we're proposing." The
visibility is what builds trust with both sides.

---

## 5. The "disagreement that's become a blocker" intervention

Sometimes the EM/PM relationship has degraded to the point
where every decision is a re-litigation. The senior move is
to **intervene explicitly**.

The script:

> *"I want to step back and name something I think we're
> both feeling: the last 3 weeks have felt like we're
> re-deciding things we'd already decided. I want to
> reset. Here's what I propose: (1) we sit down for 60
> minutes with no Slack, no calendar pressure, and align
> on the [quarterly roadmap / current sprint / specific
> project]. (2) Any change to that alignment goes through
> a 30-minute 'cost of change' conversation before we
> agree. (3) We commit to the alignment in writing. What
> do you think?"*

The senior move is to **name the pattern explicitly**.
The PM who knows there's a problem is the PM who wants to
fix it. The PM who doesn't know is the PM who'll be
surprised when the EM escalates.

---

## 6. A worked example: disagreeing with the PM on scope

The PM wants to add a new feature to the streaming
migration. The migration is already 2 weeks behind schedule.
Sam disagrees.

> **Sam:** "I want to surface a concern about adding the
> new feature to the migration. The data tells us the
> migration is already 2 weeks behind the original
> timeline, and adding the new feature would extend it
> by another 3 weeks based on the design work. The
> implication I'm drawing is that the migration's
> September 15 target slips to October 6, and the top
> customer renewal at risk. I'm not sure that's the
> right read — what do you think? Is there a reason
> the new feature has to be in this migration vs. the
> next one?"
>
> **PM:** "The new feature came up in a customer call
> yesterday. It's not a hard deadline, but it would
> strengthen the renewal story."
>
> **Sam:** "Here's what I propose: we ship the migration
> on September 15 without the new feature, and we scope
> the new feature as a 2-week project starting October
> 1. That way the migration lands on the customer
> renewal, and the new feature lands 4 weeks later. The
> PM and I can co-present the roadmap to the customer
> to make sure the new feature commitment is visible."
>
> **PM:** "That works. Let's write it up."

**What makes this land:** The data leads. The implication
is specific (September 15 → October 6, customer renewal).
The PM is asked to weigh in, not lectured. The proposal
preserves the PM's goal (customer relationship) while
protecting the team's timeline. The outcome is in writing.

---

## 7. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- People Management #3: *"Tell me about a time when you
  dealt with a conflict with engineers."*
- Behavioral #1: *"Tell me about a time when you handled a
  difficult stakeholder."*
- Behavioral #27: *"Tell me about a time you had to work
  with a difficult team member."*
- Behavioral #84: *"Tell me about a time when you had to
  build a relationship with a stakeholder."*
- Behavioral #120: *"Tell me about a time when you had to
  influence someone without authority."*

---

## Try it

Identify a current disagreement with a PM or a Design
partner. Write the disagreement using the "data tells us
X, what do you think" script. Notice how the script forces
you to lead with data, name the implication, and invite
the partner to weigh in. The senior move is the discipline
of the script, even when the disagreement is emotional.

---

## Action item

This week, schedule a 60-minute reset conversation with
your PM partner (using the intervention script in
section 5 if needed). The reset is the senior move that
prevents the next escalation.