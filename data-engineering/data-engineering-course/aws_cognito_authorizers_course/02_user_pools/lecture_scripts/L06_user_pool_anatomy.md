---
lecture: L06
title: "Anatomy of a User Pool — IdP, Directory, App Clients"
duration: "14:00"
section: 2
prereqs:
  - L05
---

# L06 — Anatomy of a User Pool — IdP, Directory, App Clients

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — Cognito User Pools
> **Duration:** 14:00

## Prereqs

- Watched **L05 — Section Overview**.

## Key terms

- **User Pool ID** — a unique 26-character identifier for the pool, e.g.
  `us-east-1_aBcDeFgHi`. The pool's region is encoded in the prefix.
- **User Pool ARN** — `arn:aws:cognito-idp:<region>:<account>:userpool/<id>`.
  Used in IAM policies and CloudFormation.
- **App Client ID** — a public identifier for an application. Not a
  secret. Safe to ship in your SPA bundle or your mobile app binary.
- **App Client Secret** — an optional secret paired with the client ID.
  Only used by confidential clients (server-side apps). Never embed in
  an SPA.
- **User Pool Domain** — a stable hostname for the Hosted UI:
  `https://<prefix>.auth.<region>.amazoncognito.com`. You choose the
  prefix at pool creation; it's globally unique.
- **Resource Server** — defines custom OAuth scopes. e.g. your API at
  `https://api.example.com` with a `read:items` scope.
- **User Pool Group** — a logical grouping of users, used for RBAC
  (e.g. `admins`, `readers`, `writers`).

## Lecture

Welcome back. In L05 I gave you the 30,000-foot view of a User Pool —
the "four things glued together" diagram. Today we crack the box open
and look at every sub-component in detail. By the end of this lecture
you should be able to look at any production Cognito deployment and
name every moving part.

### The User Pool itself

When you `create_user_pool`, you specify:

| Field | What it does | Required? |
|---|---|---|
| `PoolName` | Human-friendly name, unique per account/region | Yes |
| `UsernameAttributes` | `["email"]` for email-as-username, `["phone_number"]` for SMS-as-username, or `[]` for a separate `username` | One of the two patterns |
| `AutoVerifiedAttributes` | Which attributes Cognito auto-verifies (typically `email` and/or `phone_number`) | Recommended |
| `Policies.PasswordPolicy` | Min length, complexity rules, temp-password validity | Yes |
| `Schema` | The list of attributes | Min `email` if email-as-username |
| `AccountRecoverySetting` | How users recover forgotten passwords | Default: email only |
| `AdminCreateUserConfig` | Whether self-sign-up is allowed | Default: admin-only |
| `LambdaConfig` | Triggers (L22) | Optional |
| `EmailConfiguration` | SES vs Cognito sandbox | Default: sandbox |
| `MfaConfiguration` | `OFF` / `ON` / `OPTIONAL` | Default: `OFF` |
| `UserPoolTags` | Arbitrary tags for cost allocation | Optional |

The pool is **regional** — you create it in one AWS region, and it
serves users globally, but the data lives in that region. (Cross-region
replication is not a first-class feature; you can replicate users
yourself with `admin_create_user` if needed.)

### The directory

This is the actual user table. Each user has:

- A `Username` (or, if you set `UsernameAttributes=["email"]`, the
  email address is the username)
- A `sub` claim — a UUID that is **immutable for the user's lifetime**.
  This is the canonical identifier in every JWT.
- A list of `UserAttributes` (the schema you defined)
- A `UserStatus` — `UNCONFIRMED`, `CONFIRMED`, `ARCHIVED`, `COMPROMISED`,
  `UNKNOWN`, `RESET_REQUIRED`, `FORCE_CHANGE_PASSWORD`
- `Enabled` flag
- `MFAOptions` (which MFA methods the user has enrolled in)

You **don't** query the directory with SQL. You use the
`cognito-idp` API: `list_users`, `admin_get_user`, `admin_update_user_attributes`,
etc. The directory is internally sharded across 3 AZs and you have
read-after-write consistency within a single region.

### The IdP list

