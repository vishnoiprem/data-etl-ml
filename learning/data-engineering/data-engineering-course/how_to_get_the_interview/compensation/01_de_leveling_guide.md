# 01 — The Data Engineering Leveling Guide

> **Lesson 1 of 4** · ~45 min

What each level actually signals, how the big companies stack-rank
against each other, and how to make sure you're offered the right
one.

---

## 1. Why leveling matters more than title

A "Senior Data Engineer" at a 50-person startup and a "Senior Data
Engineer" at Meta are not the same role. The first might own the
entire data platform and report to the CTO; the second might be
E4 with 2 reports and a single-quarter scope.

**Level is the unit of currency at big tech.** It determines:

- Your base salary band.
- Your RSU grant size (often by 2-3x between adjacent levels).
- The scope of projects you can be staffed on.
- Whether you're in the leveling committee at all (staff and
  above) or whether your manager does it in a 30-min meeting
  (IC and senior).
- Your promo velocity. One missed promo cycle at E5 → E6 is
  18 months and ~$200k+ in expected equity.

This lesson gives you a single mental model: the **5 signals of
leveling**, the **level stack-rank across 7 companies**, and a
**self-assessment rubric** you can run against your own resume
before the loop ends.

---

## 2. The 5 signals of leveling

Every leveling committee — Meta, Google, Stripe, Netflix — uses
some version of these 5 axes. They are not all equal: **scope of
impact** and **scope of influence** are the two that move you
between levels. The other three are the table stakes.

### 2.1 Scope of impact

The size of the unit your work moves.

| Level | Scope of impact | Example |
|---|---|---|
| IC2 / E3 / L3 | Owns a feature or task | "Migrated one DAG from cron to Airflow" |
| Senior (IC3 / E4 / L4) | Owns a project across a team | "Led migration of 12 Airflow DAGs to v2 over 3 months" |
| Staff (IC4 / E5 / L5) | Owns a multi-quarter initiative across teams | "Drove the company-wide adoption of dbt over 9 months; 5 teams migrated" |
| Senior Staff (IC5 / E6 / L6) | Owns a multi-year platform across an org | "Set the data platform strategy for 200+ engineers over 3 years; net $4M/yr infra savings" |
| Principal (IC6 / E7 / L7) | Owns a multi-year platform across the company | "Authored the company data mesh strategy; adopted by 1,200+ engineers across 4 BUs" |

### 2.2 Scope of influence

Whose decisions you can move. This is the **most underrated** of
the 5 signals. A staff engineer who can't convince 3 other teams
to follow their design is, in practice, a senior engineer with a
staff title.

| Level | Influence |
|---|---|
| Senior | Drives consensus within their own team. Relies on seniority to be heard. |
| Staff | Drives consensus across 2-4 teams. Sets direction without formal authority. Sets up RFCs, design reviews, and decision records. |
| Senior Staff | Sets direction across an org. Influences VP-level decisions through written artifacts and trusted relationships. |
| Principal | Sets direction across the company. Speaks the language of business strategy and engineering tradeoffs interchangeably. |

### 2.3 Technical depth

The depth of your technical judgment. This is the table-stakes
axis — you don't get to staff without it. It's how *deep* you can
go, not how *broad*.

| Level | Depth signal |
|---|---|
| Senior | Designs a system end-to-end. Makes the right tradeoff 80% of the time without help. |
| Staff | Sees the second-order consequences of a design. Calls out failure modes the senior didn't. |
| Senior Staff | Invents new patterns. Has 2-3 "go-to" areas where they're the company expert. |
| Principal | Defines what "good" looks like in a domain. Other principals cite their work. |

### 2.4 Leadership signals

How visibly you multiply the team. This is not "people management."
It's whether other engineers get better because of you.

| Level | Leadership signal |
|---|---|
| Senior | Mentors 1-2 juniors. Reviews PRs. Owns onboarding. |
| Staff | Mentors across teams. Writes the design doc template the org uses. Runs the architecture review. |
| Senior Staff | Sets the technical bar. Hires 5+ senior+ engineers. Sets the promo criteria. |
| Principal | Sets the technical direction at the company level. Visible to VPs and CTOs. |

### 2.5 Business judgment

How well you tie technical decisions to business outcomes. This
is the axis that **most engineers under-invest in**, and the one
that gets you promoted from senior to staff.

