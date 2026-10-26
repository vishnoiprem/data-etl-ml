# 01 — An Introduction to People Management

> **Lesson 1 of 21 — Overview** · ~20 min

What the People Management round actually tests, the 5 categories of
EM questions, what the rubric looks like at Meta M5 / Google L6, and
why this round is the most common downlevel vector for senior ICs
transitioning to management.

---

## 1. What the round actually tests

The People Management round (sometimes called "EM Behavioral" or
"People & Leadership") is **45-60 minutes, 5-7 questions, all
behavioral**. The questions are drawn almost entirely from the 22
People Management + the 131 Behavioral questions in
`docs/reference/em_interview_canonical_questions.md`. The format is
identical to senior-IC behavioral: STAR / PAR stories, 90-120
seconds, "so what" beats.

The difference is **what the interviewer is listening for**.

A senior-IC interviewer is listening for: *Can this person navigate
ambiguity? Can they influence without authority? Can they make hard
tradeoffs and own the outcome?*

An EM interviewer is listening for: *Can this person grow another
human? Can they hold someone accountable for underperformance? Can
they make a hard call that they'll be questioned on later? Will their
team thrive under them, or burn out and quit?*

The same STAR story lands differently depending on the role. The
"streaming migration" story from the senior-IC mock interview
(`behavioral_interviews/04_mock_interviews_and_analyses/`) would land
at M5 — but it'd land *stronger* at M5 if you framed the same
migration as: *how you grew the 3 engineers who owned the
sub-projects, how you handled the data-scientist who pushed back
hardest, how you decided who got the on-call rotation, what you
learned about yourself as a first-time manager of a 6-person team.*

The senior move is to **lead with the people, not the project**. The
project is the substrate. The people are the story.

---

## 2. The 5 categories

Every People Management question you'll get in an interview falls
into one of 5 categories. Internalize the frame. It maps cleanly to
the canonical question bank.

| # | Category | What it's really asking | Sample canonical questions |
|---|---|---|---|
| 1 | **Managing down** | Can you grow, develop, and hold accountable the engineers who report to you? | "Tell me about a time you coached an underperformer." "Tell me about a time you had to deliver hard feedback." "Tell me about a time you delegated something important." |
| 2 | **Managing up** | Can you disagree with your manager, manage your skip-level, and represent your team upward without selling them out? | "Tell me about a time you disagreed with your manager." "How do you keep your skip-level informed without bypassing your manager?" |
| 3 | **Managing sideways** | Can you work with PM, Design, peer EMs, and adjacent teams to ship without being a blocker? | "Tell me about a time you had to influence a peer team." "How do you handle a PM who keeps changing scope?" |
| 4 | **Managing self** | Do you have a coherent management philosophy? Do you learn from your mistakes? Why EM, and what kind of EM are you? | "Why did you choose Engineering Manager as a career path?" "Tell me about a time you made a mistake as a manager." |
| 5 | **Crisis / ambiguity** | When the situation is bad and the data is incomplete, can you make a defensible call? | "Tell me about a time you had to let someone go." "Tell me about a production incident you led." |

The 5 categories map cleanly to the 5 modules of this track:

