---
lecture: L24
title: "OIDC Integration — Auth0, Okta, Cognito as the IdP"
duration: "16:00"
section: 5
prereqs: ["L23"]
---

# L24 — OIDC Integration — Auth0, Okta, Cognito as the IdP

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 5 — Advanced Patterns
> **Duration:** 16:00

## Prereqs

- L23 — WebSocket challenges.

## Key terms

- **OIDC (OpenID Connect)** — an identity layer on top of OAuth2.
  The relevant piece for Lambda Authorizers is that OIDC defines
  how an IdP issues an **ID token** (a JWT) to a client.
- **`id_token` vs `access_token`** — OIDC clients receive both.
  The `id_token` proves who the user is (use for
  authentication); the `access_token` proves the user is allowed
  to call the API (use for authorization).
- **`/.well-known/openid-configuration`** — the discovery endpoint
  every OIDC IdP publishes. Lists the JWKS URI, the issuer, the
  supported algorithms, etc.
- **JWKS URL** — the URL that serves the IdP's public signing
  keys. Format: `<idp-host>/.well-known/jwks.json`.

## Lecture

If your IdP is **Auth0, Okta, Cognito, or any other OIDC-compliant
provider**, your job is much simpler than rolling your own JWT
system. The IdP mints signed JWTs; your authorizer just has to
verify them.

The pattern is identical to L09. The only difference is the URL
of the JWKS.

### Discovery

Every OIDC IdP publishes a discovery document at:

```
GET https://<idp-host>/.well-known/openid-configuration
```

The response is JSON:

```json
{
  "issuer": "https://auth.example.com",
  "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
  "authorization_endpoint": "https://auth.example.com/authorize",
  "token_endpoint": "https://auth.example.com/oauth/token",
  "userinfo_endpoint": "https://auth.example.com/userinfo",
  …
}
```

For your authorizer, the two fields you care about are
**`issuer`** and **`jwks_uri`**.

### Provider-specific JWKS URLs

| Provider | JWKS URL |
|---|---|
| **Auth0** | `https://<tenant>.auth0.com/.well-known/jwks.json` |
| **Okta** | `https://<org>.okta.com/oauth2/v1/keys` |
| **AWS Cognito** | `https://cognito-idp.<region>.amazonaws.com/<user-pool-id>/.well-known/jwks.json` |
| **Google** | `https://www.googleapis.com/oauth2/v3/certs` |
| **Azure AD** | `https://login.microsoftonline.com/<tenant-id>/discovery/v2.0/keys` |

### A reference verifier

```python
import jwt
from jwt import PyJWKClient

JWKS_URL = "https://auth.example.com/.well-known/jwks.json"
_jwks = PyJWKClient(JWKS_URL, cache_keys=True, lifespan=3600)


def verify(token: str, *, audience: str, issuer: str) -> dict:
    signing_key = _jwks.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=audience,
        issuer=issuer,
        options={"require": ["exp", "iat", "iss", "sub", "aud"]},
    )
```

That's it. `PyJWKClient` handles the cache and the `kid` lookup
for you.

### Cognito-specific gotchas

Cognito is the most common IdP for AWS-native systems. Three
things to know:

1. **The JWKS URL is per-user-pool.** `<user-pool-id>` is unique
   to your pool.
2. **The `aud` claim is the Cognito *app client* id**, not your
   API id. Configure this in the user's app client settings.
3. **Cognito tokens have a `token_use` claim** —
   `"access"` for access tokens, `"id"` for ID tokens. Your
   authorizer should check:

```python
if claims.get("token_use") != "access":
    return _deny(method_arn)
```

This stops an ID token (which is meant for *your* client, not
your server) from being replayed against your API.

### Auth0-specific gotchas

1. **Auth0 tenants are per-environment.** The dev tenant is
   different from the prod tenant. Bake the right tenant URL into
   the Lambda at deploy time.
2. **Auth0 supports multiple algorithms.** HS256, RS256, and ES256
   are all on by default. Pin the one your app uses:

```python
jwt.decode(token, key, algorithms=["RS256"])  # pin it
```

### Okta-specific gotchas

1. **Okta tokens carry a `scp` (scope) claim** as an array, not a
   space-separated string. Don't `claims["scope"].split()` —
   iterate:

```python
if "admin" not in claims.get("scp", []):
    return _deny(method_arn)
```

2. **Okta rotates keys every 30 days.** Your JWKS cache TTL
   should be 1 day (86400 s) so you pick up rotations promptly.

## Hands-on

There's no runnable code in this lecture. The full OIDC + JWKS +
PyJWKClient demo is in section 4's working code (see
`04_policy_cache/code/param_authorizer.py` for the pattern, with
a static dict in place of a real JWKS).

To exercise this end-to-end, sign up for an Auth0 free-tier
account, create a tenant, configure an RS256 application, mint
a test token, and point your authorizer at the tenant's JWKS.

## Quiz prep

- What's the difference between an `id_token` and an `access_token`?
- What is the JWKS URL format for Cognito / Auth0?
- Why should you pin the algorithm on the verifier side?

## Further reading

- OpenID Connect Discovery 1.0 spec.
- AWS docs: [Verifying a JSON Web Token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html).

## What's next

**L25 — When NOT to Use a Lambda Authorizer — Design Trade-offs**.
The closing lecture.