# 04 — Making Targeted Resumes

> **Lesson 4 of 9** · ~20 min

A workshop on how to read a job description, extract the keywords
and signals, and rewrite the *same* resume for 3 different role
families. The highest-leverage hour in your job search.

---

## 1. Why targeted resumes work

A "targeted resume" is a customized version of your master resume
where the *positioning statement*, *skills section*, and 2-3
*bullets* are rewritten to mirror a specific job description (JD).
The rest of the resume stays the same.

The data on how much this matters is clear:

- **Targeted resumes get 2-3x the response rate** of generic ones.
  Multiple studies (Jobscan, ResumeGo, TopResume) show this across
  industries and seniority levels. The mechanism is the ATS keyword
  pass + the recruiter 6-second scan both working in your favor.
- **A targeted resume takes 30-90 minutes to produce** (after the
  master is done). Less, once you've done 2-3 — you start to see
  the pattern.
- **The math is obvious.** 30 targeted applications, 2 hours of
  customization total, 9-12 screen calls. 30 generic applications,
  0 hours of customization, 3 screen calls. The custom work pays
  for itself many times over.

The "tells" of a generic resume that get you filtered:

- **No company name in the cover letter or positioning statement**
  (recruiter assumes the candidate doesn't know who they're
  applying to)
- **No specific tech stack from the JD** (recruiter assumes the
  candidate doesn't have *that* stack)
- **No mirror keywords** (the ATS doesn't tag the resume as a
  match for this req)
- **Vague "responsible for" bullets** (recruiter assumes no impact)

A targeted resume eliminates all 4 of these.

---

## 2. How to read a JD: the 4-pass method

Before you write a single word, you read the JD four times. Each
pass extracts a different layer of information.

**Pass 1 — Title and level (30 sec).** What title and level is
this? Senior? Staff? IC vs. manager? What title family — data
engineer, analytics engineer, ML platform? Write the answer at
the top of your notes.

**Pass 2 — Required vs. preferred (2 min).** Most JDs separate
"Required" and "Preferred" qualifications. The required list is
what the ATS filters on. If you don't have 80%+ of the required
list, the application is a stretch. The preferred list is what
the hiring manager looks for. If you have 2-3 items from the
preferred list, mention them.

**Pass 3 — The 3-5 keywords (5 min).** Read the JD once more and
list the 3-5 *tools, technologies, or skills* that get mentioned
the most. These are your **mirror keywords** — the exact terms
that need to appear in your positioning statement, skills section,
and at least 1 bullet.

**Pass 4 — The "pain" and the "win" (5 min).** Every JD has an
implicit *pain* (what the team is struggling with) and an implicit
*win* (what success in this role looks like). Read between the
lines:

| Phrase in JD | Implicit pain | Your counter-bullet |
|---|---|---|
| "We're rebuilding our data platform" | Legacy infra, technical debt | "Migrated legacy Hadoop to AWS, $280k/yr savings" |
| "We're scaling 10x" | Current infra is breaking | "Scaled pipeline 4 TB → 40 TB/day with no headcount increase" |
| "We're investing in data quality" | Bad data, broken dashboards | "Built Great Expectations suite catching 95% of schema drift" |
| "Strong collaboration with product" | Silos, slow turnarounds | "Partnered with 4 PMs to ship 12 pipelines in 6 months" |

The pain-and-win pass is the highest-leverage part. The recruiter
isn't just scanning for keywords — they're scanning for *evidence
that you've solved a problem like theirs*. Your bullet should
mirror their problem.

---

## 3. The 30-min vs. 4-hour decision

Not every application deserves a 4-hour resume rewrite. The
decision tree:

```
Is this a "dream" role (top-3 target company, or 2x comp)?
  ├─ Yes → 4-hour rewrite. 2-3 bullets customized, full positioning
  │        statement rewritten, cover letter customized.
  └─ No  → Is this a credible role (50%+ match on required skills)?
            ├─ Yes → 30-min rewrite. Skills section + positioning
            │        statement only. No per-bullet customization.
            └─ No  → Skip. Volume play only.
```

Most candidates do this **backwards** — they spend 4 hours on a
mid-fit role (because the JD is exciting) and 30 minutes on a
dream role (because they assume the resume will speak for itself).
The reverse is correct: spend the 4 hours where it pays off.

A 30-minute targeted resume involves:

- Rewrite the positioning statement (5 min)
- Reorder the skills section to put the JD's top 3 keywords first
  (5 min)
- Re-read your existing bullets, tighten any that already match the
  JD's keywords (15 min)
- Save the file as `resume_<company>_<role>.pdf` (5 min)

A 4-hour rewrite is the same, plus:

- Pick 2-3 bullets and rewrite them in XYZ format, using the JD's
  mirror keywords (60-90 min)
- Write a customized cover letter (60 min)
- Proofread, export to PDF, save (15 min)

---

## 4. Worked example: same master resume, 3 target roles

**Master resume (Jordan Park, 5 years DE) — the unchanging core:**

> **Jordan Park**
> Seattle, WA · jordan.park@email.com · linkedin.com/in/jordanparkdev
> · github.com/jordanpark
>
> **Experience**
>
> **Senior Data Engineer** — MidPay (2022-2025)
> - Led migration of 14 TB on-prem Hadoop cluster to AWS (S3 +
>   Glue + Redshift), $280k/yr infra savings, zero downtime
> - Built and operated 18 Airflow DAGs ingesting 2.4 TB/day into
>   Redshift with 99.7% on-time SLA
> - Owned 8 dbt models + Great Expectations suite serving 4
>   product teams; cut data quality incidents 70%
> - Mentored 2 junior DEs; both promoted to mid-level within 18
>   months
>
> **Data Engineer** — LogiCo (2020-2022)
> - Built Kafka streaming pipeline ingesting 800M events/day into
>   Snowflake
> - Reduced dashboard query latency 8s → 320ms via materialized
>   views + dbt
>
> *(Skills, projects, education omitted for the example.)*

**Now the 3 targeted versions.**

### Target A: Senior Pipeline Engineer at Stripe

JD highlights: *"5+ years building production data pipelines;
strong Python and SQL; experience with Kafka, Snowflake, or
similar; experience with data quality tooling; comfortable
owning production on-call."*

**Targeted positioning statement:**

> *Senior data engineer with 5 years building production Python
> pipelines on Kafka + Snowflake, targeting senior data
> engineering roles on infrastructure-focused teams.*

**Skills reordered to match:** Python, SQL, Kafka, Snowflake,
Airflow, dbt, Great Expectations, AWS (S3, Glue, Redshift),
Terraform.

**Bullet tweaks:**

- "Led migration of 14 TB on-prem Hadoop cluster to AWS" →
  **"Led migration of 14 TB on-prem Hadoop cluster to AWS
  (S3+Glue+Redshift), $280k/yr infra savings, zero downtime;
  now familiar with Snowflake-based equivalents."** *(Same
  bullet, but the parenthetical lists services that mirror the
  JD's cloud style; the trailing sentence bridges to Snowflake.)*
- "Built Kafka streaming pipeline ingesting 800M events/day" →
  **"Built and operated Kafka streaming pipeline ingesting
  800M events/day into Snowflake with 99.9% delivery SLA;
  owned production on-call rotation for 18 months."** *(The
  on-call callout mirrors the JD's "comfortable owning production
  on-call.")*

**Why this works:** The positioning statement uses the JD's
exact phrasing ("production data pipelines," "Python," "Kafka,"
"Snowflake"). The bullet rewrites add the on-call signal and
the delivery SLA — both of which the JD mentioned.

### Target B: Staff Data Architect at Airbnb

JD highlights: *"7+ years experience; architecture-level design
of data platforms; cross-team influence; experience presenting
to senior leadership; thought leadership."*

**Targeted positioning statement:**

> *Senior data engineer with 5 years building data platforms at
> scale, with 2 years of cross-team architecture work and
> mentorship, targeting staff data platform roles.*

**Skills reordered to match:** Architecture, system design,
Python, SQL, AWS, dbt, Terraform, mentorship.

**Bullet tweaks:**

- "Mentored 2 junior DEs" → **"Mentored 2 junior DEs to
  mid-level within 18 months; established the team's first
  architecture review forum, adopted org-wide within 6
  months."** *(The architecture-review callout maps to the
  "cross-team influence" JD signal. The "adopted org-wide"
  is the staff-level scope signal.)*