- Modules 02 + 03 = Managing down (coaching, career, performance)
- Module 04 = Team execution (the operational substrate for #1)
- Module 05 = Managing up + sideways (the soft power)
- Lesson 02 of this module = Managing self (story bank + philosophy)
- Module 04 Lesson 15 (on-call) + Module 03 Lesson 08 (PIPs) = Crisis

When an interviewer asks a question, your first job is to **place it
in the 5-category frame**. That tells you which stories from your
bank to consider, which rubric rows to demonstrate, and which "so
what" beat to land on.

---

## 3. The rubric at Meta M5 / Google L6

Different companies phrase the rubric differently, but they all
measure the same 6 things. Here's the synthesis:

| Rubric row | What they're listening for |
|---|---|
| **People growth** | Did the engineers on your team get better under you? Promotions, scope, skill? |
| **Performance management** | Did you hold underperformers accountable? Top performers retained and grown? |
| **Hiring** | Did you raise the bar of the team over time? |
| **Execution** | Did the team ship? Did unblock dependencies? Handle incidents? |
| **Influence** | Did you work effectively with PM, Design, peer EMs, execs? |
| **Self-awareness** | Do you know what kind of manager you are? What you're bad at? What you're working on? |

Notice what's *not* on the list: technical depth. That's a separate
round (system design / architecture judgment). In the People
Management round, technical depth is table stakes — you need to
*have* it, but you don't get credit for *demonstrating* it. The
credit comes from the 6 rows above.

The mistake senior ICs make: they answer People Management questions
with a system-design-flavored story. "Here's how I designed the new
service." The interviewer is thinking: *but how did you grow the
junior engineer who did most of the work? How did you handle the
senior engineer who pushed back?* The answer is technically correct
and rubric-wise a miss.

The fix: **for every project you describe, name 1-2 specific people
by role, describe what they were like at the start, and describe
what they grew into**. That's the rubric row "people growth" being
demonstrated in passing, which is exactly where senior EMs land it.

---

## 4. The downlevel vector

The most common way senior ICs get downleveled in this round is
**the "I would have done it myself" tell**. Symptoms:

- Stories that end with "I ended up doing it myself" or "I took it
  over and shipped it in 2 weeks."
- Coaching framed as "I told them exactly what to do."
- Delegation framed as "I assigned it and checked in."
- Disagreement framed as "I escalated to my manager."

Each of these is technically true and rubric-wise catastrophic. They
tell the interviewer: *this person hasn't internalized that the job
is to grow other humans, not to be the most productive person on the
team.*

The senior-EM move: every story lands on a beat about the *other
person* — what they learned, how they grew, what they're doing now.
The candidate is the supporting character. The IC is the protagonist.

If you have even one story in your bank that ends with "I did it
myself," rewrite it before the interview. The fix is usually: what
did you do *after* you took it over? Did you grow the next person who
touched the work? Did you write a doc, run a training, change the
process? Find the beat that isn't about you.

---

## 5. A worked example: the same story, 2 framings

Same project — leading the migration of a 6-person data team from
nightly batch to streaming. Same outcome — shipped on time, 0
downstream breakage.

**Senior-IC framing (lands at E5, weak at M5):**

> *"I led the migration of our analytics pipeline from nightly
> batch to sub-minute streaming. The data science team was blocking
> it because their downstream models would break under the new
> schema. I scheduled a 90-minute working session with the 3 data
> scientists whose models were most affected. I came prepared with
> a backward-compatible schema proposal. All 3 signed off within 2
> weeks. The migration shipped on time with 0 downstream breakage."*

This lands 4/4 at the senior-IC bar. At the M5 bar, it's a 2/4 —
the work is correct, but the *people* are invisible. You can't tell
who was on the team, who struggled, who grew.

**EM framing (lands at M5):**

> *"I was managing a 6-person data team through a streaming
> migration. The hardest part wasn't the tech — it was the 2
> engineers on my team who were visibly anxious about the new
> stack. One had been on the team for 7 years and was worried
> his Kafka knowledge was obsolete. The other was a junior who'd
> joined 6 months earlier and was afraid to ask 'dumb' questions
> on the new system.*
>
> *I ran a 1:1 a week with each for the first 6 weeks. With the
> senior engineer, the conversation was about career — he'd been
> a 'Kafka expert' for so long that his identity was tied to it.
> We worked out a path where he owned the legacy decommission
> (his strength) AND led the runbook for the new system (his
> growth area). 6 months later he'd written the internal training
> on the new stack and was presenting it to 3 other teams.*
>
> *With the junior, I paired her with the senior on the first 3
> tickets and explicitly framed the pairing as 'I'm asking you to
> learn from Sam, not to prove yourself.' She shipped her first
> independent ticket in week 5. By the end of the migration she
> was the team's go-to for the new pipeline's observability layer.*
>
> *The migration itself: data-science signoff in 2 weeks, shipped
> on schedule, 0 downstream breakage. The bigger outcome: both
> engineers got promoted within 12 months — the senior to E6, the
> junior to E4 — and neither is interviewing elsewhere."*

Same project, same outcome. The EM framing lands 4/4 at M5 because:

- Specific people named (senior engineer with 7 years of Kafka
  expertise, junior who'd been on the team 6 months)
- Specific growth trajectories (senior → E6, junior → E4, neither
  interviewing elsewhere)
- A management philosophy visible in the actions (1:1 cadence
  matched to need, pairing framed as learning not proving, identity
  work for the senior)
- The "I" is supporting; the engineers are the protagonists

The senior move is the EM framing. Practice it.

---

## Try it

Take the most recent project you led. Write a 90-second answer in
**both framings** — senior-IC and EM. Notice where the EM framing
asks you to name people, where you have to invent (or remember) the
specific human moments, and where the senior-IC version is just
*easier* to tell.

If the EM version is hard to write, that's the signal. It's the
version you need to practice.

---

## Action item

Before Lesson 02, list the 5-7 people you've worked most closely
with in the last 3 years. For each, write 2-3 sentences: who they
were at the start, what they grew into, and what you specifically
did (or didn't do) that contributed. This is the raw material for
your EM story bank.
