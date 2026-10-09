# 05 — How to Get a Solutions Architect Job

> **Lesson 5 of 8 — SA Interview Introduction** · ~15 min

The on-ramps to an SA role. The 4 most common paths: the AWS
SA Associate program, the lateral move from engineering, the
move from a smaller vendor, and the move from sales
engineering. The trade-offs of each, the prep time, and the
first 30/60/90 days once you're in.

---

## 1. The 4 on-ramps

| Path | Time to first SA role | Best for | Trade-off |
|---|---|---|---|
| **AWS SA Associate** | 12-18 months internal | Internal AWS engineers (Solutions Architect, SE, EM) | Internal only; requires the SAA-C03 cert |
| **Lateral from engineering** | 0-3 months external | Senior+ engineers at any company | Comp trade (year 1 is often -10 to -20%) |
| **From a smaller vendor** | 0-6 months external | SEs / SAs at Series B-C startups | Brand-name change; interview bar is the same |
| **From sales engineering** | 0-3 months external | Current SEs wanting the SA title | Title is the same at some companies; the work is different |

The first three are the most common. The fourth (SE → SA) is
common at companies where the two titles are used
interchangeably.

### Path 1: AWS SA Associate program

The most well-known on-ramp. AWS recruits internally for the
SA Associate program once or twice a year. The program:

- **Eligibility:** Internal AWS employees with 2+ years at
  AWS in a customer-facing role (TAM, Solutions Architect,
  Specialist SA, Support Engineer, ProServe, etc.). The bar
  is *not* high for the application; the bar is high for the
  program.
- **Application:** Internal job posting, resume + 1-page
  "why SA" essay + your manager's recommendation.
- **Selection:** 1-2 rounds of internal interview, including
  a customer-interaction mock.
- **Duration:** 12-18 months of structured on-ramp:
  classroom training, shadow rotations, mentored customer
  calls, internal certifications.
- **Comp:** Often a level + title bump (SA I → SA II).
  Variable comp is added.

The 12-18 month duration is the trade-off. The benefit is
that you enter the SA role with 12 months of structured
mentorship and a network of peer SAs.

### Path 2: Lateral from engineering

The most common external on-ramp. The candidate profile:

- **Senior engineer at a non-vendor company** (e.g., a
  data engineer at a fintech) who's been the de facto SE
  on their team's customer engagements.
- **Interview prep:** 8-12 weeks, focused on the
  customer-interaction and behavioral rounds (Modules 02 +
  05 of this track). The technical rounds are easier for
  senior engineers; the customer rounds are the gap.
- **Comp:** Year 1 is often -10 to -20% vs. the IC track,
  because the SA variable comp is back-loaded. Year 2
  typically catches up; year 3 often exceeds the IC
  equivalent.
- **Common target companies:** AWS, GCP, Azure, Snowflake,
  Databricks, Confluent, MongoDB, HashiCorp, Elastic,
  Cloudflare, Datadog.

The biggest risk on this path: candidates fail to
*demonstrate* the customer-facing work in the interview.
"De facto SE" doesn't get read as "ready for SA" unless
the candidate's stories are *customer-flavored* (Module 05).

### Path 3: From a smaller vendor

The most underrated on-ramp. SEs and SAs at Series B-C
startups often have *better* customer-interaction reps
than senior engineers at big companies, because they did
the whole job (discovery, demo, whiteboarding, objection
handling) on every deal.

- **Brand-name change:** Moving from a 200-person startup
  to a hyperscaler is a step *up* in comp, scope, and
  brand. The interview bar is the same — but the
  candidate's actual experience is more directly
  relevant than a senior engineer's.
- **Comp:** Often a +30% to +50% jump in year 1, plus
  RSU.
- **Common target companies:** AWS, GCP, Azure, Snowflake,
  Databricks, Confluent, MongoDB, HashiCorp, Elastic.

The biggest risk: the candidate's *technical depth* is
calibrated to a smaller product surface. The hyperscaler
interview may probe depth in a specific service (e.g., 30
minutes of Kinesis deep-dive) that the candidate hasn't
worked with. Pre-study the target company's
*specialty-relevant* services.

### Path 4: From sales engineering

The most common internal on-ramp at companies where SE
and SA are different titles. The candidate profile:

- **Current SE at a large vendor** (Cisco, VMware,
  ServiceNow, Salesforce, Workday) wanting the SA title.
- **Trade-off:** At companies where the two roles are
  separate, the SE role is more demo-and-pitch focused,
  and the SA role is more architecture-and-influence
  focused. The move is not automatic.

---

## 2. The AWS SA Associate program in detail

If you're an internal AWS employee, this is the most
structured on-ramp. The key dates and requirements (2024-2026
vintage):

