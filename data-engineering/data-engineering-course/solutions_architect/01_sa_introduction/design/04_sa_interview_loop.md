# 04 — The SA Interview Loop

> **Lesson 4 of 8 — SA Interview Introduction** · ~20 min

The SA interview loop is structurally different from a
software-engineering loop. Most candidates who come from pure
engineering roles under-prepare for the customer-interaction
rounds and over-prepare for the technical rounds. This lesson
gives you the 5-6 round structure, what each round tests, and
the 2-4 week timeline.

---

## 1. The structure (5-6 rounds, 2-4 weeks)

The SA loop at AWS, GCP, Azure, Salesforce, and Snowflake
all share the same skeleton. The names differ, the bar
differs, but the *shape* is consistent.

| Round | Format | Duration | What it tests | Module in this track |
|---|---|---|---|---|
| **Recruiter screen** | Phone, behavioral | 30-45 min | Background, motivation, comp alignment | — |
| **Hiring manager** | Video, mixed | 60 min | Story depth, customer fit, deal examples | Module 05 |
| **Customer interaction / Discovery** | Live roleplay | 45-60 min | Discovery skill, listening, qualifying | Module 02 |
| **Architecture / Whiteboard** | Live roleplay | 60 min | Defensible design under pressure | Module 03 + `../system_design/` |
| **Behavioral (deep)** | Video, STAR | 60 min | Customer-facing stories, conflict, influence | Module 05 |
| **Bar-raiser (AWS) / Cross-functional (others)** | Video, mixed | 60 min | "Would you be a good peer?" — character | Module 06 |
| **(Sometimes) Live demo / POC** | Live roleplay | 60 min | Demo delivery, dealing with breakage | Module 02 |

The total loop is 5-6 rounds + a recruiter screen. Some
companies combine rounds (Salesforce often combines the
hiring-manager and behavioral into one longer round). AWS
keeps them strictly separate, with a dedicated "bar-raiser"
round run by an SA from a different org.

The total timeline from "application submitted" to "offer
extended" is typically 2-4 weeks. AWS can move faster (often
1-2 weeks) for senior candidates; Salesforce and Snowflake
are typically 3-4 weeks.

---

## 2. What each round tests

### Recruiter screen (30-45 min)

What the recruiter is actually looking for:

- **Comp alignment.** They're screening for "can we afford
  this candidate." If your current comp is $400k and you're
  asking $700k, the recruiter wants to know your reasoning.
  Have a number in mind before the call.
- **Motivation.** Why SA? Why this company? If your answer is
  "the comp is better," the recruiter will note that and
  the hiring manager will probe it.
- **Background fit.** The recruiter is looking for the 3-5
  keywords that match the JD (e.g., "data and analytics,"
  "AWS," "customer-facing"). If your resume doesn't have
  those, the call will be short.

What to prepare: 60-second "why SA" pitch, comp range, and
3 quick stories. See Module 01 Lesson 05 for the
"how to get the SA job" content.

### Hiring manager (60 min)

What they're looking for:

- **Customer-facing signal.** Most of the questions will be
  flavored — "tell me about a customer you worked with," "tell
  me about a deal you helped close," "tell me about a time you
  lost a customer." Pure engineering stories get downleveled.
- **Bar at the right level.** The HM is the first person who
  can actually calibrate "is this candidate an SA I or SA II?"
- **Culture fit.** Most HM interviews are 30% technical and 70%
  cultural. They're deciding "could I work with this person
  every week?"

What to prepare: 3-5 customer-flavored STAR stories, a clear
"why SA" pitch, and 2-3 "why us" talking points specific to
the company.

### Customer interaction / Discovery (45-60 min)

The round most candidates under-prepare for. The format
varies:

- **AWS:** "Customer interaction" round, 45 minutes, a
  bar-raiser SA plays a customer. You run a discovery call.
- **GCP:** "Discovery" round, 45 minutes, similar setup.
- **Salesforce:** "Discovery" round, 45 minutes, sometimes
  combined with objection-handling.
- **Snowflake / Databricks / Confluent:** "Customer scenario"
  round, 60 minutes, often discovery + demo + objection in
  one round.

What they test:

- **Can you listen?** 60% of the round is *listening* to the
  customer, not pitching.
- **Can you qualify?** Did you identify the decision-maker,
  the decision-process, the timeline, the budget, the
  technical decision criteria?
