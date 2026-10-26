# 03 — Good Resumes

> **Lesson 3 of 9** · ~15 min

The mechanics of a resume that survives the 6-second scan, the ATS,
and the 2-3 minute hiring-manager read. The XYZ formula, the
one-page rule, and the 8 anti-patterns that get you filtered.

---

## 1. The XYZ formula

The single most useful resume-writing tool is the **XYZ formula**,
attributed to Laszlo Bock (Google's former SVP of People Operations,
who wrote about it in *Work Rules!*).

> **"Accomplished [X], as measured by [Y], by doing [Z]."**

Where:
- **X** = the *what* (the scope of the work, often a verb + object)
- **Y** = the *measurable result* (a number, a percent, a scale)
- **Z** = the *how* (the method, the technology, the specific action)

**Why it works:** the XYZ formula forces every bullet to have
*substance*. It rejects the two most common resume-writing sins —
vagueness ("improved the system") and duty-listing ("responsible
for the pipeline") — by making the bullet mechanically incomplete
without an X, a Y, and a Z.

**Worked example — a data engineer bullet:**

| Style | Bullet |
|---|---|
| **Vague (no Y, no Z)** | Improved the data pipeline. |
| **Duty-listed (no Y)** | Responsible for the data pipeline, including ETL and orchestration. |
| **XYZ (good)** | Cut nightly batch pipeline runtime 60% (8h → 3.2h) by rewriting ETL in PySpark on AWS Glue, processing 4 TB/day. |

Notice what the XYZ bullet does that the other two don't:
- Names a *specific* result (60% reduction, 8h → 3.2h, 4 TB/day)
- Names a *specific* method (PySpark on AWS Glue)
- Is in *past tense, active voice* ("Cut" — strong verb)
- Is *bounded* — the reader knows exactly what was built, in what
  scale, with what result

That single bullet, in 6 seconds, tells the recruiter: this person
ships Python, knows Spark, has worked at the 4 TB/day scale, and
measures their work. **That is the entire point of the resume.**

---

## 2. The anatomy of a good DE resume

A good senior+ data engineering resume, top to bottom, in this
order:

| Section | Purpose | Length |
|---|---|---|
| **Header** | Name, location, email, LinkedIn, GitHub | 1-2 lines |
| **Positioning statement** | Who you are, what you do, what you want | 1 line |
| **Skills** | Keyword-dense, organized by category | 1 column, 4-6 lines |
| **Experience** | 3-4 jobs, 4-6 bullets each, all XYZ | Most of the page |
| **Selected projects** | 2-3 side projects / open source, with tech stack + outcome | 4-6 lines |
| **Education** | Degree(s), school, year. Optional: honors, GPA if strong | 1-2 lines |

That's the whole resume. No objective (the positioning statement
replaces it). No "References available upon request" (assumed). No
hobbies (unless directly relevant — e.g. you maintain a popular
open-source data tool). No "Skills" ratings (1-5 stars — recruiters
literally laugh at these).

### The positioning statement

A 1-line summary that does three things, in this order:

1. **Names your title** (matches the JD title family)
2. **Names your tech stack** (the 2-3 most relevant tools)
3. **Names the role you're targeting** (the one you're applying to)

Example for a senior DE applying to a staff data platform role:

> *Data engineer with 6 years building production Python + Scala
> pipelines on AWS and GCP, targeting staff data platform roles
> at infrastructure-scale companies.*

Example for an analytics engineer applying to a data engineer role:

> *Analytics engineer with 4 years on dbt + Snowflake + Looker,
> transitioning to data engineering to own end-to-end pipeline
> architecture.*

Both are 1 line. Both name the title, the stack, and the target
role. The recruiter reads it in 1 second and knows whether to
keep reading.

### The skills section

This is **not** a list of everything you've ever touched. It's a
**keyword-dense, 4-category block** that the ATS will scan, and
the recruiter will skim, looking for the JD's specific terms.

Standard categories for a DE resume:

- **Languages:** Python, SQL, Scala, Java, Go (pick 3-5)
- **Data:** Airflow, dbt, Spark, Kafka, Flink, Snowflake, BigQuery,
  Redshift, Databricks (pick 4-6)
- **Cloud:** AWS (S3, Glue, Lambda, Redshift), GCP (BigQuery,
  Dataflow, Pub/Sub), Azure (Data Factory, Synapse) (pick 1-2
  clouds, name the specific services)
- **Tooling:** Terraform, Docker, Kubernetes, Git, CI/CD, dbt,
  Looker, Tableau (pick 4-6)

**The rule:** every term in your skills section should also appear
in the JD of the role you're targeting (for a targeted resume) or
in *most* JDs in your target role family (for a master resume).
Skills that don't match JDs are wasted real estate.

---

## 3. Quantification: the rule of "at least one number per role"

Every job on your resume should have **at least one bullet with
a number**. Numbers are what the recruiter scans for in the
6-second pass. A resume with no numbers is, in their eyes, a
resume with no impact.

What "a number" means (in order of strength):

| Strength | Example |
|---|---|
| **Dollar impact** | Saved $1.2M/yr in cloud spend by retiring Redshift cluster |
| **Scale (volume)** | Pipeline processes 4 TB/day, 1.2B events/day |
| **Latency / time** | Cut dashboard load time from 8s to 320ms |
| **Percent improvement** | Reduced on-call pages by 70% via better monitoring |
| **Users / customers** | Dashboards used by 200+ stakeholders across 4 orgs |
| **Count of things** | Built 12 Airflow DAGs serving 6 product teams |
| **Duration** | Shipped in 3 months vs. initial 9-month estimate |

