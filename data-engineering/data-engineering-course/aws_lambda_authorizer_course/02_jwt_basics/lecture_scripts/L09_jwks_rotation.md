---
lecture: L09
title: "JWK and JWKS — Rotating Public Keys"
duration: "18:00"
section: 2
prereqs: ["L08"]
---

# L09 — JWK and JWKS — Rotating Public Keys

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 2 — JWT Basics
> **Duration:** 18:00

## Prereqs

- L08 — signing algorithms.

## Key terms

- **JWK (JSON Web Key)** — a JSON object that represents a single
  public key. Has at least `kty` (key type), `kid` (key id),
  `alg` (intended algorithm), and `use` ("sig" for signature).
- **JWKS (JSON Web Key Set)** — a JSON object with a `keys` array
  of JWKs. Served at a stable URL by the issuer.
- **JWKS endpoint** — the URL the issuer publishes its JWKS at.
  Cognito: `https://cognito-idp.<region>.amazonaws.com/<userpool-id>/.well-known/jwks.json`.
  Auth0: `https://<tenant>.auth0.com/.well-known/jwks.json`.
- **`kid` (key id)** — the field in the JOSE header that tells the
  verifier which JWK in the JWKS to use.
- **Key rotation** — the process of generating a new keypair,
  publishing the new public key on the JWKS endpoint, signing new
  tokens with the new private key, and (after a grace period)
  retiring the old public key.

## Lecture

When the issuer is a third-party IdP (Auth0, Okta, Cognito), your
authorizer doesn't have the public key ahead of time — the issuer
publishes it on a URL. This lecture is about how to fetch that URL,
cache it, and use the right key for the right token.

### A JWK

A single public key, JSON-encoded:

```json
{
  "kty": "RSA",
  "alg": "RS256",
  "use": "sig",
  "kid": "abcd-1234",
  "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86z",
  "e": "AQAB"
}
```

- `kty` — key type. `"RSA"` for RS256, `"EC"` for ES256.
- `alg` — intended algorithm. The verifier can use this as a
  secondary check, but you should still pin the algorithm you
  expect on your side.
- `use` — purpose. `"sig"` for signature verification, `"enc"` for
  encryption. Most JWKS endpoints only publish `"sig"` keys.
- `kid` — the key id. **This is the field the token's JOSE header
  references.** Every token signed with this private key carries
  `"kid": "abcd-1234"` in its header.
- `n`, `e` — the RSA modulus and public exponent. Base64url-encoded,
  big-endian.

### A JWKS

A set of JWKs, served as a JSON document:

```json
{
  "keys": [
    {
      "kty": "RSA", "alg": "RS256", "use": "sig",
      "kid": "abcd-1234",
      "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86z",
      "e": "AQAB"
    },
    {
      "kty": "RSA", "alg": "RS256", "use": "sig",
      "kid": "efgh-5678",
      "n": "1vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86z",
      "e": "AQAB"
    }
  ]
}
```

Two keys are published at the same time. Why? **Rotation.**

### Key rotation

You never want a single key signing tokens forever. The standard
rotation pattern is:

1. **Generate** a new keypair (`kid: efgh-5678`).
2. **Publish** the new public key on the JWKS endpoint. The endpoint
   now lists two keys: `abcd-1234` (still used to sign) and
   `efgh-5678` (advertised but not yet used).
3. **Wait** for any caches in the verifier population to pick up
   the new endpoint. 5 minutes is the typical grace period; you
   can enforce this with the JWKS endpoint's `Cache-Control:
   max-age=300` header.
4. **Switch** the IdP to sign new tokens with the new private key.
   Existing tokens signed with the old key are still valid.
5. **Wait** for the longest-lived token to expire (15 minutes for
   access tokens; up to 24 hours for some refresh flows).
6. **Retire** the old public key by removing it from the JWKS
   endpoint. Old tokens are now un-verifiable.

The grace period between (2) and (6) is the window where both keys
are valid. This is what lets you rotate keys **without downtime**.

### The author's JWKS-handling code

A typical authorizer caches the JWKS in memory (and optionally
revalidates with the endpoint on a TTL):

```python
import time
import requests
import jwt
from jwt import PyJWKClient

_JWKS_URL = "https://auth.example.com/.well-known/jwks.json"
_jwks_client = PyJWKClient(_JWKS_URL, cache_keys=True, lifespan=300)

def verify_token(token: str) -> dict:
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience="api.example.com",
        issuer="https://auth.example.com",
    )
```

`PyJWKClient` does the heavy lifting:

- Fetches the JWKS endpoint (lazily, on first call).
- Caches the keys in memory for `lifespan` seconds.
- Looks up the right key by `kid` from the token's JOSE header.
- Raises `jwt.PyJWKClientError` if the `kid` isn't in the cache
  (the token was signed by a key you don't know about — the right
  thing to do is refresh the cache and try once, then fail).

### What to do when `kid` is unknown

If a token comes in with `"kid": "zzzz-9999"` and that key isn't
in the JWKS cache, it means one of three things:

1. **The IdP rotated keys** and you haven't refreshed the cache.
   → Force-refresh the JWKS and retry.
2. **The token is forged** and the attacker is guessing `kid`s.
   → Return Deny.
3. **The token is from a different IdP** (algorithm confusion or
   misconfiguration). → Return Deny.

A reasonable strategy is: on `PyJWKClientError`, do **one** forced
refresh, then fail closed. The second failure is never legitimate.

### What to do when the JWKS endpoint is down

`requests.exceptions.RequestException`. Three options:

- **Fail closed** (recommended for most APIs). Return Deny. Better
  to take an outage than to silently let unauthenticated traffic
  through.
- **Fail open** (only for public-health-check endpoints). Allow
  with a warning. The cost is that an attacker who can DoS the
  JWKS endpoint can also bypass your auth.
- **Use the stale cache**. If your cache TTL is 24 h and the
  endpoint has been down for 5 minutes, the cache is still
  authoritative. Return Allow based on the cached keys, log a
  warning, page on-call.

## Hands-on

The working code in L10 demonstrates the JWKS-less case (a single
in-process keypair). To exercise the JWKS case you'll need a real
issuer; the easiest is to run a local JWKS server with
`python -m http.server` serving a static `jwks.json`, but the
section 4 demo is a more realistic exercise.

## Quiz prep

- What does `kid` mean in a JWT header?
- How long should you cache a JWKS in your authorizer?
- What should you do if the JWKS endpoint is down?

## Further reading

- RFC 7517 — JSON Web Key (JWK).
- Auth0 docs: [JSON Web Key Sets](https://auth0.com/docs/secure/tokens/json-web-tokens/json-web-key-sets).

## What's next

**L10 — Verifying a JWT in Pure Python** — the hands-on lab. We
generate a keypair, sign a JWT, verify it, and write five unit
tests covering the failure modes.
