# SYLLABUS — AWS Cognito Authorizers — Crash Course

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Format:** **5 sections**, **25 lectures** (L01–L25), **~5h 30m** total. 2 working boto3 + moto demos, 2 mermaid diagrams, 5 quizzes, 1 graded assignment, 2 downloadable resources.
> **Source:** Udemy-published curriculum "AWS Cognito Authorizers — Crash Course" (October 2026 edition).

This is the **authoritative lecture-to-file map**. The Udemy lecture order
is preserved exactly as L01–L25 below. Section folders are numbered to
match the Udemy course sections.

| Section | Lectures | Min | Title |
|---|---|---|---|
| 1 | L01–L04 | 50 | Foundations — Authentication vs Authorization, OAuth 2.0, OIDC, JWT |
| 2 | L05–L10 | 80 | AWS Cognito User Pools — Sign-up, Sign-in, Attributes, MFA, Hosted UI |
| 3 | L11–L14 | 70 | Cognito Identity Pools — Federation & AWS Credential Vending |
| 4 | L15–L20 | 100 | API Gateway + Cognito Authorizer (REST + HTTP APIs) |
| 5 | L21–L25 | 80 | Advanced — Custom Auth Challenges, Lambda Triggers, SAML/OIDC Federation |

**Total: 25 lectures, ~5h 30m, 2 working demos, 5 quizzes, 2 diagrams.**

---

## Section 1 — Foundations (L01–L04, ~50 min)

| L# | Title | Min | File |
|---|---|---|---|
| L01 | Course Introduction & Why Cognito | 8 | `01_foundations/lecture_scripts/L01_course_intro.md` |
| L02 | Authentication vs Authorization — The Mental Model | 12 | `01_foundations/lecture_scripts/L02_authn_vs_authz.md` |
| L03 | OAuth 2.0 — Roles, Flows & Tokens | 15 | `01_foundations/lecture_scripts/L03_oauth2.md` |
| L04 | OpenID Connect (OIDC) & JWTs | 15 | `01_foundations/lecture_scripts/L04_oidc_jwt.md` |

---

## Section 2 — AWS Cognito User Pools (L05–L10, ~80 min)

| L# | Title | Min | File |
|---|---|---|---|
| L05 | Section Overview & Cognito in the AWS Security Ecosystem | 8 | `02_user_pools/lecture_scripts/L05_section_overview.md` |
| L06 | Anatomy of a User Pool — IdP, Directory, App Clients | 14 | `02_user_pools/lecture_scripts/L06_user_pool_anatomy.md` |
| L07 | Sign-up, Sign-in & Custom Attributes | 14 | `02_user_pools/lecture_scripts/L07_signup_signin_attributes.md` |
| L08 | Password Policy, MFA & Account Recovery | 14 | `02_user_pools/lecture_scripts/L08_password_mfa_recovery.md` |
| L09 | Hosted UI, OAuth 2.0 Flows & App Client Settings | 15 | `02_user_pools/lecture_scripts/L09_hosted_ui_oauth_flows.md` |
| L10 | Hands-on: Create a User Pool with boto3 + moto | 15 | `02_user_pools/lecture_scripts/L10_boto3_hands_on.md` |

**Working code:** `02_user_pools/code/create_user_pool.py` + `test_create_user_pool.py` (6 moto tests pass).

---

## Section 3 — Cognito Identity Pools (L11–L14, ~70 min)

| L# | Title | Min | File |
|---|---|---|---|
| L11 | Section Overview & Identity Pool Mental Model | 10 | `03_identity_pools/lecture_scripts/L11_section_overview.md` |
| L12 | Authentication Providers — User Pool, OIDC, SAML, Guest | 15 | `03_identity_pools/lecture_scripts/L12_auth_providers.md` |
| L13 | IAM Roles for Authenticated & Guest Users | 15 | `03_identity_pools/lecture_scripts/L13_iam_roles.md` |
| L14 | Hands-on: Identity Pool with boto3 + moto | 30 | `03_identity_pools/lecture_scripts/L14_boto3_hands_on.md` |

