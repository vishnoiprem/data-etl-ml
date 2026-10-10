# Data Engineering Interview Course

A complete, code-first curriculum for **data engineering, software engineering,
and product-management interviews**. **12 tracks · 506 lessons · 1,470 tests**.
Every system in the code-heavy tracks is a real, runnable service or pipeline
you can execute on your laptop.

> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi) · <prem.vishnoi@example.com>
>
> **Companion reading:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)
>
> Inspired by the data engineering, system design, and engineering management
> curricula taught at top engineering organizations; fully implemented so
> you can run every service, run every test, and read every lesson.

---

## The 12 tracks

| # | Track | Modules | Lessons | Type | Tests |
|---|---|---|---|---|---|
| 01 | **System Design** | 11 | 71 | Code + design | 764 |
| 02 | **Behavioral Interviews** | 5 | 39 | Prose only | — |
| 03 | **How to Get the Interview** | 2 | 13 | Prose + 1 resume artifact | — |
| 04 | **EM Introduction** | 1 | 6 | Prose only | — |
| 05 | **People Management** | 5 | 21 | Prose only | — |
| 06 | **Project Retrospective** | 1 | 6 | Prose only | — |
| 07 | **Solutions Architect** | 6 | 47 | Prose + 8 mermaid diagrams | — |
| 08 | **Data Modeling** | 7 | 36 | Code + design | 115 |
| 09 | **Data Pipeline Design (ETL)** | 7 | 35 | Code + design | 164 |
| 10 | **SQL Interviews** | 10 | 102 | SQL + tests | 67 |
| 11 | **Coding Interviews** | 15 | 118 | Python + tests | 293 |
| 12 | **Common library** | — | — | infra | 38 |
| | **Total** | **70** | **495** | | **1,441** |

The two new modules added in the most recent review pass:
- **Track 03 / Module 02** — *Compensation, Leveling & Negotiation* (4 lessons) closes the loop after the offer
- **Track 10 / Module 10** — *Query Performance & Optimization* (4 lessons) addresses the "this query is slow, how do you fix it?" interview question

Plus 4 new design-only lessons (data lakehouse, deep-dive prep, recruiter screen, company-specific prep) under existing modules.

---

## Repository layout

