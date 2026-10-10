---
lecture: L05
title: "Section Overview & Cognito in the AWS Security Ecosystem"
duration: "8:00"
section: 2
prereqs:
  - L01
  - L02
  - L03
  - L04
---

# L05 — Section Overview & Cognito in the AWS Security Ecosystem

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 2 — Cognito User Pools
> **Duration:** 8:00

## Prereqs

- Watched **L01–L04** (mandatory — section 1 is the theory spine for
  everything that follows).

## Key terms

- **Cognito User Pool** — the AWS-managed user directory. Stores users,
  issues OAuth/OIDC tokens, supports MFA, password policies, and
  custom attributes.
- **Identity Provider (IdP)** — the role Cognito plays in the OAuth/OIDC
  flow (L03). It is a "Social IdP" if you federate from Google/Facebook,
  or a "Native IdP" if you store users directly.
- **Directory** — a database of users + their attributes. Cognito's
  directory is a managed, multi-tenant, queryable store backed by
  Amazon's internal infrastructure (not directly accessible; you query
  it via API).
- **App Client** — a configuration object inside a User Pool that says
  "this app is allowed to call the pool, and here is what it can do".
  Each mobile app, web app, and backend service typically gets its own
  App Client.
- **MFA** — Multi-Factor Authentication. Cognito supports SMS, TOTP
  (authenticator apps), and WebAuthn/passkeys (2025+).
- **Hosted UI** — a pre-built login page hosted by Cognito at
  `https://<domain-prefix>.auth.<region>.amazoncognito.com`. Handles
  sign-up, sign-in, MFA, and OAuth flows for you.

## Lecture

Welcome to section 2. Over the next 80 minutes we'll take the OAuth
2.0 and OIDC theory from section 1 and apply it to AWS Cognito User
Pools. By the end of this section you'll have a fully working User
Pool created with boto3, a test user, an app client, and a permanent
password — all reproducible offline with `moto`.

### Where Cognito sits in the AWS security stack

AWS has a **layered** security model. Each layer answers a different
question:

| Layer | Service | Question it answers |
|---|---|---|
| Edge | CloudFront, Route 53, AWS WAF | "Should this request even reach AWS?" |
| Front door | API Gateway, AppSync, ALB | "Is this request well-formed and authorized to reach my backend?" |
| Identity (end users) | **Cognito** | "Who is this end user and what tokens do they have?" |
| Identity (workforce) | IAM Identity Center (SSO) | "Which employee is this, and what AWS accounts/roles can they assume?" |
| Identity (machine) | IAM roles + STS | "Which service is calling me and what IAM permissions does it have?" |
| Authorization | IAM, resource policies | "Is this principal allowed to do this action on this resource?" |
| Audit | CloudTrail, CloudWatch | "Who did what, when, and from where?" |

**Cognito is the identity layer for end users.** The people on the
other side of your REST API, mobile app, or SPA. Not your employees,
not your services, not your EC2 instances.

### Why not just use IAM?

You absolutely can issue an IAM role per user and skip Cognito. It's
the most powerful option: every AWS API call is governed by IAM. But
it's also the worst UX:

- Each end user would need an AWS account.
- You'd be paying $1/month per user for an IAM user (yes, really).
- You'd be writing your own login flow, your own MFA, your own
  password reset emails, your own OAuth provider.
- The IAM console is not a friendly place for non-technical end users.

Cognito exists to give you "almost all of the power of IAM, with the
**UX of a SaaS identity provider**".

### What "fully managed" means here

When you create a User Pool, you are **not** standing up an EC2
instance running a Postgres database. You are configuring a
multi-tenant service. Cognito handles:

- The underlying database
- Replication across 3 AZs
- Encryption at rest (KMS, AWS-managed keys)
- Backups
- Patching
- Compliance certifications (SOC 2, ISO 27001, HIPAA-eligible, PCI
  DSS-eligible)

You bring the configuration: password policy, MFA settings, attribute
schema, app clients, OAuth flows, Lambda triggers, and the
identity-provider list.

### The User Pool mental model

Think of a User Pool as **four things glued together**:

```
+---------------------------------------+
|             User Pool                 |
|                                       |
|  +-------------+   +---------------+  |
|  |  Schema     |   |   IdP list    |  |
|  |  (attrs)    |   |  (Cognito +   |  |
|  |             |   |   social/     |  |
|  +-------------+   |   SAML/OIDC)  |  |
|                    +---------------+  |
|  +-------------+   +---------------+  |
|  |  Directory  |   |   App clients |  |
|  |  (users)    |   |   (per app)   |  |
|  +-------------+   +---------------+  |
+---------------------------------------+
```

| Sub-part | What it is | Where you'll touch it in this course |
|---|---|---|
| Schema | The list of attributes your users have | L07 (custom attributes) |
| IdP list | Who can sign users in (Cognito itself, Google, Okta, …) | L07 (basic), L24–L25 (federation) |
| Directory | The actual user records | L07 (admin_create_user) |
| App clients | Per-app configuration (OAuth flows, secrets, validity) | L09 (Hosted UI), L10 (boto3) |

In L06 we'll unpack each of these in detail.

### What's coming in this section

| Lecture | Outcome |
|---|---|
| L06 | You can describe every sub-component of a User Pool and explain how it maps to boto3 |
| L07 | You can sign a user up, sign them in, and read custom attributes |
| L08 | You can write a password policy and turn on TOTP MFA |
| L09 | You can wire the Hosted UI to your app and pick the right OAuth flow |
| L10 | You can run `create_user_pool.py` offline with `moto` and explain every line |

By the end of L10 you'll be ready to drop Cognito into a real project
in under an hour.

## Hands-on

No code yet. Three things to do before L06:

1. **Sign up for an AWS account** (if you don't have one). Free tier
   is enough.
2. **Create a non-root IAM user** with `AdministratorAccess` and enable
   MFA. Lock the root user away.
3. **Run `aws configure`** so your CLI is wired up. Verify with
   `aws sts get-caller-identity`.

We'll use the same region for the entire course. **Strong
recommendation: `us-east-1`**.

## Quiz prep

For this lecture, focus on:

- Which question does Cognito answer in the AWS security stack?
- What's the difference between Cognito and IAM Identity Center?
- The four sub-parts of a User Pool

## Further reading

- AWS Cognito User Pools overview: <https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html>
- Cognito pricing: <https://aws.amazon.com/cognito/pricing/>
- `../../downloads/cognito_cheat_sheet.pdf`

## What's next

Next is **L06 — Anatomy of a User Pool**, where we look at every
sub-component in detail.