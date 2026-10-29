# DIRECTORY — dbt + Snowflake Analytics Engineering Cert Prep

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

A one-page structural map of the course. For the lecture-to-file
cross-reference use [`SYLLABUS.md`](SYLLABUS.md).

```
aws_snowflake_dbt_course/
├── README.md
├── SYLLABUS.md
├── DIRECTORY.md        ← you are here
├── CHANGELOG.md
├── requirements.txt
├── conftest.py
├── scripts/
│   ├── run_all_tests.py
│   └── bootstrap.sh
├── downloads/
│   └── slides_placeholder.md
├── diagrams/                       ← 6 mermaid .mmd files
├── assignments/                    ← 4 graded assignments
├── quizzes/                        ← 19 quiz files (section_1.md … section_19.md)
├── dbt_project/                    ← shared runnable dbt project (built lecture by lecture)
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── packages.yml
│   ├── selectors.yml
│   ├── models/
│   │   ├── staging/                ← _sources.yml + stg_ethereum__*
│   │   └── marts/                  ← transactions, activity, stablecoin_activity, fraud_score.py, dag_demo + 5 .yml files
│   ├── macros/                     ← log_macro, dry_refactor, debug_helper
│   ├── seeds/                      ← static_categories.csv
│   ├── snapshots/                  ← transactions_snapshot.sql
│   └── tests/
│       ├── generic/                ← test_positive_value.sql
│       └── unit/                   ← test_fraud_score_unit.yml
└── <NN_section>/
    ├── README.md                   ← 19 section READMEs
    ├── lecture_scripts/            ← 133 lecture scripts (L01..L133)
    └── code/                       ← isolated demos + test_*.py
```

**Convention notes:**

- Each section is numbered `NN_section` (zero-padded to 2 digits, e.g.
  `01_section`, `02_section`, … `19_section`). Renumbering a section
  means renaming the folder AND updating every cross-reference in the
  section's README + lectures + quiz.
- Each section has a `README.md` that lists its lectures, summary,
  key concepts, and "what comes next".
- Each `lecture_scripts/` directory contains `L##_<slug>.md` files
  with frontmatter (`l_id`, `title`, `duration`, `prereqs`,
  `downloads`).
- Each section that introduces a *new* dbt artifact has a `code/`
  directory with a stand-alone demo + a `test_*.py` that asserts on
  the rendered Jinja.
- The shared `dbt_project/` grows as lectures introduce new files.
  Every section that adds a model/macro/test/snapshot adds it to
  `dbt_project/` (so the final project is the artifact).