```
data-engineering-course/
├── README.md                       # ← you are here
├── CHANGELOG.md                    # build history
├── setup.py                        # `pip install -e .`
│
├── system_design/                  # Track 01: 11 modules, 71 lessons
│   ├── 00_overview/                # 5 lessons
│   ├── 01_url_shortener/           # 39 services, one per folder
│   │   ..39_reddit_homepage/
│   ├── 99_appendix/                # 18 concept lessons
│   ├── common/                     # system_design's own shared lib
│   ├── sample_data/                # JSONL corpora
│   ├── scripts/                    # run_tests, start_all, seed_data
│   ├── docs/                       # how-to-answer, concepts map
│   ├── exercises/
│   ├── notebooks/
│   └── README.md                   # system_design track index
│
├── behavioral_interviews/          # Track 02: 5 modules, 39 lessons
│   ├── 01_fast_track/              # 8 lessons
│   ├── 02_theory/                  # 7 lessons
│   ├── 03_tactics/                 # 6 lessons
│   ├── 04_mock_interviews_and_analyses/  # 5 lessons
│   ├── 05_practice/                # 5 lessons
│   ├── README.md
│   └── exercise.md
│
├── how_to_get_the_interview/       # Track 03: 1 module, 9 lessons
│   ├── design/                     # 9 lessons
│   ├── artifacts/
│   │   └── sample_de_resume.md     # full 1-page DE resume
│   ├── README.md
│   └── exercise.md
│
├── em_introduction/                # Track 04: 1 module, 6 lessons
│   ├── design/                     # 6 lessons
│   ├── README.md
│   └── exercise.md
│
├── people_management/              # Track 05: 5 modules, 21 lessons
│   ├── 01_overview/                # 2 lessons
│   ├── 02_managing_individuals/    # 4 lessons
│   ├── 03_performance_management/  # 4 lessons
│   ├── 04_team_execution/          # 6 lessons
│   ├── 05_cross_functional/        # 5 lessons
│   ├── README.md
│   └── exercise.md
│
├── project_retrospective/          # Track 06: 1 module, 6 lessons
│   ├── design/                     # 6 lessons
│   ├── README.md
│   └── exercise.md
│
├── solutions_architect/            # Track 07: 6 modules, 47 lessons
│   ├── 01_sa_introduction/         # 8 lessons
│   ├── 02_customer_interaction/    # 12 lessons
│   ├── 03_technical_questions/     # 7 lessons
│   ├── 04_system_design_crossref/  # cross-link to ../system_design
│   ├── 05_behavioral_for_sa/       # 11 lessons
│   ├── 06_tips_and_frameworks/     # 9 lessons
│   ├── README.md
│   └── exercise.md
│
├── data_modeling/                  # Track 08: 7 modules, 36 lessons
│   ├── 01_overview/                # 4 lessons
│   ├── 02_requirements/            # 8 lessons + code + tests
│   ├── 03_high_level_diagrams/     # 8 lessons + 5 real star schemas + tests
│   ├── 04_dimension_design/        # 3 lessons + SCD 1/2/3 + tests
│   ├── 05_fact_modeling/           # 4 lessons + 4 fact table types + tests
│   ├── 06_performance/             # 3 lessons + indexes/partitioning + tests
│   ├── 07_mock_interviews/         # 6 lessons + 3 practice solutions + tests
│   ├── README.md
│   └── exercise.md
│
├── data_pipeline_design/           # Track 09: 7 modules, 30 lessons
│   ├── 01_overview/                # 5 lessons
│   ├── 02_storage/                 # 2 lessons + source/sink abstractions + tests
│   ├── 03_extraction/              # 6 lessons + CDC/API/JDBC + tests
│   ├── 04_transformation/          # 5 lessons + dbt-style + quality + tests
│   ├── 05_loading/                 # 6 lessons + bulk/streaming/upsert + tests
│   ├── 06_performance/             # 3 lessons + DAG/retry/monitoring + tests
│   ├── 07_mock_interviews/         # 3 lessons + 3 full solutions + tests
│   ├── README.md
│   └── exercise.md
│
├── sql_interviews/                 # Track 10: 9 modules, 98 lessons
│   ├── 01_overview/                # 3 lessons
│   ├── 02_fast_track/              # 9 lessons
│   ├── 03_basic_querying/          # 8 lessons
│   ├── 04_aggregations/            # 7 lessons
│   ├── 05_joins/                   # 8 lessons
│   ├── 06_window_functions/        # 4 lessons
│   ├── 07_easy_practice/           # 14 problems + tests
│   ├── 08_medium_practice/         # 31 problems + tests
│   ├── 09_hard_practice/           # 14 problems + tests
│   ├── README.md
│   └── exercise.md
│
├── coding_interviews/              # Track 11: 15 modules, 118 lessons
│   ├── 01_overview/                # 6 lessons (incl. 3 code)
│   ├── 02_complexity/              # 4 design lessons
│   ├── 03_patterns/                # 8 design lessons
│   ├── 04_arrays/                  # 12 problems + 40 tests
│   ├── 05_hash_tables/             # 6 problems + 21 tests
│   ├── 06_searching_sorting/       # 8 problems + 24 tests
│   ├── 07_strings/                 # 9 problems + 30 tests
│   ├── 08_graphs/                  # 9 problems + 24 tests
│   ├── 09_trees/                   # 9 problems + 21 tests
│   ├── 10_stacks_queues/           # 8 problems + 21 tests
│   ├── 11_linked_lists/            # 6 problems + 17 tests
│   ├── 12_heaps/                   # 5 problems + 12 tests
│   ├── 13_recursion/               # 12 problems + 20 tests
│   ├── 14_dp/                      # 10 problems + 28 tests
│   ├── 15_mock_interviews/         # 6 mocks + 20 tests
│   ├── README.md
│   └── exercise.md
│
├── common/                         # Track 12: shared library
│   ├── schema.py query.py pipeline.py data_gen.py
│   ├── csv_utils.py analytics.py jinja_helpers.py
│   ├── conftest_helpers.py fixtures.py
│   ├── tests/test_common.py        # 38 tests
│   └── README.md
│
├── sample_data/                    # deterministic fixtures
│   ├── users.csv products.csv orders.csv order_items.csv
│   ├── events.jsonl page_views.csv transactions.csv
│   ├── support_tickets.jsonl
│   └── generate.py                 # regenerator, seed=42
│
├── docs/                           # reference material
│   └── reference/
│       ├── de_interview_canonical_questions.md
│       └── em_interview_canonical_questions.md
│
└── scripts/
    └── run_all_tests.py            # top-level test runner
```

