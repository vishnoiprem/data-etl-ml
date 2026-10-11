# Section 5 — Advanced Patterns (L21–L25)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** 5 (~68 min)
> **Working code:** none (conceptual section)

Section 5 is the "beyond REST APIs" section. We cover three real-world
patterns you will encounter in production but not in the basic
sections:

- **CloudFront Lambda@Edge** — authenticating viewer requests at the
  CDN edge, *before* they reach API Gateway at all.
- **WebSocket auth challenges** — the IAM auth flow for WebSocket
  APIs, where the client connects first and authenticates second.
- **OIDC integration** — wiring Auth0, Okta, or Cognito as the IdP
  behind a Lambda Authorizer.

We close with a frank discussion of when **not** to use a Lambda
Authorizer — because not every API needs one.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L21 | Section Overview — Beyond REST APIs | 4:00 | `lecture_scripts/L21_section_overview.md` |
| L22 | CloudFront Lambda@Edge — Viewer-Request Authentication | 18:00 | `lecture_scripts/L22_cloudfront_lambda_edge.md` |
| L23 | Custom Auth Challenges for WebSocket APIs | 14:00 | `lecture_scripts/L23_websocket_challenges.md` |
| L24 | OIDC Integration — Auth0, Okta, Cognito as the IdP | 16:00 | `lecture_scripts/L24_oidc_integration.md` |
| L25 | When **Not** to Use a Lambda Authorizer — Design Trade-offs | 16:00 | `lecture_scripts/L25_when_not_to_use.md` |

## Conventions

- Every lecture follows **Prereqs → Key terms → Lecture → Hands-on →
  Quiz prep → Further reading**.
- The quiz for this section is in `../quizzes/section_5.md`.