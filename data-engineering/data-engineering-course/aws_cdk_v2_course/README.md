# AWS CDK v2 — Crash Course

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Format:** **6 sections, 30 lectures (L01–L30), ~6h total**. 3 working TypeScript CDK projects. 6 quizzes. 1 graded assignment.

This is the local companion repo for the **AWS CDK v2 Crash Course**. The
lecture-to-file map in `SYLLABUS.md` is authoritative. Every lecture is a
self-contained `.md` file under `<section>/lecture_scripts/`, and every
working project lives under `<section>/code/<project>/`.

## What you'll learn

- **What IaC is** and why CDK is the most productive way to write it on
  AWS in 2026 (Section 1).
- **The CDK construct model** — App → Stack → L1/L2/L3 constructs — and
  how `cdk synth` turns TypeScript into a CloudFormation template
  (Section 2).
- **Building real stacks** with Lambda, API Gateway, S3, and IAM using
  L2 constructs (Section 3).
- **AppSync, Step Functions, and EventBridge** with CDK — the three
  most common serverless orchestration patterns (Section 4).
- **Testing, snapshots, assertions, and CI/CD** — the fine line between
  "synth succeeded" and "this stack will deploy" (Section 5).
- **Real-world patterns** — multi-stack apps, cross-region stacks, CDK
  context, escape hatches, and Aspect-based compliance (Section 6).

## What you build

| # | Working artifact | Section | L-IDs |
|---|---|---|---|
| 1 | `hello-cdk/` — minimal S3 bucket stack + output | 2 | L05–L10 |
| 2 | `lambda-api/` — Lambda + API Gateway + S3 + IAM | 3 | L11–L15 |
| 3 | `app-sync-sfn/` — AppSync + Step Functions + resolver Lambda | 4 | L16–L20 |
| 4 | CDK test/snapshot demo (Jest + `Template.fromStack`) | 5 | L21–L25 |

All projects are **TypeScript CDK v2** (not boto3, not Python CDK) and
ship with `package.json`, `tsconfig.json`, `cdk.json`, `bin/`, `lib/`,
and `test/`. Tests run with `npm test` (Jest + `aws-cdk-lib/assertions`).

## Repo layout

```
aws_cdk_v2_course/
├── README.md                       ← you are here
├── SYLLABUS.md                     ← authoritative L-ID ↔ file map (30 lectures)
├── DIRECTORY.md                    ← every file in the course
├── CHANGELOG.md
├── requirements.txt                ← CDK is npm-based; see notes
├── 01_foundations/                 ← L01–L04 (IaC, CDK vs CFN, constructs)
├── 02_app_stack_construct/         ← L05–L10 (App, Stack, L1/L2/L3)
│   └── code/hello-cdk/             ← TypeScript CDK project #1
├── 03_building_with_cdk/           ← L11–L15 (Lambda, API GW, S3, IAM)
│   └── code/lambda-api/            ← TypeScript CDK project #2
├── 04_appsync_stepfunctions/       ← L16–L20 (AppSync, SFN, EventBridge)
│   └── code/app-sync-sfn/          ← TypeScript CDK project #3
├── 05_testing_cicd/                ← L21–L25 (Jest, snapshots, CI/CD)
├── 06_real_world/                  ← L26–L30 (multi-stack, cross-region)
├── diagrams/                       ← 3 mermaid diagrams
├── downloads/                      ← PDF/zip student resources
├── quizzes/                        ← 6 quiz files
├── scripts/                        ← run_all_tests.py, bootstrap.sh
└── assignments/                    ← 1 graded task
```

Each section follows the **lecture_scripts/** + **code/** + `README.md`
convention. Code is in TypeScript; tests are Jest.

## Prerequisites

- **Node 20+** and **npm 10+** (CDK v2 is JavaScript/TypeScript)
- **AWS CLI v2** with credentials configured (`aws configure`)
- **AWS CDK v2 CLI** — `npm install -g aws-cdk` (≥ 2.140.0)
- **TypeScript 5.x** — installed locally per project via `npm install`
- An AWS account (free tier is enough for sections 1–5)
- Basic JavaScript/TypeScript literacy; we explain the rest

```bash
git clone <this-repo>
cd aws_cdk_v2_course
npm install -g aws-cdk            # CLI
aws configure                      # credentials
cd 02_app_stack_construct/code/hello-cdk
npm install                       # per-project deps
npm test                          # run the Jest tests
```

## How to use this repo

- **Linear read:** start at `01_foundations/lecture_scripts/L01_what_is_iac.md`.
- **Reference:** every lecture has **Prereqs → Key terms → Lecture →
  Hands-on → Quiz prep → Further reading** sections.
- **Hands-on:** all code lives in `<section>/code/<project>/`. Each
  project has a `package.json`; run `npm install && npm test`.
- **Quizzes:** `quizzes/section_N.md` — 8–12 questions, answers hidden
  in collapsible `<details>` blocks.
- **Assignment:** `assignments/assignment_1_multi_stack.md` — multi-stack
  extension exercise.

## AWS Services touched

S3, Lambda, API Gateway, IAM, AppSync, Step Functions, EventBridge,
CloudFormation (the deploy target — never hand-edited), CloudWatch.

## Conventions

- **Author of every commit:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
- **Lecture files:** `<section>/lecture_scripts/L##_topic.md`
- **Code projects:** `<section>/code/<project>/` (each is a standalone
  npm project with `bin/`, `lib/`, `test/`, `cdk.json`, `tsconfig.json`)
- **Tests:** Jest with `aws-cdk-lib/assertions` and `Template.fromStack`
- **L1 vs L2 vs L3:** we always reach for the L2 first, escape-hatch to
  L1 only when an L2 doesn't exist

## License & attribution

Course material authored by **Prem Vishnoi &lt;prem.vishnoi@example.com&gt;**.
Code samples are MIT-licensed. See `../../LICENSE` for the full text.
