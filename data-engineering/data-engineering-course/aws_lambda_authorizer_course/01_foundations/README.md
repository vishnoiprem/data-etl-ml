# Section 1 — Foundations (L01–L04)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** 4 (~32 min)
> **Working code:** none (conceptual section)

This section answers the question: **what is a Lambda Authorizer, and
why would you build one when API Gateway already ships with IAM auth,
Cognito User Pools, and API Keys?**

By the end of these four lectures you'll be able to:

- draw the request lifecycle diagram and point to the slot where the
  authorizer runs;
- pick the right auth pattern from API Gateway's four options for a
  given use case;
- read and write an IAM policy document that API Gateway will accept
  as the response of a Lambda Authorizer.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L01 | Course Intro — Why API Security Matters | 6:00 | `lecture_scripts/L01_course_intro.md` |
| L02 | Where the Lambda Authorizer Fits in the Request Lifecycle | 8:00 | `lecture_scripts/L02_request_lifecycle.md` |
| L03 | The Four Auth Patterns in API Gateway (IAM, Cognito, Lambda, API Keys) | 10:00 | `lecture_scripts/L03_four_auth_patterns.md` |
| L04 | Anatomy of an IAM Policy Document (Allow, Deny, principalId, context) | 8:00 | `lecture_scripts/L04_iam_policy_anatomy.md` |

## Conventions

- Every lecture follows **Prereqs → Key terms → Lecture → Hands-on →
  Quiz prep → Further reading**.
- This section has no runnable code; the first hands-on lab is in
  section 2 (`02_jwt_basics/code/jwt_verify.py`).
- The quiz for this section is in `../quizzes/section_1.md`.
