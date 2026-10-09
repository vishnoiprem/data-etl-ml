# Solutions Architect (SA) Interview Prep

> **6 modules · 47 lessons · ~62 videos · ~30 hours of focused practice**
>
> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi) · <prem.vishnoi@example.com>
>
> **Companion articles:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

A practical guide to the part of the technical interview loop that
candidates who come from pure engineering roles underestimate the
most: **the Solutions Architect interview**. If you're interviewing
at AWS, GCP, Azure, Salesforce, Snowflake, Databricks, Confluent,
HashiCorp, or any vendor with a "pre-sales" or "post-sales" SA
track, this is the track for you.

The SA loop is structurally different from a software engineering
loop. The bar is not "can you design a system on a whiteboard." The
bar is **"can you discover what the customer actually needs, design
a defensible solution in real time, defend it against objections,
and do it all while building trust with a room full of skeptical
buyers."** That's a *people* skill layered on top of technical
depth, and most engineers have no training in it.

This track fixes that.

---

## What's in this track

**Pattern-based.** Every lesson is built around patterns that
repeat across companies: the discovery call, the live demo, the
objection-handling moment, the whiteboarding session, the "tell me
about a time you lost a deal" question. Once you see the pattern,
you stop being surprised by the round.

**Cross-linked.** The **System Design** track at
`../system_design/` (71 lessons) is the technical foundation. We
don't re-build it — Module 04 points you straight there. This
track is the *customer-facing* and *behavioral* layer on top of
it.

**Calibrated for senior+.** The audience is engineers and
architects interviewing for **SA I / SA II / Senior SA / Principal
SA** at hyperscalers and large vendors. The framing is "be seen as
a customer-trusted technical advisor," not "be seen as a
solutions engineer who can deploy a reference architecture."

---

## The 6 modules

| # | Module | Lessons | What you'll get out of it |
|---|---|---|---|
| [01](01_sa_introduction/) | **SA Interview Introduction** | 8 | What an SA actually is (3 flavors), the interview loop, the AWS SA path, comp, misconceptions. |
| [02](02_customer_interaction/) | **Customer Interaction Interviews** | 12 | Discovery, demo, objection handling, whiteboarding, mock transcripts. |
| [03](03_technical_questions/) | **Technical Questions for SAs** | 7 | API design, DB schema, architecture diagrams, tradeoff frameworks, the 30-second decision tree. |
| [04](04_system_design_crossref/) | **System Design Interviews (cross-link)** | 0 | Direct pointer to `../system_design/` — already built. |
| [05](05_behavioral_for_sa/) | **Behavioral Interviews for SAs** | 11 | The 7 most-asked behavioral questions for SAs, each with 2-3 worked answers. |
| [06](06_tips_and_frameworks/) | **Interview Tips & Frameworks** | 9 | The 4 C's, the PREP framework, pausing, whiteboarding, the 24-hour checklist. |

**Total: 47 lessons.**

---

## How to use this track

**Week 1 — On-ramp (4-6 hours).** Read Module 01 in one sitting.
You should know what an SA is, the 3 flavors, the interview loop,
and the comp ranges by Sunday. If you don't want any of the
flavors after Lesson 02, you've saved yourself 25 hours of prep.

**Week 2 — Customer interaction (8-10 hours).** Module 02 is the
core of the SA interview. Do the discovery mock (Lesson 06) and
the demo mock (Lesson 08) *out loud*, with a friend. The
whiteboard demo (Lesson 10) is the highest-leverage lesson in the
entire track.

**Week 3 — Technical + system design (10-12 hours).** Module 03
in one sitting, then 2-3 system design problems from
`../system_design/`. The "30-second architecture decision" tree
(Lesson 03_07) is the framework; the system design track is the
catalog.

**Week 4 — Behavioral + frameworks (6-8 hours).** Module 05 with
the story-bank worksheet in `exercise.md`. Then Module 06 — the
4 C's, the PREP framework, the 24-hour checklist. Do a final mock
with a friend.

By week 4, you should be able to (a) run a 30-minute discovery
call that surfaces a real customer pain, (b) whiteboard a
defensible architecture under pressure, (c) handle the 6 most
common objections without flinching, and (d) tell 7 STAR stories
with the SA-flavored signals (customer outcomes, cross-team
influence, deal context).

---

## Layout

```
solutions_architect/
├── README.md                       # ← you are here
├── 01_sa_introduction/
│   ├── module_overview.md
│   └── design/                    (8 lessons)
├── 02_customer_interaction/
│   ├── module_overview.md
│   └── design/                    (12 lessons)
├── 03_technical_questions/
│   ├── module_overview.md
│   └── design/                    (7 lessons)
├── 04_system_design_crossref/
│   └── module_overview.md         # cross-link only
├── 05_behavioral_for_sa/
│   ├── module_overview.md
│   └── design/                    (11 lessons)
├── 06_tips_and_frameworks/
│   ├── module_overview.md
│   └── design/                    (9 lessons)
└── exercise.md                     # one cross-module capstone
```

---

## A note on the customer-facing format

There is intentionally **no `app.py`, no `docker-compose.yml`,
no `pytest`** in this track. SA interviews are a *craft* — like
sales, like consulting, like teaching. You can't unit test whether
your discovery question lands. You can only practice, get
feedback, iterate.

So: **read the lesson. Do the "Try it" out loud. Get a friend to
play the customer. Repeat.** That's the entire workflow.

---

## Where to go next

- For system design depth: see `data-engineering-course/system_design/`.
- For data engineering behavioral questions (DE-flavored STAR): see
  `data-engineering-course/behavioral_interviews/`.
- For the EM-flavored behavioral questions (if you're targeting an
  SA-with-direct-reports role): see `data-engineering-course/em_introduction/`.
- Author articles: <https://medium.com/@premvishnoi>
