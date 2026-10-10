# Changelog — aws_cognito_authorizers_course

All notable changes to this course material are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/) / dates in YYYY-MM-DD.

## [1.0.0] — 2026-10-10

### Added

- 5 sections, 25 lectures (L01–L25), ~5h 30m total
- **Section 1 — Foundations** (L01–L04): authentication vs authorization, OAuth 2.0, OIDC, JWT
- **Section 2 — Cognito User Pools** (L05–L10): sign-up, sign-in, attributes, MFA, hosted UI. Includes `02_user_pools/code/create_user_pool.py` + `test_create_user_pool.py` (6 moto tests pass) — idempotent boto3 script that creates a User Pool with email-as-username, password policy (min length 8, requires symbols), an App Client with no client secret, a test user, and sets a permanent password. Supports `--dry-run`.
- **Section 3 — Cognito Identity Pools** (L11–L14): federation + AWS credential vending. Includes `03_identity_pools/code/identity_pool_demo.py` + `test_identity_pool_demo.py` (4 moto tests pass) — idempotent boto3 script that creates an Identity Pool with the User Pool as the auth provider and configures an IAM role for authenticated users. Supports `--dry-run`.
- **Section 4 — API Gateway + Cognito Authorizer** (L15–L20): User Pool Authorizer on REST + HTTP APIs, scopes/groups, JWT validation, end-to-end demo.
- **Section 5 — Advanced Patterns** (L21–L25): custom auth challenges, Lambda triggers (pre/post auth, pre-token-generation, custom message), SAML 2.0 federation (Okta, Azure AD), OIDC federation (Auth0, Google) and course wrap-up.
- **5 quizzes** (`quizzes/section_1.md` through `section_5.md`) — 54 questions total, answers in collapsible `<details>` blocks.
- **2 diagrams** (`diagrams/jwt_validation_flow.mmd`, `diagrams/identity_pool_federation.mmd`).
- **1 assignment** (`assignments/assignment_1_user_pool_api.md` — graded extension tying sections 2 and 4 together).
- **`scripts/run_all_tests.py`** — runs every section's `test_*.py` in its own subprocess, aggregate pass/fail summary.
- **`scripts/bootstrap.sh`** — sets up a venv, installs `requirements.txt`, sanity-checks AWS CLI.
- **`requirements.txt`** — `boto3>=1.34.0`, `botocore>=1.34.0`, `moto[cognito-idp]>=5.0`, `pyjwt>=2.8.0`, `pytest>=8.0`.

### Conventions

- Author of every commit: **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**
- Lecture files: `<section>/lecture_scripts/L##_topic.md`
- Code files: `<section>/code/<topic>/<file>.py`
- Every lecture follows the structure: **Prereqs → Key terms → Lecture →
  Hands-on → Quiz prep → Further reading**
- Every section has a `README.md` summarizing the lectures
- Quizzes: 10–12 multiple-choice questions per section, answers in
  `<details><summary>Show answer</summary>…</details>` blocks
- Code uses `boto3` 1.34+, `moto[cognito-idp]` 5+, `pyjwt` 2.8+
- Free tier-eligible; no paid third-party SaaS dependencies

### Test status

- 10 pytest tests pass (6 user-pool + 4 identity-pool) using `moto` 5.x.
- `python3 scripts/run_all_tests.py -v` exits 0.