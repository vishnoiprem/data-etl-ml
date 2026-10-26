# Changelog — aws_cloudwatch_course

All notable changes to this course material are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/) / dates in YYYY-MM-DD.

## [1.0.0] — 2026-10-10

### Added
- Initial release: **7 sections, 35 lectures (L01–L35)**, ~6h total
- 7 quizzes (`quizzes/section_1.md` … `section_7.md`), 8–10 questions each
- 5 working `boto3 + moto` demos:
  - `02_metrics/code/put_metric_data.py` (+ 5 moto tests)
  - `03_logs/code/create_log_group.py` (+ 5 moto tests)
  - `04_alarms/code/put_metric_alarm.py` (+ 5 moto tests)
  - `05_dashboards/code/create_dashboard.py` (+ 4 moto tests)
  - `06_logs_insights_subs/code/subscription_filter.py` (+ 4 moto tests)
- 3 Mermaid diagrams (`diagrams/`)
- 1 graded assignment: `assignments/assignment_1_slo_dashboard.md`
- `scripts/run_all_tests.py` — runs every section's tests
- `scripts/bootstrap.sh` — venv + requirements setup
- 3 PDF placeholders under `downloads/`

### Conventions
- Author of every commit: **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**
- Lecture files: `<section>/lecture_scripts/L##_topic.md`
- Code files: `<section>/code/<demo>/<script>.py` and `test_<script>.py`
- Every lecture follows the structure: **Prereqs → Key terms → Lecture →
  Hands-on → Quiz prep → Further reading**
- Every section has a `README.md` summarizing the lectures
- Quizzes: 8–10 multiple-choice questions per section, answers in
  `<details><summary>Show answer</summary>…</details>` blocks
- Code uses `boto3` 1.34+, `moto[cloudwatch,logs]` 5+, `pytest` 8+
- Free tier-eligible; no paid third-party SaaS dependencies
