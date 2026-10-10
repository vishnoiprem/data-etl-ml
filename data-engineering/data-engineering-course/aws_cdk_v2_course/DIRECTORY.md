# DIRECTORY — aws_cdk_v2_course

> Full file index for the course. See `SYLLABUS.md` for the
> lecture-to-file map. **All paths are relative to this file.**

## Top-level

| Path | Purpose |
|---|---|
| `README.md` | Course overview |
| `SYLLABUS.md` | L01–L30 ↔ file map (authoritative) |
| `DIRECTORY.md` | this file |
| `CHANGELOG.md` | changelog |
| `requirements.txt` | npm-equivalent dependencies (informational) |
| `diagrams/` | 3 mermaid diagrams |
| `downloads/` | PDF/zip student resources |
| `quizzes/` | 6 quiz files (one per section) |
| `scripts/` | `run_all_tests.py`, `bootstrap.sh` |
| `assignments/` | 1 graded task |

## Sections

| # | Folder | L-IDs | Lectures |
|---|---|---|---|
| 1 | `01_foundations/` | L01–L04 | 4 |
| 2 | `02_app_stack_construct/` | L05–L10 | 6 |
| 3 | `03_building_with_cdk/` | L11–L15 | 5 |
| 4 | `04_appsync_stepfunctions/` | L16–L20 | 5 |
| 5 | `05_testing_cicd/` | L21–L25 | 5 |
| 6 | `06_real_world/` | L26–L30 | 5 |
| | **Total** | | **30** |

## Per-section layout

Every section folder has the same shape:

```
<NN_topic>/
├── README.md                  ← short summary of the section
├── lecture_scripts/           ← L##_topic.md (one per lecture)
│   ├── L01_…
│   ├── L02_…
│   └── …
└── code/                      ← runnable TypeScript CDK project
    └── <project>/
        ├── package.json
        ├── tsconfig.json
        ├── cdk.json
        ├── bin/<name>.ts
        ├── lib/<name>-stack.ts
        └── test/<name>.test.ts
```

## Quizzes (6)

| # | File |
|---|---|
| 1 | `quizzes/section_1.md` (10 questions) |
| 2 | `quizzes/section_2.md` (12 questions) |
| 3 | `quizzes/section_3.md` (10 questions) |
| 4 | `quizzes/section_4.md` (8 questions) |
| 5 | `quizzes/section_5.md` (10 questions) |
| 6 | `quizzes/section_6.md` (10 questions) |

## Diagrams

```
diagrams/
├── cdk_construct_tree.mmd        ← App → Stacks → L1/L2/L3
├── synth_cfn_deploy.mmd          ← cdk synth → CFN → cdk deploy
└── multi_stack_pattern.mmd       ← 2 stacks sharing VPC, envs
```

## Downloads

| File | Purpose |
|---|---|
| `downloads/cdk_v2_cheat_sheet.pdf` | CLI flags, common L2s, escape hatches |
| `downloads/construct_l1_l2_l3_cheat_sheet.pdf` | All 3 levels side by side |
| `downloads/cdk_serverless_project_pack.zip` | All 3 working projects |
| `downloads/cdk_testing_patterns.pdf` | Snapshot + assertion recipes |

## Assignments (1)

| # | File |
|---|---|
| 1 | `assignments/assignment_1_multi_stack.md` (multi-stack extension) |

## Working TypeScript CDK projects (3)

| # | Folder | Stack summary |
|---|---|---|
| 1 | `02_app_stack_construct/code/hello-cdk/` | 1 S3 bucket + `CfnOutput` |
| 2 | `03_building_with_cdk/code/lambda-api/` | Lambda + API GW + S3 + IAM |
| 3 | `04_appsync_stepfunctions/code/app-sync-sfn/` | AppSync + SFN + resolver Lambda |
