# AWS Lambda Authorizer — Crash Course

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Format:** **5 sections, 25 lectures (L01–L25), ~6h 00m total** (companion to the published Udemy course).
> **Based on:** "AWS Lambda Authorizer — Crash Course" (October 2026 edition).

This is the local companion repo for the AWS Lambda Authorizer crash course.
The lecture-to-file map in `SYLLABUS.md` is authoritative.

## What you'll learn

- **What an Authorizer is and why you'd build one** — the place a Lambda
  Authorizer sits in the API Gateway request lifecycle, and the four
  authentication patterns API Gateway offers (IAM auth, Cognito User
  Pool, Lambda Authorizer, API Keys).
- **JWT fundamentals** — header / payload / signature, HMAC vs RSA
  signing, JWK / JWKS rotation, the standard claims (`iss`, `sub`,
  `aud`, `exp`, `nbf`, `iat`, `jti`), and how to verify a token in
  pure Python with `pyjwt`.
- **Token-based Lambda Authorizers** — the API Gateway TOKEN event
  shape, the IAM policy document contract (`Allow` / `Deny` /
  `principalId` / `context`), and a reference implementation that
  returns a least-privilege policy.
- **Request-parameter Authorizers and policy caching** — the REQUEST
  event shape (headers, query string, stage variables), the
  `IdentitySource` / `ReauthorizeEvery` semantics, and a reference
  implementation that uses an in-process LRU cache with TTL.
- **Advanced patterns** — CloudFront Lambda@Edge viewer-request
  authentication, custom auth challenges for WebSocket APIs, and
  OIDC integration with IdPs like Auth0 / Okta / Cognito.

## What you build

| # | Working artifact | Section | L-IDs |
|---|---|---|---|
| 1 | **JWT verify** — RSA keypair, sign + verify, expired / tampered / wrong-key rejection (5 tests) | 2 | L05–L10 |
| 2 | **Token-based Lambda Authorizer** — `Bearer` JWT → IAM policy (6 tests) | 3 | L11–L15 |
| 3 | **Request-parameter Authorizer + policy cache** — `?user=…&token=…` → Allow/Deny with TTL'd LRU cache (4 tests) | 4 | L16–L20 |

**Total: 3 working demos, 15+ moto-free unit tests, 5 quizzes, 2 diagrams.**

## Repo layout

```
aws_lambda_authorizer_course/
├── README.md                       ← you are here
├── SYLLABUS.md                     ← authoritative L01–L25 map
├── DIRECTORY.md                    ← every file in the course
├── CHANGELOG.md
├── requirements.txt                ← boto3, moto, pyjwt, cryptography, pytest
├── 01_foundations/                 ← L01–L04 — what an authorizer is
├── 02_jwt_basics/                  ← L05–L10 — JWT structure, signing, verification
│   └── code/
│       ├── jwt_verify.py           ← pure-Python + pyjwt demo
│       └── test_jwt_verify.py      ← 5+ tests
├── 03_simple_authorizer/           ← L11–L15 — TOKEN authorizer
│   └── code/
│       ├── token_authorizer.py     ← reference handler
│       └── test_token_authorizer.py← 6+ tests
├── 04_policy_cache/                ← L16–L20 — REQUEST authorizer + caching
│   └── code/
│       ├── param_authorizer.py     ← reference handler + LRU TTL cache
│       └── test_param_authorizer.py← 4+ tests
├── 05_advanced_patterns/           ← L21–L25 — CloudFront, challenges, OIDC
├── diagrams/                       ← 2 mermaid diagrams
│   ├── lambda_authorizer_flow.mmd
│   └── policy_cache_lifecycle.mmd
├── downloads/                      ← PDF/zip placeholders
├── quizzes/                        ← 5 quiz files (one per section)
├── scripts/                        ← run_all_tests.py, bootstrap.sh
└── assignments/                    ← 1 graded extension task
```

Each section follows the **lecture_scripts/** + **code/** convention
established in `../aws_lambda_course/`. Every lecture is a standalone
`.md` you can read top-to-bottom; every `code/` folder is runnable
end-to-end with `pytest`.

## Prerequisites

- AWS account (free tier is enough for sections 1–4)
- Python 3.11+ (we use `boto3` 1.34+, `pyjwt` 2.8+, `cryptography` 42+)
- AWS CLI v2
- `moto[apigateway]` 5+ for offline tests
- `pytest` 8+ to run the test suite

```bash
git clone <this-repo>
cd aws_lambda_authorizer_course
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
aws configure   # optional — only needed for the real-AWS section
```

## How to use this repo

- **Linear read:** start at `01_foundations/lecture_scripts/L01_course_intro.md`.
- **Reference:** every lecture file has **Prereqs**, **Key terms**,
  **Lecture**, **Hands-on** and **Quiz prep** sections.
- **Hands-on:** all code lives under `<section>/code/`. Each code
  folder has a `README.md` that walks you through running it.
- **Quizzes:** `quizzes/section_N.md` — 8–12 questions, hidden answers
  in `<details><summary>Show answer</summary>…</details>` blocks.
- **Assignment:** `assignments/assignment_1_lambda_authorizer.md` — a
  graded extension that ties sections 2–4 together.

## AWS Services used in the course

API Gateway (REST, HTTP, WebSocket), AWS Lambda, AWS Secrets Manager,
SSM Parameter Store, Amazon Cognito (OIDC), CloudFront (Lambda@Edge),
AWS SAM (optional), OpenID Connect (Auth0 / Okta).

## License & attribution

Course material authored by **Prem Vishnoi &lt;prem.vishnoi@example.com&gt;**
based on the published Udemy curriculum. Code samples are MIT-licensed.
See `../../LICENSE` for the full text.
