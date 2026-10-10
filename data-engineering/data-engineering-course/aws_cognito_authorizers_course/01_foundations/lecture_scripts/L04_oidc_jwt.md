---
lecture: L04
title: "OpenID Connect (OIDC) & JWTs"
duration: "15:00"
section: 1
prereqs:
  - L03
---

# L04 — OpenID Connect (OIDC) & JWTs

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 1 — Foundations
> **Duration:** 15:00

## Prereqs

- Watched **L03 — OAuth 2.0** (mandatory).

## Key terms

- **OpenID Connect (OIDC)** — a thin **authentication** layer on top of
  OAuth 2.0. Defined in the OpenID Connect Core 1.0 spec. Adds the
  **ID token**, the **UserInfo endpoint**, and standardized claims.
- **ID Token** — a JWT that asserts the user's identity. The audience
  is the **client**, not the resource server. Section 4 will be all
  about validating these.
- **JSON Web Token (JWT)** — RFC 7519. Three Base64URL sections
  (`header.payload.signature`) carrying JSON claims, signed (typically
  with RS256) by the issuer. **Not encrypted** — the payload is
  readable by anyone who has the token.
- **JWS / JWE** — JWT is the umbrella; JWS is signed; JWE is encrypted.
  Cognito issues JWS.
- **JWKS (JSON Web Key Set)** — a JSON document at a stable URL that
  lists the issuer's public keys. Validation always starts here.
- **Claims** — name/value pairs in the JWT payload. Standard claims:
  `iss`, `sub`, `aud`, `exp`, `iat`, `nbf`, `jti`. Custom claims:
  anything else.

## Lecture

Welcome back. In L03 we built the **OAuth 2.0** delegation protocol —
the part that handles **authorization** ("what can this client do?").
Today we add **authentication** ("who is the user?") on top of it.
The combination is called **OpenID Connect** — and it's the most
deployed authentication protocol in the world. Every "Sign in with
Google" button you've ever clicked uses it.

### OIDC in one sentence

> OIDC = OAuth 2.0 + an ID token, plus a UserInfo endpoint, plus
> standardized identity claims.

That's the delta from L03. The OAuth flows are unchanged; you add one
new token (the **ID token**) and a few new endpoints.

### The ID token — what it is and what it isn't

The **ID token** is a JWT. Its job is to **prove to the client that
the user just authenticated at the authorization server**. That's it.

