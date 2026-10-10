# 05 — The 50-Hour Reading List

> **Lesson 5 of 5 — Workshops** · ~10 min to plan, ~50 hours to complete
>
> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

The book list, the practice communities, the mock-interview
services, the long-term plan for staying sharp, **and the
50-hour reading schedule** that parallel-tracks the 8-week
course plan in the per-track READMEs.

Every reading in this list is cross-referenced to a specific
lesson in the course. Read the lesson, then read the matching
reading, then run the code, then come back. That rhythm is
what makes 50 hours of reading compound instead of evaporate.

---

## The 50-hour reading list at a glance

| Track | Hours | Resources |
|---|---|---|
| **Foundations** (data engineering, distributed systems) | 10 | 4 books, 3 papers |
| **SQL** | 6 | 2 books, 1 long-form blog series |
| **Pipelines** (ETL/ELT, batch, streaming) | 8 | 2 books, 3 case studies |
| **Data modeling** (star schema, SCD, dimensional) | 6 | 2 books, 4 articles |
| **System design** (the SE interview round) | 8 | 2 books, 5 case studies |
| **Behavioral** (the cross-cutting interview round) | 4 | 4 books, 2 HBR articles |
| **Career & leveling** (post-offer, growth) | 4 | 2 books, 2 long-form newsletters |
| **Cloud** (AWS / Azure / GCP / Snowflake / Databricks) | 4 | 4 whitepapers, 2 docs |
| **Total** | **50** | **22 books · 14 articles/papers · 14 case studies** |

The 50-hour budget assumes a working professional studying 6-8
hours per week over ~8 weeks, parallel to the per-track course
plans. Every reading is *replaceable* with another resource in
the same tier; the schedule is a default, not a contract.

---

## 1. Foundations — 10 hours

> **Pairs with:** `system_design/00_overview/`,
> `data_pipeline_design/01_overview/`,
> `data_modeling/01_overview/`.

The foundations track is the most leveraged 10 hours of the
whole list. Every other topic assumes you have the vocabulary
in these books.

### Tier 1: The must-reads (3 books, ~7 hours)

1. **"Designing Data-Intensive Applications" by Martin
   Kleppmann** *(~5 hrs)* — the single best book on the
   tradeoffs in modern data systems. **Read chapters 1, 5, 6,
   7, 8, 9, 11, 12.** Skip the others on first pass; come
   back for 2, 3, 4, 10, 13 in year 2. Pairs with
   `system_design/00_overview/` and the 18 concept lessons
   in `system_design/99_appendix/`.

2. **"Database Internals" by Alex Petrov** *(~1.5 hrs)* —
   read the B-tree chapters (3, 4, 5) and the LSM-tree
   chapter (7). The "why databases are slow" interview
   question collapses if you can talk fluently about
   page layout, write-ahead logging, and compaction.
   Pairs with `data_modeling/06_performance/`.

3. **"The Data Warehouse Toolkit" by Ralph Kimball &
   Margy Ross** *(~1 hr — just the dimensional chapters)* —
   read chapters 1-4 and 12-15. The interview answer to
   "design a star schema" is in chapter 2. Pairs with
   `data_modeling/03_high_level_diagrams/` and
   `04_dimension_design/`.

### Tier 2: The 3 papers (3 hours)

4. **"MapReduce: Simplified Data Processing on Large
   Clusters" by Dean & Ghemawat (2004)** *(~45 min)* —
   the paper that started the modern batch-processing era.
   Read for vocabulary: mapper, reducer, shuffle, partition
   function. Pairs with `data_pipeline_design/03_extraction/`.

5. **"Dynamo: Amazon's Highly Available Key-value Store"
   (2007)** *(~1 hr)* — read sections 1, 2, 4, 6. The
   "design a key-value store" interview question is a
   descendant of this paper. Pairs with
   `system_design/14_kv_store/`.

6. **"The Log-Structured Merge-Tree (LSM-Tree)" by
   O'Neil et al. (1996)** *(~1 hr)* — read sections 1,
   2, 3. The "why is my write-heavy DB fast" interview
   question lives here. Pairs with `data_modeling/06_performance/`.

---

## 2. SQL — 6 hours

