# DIRECTORY — aws_lambda_authorizer_course

> Full file index for the course. See `SYLLABUS.md` for the lecture-to-file
> map. **All paths are relative to this file.**

## Top-level

| Path | Purpose |
|---|---|
| `README.md` | Course overview |
| `SYLLABUS.md` | L01–L25 ↔ file map |
| `DIRECTORY.md` | this file |
| `CHANGELOG.md` | changelog |
| `requirements.txt` | Python dependencies (root) |
| `diagrams/` | 2 Mermaid diagrams (flow + cache lifecycle) |
| `downloads/` | 4 PDF / zip placeholders |
| `quizzes/` | 5 quiz files (one per section) |
| `scripts/` | `run_all_tests.py`, `bootstrap.sh` |
| `assignments/` | 1 graded task |

## Sections

| # | Folder | L-IDs | Lectures |
|---|---|---|---|
| 1 | `01_foundations/` | L01–L04 | 4 |
| 2 | `02_jwt_basics/` | L05–L10 | 6 |
| 3 | `03_simple_authorizer/` | L11–L15 | 5 |
| 4 | `04_policy_cache/` | L16–L20 | 5 |
| 5 | `05_advanced_patterns/` | L21–L25 | 5 |
| | **Total** | | **25** |

## Per-section layout

Every section folder has the same shape:

```
<NN_topic>/
├── README.md              ← short summary of the section
├── lecture_scripts/       ← L##_topic.md (one per lecture)
│   ├── L01_…
│   ├── L02_…
│   └── …
└── code/                  ← runnable code samples
    └── <topic>/
            ├── README.md
            ├── <topic>.py
            └── test_<topic>.py
```

## Quizzes (5)

| # | File |
|---|---|
| 1 | `quizzes/section_1.md` |
| 2 | `quizzes/section_2.md` |
| 3 | `quizzes/section_3.md` |
| 4 | `quizzes/section_4.md` |
| 5 | `quizzes/section_5.md` |

## Diagrams (2)

```
diagrams/
├── lambda_authorizer_flow.mmd       ← sequence: Client → API GW → Lambda Authorizer → IAM Policy → Back to API GW → Lambda
└── policy_cache_lifecycle.mmd       ← flowchart: First request → Cache populated → Subsequent requests → Cached policy reused
```

## Downloads

| File | Purpose |
|---|---|
| `downloads/jwt_cheat_sheet.pdf` | All JWT claims, signing algorithms, library snippets in one page |
| `downloads/iam_policy_cheat_sheet.pdf` | Allow / Deny, statement structure, principalId / context |
| `downloads/api_gateway_event_shapes.pdf` | TOKEN vs REQUEST authorizer event reference |
| `downloads/lambda_authorizer_template_pack.zip` | SAM / CDK starter projects for sections 3–4 |

## Assignments (1)

| # | File |
|---|---|
| 1 | `assignments/assignment_1_lambda_authorizer.md` |

## Code demos (3)

| # | Folder | File | Tests |
|---|---|---|---|
| 1 | `02_jwt_basics/code/` | `jwt_verify.py` + `test_jwt_verify.py` | 5 |
| 2 | `03_simple_authorizer/code/` | `token_authorizer.py` + `test_token_authorizer.py` | 6 |
| 3 | `04_policy_cache/code/` | `param_authorizer.py` + `test_param_authorizer.py` | 4 |