The audience (`aud`) of an ID token is the **client** — the SPA, the
mobile app — that just received it. **Not** your API. If you put an
ID token in an `Authorization: Bearer ...` header and send it to your
API, your API will reject it (assuming the API knows what it's doing)
because `aud` won't match.

What your API wants is the **access token**. Different token,
different audience, different purpose.

| | ID Token | Access Token |
|---|---|---|
| Audience | Client | Resource Server (your API) |
| Purpose | "Who is the user?" | "What can this caller do?" |
| Standard claims | `iss`, `sub`, `aud=client`, `exp`, `email`, `name` | `iss`, `sub`, `aud=api`, `exp`, `scope`, `client_id` |
| Carries user info? | Yes (claims are the user info) | No (just scopes + client_id) |
| Lifetime | 60 min default | 60 min default (often shorter) |
| Sent to API? | No (don't!) | Yes (`Authorization: Bearer`) |

### A JWT, dissected

```
eyJraWQiOiJrLTYzX2ZRQTI4VTMifQ  ← header (Base64URL-decoded below)
.eyJzdWIiOiI1MDVjMWJmYS00ZWIzLTRkZmItYjA3Ny00Y2Y4YyJ9  ← payload
.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c          ← signature
```

Header:

```json
{ "alg": "RS256", "typ": "JWT", "kid": "k-63_fQA49" }
```

Payload (standard claims):

```json
{
  "sub": "505c1bfa-4eb3-4dfb-b077-4cf8c",
  "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_aBcDe",
  "aud": "7a1b2c3d4e5f6g7h",
  "exp": 1730659200,
  "iat": 1730655600,
  "auth_time": 1730655500,
  "token_use": "id",
  "email": "alice@example.com",
  "email_verified": true,
  "cognito:username": "alice@example.com",
  "cognito:groups": ["admins"]
}
```

Signature: RSA over `header.payload` using the issuer's private key.
Anyone with the matching public key (everyone — it's published at the
JWKS endpoint) can verify.

### The validation algorithm — the only thing section 4 will test you on

```
1. FETCH  https://cognito-idp.<region>.amazonaws.com/<pool-id>/.well-known/jwks.json
   CACHE  it (5 min TTL) — never call Cognito per request.

2. DECODE the JWT header (Base64URL). Look at alg, kid.

3. PICK  the JWK from the JWKS whose kid matches.

5. Reject if alg is not in your allowlist (RS256 only for Cognito;
   never accept "none", HS256 with shared secrets, etc).

6. VERIFY the RSA signature with the JWK's public key.

7. CHECK  the standard claims:
   • exp > now  (token not expired)
   • iss == https://cognito-idp.<region>.amazonaws.com/<pool-id>
   • aud == <your-app-client-id>
   • token_use == "id"  (or "access", depending on which token you got)
```

**Step 5 is the security-critical one.** If you accept `alg: none` or
`alg: HS256` with the public key as the secret, your API is wide open.
Cognito only ever signs with `RS256`, so anything else is a forgery
attempt and must be rejected.

### The JWKS endpoint — your cache's best friend

```
https://cognito-idp.us-east-1.amazonaws.com/us-east-1_aBcDe/.well-known/jwks.json
```

Returns:

```json
{
  "keys": [
    {
      "kid": "k-63_fQA49",
      "kty": "RSA",
      "alg": "RS256",
      "use": "sig",
      "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQ2...",
      "e": "AQAB"
    }
  ]
}
```

Cognito rotates keys **rarely** (typically never for a given pool). You
cache this JSON for 5 minutes minimum; many production systems cache
for hours.

### What Cognito gives you vs what you have to write

| Step | Cognito does it? |
|---|---|
| Sign the ID token with RS256 | Yes |
| Publish the public key at JWKS | Yes |
| Issue ID + access + refresh tokens | Yes |
| Set `iss`, `aud`, `exp`, `sub` | Yes |
| **Verify** the signature on your API | **API Gateway does it for you** (Cognito User Pool Authorizer) |
| Check `aud`, `iss`, `exp` on your API | **API Gateway does it for you** |
| Read custom claims (`cognito:groups`, `email`) | Your backend reads them from the validated JWT context |

In other words: with **API Gateway + Cognito User Pool Authorizer**,
you don't write any of the JWT validation code in section 4 — API
Gateway does it for you. The lecture still teaches you the recipe
(L19) so you know what it's doing and so you can write a Lambda
Authorizer that does its own validation (L37 in the Lambda course).

### Section 1 mental model — complete

> OAuth 2.0 is an authorization delegation framework. OpenID Connect
> adds an authentication layer on top. The ID token is a signed
> assertion of identity issued by the OpenID Provider after successful
> authentication. The access token is a bearer authorization credential
> used to call protected APIs.

You now have the entire vocabulary you need for sections 2–5. Section
2 is going to start handing you real Cognito resources, and every
phrase — "User Pool", "App Client", "Hosted UI", "scope", "JWKS" — is
something you can now place in the right box.

## Hands-on

No code. Decode a real ID token by hand (just `base64.urlsafe_b64decode`
the middle section, no signature verification). Write down every
claim. Confirm: is `aud` your App Client ID? Is `iss` your user pool
URL? Is `exp` in the future? Is `token_use == "id"`?

In section 2 we'll mint these tokens with `boto3` and verify them
with `pyjwt`.

## Quiz prep

For this lecture, focus on:

- The difference between an ID token and an access token
- Why the JWT signature is the only thing that proves authenticity
- The 5 steps of the validation algorithm
- Why you must pin `alg: RS256` (and reject `alg: none`)

## Further reading

- OpenID Connect Core 1.0: <https://openid.net/specs/openid-connect-core-1_0.html>
- RFC 7519 — JSON Web Token: <https://datatracker.ietf.org/doc/html/rfc7519>
- RFC 7517 — JSON Web Key: <https://datatracker.ietf.org/doc/html/rfc7517>
- Cognito JWT verification: <https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying.html>
- `../../downloads/jwt_validation_cheat_sheet.pdf` — pin it.

## What's next

Section 1 is done. Next stop: **Section 2 — Cognito User Pools**, where
we use everything we just learned to create a real User Pool with
boto3 and then sign a user in with `initiate_auth`.