# 16 — Hiring, Interviewing, and Closing Candidates

> **Lesson 16 of 21 — Managing Team Execution** · ~25 min

Rubric-based interviews, debriefs, closing strategy, and the
hiring loop end-to-end. Hiring is the EM's highest-leverage
long-term move — a strong hire compounds for years, a weak
hire compounds for years in the other direction. Most senior
ICs have been interviewed, but the EM's job is different:
the EM designs the loop, runs the debriefs, and closes the
candidate.

---

## 1. The hiring loop end-to-end

A typical engineering hiring loop has 5-7 stages. The EM's
role varies by stage, but the load-bearing ones are the
debrief and the close.

| Stage | What happens | EM's role |
|---|---|---|
| **Recruiter screen** | 30-min phone call, recruiter assesses basic qualifications | Define the role with the recruiter, review feedback |
| **Hiring manager screen** | 30-60 min call, EM assesses mutual fit | Run the call, decide whether to advance |
| **Technical phone screen** | 60 min, coding or system design, conducted by an engineer | Define the rubric, review feedback |
| **On-site (or virtual on-site)** | 4-6 hours, multiple interviewers across multiple rubrics | Define the rubric, run the debrief |
| **Debrief** | 30-60 min, all interviewers align on a hire/no-hire | Run the debrief, make the final call |
| **Reference checks** | 3-5 calls with former colleagues and managers | Run the references, look for red flags |
| **Close** | Offer, negotiation, acceptance | Make the offer, negotiate, close |

The mistake new EMs make: skipping the hiring manager
screen because "the recruiter screen was enough." The
senior move is to **always do a hiring manager screen** —
it's the only stage where the EM can assess mutual fit
(does this person want the role? does this role want this
person?) before the candidate invests in the loop.

---

## 2. The rubric-based interview

The most important thing the EM does for the hiring loop
is to **define the rubric**. The rubric is the list of
specific signals the interviewers should look for. Without
a rubric, every interviewer evaluates on their own curve,
and the debrief becomes 5 different opinions about
"senior" with no shared definition.

A useful rubric structure for a senior IC role:

```
RUBRIC — Senior Data Engineer — Data Platform Team

CORE SIGNALS (every interviewer assesses):

1. Technical depth
   - Junior: Can solve a problem with clear requirements
     and known techniques.
   - Senior: Can solve a problem with ambiguous requirements
     and unknown techniques. Reason about tradeoffs.
   - Staff: Can solve a problem that involves multiple
     systems, with constraints that conflict.
   - Signal: [Specific question, what good looks like,
     what "above bar" looks like]

2. System design
   - Junior: Designs a single service for a single use case.
   - Senior: Designs a service for multiple use cases, with
     consideration of edge cases.
   - Staff: Designs a system of services for a complex
     domain, with clear API boundaries.
   - Signal: [Specific question, what good looks like,
     what "above bar" looks like]

3. Cross-functional collaboration
   - Junior: Communicates clearly within the team.
   - Senior: Communicates across teams, navigates
     disagreement.
   - Staff: Influences cross-functionally without authority.
   - Signal: [Specific question, what good looks like,
     what "above bar" looks like]

4. Execution under ambiguity
   - Junior: Asks clarifying questions when stuck.
   - Senior: Identifies the right questions to ask, makes
     progress in the face of unclear requirements.
   - Staff: Defines the problem in addition to solving it.
   - Signal: [Specific question, what good looks like,
     what "above bar" looks like]

ROLE-SPECIFIC SIGNALS (only the EM assesses):

5. Mutual fit
   - Why this role? Why this team? Why this company?
   - Signal: Authentic, specific answer; not generic.

6. Career trajectory
   - Where do they want to be in 2-3 years?
   - Signal: Aligned with what the role can offer.
```

The mistake new EMs make: writing a rubric that's a list
of skills. The rubric is **about behaviors at level**,
not skills. "Knows Kafka" is a skill. "Reasoned about
Kafka tradeoffs in a design problem with conflicting
constraints" is a behavior.

---

## 3. The debrief

The debrief is the 30-60 minute meeting where all
interviewers align on a hire / no-hire. The EM runs the
debrief. The structure:

1. **Open with the EM's overall impression.** "My read
   from the hiring manager screen is [X]."
2. **Each interviewer shares their signal.** Not their
   opinion — the specific signal they observed. "In the
   coding round, the candidate got the brute-force
   solution but didn't recognize the opportunity for the
   heap-based optimization until I prompted."
3. **Discuss against the rubric.** "Based on the signals,
   where does this candidate land on the Technical Depth
   row? Junior, Senior, or Staff?"
4. **Make the decision.** Strong hire / hire / no hire /
   strong no hire. The senior move is to **make the
   decision explicitly**, not "let's see how the other
   interviews go."

The mistake new EMs make: not making a decision in the
debrief. The decision gets pushed to "let's discuss
async" or "I'll think about it" — and the candidate
ghosts the next round because they can sense the lack of
conviction.

The senior move: **make the decision in the room**,
document it in writing, and communicate it to the
recruiter within 24 hours.

---

## 4. The close

The close is the most underrated part of the loop. The
EM's role is to make the offer, negotiate, and close. The
3 things the EM owns:

