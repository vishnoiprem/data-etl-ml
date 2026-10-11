# AWS Cognito Authorizers — Crash Course

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Format:** **5 sections, 25 lectures (L01–L25), ~5h 30m total** (Udemy-published 2026 edition).
> **Source:** Companion repo to the "AWS Cognito Authorizers — Crash Course" curriculum.

This is the local companion repo for the published crash course on **AWS
Cognito as a fully-managed identity and authorization service for APIs and
applications**. The lecture-to-file map in `SYLLABUS.md` is authoritative.

## What you'll learn

- The **theory** behind authentication vs authorization, OAuth 2.0, OIDC,
  and JWT — the four building blocks every API security engineer must
  internalize.
- How to design, create, and operate an **AWS Cognito User Pool**: sign-up
  flows, sign-in, custom attributes, password policy, MFA, Lambda
  triggers, and the Hosted UI.
- How to wire **Cognito Identity Pools** to vend **temporary AWS
  credentials** to federated users (User Pool tokens, SAML, OIDC,
  anonymous guest access).
- How to attach a **Cognito User Pool Authorizer** to **API Gateway REST
  APIs and HTTP APIs** — including scopes, groups, and caching.
- **Advanced patterns**: custom auth challenges, Lambda triggers
  (pre-token-generation, post-confirmation, pre-authentication), and
  **SAML/OIDC federation** with corporate identity providers (Okta,
  Azure AD, Google Workspace, Ping).

## What you build

| # | Working artifact | Section | L-IDs |
|---|---|---|---|
| 1 | **Idempotent boto3 + moto script** that creates a Cognito User Pool, an App Client (no client secret), a test user, and a permanent password | 2 | L05–L10 |
| 2 | **Idempotent boto3 + moto script** that creates a Cognito Identity Pool, links a User Pool as the auth provider, and configures an IAM role for authenticated users | 3 | L11–L14 |
| 3 | **JWT validation flow** Mermaid sequence diagram (Client → API Gateway → JWKS → Lambda authorizer → Allow/Deny) | 4 | L15–L20 |
| 4 | **Identity Pool federation** Mermaid flowchart (User → User Pool → Identity Pool → AWS Service) | 3 | L11–L14 |

## Repo layout

```
aws_cognito_authorizers_course/
├── README.md                       ← you are here
├── SYLLABUS.md                     ← authoritative L-ID ↔ file map (25 lectures)
├── DIRECTORY.md                    ← every file in the course
├── CHANGELOG.md
├── requirements.txt                ← boto3, moto[cognito-idp], pyjwt, pytest
├── 01_foundations/                 ← L01–L04 (authN vs authZ, OAuth, OIDC, JWT)
├── 02_user_pools/                  ← L05–L10 (sign-up, sign-in, attributes, MFA, hosted UI)
├── 03_identity_pools/              ← L11–L14 (federation + AWS credential vending)
├── 04_api_gateway_integration/     ← L15–L20 (Cognito User Pool Authorizer on REST + HTTP APIs)
├── 05_advanced_patterns/           ← L21–L25 (custom auth, Lambda triggers, SAML/OIDC)
├── diagrams/                       ← 2 mermaid diagrams
├── downloads/                      ← PDF placeholders
├── quizzes/                        ← 5 quiz files (one per section)
├── scripts/                        ← run_all_tests.py, bootstrap.sh
└── assignments/                    ← 1 graded task
```

Each section follows the **lecture_scripts/** + **code/** + **README.md**
convention established in `../aws_lambda_course/`. Every lecture is a
standalone `.md` you can read top-to-bottom; every `code/` folder is
runnable end-to-end against `moto` (no AWS credentials required).

## Prerequisites

- AWS account (free tier is enough for all 5 sections)
- Python 3.11+ (we use `boto3` 1.34+)
- AWS CLI v2
- Familiarity with HTTP/REST APIs and JSON
- Basic Python — we keep the boto3 code small and well-commented
- `moto[cognito-idp]` for offline tests
- `pyjwt` for token validation exercises

```bash
git clone <this-repo>
cd aws_cognito_authorizers_course
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
aws configure
```

## How to use this repo

- **Linear read:** start at `01_foundations/lecture_scripts/L01_authn_vs_authz.md`.
- **Reference:** every lecture file has a **Prereqs**, **Key terms**,
  **Lecture**, **Hands-on**, **Quiz prep** and **Further reading** section.
- **Hands-on:** all code lives under `<section>/code/`. Each subdir has a
  `README.md` that walks you through running it.
- **Quizzes:** `quizzes/section_N.md` — 8–12 questions, hidden answers in
  a collapsible block.
- **Assignment:** `assignments/assignment_1_user_pool_api.md` — graded
  extension exercise that ties sections 2 and 4 together.

## Run the tests (no AWS account required)

```bash
cd aws_cognito_authorizers_course
python3 -m pytest 02_user_pools/code/test_create_user_pool.py \
                  03_identity_pools/code/test_identity_pool_demo.py -v
# OR all sections in one go:
python3 scripts/run_all_tests.py -v
```

## AWS Services used in the course

AWS Cognito (User Pools, Identity Pools), API Gateway (REST + HTTP), AWS
Lambda (triggers + custom auth), IAM, AWS STS, CloudWatch Logs, plus
optional: Amazon SES (for email delivery during sign-up), AWS KMS (for
custom SMS MFA).

## License & attribution

Course material authored by **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**
based on the published Udemy curriculum. Code samples are MIT-licensed.
See `../../LICENSE` for the full text.
