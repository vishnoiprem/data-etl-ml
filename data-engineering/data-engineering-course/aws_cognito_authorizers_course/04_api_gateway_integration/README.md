# Section 4 — API Gateway + Cognito Authorizer (L15–L20, ~100 min)

Section 4 is the **production pattern** lecture sequence of the course.
We take the User Pool tokens from section 2 and the Identity Pool
from section 3, and we wire them into **API Gateway** as a
**Cognito User Pool Authorizer**. By the end of this section you'll
understand every step in the JWT validation flow and be able to
explain why API Gateway is rejecting (or accepting) a specific
request.

| L# | Title | Min |
|---|---|---|
| L15 | Section Overview & Auth Methods Recap | 12 |
| L16 | Cognito User Pool Authorizer on REST APIs | 18 |
| L17 | Cognito User Pool Authorizer on HTTP APIs (JWT) | 18 |
| L18 | Scopes, Groups & Fine-Grained Authorization | 16 |
| L19 | Token Validation — JWKS, Expiry, Issuer & Audience | 18 |
| L20 | End-to-End Demo — Secure a REST API End-to-End | 18 |

## Diagram

`diagrams/jwt_validation_flow.mmd` — sequence: Client → API Gateway
→ Cognito User Pool (JWKS fetch) → Lambda authorizer (validate JWT)
→ Allow/Deny.