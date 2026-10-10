---
lecture: L07
title: "Sign-up, Sign-in & Custom Attributes"
duration: "14:00"
section: 2
prereqs:
  - L06
---

# L07 — Sign-up, Sign-in & Custom Attributes

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 2 — Cognito User Pools
> **Duration:** 14:00

## Prereqs

- Watched **L06 — User Pool Anatomy**.

## Key terms

- **Sign-up** — creating a new user. Two flavors: **admin-created** (the
  app creates the user with `admin_create_user`) or **self-sign-up**
  (the user signs themselves up through the Hosted UI or a custom UI).
- **Sign-up confirmation** — verifying the user's email or phone
  number. Cognito sends a 6-digit code; the user enters it; the user's
  status moves from `UNCONFIRMED` to `CONFIRMED`.
- **InitiateAuth** — the API call that returns the ID/access/refresh
  tokens. The most common auth flow is `USER_PASSWORD_AUTH` (server
  side, no SRP) or `USER_SRP_AUTH` (more secure, client side).
- **Custom attributes** — user attributes beyond the standard schema
  (e.g. `tenant_id`, `plan`, `signup_source`). Defined in the pool
  schema; accessible in tokens and via `admin_get_user`.
- **User status** — `UNCONFIRMED`, `CONFIRMED`, `ARCHIVED`,
  `COMPROMISED`, `RESET_REQUIRED`, `FORCE_CHANGE_PASSWORD`.

## Lecture

In L06 we looked at the static structure of a User Pool. Today we
make it dynamic: we create users, sign them in, and inspect the
tokens. By the end of this lecture you should be able to look at a
Cognito-issued ID token and know which claims are standard, which
are custom, and which your app should care about.

### Two ways to create a user

| | Admin-created | Self-sign-up |
|---|---|---|
| API call | `admin_create_user` | `sign_up` (or Hosted UI) |
| Cognito sends welcome email? | Yes (configurable) | No (user just signed up themselves) |
| User status at creation | `FORCE_CHANGE_PASSWORD` (or `CONFIRMED` if you set permanent password) | `UNCONFIRMED` |
| Verification needed? | Optional (you can set `email_verified=true` directly) | Yes — user must enter the code |
| Use case | First-party admin tools, internal apps | Public-facing apps, "create your account" flows |

For the course we'll use **admin-created users** with a permanent
password (we set this in `create_user_pool.py` via
`admin_set_user_password(Permanent=True)`). This makes the tests
simple and avoids needing a real email inbox.

In production you usually want a mix: admin creates internal users
with permanent passwords, public sign-up handles the rest.

### Sign-up confirmation

If you create a user with `admin_create_user` and don't set
`email_verified=true`, Cognito sends a welcome email with a
temporary password. The user's status is `FORCE_CHANGE_PASSWORD`.
On first sign-in, Cognito will require the user to change the
password (the `NEW_PASSWORD_REQUIRED` challenge).

If you set `email_verified=true` and call `admin_set_user_password`
with `Permanent=True`, the user can sign in immediately with the
permanent password. No challenge, no email. This is the path we
take in the course.

### Sign-in: the auth flows

| Auth flow | Who computes what | Secure? | Notes |
|---|---|---|---|
| `USER_SRP_AUTH` | Client uses SRP (Secure Remote Password) | **Yes** | Recommended for client-side auth |
| `USER_PASSWORD_AUTH` | Client sends password over TLS | OK | Only over TLS; only for first-party apps |
| `ADMIN_USER_PASSWORD_AUTH` | Server uses admin creds + user's password | OK | For migration / testing only |
| `REFRESH_TOKEN_AUTH` | Send refresh token, get new access token | Yes | Silent refresh — invisible to the user |
| `CUSTOM_AUTH` | Lambda challenges (L21) | Depends | Most flexible, most code |
| `USER_AUTH` | Wrapper for federated / SRP | Yes | Newer, Cognito-recommended client-side flow |

In `create_user_pool.py` we use `USER_PASSWORD_AUTH` because the test
needs to sign a user in without a network round-trip to a Hosted UI.
In production you'd use `USER_SRP_AUTH` (server-side) or the
Hosted UI (browser-side, OAuth code flow).

### The token response

After a successful sign-in, Cognito returns:

```json
{
  "AuthenticationResult": {
    "AccessToken": "eyJraWQi...",
    "ExpiresIn": 3600,
    "IdToken": "eyJraWQi...",
    "RefreshToken": "eyJjdHki...",
    "TokenType": "Bearer"
  }
}
```

