# Section 13 — AWS CloudFormation (Infrastructure as Code)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 13 (L60–L70, 73 min)
> **Use case:** Re-implement **Enterprise Use Case 2** (API Gateway + Lambda + S3 CRUD)
> as a single CloudFormation stack so the whole architecture is repeatable,
> version-controlled, and reviewable.

This section takes the API Gateway + Lambda + S3 architecture you built
by hand in section 8 and rewrites it as **declarative infrastructure**.
By the end you will be able to express the entire serverless stack in a
single YAML file and stand it up with one `aws cloudformation deploy`
command.

## Why this section matters

The console-based workflow from sections 7–8 is great for learning, but
in real teams you cannot click through the console every time you ship
a feature. CloudFormation gives you:

- **A single source of truth.** The whole stack — S3, IAM, Lambda, API
  Gateway, methods, deployment, stage — is one file you can put in Git.
- **Repeatable environments.** Spin up `dev`, `staging` and `prod`
  with different parameter values, identical topology.
- **Change review.** Every change is a diff against the previous
  template. Pull requests become infrastructure review.
- **Safe rollbacks.** CloudFormation tracks stack state; if a deploy
  fails, you can roll back to the last known-good version.
- **Drift detection.** `detect-drift` tells you when someone clicked in
  the console and desynced the stack from the template.

## Lecture map (L60–L70, 73 min)

| L# | Title | Min | File |
|---|---|---|---|
| L60 | Optional — AWS CloudFormation Basics | 2:29 | `lecture_scripts/L60_cfn_basics.md` |
| L61 | AWS CloudFormation — Serverless Architecture (API GW + Lambda + S3) | 2:16 | `lecture_scripts/L61_cfn_architecture.md` |
| L62 | AWS CloudFormation — S3 Bucket | 6:25 | `lecture_scripts/L62_cfn_s3.md` |
| L63 | AWS CloudFormation — Lambda Execution Role | 6:09 | `lecture_scripts/L63_cfn_lambda_role.md` |
| L64 | AWS CloudFormation — AWS Lambda | 14:02 | `lecture_scripts/L64_cfn_lambda.md` |
| L65 | AWS CloudFormation — REST API and API Resources | 7:17 | `lecture_scripts/L65_cfn_rest_api.md` |
| L66 | AWS CloudFormation — API Method and API Deployment | 14:35 | `lecture_scripts/L66_cfn_method_deploy.md` |
| L67 | AWS CloudFormation — Lambda Invoke Permission | 4:29 | `lecture_scripts/L67_cfn_invoke_permission.md` |
| L68 | AWS CloudFormation — End to End Demo | 1:10 | `lecture_scripts/L68_cfn_e2e_demo.md` |
| L69 | AWS CloudFormation — End to End with Parameters Section | 8:55 | `lecture_scripts/L69_cfn_parameters.md` |
| L70 | AWS CloudFormation — End to End with Metadata and Parameters Section | 4:34 | `lecture_scripts/L70_cfn_metadata_params.md` |

## Working code (`code/`)

The full CloudFormation template pack — also zipped into
`downloads/cfn_serverless_template_pack.zip`:

```
code/
├── README.md                              ← deploy + tear-down instructions
├── templates/
│   ├── 01_minimal_s3_bucket.yaml          ← L62 standalone
│   ├── 02_lambda_execution_role.yaml      ← L63 standalone
│   ├── 03_lambda_function.yaml            ← L64 standalone
│   ├── 04_rest_api_resources.yaml         ← L65 standalone
│   ├── 05_method_deployment.yaml          ← L66+L67 standalone
│   ├── 06_serverless_full_stack.yaml      ← L68 — the full e2e stack
│   ├── 07_serverless_with_parameters.yaml ← L69 — adds Parameters
│   └── 08_serverless_with_metadata.yaml   ← L70 — adds Metadata
├── lambdas/
│   ├── get_object.py                       ← packaged as zip
│   └── put_object.py                       ← packaged as zip
└── deploy.sh                              ← bash deploy script
```

Each template is valid YAML (2-space indent) and passes
`aws cloudformation validate-template --template-body file://...`.

## Prerequisites

- AWS account with admin-equivalent permissions for the region you
  deploy to (or at minimum: S3, IAM, Lambda, API Gateway full access).
- AWS CLI v2 (`aws --version`).
- Python 3.11+ (for the Lambda handler source).
- Familiarity with the API Gateway + Lambda + S3 architecture from
  section 8 (L30–L32). If you have not done that yet, watch it first.

## How to use this section

1. Read L60 first — it is the conceptual primer (resources,
   parameters, outputs, mappings, conditions, change sets).
2. Walk through L61 for the architecture diagram of what we are
   building.
3. L62–L67 each introduce one CloudFormation resource at a time,
   with a runnable standalone template in `code/templates/`.
4. L68 wires all of those into the full e2e stack
   (`06_serverless_full_stack.yaml`) and deploys it.
5. L69 adds the `Parameters` block to make the stack
   environment-agnostic.
6. L70 adds the `Metadata` block to group parameters in the console
   wizard and document defaults.

## Quiz

`quizzes/section_13.md` — 10 questions, hidden answers.