- "Built Kafka streaming pipeline" → **"Designed the
  multi-region data architecture for LogiCo's analytics
  platform, presented to VP-Engineering as the standard for
  4 subsequent team migrations."** *(Same person, same work,
  reframed for the architecture + leadership + cross-team
  signal that staff JDs care about.)*

**Why this works:** A staff JD looks for *scope* and *influence*,
not *delivery*. Same bullets, but reframed to emphasize the
scope (org-wide adoption, architecture review, VP-Eng
presentation). The same engineer looks more senior in 30
minutes of editing.

### Target C: ML Platform Engineer at Databricks

JD highlights: *"Experience with ML pipelines, feature stores,
model serving; Python + Spark; experience with ML frameworks
(PyTorch, TensorFlow); bonus: Databricks/MLflow experience."*

**Targeted positioning statement:**

> *Data engineer with 5 years building Python + PySpark
> pipelines on AWS, with hands-on experience serving ML
> feature pipelines, targeting ML platform engineering roles.*

**Skills reordered to match:** Python, PySpark, MLflow, AWS
(S3, Glue, SageMaker), feature stores, Kafka, dbt, Airflow.

**Bullet tweaks:**

- "Built and operated 18 Airflow DAGs" → **"Built and operated
  18 Airflow DAGs serving both analytics and ML feature
  pipelines, with feature store integration via SageMaker
  Feature Store; used by 4 data-science teams for training
  and inference."** *(Same DAGs, reframed for the ML audience.
  The feature-store + data-science callouts mirror the JD.)*
