# 05 — Project Retrospective Example

> **Lesson 5 of 6** · ~20 min read

The full, 5-minute worked example. This is the
centerpiece of the track — a realistic Project
Retrospective on a real-shaped project, walked
through with the 5-beat structure from Lesson 03
and annotated to show what each beat is doing.

The project: **re-platforming a 4-year-old nightly
ETL pipeline from a custom Airflow-on-EC2 setup to
dbt + Snowflake, reducing cost by 60% and runtime
from 8 hours to 45 minutes.**

Read it twice. First, read it straight through as
if you were the interviewer. Then read it a second
time with the annotations — they show what each
beat is testing and why each sentence is where it
is.

---

## The retrospective (5-minute spoken version)

> **Context.** "Two years ago I inherited a
> 4-year-old nightly ETL pipeline that ran on a
> custom Airflow-on-EC2 setup. By the time I
> took it over, the runtime had crept to 8 hours,
> the cost was $180,000 a year, and the data was
> 24 hours stale by the time the morning dashboards
> ran. The data science team had started working
> around the staleness with manual snapshots — which
> was expensive, error-prone, and unsustainable. I
> was the tech lead, with 4 engineers reporting to
> me, and 3 data scientists as my primary
> stakeholders. The mandate from my director was
> clear: fix the cost and the staleness, and don't
> break the data-science models in the process.
>
> **Approach.** "The first thing I did — and this
> is the part I'd want a senior EM candidate to
> emphasize — I spent two weeks just listening. I
> scheduled 90-minute working sessions with each
> of the 3 data scientists whose models were most
> affected by the migration. I asked them three
> questions: what do you need, what would break
> under a naive cutover, and what's non-negotiable.
> I came back with a proposal: a backward-
> compatible schema that preserved their existing
> model interfaces and added the new fields with
> sensible defaults. I also offered to be the
> point-of-contact for any breakage for the first
> three months. That last bit mattered more than
> I expected — it put the social cost on me, not
> on them.
>
> "All three signed off within two weeks. Two
> migrated immediately. The third delayed by two
> months, which we'd explicitly budgeted for. The
> actual migration took four months from kickoff
> to final cutover, with a three-week shadow mode
> where the new pipeline ran in parallel with the
> old one and we compared row-by-row.
>
> **Outcome.** "We shipped on schedule. Runtime
> went from 8 hours to 45 minutes — a 10x
> improvement, mostly because dbt materializations
> are dramatically more efficient than the
> hand-rolled SQL we'd been running. Cost dropped
> from $180k a year to $72k a year, a 60%
> reduction. Data freshness went from 24 hours to
> sub-minute, because the new pipeline could run
> on every commit instead of nightly. Zero
> downstream breakage across the 12 data-science
> models in production.
>
> "Two things went differently than I'd planned.
> The first was positive: the cost reduction was
> *larger* than we'd projected, because Snowflake's
> auto-suspend kicked in much more aggressively
> than our EC2 setup had. The second was negative:
> the migration took 2 weeks longer than I'd
> estimated, because we discovered that 3 of our
> 12 source systems had un-documented schema drift
> — fields that had been added or renamed without
> anyone telling the data team. We caught all 3
> during shadow mode, which is exactly why I'd
> pushed for the 3-week parallel run in the
> Approach beat. If we'd done a big-bang cutover,
> those 3 schema drifts would have hit production
> and broken at least 4 of the 12 downstream
> models.
>
> **Lessons.** "Three lessons, all transferable.
> First, 'listening first' sounds obvious but
> almost nobody does it — most engineers walk
> into a stakeholder meeting with a solution. The
> 2 weeks I spent listening to the data science
> team saved us months of downstream breakage. I
> now default to a '2 weeks of listening' on any
> cross-team migration, no matter how clear the
> technical path looks. Second, 'I'll be the
> point-of-contact' is a stronger commitment than
> 'just ping me' — it puts the social cost on me,
> not on them, which is what unlocked the data
> science team's signoff. I now use this phrasing
> deliberately. Third, shadow mode is a default
> for me on any non-trivial cutover. The 3-week
> parallel run caught 2 of the 3 risks I'd flagged
> in the design doc. Without it, we'd have shipped
> a regression.
>
> **What I'd Do Differently.** "Two things, and
> both are about communication, not code. First,
> I'd write the backward-compat design doc as a
> shared, living document — not a 1-pager — because
> the data science team kept asking the same
> questions for 3 weeks, and a 1-pager forces
> follow-up. A shared doc would have let them
> comment inline and saved us about 2 weeks of
> email back-and-forth. Second, I'd set up a
> shared Slack channel for the migration from day
> 1, not week 6. The first 5 weeks of stakeholder
> coordination happened over email, and we lost
> context twice — once on the schema design and
> once on the cutover timing. Both of these
> changes would have saved us 2-3 weeks of
> miscommunication, which is a third of the
> schedule slip we ended up with. The technical
> work was fine. The communication was the
> bottleneck."

**Time: 4 minutes 50 seconds at 150 wpm.** Within
the 5-minute target.

---

## What each beat is doing (annotation)

The retrospective is 5 beats, but each beat is
testing a specific signal. Here's the annotation.

### Context (45 seconds)

**What it's doing:** Establishing scope, baseline,
and stakes.

**The signal it's testing:** *Did you understand
the problem?*