**Working code:** `03_identity_pools/code/identity_pool_demo.py` + `test_identity_pool_demo.py` (4 moto tests pass).

---

## Section 4 — API Gateway + Cognito Authorizer (L15–L20, ~100 min)

| L# | Title | Min | File |
|---|---|---|---|
| L15 | Section Overview & Auth Methods Recap | 12 | `04_api_gateway_integration/lecture_scripts/L15_section_overview.md` |
| L16 | Cognito User Pool Authorizer on REST APIs | 18 | `04_api_gateway_integration/lecture_scripts/L16_rest_authorizer.md` |
| L17 | Cognito User Pool Authorizer on HTTP APIs (JWT) | 18 | `04_api_gateway_integration/lecture_scripts/L17_http_authorizer.md` |
| L18 | Scopes, Groups & Fine-Grained Authorization | 16 | `04_api_gateway_integration/lecture_scripts/L18_scopes_groups.md` |
| L19 | Token Validation — JWKS, Expiry, Issuer & Audience | 18 | `04_api_gateway_integration/lecture_scripts/L19_jwt_validation.md` |
| L20 | End-to-End Demo — Secure a REST API End-to-End | 18 | `04_api_gateway_integration/lecture_scripts/L20_e2e_demo.md` |

**Diagrams:** `diagrams/jwt_validation_flow.mmd` (L19), `diagrams/identity_pool_federation.mmd` (L14).

---

## Section 5 — Advanced Patterns (L21–L25, ~80 min)

| L# | Title | Min | File |
|---|---|---|---|
| L21 | Section Overview & Custom Auth Challenge Flow | 12 | `05_advanced_patterns/lecture_scripts/L21_section_overview.md` |
| L22 | Lambda Triggers — Pre/Post Authentication, Pre Token Generation | 18 | `05_advanced_patterns/lecture_scripts/L22_lambda_triggers.md` |
| L23 | Custom Message & Email/SMS Sender Triggers | 14 | `05_advanced_patterns/lecture_scripts/L23_custom_message.md` |
| L24 | SAML 2.0 Federation with Corporate IdPs (Okta, Azure AD) | 18 | `05_advanced_patterns/lecture_scripts/L24_saml_federation.md` |
| L25 | OIDC Federation (Auth0, Google, Login.gov) & Course Wrap-up | 18 | `05_advanced_patterns/lecture_scripts/L25_oidc_federation_wrapup.md` |

---

## Quizzes (5 — one per section)

| # | Section | File |
|---|---|---|
| 1 | Foundations | `quizzes/section_1.md` |
| 2 | User Pools | `quizzes/section_2.md` |
| 3 | Identity Pools | `quizzes/section_3.md` |
| 4 | API Gateway + Cognito Authorizer | `quizzes/section_4.md` |
| 5 | Advanced Patterns | `quizzes/section_5.md` |

---

## Working demos (2)

| # | File | Tests |
|---|---|---|
| 1 | `02_user_pools/code/create_user_pool.py` | `02_user_pools/code/test_create_user_pool.py` (6 moto tests) |
| 2 | `03_identity_pools/code/identity_pool_demo.py` | `03_identity_pools/code/test_identity_pool_demo.py` (4 moto tests) |

---

## Diagrams (2)

| # | File | Lecture |
|---|---|---|
| 1 | `diagrams/jwt_validation_flow.mmd` | L19 |
| 2 | `diagrams/identity_pool_federation.mmd` | L14 |

---

## Downloadable resources (2)

| # | File |
|---|---|
| 1 | `downloads/cognito_cheat_sheet.pdf` |
| 2 | `downloads/jwt_validation_cheat_sheet.pdf` |

---

## Assignments (1)

| # | File |
|---|---|
| 1 | `assignments/assignment_1_user_pool_api.md` |
