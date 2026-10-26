# Jordan Park — Data Engineering Resume (Sample)

> **Sample artifact for the "How to Get the Interview" track.**
> Copy this as a template. Replace the name, contact info, and
> bullets with your own. See `../design/05_sample_de_resume.md`
> for the full annotated walkthrough.

This is a fictional candidate. The name, experience, and
quantified bullets are illustrative. Do not use this verbatim
for your own application — it is a *template*, not a real
resume.

---

## The resume (clean version)

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

---

## 5 before/after rewrites (templates for your own bullets)

### 1. "Responsible for" → "Led"

**Before:**
> *Responsible for the data pipeline migration to the cloud,
> working with the platform team and various stakeholders over
> the past year.*

**After:**
> *Led migration of 14 TB on-prem Hadoop cluster to AWS (S3 +
> Glue + Redshift) over 4 months, zero downtime, $280k/yr infra
> savings.*

### 2. "Worked on" → "Built and operated"

**Before:**
> *Worked on the streaming pipeline using Kafka.*

**After:**
> *Built and operated Kafka streaming pipeline ingesting 800M
> events/day into Snowflake with 99.9% delivery SLA; owned
> on-call rotation for 18 months.*

### 3. "Improved" → "Reduced X from A to B"

**Before:**
> *Improved dashboard performance for the analytics team.*

**After:**
> *Reduced dashboard query latency 8s → 320ms via materialized
> views + dbt; cut user-facing "slow dashboard" complaints 85%.*

### 4. "Helped" → cross-functional with measurable outcome

**Before:**
> *Helped the data science team with feature pipelines for
> their ML models.*

**After:**
> *Partnered with data science team to ship a real-time feature
> pipeline powering 3 production ML models; cut model training
> data latency from 24h to 90s.*

### 5. "Mentored" → leadership with measurable outcome

**Before:**
> *Mentored junior engineers on the team.*

**After:**
> *Mentored 2 junior DEs; both promoted to mid-level within 18
> months.*

---

## How to use this artifact

1. **Copy the resume structure** — header, positioning statement,
   skills in 4 categories, experience in 3 roles, selected projects,
   education. Don't deviate.
2. **Use the before/after rewrites as templates** — find the
   closest "before" bullet on your own resume and apply the same
   transformation.
3. **Cut to 1 page.** If you can't, you're not done.
4. **Save as `resume_master.md`** and convert to PDF before sending.

For targeted versions of this same resume (Stripe, Airbnb,
Databricks), see `../design/04_making_targeted_resumes.md`.