If you genuinely cannot quantify a bullet (rare, but happens for
new roles), use a *count* ("owned 8 pipelines") or a *time period*
("shipped within 3 months of joining"). Never use "many" or
"several" or "various" — those read as evasive.

---

## 4. Action verbs and tense

Every bullet starts with a **strong, past-tense action verb**:

- **Built, Shipped, Led, Owned, Designed, Migrated, Reduced, Cut,
  Doubled, Halved, Scaled, Refactored, Optimized, Automated,
  Instrumented, Mentored, Negotiated, Architected, Replaced,
  Launched**

Avoid:

- **Worked on, Helped with, Was responsible for, Participated in,
  Contributed to, Was involved in, Assisted with**

The "responsible for" family is the single biggest tell of a
mid-level resume. **"Responsible for" is duty-listing, not
accomplishment-stating.** Recruiters mentally translate "responsible
for X" to "did X sometimes, possibly under duress." Use "Owned,"
"Led," or "Built" instead.

Tense:

- **Past tense for previous roles** ("Built," "Shipped," "Led")
- **Present tense only for your current role** ("Building,"
  "Shipping," "Leading") — and even then, only if you're still
  actively doing it

---

## 5. The one-page rule

For senior+ data engineers (Senior, Staff, Principal), the resume
is **one page**. Period. There are very narrow exceptions:

- **Principal+ (L7/E7+)** — 2 pages acceptable if the page-2 content
  is publications, patents, or open-source maintainership.
- **Academic → industry transition** — 2 pages if you have a
  publication list that won't compress.
- **Contract / consulting with 10+ clients** — 2 pages if every
  client role is materially different.

If you're below principal, 1 page. The reason is not "resumes
should be short" — it's that **a 1-page resume forces you to
prioritize**. The act of cutting your 4-page master resume to 1
page is the act of figuring out what actually matters. Most
candidates discover that 70% of their 4-page resume is filler.

The format: **1 page, 9-11pt font, 0.5-0.7" margins, single
column.** Single column is critical for ATS parsing. Multi-column
layouts (especially with text wrapping in narrow columns) are the
#1 cause of ATS parse failures.

---

## 6. The 8 anti-patterns that get you filtered

In rough order of how often I see them:

| # | Anti-pattern | Why it's bad | Fix |
|---|---|---|---|
| 1 | **"Responsible for" bullets** | Reads as duty-listing, no impact | "Built," "Led," "Owned" + a number |
| 2 | **No numbers anywhere** | No impact signal in 6 seconds | At least 1 number per role, ideally per bullet |
| 3 | **"Objective" instead of positioning** | Recruiter doesn't care what you want | Replace with a 1-line positioning statement |
| 4 | **Skills list with 30+ tools** | Looks like a keyword dump, ATS-pessimizers reject | 4 categories, 4-6 tools each, JD-relevant |
| 5 | **Skills rated 1-5 stars** | Literally a joke to recruiters | Just list the skills, no ratings |
| 6 | **2+ page resume (senior)** | Signals inability to prioritize | Cut to 1 page; put the rest in a "selected projects" section |
| 7 | **Multi-column layout** | Breaks ATS parsing | Single column, no tables for content |
| 8 | **Embedded images / icons / graphs** | Doesn't parse, doesn't print | Plain text, with maybe a header line of links |

---

## 7. A worked example: a bad bullet → a good bullet

**Same engineer, same work, before and after.**

**Before (4 anti-patterns in one bullet):**

> *Responsible for helping with the migration of the company's
> data infrastructure to the cloud over the past year or so, which
> involved working with various teams and tools.*

**After (XYZ, action verb, specific, quantified):**

> *Led migration of 14 TB on-prem Hadoop cluster to AWS (S3 +
> Glue + Redshift) over 4 months, zero downtime, $280k/yr
> infrastructure savings.*

What's different:

- **Action verb** ("Led" not "Responsible for helping with")
- **Specific scope** (14 TB, Hadoop → AWS, the actual services)
- **Duration** (4 months, named, not "past year or so")
- **Outcome** ($280k/yr, zero downtime)
- **No filler** ("various teams and tools" is gone; replaced with
  the actual tech stack)

**One more:**

**Before:**

> *Built dashboards for the analytics team.*

**After:**

> *Built 8 Looker dashboards on top of dbt models, used by 200+
> stakeholders across Product, Marketing, and Finance; cut
> ad-hoc SQL requests by 40% in 6 months.*

Same engineer. Same work. The "after" version has 6 pieces of
information the "before" version doesn't: tool count, model
layer, user count, departments, downstream impact, time period.

---

## Try it

Pick the *worst* bullet on your current resume. Rewrite it using
the XYZ formula. Use this checklist:

- [ ] Starts with a strong action verb (past tense)
- [ ] Names the *what* (scope)
- [ ] Names a *measurable result* (number, percent, scale)
- [ ] Names the *how* (method, tech, specific action)
- [ ] Fits on one line (~120 characters max)

If your bullet is >2 lines, it's a paragraph — split it. If it
has no number, add one. If it starts with "responsible for" or
"worked on," change the verb.

Then pick your *best* bullet. Tighten it. See if you can cut
30% of the words without losing the meaning.
