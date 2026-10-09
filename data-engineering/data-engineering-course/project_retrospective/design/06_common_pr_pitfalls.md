# 06 — Common Project Retrospective Pitfalls

> **Lesson 6 of 6** · ~20 min

The 8 most common PR pitfalls, why they happen, what
to do instead, and a sample rewrite for each. These
are the patterns that turn a 4/4 retrospective into
a 2/4 — the patterns that get senior candidates
downleveled because their *telling* undersold their
actual work.

Each pitfall has the same shape:

- **The pitfall** (what it sounds like)
- **Why it happens** (the mental model behind it)
- **What to do instead** (the fix)
- **Sample rewrite** (before / after)

Read this list once, then run your own retrospectives
through it as a checklist.

---

## Pitfall 1: Over-using "we"

**The pitfall:** "We decided to migrate to dbt and
Snowflake. We built it out over 4 months. We shipped
on time. We reduced cost by 60%."

**Why it happens:** Candidates are trained to avoid
"I" because it sounds boastful. The "we" is meant
to share credit.

**The problem:** The interviewer is evaluating
*you*, not your team. "We" without "I" reads as
narrating someone else's work. It's also where
junior candidates hide — the "we" lets them avoid
owning the specific decision.

**What to do instead:** Use "I" for *your*
decisions and "we" for *team* execution. The
balance should be roughly 30% "I" and 70% "we" —
but the "I" should be on the judgment calls.

**Sample rewrite:**

> ❌ "We decided to migrate to dbt and Snowflake. We
> built it out over 4 months. We shipped on time.
> We reduced cost by 60%."
>
> ✅ "I picked dbt and Snowflake after a 2-week
> evaluation, with input from the team. I designed
> the migration plan and we built it out over 4
> months. We shipped on time, and cost dropped 60%
> — which I underestimated, because Snowflake's
> auto-suspend turned out to be much more
> aggressive than our EC2 setup had been."

---

## Pitfall 2: Skipping the metrics

**The pitfall:** "We shipped on time. The data is
much fresher now. The cost is way down."

**Why it happens:** Candidates know the project
was a success but didn't capture the specific
numbers. They default to qualitative descriptors
("much fresher", "way down") because the exact
number is fuzzy.

**The problem:** Qualitative descriptors are
forgettable. "Much fresher" doesn't survive the
interview debrief. The interviewer is writing
notes for the hiring committee, and "much fresher"
becomes "vague impact" in the writeup.

**What to do instead:** Every Outcome beat needs
*at least 2 numbers* — one for the improvement
and one for the surprise. If you don't have the
exact number, estimate it and own the estimate
("roughly 8 hours", "about 60% lower").

**Sample rewrite:**

> ❌ "We shipped on time. The data is much fresher
> now. The cost is way down."
>
> ✅ "We shipped on time. Runtime went from 8 hours
> to 45 minutes — a 10x improvement. Cost dropped
> from $180k a year to $72k. Data freshness went
> from 24 hours to sub-minute."

---

## Pitfall 3: Blaming others

**The pitfall:** "The data science team was
blocking the migration because they didn't
understand the new schema. I had to spend weeks
getting them on board."

**Why it happens:** Candidates remember the
friction more vividly than the cooperation. The
"us vs. them" framing is a natural cognitive bias.

**The problem:** Blaming is a 1/4. Period. It
signals that the candidate externalizes problems
instead of solving them, which is the opposite of
the senior signal. Even if the data science team
*was* blocking, the candidate's job was to unblock
them.

**What to do instead:** Reframe every "they" into
"we". The data science team's concerns become
"the constraints we had to design around". Their
delay becomes "the timeline we budgeted for".

**Sample rewrite:**

> ❌ "The data science team was blocking the
> migration because they didn't understand the new
> schema. I had to spend weeks getting them on
> board."
>
> ✅ "The data science team had legitimate concerns
> about downstream breakage. I spent 2 weeks
> understanding their constraints, and came back
> with a backward-compatible schema that addressed
> their top 3 concerns. All 3 signed off within 2
> weeks."

---

## Pitfall 4: "Everything went well" stories

**The pitfall:** "The project was a great success.
The team executed well. We hit all our milestones.
The new system is in production and everyone is
happy."

**Why it happens:** Candidates think the
interviewer wants to hear about success, and they
default to the press-release version.

**The problem:** A retrospective without a failure
beat is *not credible*. Every project has
something that went wrong. The candidate who can't
name what went wrong either didn't notice (a red
flag for lack of self-awareness) or is hiding
something (a red flag for lack of honesty).

**What to do instead:** Name the unexpected beat —
good *or* bad. "The unexpected part was..." is
the move. A negative surprise that you recovered
from is more credible than 5 minutes of unalloyed
success.

**Sample rewrite:**

> ❌ "The project was a great success. The team
> executed well. We hit all our milestones. The new
> system is in production and everyone is happy."
>
> ✅ "We shipped on schedule, but the migration
> took 2 weeks longer than I'd estimated because
> 3 of our 12 source systems had un-documented
> schema drift. We caught all 3 during shadow mode,
> which is why I'd pushed for the 3-week parallel
> run."

---

## Pitfall 5: Skipping "what I'd do differently"

**The pitfall:** The retrospective ends on the
Outcome beat. "And then we shipped. The end."

**Why it happens:** Candidates run out of time, or
they don't know what to put in the beat, or they
think admitting mistakes is weakness.

**The problem:** "What I'd Do Differently" is the
self-awareness signal. Skipping it is a 1-point
deduction. It's the beat that most clearly
separates an L5 from an L6 — the L6 has the
humility to look at their own work and see the
gaps.

**What to do instead:** Always have 2-3 specific
changes. "I'd communicate better" is generic and
forgettable. "I'd write the design doc as a shared
doc, not a 1-pager" is specific and credible.

