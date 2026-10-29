# 21 — Working Across Time Zones and Cultures

> **Lesson 21 of 21 — Cross-functional Collaboration** · ~20 min

Overlap hours, async-first, written-decision style, and the
cultural fluency needed for distributed teams. Cross-timezone
work is increasingly the norm — and the patterns are
different from co-located work. Most EMs have been
*in* distributed teams, but few have managed one.

---

## 1. The 3 principles of cross-timezone work

The patterns that work for co-located teams break under
timezone distance. The 3 principles that survive:

1. **Async-first, sync-second.** The default is to
   communicate in writing. The synchronous meeting is the
   exception, not the default. The senior move is to
   **write things down by default**, and only escalate
   to a meeting when the written communication can't
   resolve it.

2. **Over-document decisions.** The co-located team can
   rely on the hallway conversation; the distributed
   team can't. The senior move is to **write down every
   decision** — in a doc, in Slack, in a meeting note —
   so the people in other timezones have the same
   context as the people in the meeting.

3. **Respect the overlap hours.** The overlap is sacred.
   The senior move is to **use the overlap for the
   decisions that need synchronous conversation** (design
   reviews, conflict resolution, hiring loops) and
   **protect the non-overlap for deep work**. The team
   that turns the overlap into a "let's all be online
   together" session burns out.

---

## 2. The async-first default

The async-first default means: before you send a Slack
message asking for a meeting, ask yourself: can this be
resolved in writing? Before you ask a question in a
meeting, ask yourself: could this be answered in a doc
that people read on their own time?

The async-first default doesn't mean no meetings. It
means the meetings that happen are higher-leverage —
they're for the conversations that can't be async (design
reviews, conflict resolution, 1:1s, hiring loops).

The mistake: assuming "async-first" means "no meetings."
The senior move is to **have fewer, more important
meetings**, with the people who need to be in the room
(and the timezones who need to be represented).

---

## 3. The written-decision style

The written-decision style is the practice of **putting
decisions in writing**, with the rationale, the
alternatives considered, and the next steps. The
distributed team runs on written decisions because the
people in other timezones need the context the meeting
provided.

The structure for a written decision:

```
DECISION — [Topic] — [Date]

THE DECISION:
[One sentence: what was decided.]

THE RATIONALE:
[2-3 sentences: why this decision was made.]

THE ALTERNATIVES CONSIDERED:
- [Alternative 1: what it was, why it wasn't chosen]
- [Alternative 2: what it was, why it wasn't chosen]

THE NEXT STEPS:
- [Step 1: who, by when]
- [Step 2: who, by when]

THE DISSENT (if any):
[Any objections raised, and how they were addressed.]
```

The senior move is the **"dissent" section**. The team
that pretends everyone agreed is the team that has
quiet resentment. The team that records the dissent
(and the response to the dissent) is the team that
trusts the decision.

The mistake: using the written-decision style for
everything, including the small things. The senior
move is to **use the written-decision style for
decisions that affect multiple people or have
durable consequences**. The small things can stay in
Slack.

---

## 4. Cultural fluency

Distributed teams are also cross-cultural teams. The
senior move is to **build cultural fluency** —
awareness of the cultural norms and communication
styles of the people on the team.

The 3 dimensions that matter most:

1. **Directness.** Some cultures are direct
   (low-context, say what you mean); some are
   indirect (high-context, read between the lines).
   The senior move is to **be explicit about which
   style you use** in writing, so the indirect
   communicator doesn't feel attacked and the direct
   communicator doesn't feel hedged.
2. **Hierarchy.** Some cultures defer to hierarchy
   ("let me check with my manager"); some are flat
   ("I'll decide this myself"). The senior move is
   to **name the decision-maker explicitly** in
   every decision doc, so the high-hierarchy cultures
   know whose authority is in play.
3. **Time orientation.** Some cultures are
   time-linear (deadlines are hard); some are
   time-flexible (deadlines are aspirational). The
   senior move is to **name the deadline and the
   consequence of missing it** in every commitment.

---

## 5. The overlap hours design

The overlap is the most-valuable time on a distributed
team. The senior move is to **design the overlap
deliberately**, with specific activities for specific
days.

A common pattern:

