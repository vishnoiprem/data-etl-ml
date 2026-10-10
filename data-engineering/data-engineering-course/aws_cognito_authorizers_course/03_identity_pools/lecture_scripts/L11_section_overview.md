---
lecture: L11
title: "Section Overview & Identity Pool Mental Model"
duration: "10:00"
section: 3
prereqs:
  - L05
  - L06
  - L07
  - L08
  - L09
  - L10
---

# L11 — Section Overview & Identity Pool Mental Model

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 3 — Cognito Identity Pools
> **Duration:** 10:00

## Prereqs

- Watched **L05–L10** (section 2). You should already have a working
  User Pool and a test user.

## Key terms

- **Identity Pool** — a Cognito construct that **trades a token for
  temporary AWS credentials**. It does not authenticate; it
  federates.
- **Federation** — letting an identity from one system act in another.
  Cognito Identity Pools federate **into AWS** — they take a token
  from a User Pool (or an OIDC/SAML/social IdP) and produce
  credentials that work against S3, DynamoDB, Lambda, etc.
- **STS (AWS Security Token Service)** — the AWS service that mints
  temporary credentials. Identity Pools call STS on your behalf.
- **Identity ID** — a stable UUID that Cognito assigns to each
  federated user. It persists across sessions for up to 365 days and
  is the principal your IAM policies are scoped to.
- **Authenticated role** — the IAM role Cognito assumes when the user
  presents a valid token.
- **Unauthenticated (guest) role** — the IAM role Cognito assumes
  when the user has no token (i.e. anonymous web traffic). Optional
  but useful for public read-only content.