- The "8 hours" / "$180k" / "24 hours" baseline
  anchors the rest of the story. The interviewer
  now knows what you're solving for, and they have
  a yardstick for the Outcome beat.
- The "data science team" stakeholder tells the
  interviewer that this was a cross-team project,
  not a solo effort. That's a senior signal.
- The "I was the tech lead, 4 engineers, 3
  data scientists" line establishes scope without
  being long. It's 10 words; it does a lot of work.
- The "don't break the data-science models"
  constraint is the *real* mandate. It tells the
  interviewer what you had to optimize for, which
  sets up the Approach beat.

### Approach (90 seconds)

**What it's doing:** Naming the judgment call.

**The signal it's testing:** *Did you make the
right call?*

- "The first thing I did — and this is the part
  I'd want a senior EM candidate to emphasize — I
  spent two weeks just listening." This is the
  meta-signal: the candidate knows what the
  interviewer is looking for, and they're leaning
  into it. Senior candidates do this. Junior
  candidates apologize for "wasting time" on
  listening.
- "What do you need, what would break, what's
  non-negotiable." The 3 questions are specific
  and tactical. The interviewer can picture the
  meeting.
- "Backward-compatible schema... I also offered to
  be the point-of-contact." Two specific moves,
  not one. Both are judgment calls. Both are
  defensible.
- "Two migrated immediately, the third delayed 2
  months, which we'd budgeted for." This is the
  humility beat: not everything went perfectly,
  but you'd planned for the imperfection. Senior
  candidates do this. Junior candidates pretend
  everything went perfectly.
- "3-week shadow mode." Set up explicitly so the
  Outcome beat can pay it off. That's the
  structure working.

### Outcome (90 seconds)

**What it's doing:** Quantifying the result AND
the surprise.

**The signal it's testing:** *Did you ship? Did
you understand what you shipped?*

- "8 hours → 45 minutes" / "$180k → $72k" /
  "24 hours → sub-minute" / "0 downstream
  breakage." Four numbers, each one a different
  axis (latency, cost, freshness, safety). The
  interviewer can't ask for a number you don't
  have.
- "Two things went differently than I'd planned.
  The first was positive... the second was
  negative." This is the credibility move. Every
  project has surprises; the candidate is naming
  both the good and the bad. That's senior.
- "3 of our 12 source systems had un-documented
  schema drift." Specific, technical, honest.
  This is the technical depth signal — the
  candidate understands the system at the level
  where they can name the failure mode.
- "We caught all 3 during shadow mode, which is
  exactly why I'd pushed for the 3-week parallel
  run in the Approach beat." The setup-payoff
  loop closes. The shadow mode isn't a footnote;
  it's a vindication.

### Lessons (60 seconds)

**What it's doing:** Naming the transferable
insights.

**The signal it's testing:** *Did you learn?*

- Three lessons, each with a behavior change.
  Not "I learned that migrations are hard" (the
  weak version). "I now default to a '2 weeks of
  listening' on any cross-team migration" (the
  strong version).
- Each lesson is a *pattern*, not a *project
  fact*. The 2-weeks-of-listening applies to any
  cross-team migration, not just dbt-on-Snowflake.
  That's what makes it transferable.
- The 3 lessons are sequenced in increasing
  seniority: stakeholder alignment (M3) → social
  commitment (M4) → technical discipline (M4-M5).
  The interviewer is reading 3 levels of seniority
  in 60 seconds.

### What I'd Do Differently (45 seconds)

**What it's doing:** Demonstrating self-awareness.

**The signal it's testing:** *Do you have the
humility to see your own gaps?*

- "Two things, and both are about communication,
  not code." The candidate is explicitly *not*
  blaming the team, the data scientists, the
  tools, or the timeline. They're blaming
  themselves, which is the senior move.
- "I'd write the doc as a shared doc, not a
  1-pager." Specific. Actionable. Credible.
- "I'd set up a shared Slack channel from day 1,
  not week 6." Specific. Actionable. Credible.
- "Both of these would have saved us 2-3 weeks of
  miscommunication, which is a third of the
  schedule slip." The candidate quantifies the
  cost of their own communication gaps. That's
  rare. That's a 4/4.

---

## Why this retrospective lands

Three reasons.

**1. It has 6 numbers, 4 specific decisions, 3
lessons, and 2 honest changes.** That's the density
of a senior answer. A junior answer has 1-2 numbers,
1 decision, 1 generic lesson, and 0 honest changes.

**2. It has structure.** The 5 beats are clean, the
setup-payoff loops close, and the cadence is
unbroken. The interviewer can follow without
working.

**3. It's honest.** The candidate admits the
migration took 2 weeks longer than estimated. The
candidate admits the 1-pager was a mistake. The
candidate admits the Slack channel should have been
set up earlier. No "we" without "I". No blame. No
boasting. Just specific, honest, accountable
narrative.

That's the bar. A retrospective that lands is a
retrospective that does all three.

---

## Try it

Read this retrospective out loud, twice. Time
yourself. Note the cadence. Note the places where
you'd naturally pause for emphasis.

Then pick one of your own retrospectives and write
it in the same shape. Use the same number density
(4+ numbers), the same lesson density (3 lessons
with behavior changes), and the same "what I'd do
differently" density (2 specific changes with a
cost estimate).

When your retrospective matches this density, it
will land.
