# DIRECTORY — aws_cognito_authorizers_course

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
| `diagrams/` | 2 Mermaid diagrams (jwt validation + identity pool federation) |
| `downloads/` | 2 PDF placeholder files |
| `quizzes/` | 5 quiz files (one per section) |
| `scripts/` | `run_all_tests.py`, `bootstrap.sh` |
| `assignments/` | 1 graded task |

## Sections

| # | Folder | L-IDs | Lectures | Working code |
|---|---|---|---|---|
| 1 | `01_foundations/` | L01–L04 | 4 | – |
| 2 | `02_user_pools/` | L05–L10 | 6 | `create_user_pool.py` + 6 moto tests |
| 3 | `03_identity_pools/` | L11–L14 | 4 | `identity_pool_demo.py` + 4 moto tests |
| 4 | `04_api_gateway_integration/` | L15–L20 | 6 | – |
| 5 | `05_advanced_patterns/` | L21–L25 | 5 | – |
| | **Total** | | **25** | **2 demos** |

## Per-section layout

Every section folder has the same shape:

```
<NN_topic>/
├── README.md              ← short summary of the section
├── lecture_scripts/       ← L##_topic.md (one per lecture)
│   ├── L01_…
│   ├── L02_…
│   └── …
└── code/                  ← runnable code samples (sections 2 + 3 only)
    ├── <topic_1>/
    │   ├── README.md
    │   ├── script.py
    │   └── test_script.py
    └── …
```

## Quizzes (5)

| # | File | Questions |
|---|---|---|
| 1 | `quizzes/section_1.md` | 10 |
| 2 | `quizzes/section_2.md` | 12 |
| 3 | `quizzes/section_3.md` | 10 |
| 4 | `quizzes/section_4.md` | 12 |
| 5 | `quizzes/section_5.md` | 10 |

## Diagrams

| # | File | Purpose |
|---|---|---|
| 1 | `diagrams/jwt_validation_flow.mmd` | Sequence: Client → API Gateway → Cognito User Pool (JWKS fetch) → Lambda authorizer → Allow/Deny |
| 2 | `diagrams/identity_pool_federation.mmd` | Flowchart: User → User Pool (token) → Identity Pool (assume role) → AWS Service |

## Downloads

| File | Purpose |
|---|---|
| `downloads/cognito_cheat_sheet.pdf` | All Cognito User Pool / Identity Pool fields, limits, and IAM ARNs in one page |
| `downloads/jwt_validation_cheat_sheet.pdf` | JWT header/payload claims, JWKS endpoint, validation recipe in `pyjwt` |

## Assignments (1)

| # | File | Estimated time |
|---|---|---|
| 1 | `assignments/assignment_1_user_pool_api.md` | 4h |