A User Pool can authenticate users from multiple identity providers.
By default, the pool **is** the IdP (Cognito's own user store). You
can also add:

- **Social IdPs** — Facebook, Google, Amazon, Apple, Twitter
- **SAML 2.0 IdPs** — Okta, Azure AD, PingFederate, OneLogin, ADFS
- **OIDC IdPs** — Auth0, Google, Login.gov, any compliant OIDC provider

When you add a social IdP, your Hosted UI shows a "Sign in with
Google" button. When the user clicks it, they're redirected to Google,
Google authenticates them, and Google sends an authorization code to
your callback URL. The pool then issues its own ID/access/refresh
tokens — the user has been **federated** into your pool.

In section 5 (L24–L25) we go deep on SAML and OIDC federation.

### App Clients

This is the most important sub-component for a working app. An App
Client is a configuration record that says "this app is allowed to
call the pool, and here is what it can do":

| Field | What it does |
|---|---|
| `ClientName` | Human-friendly name (e.g. `web-spa`, `ios-app`, `backend-service`) |
| `GenerateSecret` | If `True`, a secret is generated. **Never** use for SPA/mobile. |
| `AllowedOAuthFlows` | `code`, `implicit` (deprecated), `client_credentials` |
| `AllowedOAuthScopes` | `openid`, `email`, `profile`, plus your custom scopes |
| `AllowedOAuthFlowsUserPoolClient` | Must be `True` for OAuth to work |
| `CallbackURLs` | Where Cognito redirects after auth (your SPA, your app) |
| `LogoutURLs` | Where Cognito redirects after sign-out |
| `SupportedIdentityProviders` | `COGNITO`, `Google`, `SignInWithApple`, etc. |
| `AccessTokenValidity` / `IdTokenValidity` | TTLs in minutes/hours/days |
| `RefreshTokenValidity` | TTL in days (max 3650) |
| `TokenValidityUnits` | The units for the three above |
| `EnableTokenRevocation` | Allow per-token revocation |
| `PreventUserExistenceErrors` | Don't leak whether an email is registered (security best practice) |
| `EnablePropagateAdditionalUserContextData` | Pass extra data to your Lambda authorizer |

You typically have **one app client per environment per platform**:
`web-spa-dev`, `web-spa-prod`, `ios-app-dev`, `ios-app-prod`, etc.

### Resource Servers and custom scopes

If you want to use **OAuth scopes** (L03) to enforce fine-grained
authorization on your API, you need to register a **resource server**
in the pool:

```python
cognito.create_resource_server(
    UserPoolId=pool_id,
    Identifier="https://api.example.com",
    Name="My API",
    Scopes=[
        {"ScopeName": "read:items", "ScopeDescription": "Read items"},
        {"ScopeName": "write:items", "ScopeDescription": "Modify items"},
    ],
)
```

This creates the scopes `https://api.example.com/read:items` and
`https://api.example.com/write:items`. You then add them to the App
Client's `AllowedOAuthScopes`. In section 4 we'll see API Gateway
rejecting requests that don't have the right scope.

### User Pool Groups

Cognito has first-class **groups**. They:

- Are containers of users
- Can have an IAM role attached (so a user in group `admins` gets
  `AdminRole`, a user in group `readers` gets `ReaderRole`)
- Are surfaced in the ID token as the `cognito:groups` claim

When you combine groups with API Gateway Cognito User Pool Authorizer,
you get **RBAC for free**: API Gateway passes the `cognito:groups`
claim to your backend, and your backend can do `if "admins" in
event["requestContext"]["authorizer"]["claims"]["cognito:groups"]: ...`.

### Domain (Hosted UI)

The Hosted UI needs a stable domain. You set it at pool creation:

```python
cognito.create_user_pool_domain(
    Domain="my-app-2026",
    UserPoolId=pool_id,
)
```

The Hosted UI is then at `https://my-app-2026.auth.us-east-1.amazoncognito.com`.
You can also bring your own custom domain (with an ACM certificate) via
`create_user_pool_domain` with `CustomDomainConfig`.

### What we'll build in this section

In L10 we'll create all of the above with boto3, and you'll see
every field we touch mapped to one of these sub-components. The
`create_user_pool.py` script is structured so each sub-component is
its own helper function (`_build_pool_kwargs`, `_build_client_kwargs`,
etc.) so the mapping is one-to-one.

## Hands-on

No code yet. Open the AWS Console and:

1. Go to Cognito → User Pools → "Create user pool".
2. Pick the "Cognito user pool" sign-in experience (not the legacy
   wizard).
3. Step through every page and **write down which sub-component each
   field belongs to** (directory, schema, IdP, app client, …).
4. Don't click "Create" yet — we'll do it programmatically in L10.

## Quiz prep

For this lecture, focus on:

- The 5 sub-components of a User Pool (schema, IdP, directory, app
  clients, plus resource servers / groups / domain)
- Why you should never set `GenerateSecret=True` for an SPA or mobile
  app
- The difference between an App Client and a Resource Server

## Further reading

- AWS docs — app client settings: <https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-client-apps.html>
- AWS docs — resource servers: <https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-define-resource-servers.html>
- `../../downloads/cognito_cheat_sheet.pdf` — every field in one page.

## What's next

Next is **L07 — Sign-up, Sign-in & Custom Attributes**, where we
actually create users and inspect the tokens Cognito hands back.