# 07 — The Performance Review Process

> **Lesson 7 of 21 — Performance Management** · ~20 min

The 4 boxes (exceeds, meets, partially meets, doesn't meet), how
to write a perf review, and how to deliver it. The 4-boxes
framework is the substrate for everything in this module.

---

## 1. The 4 boxes

Most engineering orgs use some version of a 4-box performance
distribution. The exact names vary, but the shape is the same:

| Box | What it means | What % of the org it should cover |
|---|---|---|
| **Exceeds** (sometimes "Exceeds Expectations" or "Strong Exceeds") | Doing work meaningfully above the current level. Ready for promo. | 10-15% |
| **Meets** (sometimes "Successful") | Doing work solidly at the current level. Reliable, growing at a healthy pace. | 65-75% |
| **Partially Meets** | Doing some of the work at the current level, but with material gaps. On a trajectory to meet, or to not meet. | 10-15% |
| **Doesn't Meet** | Doing work materially below the current level. Active performance plan or PIP. | <5% |

The percentages above are a rough guide. The hard constraint is
**the ratio of "Exceeds" to "Doesn't Meet"** — most calibration
committees enforce roughly 3-5:1, sometimes 10:1, in either
direction. The thinking: if more than 5% of the org is failing
their current level, either the hiring is broken or the
management is broken. If less than 5% is "Exceeds," the bar is
too low.

The mistake new EMs make: putting everyone in "Meets." This is
the path of least resistance — nobody's feelings get hurt — but
it destroys the signal in the system. If "Meets" means
"anybody who didn't actively screw up," then "Exceeds" means
nothing and "Partially Meets" is a surprise. Calibration
committees will force-distribute the EMs who do this, and the
EM ends up in a hard conversation with a direct who thought
they were doing fine.

The senior move: **be honest in the 1:1s all year, so the perf
review is never a surprise.** A direct who lands in "Partially
Meets" should have heard it 3 months earlier in a 1:1, with a
specific plan to climb out.

---

## 2. How to write a perf review

A perf review is a 1-2 page document that goes to the
calibration committee (Lesson 10) and (with appropriate edits)
to the engineer themselves. The structure:

```
PERF REVIEW — [Name] — [Level] — [Cycle]

OVERALL RATING: [Exceeds / Meets / Partially Meets / Doesn't Meet]

ONE-SENTENCE SUMMARY:
[One sentence on the engineer's impact this cycle. Don't bury
the lede — the committee reads 50 of these.]

STRENGTHS (2-3, with evidence):
- [Strength 1] — [Specific project, decision, number]
- [Strength 2] — [Specific project, decision, number]
- [Strength 3] — [Specific project, decision, number]

GROWTH AREAS (1-3, with specifics):
- [Growth area 1] — [What "better" looks like, with an
  example of what the engineer did this cycle that was short
  of "better"]
- [Growth area 2] — [Same structure]

CAREER TRAJECTORY:
[Where is this engineer going? What's the next-level work
they're already doing? What's the gap to the next level?]

PEER COMPARISON:
[Honest comparison to peers at the same level. "Solidly at
the median of the E5 cohort" / "in the top quartile of E5s
I've worked with" / "in the bottom quartile."]

PROPOSED NEXT STEPS:
[Promo? Goal-setting for next cycle? Performance plan? Stay
the course?]
```

The "peer comparison" section is the part most EMs skip. It's
also the part the calibration committee cares about most.
Without it, the committee can't tell if "Meets" means "median
E5" or "top of the cohort" or "bottom of the cohort."

The "growth areas" section is the second part most EMs skip.
The instinct is to be positive. The calibration committee
discounts reviews without growth areas because the
distribution of growth areas across the org is a signal of
where the org's weaknesses are.

---

## 3. How to deliver a perf review

The perf review is delivered in a 1:1. The 1:1 is 30-45
minutes, scheduled in advance, with no other agenda. The
engineer is allowed to take notes. The conversation has 4
parts:

1. **Set the frame (3-5 min).** "I want to walk you through
   your perf review for the cycle. I'll share the doc, walk
   you through the rating and the reasoning, then I want to
   hear your reaction."

2. **Walk through the doc (10-15 min).** Read it together. Be
   specific about the strengths (cite the project) and the
   growth areas (cite the example). The engineer should not
   be hearing any of this for the first time — but they will
   be hearing it in this form, and that's OK.

3. **Hear the reaction (10-15 min).** The engineer may push
   back. They may be surprised, disappointed, angry. The
   senior move is to **listen without defending**. Don't
   argue with the rating in the room. If the engineer has
   new evidence ("I did X, you didn't mention it"), thank
   them and say you'll factor it in. If the engineer
   disagrees with the rating ("I think I should be
   'Exceeds'"), listen to the reasoning, acknowledge it,
   and either adjust or explain why you don't.

4. **Land on next steps (5-10 min).** "Here's what I propose
   for the next cycle: [specific goals, specific support,
   specific check-ins]." The senior move is to leave the 1:1
   with a plan, not just a rating.

The mistakes to avoid:

- **Delivering the rating cold.** "I just got out of
  calibration, you got 'Partially Meets.'" Always deliver
  in a 1:1, with the doc, with preparation.
- **Apologizing for the rating.** "I'm sorry, but the
  committee decided..." The engineer doesn't care whose
  decision it was. They care about your judgment and your
  ownership. Own it.
- **Sugarcoating the growth areas.** "You could maybe think
  about..." No. The growth areas are the engineer's roadmap
  for the next cycle. Be specific.

---

## 4. A worked example: the "Partially Meets" review for Jordan

Jordan, an E4 on Sam's team, has had a rough cycle. The work
is technically competent, but the projects have slipped
timelines, the cross-functional collaboration has been rocky,
and 2 peers have privately mentioned that Jordan is hard to
work with.

> **PERF REVIEW — Jordan — E4 — H2 2025**
>
> **OVERALL RATING: Partially Meets**
>
> **ONE-SENTENCE SUMMARY:** Jordan is a strong individual
> contributor whose collaboration patterns are creating
> friction on the team and missing project timelines.
>
> **STRENGTHS:**
> - Owned the legacy decommission project end-to-end, including
>   a non-trivial refactor of the on-call tooling that 3 other
>   teams have since adopted.
> - Code quality on his own work is consistently high — review
>   comments from peers and skips specifically call out his
>   test coverage and edge-case handling.
> - Mentored a new hire (Aisha) through her first 8 weeks;
>   she's now shipping independently.
>
> **GROWTH AREAS:**
> - **Cross-functional collaboration.** Two specific
>   incidents this cycle: (1) the schema design review with
>   the data science team where Jordan pushed back on the
>   proposal for 45 minutes in a way that 2 attendees
>   described to me as "dismissive"; (2) the on-call
>   handoff to the consumer team where the
>   documentation was missing context that caused a 4-hour
>   debug during an incident.
> - **Project estimation.** Two projects slipped timeline
>   by 30-40% (the legacy decommission went from 6 to 9
>   weeks, the consumer migration went from 4 to 6
>   weeks). In both cases, the slip was due to
>   under-counted cross-team dependencies, not technical
>   complexity.
>
> **CAREER TRAJECTORY:** Jordan has the technical bar for E5,
> but the collaboration patterns are a blocker for the next
> level and for the current level's effectiveness on the
> team. With focused work on cross-functional
> communication and project estimation, E5 is realistic
> for the H1 2026 cycle.
>
> **PEER COMPARISON:** Below the median of the E4 cohort on
> cross-functional collaboration; above the median on
> technical execution.
>
> **PROPOSED NEXT STEPS:** 90-day growth plan focused on (1)
> weekly check-ins on cross-functional comms, (2) joint
> estimation on the next 2 projects, (3) a goal to ship
> one project on time. If the patterns don't shift, we'll
> have a hard conversation in Q1.

**What makes this land:** The growth areas cite specific
incidents, not vague feedback. The peer comparison is honest.
The proposed next steps are specific, time-bound, and tied
to a consequence. The "career trajectory" is realistic without
being falsely reassuring.

---

## 5. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- People Management #7: *"Tell me about a time when you had to
  give someone difficult feedback."*
- People Management #10: *"Tell me about a time when you had
  to deliver hard feedback to a direct report."*
- Behavioral #18: *"Tell me about a time when you had to have
  a difficult conversation with a colleague."*
- Behavioral #52: *"Tell me about a time when you had to
  evaluate someone's performance."*

---

## Try it

Write a perf review for one of your directs, even if you're
not in a cycle. Use the format above. Notice which sections
feel easy (probably strengths) and which feel hard
(probably peer comparison). The hard sections are where you
need to do more 1:1 work next cycle.

If you're an IC interviewing for an EM role, the equivalent
exercise: write a perf review for yourself at the next
level. Same template. Notice which sections have the most
evidence and which are thinnest.

---

## Action item

Block 1 hour this week to draft 1 perf review in the format
above. Even if you're not in a cycle, the practice of writing
the doc surfaces the gaps in your 1:1 work for the year. The
gaps are the 1:1 priorities for next cycle.