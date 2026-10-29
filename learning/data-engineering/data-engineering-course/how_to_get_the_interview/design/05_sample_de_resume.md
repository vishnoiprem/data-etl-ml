# 05 — Sample DE Resume

> **Lesson 5 of 9** · ~15 min

The artifact lesson. A full 1-page data engineering resume (Jordan
Park, 5 years experience, mid-size fintech) with a bullet-by-bullet
walkthrough of *why* each line is there, plus 5 before/after
rewrites you can use as templates for your own bullets.

The full Markdown version of the resume (clean, copy-pasteable) is
in `../artifacts/sample_de_resume.md`. This lesson is the annotated
walkthrough.

---

## 1. The candidate

**Jordan Park, 5 years data engineering experience.**

- Started as a backend engineer (2 years at a logistics company),
  transitioned to data engineering 5 years ago.
- 3 years at a mid-size fintech (MidPay) as a Data Engineer →
  Senior Data Engineer.
- 2 years before that at LogiCo (logistics startup) as a Data
  Engineer.
- Stack: Python, SQL, Scala (working), Airflow, dbt, Spark, Kafka,
  AWS (S3, Glue, Redshift, Lambda, SageMaker), Snowflake, Terraform.
- Side projects: maintains a popular open-source dbt package
  (jpark_dbt_utils, 400+ GitHub stars), wrote a Medium post on
  dbt incremental models that got 30k views.
- Targeting: Senior → Staff data platform roles at
  infrastructure-scale companies (Databricks, Stripe, Airbnb, Notion).

The resume below is the **master version** — the un-targeted one.
Targeted versions (for Stripe, Databricks, etc.) are derived from
this. The artifact in `artifacts/sample_de_resume.md` is the
clean copy.

---

## 2. The resume

```
─────────────────────────────────────────────────────────────────────
JORDAN PARK
Seattle, WA · jordan.park@email.com · linkedin.com/in/jordanparkdev
github.com/jordanpark · medium.com/@jordanpark

Senior data engineer with 5 years building production Python + SQL
pipelines on AWS, with 2 years of cross-team architecture and
mentorship, targeting staff data platform roles at infrastructure-
scale companies.

SKILLS
Languages:    Python, SQL, Scala (working), Bash
Data:         Airflow, dbt, Spark, Kafka, Snowflake, Redshift,
              BigQuery, Databricks, Great Expectations
Cloud:        AWS (S3, Glue, Lambda, Redshift, SageMaker), GCP
              (BigQuery, Dataflow), Terraform, Docker, Kubernetes
Tooling:      Git, CI/CD (GitHub Actions), dbt, Looker, Tableau,
              Prometheus, Grafana, MLflow

EXPERIENCE

Senior Data Engineer · MidPay                                   2022 - Present
   • Led migration of 14 TB on-prem Hadoop cluster to AWS (S3 +
     Glue + Redshift) over 4 months, zero downtime, $280k/yr
     infrastructure savings
   • Built and operated 18 Airflow DAGs ingesting 2.4 TB/day
     into Redshift with 99.7% on-time SLA across 4 product teams
   • Owned 8 dbt models + Great Expectations data-quality suite
     serving 4 product teams; cut data quality incidents 70%
   • Established the team's first architecture-review forum,
     adopted org-wide by 3 other teams within 6 months
   • Mentored 2 junior DEs; both promoted to mid-level within 18
     months
   • Authored internal "Data Engineering Handbook" (60 pages);
     used as the onboarding doc for 12+ new hires

Data Engineer · LogiCo                                          2020 - 2022
   • Built and operated Kafka streaming pipeline ingesting 800M
     events/day into Snowflake with 99.9% delivery SLA
   • Designed the multi-region analytics architecture for
     LogiCo's customer-facing dashboards; presented to
     VP-Engineering as the standard for 4 subsequent migrations
   • Reduced dashboard query latency 8s → 320ms via materialized
     views + dbt; cut user-facing "slow dashboard" complaints 85%
   • Partnered with data science team to ship a real-time feature
     pipeline powering 3 production ML models; cut model training
     data latency from 24h to 90s

Software Engineer · LogiCo                                      2018 - 2020
   • Built and operated 6 Python services in the fulfillment
     pipeline; owned 1 on-call rotation

SELECTED PROJECTS
   • jpark_dbt_utils (open source) — dbt package with 14 macros
     for incremental models and testing; 400+ GitHub stars
   • "Idempotent dbt Incremental Models" (Medium, 30k views) —
     technical deep-dive referenced in dbt's official docs

EDUCATION
   • B.S. Computer Science, University of Washington, 2018
─────────────────────────────────────────────────────────────────────
```

