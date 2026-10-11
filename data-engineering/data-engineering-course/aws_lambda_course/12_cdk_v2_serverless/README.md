# Section 12 — AWS CDK v2 (Infrastructure as Code)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 12 of `aws_lambda_course/`
> **Lectures:** L71–L77 (7 lectures, ~45 minutes)
> **Working artifact:** `code/` — a complete AWS CDK v2 TypeScript project that
> rebuilds the Section 8 serverless use case (API Gateway + Lambda + S3 CRUD).

## What this section covers

Section 12 is the **Infrastructure as Code (IaC)** twin of section 13
(CloudFormation). Where section 13 spells every resource out in JSON/YAML, this
section shows the **same serverless architecture** declared in
**TypeScript** with the **AWS CDK v2**.

By the end of L77 you will have:

- Understood what CDK is, how it differs from CloudFormation and SAM, and how
  it synthesizes to a CloudFormation template under the hood.
- Installed the CDK v2 toolkit, bootstrapped your AWS account, and
  authenticated from the command line.
- A working `cdk` project under `code/` that defines:
  - An S3 bucket (versioning + encryption on by default)
  - An IAM execution role with least-privilege S3 permissions
  - Two Lambda functions (Node.js 20, 256 MB, 30 s) using AWS SDK v3
  - A REST API with `GET` and `PUT /objects/{key}`, CORS enabled
- The muscle memory to run `cdk synth`, `cdk deploy`, and `cdk destroy`.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L71 | (Optional) Introduction to AWS Cloud Development Kit (CDK) | 7:23 | `lecture_scripts/L71_cdk_intro.md` |
| L72 | AWS CDK v2 — Pre-requisites | 9:27 | `lecture_scripts/L72_cdk_prereqs.md` |
| L73 | Implementing Serverless Use Case 2 using AWS CDK v2 | 0:39 | `lecture_scripts/L73_cdk_implementing_usecase2.md` |
| L74 | AWS CDK — Create S3 bucket using AWS CDK v2 | 11:22 | `lecture_scripts/L74_cdk_s3.md` |
| L75 | AWS CDK — Create IAM Role using AWS CDK v2 | 6:56 | `lecture_scripts/L75_cdk_iam_role.md` |
| L76 | AWS CDK — Create Lambda using AWS CDK v2 | 8:57 | `lecture_scripts/L76_cdk_lambda.md` |
| L77 | AWS CDK — Create API Gateway using AWS CDK v2 | 7:53 | `lecture_scripts/L77_cdk_apigw.md` |

## Working code

```
12_cdk_v2_serverless/
└── code/
    ├── README.md                  ← install, build, bootstrap, deploy, test
    ├── package.json               ← CDK v2 + AWS SDK v3 deps
    ├── tsconfig.json
    ├── cdk.json                   ← CDK app entry
    ├── cdk.context.json
    ├── bin/
    │   └── serverless-app.ts      ← CDK app entry point
    ├── lib/
    │   └── serverless-stack.ts    ← The stack: S3 + IAM + Lambda x2 + API GW
    ├── lambda/
    │   ├── get-object.ts          ← handler for GET /objects/{key}
    │   └── put-object.ts          ← handler for PUT /objects/{key}
    └── .gitignore
```

See `code/README.md` for the full walkthrough.

## How to use this section

1. Skim **L71** for the conceptual model (CDK vs CFN vs SAM vs Terraform).
2. Do **L72** hands-on: install Node 20, `npm install -g aws-cdk`, configure
   AWS credentials, and run `cdk bootstrap` once per account/region.
3. Skim **L73** to see the target architecture diagram.
4. Work through **L74 → L77** in order; each one adds one construct to the
   stack. At the end of L77 you have a fully deployable serverless CRUD API.
5. Take the quiz in `quizzes/section_12.md` to lock the concepts in.

## Prerequisites

- AWS account (free tier is enough for this section)
- Node.js 20 LTS and npm 10+
- AWS CLI v2 with `aws configure` already done
- Sections 7 and 8 of this course (API Gateway + Lambda + S3 CRUD)
- Section 13 is recommended reading but not required — section 12 stands alone

## Companion materials

- Quiz: [`../quizzes/section_12.md`](../quizzes/section_12.md) (10 Qs)
- CFN equivalent: [`../13_cloudformation_serverless/`](../13_cloudformation_serverless/)
- Architecture diagrams: [`../assets/cdk_*.mmd`](../assets/) (if present)
- Cheat sheet: [`../downloads/cdk_serverless_project_pack.zip`](../downloads/)

## License & attribution

Course material authored by **Prem Vishnoi <pvishnoi@avilx.com>**. Code
samples are MIT-licensed.
