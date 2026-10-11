# AWS Lambda, Python (Boto3) & Serverless — Beginner to Advanced

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Format:** **16 sections, 88 lectures (L01–L81 + L31a, L36a–L36e, L44a, L82–L87), ~10h 30m total** (Udemy-published 2026 edition).
> **Based on:** "AWS Lambda, Python(Boto3) & Serverless- Beginner to Advanced" Udemy course.

This is the local companion repo for the published Udemy course. The
lecture-to-file map in `SYLLABUS.md` is authoritative.

## What you'll learn

- Develop expertise in designing and writing AWS Lambda functions using Python
  (Absolute Beginner to Advanced) — no previous coding experience required.
- **Generative AI:** Build end-to-end Manufacturing Industry use case with
  **AWS Bedrock (Cohere Foundational Model) + AWS Lambda + AWS API Gateway**
  (Section 10).
- Basics of Python which will be used to write key AWS Services such as
  **EC2, S3 and DynamoDB** using AWS Lambda(Python) (Section 4).
- **Enterprise Use Case 1:** banking/retail use case where a bank gets a
  regular feed through a JSON file which triggers a Lambda function via an S3
  event notification; Lambda reads the data and inserts it into DynamoDB
  (Section 6).
- **Enterprise Use Case 2:** API Gateway, AWS Lambda, S3, Cognito Authorizer,
  Lambda Authorizer, API Keys and Usage Plans (Sections 7–9).
- **Securing APIs:** AWS Lambda Authorizers + AWS Cognito Authorizers —
  theory and hands on (Section 9).
- **CloudFormation:** Implementing the serverless use case in a single
  template — API Gateway + Lambda + S3 (Section 13).
- **AWS CDK v2:** Same serverless use case in TypeScript IaC — API Gateway +
  IAM Role + Lambda + S3 (Section 12).
- **API Gateway deep dive:** API types, endpoint types, resources, methods,
  integration, authentication, authorization, private APIs and private
  integration (Section 7).
- **Lambda advanced concepts:** invocation models, limits & pricing,
  provisioned & reserved concurrency, handler, events, context, versions,
  aliases, environment variables, VPC networking, CloudWatch monitoring
  (Section 11).

## What you build

| # | Working artifact | Section | L-IDs |
|---|---|---|---|
| 1 | Python + boto3 scripts to list/create/delete S3 buckets | 4 | L12–L15 |
| 2 | Lambda Automation Use Case — EC2 start/stop on EventBridge schedule | 4 | L16–L17 |
| 3 | Lambda to create DynamoDB table + put items | 4 | L18 |
| 4 | **Use Case 1:** S3 → Lambda → DynamoDB banking JSON pipeline | 6 | L23–L24 |
| 5 | **Use Case 2:** API Gateway + Lambda + S3 CRUD (query string params) | 8 | L30–L32, L31a |
| 6 | API Gateway API Keys + Usage Plan | 8 | L33–L34 |
| 7 | Use Case 2 re-walked with a security lens (5 lectures) | 9 | L36a–L36e |
| 8 | Lambda Authorizer (custom JWT validation) | 9 | L36–L37 |
| 9 | Cognito User Pool Authorizer | 9 | L38–L39 |
| 10 | **GenAI use case:** Bedrock Cohere → Lambda → API Gateway (manufacturing defect summarizer) | 10 | L40–L46, L44a |
| 11 | Lambda in VPC (CloudWatch + ENI walkthrough) | 11 | L51–L52 |
| 12 | CloudWatch Metrics + Logs hands-on for Lambda | 11 | L53–L56 |
| 13 | Lambda Versions + Aliases | 11 | L57–L58 |
| 14 | CloudFormation: full serverless stack with Parameters + Metadata | 13 | L60–L70 |
| 15 | CDK v2 TypeScript: same serverless stack | 12 | L71–L77 |
| 16 | **Use Case 3:** FCI Cluster Monitor (AWS MS AD + FSx + Lambda + SNS + EventBridge) | 15 | L82–L87 |

## Repo layout

```
aws_lambda_course/
├── README.md                       ← you are here
├── SYLLABUS.md                     ← authoritative L-ID ↔ file map (81 lectures)
├── DIRECTORY.md                    ← every file in the course
├── CHANGELOG.md
├── 01_introduction/                ← L01–L02
├── 02_lambda_basic_concepts/       ← L03–L08
├── 03_python_basics/               ← L09–L10
├── 04_lambda_with_aws_resources/   ← L11–L18
├── 05_lambda_basic_concepts_pt2/   ← L19–L22
├── 06_usecase1_s3_lambda_dynamodb/ ← L23–L24
├── 07_apigw_overview/              ← L25–L29
├── 08_usecase2_apigw_lambda_s3/    ← L30–L35
├── 09_api_security_lambda_cognito_auth/ ← L36–L39
├── 10_generative_ai_bedrock/       ← L40–L46
├── 11_lambda_advanced_concepts/    ← L47–L59
├── 12_cdk_v2_serverless/           ← L71–L77
├── 13_cloudformation_serverless/   ← L60–L70
├── 14_python_basics_appx/          ← L78–L81
├── assets/                         ← mermaid diagrams
├── downloads/                      ← PDF/zip resources
├── quizzes/                        ← 14 quiz files
├── scripts/                        ← run_all_tests.py, bootstrap.sh
└── assignments/                    ← 6 graded tasks
```

Each section follows the **lecture_scripts/** + **code/** + **assignments/**
convention established in `../aws_glue_course/`. Every lecture is a
standalone `.md` you can read top-to-bottom; every `code/` folder is
runnable end-to-end.

## Prerequisites

- AWS account (free tier is enough for sections 1–11)
- Python 3.11+ (we use `boto3` 1.34+)
- AWS CLI v2
- Optional: Node 20+ (for CDK in section 12), `sam` CLI, Docker (for local
  Lambda testing)

```bash
git clone <this-repo>
cd aws_lambda_course
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
aws configure
```

## How to use this repo

- **Linear read:** start at `01_introduction/lecture_scripts/L01_course_intro.md`.
- **Reference:** every lecture file has a **Prereqs**, **Key terms**,
  **Hands-on** and **Quiz** section.
- **Hands-on:** all code lives under `<section>/code/`. Each subdir has a
  `README.md` that walks you through running it (`python script.py`,
  `sam local invoke`, `cdk deploy`, etc.).
- **Quizzes:** `quizzes/section_N.md` — 10 questions, hidden answers in a
  collapsible block.
- **Assignment:** `assignments/assignment_N.md` — 4h–8h graded task.

## AWS Services used in the course

Lambda, EC2, S3, DynamoDB, API Gateway, AWS MS AD, FSx, SNS, CloudWatch,
CloudWatch Alarm, AWS CDK, Lambda Authorizer, Cognito Authorizer,
EventBridge, AWS Bedrock (Cohere foundational model), AWS CloudFormation.

## License & attribution

Course material authored by **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**
based on the published Udemy curriculum. Code samples are MIT-licensed.
See `../../LICENSE` for the full text.
