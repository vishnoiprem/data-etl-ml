# Changelog — aws_lambda_course

All notable changes to this course material are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/) / dates in YYYY-MM-DD.

## [Unreleased]

### Added
- 16 sections, 88 lectures (L01–L81 + L31a + L36a–L36e + L44a + L82–L87),
  16 quizzes, 4 downloadable resources
- 7 graded assignments (`assignments/`) including the new
  `assignment_7_fci_monitor.md`
- 7 working serverless use cases (S3+Lambda+DynamoDB, API Gateway CRUD,
  Lambda Authorizer, Cognito Authorizer, API Keys/Usage Plan, Bedrock
  GenAI manufacturing use case, FCI Cluster Monitor)
- New **Section 15 — Enterprise Use Case 3: FCI Cluster Monitor**
  (L82–L87) — AWS Managed Microsoft AD + FSx for Windows + Lambda
  monitor + SNS + EventBridge + CloudWatch. Includes 6 lecture scripts,
  a `monitor_lambda/` Python module with 7 moto tests, a least-privilege
  IAM policy, a CloudFormation stack (`fci_monitor_stack.yaml`) with a
  `DryRun` parameter, a `deploy.sh`, and an `event_payloads/scheduled_event.json`
  fixture.
- New **L31a — Use Case 2 Part 3** (Section 8) — unified GET + DELETE
  Lambda with the full 4xx/5xx error model and CORS. Includes
  `api_pt3_handlers/` with 8 moto tests.
- New **L36a–L36e — Use Case 2 re-walked with a security lens** (Section 9)
  — five new lectures that re-walk Use Case 2 with Lambda Authorizer,
  Cognito Authorizer, and API Keys + Usage Plan layered on top. Includes
  `usecase2_with_auth/` working code (5 moto tests) and the extended
  section 9 quiz (10 → 13 questions).
- New **L44a — API Keys for Amazon Bedrock** (Section 10) — 12-minute
  lecture that generates, stores, and injects an Amazon Bedrock API key.
  Includes `api_keys_for_bedrock/` working code (7 moto tests).
- Extended `quizzes/section_8.md` to 12 questions, `section_9.md` to 13,
  `section_10.md` to 11. New `quizzes/section_15.md` (10 questions).
- `scripts/run_all_tests.py` now also covers section 15; runs each test
  file in its own subprocess to avoid pytest's same-name module
  collision in section 8.
- 102 pytest tests pass across 9 sections with `python scripts/run_all_tests.py`.

### Conventions
- Author of every commit: **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**
- Lecture files: `<section>/lecture_scripts/L##_topic.md`
- Code files: `<section>/code/<topic>/<file>.py` (or `.ts` for CDK)
- Every lecture follows the structure: **Prereqs → Key terms → Lecture →
  Hands-on → Quiz prep → Further reading**
- Every section has a `README.md` summarizing the lectures
- Quizzes: 10+ multiple-choice questions per section, answers in
  `<details><summary>Show answer</summary>…</details>` blocks
- Code uses `boto3` 1.34+, AWS CDK v2, AWS CloudFormation (JSON+YAML)
- Free tier-eligible; no paid third-party SaaS dependencies

### Conventions
- Author of every commit: **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**
- Lecture files: `<section>/lecture_scripts/L##_topic.md`
- Code files: `<section>/code/<topic>/<file>.py` (or `.ts` for CDK)
- Every lecture follows the structure: **Prereqs → Key terms → Lecture →
  Hands-on → Quiz prep → Further reading**
- Every section has a `README.md` summarizing the lectures
- Quizzes: 10 multiple-choice questions per section, answers in
  `<details><summary>Show answer</summary>…</details>` blocks
- Code uses `boto3` 1.34+, AWS CDK v2, AWS CloudFormation (JSON+YAML)
- Free tier-eligible; no paid third-party SaaS dependencies