- Add a **new bullet** for the LogiCo role: *"Partnered with
  data science team to ship a real-time feature pipeline
  powering 3 production ML models; cut model training data
  latency from 24h to 90s."* *(The JD asks for "ML pipelines"
  — this bullet is the single best evidence you can offer.)*

**Why this works:** You're not pretending to be a different
engineer — you're showing the *ML-relevant* parts of the same
work. The Kafka streaming bullet, for the Stripe role, was
about throughput. For the Databricks role, it's about
serving ML use cases. Same work, different angle.

---

## 5. The tells of a generic resume — and the fix

| Tell | What it signals to the recruiter | The fix |
|---|---|---|
| **"Objective: Seeking a data engineering role at a great company"** | The candidate didn't read the JD | Replace with a positioning statement that names *this* role |
| **Skills section in same order for every application** | The candidate sent the same resume to 100 companies | Reorder skills to put the JD's top 3 first |
| **No mention of the company's stack in any bullet** | The candidate doesn't have *that* stack | Add at least 1 bullet that names a tech from the JD |
| **Vague "Worked on various data projects"** | No specific impact | Use XYZ on every bullet |
| **2+ page resume with no Senior/Staff signal in the first half** | Junior or unclear seniority | Tighten to 1 page; the senior+ signal should be visible in the first 1/3 |

---

## Try it

Pick 2 real JDs in your target role family. Do the 4-pass read
on each (15 min total). For each, write down:

1. The 3-5 mirror keywords (Pass 3)
2. The implicit pain (Pass 4)
3. The 1 bullet on your current resume that best addresses the pain

Now rewrite the positioning statement for each role. Save each
version as `resume_<company>_<role>.md` or `.pdf`. Time yourself.
If you can do this in <30 min per role, you're at speed.

That's your first 2 targeted resumes. Lesson 05 gives you a
full sample to compare yours against.