**Sample rewrite:**

> ❌ "And then we shipped. The end."
>
> ✅ "Two things I'd change. First, I'd write the
> backward-compat design doc as a shared doc, not a
> 1-pager, because the data-science team kept
> asking the same questions for 3 weeks. Second,
> I'd set up a shared Slack channel for the
> migration from day 1, not week 6 — we lost
> context twice in the first 5 weeks. Both changes
> would have saved us 2-3 weeks of miscommunication."

---

## Pitfall 6: Vague technical depth

**The pitfall:** "We migrated to a modern data
stack. The new system is much more scalable. The
team is using best practices."

**Why it happens:** Candidates who weren't deep on
the technical work default to abstractions ("modern
data stack", "best practices", "scalable") because
they don't have the specifics.

**The problem:** EMs aren't expected to code, but
they ARE expected to reason about architecture at
the level where they can ask the right questions.
"Modern data stack" is a buzzword; "dbt
materializations on Snowflake with auto-suspend"
is a system. The interviewer is testing which one
the candidate can hold in their head.

**What to do instead:** Name the specific tools,
the specific failure mode, the specific reason for
the choice. "We picked dbt over hand-rolled SQL
because the materialization efficiency was 5-10x
better, and the cost reduction came from
Snowflake's auto-suspend" is technical depth.

**Sample rewrite:**

> ❌ "We migrated to a modern data stack. The new
> system is much more scalable. The team is using
> best practices."
>
> ✅ "We moved from hand-rolled Airflow SQL to dbt
> on Snowflake. The 10x runtime improvement came
> from dbt's incremental materializations, which
> only re-process the partitions that changed. The
> 60% cost reduction came from Snowflake's
> auto-suspend, which kicked in much more
> aggressively than our EC2 setup had."

---

## Pitfall 7: Generic lessons

**The pitfall:** "I learned that communication is
important. I learned that stakeholder alignment
matters. I learned that migrations are hard."

**Why it happens:** Candidates reach the Lessons
beat without having thought about what they
actually learned. They default to platitudes.

**The problem:** Generic lessons signal that the
candidate didn't actually learn anything specific
to *this* project. "Communication is important" is
true of every project ever; it's not a takeaway.

**What to do instead:** Every lesson should have
*two* parts: (1) the specific insight from *this*
project, and (2) the behavior change you'll apply
*next* time. "I now default to a 2-week listening
phase on any cross-team migration" is specific and
behavioral.

**Sample rewrite:**

> ❌ "I learned that communication is important. I
> learned that stakeholder alignment matters. I
> learned that migrations are hard."
>
> ✅ "Three lessons. First, 'listening first'
> sounds obvious but almost nobody does it — the 2
> weeks I spent listening saved us months of
> downstream breakage. I now default to a 2-week
> listening phase on any cross-team migration.
> Second, 'I'll be the point-of-contact' is a
> stronger commitment than 'just ping me' — it puts
> the social cost on me. I now use this phrasing
> deliberately. Third, shadow mode is a default for
> me on any non-trivial cutover — it caught 2 of
> the 3 risks I'd flagged."

---

## Pitfall 8: Rambling past 5 minutes

**The pitfall:** The retrospective runs to 7, 8,
even 10 minutes. The interviewer is visibly
checking the clock. The candidate is still
describing the cutover.

**Why it happens:** Candidates think the value is
in the detail, and they keep adding "one more
thing" to make sure the interviewer has the full
picture.

**The problem:** Past 5 minutes, you're losing the
room. The interviewer's note-taking has stopped.
Their attention has drifted. The signal you think
you're sending ("look how thorough I am") is the
opposite of the signal you're actually sending
("look how little I respect the format").

**What to do instead:** Time yourself. Rehearse
at 5 minutes. If you go over, the cut is in the
Context beat (drop the team description) or the
Outcome beat (drop the recap of every metric), not
in the Lessons or "What I'd Do Differently" beats.

**Sample rewrite:**

> ❌ [7 minutes of dense, undifferentiated detail
> about the migration, including the team
> structure, the 4 standup cadence choices, the 3
> retrospective decisions, the dbt-vs-SQLBench
> evaluation, and a digression on the data
> governance review]
>
> ✅ [5 minutes of structure: Context with 3
> numbers, Approach with the judgment call,
> Outcome with 4 numbers + the surprise, Lessons
> with 3 specific takeaways, "What I'd Do
> Differently" with 2 specific changes. The
> standup cadence, the SQLBench evaluation, and
> the data governance review are all available as
> follow-up material if the interviewer asks.]

---

## The pre-interview self-audit

Before any interview, run your 3 retrospectives
through this checklist. If any of them trip a
pitfall, fix it.

- [ ] "I" appears at least 5-7 times in the
      5-minute version
- [ ] At least 4 specific numbers (latency, cost,
      freshness, scale, etc.)
- [ ] No "they" without "we" reframing
- [ ] At least one negative surprise, named
      specifically
- [ ] "What I'd Do Differently" has 2-3 specific
      changes with a cost estimate
- [ ] Specific tools, schemas, and failure modes
      are named (not "the system", "the pipeline",
      "the team")
- [ ] Every lesson has a behavior change attached
- [ ] Total time is 4.5-5.5 minutes

If any box is unchecked, rewrite that beat. The
checklist is the bar.

---

## Try it

Take one of your 3 retrospectives. Read it
aloud. Score it against the 8-pitfall checklist.
For any pitfall you trip, do the sample rewrite
exercise on that specific beat.

Then re-record the retrospective and re-score.
Repeat until all 8 pitfalls are clean.

This is the last step before the interview. The
retrospective that passes the audit is the one
you take into the room.
