# SYLLABUS — AWS Lambda Authorizer Crash Course

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Format:** **5 sections**, **25 lectures** (L01–L25), **~6h 00m** total. 5 quizzes (one per section). 3 working demos with 15+ offline tests. 1 graded assignment. 2 diagrams.
> **Source:** Udemy-published curriculum "AWS Lambda Authorizer — Crash Course" (October 2026 edition).

This is the **authoritative lecture-to-file map**. The Udemy lecture order is preserved exactly as L01–L25 below.

| Section | Lectures | Min | Title |
|---|---|---|---|
| 1 | L01–L04 | 32 | Foundations — What is an Authorizer (and why custom) |
| 2 | L05–L10 | 88 | JWT Basics — Structure, Claims, Signing, Verification |
| 3 | L11–L15 | 84 | Simple Token-Based Lambda Authorizer |
| 4 | L16–L20 | 88 | Request-Parameter Authorizer & Policy Caching |
| 5 | L21–L25 | 68 | Advanced — CloudFront Lambda@Edge, Challenges, OIDC |
| | **Total** | **~6h 00m** | **25 lectures, 5 quizzes, 3 demos, 15+ tests** |

---

## Section 1 — Foundations (L01–L04, ~32 min)

| L# | Title | Min | File |
|---|---|---|---|
| L01 | Course Intro — Why API Security Matters | 6:00 | `01_foundations/lecture_scripts/L01_course_intro.md` |
| L02 | Where the Lambda Authorizer Fits in the Request Lifecycle | 8:00 | `01_foundations/lecture_scripts/L02_request_lifecycle.md` |
| L03 | The Four Auth Patterns in API Gateway (IAM, Cognito, Lambda, API Keys) | 10:00 | `01_foundations/lecture_scripts/L03_four_auth_patterns.md` |
| L04 | Anatomy of an IAM Policy Document (Allow, Deny, principalId, context) | 8:00 | `01_foundations/lecture_scripts/L04_iam_policy_anatomy.md` |

---

## Section 2 — JWT Basics (L05–L10, ~88 min)

| L# | Title | Min | File |
|---|---|---|---|
| L05 | Section Overview — Why JWTs | 4:00 | `02_jwt_basics/lecture_scripts/L05_section_overview.md` |
| L06 | JWT Structure — Header, Payload, Signature (base64url) | 14:00 | `02_jwt_basics/lecture_scripts/L06_jwt_structure.md` |
| L07 | Standard Claims — iss, sub, aud, exp, nbf, iat, jti | 16:00 | `02_jwt_basics/lecture_scripts/L07_standard_claims.md` |
| L08 | Signing Algorithms — HS256 (HMAC) vs RS256 (RSA) | 16:00 | `02_jwt_basics/lecture_scripts/L08_signing_algorithms.md` |
| L09 | JWK and JWKS — Rotating Public Keys | 18:00 | `02_jwt_basics/lecture_scripts/L09_jwks_rotation.md` |
| L10 | Verifying a JWT in Pure Python (pyjwt) | 20:00 | `02_jwt_basics/lecture_scripts/L10_verifying_in_python.md` |

**Working code:** `02_jwt_basics/code/jwt_verify.py` + `test_jwt_verify.py` (5 moto-free tests).

---

## Section 3 — Simple Token-Based Lambda Authorizer (L11–L15, ~84 min)

| L# | Title | Min | File |
|---|---|---|---|
| L11 | Section Overview — TOKEN Authorizer Event Shape | 6:00 | `03_simple_authorizer/lecture_scripts/L11_section_overview.md` |
| L12 | The API Gateway TOKEN Event (authorizationToken, methodArn, type) | 14:00 | `03_simple_authorizer/lecture_scripts/L12_token_event_shape.md` |
| L13 | Building the Allow Policy (Resource = methodArn, Action = execute-api:Invoke) | 16:00 | `03_simple_authorizer/lecture_scripts/L13_allow_policy.md` |
| L14 | Returning Claims via the `context` Map | 14:00 | `03_simple_authorizer/lecture_scripts/L14_context_map.md` |
| L15 | End-to-End: TOKEN Authorizer with HS256 JWT | 34:00 | `03_simple_authorizer/lecture_scripts/L15_end_to_end.md` |

**Working code:** `03_simple_authorizer/code/token_authorizer.py` + `test_token_authorizer.py` (6 moto-free tests).

---

## Section 4 — Request-Parameter Authorizer & Policy Caching (L16–L20, ~88 min)

| L# | Title | Min | File |
|---|---|---|---|
| L16 | Section Overview — Why a Request Authorizer | 6:00 | `04_policy_cache/lecture_scripts/L16_section_overview.md` |
| L17 | The API Gateway REQUEST Event (headers, query, stage vars, body) | 18:00 | `04_policy_cache/lecture_scripts/L17_request_event_shape.md` |
| L18 | IdentitySource, Multi-Identity-Source & ReauthorizeEvery | 20:00 | `04_policy_cache/lecture_scripts/L18_identity_source_cache.md` |
| L19 | Building an LRU Cache with TTL (time-bounded, thread-safe) | 24:00 | `04_policy_cache/lecture_scripts/L19_lru_cache_ttl.md` |
| L20 | End-to-End: REQUEST Authorizer with Policy Cache | 20:00 | `04_policy_cache/lecture_scripts/L20_end_to_end.md` |

**Working code:** `04_policy_cache/code/param_authorizer.py` + `test_param_authorizer.py` (4 moto-free tests).

---

## Section 5 — Advanced Patterns (L21–L25, ~68 min)

| L# | Title | Min | File |
|---|---|---|---|
| L21 | Section Overview — Beyond REST APIs | 4:00 | `05_advanced_patterns/lecture_scripts/L21_section_overview.md` |
| L22 | CloudFront Lambda@Edge — Viewer-Request Authentication | 18:00 | `05_advanced_patterns/lecture_scripts/L22_cloudfront_lambda_edge.md` |
| L23 | Custom Auth Challenges for WebSocket APIs | 14:00 | `05_advanced_patterns/lecture_scripts/L23_websocket_challenges.md` |
| L24 | OIDC Integration — Auth0, Okta, Cognito as the IdP | 16:00 | `05_advanced_patterns/lecture_scripts/L24_oidc_integration.md` |
| L25 | When **Not** to Use a Lambda Authorizer — Design Trade-offs | 16:00 | `05_advanced_patterns/lecture_scripts/L25_when_not_to_use.md` |

---

## Quizzes (5 — one per section)

| # | Section | File |
|---|---|---|
| 1 | Foundations | `quizzes/section_1.md` |
| 2 | JWT Basics | `quizzes/section_2.md` |
| 3 | Token-Based Authorizer | `quizzes/section_3.md` |
| 4 | Policy Cache | `quizzes/section_4.md` |
| 5 | Advanced Patterns | `quizzes/section_5.md` |

---

## Downloads (4 placeholders)

| # | File |
|---|---|
| 1 | `downloads/jwt_cheat_sheet.pdf` |
| 2 | `downloads/iam_policy_cheat_sheet.pdf` |
| 3 | `downloads/api_gateway_event_shapes.pdf` |
| 4 | `downloads/lambda_authorizer_template_pack.zip` |

---

## Assignments (1)

| # | File |
|---|---|
| 1 | `assignments/assignment_1_lambda_authorizer.md` |