| Step | What happens | Duration |
|---|---|---|
| **Internal application** | Job posting, resume + "why SA" essay | 1-2 weeks |
| **Manager endorsement** | Your current manager signs off | 1 week |
| **Internal interview** | 1-2 rounds with the SA hiring team | 2-4 weeks |
| **Selection** | If selected, you enter the cohort | — |
| **Cohort kickoff** | Classroom training, 2-4 weeks | 2-4 weeks |
| **Cert requirements** | SAA-C03 + 1 specialty (e.g., Data Analytics) | 3-6 months |
| **Shadow rotations** | 2-3 months of customer-call shadowing with a Sr. SA | 2-3 months |
| **First customer accounts** | You start owning 2-3 accounts | Month 6-9 |
| **Full caseload** | You own 8-12 accounts, the standard SA I caseload | Month 12-18 |

The 12-18 month duration is real. Most SA Associates
*underestimate* the ramp time. The shadow rotations in
particular are the highest-leverage part — you observe
how a Sr. SA runs a discovery call, handles objections,
and writes proposals. Take notes. The 50% of the SA job
that you can't learn in classroom is in the shadow.

---

## 3. The lateral move prep plan (8-12 weeks)

If you're on Path 2 (lateral from engineering) or Path 3
(from a smaller vendor), this is the 8-12 week plan:

| Week | Focus | Module |
|---|---|---|
| 1 | Read Module 01 in one sitting | Module 01 |
| 2-3 | Read Module 02 (customer interaction) | Module 02 |
| 4 | Read Module 03 (technical SA questions) | Module 03 |
| 5 | Pick 3-5 system design problems from `../system_design/` | Cross-link |
| 6-7 | Read Module 05 (behavioral for SAs) | Module 05 |
| 8 | Read Module 06 (tips and frameworks) | Module 06 |
| 9 | 2-3 mock customer-interaction rounds with a friend | Practice |
| 10 | 2-3 mock behavioral rounds with a friend | Practice |
| 11 | Final review of the 4 C's + PREP frameworks | Module 06 |
| 12 | Apply + start interviewing | — |

The two weeks that matter most are 2-3 (customer interaction)
and 9 (mocks). Without the customer-interaction prep, the
interview bar will surprise you. Without the mocks, the
customer-interaction prep is theoretical.

---

## 4. The first 30/60/90 days as a new SA

Once you land the role, the first 90 days are the
make-or-break period. The pattern at most hyperscalers:

| Days | What to do |
|---|---|
| **0-30** | Shadow. 80% of your time is on customer calls with your mentor. You're listening, taking notes, learning the product, learning the customers. **Do not propose solutions in month 1.** Your mentor is wrong sometimes; you'll learn more by listening. |
| **30-60** | Co-own. You start co-owning 2-3 small accounts with your mentor. You run parts of customer calls (e.g., the architecture walkthrough) under supervision. You start contributing to proposals. |
| **60-90** | Own. You own 2-3 accounts outright (still with mentor available). You run discovery calls solo. You write proposals. You start being measured on account outcomes, not just activity. |

The "shadow first" instinct is the right one. New SAs who
propose solutions in month 1 get trusted less in month 6.
The most successful new SAs I've seen spent 50%+ of month 1
*just listening* to customer calls.

---

## 5. The resume for an SA role

The same resume principles from `how_to_get_the_interview/`
apply, with 2 SA-specific adjustments:

1. **Lead with customer-facing bullets.** Your resume should
   have 4-6 bullets that explicitly say "customer," "stakeholder,"
   "client," or "cross-functional." If every bullet is internal
   ("I shipped feature X in service Y"), you're reading as
   engineer, not SA.
2. **Quantify business outcomes, not just technical metrics.**
   "Reduced pipeline latency from 24h to 90s" is a technical
   metric. "Cut model training data latency from 24h to 90s,
   enabling $4M/year in faster-fraud-detection savings" is
   a business outcome. The SA rubric rewards the second.

If you don't have 4-6 customer-facing bullets, your resume
needs work *before* you start interviewing. See the
"before-the-loop" content in `../how_to_get_the_interview/`
for the full playbook.

---

## Try it

For your target company and target on-ramp, answer these in
writing:

1. **What on-ramp am I on?** (Path 1, 2, 3, or 4.)
2. **What is the interview bar at my target company?** (Look
   at 3-5 recent interview reports. What's the consensus
   difficulty?)
3. **What's my biggest gap?** (Customer-interaction
   experience? System design depth? Behavioral story bank?
   Comp alignment?)
4. **What's my 8-12 week prep plan?** (Use the template
   above, customized to your gaps.)
5. **What's my "why SA" 60-second pitch?** (Out loud, no
   notes.)

If any answer is vague, fix it before you start
interviewing. The most common reason senior engineers fail
SA loops is *not* the technical bar — it's the customer-
facing bar. The prep has to close that gap, not just the
technical one.
