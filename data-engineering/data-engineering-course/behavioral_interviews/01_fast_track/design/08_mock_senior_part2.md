# 08 — Be Seen as a Senior Engineer (Part 2: Analysis)

> **Lesson 8 of 8 — Fast Track** · ~20 min

Frame-by-frame analysis of Sam's mock interview from Lesson 07.
Where the answers earned points, where they lost them, and exactly
what Sam should have said instead.

---

## 1. The summary

| Q | Question | Score | Verdict |
|---|---|---|---|
| 1 | Tell me about yourself | 2 | Functional but unremarkable |
| 2 | Project you're proud of | 2.5 | Has the bones, lacks the senior frame |
| 3 | Conflict with a coworker | 1 | Red flags: blaming, escalation framing |
| 4 | Tell me about a failure | 1 | Confession without growth |
| 5 | How do you handle ambiguity | 1 | Generic, no story, no specifics |
| 6 | Influence without authority | 2.5 | Right story, but a re-tread of Q2 |
| 7 | Questions to ask | 2 | Generic, recruiter-question level |

**Net: 1.8 / 4.0.** This is a **downlevel signal.** A hiring
committee would look at this and either reject or push Sam to E4.

The good news: Sam has the *material* for a strong E5 answer in
every one of these questions. The work was real. The framing was
just below the bar. This lesson is about that gap.

---

## 2. Q1: "Tell me about yourself" — 2/4

**What worked:** Sam did the basic structure (background, current
role, why this company). No ramble, no "I grew up in Ohio" filler.

**What didn't:** The answer is *generic*. There is no hook, no
signal, no reason for the interviewer to remember Sam 30 seconds
later. "I want to work on bigger systems with more users" is the
answer every candidate gives. The interviewer will hear this 6
times in a day.

**What Sam should have said:**

> *"I'm a data engineer with 6 years of experience, and the work
> I'm proudest of is the streaming migration I led at my current
> company — it changed how the whole analytics org works, not
> just my team. What I'm looking for now is to do that kind of
> cross-team work at a larger scale, which is why I'm excited
> about [Company]'s data platform. Three things I'd want you to
> know about me: I tend to over-index on stakeholder alignment
> before I start building; I've gotten good at estimating work
> that has a lot of moving parts; and I care a lot about
> observability — I'd rather have a good dashboard than a clever
> algorithm."*

Why this is stronger: the 60-second version of Sam has **three
specific signals** (stakeholder alignment, estimation, observability)
that the interviewer can probe later. Each one is a potential follow-
up question and a potential "above the bar" mark on the rubric.

---

## 3. Q2: "Project you're proud of" — 2.5/4

**What worked:** Sam picked a real, concrete project. The number
(24 hours → under a minute) is good. The mention of cross-team
work (data science) is a senior signal.

**What didn't:** The answer is *chronological* ("we did A, then
B, then C") rather than *thematic*. The reader can't tell what
Sam's *specific* contribution was. "I designed the new
architecture" — but what was the design? What were the
alternatives? What was hard?

**What Sam should have said:**

> *"The project I'm proudest of is the streaming migration at
> [company] — partly because of the technical result, but more
> because of the organizational result. When I started, the
> data science team was actively blocking the migration because
> they were worried about schema changes breaking their
> downstream models. I spent two weeks just listening to them —
> what they needed, what would break, what was non-negotiable.
> I came back with a proposal: a backward-compatible schema with
> a 6-month deprecation window, plus me as the point of contact
> for any breakage. The technical architecture was relatively
> straightforward Kafka + Flink, but the *alignment* was the
> actual work. We shipped 4 months later. Data freshness went
> from 24 hours to sub-minute. The data science team's models
> didn't break. And the next time we did a schema change, we
> used the same playbook."*

The reframe: same project, but now the **decision under
ambiguity** (how to align the data science team) is the *protagonist*
of the story, not the technical architecture. The technical
architecture is mentioned in one sentence. The people work is
the whole story.

---

## 4. Q3: "Conflict with a coworker" — 1/4

**What worked:** Sam told a real story.

**What didn't:** Almost everything else.

- "He was resistant" — other person is the obstacle.
- "I tried to convince him but he wasn't really budging" —
  the other person is unreasonable.
- "I ended up going to my manager" — escalation is the move.
- "My manager agreed with me" — I won.
- "He came around eventually" — eventual vindication.
- "Sometimes you just have to escalate" — the takeaway is "I
  was right and I went around him."

**The interviewer's mental model after this answer:** *"This person
will, in 6 months, be the person I'm having a hard conversation
with. They escalate instead of persuading, they frame disagreement
as the other person being unreasonable, and they take credit for
the resolution. Hard no."*

**What Sam should have said:**

> *"I had a peer who was skeptical of moving from batch to streaming
> because he'd had a bad experience with Kafka at his previous
> company. I disagreed — our scale and our use case were different
> — but I also didn't want to dismiss his experience, because the
> failure mode he was worried about (operational complexity, on-
> call burden) was real even if the conclusion was different.*
>
> *What I did: I asked him to write a one-page doc on the specific
> risks he was worried about. I wrote a one-page doc on the risks
> of *not* moving. We presented both to the team. The conversation
> shifted from 'are you for or against' to 'here are the actual
> risks and here are the mitigations.' We ended up with a hybrid
> approach that addressed most of his concerns — including a 6-
> month parallel-running period so the on-call burden was bounded.*
>
> *What I learned: technical disagreement is often a proxy for
> unstated risk concerns. Surfacing the underlying risk turns
> the conversation from 'who's right' to 'how do we both de-
> risk.'"*

