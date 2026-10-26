# Course directory map

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

A one-page map of the 12 tracks + 4 shared dirs in this course.
Read top-to-bottom for the recommended study order; read per-track
in any order once you know the foundations.

| # | Track | Path | Modules | What's inside |
|---|-------|------|---------|---------------|
| 1 | **System Design** | `system_design/` | 11 | 39 working Flask / FastAPI services + design docs + tests. The flagship track. |
| 2 | **Data Modeling** | `data_modeling/` | 7 | 5 working star/snowflake schemas in SQLite, SCD 1/2/3, 6 mock interviews. |
| 3 | **Data Pipeline Design** | `data_pipeline_design/` | 7 | 7 working ETL/ELT pipelines (Python), idempotency, retry, exactly-once. |
| 4 | **SQL Interviews** | `sql_interviews/` | 12 | 59 working SQL problems + Module 11 (2026 Meta CoderPad) + Module 12 (4 onsite rounds). |
| 5 | **Software Engineering Coding** | `coding_interviews/` | 15 | 118 Python algorithm solutions across 14 data structures + 6 mock interviews. |
| 6 | **Behavioral Interviews** | `behavioral_interviews/` | 5 | 14 lessons + 40-question taxonomy + 50-hour reading list. |
| 7 | **People Management** | `people_management/` | 5 | 5 modules on managing individuals, performance, execution, cross-functional. |
| 8 | **Solutions Architect** | `solutions_architect/` | 6 | 6 modules on the SA loop, customer interaction, system design crossref. |
| 9 | **EM Introduction** | `em_introduction/` | 1 | Engineering-management intro for IC -> EM transition. |
| 10 | **How to Get the Interview** | `how_to_get_the_interview/` | 1 | Resume, LinkedIn, referrals, compensation negotiation. |
| 11 | **Project Retrospective** | `project_retrospective/` | 1 | 6 lessons on "tell me about a project you shipped" answers. |
| 12 | **AWS Glue Masterclass** | `aws_glue_course/` | 11 | 78 lecture scripts (4h 11m), 4 downloadable resources, 11 quizzes, 6 assignments, 3 role plays. |

## Shared infrastructure (read-only, used by the tracks)

| Path | What |
|------|------|
| `common/` | The shared library: `QueryRunner` (SQLite test harness), `data_gen`, `pipeline` (ETL runner with idempotency). |
| `docs/reference/` | `company_specific_prep.md` — per-company interview-loop deep-dives (Meta, Google, Stripe, Netflix, Airbnb, Databricks, Snowflake, 2026 guides). |
| `sample_data/` | Tiny CSVs / JSONL fixtures used across tracks (`orders.csv`, `events.jsonl`, etc). |
| `scripts/` | `run_all_tests.py` — runs every track's tests in sequence. |

## Per-module layout (convention)

Every `XX_module_name/` follows:

```
XX_module_name/
├── module_overview.md     ← what the module is, who it's for
├── design/                ← lesson READMEs (one per concept)
├── code/                  ← working services / SQL / Python implementations
├── tests/                 ← unittest-based tests
├── notebooks/             ← Jupyter notebooks (where applicable)
└── exercise.md            ← capstone exercise prompt
```

`common/`, `sample_data/`, `docs/`, `scripts/` are the four shared dirs that don't follow the module layout.

## Top-level files

| File | What |
|------|------|
| `README.md` | The 1-page course overview. |
| `CHANGELOG.md` | The change log (one entry per session, dated). |
| `DIRECTORY.md` | This file. |
| `setup.py` | Installable package metadata for `common/`. |

## Running everything

```bash
cd data-engineering-course/

# Run every track's tests
python3 scripts/run_all_tests.py

# Run a single track
python3 scripts/run_all_tests.py sql_interviews
```

The `scripts/run_all_tests.py` wrapper walks the 6 test-bearing
tracks (`system_design`, `data_modeling`, `data_pipeline_design`,
`sql_interviews`, `coding_interviews`, `common`) in sequence and
prints a per-track summary.

## Adding a new module

1. Pick the track directory.
2. Use the next available `NN_short_name/` (zero-pad to 2 digits).
3. Follow the per-module layout above. Match the existing module style:
   `module_overview.md` at the top, `design/`, `code/`, `tests/`,
   `notebooks/`, `exercise.md` at the bottom.
4. Add a row to the track's `README.md` module count.
5. Add a `## YYYY-MM-DD` entry to `CHANGELOG.md`.
6. If the track has a master count in the top-level `README.md`,
   bump that too.
