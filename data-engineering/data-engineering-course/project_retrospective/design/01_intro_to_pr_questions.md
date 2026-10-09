# 01 — Introduction to Project Retrospective Questions

> **Lesson 1 of 6** · ~15 min

The Project Retrospective (PR) is the single most
under-prepared question in the EM interview loop. This
lesson maps what interviewers are actually testing, why
the PR is different from the general behavioral
"tell me about a project" prompt, and the 5 categories
of projects that tend to land best.

---

## 1. What interviewers are actually testing

When an EM interviewer asks a PR question, they are
testing for **four specific signals** — not one. Most
candidates optimize for the first one and miss the
other three, which is why they get downleveled even
when they have a great project to talk about.

### Signal 1: Judgment

The interviewer wants to know: **did you make the
right call?** Not the perfect call. The right call
*given the information you had at the time*. They're
testing whether you can reason about tradeoffs, weigh
competing constraints, and commit to a direction
under uncertainty. This is the signal that most
clearly separates an M3 from an M4, an L5 from an
L6.

A weak answer says: "We picked the best option." A
strong answer says: "We picked option A over option B
for these three reasons, knowing we'd accept cost X
in exchange for benefit Y." Specificity is the move.

### Signal 2: Learning

The interviewer wants to know: **what did you take
away from this project that you'll apply to the next
one?** A senior EM doesn't just ship; they *compound*.
The retrospective is the moment you demonstrate that
compounding — that the project made you a better
leader, not just a busier one.

A weak answer ends on "and then we shipped it." A
strong answer ends on a lesson that's *transferable*
to a project the interviewer cares about. "I now
default to a 1-page risk doc for any cutover" is
transferable. "We learned that dbt is great" is not.

### Signal 3: Technical depth

The interviewer wants to know: **do you actually
understand the system, or are you narrating someone
else's work?** EMs aren't expected to code in detail,
but they ARE expected to reason about architecture
at the level where they can ask the right questions,
spot the wrong abstractions, and debug the team's
mental model. The PR is where you demonstrate that
you can hold the technical shape of the project in
your head.

A weak answer uses terms like "the pipeline" and
"the system" without ever naming a technology, a
schema, a metric, or a tradeoff. A strong answer
names the specific tools (dbt, Snowflake, Airflow,
Kafka), the specific failure mode (silent
deserialization), and the specific reason for the
choice (cost, latency, team familiarity).

### Signal 4: Self-awareness

The interviewer wants to know: **what would you do
differently?** A senior EM has the humility to look
at their own work and see the gaps. A weak answer
is all "we" and no "I" — and it has no "what I'd do
differently" beat at all. A strong answer has 2-3
specific things you'd change, framed as growth, not
as confession.

The "what I'd do differently" beat is the move that
most candidates skip. Don't skip it.

---

## 2. How PR is different from general behavioral

A "tell me about a project" question appears in
**every** behavioral round. The PR variant is
specific to EM loops and to senior+ levels. Here's
the difference:

| | General behavioral | Project Retrospective |
|---|---|---|
| **Focus** | A category (conflict, failure, leadership) | A specific project |
| **Length** | 90-120 seconds | 3-5 minutes |
| **Structure** | STAR / CAR / PAR | CAR + Lessons + What I'd Do Differently |
| **Number of stories** | 10-15 needed | 3-5 deep ones |
| **What it tests** | Signal across 7 categories | Depth on 1 project |
| **Closer** | A takeaway | A specific change you'd make next time |

The PR is the question where you get the most
airtime. Most behavioral questions are 90-120
seconds; the PR is 3-5 minutes. That extra time is
both a gift and a trap: the gift is you can go deep,
the trap is that without structure, you'll ramble
and lose the room by minute 3.

The senior move is to **use the structure
religiously**. CAR + Lessons + What I'd Do
Differently. Five minutes. Four beats. One takeaway.
No improvising.

---

## 3. The 5 categories of PR topics

Not all projects make good retrospectives. The
interviewer is fishing for a specific kind of
project, and they're listening for specific kinds of
decisions. Across the 131 community-reported
behavioral questions in
`docs/reference/em_interview_canonical_questions.md`,
the PR questions cluster into 5 categories. The
projects that land best fall into one of these.

### Category 1: Re-platforms

The most common PR topic. A re-platform is when you
move a system from one technology to another — a
database migration, a framework migration, a
pipeline migration. Re-platforms are great PR topics
because they have:

- A clear "before" and "after" (the metric the
  interviewer will ask about)
- A natural failure mode (the migration went wrong
  somehow)
- A natural judgment call (build vs buy, big-bang vs
  incremental, shadow vs cutover)

Example prompts: "Tell me about a time you
re-platformed a system." "Walk me through a migration
you led." "Tell me about a time you replaced a
critical piece of infrastructure."

