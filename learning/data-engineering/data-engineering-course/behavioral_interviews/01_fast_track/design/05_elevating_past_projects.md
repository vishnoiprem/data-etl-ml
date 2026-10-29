# 05 — Elevating Your Past Projects

> **Lesson 5 of 8 — Fast Track** · ~12 min

The most underrated skill in behavioral interviewing: **taking a
mundane piece of work and framing it as a senior-level story.**
Most candidates have 3-5 interesting projects and 20+ boring ones.
The senior move is to elevate the boring ones.

---

## 1. The reframe

Every piece of work has a senior story inside it. The reframe
isn't dishonest — it's about **choosing which aspect of the work
to emphasize**. The same six months of work can be told as:

- "I shipped a feature" (E4)
- "I shipped a feature" (E4 again, no matter how many times you
  say it)
- "I drove the cross-team rollout of a feature that required
  negotiating schema changes with 4 downstream consumers and
  running a 3-week shadow mode" (E5)
- "I led the technical strategy for our team's surface area in
  the unified billing platform, aligning the long-term direction
  with two other teams and a director-level stakeholder" (E6)

All four are *true* descriptions of the same work. The work didn't
change. **The framing did.**

---

## 2. The three elevation moves

### Move 1: From output to outcome

**Output (E4):** "I built a dashboard that shows pipeline health."

**Outcome (E5):** "I built a pipeline health dashboard that the on-
call team now uses as their primary triage tool. We've cut mean
time-to-detect from 47 minutes to 6 minutes — a 7× improvement —
and the on-call rotation has gone from a 2-person pain point to
something the team actively volunteers for."

To make this move, ask: **"What did the work let someone else do,
that they couldn't do before?"** If you can answer that, you have
an outcome.

### Move 2: From "I" to "I, in a system"

**Solo (E4):** "I wrote a Python script to detect schema drift
between our staging and production databases."

**System (E5):** "I designed a schema-drift detection system that
runs as a pre-merge CI check, so every PR that introduces a
breaking change gets flagged before it ships. We caught 23
breaking changes in the first month and the rate of new ones has
dropped 80%. The pattern is now used by two other teams."

To make this move, ask: **"What did I do to make this scale
beyond me, beyond this one moment?"** If you wrote a script and
ran it once, that's an output. If you wrote a script and made it
part of the team's workflow, that's a system.

### Move 3: From "task" to "decision under constraint"

**Task (E4):** "I migrated the database from MySQL to Postgres."

**Decision (E5):** "We had to migrate the user-table from MySQL
to Postgres as part of a 6-month platform consolidation. The
constraint was zero downtime and no data loss across a 200M-row
table with active writes. The decision I owned: cutover strategy.
I evaluated three approaches (logical replication, dual-write,
maintenance window), and chose dual-write with a 4-hour shadow
validation period. We caught 11 silent truncation bugs that
logical replication would have shipped to production. Cutover
finished on schedule with zero incidents."

To make this move, ask: **"What was the hard call I made, and
what did I consider and reject?"** If your story has a moment
where you picked option A over option B and can defend why, you
have a decision.

---

## 3. The "boring" project test

Apply this to a project you think is too boring to put in an
interview. Write down the answers:

1. What was the **specific technical challenge** (not "it was hard"
   but "we had X, Y, Z conflicting constraints")?
2. Who **else** was involved or affected, and what did you have to
   align them on?
3. What **changed** in the system, the team, or the business as a
   result of your work (with a number if possible)?
4. What would have **happened if you hadn't done it**, or if
   you'd done it differently?

If you can answer 3 of 4 with specifics, you have a senior story.
Most candidates are surprised by how much senior-level judgment was
involved in work they remember as "just a project."

---

## 4. A worked example: "I just shipped a feature"

Imagine your actual work for the last 6 months was a routine
feature: a new export endpoint for our analytics product. You
remember it as "I shipped the export endpoint and we had a few
bugs in the first week."

That's not a story. But the *real* story might be:

> *"I owned the new analytics export endpoint. The challenge was
> that we had 4 different internal consumers, each with their own
> ad-hoc data format, and our CS team was spending ~10 hours/week
> manually reformatting exports for the top 3 enterprise customers.*
>
> *What I did: I sat with the 4 consumer teams, defined a single
> canonical export format that covered ~80% of the use cases, and
> shipped a new endpoint that supported both the canonical format
> and 3 backward-compat format flags. Migration was opt-in per
> consumer.*
>
> *Outcome: 3 of the 4 teams migrated within the first month.
> CS reclaimed 8 hours/week. The 4th team migrated the following
> quarter after their downstream consumer updated. We standardized
> the canonical-format approach for the next two export endpoints
> the team shipped.*
>
> *What I'd do differently: I would have started the
> stakeholder-alignment conversation a month earlier. I lost
> 3 weeks to a CSV-vs-JSON debate that I could have settled in
> one meeting with the right people in the room."*

The work didn't change. The framing elevated a "boring feature"
into a story with cross-team alignment, format design, migration
strategy, and a measurable outcome. **Same six months, same code,
same PRs.** The only thing that changed is which 90 seconds you
chose to talk about.

---

## 5. What to do with the work that truly has no story

Sometimes the work really is just "I shipped a thing." That's fine —
you don't have to use every project. The story bank in Module 03
helps you identify the 10-15 stories that *do* have senior-level
signal and retire the rest.

The trap to avoid: **don't fabricate a story to fit a question.**
If the interviewer asks about a time you had a major conflict and
the only conflict you can think of is "my PM wanted red and I wanted
blue," it's better to honestly use a smaller, real conflict than
to make up a big, fake one. Interviewers can tell, and fabrication
is an instant downlevel.

---

## Try it

Pick a project from the last 6 months that you think is too
mundane to use in an interview. Spend 10 minutes applying the
"boring project test" from Section 3. Then spend 10 minutes
writing the story using Moves 1, 2, and 3 from Section 2.

If you end up with a 90-second story that includes a specific
decision, a number, and a takeaway — congratulations, you just
turned a "boring" project into interview material.
