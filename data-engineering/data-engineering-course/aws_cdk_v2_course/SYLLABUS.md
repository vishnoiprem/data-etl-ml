# SYLLABUS — AWS CDK v2 — Crash Course

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Format:** **6 sections, 30 lectures (L01–L30), ~6h total**. 3 working TypeScript CDK projects. 6 quizzes. 1 graded assignment.

This is the **authoritative lecture-to-file map**. Section folders are
numbered to match the published course. L-IDs run L01–L30 with no gaps.

| Section | Lectures | Min | Title |
|---|---|---|---|
| 1 | L01–L04 | 50 | Foundations (IaC, CDK vs CloudFormation, constructs) |
| 2 | L05–L10 | 65 | CDK App, Stack, Construct (the L1/L2/L3 model) |
| 3 | L11–L15 | 60 | Building with CDK (Lambda, API Gateway, S3, IAM) |
| 4 | L16–L20 | 60 | AppSync + Step Functions + EventBridge |
| 5 | L21–L25 | 55 | Testing, snapshots, assertions, CI/CD |
| 6 | L26–L30 | 60 | Real-world patterns (multi-stack, cross-region, cdk.context) |

**Total: 30 lectures, ~5h 50m, 3 working TypeScript CDK projects, 6 quizzes, 1 assignment.**

---

## Section 1 — Foundations (L01–L04, ~50 min)

| L# | Title | Min | File |
|---|---|---|---|
| L01 | What is Infrastructure as Code (IaC)? | 12 | `01_foundations/lecture_scripts/L01_what_is_iac.md` |
| L02 | CDK vs CloudFormation vs Terraform | 13 | `01_foundations/lecture_scripts/L02_cdk_vs_cfn_vs_tf.md` |
| L03 | CDK v2 architecture — `aws-cdk-lib`, `constructs`, the CLI | 13 | `01_foundations/lecture_scripts/L03_cdk_architecture.md` |
| L04 | Installing and bootstrapping CDK (Node, AWS CLI, `cdk bootstrap`) | 12 | `01_foundations/lecture_scripts/L04_install_bootstrap.md` |

---

## Section 2 — App, Stack, Construct (L05–L10, ~65 min)

| L# | Title | Min | File |
|---|---|---|---|
| L05 | The CDK construct tree — App → Stack → Construct | 11 | `02_app_stack_construct/lecture_scripts/L05_construct_tree.md` |
| L06 | L1, L2, L3 constructs — when to use which | 12 | `02_app_stack_construct/lecture_scripts/L06_l1_l2_l3.md` |
| L07 | `cdk init` — the TypeScript project template | 10 | `02_app_stack_construct/lecture_scripts/L07_cdk_init.md` |
| L08 | `cdk synth` — turning TypeScript into a CloudFormation template | 12 | `02_app_stack_construct/lecture_scripts/L08_cdk_synth.md` |
| L09 | Escape hatches and `Stack.of(scope)` | 10 | `02_app_stack_construct/lecture_scripts/L09_escape_hatches.md` |
| L10 | `cdk deploy` + `cdk destroy` + stack outputs | 10 | `02_app_stack_construct/lecture_scripts/L10_cdk_deploy_destroy.md` |

**Working code:** `02_app_stack_construct/code/hello-cdk/` — 1 S3
bucket, 1 `CfnOutput`. Jest test asserts the bucket exists.

---

## Section 3 — Building with CDK (L11–L15, ~60 min)

| L# | Title | Min | File |
|---|---|---|---|
| L11 | L2 constructs for Lambda, API Gateway, S3, IAM | 12 | `03_building_with_cdk/lecture_scripts/L11_l2_overview.md` |
| L12 | Building a Lambda function with `lambda.Code.fromAsset` | 12 | `03_building_with_cdk/lecture_scripts/L12_lambda_function.md` |
| L13 | Building a REST API with `apigateway.LambdaRestApi` | 12 | `03_building_with_cdk/lecture_scripts/L13_apigw_lambda.md` |
| L14 | IAM roles, policies, and `grantInvoke` patterns | 12 | `03_building_with_cdk/lecture_scripts/L14_iam_grants.md` |
| L15 | Putting it together — end-to-end serverless stack | 12 | `03_building_with_cdk/lecture_scripts/L15_end_to_end_stack.md` |

**Working code:** `03_building_with_cdk/code/lambda-api/` — Lambda +
API Gateway + S3 asset bucket + IAM role. Tests assert the resources
exist with `Template.fromStack`.

---

## Section 4 — AppSync + Step Functions + EventBridge (L16–L20, ~60 min)