> **Pairs with:** all of `sql_interviews/`.

### Tier 1: The must-reads (2 long-form series, ~3 hours)

1. **"Use The Index, Luke" by Markus Winand** *(~2 hrs)* —
   the single best free resource on SQL indexing. Read
   the chapters on B-trees, partial indexes, and
   index-only scans. The "EXPLAIN plan" interview
   question collapses if you can talk through a
   realistic plan. Pairs with
   `sql_interviews/10_query_performance/`.

2. **"SQL Performance Explained" by Markus Winand** *(~1 hr)* —
   the print version of Use The Index, Luke. Read the
   chapters on joins and on filtering. Pairs with
   `sql_interviews/05_joins/`.

### Tier 2: The blog (3 hours)

3. **"Modern SQL" by Markus Winand** *(~3 hrs)* — the free
   web version of his "Modern SQL" book. Read the
   chapters on window functions, CTEs, and
   `GROUPING SETS` / `ROLLUP` / `CUBE`. Pairs with
   `sql_interviews/06_window_functions/`.

---

## 3. Pipelines — 8 hours

> **Pairs with:** `data_pipeline_design/`.

### Tier 1: The must-reads (2 books, ~5 hours)

1. **"Fundamentals of Data Engineering" by Joe Reis &
   Matt Housley** *(~3 hrs — skim mode)* — read
   chapters 1-6 (the lifecycle and storage chapters).
   The "data engineering lifecycle" framing
   (ingest → transform → serve) is the *single
   most-cited* mental model in 2026 DE interviews.
   Pairs with `data_pipeline_design/01_overview/`.

2. **"Designing Event-Driven Systems" by Ben Stopford** *(~2 hrs)* —
   the free Confluent book. Read the chapters on
   event streams as a database, on change-data-capture,
   and on the dual-write problem. Pairs with
   `data_pipeline_design/03_extraction/03_cdc.md`.

### Tier 2: The case studies (3 hours)

3. **"How Netflix Knows What You Want Before You Do"**
   (free article) *(~45 min)* — read for the
   lakehouse framing and the cost-model discussion.
   Pairs with `data_pipeline_design/07_mock_interviews/`.

4. **"The Uber Big Data Platform" (free article,
   2024 refresh)** *(~1 hr)* — read for the
   real-time pipeline decisions and the trip-event
   schema. Pairs with
   `data_modeling/07_mock_interviews/design/31_ride_sharing.md`.

5. **"Stripe's Data Platform" (free article, 2024)** *(~45 min)* —
   read for the multi-tenant analytics patterns. Pairs
   with `data_pipeline_design/07_mock_interviews/`.

6. **"How Airbnb Built a Data Quality Framework" (free
   article)** *(~30 min)* — read for the 5 canonical
   DQ checks. Pairs with
   `data_pipeline_design/06_performance/design/28_data_quality.md`.

---

## 4. Data modeling — 6 hours

> **Pairs with:** all of `data_modeling/`.

### Tier 1: The must-reads (2 books, ~5 hours)

1. **"Star Schema: The Complete Reference" by Christopher
   Adamson** *(~3 hrs)* — read chapters 1-12. The
   interview answer to "design a star schema" is in
   chapter 2. Pairs with
   `data_modeling/03_high_level_diagrams/`.

2. **"The Data Warehouse Toolkit" (Kimball & Ross) — chapters
   5-11** *(~2 hrs)* — read the chapters on fact tables
   (transactional, periodic snapshot, accumulating
   snapshot, factless) and on conformed dimensions.
   Pairs with `data_modeling/05_fact_modeling/` and
   `04_dimension_design/`.

### Tier 2: The 4 articles (1 hour)

3. **"Slowly Changing Dimensions" (Kimball Group, 4 articles)**
   *(~30 min)* — read all four. Pairs with
   `data_modeling/04_dimension_design/`.

4. **"Conformed Dimensions" (Kimball Group)** *(~15 min)* —
   pairs with `data_modeling/04_dimension_design/`.

5. **"The 7 Components of a Good Dimension" (Kimball Group)**
   *(~15 min)* — pairs with
   `data_modeling/04_dimension_design/design/21_dimension_table_design.md`.

---

## 5. System design — 8 hours