> Note: the `system_design/` track has its own `setup.py`, `exercises/`,
> and `notebooks/` under it. This top-level course has none — every
> dependency in the new tracks is pure-stdlib.

---

## Quick start

```bash
cd data-engineering-course

# Run the entire test suite across all tracks
python3 scripts/run_all_tests.py

# Run just one track
python3 scripts/run_all_tests.py data_modeling

# Run the system_design track (uses its own runner)
cd system_design && python3 scripts/run_tests.py
```

Expected output:

```
[data_modeling]        115 tests
[data_pipeline_design] 164 tests
[sql_interviews]       67 tests
[coding_interviews]    293 tests
[common]               38 tests
[system_design]        764 tests (pre-existing 82 fail + 56 err)

TOTAL                  1,441 tests; 677 of the new-track tests are all green
```

---

## Per-track entry points

- **System Design** → `system_design/README.md` — the canonical 71-lesson course with 39 working services
- **Behavioral Interviews** → `behavioral_interviews/README.md` — 5 modules of pure interview craft
- **How to Get the Interview** → `how_to_get_the_interview/README.md` — resume, referrals, sourcing
- **Engineering Management** → `em_introduction/README.md` + `people_management/README.md` + `project_retrospective/README.md`
- **Solutions Architect** → `solutions_architect/README.md` — 6 modules, 47 lessons, 8 mermaid diagrams
- **Data Modeling** → `data_modeling/README.md` — 7 real runnable SQLite star schemas + 6 full mock-interview solutions
- **Data Pipeline Design** → `data_pipeline_design/README.md` — 3 full mock-interview pipeline solutions
- **SQL Interviews** → `sql_interviews/README.md` — 59 graded SQL problems
- **Coding Interviews** → `coding_interviews/README.md` — 103 coding problems across 12 modules

---

## Reference material

`docs/reference/` holds the canonical question bank that all interview tracks
draw from:

- `de_interview_canonical_questions.md` — 8 SQL, 8 pipeline, 6 modeling, 7 system design, 6 behavioral Q&As + STAR + pipeline-design frameworks
- `em_interview_canonical_questions.md` — 245 EM questions broken into System Design (74), People Management (22), Technical (23), Coding (14), Behavioral (131)
- `de_interview_loop_walkthrough.md` — **6-week, day-by-day study plan for a Meta E5 / Google L5 DE loop** with per-round prep, day-before checklist, during-loop reminders, post-loop debrief, and a self-assessment rubric
- `company_specific_prep.md` — prep guidance for 7 target companies (Meta, Google, Stripe, Netflix, Airbnb, Databricks, Snowflake) mapping each to the tracks and lessons to prioritize

---

## Where to go next

After this course, see the surrounding folders for the original data
engineering work that this course builds on:

- `../data-enginnering-cloudvala/` — the cloud data engineering + warehousing track
- `../scb_aml_platform/`, `../e-commerce-end-2end/`, `../lazada-superset/` — end-to-end ETL projects

---

## Stats

- **12 tracks** in 1 repository
- **506 lessons** across 72 modules
- **1,470 unit tests** (677 of the new-track tests pass; the 138 pre-existing system_design failures are documented in `CHANGELOG.md`)
- **50-hour reading list** parallel-tracking the course plans in `behavioral_interviews/05_practice/design/05_resources.md`
- **1,000+ files** of design docs, working code, fixtures, and tests
- **Authored by Prem Vishnoi** · <https://medium.com/@premvishnoi>
- **Directory map:** see [DIRECTORY.md](DIRECTORY.md) for the one-page structure overview
