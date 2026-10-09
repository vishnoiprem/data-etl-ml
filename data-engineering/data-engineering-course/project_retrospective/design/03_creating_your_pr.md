# 03 — Creating Your Project Retrospective

> **Lesson 3 of 6** · ~20 min

The 5-part structure for a Project Retrospective:
**Context, Approach, Outcome, Lessons, What I'd Do
Differently.** With a sample breakdown showing how
to allocate the 5 minutes across the 5 beats, and
worked examples of each beat written out.

---

## 1. The structure: CAR + Lessons + What I'd Do Differently

A Project Retrospective is not a STAR story. It's
not a CAR story. It's a 5-part structure that
extends CAR with two extra beats — **Lessons** and
**What I'd Do Differently** — that are specific to
the PR format.

The 5 beats:

1. **Context** (30-45 seconds) — the situation
   before you started. The constraints. The
   stakeholders. The numbers.
2. **Approach** (60-90 seconds) — what you did, and
   *why*. The judgment call. The decision.
3. **Outcome** (60-90 seconds) — what happened. The
   number. The scope. The unexpected.
4. **Lessons** (45-60 seconds) — what you took away
   from the project. The transferable insight.
5. **What I'd Do Differently** (30-45 seconds) —
   the honest beat. The 2-3 specific changes you'd
   make if you were doing it again.

Total: **5 minutes.** That's the target. If you're
under 4 minutes, you're too short; if you're over 6
minutes, you've lost the room.

The structure is a *guide*, not a *script*. Most
retrospectives will follow this shape, but the
specific allocation will vary by project. A project
with a complicated judgment call (a re-platform)
might spend 2 minutes on Approach. A project with a
dramatic failure (an incident) might spend 90 seconds
on Outcome. The structure is the skeleton; the
content is the muscle.

---

## 2. Beat 1: Context (30-45 seconds)

The Context beat answers three questions:

- **What was the situation?** (the system, the
  team, the product)
- **What was the constraint?** (cost, time, scope,
  people)
- **What was the number?** (the metric that made
  the project necessary)

A weak Context beat says: "We had an old pipeline
that needed to be modernized."

A strong Context beat says: "We had a 4-year-old
nightly ETL pipeline running on a custom Airflow-on-
EC2 setup. The runtime had crept to 8 hours, the
cost was $180k/year, and the data was 24 hours
stale by the time the morning dashboards ran. The
data science team had started working around the
staleness with manual snapshots — which was
expensive, error-prone, and unsustainable."

The strong version has 3 numbers (8 hours, $180k,
24 hours) and a stakeholder (the data science
team). The interviewer now knows exactly what you
were solving for, and they have a baseline for the
Outcome beat.

**Rule of thumb:** if your Context doesn't have a
number, rewrite it until it does. The number is
what makes the project concrete.

---

## 3. Beat 2: Approach (60-90 seconds)

The Approach beat is the heart of the PR. It
answers three questions:

- **What did you do?** (the high-level approach)
- **Why did you pick this approach over the
  alternatives?** (the judgment call)
- **Who was involved?** (the team, the
  stakeholders, the resistors)

A weak Approach beat says: "We decided to migrate
to dbt and Snowflake. We built it out over 4
months."

