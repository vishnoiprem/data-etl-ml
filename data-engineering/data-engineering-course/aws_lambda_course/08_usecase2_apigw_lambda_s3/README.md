# Section 8 — Enterprise Use Case 2: API Gateway, AWS Lambda, S3

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **L-IDs:** L30–L35
> **Total duration:** ~46 min
> **Use case:** A simple, fully serverless CRUD API that stores and retrieves
> JSON documents in an S3 bucket. Fronted by Amazon API Gateway, executed
> by AWS Lambda, persisted in S3.

## What you build

A REST API with two endpoints, plus an API Key + Usage Plan that throttles
unauthenticated callers. Both endpoints proxy to AWS Lambda functions that
read from and write to an S3 bucket.

| Method | Path | Lambda | Purpose |
|---|---|---|---|
| `GET`  | `/{proxy+}` | `api_get_object`  | Read an object whose key is supplied via query string or path. |
| `POST` | `/{proxy+}` | `api_put_object`  | Write a JSON body to an S3 key supplied via path. |
| (any)  | (API)         | (authorizer)      | API Key + Usage Plan throttling (L33–L34). |

The same stack is rebuilt later with **CloudFormation** (section 13) and
**AWS CDK v2** (section 12) so you can compare the three authoring
styles: console → boto3 → CFN → CDK.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L30 | Architecture (API Gateway, AWS Lambda, S3) | 1:01 | `lecture_scripts/L30_usecase2_architecture.md` |
| L31 | S3, Lambda and API Gateway — Part 1 | 12:29 | `lecture_scripts/L31_s3_lambda_apigw_pt1.md` |
| L32 | S3, Lambda and API Gateway with Query String Parameters — Part 2 | 9:43 | `lecture_scripts/L32_query_string_params_pt2.md` |
| L33 | API Keys and Usage Plan — Theory | 4:10 | `lecture_scripts/L33_api_keys_theory.md` |
| L34 | API Keys and Usage Plan — Hands On | 7:56 | `lecture_scripts/L34_api_keys_hands_on.md` |
| L35 | Agentic AI Architect Roadmap on AWS (Optional) | 10:10 | `lecture_scripts/L35_agentic_ai_roadmap.md` |

## Working code (under `code/`)

| Subdir | Purpose |
|---|---|
| `code/api_get_object/`     | Lambda that returns an S3 object + metadata; `moto`-backed test. |
| `code/api_put_object/`     | Lambda that writes the request body to S3; `moto`-backed test. |
| `code/api_keys_setup/`     | Idempotent boto3 script: create API Key + Usage Plan + stage link. |
| `code/event_payloads/`     | Sample API Gateway proxy event JSON for GET and POST. |

## Conventions

- All Lambda handlers are written for **Python 3.11+** and follow the
  handler-signature contract documented in section 2 (L08).
- The Lambdas assume a single, well-known bucket name passed in via the
  `BUCKET_NAME` environment variable. This keeps them testable with
  `moto.mock_aws` without an IAM role.
- All boto3 scripts are **idempotent**: re-running them on an existing
  resource should not fail (e.g. they look up the API by name before
  creating a new one).
- The proxy+ resource is intentional: it lets us extract the object key
  from the URL path itself (used in L32's "key from path" example).

## How to read this section

1. Watch L30 to understand the architecture.
2. Read L31 — the long-form hands-on lecture — alongside the working
   code in `code/api_get_object/` and `code/api_put_object/`.
3. L32 builds on L31 with query string parameters and mapping templates.
4. L33–L34 add the API Key + Usage Plan on top of the same stack.
5. L35 is optional: a 2026 roadmap for agentic AI architects on AWS.
6. Take the quiz in `../../quizzes/section_8.md`.
