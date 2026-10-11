# Section 3 — Cognito Identity Pools (L11–L14, ~70 min)

Section 3 is the second hands-on section. We trade the JWT we minted
in section 2 for **temporary AWS credentials** via Cognito Identity
Pools + AWS STS. By the end of this section you'll understand the
federation flow well enough to wire an Identity Pool into a mobile
app, an IoT device, or a server-side microservice.

| L# | Title | Min |
|---|---|---|
| L11 | Section Overview & Identity Pool Mental Model | 10 |
| L12 | Authentication Providers — User Pool, OIDC, SAML, Guest | 15 |
| L13 | IAM Roles for Authenticated & Guest Users | 15 |
| L14 | Hands-on: Identity Pool with boto3 + moto | 30 |

## Working artifact

- `03_identity_pools/code/identity_pool_demo.py` — idempotent boto3
  script (~140 lines). Creates a Cognito Identity Pool with the
  section-2 User Pool as the auth provider, creates an IAM role for
  authenticated users with a least-privilege S3 inline policy, and
  attaches the role to the pool. Supports `--dry-run`.
- `03_identity_pools/code/test_identity_pool_demo.py` — 5 moto tests
  (1 above the required minimum): pool created, User Pool set as
  provider, role has correct trust policy, idempotent re-create, and
  dry-run path.

## Diagram

`diagrams/identity_pool_federation.mmd` — flowchart: User → User Pool
(token) → Identity Pool (assume role) → AWS Service.