# Changelog — aws_lambda_authorizer_course

All notable changes to this course material are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/) / dates in YYYY-MM-DD.

## [1.0.0] — 2026-10-10

### Added
- 5 sections, 25 lectures (L01–L25), 5 quizzes, 1 graded assignment.
- 3 working demos with offline unit tests:
  - `02_jwt_basics/code/jwt_verify.py` + `test_jwt_verify.py` (5 tests)
  - `03_simple_authorizer/code/token_authorizer.py` + `test_token_authorizer.py` (6 tests)
  - `04_policy_cache/code/param_authorizer.py` + `test_param_authorizer.py` (4 tests)
- 2 Mermaid diagrams:
  - `diagrams/lambda_authorizer_flow.mmd` — full request sequence
  - `diagrams/policy_cache_lifecycle.mmd` — cache populate / reuse / TTL
- 1 graded assignment (`assignments/assignment_1_lambda_authorizer.md`).
- 4 PDF placeholders in `downloads/`.
- `scripts/run_all_tests.py` — runs every `test_*.py` in sections 2/3/4.
- `scripts/bootstrap.sh` — POSIX-compatible venv + pip install.
- `requirements.txt` — boto3, botocore, moto[apigateway], pyjwt,
  cryptography, pytest.

### Conventions
- Author of every commit: **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**
- Lecture files: `<section>/lecture_scripts/L##_topic.md`
- Code files: `<section>/code/<topic>/<file>.py`
- Every lecture follows the structure: **Prereqs → Key terms → Lecture →
  Hands-on → Quiz prep → Further reading**
- Every section has a `README.md` summarizing the lectures
- Quizzes: 8–12 multiple-choice questions per section, answers in
  `<details><summary>Show answer</summary>…</details>` blocks
- Tests use `moto` 5+ and `pytest` 8+; all tests pass offline
- Free tier-eligible; no paid third-party SaaS dependencies
