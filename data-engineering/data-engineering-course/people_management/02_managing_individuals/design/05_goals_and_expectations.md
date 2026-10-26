# 05 — Setting Goals and Expectations

> **Lesson 5 of 21 — Managing Individuals** · ~20 min

OKRs vs MBOs vs SMART, what to do when goals change mid-cycle, and
how to set expectations that survive reality. Goals are the
substrate for performance management — if the goals are clear,
the rest of the work is easier than it looks.

---

## 1. The 3 goal frameworks (and when to use each)

There are 3 goal frameworks you'll encounter in industry. Each
has a place. Most EMs pick one and try to apply it to
everything; the senior move is to use the right one for the
right context.

### OKRs (Objectives and Key Results)

**What it is:** A qualitative Objective paired with 3-5
quantitative Key Results. Originated at Intel, popularized by
Google. Used heavily at Google, Meta, LinkedIn, and most SV
companies.

**Example:**
- **O:** Make our data pipeline the most reliable in the company
- **KR1:** Reduce dashboard error rate from 4% to <0.5%
- **KR2:** Reduce incident MTTR from 45 min to <15 min
- **KR3:** Migrate 3 critical pipelines to the new schema with 0
  downstream breakage

**When to use it:** Annual or quarterly org-level alignment.
Good for communicating direction. Bad for individual contributor
goal-setting because the KRs are too coarse to track weekly.

### MBOs (Management by Objectives)

**What it is:** Peter Drucker's framework. Each person has 3-5
specific, measurable objectives for the cycle. Reviewed mid-cycle
and at the end. Used at GE, many traditional companies, and
some SV holdouts.

**Example:**
- "Ship the schema migration by end of Q2 with 0 downstream
  breakage."
- "Mentor Jordan through the on-call rotation, with the goal of
  him being able to lead an incident response by end of Q2."

**When to use it:** Per-person accountability. Good for IC
goals. Bad for org-level alignment because the objectives don't
nest.

### SMART goals

**What it is:** Specific, Measurable, Achievable, Relevant,
Time-bound. Originated in the 1980s corporate training
literature. Used everywhere, but rarely as the primary
framework.

**When to use it:** For specific commitments in a 1:1 or a
project kickoff. Bad for org-level strategy because it's too
operational.

### The synthesis

Most senior EMs use **OKRs at the org/team level and SMART or
MBO-flavored goals at the IC level**. The OKR tells the team
*what direction*; the SMART/MBO goal tells each person *what
they're accountable for* in the next 6-12 weeks.

The mistake new EMs make: copying the org OKR and assigning it
to each person. "Make our data pipeline the most reliable" is
not a goal for a junior engineer. "Own the validation layer of
the new pipeline, with 0 P0 bugs by end of Q2" is.

---

## 2. What to do when goals change

Goals change. The market shifts, the company reorgs, the
priority pivots, the data tells you your hypothesis was wrong.
The senior move isn't to defend the old goals — it's to
re-navigate when reality changes.

The pattern:

1. **Acknowledge the change explicitly.** Don't pretend the
   goal still stands. Engineers can smell the gap between the
   doc and reality.
