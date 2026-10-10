# Data Pipeline Design (ETL) — A Practical Guide for Data Engineers

> **31 lessons · 7 modules · 3 videos · ~15 hours of focused practice**
>
> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi) · <prem.vishnoi@example.com>
>
> **Companion articles:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

A practical guide to the most underrated interview round in the data
engineering loop: **the data pipeline / ETL design interview**. This is
the round where you draw boxes and arrows on a whiteboard and convince
the interviewer you can build a system that moves data reliably from
point A to point B at scale.

This track mirrors the structure of `system_design/` and `behavioral_interviews/`.
Each module has a `design/` folder with 1-6 lesson files, a `code/`
folder with a working implementation, and a `tests/` folder that you
actually run.

---

## What's in this track

**Design + working code.** Every lesson is a Markdown file you read
*and* a Python module you run. The lessons are written as the
interview answer — what you'd say if the interviewer asked you
"design Netflix's clickstream pipeline" and you had 30 minutes.

**Pattern-based.** The eight canonical pipeline questions (document
processing, lakehouse vs warehouse, Medallion, Delta Lake, Hadoop vs
PySpark, scheduling, failure handling, Netflix clickstream) are
*the* spine. They're in `docs/reference/de_interview_canonical_questions.md`
and every module builds toward them.

**Calibrated for senior+.** The audience is engineers interviewing for
**L5/L6 (Google), Senior/Staff (most), Staff/Principal (Netflix, Stripe)**.
Junior candidates will still get value, but the framing is "be seen as a
senior data engineer".

---

## The 7 modules

| # | Module | Lessons | What you'll get out of it |
|---|---|---|---|
| [01](01_overview/) | **Overview** | 5 | Mental model, framework, rubric, tool landscape, ETL vs ELT. Design-only. |
| [02](02_storage/) | **Storage** | 2 | Sources (OLTP, APIs, files, streams) + destinations (warehouse, lakehouse, serving). |
| [03](03_extraction/) | **Extraction** | 6 | Full vs incremental, CDC, API polling, JDBC, schema evolution, backpressure. |
| [04](04_transformation/) | **Transformation** | 5 | dbt-style SQL, Python/Spark transforms, joins, data quality, SCD2. |
| [05](05_loading/) | **Loading** | 6 | Bulk loading, streaming, upsert, partitioning, idempotency, lakehouse. |
| [06](06_performance/) | **Performance & Fault Tolerance** | 4 | Orchestration, retry/DLQ, monitoring & SLA, data quality. |
| [07](07_mock_interviews/) | **Mock Interviews** | 3 | Three full pipeline designs — Netflix clickstream, doc processing, banking CDC. |

**Total: 31 lessons.**

---

## How to use this track

**Week 1 — Overview + Storage (4-6 hours).** Read Module 01 in one
sitting. Don't skip the rubric lesson (Lesson 03) — it's the most
re-readable lesson in the track. Move to Module 02 to ground the
abstract concepts in concrete sources/sinks.

**Week 2 — Extraction + Transformation (8-10 hours).** Modules 03 and
04 are the meat. Read each lesson, then *run* the corresponding code
in `code/`. Read the tests — they're a worked example of the design.

**Week 3 — Loading + Performance (6-8 hours).** Modules 05 and 06
cover the operational side. The retry + DLQ + monitoring module is
often the difference between a "junior" answer and a "senior" answer.

**Week 4 — Mock Interviews (3-4 hours).** Module 07. Read each mock
interview *twice*. First time for the architecture, second time for
the explanation. Then do `exercise.md` to design + build a small
pipeline from scratch.

By week 4 you should be able to draw any of the three mock-interview
pipelines in 30-45 minutes and explain every box.

---

## Layout

```
data_pipeline_design/
├── README.md                      # ← you are here
├── 01_overview/                   design/ only, 5 lessons
├── 02_storage/                    design/, code/, tests/
├── 03_extraction/                 design/, code/, tests/
├── 04_transformation/             design/, code/, tests/
├── 05_loading/                    design/, code/, tests/
├── 06_performance/                design/, code/, tests/
├── 07_mock_interviews/            design/, code/, tests/
└── exercise.md                    # capstone: design + build a small pipeline
```

---

## A note on the prose-first format

Each lesson is a Markdown file. Open the corresponding `code/` file
side-by-side. The code is the *implementation* of what the lesson
describes; the lesson is the *interview answer* for what the code
demonstrates. Together they form a complete unit.

---

## Running the test suite

```bash
python3 scripts/run_all_tests.py data_pipeline_design   # this track
python3 scripts/run_all_tests.py                        # all tracks
```

The script discovers every `tests/test_*.py` file, runs it with
`unittest.TextTestRunner`, and prints a summary. Exit code is `0`
only if every test passes.

---

## Where to go next

- For service-design patterns: see `system_design/`.
- For SQL interview prep: see `sql_interviews/`.
- For behavioral: see `behavioral_interviews/`.
- Author articles: <https://medium.com/@premvishnoi>
