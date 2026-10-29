# Changelog — aws_cdk_v2_course

All notable changes to this course material are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/) / dates in YYYY-MM-DD.

## [1.0.0] — 2026-10-10

### Added
- **6 sections, 30 lectures (L01–L30)** total, ~6h of material.
  - Section 1 — Foundations (L01–L04)
  - Section 2 — App, Stack, Construct — the L1/L2/L3 model (L05–L10)
  - Section 3 — Building with CDK: Lambda, API Gateway, S3, IAM (L11–L15)
  - Section 4 — AppSync + Step Functions + EventBridge (L16–L20)
  - Section 5 — Testing, snapshots, assertions, CI/CD (L21–L25)
  - Section 6 — Real-world patterns: multi-stack, cross-region,
    `cdk.context`, escape hatches, Aspects (L26–L30)
- **3 working TypeScript CDK v2 projects** in `<section>/code/`:
  - `02_app_stack_construct/code/hello-cdk/` — minimal S3 bucket stack
    + output + Jest test
  - `03_building_with_cdk/code/lambda-api/` — Lambda + API Gateway REST
    + S3 asset bucket + IAM role + Jest test
  - `04_appsync_stepfunctions/code/app-sync-sfn/` — AppSync GraphQL API
    + resolver Lambda + Step Functions state machine + Jest test
- **6 quizzes** (`quizzes/section_1.md` … `quizzes/section_6.md`), 8–12
  questions each, answers hidden in `<details>` blocks.
- **3 mermaid diagrams** in `diagrams/` — construct tree, synth/deploy
  sequence, multi-stack pattern.
- **`scripts/run_all_tests.py`** — runs `npm test` in each project
  (gracefully skips when `npm` is missing).
- **`scripts/bootstrap.sh`** — installs Node deps and runs tests.
- **`assignments/assignment_1_multi_stack.md`** — graded multi-stack
  extension exercise.
- **`downloads/README.md`** — placeholder for 4 PDF/zip resources.

### Conventions
- Author: **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**
- Lecture files: `<section>/lecture_scripts/L##_topic.md`
- Code: `<section>/code/<project>/{bin,lib,test,package.json,tsconfig.json,cdk.json}`
- Tests: Jest with `aws-cdk-lib/assertions` and `Template.fromStack`
- Every lecture follows **Prereqs → Key terms → Lecture → Hands-on →
  Quiz prep → Further reading**
- Every section has a `README.md` summarizing the lectures
- L1 vs L2 vs L3: prefer L2; escape-hatch to L1 only when an L2 doesn't
  exist (documented in L09)
- Free tier-eligible; no paid third-party SaaS dependencies
