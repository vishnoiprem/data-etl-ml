# Changelog

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

All notable changes to this course are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2026-10-10 — Initial release

### Added
- Top-level `README.md`, `SYLLABUS.md`, `DIRECTORY.md`, `CHANGELOG.md`, `requirements.txt`, `conftest.py`.
- `scripts/run_all_tests.py` and `scripts/bootstrap.sh`.
- `downloads/slides_placeholder.md` (real slide PDFs live on the instructor's drive).
- `dbt_project/` — a complete, runnable dbt project spanning the full 19-section curriculum, with:
  - `dbt_project.yml` (materialization precedence, vars, selectors).
  - `profiles.yml` (mock target — no live Snowflake required).
  - `packages.yml` (codegen, dbt_utils, audit_helper).
  - `models/staging/_sources.yml` + 2 staging models.
  - `models/marts/` — 10 mart models including incremental merge, Python dbt model, contracts, versions, access, grants, microbatch.
  - `macros/` — 3 Jinja macros (logging, DRY refactor, debug helper).
  - `seeds/static_categories.csv`.
  - `snapshots/transactions_snapshot.sql` (timestamp strategy).
  - `tests/generic/test_positive_value.sql` + `tests/unit/test_fraud_score_unit.yml`.
  - `selectors.yml` (result-based + state-based).
- 19 section folders (`01_section/` … `19_section/`), each with `README.md`, `lecture_scripts/`, and `code/`.
- 133 lecture scripts (`L01_welcome.md` … `L133_stay_connected.md`).
- 19 quizzes (`quizzes/section_1.md` … `section_19.md`), 8-12 questions each, hidden-answer pattern.
- 6 mermaid diagrams in `diagrams/`.
- 4 graded assignments in `assignments/`.
- ~15 pytest test files exercising every per-section code demo + the shared `dbt_project/` (`dbt parse` smoke test + Jinja render assertions + author signature + idempotency).
- Total: ~244 files.