| Day | Overlap activity | What it's for |
|---|---|---|
| Monday | Staff meeting (60 min) | Weekly alignment, decisions, blockers |
| Tuesday | Design reviews (60 min) | Technical decisions that need synchronous conversation |
| Wednesday | 1:1s (30 min each) | Coaching, career, project sync |
| Thursday | Cross-team syncs (60 min) | PM/Design peer relationships, escalation |
| Friday | Demo or showcase (30 min) | Show progress, build shared context |

The mistake: using the overlap for everything. The
team that has 4 hours of meetings during the overlap
is the team that has no overlap for deep work. The
senior move is to **protect the non-overlap hours**
for the engineers' best work, with the understanding
that the engineers in the early timezones get the
first part of the day for deep work, and the engineers
in the late timezones get the last part.

---

## 6. The "written handoff" pattern

The handoff is the moment when the work transitions
from one timezone to the next. The senior move is to
**write down the handoff state explicitly** — what's
in progress, what's blocked, what's expected next.

The structure:

```
HANDOFF — [Date] — [From timezone] → [To timezone]

IN PROGRESS:
- [Engineer 1] — [What's in progress, expected to land
  by [time]]
- [Engineer 2] — [What's in progress, expected to land
  by [time]]

BLOCKED:
- [Engineer 3] — [What's blocked, who can unblock,
  when]

PICKED UP NEXT (in the next timezone):
- [Engineer 4] — [What they'll pick up, expected
  timeline]

OVERLAP QUESTIONS (to discuss in the overlap):
- [Question 1 — needs the overlap to resolve]
- [Question 2]
```

The mistake: assuming the next timezone knows what to
pick up. The senior move is to **write down the state
so the next timezone has the same context as the
current one**. The team that runs on handoffs is the
team that ships across timezones.

---

## 7. A worked example: the 24-hour incident handoff

A Sev1 hits at 3pm US Eastern (12pm US Pacific, 8pm
GMT, 4am IST). The US team is in the late afternoon;
the European team is in the late afternoon; the Indian
team is in the middle of the night.

> **3:00pm ET (incident starts):** US team opens the
> incident channel, assigns US-based IC, pings the
> European team for awareness.
>
> **3:00pm-7:00pm ET:** US team leads the investigation.
> 30-minute updates in the channel.
>
> **7:00pm ET (handoff):** US team posts the handoff:
> "Root cause narrowed to the schema-version
> mismatch; fix is a 1-line config change; waiting on
> the deploy approval. Estimated time to fix: 30
> minutes once approval lands."
>
> **7:00pm-11:00pm ET (US off, EU on):** European team
> monitors the channel, pings the deploy owner for
> approval. Approval lands at 10pm ET (4am GMT, 9:30am
> IST).
>
> **11:00pm ET (handoff to IST):** European team
> posts: "Deploy approved; Indian team, can you
> deploy when you start your day at 9:30am IST
> (12:00am ET)? The fix is straightforward."
>
> **9:30am IST (12:00am ET, fix deploys):** Indian team
> deploys, confirms the fix, posts the resolution.
>
> **8:00am ET (next morning):** US team posts the
> postmortem and the action items.

**What makes this land:** Each timezone has a clear
role. The handoffs are explicit. The incident
progresses without anyone being asked to be online
outside their working hours. The 24-hour elapsed time
is acceptable for a Sev1 with no customer impact;
the 24 hours of human effort is distributed across
3 timezones, with no one carrying more than their
share.

---

## 8. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- Behavioral #34: *"Tell me about a time when you had to
  work with a team that had different priorities."*
- Behavioral #78: *"Tell me about a time when you had
  to coordinate multiple teams."*
- Behavioral #84: *"Tell me about a time when you had
  to build a relationship with a stakeholder."*
- Behavioral #122: *"Tell me about a time when you
  had to resolve a conflict between teams."*

---

## Try it

Identify one project in the next 30 days that will
involve a handoff between timezones. Write the handoff
in the format above. Notice how the format forces you
to be explicit about what's in progress, what's
blocked, and what's expected next. The discipline
of the handoff is the senior move that makes
distributed work feel like co-located work.

---

## Action item

This week, design (or redesign) your team's overlap.
What are the 3-5 synchronous activities that need
the overlap? What are the activities that should be
async? The senior move is to **protect the overlap
for the high-leverage activities** and move the rest
to async. The team that uses the overlap for the
right things is the team that doesn't burn out.