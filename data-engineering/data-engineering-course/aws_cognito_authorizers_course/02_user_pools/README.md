# Section 2 — Cognito User Pools (L05–L10, ~80 min)

Section 2 is the first **hands-on** section of the course. We leave the
theory of section 1 behind and start building real Cognito User Pools
with boto3. Every lecture in this section pairs a concept with a code
demo that you can run offline with `moto` — no AWS account required.

| L# | Title | Min |
|---|---|---|
| L05 | Section Overview & Cognito in the AWS Security Ecosystem | 8 |
| L06 | Anatomy of a User Pool — IdP, Directory, App Clients | 14 |
| L07 | Sign-up, Sign-in & Custom Attributes | 14 |
| L08 | Password Policy, MFA & Account Recovery | 14 |
| L09 | Hosted UI, OAuth 2.0 Flows & App Client Settings | 15 |
| L10 | Hands-on: Create a User Pool with boto3 + moto | 15 |

## Working artifact

- `02_user_pools/code/create_user_pool.py` — idempotent boto3 script
  (~140 lines). Creates a User Pool with email-as-username, a password
  policy (min length 8, requires symbols), an App Client with no client
  secret (suitable for SPAs/mobile), a test user, and a permanent
  password. Supports `--dry-run`.
- `02_user_pools/code/test_create_user_pool.py` — 6 `moto` tests:
  pool created, idempotent re-create, app client created, user
  created, password set, dry-run path.

By the end of section 2 you'll be able to read the script
top-to-bottom, understand every `boto3` call, and modify it for your
own app's user pool (different password policy, MFA, hosted UI
domain, etc.).