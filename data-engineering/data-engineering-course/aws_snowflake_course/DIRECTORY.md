# DIRECTORY — Snowflake — The Complete Masterclass

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

Full file index. Top-level first, then per-section.

## Top level

```
README.md                       Course overview
SYLLABUS.md                     Authoritative L01–L192 map
DIRECTORY.md                    This file
CHANGELOG.md                    v1.0.0 release notes
requirements.txt                snowflake-connector-python, pytest, etc.
scripts/
  run_all_tests.py              Runs every test_*.py under each section/code
  bootstrap.sh                  venv + pip install + run tests
quizzes/                        19 section quizzes (section_1.md … section_19.md) + section_20.md
diagrams/                       6 mermaid .mmd files
downloads/                      3 PDF placeholders
assignments/                    4 hands-on assignments
code/                          Cross-section SQL utilities + Python tests
```

## Section folders (20 — 19 published + 1 extra-topics catch-all)

Each section follows:

```
0N_<topic>/
├── README.md              Section overview, lecture map
├── lecture_scripts/       L##_…md (follows SYLLABUS.md)
└── code/                  Per-section SQL + tests (where applicable)
```

| # | Section | Lectures | Working artifact |
|---|---|---|---|
| 01 | Introduction | L01–L04 | – |
| 02 | Getting started | L05–L14 | `setup_warehouse.sql` + 4 tests |
| 03 | Snowflake architecture | L15–L23 | `editions_pricing.sql` + 3 tests |
| 04 | Loading data | L24–L32 | `load_csv.sql` + 5 tests |
| 05 | Copy options | L33–L40 | `copy_options.sql` + 4 tests |
| 06 | Loading unstructured data | L41–L49 | `parse_json.sql` + `flatten_array.sql` |
| 07 | Performance optimization | L50–L58 | `clustering.sql` + 3 tests |
| 08 | Loading from AWS | L59–L65 | `aws_storage_integration.sql` + 3 tests |
| 09 | Loading from Azure | L66–L72 | `azure_integration.sql` + 3 tests |
| 10 | Loading from GCP | L73–L78 | `gcs_integration.sql` + 3 tests |
| 11 | Snowpipe | L79–L85 | `snowpipe_setup.sql` + 3 tests |
| 12 | Cortex AI & ML | L86–L99 | `cortex_ai_demo.sql` + 4 tests |
| 13 | Snowpipe for Azure | L100–L103 | – |
| 14 | Time Travel | L104–L109 | `time_travel_demo.sql` + 4 tests |
| 15 | Fail Safe | L110–L111 | – |
| 16 | Types of tables | L112–L115 | `table_types.sql` + 3 tests |
| 17 | Zero-Copy Cloning | L116–L121 | `clone_database.sql` + 3 tests |
| 18 | Data Sharing | L122–L132 | `create_share.sql` + 4 tests |
| 19 | Data Sampling | L133–L135 | `sampling.sql` + 3 tests |
| 20 | Extra topics (Tasks, Streams, MV, Masking, Roles, BI, Best Practices, Bonus) | L136–L192 | `masking_policy.sql` + `rbac_grants.sql` + `create_task.sql` + `create_stream.sql` + `create_mv.sql` (10 tests) |

**Total: 187–192 lecture scripts, 19 published quizzes + 1 extras
quiz, 19+ SQL demos + 5 Python test suites (≈60 tests), 6 diagrams,
4 assignments.**

## Cross-section code (`code/`)

```
code/
├── sql_utils.sql              Helper macros (CURRENT_ACCOUNT, etc.)
├── snowflake_session.py       Reusable connection helper
├── tests/
│   ├── conftest.py            pytest fixtures (mocked connector)
│   ├── test_sql_utils.py
│   ├── test_session.py
│   └── README.md
```

## File counts

| Bucket | Files |
|---|---|
| Top-level meta | 5 |
| Section READMEs | 20 |
| Lecture scripts | ~190 |
| Section quizzes | 20 |
| Working SQL demos | ~20 |
| Python test files | ~10 |
| Diagrams | 6 |
| Assignments | 4 |
| Scripts | 2 |
| Downloads | 3 |
| **Total** | **~280 files** |

---

**Prem Vishnoi** — pvishnoi@avilx.com