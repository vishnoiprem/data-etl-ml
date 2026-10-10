# Section 9 — API Security: Lambda Authorizer & Cognito Authorizer

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 09
> **Lectures:** L36–L39 (44 min total)
> **Working artifacts:** 3 code subdirectories under `code/`

## What this section answers

So far in the course every API Gateway method has been **open** to the world
(or protected only by an API key). In production you almost never want that
— you want to know **who is calling your API** and **what they are allowed
to do**. Section 9 is the answer: two first-class authorizer types that
API Gateway supports natively for REST APIs.

| Authorizer type | Who validates the token? | When to use it |
|---|---|---|
| **Lambda Authorizer** (a.k.a. *custom authorizer*) | A Lambda function you write | Non-OIDC token formats, custom IdPs, fine-grained per-route policy generation, migration from a legacy auth system |
| **Cognito User Pool Authorizer** | API Gateway itself, using JWKS from a Cognito User Pool | Any OIDC-IdP-fronted app where AWS Cognito is already the identity store (web, mobile, BFF) |

Both authorizers return an **IAM policy** that API Gateway evaluates to
decide whether the call is allowed to reach the integration. Both are
configured on a REST API `Method` the same way, and both work in front of
the Lambda-based S3 CRUD we built in section 8.

## Lecture map

| L# | Title | Min | What you build |
|---|---|---|---|
| L36 | Securing APIs using AWS Lambda Authorizer — Theory | 3:30 | the request/response contract, the `AuthResponse` shape, caching, `lambda:InvokeFunction` permission |
| L37 | Securing APIs using AWS Lambda Authorizer — Hands On | 23:46 | full authorizer function, REST API wiring with boto3, JWT happy-path test |
| L38 | Securing APIs using AWS Cognito Authorizer — Theory | 2:42 | User Pool vs Identity Pool, what API Gateway validates for you, scopes & groups |
| L39 | Securing APIs using AWS Cognito Authorizer — Hands On | 14:11 | create User Pool + App Client, wire up the `COGNITO_USER_POOLS` authorizer, test with a real ID/access token |

## Code layout

```
09_api_security_lambda_cognito_auth/
├── README.md                 ← this file
├── lecture_scripts/
│   ├── L36_lambda_authorizer_theory.md
│   ├── L37_lambda_authorizer_hands_on.md
│   ├── L38_cognito_authorizer_theory.md
│   └── L39_cognito_authorizer_hands_on.md
├── code/
│   ├── lambda_authorizer/
│   │   ├── README.md
│   │   ├── lambda_authorizer.py
│   │   ├── test_lambda_authorizer.py
│   │   └── requirements.txt
│   ├── cognito_setup/
│   │   ├── README.md
│   │   ├── create_user_pool.py
│   │   ├── test_create_user_pool.py
│   │   └── requirements.txt
│   └── event_payloads/
│       ├── README.md
│       ├── token_authorizer_event.json
│       └── request_authorizer_event.json
└── assignments/
    └── assignment_lambda_authorizer.md
```

## Prerequisites

- Sections 7 and 8 complete — you need a working REST API with a Lambda
  integration (the S3 CRUD from L30–L32 is the perfect target).
- Python 3.11+, `boto3 >= 1.34`, `moto >= 5`, `pyjwt >= 2.8`.
- `aws configure` already done; default region `us-east-1` recommended.
- For hands-on: an IAM role that can call `apigateway:`, `lambda:`,
  `cognito-idp:`, `iam:PassRole`, and `s3:GetObject`/`PutObject` on the
  demo bucket.

## Key terms

- **Authorizer** — a piece of logic API Gateway calls *before* invoking
  the integration. It decides "allow" or "deny" and returns an IAM policy
  plus an optional `principalId`.
- **Lambda Authorizer** — the user supplies the Lambda; API Gateway
  invokes it with an `event` that contains the caller's identity token
  (or full request) and the method ARN.
- **Cognito Authorizer** — API Gateway is given a Cognito User Pool ARN;
  it validates the JWT signature, expiry, audience, and issuer itself
  using the User Pool's JWKS endpoint.
- **IAM policy** — what the authorizer returns. The `Resource` field must
  match the method ARN, or you can wildcard.
- **Caching** — both authorizers cache the policy for a configurable TTL
  (default 300s) to avoid paying a Lambda invocation on every request.
- **`lambda:InvokeFunction`** — the IAM permission API Gateway needs on
  the authorizer Lambda. We grant this explicitly in L37.

## How to use this section

1. Read L36 end-to-end. Do not skip the response-shape discussion — it
   is the most common source of bugs in Lambda authorizers.
2. Run L37 with `moto` first (offline, no AWS account needed), then
   redeploy against your real account.
3. L38 is short. The main thing to internalise is **what API Gateway
   does for you when you pick COGNITO_USER_POOLS**.
4. L39 wires Cognito in front of the same REST API from L37. You can
   swap one for the other to feel the difference.

## Further reading

- AWS Docs — [Use API Gateway Lambda authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html)
- AWS Docs — [Control access with Cognito User Pool authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)
- RFC 7519 — JSON Web Token
- PyJWT docs — <https://pyjwt.readthedocs.io/>
