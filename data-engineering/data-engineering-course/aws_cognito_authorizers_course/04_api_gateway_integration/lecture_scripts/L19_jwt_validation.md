---
lecture: L19
title: "Token Validation — JWKS, Expiry, Issuer & Audience"
duration: "18:00"
section: 4
prereqs:
  - L18
---

# L19 — Token Validation — JWKS, Expiry, Issuer & Audience

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 4 — API Gateway + Cognito Authorizer
> **Duration:** 18:00

## Prereqs

- Watched **L18 — Scopes & Groups**.
- Section 1 (L04) for the JWT mental model.

## Key terms

- **JWKS (JSON Web Key Set)** — a JSON document listing the issuer's
  public keys. Always fetched over HTTPS. Always cached.
- **JWK (JSON Web Key)** — a single public key, identified by its
  `kid` (key ID).
- **RSA signature verification** — verifying that the JWT's
  signature is valid for the JWT's `header.payload`, given the JWK
  and the `alg` (always `RS256` for Cognito).
- **Algorithm pinning** — restricting the accepted `alg` value to
  `RS256` only. **Critical for security** — never accept `none` or
  `HS256`.
- **`pyjwt`** — the Python library we use for validation in this
  lecture. `pip install pyjwt[crypto]`.

## Lecture

API Gateway's Cognito User Pool Authorizer does JWT validation for
you. So does HTTP API's JWT Authorizer. So why this lecture?

Three reasons:

