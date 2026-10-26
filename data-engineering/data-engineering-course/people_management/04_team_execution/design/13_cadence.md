# 13 — Meeting Cadence and Operational Rhythms

> **Lesson 13 of 21 — Managing Team Execution** · ~20 min

Staff meetings, all-hands, weekly notes, and the operating
rhythm that keeps a team aligned. The cadence is the public
substrate for the private 1:1s in Lesson 12 — it's how the
team stays aligned on direction, surface blockers, and
maintain shared context.

---

## 1. The 5-meeting weekly cadence

Most teams have a 5-meeting weekly cadence. The senior move
is to design the cadence deliberately, with each meeting
having a specific purpose, audience, and outcome.

| Meeting | Frequency | Length | Audience | Purpose |
|---|---|---|---|---|
| **Staff meeting** | Weekly | 30-60 min | All team engineers + EM | Status, blockers, decisions |
| **Project standup** | 2-3x per week | 15 min | Project team only | Tactical sync on the project |
| **Skip-level** | Monthly (per direct) | 30-45 min | EM + skip | Career, context, retention |
| **EM 1:1** | Biweekly | 30-45 min | EM + skip-level | Direction, escalations, career |
| **All-hands** | Monthly or quarterly | 60 min | Whole org or sub-org | Strategy, context, big announcements |

The mistake new EMs make: running all 5 meetings without
designing the cadence. The staff meeting becomes a status
update, the project standup becomes a rehash of Slack, the
all-hands becomes a one-way broadcast. The senior move is
to design each meeting to produce a specific outcome.

---

## 2. The staff meeting (the load-bearing one)

The staff meeting is the team's most important public
meeting. It's where direction is communicated, blockers are
surfaced, and decisions are made. The structure I
recommend:

```
STAFF MEETING — [Date] — [Attendees]

AGENDA (5 sections, 45 min total):

1. UPDATES (10 min)
   - Each engineer: 60 seconds on what they shipped this
     week, what's next week, what they're blocked on
   - Round-robin, no deep dives

2. PROJECT SPOTLIGHT (10 min)
   - One engineer presents a project in 5-10 min
   - The team gives feedback
   - Rotates weekly so everyone presents quarterly

3. DECISIONS (10 min)
   - 1-3 decisions that need to be made this week
   - Owner presents, team discusses, decision is made
   - The decision + the rationale are written into the
     meeting doc

4. BLOCKERS (5 min)
   - Anything anyone is stuck on
   - The EM (or someone) commits to unblock by [date]

5. GROWTH/LEARNING (5 min)
   - A short share from one engineer — something they
     learned, a paper they read, a conference talk they
     liked
   - Builds the learning culture
```

The "decisions" section is the load-bearing part. Most staff
meetings don't make decisions — they surface problems that
get re-surfaced in Slack for a week. The senior move is to
**make the decision in the meeting, or explicitly defer to a
named person by a named date**.

The "project spotlight" section is the senior move for
building a culture of feedback. One engineer presents, the
team gives feedback, the rotation builds shared context.

The "growth/learning" section is the senior move for
building a learning culture. The engineer who shares a
paper this week is the engineer who grows the team 6 months
from now.

---

## 3. The weekly note

The weekly note is a 1-page doc the EM writes every Friday
(or Monday morning) that summarizes the week's status to the
skip-level and the broader org. The structure:

```
WEEKLY NOTE — [Team] — [Date range]

HEADLINE:
[One sentence on the most important thing that happened
this week. If the skip reads only this sentence, they
should know what they need to know.]

PROGRESS (3-5 bullets):
- [Bullet 1: specific shipped work, with the engineer
  credited]
- [Bullet 2]
- [Bullet 3]

BLOCKERS (1-3 bullets):
- [Blocker 1: what, who, what we need to unblock]
- [Blocker 2]

DECISIONS MADE (1-3 bullets):
- [Decision 1: what was decided, by whom, with rationale]
- [Decision 2]

HEADCOUNT / HIRING (1-2 bullets):
- [Where we are on open roles, who's interviewing,
  expected closes]

NEXT WEEK (3-5 bullets):
- [The most important things for next week]
```