1. **The offer.** The EM drafts the offer (with the
   recruiter and compensation team), including base,
   bonus, equity, level, and start date. The senior
   move is to **make the offer strong enough to be
   accepted** — under-offering is the move that loses
   candidates.
2. **The negotiation.** Most senior candidates will
   negotiate. The EM should be prepared for the 2-3
   common asks: more base, more equity, higher level.
   The senior move is to **negotiate with conviction**:
   know the range, know the levers, know what's
   flexible and what's not.
3. **The close.** Once the candidate accepts, the EM
   owns the onboarding prep — the first-90-days
   plan, the laptop, the welcome. The senior move is
   to **make the candidate feel wanted** in the
   48 hours between acceptance and start date. A
   candidate who feels wanted in those 48 hours is
   a candidate who doesn't reneg.

---

## 5. The 2-3 signals it's a no-hire

Even with a good rubric, you'll see no-hires that didn't
look like no-hires in the screen. The 2-3 signals:

1. **The interviewer split.** When 3 interviewers say
   "hire" and 2 say "no hire," the senior move is to
   **default to no hire**. The split means the
   candidate has material weaknesses that some
   interviewers saw and others didn't; the burden of
   proof is on the hire side.
2. **The "lots of green, no gold."** When every
   interviewer says "good, no concerns," but no
   interviewer says "this is exceptional," the
   candidate is solid Meets, not Exceeds. For a role
   that needs Exceeds, that's a no-hire.
3. **The behavior under pressure.** When the candidate
   gets defensive, blames others, or can't admit
   they don't know something, the senior move is to
   no-hire. The behavior under interview pressure
   predicts the behavior under production pressure.

The mistake new EMs make: hiring the candidate
because "they were nice" or "they seemed smart."
The senior move is to hire the candidate because
**they demonstrated the specific signals in the
rubric, consistently across multiple interviewers**.

---

## 6. A worked example: the debrief for a senior candidate

Candidate X has just finished the on-site. 5 interviewers,
all senior data engineers or EMs. Sam is running the
debrief.

> **Sam:** "My read from the hiring manager screen: the
> candidate is strong technically, specifically motivated
> by the streaming migration we're doing, and asked 3
> really sharp questions about the team's architecture.
> Advancing to the loop was the right call. Let's go
> around the room — each of you, 2 minutes, what signal
> did you see?"
>
> **Interviewer 1 (coding):** "Got the brute-force
> solution in 20 minutes, identified the heap
> optimization when I prompted, and explained the
> tradeoff clearly. Solid Senior signal on Technical
> Depth."
>
> **Interviewer 2 (system design):** "Designed the
> streaming pipeline end-to-end. Identified the
> backpressure problem, designed the dead-letter queue
> handling, and reasoned about the schema evolution
> approach. Above bar on System Design."
>
> **Interviewer 3 (cross-functional):** "We role-played
> a disagreement with a PM. The candidate listened
> first, asked clarifying questions, and proposed a
> compromise that the PM accepted. Solid Senior on
> cross-functional collaboration."
>
> **Interviewer 4 (execution under ambiguity):** "The
> problem had unclear requirements. The candidate
> identified 3 specific clarifying questions, made
> progress without the answers, and revised their
> approach when the requirements became clear. Above
> bar."
>
> **Interviewer 5 (Priya, technical peer):** "I had them
> debug a production-style issue. They identified the
> root cause in 15 minutes (it was a schema-version
> mismatch — yes, the same one from our incident), and
> explained why the silent-drop behavior was the
> systemic problem. They asked about the action items
> from the postmortem unprompted."
>
> **Sam:** "Based on the signals, this candidate is
> above-bar Senior across all 4 core signals. The
> cross-functional and execution-ambiguity signals were
> stronger than I'd expect at the Senior level. I'm
> going to call this a strong hire at the Senior level.
> Anyone disagree?"
>
> *[silence]*
>
> **Sam:** "Okay. I'll send the decision to the
> recruiter today, make the offer tomorrow, and aim to
> close by end of week."

**What makes this land:** Each interviewer cites a
specific signal, not an opinion. The EM maps the signals
to the rubric rows explicitly. The decision is made in
the room. The EM commits to the next steps.

---

## 7. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- Behavioral #42: *"Tell me about a time when you had to
  hire someone."*
- Behavioral #68: *"Tell me about a time when you had to
  make a hiring decision."*
- Behavioral #99: *"Tell me about a time you interviewed
  someone."*
- Behavioral #125: *"Tell me about a time when you had to
  close a candidate."*

---

## Try it

If you've been an interviewer in a real loop, write the
debrief for your last interview using the structure above.
Notice which sections feel easy (the signals you observed)
and which feel hard (mapping to the rubric, making the
decision). The hard sections are your interviewer-training
priorities.

If you haven't been an interviewer, write a 90-second
answer for "Tell me about a time you had to evaluate
someone" using any context — a hire you made, a peer you
worked with, a mentee. The skill is the same: name
specific signals, map to a rubric, make the call.

---

## Action item

This week, write a rubric for the next role you're hiring
for. Use the structure above. If you don't have an open
role, write the rubric for a hypothetical role. The
exercise of writing the rubric surfaces what "above bar"
means for your team — and that definition is what every
other hire will be measured against.