A strong Approach beat says: "I spent 2 weeks just
listening to the data science team. What did they
need? What would break under a naive migration?
What was non-negotiable? I came back with a
backward-compatible schema that preserved their
existing model interfaces and added the new fields
with sensible defaults. I also offered to be the
point-of-contact for any breakage for the first 3
months — which put the social cost on me, not on
them. All 3 signed off within 2 weeks. Two migrated
immediately, the third delayed 2 months (which
we'd budgeted for). The migration took 4 months
from kickoff to cutover."

The strong version has 4 specific moves (listening,
backward-compat schema, point-of-contact commitment,
2-week signoff). It names the judgment call (we
chose backward-compat over big-bang, with this
specific reason). It names a stakeholder (the data
science team, specifically the 3 data scientists
whose models were most affected).

**Rule of thumb:** the Approach beat should have
*more specificity* than the Context beat. This is
where you demonstrate judgment.

---

## 4. Beat 3: Outcome (60-90 seconds)

The Outcome beat answers three questions:

- **What happened?** (the result)
- **What was the number?** (the improvement)
- **What was the unexpected?** (the thing that
  went differently than planned — good or bad)

A weak Outcome beat says: "We shipped on time. The
data is now fresh. The cost is lower."

A strong Outcome beat says: "We shipped on schedule.
Runtime went from 8 hours to 45 minutes — a 10x
improvement. Cost dropped from $180k/year to
$72k/year, a 60% reduction. Data freshness went
from 24 hours to sub-minute. Zero downstream
breakage across the 12 data-science models.

The unexpected part: the cost reduction was
*larger* than we'd projected, because the dbt
materializations were much more efficient than
our hand-rolled SQL. But the migration took 2
weeks longer than we'd estimated, because we
discovered that 3 of our 12 source systems had
un-documented schema drift that we had to
reconcile. We caught it during shadow mode —
which is why the 3-week shadow period I'd pushed
for in the Approach beat mattered."

The strong version has 4 numbers (8hr→45min, $180k
→$72k, 24h→sub-minute, 0 breakage), one unexpected
positive (cost reduction was larger), and one
unexpected negative (schema drift in 3 source
systems). The honest negative is what makes the
Outcome beat credible.

**Rule of thumb:** the Outcome beat should have
*at least 2 numbers* — one for the metric you
were trying to improve, and one for the metric
that surprised you. The surprise is the move.

---

## 5. Beat 4: Lessons (45-60 seconds)

The Lessons beat answers three questions:

- **What did you take away?** (the insight)
- **Is it transferable?** (would it apply to a
  different project?)
- **What did it change about how you work?** (the
  behavior change)

A weak Lessons beat says: "I learned that
migrations are hard."

A strong Lessons beat says: "Three lessons. First,
'listening first' sounds obvious but almost nobody
does it — most engineers walk into a stakeholder
meeting with a solution. The 2 weeks I spent
listening to the data science team saved us months
of downstream breakage. Second, 'I'll be the
point-of-contact' is a stronger commitment than
'just ping me' — it puts the social cost on me,
not on them, which is what unlocked the signoff.
Third, the 3-week shadow period caught 2 of the 3
risks I'd flagged in the design doc. Shadow mode
is now a default for me on any non-trivial
cutover."

The strong version has 3 specific lessons, each
with a behavior change. None of them is generic
("migrations are hard"). All of them are
transferable (they'd apply to a different project
or a different domain).

**Rule of thumb:** every lesson should have a
*behavior change* attached. "I learned X" is
weak. "I now default to X" is strong. The
behavior change is what makes the lesson stick.

---

## 6. Beat 5: What I'd Do Differently (30-45 seconds)

This is the beat most candidates skip. **Don't
skip it.** A retrospective without a "what I'd do
differently" is a press release, not a retrospective.

The "What I'd Do Differently" beat answers three
questions:

- **What would you change?** (2-3 specific things)
- **Why?** (what was the cost of not doing them
  the first time?)
- **What did they teach you?** (the senior
  self-awareness beat)

A weak "What I'd Do Differently" beat says: "I'd
do it faster."

A strong "What I'd Do Differently" beat says:
"Two things. First, I'd write the backward-compat
design doc as a shared doc, not a 1-pager, because
the data-science team kept asking the same
questions for 3 weeks — and a 1-pager forces
follow-up. Second, I'd set up a shared Slack
channel for the migration from day 1, not week 6 —
because the first 5 weeks of stakeholder
coordination happened over email, and we lost
context twice. Both of these would have saved us
2-3 weeks of miscommunication."

The strong version has 2 specific changes, each
with a cost estimate (2-3 weeks of miscommunication).
It also implicitly admits that the original approach
was suboptimal, which is the self-awareness signal
the interviewer is testing for.

**Rule of thumb:** the "What I'd Do Differently"
beat should have *2-3 specific changes*, not a
generic "I would communicate better." Generic is
forgettable; specific is credible.

---

## 7. Putting it all together: a sample structure breakdown

Here's how the 5 minutes allocate across the 5
beats for a typical re-platform retrospective:

| Beat | Time | Content | What it tests |
|---|---|---|---|
| **Context** | 30-45s | Situation, constraint, baseline number | Scope, awareness |
| **Approach** | 90-120s | What you did, why, judgment call, team | Judgment, influence |
| **Outcome** | 60-90s | Result, multiple numbers, the surprise | Deliver, technical depth |
| **Lessons** | 45-60s | 2-3 transferable insights with behavior change | Learning |
| **What I'd Do Differently** | 30-45s | 2-3 specific changes with cost estimate | Self-awareness |

**Total: 4-6 minutes, target 5.**

The 60-second version of the same retrospective
would compress all 5 beats into a single paragraph:
the context in 1 sentence, the approach in 1
sentence, the outcome in 1 sentence, the lessons
in 1 sentence, and the "what I'd do differently"
in 1 sentence. The 90-second version is the same
5 sentences with more detail on Approach and
Outcome. The 3-minute version is the full 5
beats but with less detail on each. The 5-minute
version is the full structure as written.

**The structure scales.** That's the whole point.

---

## Try it

Pick the candidate from your Pass 3 list in
Lesson 02. Write it out in the 5-beat structure.
Time yourself. Aim for 4.5-5.5 minutes.

When you're done, score it against this checklist:

- [ ] Context has at least 1 number (baseline)
- [ ] Approach names a specific judgment call
- [ ] Approach names a stakeholder
- [ ] Outcome has at least 2 numbers (improvement + surprise)
- [ ] Lessons has 2-3 specific, transferable insights
- [ ] Lessons has a behavior change attached to each
- [ ] "What I'd Do Differently" has 2-3 specific changes
- [ ] "What I'd Do Differently" has a cost estimate
- [ ] Total time is 4.5-5.5 minutes
- [ ] No blame, no "we" without "I"

If any box is unchecked, rewrite that beat. The
checklist is the bar.
