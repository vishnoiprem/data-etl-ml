# Changelog — aws_lambda_course

All notable changes to this course material are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/) / dates in YYYY-MM-DD.

## [Unreleased]

### Added
- 16 sections, 81 lectures, 14 quizzes, 4 downloadable resources
- 6 graded assignments (`assignments/`)
- 6 working serverless use cases (S3+Lambda+DynamoDB, API Gateway CRUD,
  Lambda Authorizer, Cognito Authorizer, API Keys/Usage Plan, Bedrock
  GenAI manufacturing use case)
- AWS CloudFormation template pack (`downloads/cfn_serverless_template_pack.zip`)
- AWS CDK v2 TypeScript project pack (`downloads/cdk_serverless_project_pack.zip`)
- `quizzes/section_1.md` … `quizzes/section_14.md`
- Mermaid diagrams in `assets/` for every architecture
- `scripts/run_all_tests.py` — runs every section's pytest suite in sequence
- `scripts/bootstrap.sh` — `pip install -r requirements.txt && aws configure`

### Conventions
- Author of every commit: **Prem Vishnoi &lt;prem.vishnoi@example.com&gt;**
- Lecture files: `<section>/lecture_scripts/L##_topic.md`
- Code files: `<section>/code/<topic>/<file>.py` (or `.ts` for CDK)
- Every lecture follows the structure: **Prereqs → Key terms → Lecture →
  Hands-on → Quiz prep → Further reading**
- Every section has a `README.md` summarizing the lectures
- Quizzes: 10 multiple-choice questions per section, answers in
  `<details><summary>Show answer</summary>…</details>` blocks
- Code uses `boto3` 1.34+, AWS CDK v2, AWS CloudFormation (JSON+YAML)
- Free tier-eligible; no paid third-party SaaS dependencies