| Token | What it is | When to use it |
|---|---|---|
| `AccessToken` | Bearer credential for your API | Every API call: `Authorization: Bearer <accessToken>` |
| `IdToken` | Asserts user identity (claims) | To display user info; **not** to authorize API calls |
| `RefreshToken` | Long-lived credential to mint new access tokens | Silent refresh, 30 days by default |
| `ExpiresIn` | Seconds until `AccessToken` expires | Your client should refresh at ~75% of this |

Both `AccessToken` and `IdToken` are JWTs. Both are signed with the
pool's private key. Both can be verified against the pool's JWKS
endpoint. They differ in **claims** and **audience**.

### Decoding the ID token (offline, no verification)

```python
import jwt, json
id_token = auth["AuthenticationResult"]["IdToken"]
payload = jwt.decode(id_token, options={"verify_signature": False})
print(json.dumps(payload, indent=2))
```

For a pool with `UsernameAttributes=["email"]` and a single group
`admins`, you get something like:

```json
{
  "sub": "505c1bfa-4eb3-4dfb-b077-4cf8c",
  "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_aBcDe",
  "aud": "7a1b2c3d4e5f6g7h",
  "exp": 1730659200,
  "iat": 1730655600,
  "auth_time": 1730655500,
  "jti": "abc-123-...",
  "token_use": "id",
  "email": "alice@example.com",
  "email_verified": true,
  "cognito:username": "alice@example.com",
  "cognito:groups": ["admins"]
}
```

The `sub` is the canonical user identifier — it never changes for the
life of the user, even if they change their email. Always log
`sub`, never log the email.

### Custom attributes

Standard attributes are fixed (email, name, phone_number, …). For
anything else you need **custom attributes**:

```python
cognito.add_custom_attributes(
    UserPoolId=pool_id,
    CustomAttributes=[
        {"Name": "tenant_id",  "AttributeDataType": "String",  "Mutable": True},
        {"Name": "plan",       "AttributeDataType": "String",  "Mutable": True},
        {"Name": "signup_at",  "AttributeDataType": "Number",  "Mutable": False},
    ],
)
```

Rules:

- Custom attribute names are prefixed with `custom:` in tokens. So
  `tenant_id` becomes `custom:tenant_id` in the JWT payload.
- Names are ≤ 20 chars.
- You can have up to 50 custom attributes.
- A custom attribute is **always optional** — even if you mark it
  `Required: True` at the schema level, Cognito won't enforce it
  (schema-level `Required` is honored for standard attributes only).

To set a custom attribute on a user:

```python
cognito.admin_update_user_attributes(
    UserPoolId=pool_id,
    Username="alice@example.com",
    UserAttributes=[
        {"Name": "custom:tenant_id", "Value": "acme-corp"},
        {"Name": "custom:plan",      "Value": "pro"},
    ],
)
```

After the next sign-in, `custom:tenant_id` and `custom:plan` will
appear in the ID token.

### Common attribute gotchas

1. **Standard attribute names are case-sensitive.** `Email` ≠ `email`.
   Always use lowercase: `email`, `name`, `phone_number`.
2. **Custom attributes need the `custom:` prefix in JWTs and API
   calls** but not in the schema. The schema name is the bare name;
   the JWT/API name is `custom:<bare>`.
3. **`email_verified` is read-only.** You set it via
   `admin_update_user_attributes` (and only as `true` or `false`), not
   by the user.
4. **You can't delete a custom attribute after creation.** You can mark
   it `Mutable: False` and stop writing to it, but the column lives
   forever.

## Hands-on

In L10 we'll exercise every API call from this lecture in
`create_user_pool.py` and verify them with moto. For now, in the AWS
Console:

1. Go to your pool → "Users" tab → "Create user".
2. Fill in `alice@example.com`, leave "Send an invitation" checked.
3. Note the temporary password from the email (or the console).
4. Copy the pool's JWKS URL (Pool details → "User pool ID" → construct
   the URL: `https://cognito-idp.<region>.amazonaws.com/<pool-id>/.well-known/jwks.json`).
5. Use the AWS CLI to sign in:

```bash
aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id <APP_CLIENT_ID> \
    --auth-parameters USERNAME=alice@example.com,PASSWORD=<the-temp-pw>
```

You get an access token. Decode it with `pyjwt` (no signature
verification yet) and inspect the claims.

## Quiz prep

For this lecture, focus on:

- The two ways to create a user (admin vs self-sign-up)
- The difference between an ID token and an access token
- The `sub` claim and why you should always log it, never the email
- How to add and use a custom attribute

## Further reading

- AWS docs — sign-up: <https://docs.aws.amazon.com/cognito/latest/developerguide/signing-up-users-in-your-app.html>
- AWS docs — token usage: <https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens.html>
- AWS docs — custom attributes: <https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html>
- `../../downloads/cognito_cheat_sheet.pdf`

## What's next

Next is **L08 — Password Policy, MFA & Account Recovery**, where we
harden the pool against common attacks.