| Level | Business signal |
|---|---|
| Senior | Translates PM requirements into a design. Knows the team's quarterly OKRs. |
| Staff | Proposes a project because it moves a business metric, not because it's interesting. Writes a doc that includes ROI, risk, and a kill criterion. |
| Senior Staff | Sets the team's roadmap in partnership with the PM lead. Pushes back on VPs when the metric doesn't justify the project. |
| Principal | Defines the data strategy in business terms. CFO-level fluency in infra cost / revenue tradeoffs. |

---

## 3. The 7-company stack-rank

This is the table that every senior DE candidate should have in
their head before they go on loop. It is approximate (public
levels.fyi data, recruiter conversations, internal networks) and
it will drift, but the *shape* is durable.

| Title | Meta | Google | Stripe | Netflix | Airbnb | Databricks | Snowflake |
|---|---|---|---|---|---|---|---|
| **Senior DE** | E4 | L4 | IC2 (sometimes IC1 strong) | D (Senior) | L4 (Senior) | L4 | IC2 |
| **Staff DE** | E5 | L5 | IC3 | STR (Senior Tech) | L5 (Staff) | L5 | IC3 |
| **Senior Staff DE** | E6 | L6 | IC4 | Pr (Principal) | L6 (Senior Staff) | L6 | IC4 |
| **Principal DE** | E7 | L7 | IC5 (rare, IC4 → Mgr) | VP / Distinguished | L7 (Principal) | L7 | IC5 (very rare) |

**Notes:**

- **Stripe IC1–IC2** is roughly equivalent to Meta E3–E4. Stripe
  bands run tighter than Meta's at the top end.
- **Netflix "STR"** is "Senior Tech" — the level between senior
  engineer and principal. The "D" band is senior; the "Pr" band is
  principal.
- **Databricks L4** is mid-level; their L5 is closer to Meta E5
  than to Meta E4. Their leveling skews a notch high.
- **Snowflake IC2** is closer to Meta E4 than to Meta E3 in
  practice. The bands are also tighter; IC3 is the "real" staff.

**The single most useful thing in this table:** if you interview
at Meta as an E5 loop and the recruiter comes back with an E4
offer, you have a strong case to push back — your "interview level"
was the same as Google's L5, Stripe's IC3, and Databricks' L5. The
company is down-leveling you, not the market.

---

## 4. The 5 things that move you from one level to the next

If you're targeting staff, this is the list. The promo committee
is looking for all 5. Most candidates have 2 of the 5. The
difference between senior and staff is **evidence on all 5 axes
in a 12-month window**.

1. **A project whose scope was clearly beyond your team.** Not
   "helped 3 teams." Owned the design, the execution, and the
   rollout. Multi-quarter. Cross-team.
2. **A written artifact that changed how others work.** A design
   doc, an RFC, a runbook, a public talk, a Medium post that
   gets cited. The artifact should still be in use 6 months later.
3. **A leadership signal visible to people who don't work with you
   daily.** Mentoring, interviewing, hiring loops, conference
   talks, open-source maintainership. The signal must be
   *visible* — not "I mentored informally."
4. **A business outcome tied to a number.** $ saved, latency
   reduced, revenue enabled, hours freed. Not "improved." *Number*.
5. **A second-order technical judgment call.** You saw a failure
   mode the staff reviewer didn't. You pushed back on a design and
   were right. You deprecated a system before it broke.

If you have 4 of these 5 in the last 18 months, you're a staff
candidate. If you have 2 of these 5, you're a senior candidate
with staff potential — interview at senior, target staff in 12-18
months.

---

## 5. Self-assessment rubric: what evidence to bring

A leveling committee doesn't read your resume. They read 4-6
**calibration docs** written by your interviewers and hiring
manager. Each doc has a one-paragraph "evidence" section. This is
what they need to see.

| Level | Evidence you'd cite |
|---|---|
| **E4 / L4 / Senior** | 2-3 projects you owned end-to-end. Quantified outcomes. Mentorship of 1+ junior. |
| **E5 / L5 / Staff** | 1 multi-quarter cross-team project. 1 written artifact (design doc, RFC) that 2+ teams adopted. Quantified business outcome. Visibility outside your team. |
| **E6 / L6 / Sr Staff** | 1 multi-year platform. Roadmap-setting evidence. Multiple teams adopted your designs. Spoke at conferences or wrote public-facing artifacts. Promoted 1-2 engineers. |
| **E7 / L7 / Principal** | Multi-year company-wide platform. Company-level strategy doc. Visible to VPs and CTOs. Hired and developed senior staff. |