- **Developer-authenticated identity** — a way to mint an Identity
  ID from your own backend (skip Cognito's IdP entirely). Used in
  legacy migrations.

## Lecture

Welcome to section 3. In section 2 we stood up a User Pool, signed
in, and got back three tokens. Today we take the most useful of
those tokens — the **ID token** — and trade it for **temporary AWS
credentials** that let a federated end user call S3, DynamoDB, or
Lambda directly. By the end of this section you'll understand why
this pattern is one of the most common in mobile and IoT apps.

### Why "trade a token for credentials" is useful

Most end-user apps need to call **some** AWS service directly from
the client:

- A mobile app uploads photos to an S3 bucket.
- A web app reads from a DynamoDB table.
- An IoT device publishes to an IoT Core topic.
- A SPA fetches from AppSync.

You have three options:

1. **Pre-signed URLs.** Your backend mints a pre-signed S3 URL with
   a short TTL. The client uses it directly. Works for narrow
   read/write patterns but doesn't generalize to "the client wants
   to call any of 15 AWS services".
2. **Proxy through your backend.** Every AWS call goes through your
   Lambda. Adds latency, costs Lambda invocations, and is annoying to
   scale.
3. **Cognito Identity Pool.** The client trades its User Pool ID
   token for temporary AWS credentials. The client uses those
   credentials directly. Cognito handles the STS handoff; the client
   only needs the AWS SDK.

Identity Pools exist for option 3.

### The mental model

```
+----------------+      +----------------+      +----------------+
|                |      |                |      |                |
|     User       +----->+  User Pool     +----->+ Identity Pool  |
|  (browser /    | sign |  (authN,       | ID   |  (trade        |
|   mobile app)  | in  |   issues JWT)  | token|   for STS)     |
|                |      |                |      |                |
+----------------+      +----------------+      +--------+-------+
                                                       |
                                                       | assume role
                                                       v
                                              +----------------+
                                              |                |
                                              |  STS           |
                                              |  (temp AWS     |
                                              |   credentials) |
                                              |                |
                                              +--------+-------+
                                                       |
                                                       v
                                              +----------------+
                                              |  S3 / DDB /    |
                                              |  Lambda / etc  |
                                              +----------------+
```

User Pool = "who is this person?"
Identity Pool = "what AWS credentials should this person have?"

### The token types an Identity Pool accepts

| Source | Token type | Setup effort |
|---|---|---|
| Cognito User Pool | ID token or access token (JWT) | Trivial — already done in section 2 |
| OIDC provider | ID token (JWT) | Register the OIDC IdP, supply endpoints |
| SAML 2.0 IdP | SAML assertion | Register the SAML IdP, exchange via API |
| Facebook | Facebook access token | One-time app setup |
| Google | Google ID token | One-time OAuth consent |
| Apple | Apple identity token | One-time OAuth consent |
| Amazon | Amazon access token | One-time OAuth consent |
| Twitter | OAuth1 access token | Deprecated by Twitter |
| Developer-authenticated | Custom (you decide) | You build a backend that mints an Identity ID |

For the course we focus on the **User Pool** path. In section 5
(L24–L25) we add SAML and OIDC.

### What an Identity Pool gives back

When a client calls `GetCredentialsForIdentity`, Cognito returns:

```json
{
  "IdentityId": "us-east-1:12345678-90ab-cdef-1234-567890abcdef",
  "Credentials": {
    "AccessKeyId":     "ASIA...",
    "SecretKey":       "...",
    "SessionToken":    "FwoGZX...",
    "Expiration":      "2026-10-10T13:00:00Z"
  }
}
```

These are **STS temporary credentials**. They:

- Expire in 1 hour by default (configurable, 15 min – 12 h)
- Are signed with the IAM role you attached to the pool
- Can call **any AWS service** the role's policy allows
- Are scoped to the specific `IdentityId` (so per-user authorization
  can be enforced via `Condition` blocks using
  `${cognito-identity.amazonaws.com:sub}`)

The client uses them like any other AWS credentials:

```python
import boto3
session = boto3.Session(
    aws_access_key_id=creds["AccessKeyId"],
    aws_secret_access_key=creds["SecretKey"],
    aws_session_token=creds["SessionToken"],
    region_name="us-east-1",
)
s3 = session.client("s3")
s3.list_buckets()
```

### The trade-off: granularity vs. simplicity

Identity Pools give you **federated AWS access for end users**, but
they're a coarse tool for authorization:

- You can scope the IAM role to a specific `Condition` (e.g. "this
  user can only read S3 objects under their own prefix").
- You **cannot** enforce row-level security in DynamoDB from a
  client-side identity pool credential — DynamoDB IAM policies can
  only express coarse filters.

For row-level security, use **API Gateway + Cognito User Pool
Authorizer** (section 4) and enforce row-level filters in your
Lambda. Identity Pools are best for:

- "Upload to S3" use cases (where the prefix *is* the row)
- "Read a specific object" use cases
- "Call this one specific Lambda" use cases (with a tight role)
- Anything where the client is the right place to enforce the policy

### What's coming in this section

| Lecture | Outcome |
|---|---|
| L12 | You can wire a User Pool, an OIDC IdP, a SAML IdP, or guest access into an Identity Pool |
| L13 | You can write least-privilege IAM policies that scope per-user access via `Condition` |
| L14 | You can run `identity_pool_demo.py` offline with `moto` and explain every line |

## Hands-on

No code yet. Read the IAM trust-policy docs for
`cognito-identity.amazonaws.com`:

<https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for_idp_oidc.html#when-to-use-roles-for-web-identity>

Skim the policy-reference docs for
`cognito-identity.amazonaws.com:sub`:

<https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-cognito-identity>

In L13 we'll write policies that use this `sub` condition.

## Quiz prep

For this lecture, focus on:

- The difference between a User Pool and an Identity Pool
- What "federated" means in this context (into AWS, not into the app)
- The 4 token sources an Identity Pool accepts

## Further reading

- AWS docs — Identity Pools: <https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html>
- AWS docs — GetCredentialsForIdentity: <https://docs.aws.amazon.com/cognitoidentity/latest/APIReference/API_GetCredentialsForIdentity.html>
- `../../downloads/cognito_cheat_sheet.pdf`

## What's next

Next is **L12 — Authentication Providers**, where we add OIDC, SAML,
and guest access to an Identity Pool.