| L# | Title | Min | File |
|---|---|---|---|
| L16 | AppSync GraphQL API with CDK — schema-as-code | 12 | `04_appsync_stepfunctions/lecture_scripts/L16_appsync_schema.md` |
| L17 | AppSync data sources and resolvers — Lambda, DynamoDB | 12 | `04_appsync_stepfunctions/lecture_scripts/L17_appsync_resolvers.md` |
| L18 | Step Functions state machines in CDK — `Choice`, `LambdaInvoke` | 12 | `04_appsync_stepfunctions/lecture_scripts/L18_sfn_states.md` |
| L19 | EventBridge buses, rules, and CDK `Rule` construct | 12 | `04_appsync_stepfunctions/lecture_scripts/L19_eventbridge.md` |
| L20 | Wiring AppSync → SFN → EventBridge — full serverless flow | 12 | `04_appsync_stepfunctions/lecture_scripts/L20_full_flow.md` |

**Working code:** `04_appsync_stepfunctions/code/app-sync-sfn/` —
AppSync + resolver Lambda + Step Functions state machine. Tests assert
the GraphQL schema and state-machine definition strings.

---

## Section 5 — Testing, Snapshots, Assertions, CI/CD (L21–L25, ~55 min)

| L# | Title | Min | File |
|---|---|---|---|
| L21 | Why test CDK stacks — synth vs deploy safety net | 10 | `05_testing_cicd/lecture_scripts/L21_why_test.md` |
| L22 | `aws-cdk-lib/assertions` — `Template.fromStack` | 12 | `05_testing_cicd/lecture_scripts/L22_assertions.md` |
| L23 | Jest snapshot tests with CDK | 11 | `05_testing_cicd/lecture_scripts/L23_snapshots.md` |
| L24 | Fine-grained assertions — `hasResourceProperties`, `objectLike` | 12 | `05_testing_cicd/lecture_scripts/L24_fine_grained.md` |
| L25 | CI/CD for CDK — `cdk diff` in PRs, GitHub Actions, OIDC | 10 | `05_testing_cicd/lecture_scripts/L25_cicd.md` |

**Working demo:** `05_testing_cicd/code/` — Jest snapshot demo for the
`hello-cdk` stack (same stack, multiple test styles).

---

## Section 6 — Real-World Patterns (L26–L30, ~60 min)

| L# | Title | Min | File |
|---|---|---|---|
| L26 | Multi-stack applications — shared VPC, network + app stacks | 12 | `06_real_world/lecture_scripts/L26_multi_stack.md` |
| L27 | Cross-region stacks — DR, global APIs, regional resources | 12 | `06_real_world/lecture_scripts/L27_cross_region.md` |
| L28 | `cdk.context` — environment values, lookups, `cdk.json` | 12 | `06_real_world/lecture_scripts/L28_cdk_context.md` |
| L29 | CDK Aspects — organization-wide compliance tags | 12 | `06_real_world/lecture_scripts/L29_aspects.md` |
| L30 | Course wrap-up — CDK vs CFN in 2026, when to reach for what | 12 | `06_real_world/lecture_scripts/L30_wrap_up.md` |

---

## Quizzes (6 — one per section)

| # | Section | File |
|---|---|---|
| 1 | Foundations | `quizzes/section_1.md` |
| 2 | App/Stack/Construct | `quizzes/section_2.md` |
| 3 | Building with CDK | `quizzes/section_3.md` |
| 4 | AppSync + SFN | `quizzes/section_4.md` |
| 5 | Testing & CI/CD | `quizzes/section_5.md` |
| 6 | Real-world patterns | `quizzes/section_6.md` |

---

## Diagrams (3)

| # | File | Purpose |
|---|---|---|
| 1 | `diagrams/cdk_construct_tree.mmd` | Tree: App → Stacks → Constructs (L1, L2, L3) |
| 2 | `diagrams/synth_cfn_deploy.mmd` | Sequence: `cdk synth` → CloudFormation → `cdk deploy` |
| 3 | `diagrams/multi_stack_pattern.mmd` | Multi-stack: 2 stacks sharing VPC, env per stage |

---

## Working TypeScript CDK projects (3)

| # | Folder | Stack | Tests |
|---|---|---|---|
| 1 | `02_app_stack_construct/code/hello-cdk/` | 1 S3 bucket + output | Jest: `Template.hasResourceProperties` |
| 2 | `03_building_with_cdk/code/lambda-api/` | Lambda + API GW + S3 + IAM | Jest: asserts Lambda, API, role |
| 3 | `04_appsync_stepfunctions/code/app-sync-sfn/` | AppSync + SFN + Lambda | Jest: asserts schema + SFN def |

---

## Downloadable resources (4)

| # | File |
|---|---|
| 1 | `downloads/cdk_v2_cheat_sheet.pdf` |
| 2 | `downloads/construct_l1_l2_l3_cheat_sheet.pdf` |
| 3 | `downloads/cdk_serverless_project_pack.zip` |
| 4 | `downloads/cdk_testing_patterns.pdf` |
