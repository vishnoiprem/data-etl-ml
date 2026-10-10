# DIRECTORY — aws_lambda_course

> Full file index for the course. See `SYLLABUS.md` for the lecture-to-file
> map. **All paths are relative to this file.**

## Top-level

| Path | Purpose |
|---|---|
| `README.md` | Course overview |
| `SYLLABUS.md` | L01–L81 ↔ file map |
| `DIRECTORY.md` | this file |
| `CHANGELOG.md` | changelog |
| `requirements.txt` | Python dependencies (root) |
| `assets/` | Mermaid diagrams + architecture SVGs |
| `downloads/` | PDF/zip student resources |
| `quizzes/` | 14 quiz files (one per section) |
| `scripts/` | `run_all_tests.py`, `bootstrap.sh` |
| `assignments/` | 6 graded tasks |

## Sections

| # | Folder | L-IDs | Lectures |
|---|---|---|---|
| 1 | `01_introduction/` | L01–L02 | 2 |
| 2 | `02_lambda_basic_concepts/` | L03–L08 | 6 |
| 3 | `03_python_basics/` | L09–L10 | 2 |
| 4 | `04_lambda_with_aws_resources/` | L11–L18 | 8 |
| 5 | `05_lambda_basic_concepts_pt2/` | L19–L22 | 4 |
| 6 | `06_usecase1_s3_lambda_dynamodb/` | L23–L24 | 2 |
| 7 | `07_apigw_overview/` | L25–L29 | 5 |
| 8 | `08_usecase2_apigw_lambda_s3/` | L30–L35 | 6 |
| 9 | `09_api_security_lambda_cognito_auth/` | L36–L39 | 4 |
| 10 | `10_generative_ai_bedrock/` | L40–L46 | 7 |
| 11 | `11_lambda_advanced_concepts/` | L47–L59 | 13 |
| 12 | `12_cdk_v2_serverless/` | L71–L77 | 7 |
| 13 | `13_cloudformation_serverless/` | L60–L70 | 11 |
| 14 | `14_python_basics_appx/` | L78–L81 | 4 |
| | **Total** | | **81** |

## Per-section layout

Every section folder has the same shape:

```
<NN_topic>/
├── README.md              ← short summary of the section
├── lecture_scripts/       ← L##_topic.md (one per lecture)
│   ├── L01_…
│   ├── L02_…
│   └── …
├── code/                  ← runnable code samples
│   ├── <topic_1>/
│   │   ├── README.md
│   │   ├── script.py
│   │   └── test_script.py
│   └── …
└── assignments/           ← section-specific assignments (if any)
```

## Quizzes (14)

| # | File |
|---|---|
| 1 | `quizzes/section_1.md` |
| 2 | `quizzes/section_2.md` |
| 3 | `quizzes/section_3.md` |
| 4 | `quizzes/section_4.md` |
| 5 | `quizzes/section_5.md` |
| 6 | `quizzes/section_6.md` |
| 7 | `quizzes/section_7.md` |
| 8 | `quizzes/section_8.md` |
| 9 | `quizzes/section_9.md` |
| 10 | `quizzes/section_10.md` |
| 11 | `quizzes/section_11.md` |
| 12 | `quizzes/section_12.md` |
| 13 | `quizzes/section_13.md` |
| 14 | `quizzes/section_14.md` |

## Assets

```
assets/
├── architecture_usecase1.png
├── architecture_usecase2.png
├── architecture_bedrock.png
├── architecture_cfn.png
├── architecture_cdk.png
└── mermaid/
    ├── usecase1.mmd
    ├── usecase2.mmd
    ├── bedrock.mmd
    ├── cfn.mmd
    └── cdk.mmd
```

## Downloads

| File | Purpose |
|---|---|
| `downloads/lambda_cheat_sheet.pdf` | All Lambda limits, env vars, IAM ARNs in one page |
| `downloads/boto3_patterns_cheat_sheet.pdf` | Pagination, waiters, error handling recipes |
| `downloads/cfn_serverless_template_pack.zip` | All CFN templates from section 13 |
| `downloads/cdk_serverless_project_pack.zip` | CDK v2 TypeScript project from section 12 |

## Assignments (6)

| # | File |
|---|---|
| 1 | `assignments/assignment_1_boto3_miniproject.md` |
| 2 | `assignments/assignment_2_usecase1.md` |
| 3 | `assignments/assignment_3_usecase2.md` |
| 4 | `assignments/assignment_4_lambda_authorizer.md` |
| 5 | `assignments/assignment_5_cfn_template.md` |
| 6 | `assignments/assignment_6_cdk_bedrock.md` |
