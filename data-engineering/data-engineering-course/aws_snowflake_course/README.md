# Snowflake — The Complete Masterclass

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Format:** 28 sections, 192 lectures, 18h 39m total runtime
> **Repo convention:** sibling to the AWS course family (Lambda, EC2, Glue, EventBridge, Cognito, Lambda Authorizer, CDK v2, CloudWatch)

A hands-on, practice-oriented Snowflake course. Every section is paired
with a SQL demo (idempotent, runnable against the Snowflake free trial),
lecture quizzes, and at least one hands-on assignment. The 192 lectures
mirror the published course 1:1 in order so you can follow along
sequentially or jump to a specific topic.

## What you'll build

| Section | What you'll be able to do after |
|---|---|
| 01–04 | Navigate the Snowflake UI, set up warehouses, read pricing tables |
| 05–07 | Load CSV/JSON/Parquet from local + S3/Azure/GCS using `COPY INTO` |
| 08–10 | Configure storage integrations for AWS, Azure, and GCS |
| 11–15 | Use Snowpipe, Cortex AI (Functions, Search, Analyst), ML + Notebooks |
| 16–19 | Time Travel, Fail-safe, Zero-Copy Cloning, Data Sharing |
| 20–22 | Sampling, Tasks, Streams (CDC) |
| 23–25 | Materialized views, Data Masking, Roles deep-dive |
| 26–28 | BI tool integration, Best practices, Bonus content |

## Working artifacts (every section has one)

| Section | Working artifact | Tests |
|---|---|---|
| 04 | `setup_warehouse.sql` (idempotent warehouse create) | 3 |
| 05 | `load_csv.sql` + `test_load_csv.py` (mock Snowflake) | 5 |
| 06 | `copy_options_demo.sql` (ON_ERROR, FORCE, SIZE_LIMIT, …) | 4 |
| 07 | `parse_json.sql` + `flatten_array.sql` | 4 |
| 08 | `aws_storage_integration.sql` + terraform-style script | 3 |
| 11 | `unload_snowpipe.sql` (Snowpipe setup) | 3 |
| 12 | `cortex_ai_demo.sql` (AI SQL functions) | 4 |
| 14 | `time_travel_demo.sql` + `undrop.sql` | 4 |
| 17 | `clone_database.sql` (zero-copy clone) | 3 |
| 18 | `create_share.sql` + reader account | 4 |
| 20 | `create_task.sql` (cron + tree) | 3 |
| 21 | `create_stream.sql` (CDC stream) | 4 |
| 22 | `create_materialized_view.sql` | 3 |
| 23 | `masking_policy.sql` | 3 |
| 24 | `rbac_grants.sql` | 4 |

All SQL files are idempotent and runnable against the Snowflake free
trial. The Python tests use the `snowflake-connector-python` driver
against a mocked Snowflake via `pytest-mock` so they pass without a
live account (see `tests/README.md`).

## Repo layout

```
aws_snowflake_course/
├── README.md, SYLLABUS.md, DIRECTORY.md, CHANGELOG.md
├── requirements.txt
├── lecture_scripts/         ← only cross-section lecture scripts
├── diagrams/                ← 6 mermaid .mmd files
├── downloads/               ← 3 PDF slide placeholders
├── scripts/                 ← run_all_tests.py + bootstrap.sh
├── quizzes/                 ← 28 section quizzes (8–12 Qs each)
├── assignments/             ← 4 hands-on assignments
├── code/                    ← cross-section SQL utilities + tests
└── 0N_<section>/
    ├── README.md
    ├── lecture_scripts/     ← L01_…md … L##_…md
    └── code/                ← per-section SQL + tests
```

## Running the SQL

The course assumes you have a Snowflake account (free trial is fine).
Set these env vars and any SQL file will work:

```bash
export SNOWFLAKE_USER=your_user
export SNOWFLAKE_PASSWORD=your_password
export SNOWFLAKE_ACCOUNT=xy12345.us-east-1
export SNOWFLAKE_WAREHOUSE=COMPUTE_WH
export SNOWFLAKE_DATABASE=DEMO_DB
export SNOWFLAKE_SCHEMA=PUBLIC
```

Or run the local tests:

```bash
cd aws_snowflake_course
pip install -r requirements.txt
python3 scripts/run_all_tests.py
```

## Not affiliated with Snowflake Inc.

This is a community open-source companion to a published Udemy course.
Not provided by, affiliated with, or sponsored by Snowflake Inc.

---

**Prem Vishnoi** — pvishnoi@avilx.com