> **Pairs with:** `system_design/`.

### Tier 1: The must-reads (2 books, ~5 hours)

1. **"System Design Interview, Vol 1" by Alex Xu** *(~3 hrs)* —
   read the chapters on rate limiter, consistent hashing,
   key-value store, and the unique-ID generator. These
   are the four most-asked system design problems in
   2026. Pairs with `system_design/00_overview/`.

2. **"System Design Interview, Vol 2" by Alex Xu** *(~2 hrs)* —
   read the chapters on publish-subscribe, news feed,
   and chat. Pairs with the corresponding services
   in `system_design/`.

### Tier 2: The case studies (3 hours)

3. **"Pinterest's Manhattan Recommendation System" (free
   article)** *(~30 min)* — pairs with
   `system_design/02_typeahead/`.

4. **"Dropbox's Magic Pocket" (free article)** *(~45 min)* —
   pairs with `system_design/18_dropbox/`.

5. **"Discord's Trillion-Message Storage" (free article,
   2024)** *(~45 min)* — read for the ScyllaDB + Cassandra
   cost-model decisions. Pairs with
   `system_design/26_messenger/`.

6. **"How Slack Built a Search System" (free article)** *(~30 min)* —
   pairs with `system_design/32_slack/`.

7. **"What Makes a Good System Design Interview" (free
   article, hellointerview.com)** *(~30 min)* — read this
   *last*, after you've done mock interviews. Pairs with
   `system_design/00_overview/`.

---

## 6. Behavioral — 4 hours

> **Pairs with:** all of `behavioral_interviews/`,
> `em_introduction/`, `people_management/`.

### Tier 1: The must-reads (2 books, ~2 hours)

1. **"Never Split the Difference" by Chris Voss** *(~1 hr)* —
   read the chapters on tactical empathy, on labeling
   emotions, and on the "calibrated questions" framework.
   The negotiation chapter doubles as the calibration
   chapter for compensation negotiation. Pairs with
   `how_to_get_the_interview/compensation/`.

2. **"An Elegant Puzzle: Systems of Engineering Management"
   by Will Larson** *(~1 hr)* — read the essays on
   "pull" vs "push," on hiring, and on the
   one-on-one. The senior-mindset framing transfers
   1:1 to behavioral interviews.

### Tier 2: The 2 should-reads (2 hours)

3. **"The Manager's Path" by Camille Fournier** *(~1 hr)* —
   read chapters 1-3 (the IC-to-lead transition). Even
   ICs benefit — it teaches the vocabulary of
   alignment and scope that the behavioral round
   tests for.

4. **"Quiet" by Susan Cain** *(~1 hr)* — read for the
   "introverts in meetings" framing, which is
   directly applicable to "tell me about a time
   you disagreed" answers.

### Tier 3: The 2 HBR articles (30 min)

5. **"The Leader Who Had No Title" (HBR, Robin Sharma)** *(~15 min)* —
   pairs with `em_introduction/`.

6. **"Managing Your Manager" (HBR)** *(~15 min)* — pairs
   with `08_difficult_team_members.md`.

---

## 7. Career & leveling — 4 hours

> **Pairs with:** `how_to_get_the_interview/`,
> `em_introduction/`, `people_management/`.

### Tier 1: The must-reads (2 long-form newsletters, ~3 hours)

1. **The Pragmatic Engineer Newsletter (Gergely Orosz) — DE
   issues** *(~2 hrs)* — read the 2024-2026 issues
   tagged "data" and "engineering levels." The
   comp-banding data is canonical. Pairs with
   `how_to_get_the_interview/compensation/design/04_comp_benchmarking.md`.

2. **levels.fyi — Data Engineer comp data** *(~1 hr)* —
   read the methodology page, then drill into 3
   target companies (Meta, Google, Stripe). Pairs
   with the comp module.

### Tier 2: The 2 books (1 hour)

3. **"The Pragmatic Programmer" by Hunt & Thomas — chapter
   on "invest regularly in your knowledge portfolio"** *(~30 min)* —
   pairs with `how_to_get_the_interview/`.

4. **"Staff Engineer" by Will Larson — the "beyond
   tech lead" essay** *(~30 min)* — pairs with
   `em_introduction/`.

---