### Category 2: Launches

The second most common. A launch is when you ship a
new product, feature, or capability from zero to
one. Launches are great PR topics because they have:

- A clear outcome metric (DAU, revenue, latency,
  error rate)
- A natural ambiguity (the requirements were vague
  or shifting)
- A natural cross-functional angle (you had to
  align PM, design, sales, support)

Example prompts: "Tell me about a product you
launched." "Walk me through shipping a new
capability from scratch." "Tell me about a 0-to-1
project you led."

### Category 3: Incident response

The third most common, and often the strongest
category because it forces honesty. An incident is
when something broke in production and you had to
fix it. Incidents are great PR topics because they
have:

- A clear failure mode (the system was down or
  degraded)
- A natural root-cause analysis beat (you had to
  find the bug)
- A natural "what I'd do differently" (the post-mortem)

Example prompts: "Tell me about a production
outage you handled." "Walk me through the hardest
production incident you've worked on." "Tell me
about a time you had to debug a critical issue
under time pressure."

### Category 4: Cross-team migrations

The fourth most common, and the category that
most clearly signals senior+ scope. A cross-team
migration is when you move a system, process, or
capability across organizational boundaries —
consolidating N pipelines into one, migrating from
a per-team tool to a centralized platform, or
aligning N teams on a shared standard. These are
great PR topics because they have:

- A natural "influence without authority" beat
- A natural "scope" beat (the project is bigger
  than your team)
- A natural "competing priorities" beat (you had
  to negotiate with peer managers)

Example prompts: "Tell me about a time you
influenced teams that didn't report to you."
"Walk me through a cross-functional migration."
"Tell me about a time you had to align multiple
teams on a shared approach."

### Category 5: Technical strategy shifts

The rarest but the most senior-signal. A strategy
shift is when you change the team's technical
direction in a way that's visible across the org —
adopting a new language, moving to microservices,
moving to a monorepo, changing on-call structure,
introducing a new testing standard. These are
great PR topics because they have:

- A clear "before" and "after" (the strategy itself
  changed)
- A natural "why this and not that" beat (the
  judgment call)
- A natural "how did you get buy-in" beat (the
  influence work)

Example prompts: "Tell me about a time you
changed the technical direction of your team."
"Walk me through a technical decision you made
that had org-wide impact." "Tell me about a
time you had to convince your team to take a
hard, contrarian approach."

---

## 4. A worked example: a PR vs a non-PR

To see the difference between a PR-ready story and
a non-PR-ready story, compare these two on the
same project:

**Non-PR (90 seconds, general behavioral):**

> "I led the migration of our analytics pipeline
> from nightly batches to streaming. I worked with
> the data science team to align on the schema, and
> we shipped 4 months later. Data freshness went
> from 24 hours to sub-minute. The pattern is now
> the default for the next 2 schema changes on the
> team."

**PR (5 minutes, with structure):**

> **Context:** "We had a 4-year-old analytics
> pipeline running nightly batches. By Q3 of last
> year, the data was 24 hours stale, the cost had
> crept to $180k/year, and the data science team
> was working around the staleness with manual
> snapshots. I was the tech lead, with 4 engineers
> reporting to me, plus 3 data scientists as
> stakeholders. **Approach:** I spent 2 weeks just
> listening to the data scientists. What did they
> need? What would break? What was non-negotiable?
> I came back with a backward-compatible schema
> that preserved their existing model interfaces
> and added the new fields with sensible defaults.
> I also offered to be the point-of-contact for any
> breakage for the first 3 months. **Outcome:** We
> shipped 4 months later. Data freshness went from
> 24 hours to sub-minute. Cost dropped to $72k/year.
> Zero downstream breakage. The backward-compat
> pattern is now used for the next 2 schema changes
> on the team. **Lessons:** The biggest one is
> that 'listening first' sounds obvious but almost
> nobody does it — most engineers walk in with a
> solution. The second is that 'I'll be the
> point-of-contact' is a stronger commitment than
> 'just ping me' — it puts the social cost on me,
> not on them. **What I'd do differently:** I'd
> write the backward-compat design doc as a
> shared doc, not a 1-pager, because the
> data-science team kept asking the same questions
> for 3 weeks. And I'd have set up a shared Slack
> channel for the migration from day 1 instead of
> week 6."

Same project, same numbers, same takeaway. The PR
version has 4 more beats, 3 more numbers, and a real
"what I'd do differently" closer. That's the
difference between a 2/4 and a 4/4.

---

## Try it

Pick a project from your career — any project where
you made a meaningful decision and shipped to a
measurable outcome. Write it as a non-PR (90
seconds), then as a PR (5 minutes, using the 5-part
structure). Compare.

Notice: the project didn't change. The *telling* of
it did. That's the entire game.