1. **You'll write a Lambda Authorizer eventually.** Some teams need
   custom authorization logic (e.g. "deny if the user's tenant is
   suspended"). A Lambda Authorizer is the right tool, and it has to
   validate the JWT itself.
2. **You need to debug "why is my request returning 401?"** — and the
   answer is in the JWT.
3. **You need to understand what API Gateway is doing for you** so
   you can make informed trade-offs (e.g. should you trust the cache
   for 5 minutes or 0?).

By the end of this lecture you'll be able to write a JWT validator
from scratch in 30 lines of Python.

### The 5-step algorithm

```
1. FETCH  https://cognito-idp.<region>.amazonaws.com/<pool-id>/.well-known/jwks.json
   CACHE  it (5 min minimum).

2. DECODE the JWT header. Read alg, kid.

3. REJECT if alg is not in your allowlist (RS256 only).

4. FIND  the JWK in the JWKS whose kid matches the JWT's kid.
   VERIFY the RSA signature with that JWK.

5. CHECK the standard claims:
   • exp > now               (not expired)
   • iss == <issuer>         (from this pool)
   • aud == <app-client-id>  (for this app)
   • optionally: token_use == "id" or "access"
```

If any check fails, reject the token. **Be loud** about why — log
the specific failure for debugging, but don't leak details to the
client (a generic "Unauthorized" is fine for the response).

### The JWKS endpoint

Every Cognito User Pool publishes its public keys at:

```
https://cognito-idp.<region>.amazonaws.com/<pool-id>/.well-known/jwks.json
```

Sample:

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

Cognito rotates keys **rarely** (typically never for a given pool).
You cache this JSON for **at least 5 minutes** in production; many
production systems cache for 1 hour.

### The pyjwt recipe

```python
import json
import time
import urllib.request

import jwt
from jwt.algorithms import RSAAlgorithm

JWKS_URL = (
    "https://cognito-idp.us-east-1.amazonaws.com/"
    "us-east-1_aBcDeFgHi/.well-known/jwks.json"
)
ISSUER = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_aBcDeFgHi"
APP_CLIENT_ID = "7a1b2c3d4e5f6g7h"

_JWKS_CACHE: dict = {"keys": None, "fetched_at": 0.0}


def _get_jwks(force: bool = False) -> dict:
    """Fetch (and cache) the JWKS."""
    if not force and time.time() - _JWKS_CACHE["fetched_at"] < 300:
        return _JWKS_CACHE["keys"]
    with urllib.request.urlopen(JWKS_URL, timeout=2) as r:
        _JWKS_CACHE["keys"] = json.loads(r.read())
    _JWKS_CACHE["fetched_at"] = time.time()
    return _JWKS_CACHE["keys"]


def validate_token(token: str, *, expected_token_use: str = "access") -> dict:
    """Validate a Cognito JWT. Return the payload, or raise."""
    # 1. Decode header to find the kid
    unverified_header = jwt.get_unverified_header(token)
    if unverified_header.get("alg") != "RS256":
        raise ValueError(f"Unexpected alg: {unverified_header.get('alg')}")

    # 2. Pick the matching JWK
    jwks = _get_jwks()
    kid = unverified_header.get("kid")
    key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if key is None:
        raise ValueError(f"kid {kid!r} not in JWKS")

    # 3. Verify signature
    rsa_key = RSAAlgorithm.from_jwk(json.dumps(key))

    # 4. Decode + verify claims in one call
    payload = jwt.decode(
        token,
        key=rsa_key,
        algorithms=["RS256"],            # ← pin algorithm
        audience=APP_CLIENT_ID,          # ← check aud
        issuer=ISSUER,                   # ← check iss
        options={
            "require": ["exp", "iss", "aud", "sub", "token_use"],
        },
    )

    # 5. Extra check for token_use
    if payload.get("token_use") != expected_token_use:
        raise ValueError(
            f"Expected token_use={expected_token_use!r}, "
            f"got {payload.get('token_use')!r}"
        )
    return payload
```

30 lines, including the JWKS cache. This is the entire security
contract of the authorizer.

### Algorithm pinning — the single most important line

```python
algorithms=["RS256"]
```

That's the line that prevents the catastrophic vulnerability. If you
omit it or pass `algorithms=["RS256", "HS256"]`, a malicious client
can forge a token by:

1. Taking a real Cognito JWT.
2. Replacing the header's `alg` with `HS256`.
3. Re-signing the token with the **public** key as the HMAC secret.
4. Sending it to your API.

If you accept `HS256`, your API will verify the HMAC using the
public key (which the attacker has) and the token will pass. The
attacker can now impersonate any user.

**Always pin `algorithms=["RS256"]` for Cognito.**

### The 5 standard claims you must check

| Claim | Check | Why |
|---|---|---|
| `exp` | `> now()` | Not expired |
| `iss` | `== <issuer URL>` | From the right pool |
| `aud` | `== <app client id>` | For the right app |
| `sub` | present | Identity |
| `token_use` | `id` or `access` depending on context | Not the wrong type |

`pyjwt.decode` checks `exp`, `iss`, `aud` automatically when you pass
the matching kwargs. It also raises `MissingRequiredClaimError` for
the `require` list.

### The 7 things you don't need to validate

| | Why |
|---|---|
| `iat` | Just for audit; not a security check |
| `auth_time` | Same |
| `jti` | Used for revocation, but Cognito doesn't honor it via standard claims |
| `email` / `email_verified` | Whatever the issuer says; trust the signature |
| `cognito:groups` | Same |
| Custom claims | Same |
| `nbf` | If present, pyjwt checks it. Otherwise ignore. |

**Trust the signature.** If the signature is valid and the standard
claims pass, every other claim is as good as the issuer's word.

### The Lambda Authorizer pattern

When you want custom authorization (e.g. "deny if the user's tenant
is suspended"), you write a Lambda Authorizer that calls
`validate_token()` and then runs your custom logic:

```python
def authorizer_handler(event, context):
    token = event["authorizationToken"].removeprefix("Bearer ")
    try:
        claims = validate_token(token, expected_token_use="access")
    except (jwt.PyJWTError, ValueError) as e:
        raise Exception(f"Unauthorized: {e}")  # API Gateway returns 401

    # Custom AuthZ
    if claims.get("custom:tenant_status") == "suspended":
        raise Exception("Tenant suspended")

    return {
        "principalId": claims["sub"],
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": "Allow",
                "Resource": event["methodArn"],
            }],
        },
        "context": {k: str(v) for k, v in claims.items()},
    }
```

API Gateway calls this Lambda once per request (or once per cache
window if you've enabled caching). The return value is a
**policy document** — Allow or Deny, optionally scoped to a specific
ARN.

### Caching strategies

| Cache TTL | Behavior |
|---|---|
| `0` (disabled) | Every request re-validates. Slowest, safest. |
| `60` (1 min) | Balance of speed and freshness. |
| `300` (5 min, default) | Most production systems. Revoked tokens valid for up to 5 min. |
| `3600` (1 h) | Best performance. Revoked tokens valid for up to 1 h. |

For most APIs the default 5 minutes is fine. For sensitive endpoints
(set `AuthorizerResultTtlInSeconds=0` per authorizer) cache less.

### What's coming

L20 — end-to-end demo. We put L16–L19 together in one flow.