2. **Name what changed and why.** A 5-minute context dump ("we
   had a customer churn, the new top priority is X") goes
   further than a paragraph.
3. **Propose the new goal, with reasoning.** Don't make the
   engineer infer the new direction. State it.
4. **Ask for input.** "What do you think? What am I missing?"
   The engineer may see a path you didn't.
5. **Commit to the new goal in writing.** Update the doc. Date
   it. The audit trail matters.

A useful script for a goal-change conversation:

> *"Heads up — the goal we set at the start of the quarter is
> changing. The reason: [1-2 sentences on the new context]. The
> new direction is: [1-2 sentences on the new goal]. What I
> need from you: [specific, time-bound]. What I want your input
> on: [the part of the new direction where the engineer's
> judgment matters]. I'll update the doc by EOW and we'll
> re-baseline in next week's 1:1."*

The worst version: "things have changed, just keep doing good
work." The engineer will fill the void with anxiety.

---

## 3. How to set expectations that survive reality

The single most common reason engineers underperform isn't lack
of skill — it's unclear expectations. The senior move is to
make the expectations explicit at three levels:

| Level | What the engineer should know | How to communicate it |
|---|---|---|
| **Direction** | "We're trying to do X because Y." | OKR doc, all-hands, 1:1 context. |
| **Accountability** | "You're owning Z. Here's what 'done' looks like." | Per-person goal doc, 1:1 agreement. |
| **Operating norms** | "We ship on time, we don't skip reviews, we do on-call when it's our turn." | Team doc, 1:1 reinforcement. |

The mistake new EMs make: communicating direction clearly and
accountability vaguely. The engineer knows the team is trying
to migrate to streaming, but doesn't know whether they're
accountable for the schema, the producer, the consumer, or the
on-call runbook. The senior move is to be specific about who
owns what.

A useful exercise: at the start of every project, write a
1-page "RACI" (Responsible / Accountable / Consulted /
Informed) for the project, and share it with the team. A RACI
sounds corporate, but the underlying move is what matters: name
who owns each piece, and make sure the owner agrees.

---

## 4. The "stretch" goal conversation

Stretch goals are goals that are deliberately above the
engineer's current level. The point isn't to set them up to
fail — it's to give them a target that requires growth.

The senior move is to **frame stretch goals as a learning
opportunity, not a pass/fail test**:

> *"This goal is a stretch. I don't fully expect you to hit
> all of it by end of quarter. What I want is for you to be
> 70% of the way there, with a clear story about what you
> learned in the other 30%. If you hit all of it, we'll have
> a strong promo packet. If you hit 70% with a great learning
> story, we'll have a great 6-month goal for the next cycle
> that gets you there. Either outcome is a win."*

The worst version: "I expect you to hit this, and if you
don't, it goes in your perf review." That's a coercion move
that burns trust.

---

## 5. A worked example: the goals doc

For Priya, the E5→E6 candidate from Lesson 04. Sam is setting
her goals for the next 6 months.

> **GOALS — Priya — H2 2026**
>
> **Org context:** We're migrating the data platform to the
> streaming pipeline. Top customer churn risk if the migration
> slips past Q4.
>
> **Your goals (in priority order):**
>
> 1. **Own the validation layer of the streaming pipeline.**
>   *Definition of done:* 0 P0 bugs in production for 30 days
>   post-launch, full test coverage on the deserialization
>   edge cases, and a runbook for the on-call rotation.
>   *Why this is your goal:* It's the highest-leverage
>   technical work on the project, and the E6 promo packet
>   needs to show you owning a multi-engineer area.
>
> 2. **Co-author the 2026 data platform roadmap with me.**
>   *Definition of done:* 1-page roadmap doc, signed off by
>   you, me, and the director, by end of Q3. *Why this is
>   your goal:* The growth area from your promo packet was
>   "long-term strategy." This is the artifact that proves
>   you've closed it.
>
> 3. **Mentor Aarav into the on-call lead role.** *Definition
>   of done:* Aarav leads 2 incident responses end-to-end by
>   end of Q3, with you shadowing but not running. *Why this
>   is your goal:* Multiplies your impact. Also a growth area
>   from your promo packet (cross-functional influence).
>
> **What I expect from you:**
> - Weekly status update in our 1:1, even if it's "still on
>   track, no blockers."
> - Flag risks early — if goal 1 is slipping, I want to know
>   3 weeks before the deadline, not 3 days.
> - Push back on these goals if they don't feel right.
>
> **What you can expect from me:**
> - 1:1s weekly, GROW format (see Lesson 03).
> - Office hours every Thursday for design-doc reviews.
> - Help unblocking cross-team dependencies.
> - Honest feedback on the roadmap doc, not just at the end.

**What makes this land:** Each goal has a definition of done
that's measurable. Each goal is anchored to a rubric row from
the promo packet. The "what I expect from you / what you can
expect from me" section makes the operating norms explicit.
The order is prioritized — Priya knows that goal 1 is the
most important and the rest are secondary if there's a tradeoff.

---

## 6. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- Behavioral #22: *"Tell me about a time when you had to set
  goals for your team."*
- Behavioral #46: *"Tell me about a time when you had to
  re-prioritize."*
- Behavioral #81: *"Tell me about a time when you had to manage
  changing priorities."*
- Behavioral #119: *"Tell me about a time when you had to
  motivate a team."*

---

## Try it

Pick one of your directs (or one of your projects, if you're
an IC). Write a 1-page goals doc in the format above. Notice
which goals are easy to write specific definitions of done for
and which are vague. The vague ones are your coaching
priorities.

If the doc feels too operational, ask: what's the *direction*
the engineer is missing? That's where the OKR-style framing
helps.

---

## Action item

Schedule a goals conversation with one of your directs this
week. Use the format above. After the conversation, ask
yourself: did the engineer leave with a clear definition of
done for each goal, or did they leave with a vague sense of
direction? If the latter, the doc needs another pass.