- **Can you adapt?** The customer will say something that
  changes the deal ("actually, our CTO is reviewing this
  with a different vendor"). Can you adjust?
- **Can you summarize?** A great discovery call ends with
  you saying "let me make sure I heard you correctly" and
  summarizing the customer's pain in 3 bullets.

What to prepare: Module 02, Lessons 02, 05, 06.

### Architecture / Whiteboard (60 min)

The round candidates over-prepare for, in the wrong way.
Most candidates spend 30+ hours on system design and 0
hours on *defending their design against a skeptical
customer*.

The format: 60 minutes, you design a system on a whiteboard
(or Excalidraw) for a scenario the interviewer gives you.
The interviewer plays a CTO or principal engineer. They
will challenge every choice.

What they test:

- **Can you design?** (Yes, this is the system-design bar.)
- **Can you defend?** Every choice needs a rationale, and
  you need to know the alternative you considered and
  rejected.
- **Can you listen and adapt?** The customer will say "we
  need to add X constraint" mid-design. Can you absorb it
  without losing the thread?
- **Can you quantify tradeoffs?** Latency, cost, ops
  burden, scalability. Numbers, not adjectives.

What to prepare: Module 03 (lessons 03, 04, 05, 06, 07) +
`../system_design/`.

### Behavioral deep (60 min)

Pure STAR. 4-5 questions, each 5-7 minutes. The HM and
this round often share stories, but this round goes deeper.
What they test:

- **Customer-facing stories.** The single biggest
  down-leveling signal is internal-engineering stories.
  Every story needs a *customer* or *external stakeholder*
  as the protagonist.
- **Conflict and influence.** "Tell me about a time you
  disagreed with a customer." "Tell me about a time you
  lost a deal." The stories that show *grace under
  friction* are the ones that pass.
- **Self-awareness.** "What's your biggest weakness as an
  SA?" This is asked. A 2.5/4 answer is "I sometimes
  over-prepare." A 4/4 answer is "I sometimes over-rotate
  on the technical solution and under-rotate on the
  customer's actual business problem; here's the change I
  made."

What to prepare: Module 05, all 11 lessons.

### Bar-raiser (AWS) / Cross-functional (60 min)

The round most candidates fail because they don't know
it's the round that matters. Run by an SA from a *different
org* (at AWS) or a senior PM/architect (at other
companies). The interviewer is not evaluating "are you
smart" — they're evaluating "would you be a good peer."

What they test:

- **Would this person make the team better?** Not "is this
  person competent" — the prior rounds have established
  that. "Is this person a *force multiplier* on the team?"
- **Customer-trust signals.** Would you put this person in
  front of your most important customer?
- **Listening and curiosity.** The bar-raiser round at AWS
  is *not* a hostile interview. It's a conversation. The
  candidate who treats it as one passes.

What to prepare: Module 06, especially Lessons 06_01
(How to Pause), 06_03 (Check in with interviewers), and
06_04 (Acing phone interviews). The bar-raiser round is
often the candidate's most natural conversation; the prep
is to not over-rehearse it.

### (Sometimes) Live demo / POC (60 min)

Less common, but Snowflake and Databricks use it. You're
given a scenario and you deliver a 15-minute live demo of
how the product would solve the customer's problem. The
demo will break. How you handle the breakage is the test.

What to prepare: Module 02, Lessons 03, 08, 10.

---

## 3. The week-by-week timeline

A typical AWS SA II loop for a senior candidate (8+ years
experience):

| Day | Event |
|---|---|
| Day 0 | Application submitted / referral sent |
| Day 1-3 | Recruiter screen |
| Day 4-5 | Hiring manager interview |
| Day 6-10 | Customer interaction round |
| Day 10-14 | Architecture / whiteboard round |
| Day 14-18 | Behavioral deep + bar-raiser (often same day) |
| Day 18-21 | Debrief + offer |

A "fast" loop is 1.5 weeks. A "slow" loop (typically because
of scheduling) is 3-4 weeks. After 4 weeks, assume the
process has stalled; follow up with the recruiter weekly.

For Salesforce, Snowflake, Databricks, Confluent: expect
2-4 weeks, with slower scheduling than AWS.

---

## 4. The 3 differences from a software-engineering loop

Three things will feel different if you're coming from a
software-engineering interview background:

1. **The customer-interaction round is core, not "soft."** In
   a SWE loop, the behavioral round is one of 4-5 rounds, and
   it doesn't gate the rest. In the SA loop, the
   customer-interaction round is *the* round, and a bad
   customer-interaction result downlevels you even if your
   technical rounds are perfect.
2. **"Sell the candidate on the role" is a real signal.** AEs
   in some companies get to interview SA candidates and
   veto them. The "would this person be on my deal team" is
   a real question. Be ready to be yourself — the AEs are
   hiring a peer, not evaluating a script.
3. **The debrief is multi-vote.** Most SA loops end with a
   hiring committee that includes AEs, peer SAs, and the
   hiring manager. A single "no hire" from a non-technical
   interviewer can tank a strong technical candidate.
   *Every round matters.*

---

## 5. The rubric, translated

A typical SA loop uses a rubric like this:

| Signal | What it means |
|---|---|
| **Customer focus** | Did the candidate center the customer in every answer? |
| **Technical depth** | Did the architecture hold up under pressure? |
| **Listening** | Did the candidate ask good follow-up questions? |
| **Influence** | Did the customer-interaction round show the candidate moving the customer? |
| **Story depth** | Were the STAR stories specific, customer-flavored, and quantified? |
| **Bar-raiser signals** | Would I want this person on my deal team? |

Notice: **"customer focus" and "listening" are weighted
higher than "technical depth."** This is the rubric most
senior engineering candidates underweight. A candidate who
nails the architecture round and bombs the discovery round
will get downleveled. A candidate who nails the discovery
round and stumbles on the architecture might still pass.

---

## Try it

For your target company, write down the 5-6 round structure
as you understand it. If you don't know, look at 3-5
recent interview reports on Glassdoor or LeetCode. Identify:

1. **The round you're most worried about.** This is your
   highest-leverage prep target.
2. **The round you're most confident about.** This is your
   *secondary* prep target — don't over-prepare your
   strength.
3. **The round you have no read on.** (Often the
   customer-interaction round for engineering candidates.)
   This is the gap you need to close first; Module 02 is
   the content.

Build your 4-week prep plan around those 3 identifications.