One page. Single column. 9-11pt font (this is rendered in monospace
for readability, but in practice it's a clean sans-serif PDF).

---

## 3. The walkthrough — why each section is there

### The header (5 lines)

- **Name** in a larger font. This is the *only* place design matters.
- **City, State** (not full address). Recruiters need to know if
  you're local, hybrid-eligible, or remote-only. The full address
  is not needed and is a privacy risk.
- **Email** — a professional one. `jordan.park@email.com` is fine.
  `sexytechdude99@gmail.com` is not. The recruiter will judge you.
- **LinkedIn** — full URL, not "linkedin.com/in/jordanpark" alone
  (the auto-link breaks in some PDFs).
- **GitHub** — included because Jordan is an open-source maintainer.
  If you don't have a public GitHub with relevant code, *don't
  include this line*. Empty GitHub profiles are worse than none.
- **Medium** — included because Jordan has a popular technical
  blog. Same rule: only if it's actually good and relevant. Don't
  link to a Medium with 2 posts from 2019.

### The positioning statement (1 line, ~250 chars)

> *"Senior data engineer with 5 years building production Python
> + SQL pipelines on AWS, with 2 years of cross-team architecture
> and mentorship, targeting staff data platform roles at
> infrastructure-scale companies."*

This is doing **four** jobs in one line:

1. **Names the current title** ("Senior data engineer") so the
   recruiter can route the resume.
2. **Names the core stack** ("production Python + SQL pipelines
   on AWS") so the ATS can match keywords.
3. **Names the seniority signal** ("2 years of cross-team
   architecture and mentorship") so a staff-level reader can
   place the candidate.
4. **Names the target role** ("staff data platform roles at
   infrastructure-scale companies") so the recruiter knows which
   reqs to consider.

A recruiter reads this in 1 second and decides whether to keep
reading. **A bad positioning statement loses the resume in 1
second. A good one wins the next 5 seconds.**

### The skills section (4 categories, ~15 lines)

Organized into 4 buckets because the JD's required skills fall
into 4 natural categories for DE roles: Languages, Data, Cloud,
Tooling. The recruiter scans the categories, then the specific
tools.

**Why this exact list:**

- **Languages** — Python, SQL, Scala (working), Bash. "Scala
  (working)" is honest: it signals exposure without over-claiming.
  A recruiter at a Scala-heavy shop will read this and think
  "trainable."
- **Data** — Airflow, dbt, Spark, Kafka, Snowflake, Redshift,
  BigQuery, Databricks, Great Expectations. This is the keyword
  basket. Most JDs will hit at least 4 of these.
- **Cloud** — AWS, GCP, Terraform, Docker, Kubernetes. The "(S3,
  Glue, Lambda, Redshift, SageMaker)" parenthetical is critical:
  it lists the *specific* AWS services, not just "AWS." ATS
  filters on specific service names.
- **Tooling** — the long tail: Git, CI/CD, BI tools, observability,
  MLflow. This is the section that catches the "nice to have"
  requirements in JDs.

**What was deliberately left out:**

- **Hadoop** (only mentioned in the MidPay bullet, where it's
  the *before* state of a migration — a feature, not a stack).
- **Hive, Pig, Oozie** — legacy Hadoop ecosystem, not worth
  listing.
- **Excel, PowerPoint** — assumed.
- **Jira, Confluence, Slack** — assumed for any senior+.

### The experience section (3 roles, 16 bullets)

Three roles, in reverse chronological order. The MidPay role
gets 6 bullets (most recent, most relevant, most space). The
LogiCo DE role gets 4 bullets (the bridge between current and
Software Engineer). The LogiCo SWE role gets 1 bullet
(acknowledges the career start, doesn't pad with irrelevance).

**Every bullet is in the XYZ format** (Lesson 03). Every bullet
has a number. Every bullet starts with a strong action verb in
past tense.

### Selected projects (2 lines)

- **Open source** — jpark_dbt_utils with the star count. Stars
  are a *credibility signal* that an interviewer can verify.
  400+ stars is real, modest, and verifiable.
- **Technical writing** — the Medium post with view count. Same
  logic: 30k views is real, modest, and verifiable.

The two projects chosen both demonstrate *the same thing*: the
candidate can produce high-quality, public-facing work in the
data engineering space. This is the strongest signal you can
send short of an in-person conversation.

### Education (1 line)

- **B.S. CS, University of Washington, 2018.** School name + year
  is enough. No GPA (graduated 7 years ago — irrelevant). No
  honors (not relevant at this seniority).

---

## 4. The 5 before/after rewrites (templates for your own bullets)

These are the most common bullet-quality problems I see, with
before/after rewrites using Jordan's work as the substrate.

### Rewrite 1: from "responsible for" to "led"

**Before (vague, duty-listed):**

> *Responsible for the data pipeline migration to the cloud,
> working with the platform team and various stakeholders over
> the past year.*

**After (XYZ, specific, quantified):**

> *Led migration of 14 TB on-prem Hadoop cluster to AWS (S3 +
> Glue + Redshift) over 4 months, zero downtime, $280k/yr infra
> savings.*

**What changed:** action verb (Led), specific scope (14 TB, named
Hadoop → AWS services), duration (4 months), outcome ($280k/yr +
zero downtime). The "various stakeholders" became implicit in
"zero downtime" — that only happens if you actually coordinated
with people.

### Rewrite 2: from "worked on" to "built and operated"

**Before:**

> *Worked on the streaming pipeline using Kafka.*

**After:**

> *Built and operated Kafka streaming pipeline ingesting 800M
> events/day into Snowflake with 99.9% delivery SLA; owned
> on-call rotation for 18 months.*

**What changed:** action verb (Built and operated), specific
throughput (800M events/day), specific destination (Snowflake),
reliability metric (99.9% delivery SLA), and the *on-call
ownership* line that signals "this wasn't a one-time project, I
ran it in production."

### Rewrite 3: from "improved" to "reduced X from A to B"

**Before:**

> *Improved dashboard performance for the analytics team.*

**After:**

> *Reduced dashboard query latency 8s → 320ms via materialized
> views + dbt; cut user-facing "slow dashboard" complaints 85%.*

**What changed:** "Improved" is the worst possible verb — it's
vague, unscoped, and unmeasurable. The rewrite names the
*specific metric* (8s → 320ms), the *method* (materialized
views + dbt), and the *user-visible outcome* (85% complaint
reduction). All three are signals a hiring manager can probe
in the interview.

### Rewrite 4: from "helped" to a cross-functional bullet

**Before:**

> *Helped the data science team with feature pipelines for
> their ML models.*

**After:**

> *Partnered with data science team to ship a real-time feature
> pipeline powering 3 production ML models; cut model training
> data latency from 24h to 90s.*

**What changed:** "Helped" is the cross-functional equivalent of
"worked on" — it signals you were a junior participant. The
rewrite names the *partnership* (Partnered with), the *output*
(3 production ML models, named), and the *outcome* (24h → 90s
training data latency). The data science team is now a peer, not
a customer.

### Rewrite 5: from "mentored" to a leadership bullet

**Before:**

> *Mentored junior engineers on the team.*

**After:**

> *Mentored 2 junior DEs; both promoted to mid-level within 18
> months.*

**What changed:** Same activity (mentorship), different signal.
The first version says "I did mentorship." The second says "my
mentorship had measurable impact — 2 promotions in 18 months."
The "both promoted" is the proof point. Senior+ hiring managers
read that and think "this person grows people, not just systems."

---

## 5. What a 1-page resume forces you to cut

The hardest part of writing a 1-page resume is the *cutting*.
Jordan's actual career has more than 16 bullets worth of work.
The 16 bullets here are the 16 that matter for the roles Jordan
is targeting.

Things that were *cut* and why:

- **3 more MidPay bullets** (CI/CD work, on-call rotation, code
  review stats). The 6 chosen bullets carry the same signal
  (production ownership, mentorship, cross-team influence).
- **2 LogiCo DE bullets** (Kafka Connect plugin work, internal
  Python tooling). Same logic — the 4 chosen bullets are
  higher-signal.
- **LogiCo SWE bullets beyond the 1** (microservices work, on-call
  work, tech debt project). At 5 years DE experience, the SWE
  role is *bridge context*, not the main story.
- **Personal projects** beyond the 2 (a TensorFlow side project,
  a Kubernetes cluster, a LeetCode ranking). The 2 chosen are
  *public and verifiable*. Private side projects don't make the
  cut.

This is the senior+ discipline: **the 1-page constraint is the
feature, not the bug.** It forces you to be honest about what
matters. If you can't cut your 4-page resume to 1 page, you
don't yet know your own story.

---

## 6. The artifact

The clean, copy-pasteable version of this resume is in
`../artifacts/sample_de_resume.md`. Use it as a template:

1. Copy it.
2. Replace Jordan's name, contact info, and bullets with yours.
3. Use the 5 before/after rewrites in Section 4 as templates
   for the bullets you're struggling with.

For the targeted versions (Stripe, Airbnb, Databricks), see
`04_making_targeted_resumes.md` — the same resume becomes 3
different resumes with 30-90 min of editing each.

---

## Try it

Open `../artifacts/sample_de_resume.md`. Set a 30-minute timer.

1. Replace Jordan's bullets with your own, in the same order
   (most recent first, most impactful first within each role).
2. Write a positioning statement using Jordan's as a template
   (title + stack + seniority signal + target role).
3. Reorder the skills section to put *your* top 4 tools first.
4. Cut the resume to 1 page.

When you're done, save it as `resume_master.md`. That's your
master resume. Lessons 04 and 06 will turn it into 2 targeted
resumes + 2 cover letters.
