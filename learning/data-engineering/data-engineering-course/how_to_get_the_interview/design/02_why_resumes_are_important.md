# 02 — Why Resumes are Important

> **Lesson 2 of 9** · ~12 min

The data on recruiter time, ATS rejection rates, and the one
decision (your title) that determines more than anything else
whether your resume gets read.

---

## 1. The 6-second scan

Recruiters spend **6-8 seconds** on the first pass of a resume.
This is not an estimate — it has been measured in multiple
eye-tracking studies (TheLadders, 2012; TopResume, 2018; Google's
internal recruiting data, leaked in various forms since 2018).
The recruiter is scanning an F-pattern across the page, looking
for exactly 4 things:

1. **Your current title** (top of page, left side)
2. **Your current company** (next to the title)
3. **Your years of experience** (counted from the dates on the left)
4. **One number** (any quantified bullet, anywhere on the page)

If all 4 hit, the resume gets a second look. If any of them
*don't* hit — wrong title, no current company, no number, unclear
years — the resume is rejected. The recruiter moves to the next
one in the queue. 6 seconds is up.

This is brutal, but it's the system. You can either optimize for
it or rage against it. The smart move is to optimize.

---

## 2. The 75% ATS-rejection stat

**~75% of resumes are rejected by an Applicant Tracking System
(ATS) before any human ever sees them.** The actual number varies
by source — Jobscan reports 70-75%, research from SHRM puts it
in the same range, and Greenhouse's own customer data suggests
~50% for jobs that hit "Open to applicants" on LinkedIn. The
direction is the same: **most resumes never make it past Gate 1**.

ATS rejection is not random. It's deterministic, based on:

- **Keyword match** — does your resume contain the terms the JD
  used? If the JD says "Airflow" and your resume says "workflow
  orchestration tool," you will be filtered.
- **Title match** — does your current/recent title match the title
  family in the JD? "Data Engineer" → "Data Engineer" is a match.
  "Data Engineer" → "Analytics Engineer" might not be (depending
  on the company).
- **Years of experience** — does your total YoE meet the minimum
  in the JD? Some companies filter <3 YoE for senior, <5 for
  staff, <7 for principal.
- **Education** — does the JD require a degree you don't have?
  Some companies hard-filter on this, especially financial
  services and government-adjacent roles.
- **Formatting** — does the ATS *parse* your resume? PDFs with
  tables, columns, and embedded images are the most common
  parsing failure.

The takeaway: **your resume has to be optimized for two readers
simultaneously — the ATS and the human.** The human reads it in
6 seconds. The ATS reads it in <1 second. If either rejects you,
the other never sees it.

---

## 3. Why "data engineer" vs "analytics engineer" vs "ML engineer" matters

Title is the most important 2 words on your resume. The reason is
that both the ATS and the recruiter use it to *route* your
application: do you belong in this req's pipeline, or a different
one?

The data engineering title space is messy. The same person doing
substantially the same work can legitimately hold any of these
titles:

| Title | What the role typically does | What companies look for |
|---|---|---|
| **Data Engineer** | Pipelines, batch + streaming, ETL/ELT, infra | Python/Scala, SQL, Airflow/Spark, cloud, dbt |
| **Analytics Engineer** | dbt models, dimensional modeling, BI-adjacent | dbt, SQL, Looker/Tableau, dimensional modeling |
| **ML Engineer** | Feature pipelines, model serving, training infra | Python, ML frameworks, feature stores, model serving |
| **Data Platform Engineer** | Internal infra, query engines, data lake tooling | Distributed systems, Spark/Flink internals, infra |
| **Data Scientist** | Notebook analysis, modeling, experimentation | Stats, ML, Python, business question framing |

The same person might be a strong candidate for several of these.
The problem is that **the company's req is titled one of these**,
and the recruiter is screening for *that title* (or close
adjacencies). If you are a "Data Engineer" applying to an "ML
Engineer" req, you might get filtered even if you're a perfect
fit. If you are a "Senior Analytics Engineer" applying to a
"Staff Data Engineer" req, same problem.

The fix is not to lie about your title. The fix is to:

1. **Use the JD's exact title family in your positioning
   statement** (the 1-line summary at the top of your resume).
