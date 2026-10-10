# dbt + Snowflake — Analytics Engineer Certification Prep

> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi) · <pvishnoi@avilx.com>

A complete, code-first curriculum for the **dbt Analytics Engineer
Certification exam**. **19 sections · 133 lectures · 11h 57m · 19
quizzes · 6 diagrams · 4 assignments · ~50 dbt-project files**.

The course is **project-based**: every section maps to an official
dbt exam objective, and we build a real dbt project end-to-end on top
of a realistic **Ethereum blockchain dataset** in **Snowflake**.

> **What you'll build:** a runnable dbt project (`dbt_project/`)
> covering staging models, marts, incremental models, macros,
> sources, packages, tests, snapshots, contracts, versions, model
> access, Python models, a CI/CD pipeline, plus a Slim CI workflow.

> **Tested end-to-end** without a Snowflake account: every `.sql`,
> `.yml`, `.py`, and `.csv` artifact is exercised by `pytest` via
> Jinja rendering + `dbt parse`.

---

## Why this course exists

When I personally passed the dbt Analytics Engineer exam, I felt
frustrated by how most resources approach it: lots of isolated quiz
questions, not enough explanation of **why** things work the way they
do in dbt. This course is my attempt to fix that.

Instead of random examples, we work through a real dbt project
end-to-end, built on top of Ethereum blockchain data. Not because
this is about crypto (it's not), but because it's a rich, realistic
dataset that lets us explore dbt concepts properly.

Each section of the course maps directly to the official dbt exam
objectives, so everything you learn has a clear purpose.

---

## The 19 sections

| # | Section | Lectures | Working artifact |
|---|---|---|---|
| 1 | Welcome, Setup, dbt init | L01–L16 | `dbt_project.yml`, `models/staging/_sources.yml` |
| 2 | Transactions: fields, categorization, daily activity, stablecoins | L17–L22 | `models/marts/transactions.sql` |
| 3 | Object dependencies, staging shielding, materializations, incremental, ephemeral | L23–L29 | `models/marts/activity.sql` (incremental merge) |
| 4 | Practice quiz — materializations | L30 | – |
| 5 | DRY principles, macros | L31–L39 | `macros/log_macro.sql`, `macros/dry_refactor.sql` |
| 6 | dbt run, test, docs, seed, compile/build, clean DAGs | L40–L46 | `seeds/static_categories.csv`, `models/marts/dag_demo.sql` |
| 7 | dbt_project.yml configs: YAML, hierarchical, schemas, variables, alias | L47–L53 | `dbt_project.yml` (extended) |
| 8 | Sources + dbt packages (codegen, dbt_utils, audit_helper, Git) | L54–L57 | `packages.yml` |
| 9 | Git basics, branching, PRs, merge conflicts, docs | L58–L61 | – |
| 10 | Python models + execution constraints | L62–L63 | `models/marts/fraud_score.py` |
| 11 | Grants: Snowflake behavior, dbt grants, post-hooks, project-level | L64–L66 | `models/marts/_grants.yml` |
| 12 | Practice quiz — developing dbt models | L67 | – |
| 13 | Environments + contracts | L68–L70 | `models/marts/_contracts.yml` |
| 14 | Versions: setup + latest view, deprecation dates + warnings | L71–L72 | `models/marts/_versions.yml` |
| 15 | Model access: groups, private vs protected, fraud domain | L73–L76 | `models/marts/_access.yml` |
| 16 | Debugging: logs, debug flags, runtime/compilation/database errors | L77–L83 | `macros/debug_helper.sql` |
| 17 | State: manifest, run_results, new, result-based selectors, dbt retry | L84–L88 | `selectors.yml` |
| 18 | Managing data pipelines — CI pipelines (defer, clone, Slim CI, continuous deployment, cleanup) | L89–L100 | `dbt_project.yml` selectors, `.github/workflows/dbt_ci.yml` |
| 19 | Tests (singular, generic, custom, source, unit, severity), dbt docs, exposures, source freshness, advanced topics, snapshots (timestamp + check), microbatch, --sample, final exam | L101–L131 | `tests/generic/test_positive_value.sql`, `snapshots/transactions_snapshot.sql` |

---

## Repo layout

```
aws_snowflake_dbt_course/
├── README.md                          ← this file
├── SYLLABUS.md                        ← authoritative L-ID ↔ file map
├── DIRECTORY.md                       ← full file index
├── CHANGELOG.md                       ← v1.0 entry
├── requirements.txt                   ← dbt-core, dbt-snowflake, jinja2, pytest
├── conftest.py                        ← strip_line_comments + render_jinja helpers
├── dbt_project/                       ← runnable dbt project (one for the whole course)
│   ├── dbt_project.yml                ← materialization precedence, vars, selectors
│   ├── profiles.yml                   ← Snowflake profile (target = mock)
│   ├── packages.yml                   ← codegen, dbt_utils, audit_helper
│   ├── models/
│   │   ├── staging/                   ← _sources.yml + stg_ethereum__*
│   │   └── marts/                     ← transactions, activity, stablecoin, fraud_score, dag_demo
│   ├── macros/                        ← log_macro, dry_refactor, debug_helper
│   ├── seeds/                         ← static_categories.csv
│   ├── snapshots/                     ← transactions_snapshot.sql
│   ├── tests/                         ← generic/test_positive_value + unit/test_fraud_score_unit
│   └── selectors.yml                  ← result-based + state-based
├── <NN_section>/
│   ├── README.md                      ← section overview + lecture table
│   ├── lecture_scripts/               ← Lxx_title.md
│   └── code/                          ← (per-section isolated demos + tests)
├── quizzes/section_1.md … section_19.md
├── assignments/                       ← 4 graded assignments
├── diagrams/                          ← 6 mermaid diagrams
├── downloads/                         ← PDF slide placeholders
└── scripts/
    ├── run_all_tests.py               ← runs every test_*.py + dbt parse smoke test
    └── bootstrap.sh                   ← venv + pip + dbt parse
```

---

## Setup

```bash
cd aws_snowflake_dbt_course
bash scripts/bootstrap.sh        # create venv, pip install, run dbt parse
python scripts/run_all_tests.py  # run every pytest suite
```

Expected: `ALL PASS` (~50 tests).

> **Snowflake account:** you don't need one to read this course. The
> pytest suites use Jinja rendering + `dbt parse` against a mock
> target so everything runs locally. To run the project against real
> Snowflake (for the hands-on exercises), edit
> `dbt_project/profiles.yml` with your account, user, and database.
>
> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi) ·
> <pvishnoi@avilx.com>

**Prem Vishnoi** — pvishnoi@avilx.com