## 8. Cloud — 4 hours

> **Pairs with:** all cloud-flavored lessons in
> `data_pipeline_design/`, `data_modeling/06_performance/`.

### Tier 1: The must-reads (4 whitepapers, ~3 hours)

1. **"Snowflake Architecture" (Snowflake whitepaper, free)** *(~45 min)* —
   read the storage and compute separation section.
   Pairs with `data_pipeline_design/02_storage/`.

2. **"Databricks Lakehouse Platform" (whitepaper, free)** *(~45 min)* —
   read the Delta Lake section. Pairs with
   `data_pipeline_design/02_storage/design/08_data_lakehouse_design.md`.

3. **"BigQuery Architecture" (Google whitepaper, free)** *(~45 min)* —
   read the columnar-storage and slot-model sections.
   Pairs with `sql_interviews/10_query_performance/`.

4. **"Redshift Architecture" (AWS whitepaper, free)** *(~30 min)* —
   read the sort-key and distribution-key sections.
   Pairs with `data_modeling/06_performance/`.

### Tier 2: The 2 docs (1 hour)

5. **"dbt Documentation — best practices"** *(~30 min)* — pairs
   with `data_pipeline_design/04_transformation/`.

6. **"Apache Airflow — production deployment guide"** *(~30 min)* —
   pairs with `data_pipeline_design/06_performance/`.

---

## The 8-week, 50-hour schedule

This schedule parallel-tracks the 4-week per-track course plans.
If you're studying 6-8 hours per week, this fits exactly.

| Week | Hours | Track | What to read |
|---|---|---|---|
| **1** | 6 | Foundations | DDIA ch 1, 5, 6, 7 + Dynamo paper |
| **2** | 6 | Foundations + SQL | DDIA ch 8, 9, 11, 12 + "Use The Index, Luke" intro |
| **3** | 6 | Pipelines | "Fundamentals of Data Engineering" ch 1-4 + Uber article |
| **4** | 6 | Pipelines + Modeling | "Fundamentals" ch 5-6 + Kimball ch 1-4 + Kimball Group SCD articles |
| **5** | 6 | Modeling + System Design | Kimball ch 5-11 + System Design Vol 1 (4 chapters) |
| **6** | 6 | System Design | System Design Vol 2 (3 chapters) + 3 case studies |
| **7** | 6 | Behavioral + Career | "Never Split the Difference" + "An Elegant Puzzle" + Pragmatic Engineer |
| **8** | 8 | Cloud + Career | 4 whitepapers + 2 docs + levels.fyi drill-down |
| **Total** | **50** | | |

If you fall behind, **drop the Tier 2 readings** (the
case studies, articles, and whitepapers) before dropping
the Tier 1 books. The books are the high-leverage reads.

---

## The practice communities

Behavioral interviewing is a *motor skill*. You need to
practice. These are the communities where senior engineers
practice together.

### Online communities

- **interviewing.io** — anonymous mock interviews with
  senior engineers from top companies. The most
  effective paid service for behavioral practice.
  Roughly $200-400 per session. Worth it for 2-3
  sessions before your real loop.

- **Pramp** — free peer mock interviews. The quality
  varies because the partners are random, but the
  practice itself is valuable. Best for early-stage
  prep, less useful right before the real loop.

- **IGotAnOffer** — paid service with structured prep
  and mock interviews. More expensive than
  interviewing.io but more structured.

### Local communities

- **Local meetups** — most cities have a "tech
  interview prep" meetup or a "women in tech"
  meetup that runs mock interview groups. Search
  Meetup.com for your city. The in-person practice
  is significantly better than online.

- **Friends** — the cheapest and most effective
  practice. 3 friends × 2 mock interviews each is
  6 practice rounds. Pick friends who are *more
  senior* than you, ideally at the level you're
  targeting.

### Internal communities

- **Your company's interview prep groups** — many
  larger companies have internal Slack channels or
  ERGs (employee resource groups) that run mock
  interviews. If your company has one, use it.

---

## The mock-interview services

If you want professional coaching, these are the
options, roughly in order of cost:

| Service | Cost | Best for |
|---|---|---|
| **Friends** | Free | General practice, low-pressure |
| **interviewing.io** | ~$300/session | Real senior interviewers, anonymous |
| **IGotAnOffer** | ~$500-1500 | Structured programs with coaching |
| **Pathrise** | % of salary | Full-job-search support, more than just interviews |
| **Private coaches** | ~$300-500/hr | Personalized 1:1 coaching, often ex-interviewers from top companies |

A 4-session package with interviewing.io or a private
coach is usually enough for behavioral rounds. Save
the rest of your prep budget for system design and
coding.

---

## The long-term plan

Behavioral interviewing is a skill you'll use for the
*next 20 years*. The investment compounds. Here's the
long-term plan:

### Year 1: Get good

- Build a 10-15 story story bank (this course)
- Do 3-5 mock interviews with friends
- Do 2-3 real interview loops (whether or not you
  want the job)
- Read at least 3 of the books in the Tier 1/2 list
- **Read at least 3 of the whitepapers in the Cloud
  section** — most DE candidates skip this and it
  shows in the system design round

### Year 2: Get calibrated

- Run mock interviews for *other* people
- Watch how senior interviewers score answers
- Notice the patterns in what gets a 4/4 and what
  gets a 2/4
- Add 3-5 more stories to your bank as you do more
  work
- Re-read the Tier 1 books you *skimmed* in year 1

### Year 3+: Get sharp

- Mentor other candidates
- Write about behavioral interviewing (blog,
  conference talk, internal doc)
- Re-read this course once a year
- Re-read at least one Tier 1 book from the list per year
- Add 1-2 case-study articles to your reading list
  each year (the canonical 2026 ones are in this
  file; new ones will appear each year)

The senior move is to make behavioral interviewing a
*practice*, not a *cram*. The engineers who ace the
behavioral round across their careers are the ones
who treat it like any other skill — continuously
maintained, never assumed.

---

## The cross-references

This course is a track in a larger data engineering
course. The other 12 tracks and how the reading list
ties to them:

- **system_design** — 71 lessons. The companion track.
  The "System design — 8 hours" section in this
  reading list is calibrated to the 39 services in
  `system_design/`.
- **data_modeling** — 39 lessons. The "Data modeling
  — 6 hours" section in this reading list is
  calibrated to the 5 working star schemas in
  `data_modeling/03_high_level_diagrams/code/star_schemas.py`.
- **data_pipeline_design** — 35 lessons. The
  "Pipelines — 8 hours" section in this reading
  list is calibrated to the 7 modules in
  `data_pipeline_design/`.
- **sql_interviews** — 102 lessons. The "SQL — 6 hours"
  section in this reading list is calibrated to the
  59 graded SQL problems in
  `sql_interviews/07-09_*`.
- **coding_interviews** — 118 lessons. No reading list
  here — coding is a *practice* skill, not a
  *reading* skill. Use LeetCode, not books.
- **behavioral_interviews** — 39 lessons (after this
  module's expansion). The "Behavioral — 4 hours"
  section in this reading list is calibrated to the
  4 mock interviews in
  `behavioral_interviews/04_mock_interviews_and_analyses/`.
- **em_introduction, people_management, project_retrospective** —
  33 lessons total. The "Behavioral — 4 hours"
  section covers most of the language these tracks
  test.
- **solutions_architect** — 47 lessons. The "Cloud —
  4 hours" section in this reading list is
  calibrated to the SA customer-interaction and
  technical-questions modules.
- **how_to_get_the_interview** — 13 lessons. The
  "Career & leveling — 4 hours" section in this
  reading list is calibrated to the comp-benchmarking
  lesson in `how_to_get_the_interview/compensation/`.
- **common** — 38 tests, shared infrastructure.
  No reading list, just code.

---

## The final word

The 50 hours of reading in this list is the *complement*
to the 495 lessons in the course. The lessons teach the
patterns; the reading teaches the *vocabulary*. You can
pass an interview with just the lessons; you can
*anchor a conversation* with the reading.

The senior move is to read *one* Tier 1 book per year,
forever. The compounding is enormous — five years from
now, you'll have read the canonical 15 Tier 1 books,
and your vocabulary in any technical conversation will
be visibly deeper than 95% of your peers. That's the
career compound interest.

Good luck.

— Prem Vishnoi

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