The mistake new EMs make: writing the weekly note as a
diary ("this week we had a standup and then Priya worked
on..."). The note is for the skip-level, who needs signal,
not narrative.

The senior move: **write the note so the skip-level can
forward it to their skip-level with no edits**. The
headline sentence is the one that gets forwarded.

---

## 4. The all-hands

The all-hands is the org-level meeting, typically monthly or
quarterly. The senior move is to use the all-hands for
**strategic context, not status**. The status belongs in
the weekly note.

A useful all-hands structure (60 min):

1. **Strategy update (15 min).** Director or senior leader
   shares the org's direction, the biggest bets, the
   biggest risks.
2. **Q&A (15 min).** Pre-submitted questions, plus live
   questions. The senior move is to have a real Q&A, not
   a soft-ball one.
3. **Project showcase (15 min).** 2-3 teams share what
   they shipped, what they learned, what's next.
4. **People announcements (10 min).** New hires, promos,
   transfers. The senior move is to make the people
   announcements specific and personal, not just a list
   of names.
5. **Open mic (5 min).** Anyone can raise anything. The
   senior move is to protect this slot — it's where
   real signal lives.

The all-hands is also where the senior EM sets the tone
for the org. If the all-hands is honest about failures
("we missed this quarter's reliability goal, here's
why, here's what we're doing"), the team trusts the
direction. If the all-hands is a victory lap, the team
stops trusting the direction.

---

## 5. A worked example: the weekly note for the data platform
team

> **WEEKLY NOTE — Data Platform Team — Aug 4-8, 2026**
>
> **HEADLINE:** Streaming migration v1 hit its first shadow-
> mode milestone on schedule; the on-call rotation redesign
> is now scoped and will be presented at next week's staff
> meeting.
>
> **PROGRESS:**
> - Priya shipped the streaming migration v1 shadow mode
>   on Thursday; 100% traffic mirrored, 0 P0s, 2 P3s
>   identified and fixed within 24h.
> - Aarav finalized the on-call rotation proposal; will
>   present at next staff meeting.
> - Jordan's customer data quality dashboard hit 80%
>   coverage of the top 5 customers; the remaining 20% is
>   blocked on a data source from the finance team.
>
> **BLOCKERS:**
> - The new Kafka cluster from infra is 4 days late; if
>   it slips past Aug 15, the migration's full cutover
>   slips by 2 weeks. I'm escalating to the infra EM
>   today.
> - Jordan is blocked on a data source from the finance
>   team; finance EM has been slow to respond. I'm
>   setting up a 30-min sync this week.
>
> **DECISIONS MADE:**
> - We decided to use shadow mode for 2 weeks instead of
>   1, based on the early shadow data. This pushes the
>   full cutover to Sep 15 (was Sep 1).
>
> **HEADCOUNT / HIRING:**
> - 1 offer out for a senior data engineer; expect
>   close this week.
> - 1 on-site loop scheduled for next week for the
>   platform engineer role.
>
> **NEXT WEEK:**
> - Aarav presents the on-call rotation proposal.
> - Priya kicks off the v1 cutover plan.
> - Jordan unblocks the finance data source.

**What makes this land:** The headline is the one thing the
skip needs to know. The progress is specific, with names
and numbers. The blockers are actionable, with escalation
paths. The decisions are explicit. The next-week section
is the senior move — it tells the skip what to expect, so
they can flag any concerns before Monday.

---

## 6. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- Behavioral #22: *"Tell me about a time when you had to
  set goals for your team."*
- Behavioral #81: *"Tell me about a time when you had to
  manage changing priorities."*
- Behavioral #100: *"Tell me about a time you delivered a
  complex project."*
- Behavioral #119: *"Tell me about a time when you had to
  motivate a team."*

---

## Try it

If you're not already writing a weekly note, start this
week. Use the format above. Notice how the discipline of
writing the headline forces you to know the most important
thing, and how the "decisions made" section forces you to
actually make decisions.

If you're an IC interviewing for an EM role, write a
weekly note for your current project. The skill is the
same; the scope is smaller.

---

## Action item

This week, design (or redesign) your team's staff meeting
using the 5-section structure above. The "decisions" and
"growth/learning" sections are the ones most teams skip —
start there.