**The trick for staff candidates:** bring *specific* names of
artifacts. "I wrote the dbt migration RFC" beats "I drove
adoption." Bring the link. Bring the date. Bring the names of the
2 other teams that adopted it.

---

## 6. The down-leveling risk

**Down-leveling** is when a company offers you a lower level than
the loop was calibrated for. It happens to ~15% of senior
candidates and ~30% of staff candidates. It is almost always a
**comp decision disguised as a leveling decision**.

### 6.1 How it happens

The loop was calibrated for L5. You performed at L5. The hiring
committee came back with L4. The recruiter says: *"We think
you're a great fit, but the team's budget is for L4, and we'd
love to make you an offer at that level."*

This is **not** a leveling decision. This is a comp decision. The
company has decided that the L5 band is too expensive and is
trying to hire you at the L4 band. The fix: **call it out**.

### 6.2 The pushback script

> *"Thanks for the feedback. I want to make sure I understand:
> the loop was calibrated for [L5 / E5 / IC3], and based on the
> interview performance, the committee came back at [L4 / E4 /
> IC2]? I'd like to understand the specific signal that put me
> below the bar. I've prepared for the [L5] loop, and the
> feedback I got in the loop was that I performed at the [L5]
> bar on [design / coding / cross-functional]. Can we revisit
> the committee, or is this the final level?"*

Three things to know:

- The committee can be revisited. This is normal. Most companies
  have a "leveling appeal" path. Ask.
- The "specific signal" question forces them to either cite a
  real reason (good — you learn) or admit there's no specific
  signal (good — you push back).
- The final sentence — *"or is this the final level?"* — signals
  you're willing to walk. They may not admit this on the call, but
  recruiters escalate to the hiring manager when they sense the
  candidate is serious.

### 6.3 When to accept the down-level

Sometimes the down-level is real. The candidate interviewed for
L5 but only demonstrated L4. Accept the L4 if:

- The L4 base + RSU + signing is still above your current TC.
- The promo path to L5 is documented (in writing, not verbal).
- You have a competing L5 offer (or are willing to interview for
  one).

If all three are true, the L4 can be a 12-month stepping stone.
If the third is false, walk.

---

## 7. The 30-minute self-assessment exercise

Before you go on a staff loop, do this:

1. **Pull your resume.** Put it next to the table in Section 3.
2. **For each of the 5 signals in Section 2,** write down 1-2
   pieces of evidence. If you can't, that's the gap.
3. **Run the Section 4 list.** How many of the 5 do you have in
   the last 18 months?
4. **Pick your target level.** Be honest. Senior candidates with
   2/5 staff signals should interview at senior and target staff
   in 12-18 months. Interviewing at staff prematurely is a
   3-month time sink.
5. **For each target company in Section 3,** write down the
   *equivalent* level (Meta E5 = Google L5 = Stripe IC3 = ...).
   Use this when recruiters try to down-level you.

If your target is staff and you have 4/5 signals: interview at
staff. If you have 2/5: interview at senior and target staff
internally.

---

## 8. Common leveling mistakes

A few things to watch for.

- **Title inflation from your current company.** A "Staff
  Engineer" at a 50-person startup is rarely a Meta E6. Recruiters
  know this. The level, not the title, is what they evaluate on.
- **"Senior" with no cross-team evidence.** Strong ICs in a
  single team for 5+ years are senior, not staff. Staff requires
  evidence outside your team.
- **Staff without a written artifact.** If you can't point to a
  design doc, RFC, or runbook that's still in use 6 months
  later, the committee will read you as senior. Write more.
- **"I led the migration"** without a number. The number is what
  moves the level. No number = senior, regardless of the title.
- **Confusing scope with seniority.** Running a 6-person team
  doesn't make you staff. It makes you a senior with reports.
  The signals above are about *technical* scope, not headcount.

---

## Try it

Before Lesson 02, do this:

1. Pick the **target level** you'd interview at. Use the table in
   Section 3 to map it to the 7 companies.
2. For your target level, write down **3 specific pieces of
   evidence** from the last 18 months. Use the Section 2 rubric.
3. Run the **Section 4 checklist.** How many of the 5 signals do
   you have?
4. Write the **target level + 3 pieces of evidence** in 2
   sentences. This is the "leveling pitch" you'll use in the
   recruiter screen and the wrap-up call.

If you can do (1)–(3) honestly, you know your level. If you can't,
you don't — and that's the gap to close before the loop, not
during the offer call.

---

*Author: Prem Vishnoi <pvishnoi@avilx.com>*