2. **Use the JD's exact keywords in your skills section** (e.g.
   "ML platform" if the JD says "ML platform," not "ML
   infrastructure").
3. **Apply to the role whose title matches your title.** If you're
   a "Senior Analytics Engineer" and the role is "Staff Data
   Engineer," apply anyway — but make sure your positioning
   statement bridges the gap explicitly: *"Analytics engineer with
   4 years of data pipeline + dbt experience targeting staff data
   engineering roles."*

More on this in Lesson 04 (Targeted Resumes). The short version:
**your title and your positioning statement are the routing
mechanism. Get them right and the rest of the resume gets read.**

---

## 4. The real reason resumes are important

Here's the uncomfortable truth: **the resume is not a record of
your career. It's a sales document.** A sales document that
exists to do exactly one thing: get a human to spend 30 more
minutes on you.

Most engineers write resumes as if they're a record. "I worked
at Company X from year to year, here are the things I did." That
is a *biography*, not a *sales document*. A biography is what you
write in the third person for a Wikipedia article. A sales
document is what you write when you have 6 seconds to convince
someone to take a 30-minute meeting.

A sales document:

- **Leads with the reader's interest**, not yours. The reader
  cares about their req, not your career.
- **Quantifies everything.** "I improved the system" is a
  biography. "I cut pipeline runtime by 60%, from 8 hours to
  3.2 hours" is a sales document.
- **Front-loads the 4 things the recruiter scans for** — title,
  company, years, number.
- **Gets out of the way.** No clever design, no infographic, no
  "References available upon request." A clean 1-page PDF that
  parses correctly.

If you take only one thing from this lesson, take this: **stop
treating your resume as a record. Start treating it as a 6-second
sales document.** The rest of the lessons in this track are
mechanics for executing on that.

---

## 5. A worked example: same person, two resumes

**Same candidate: 4 years DE, Python + SQL + Airflow + AWS, last
role at a mid-size fintech.**

**Resume A (biography):**

> **John Smith**
> john.smith@email.com
>
> *Objective:* Seeking a challenging data engineering role at a
> forward-thinking company where I can grow my skills.
>
> **Experience**
> **Data Engineer** — Fintech Co (2021-2025)
> - Responsible for the data pipeline
> - Worked with the analytics team
> - Helped migrate to the cloud
> - Built dashboards
>
> **Data Analyst** — BigCo (2019-2021)
> - Wrote SQL queries
> - Made reports
> - Worked with stakeholders

**Resume B (sales document):**

> **John Smith**
> San Francisco, CA · john.smith@email.com · linkedin.com/in/john
>
> *Data engineer with 4 years building production Python + SQL
> pipelines on AWS, targeting senior data platform roles.*
>
> **Skills:** Python, SQL, Airflow, dbt, Spark, AWS (S3, Glue,
> Redshift, Lambda), Terraform, Looker
>
> **Experience**
> **Data Engineer** — Fintech Co (2021-2025)
> - Cut nightly batch pipeline runtime 60% (8h → 3.2h) by
>   rewriting ETL in PySpark on AWS Glue
> - Built and operated 12 Airflow DAGs ingesting 4 TB/day into
>   Redshift with 99.7% on-time SLA
> - Led migration of 8 analytics-team dbt models from BigQuery to
>   Redshift, zero downtime, adopted as the team default
>
> **Data Analyst** — BigCo (2019-2021)
> - Owned 30+ Looker dashboards used by 200+ stakeholders;
>   reduced ad-hoc SQL requests by 40% via a self-serve layer

Both are 4 years experience. Same person. Same actual work. Resume
B gets the screen call. Resume A doesn't, because it has no
numbers, no specific tech, and no positioning. The difference is
not "writing better" — it's "treating the document as a sales
artifact."

---

## Try it

Open your current resume. Set a 60-second timer. Read it once,
top to bottom, the way a recruiter would.

Write down:

1. What is my **current title** (as the recruiter sees it)? ____
2. What is the **first number** the recruiter sees? ____
3. How many years of experience does the date column show? ____
4. Is there a **positioning statement** that names the role I'm
   targeting? Y / N

If you can't answer all 4 in 6 seconds — or if the answers are
weak — you have a Gate 1 / Gate 2 problem. Lessons 03-05 fix it.