Why this is stronger: Sam shows **empathy for the other person**,
**structured disagreement**, and **synthesis** rather than
victory. The interviewer reads this and thinks: *"This person
will be a peer I trust in a hard conversation."*

---

## 5. Q4: "Tell me about a failure" — 1/4

**What worked:** Sam admitted to a real failure.

**What didn't:** The rest. The "requirements kept changing" framing
blames external circumstances. The "I learned that I need to be
more careful" takeaway is generic. The "we shipped it and it was
fine" outcome downplays the failure. The whole story says:
*"It wasn't really my fault, and I don't have a specific change
to point to."*

**What Sam should have said:**

> *"I missed a Q3 deadline on a 6-week project that ended up
> taking 10 weeks. The proximate cause was scope creep — the
> requirements evolved 3 times during the project. The root
> cause was mine: I treated each scope change as a one-off
> request instead of a signal that I didn't have a shared
> definition of done with the PM. I just kept absorbing the
> changes.*
>
> *What I changed: I now write a one-page 'definition of done'
> doc at the start of every project with my PM counterpart,
> signed off by both of us. Any change to the doc is treated as
> a scope change, with an explicit re-estimate. We've been
> within 10% of estimate on the last four projects."*

Why this is stronger: the failure has a **specific cause** (no
shared definition of done), a **specific change** (definition of
done doc), and a **measurable outcome** (within 10% of estimate
on four projects). The interviewer reads this and thinks: *"This
person learns, propagates the learning, and the team is better
for it."*

---

## 6. Q5: "How do you handle ambiguity?" — 1/4

**What worked:** Sam said "ask a lot of questions," which is at
least the right direction.

**What didn't:** This is a values-and-judgment question (see
`04_three_question_types.md`). It needs a specific story. Sam
gave a philosophy lecture. There is no evidence, no number, no
instance. This is the most common downlevel answer pattern.

**What Sam should have said:**

> *"I think ambiguity is uncomfortable, and I think the
> uncomfortable feeling is information. When I notice it in
> myself, that's usually the signal that I haven't pinned down
> the actual decision we're making.*
>
> *Concrete instance: last year, I was given a 1-line mandate
> — 'improve our data quality.' That was the brief. I had no
> idea what 'data quality' meant in our context. What I did:
> I scheduled four 30-minute interviews with the top consumers
> of our data, asked each of them what they wished was different,
> and built a 1-page list of the actual problems they cared
> about. Three of them were the same — late-arriving events in
> the user-events table. I scoped the project to that.*
>
> *If I'd skipped the interviews, I'd have spent 3 months
> building generic data-validation tooling. Instead I spent 6
> weeks on a specific fix that the top 3 consumers actually
> wanted, and we cleared the late-events backlog that had been
> a recurring ticket for 2 years."*

Why this is stronger: the **specific** is doing all the work.
"I ask a lot of questions" is a claim. "I scheduled four
interviews, found that 3 of 4 had the same problem, and scoped
to that" is evidence.

---

## 7. Q6: "Influence without authority" — 2.5/4

**What worked:** Right story (data science team), right tactic
(listening, then proposing).

**What didn't:** This is essentially Q2 with a different opening.
The interviewer will notice the re-tread. Also: no number, no
specific example of what changed.

The fix is mostly: **add a number, end with a beat**. Same story
arc as the rewritten Q2, but with a clear outcome ("the schema
change was adopted by all 3 downstream teams within 6 weeks")
and a takeaway ("the pattern I now use for any cross-team schema
change is...").

---

## 8. Q7: "Anything you'd like to ask me?" — 2/4

**What worked:** Sam asked a question.

**What didn't:** "What does the team look like" is a question for
the recruiter, not the hiring manager. It's a wasted opportunity.

For a senior candidate, the reverse-interview questions should
signal senior-level thinking. See `05_workshops/04_reverse_interview.md`
for the full list. Three strong options for this interviewer:

- *"What's the biggest thing the team has disagreed about in
  the last 6 months, and how did you resolve it?"*
- *"What's something you'd want a new senior engineer to be
  doing differently in their first 90 days?"*
- *"What's a recent decision the team made that you're still
  not sure was the right call?"*

These signal: *"I think about how teams make decisions, I
take the on-ramp seriously, and I have the seniority to engage
with hard questions."*

---

## 9. The pattern

Every one of Sam's answers had the right *material*. The work
was real. The projects were real. The numbers were accessible.
The growth was real.

What was missing was **the senior frame**:
- The decisions are not named
- The people work is under-emphasized
- The numbers are vague or missing
- The failure story has no specific change
- The values-and-judgment question is answered as a philosophy

If Sam takes the same set of stories, applies the rewrites above,
and delivers them in 90-120 seconds each, the scorecard flips
from 1.8/4.0 to ~3.2/4.0. **That's the difference between a
downlevel and an offer.**

---

## Try it

Pick one of the answers above (Q3 is the most instructive).
Write your own rewrite of the same story. It should be:
- 90-120 seconds when spoken
- Contain a specific decision
- Contain a number
- Not blame the other person
- End with a specific takeaway

Then read yours out loud, time it, and score it against the
5-bar checklist from `03_avoiding_downleveling.md`.
