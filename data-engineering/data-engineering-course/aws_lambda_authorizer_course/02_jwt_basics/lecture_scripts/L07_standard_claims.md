---
lecture: L07
title: "Standard Claims — iss, sub, aud, exp, nbf, iat, jti"
duration: "16:00"
section: 2
prereqs: ["L06"]
---

# L07 — Standard Claims — iss, sub, aud, exp, nbf, iat, jti

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 2 — JWT Basics
> **Duration:** 16:00

## Prereqs

- L06 — JWT structure.

## Key terms

The seven RFC-defined claims (the "registered claims") you should
expect to see in any production JWT:

- **`iss` (issuer)** — *who minted the token*. A URL identifying
  the IdP. Your authorizer should reject tokens whose `iss` isn't
  one you trust.
- **`sub` (subject)** — *who the token is about*. The user id, the
  service account, the API key name. Becomes `principalId` in the
  policy.
- **`aud` (audience)** — *who the token is intended for*. Should be
  a string (or array of strings) naming your API. Your authorizer
  should reject tokens whose `aud` doesn't include you — otherwise a
  token minted for a different service could be replayed against
  yours.
- **`exp` (expiration)** — when the token stops being valid. Numeric
  date (seconds since the Unix epoch). Your authorizer MUST reject
  expired tokens.
- **`nbf` (not before)** — when the token *starts* being valid.
  Optional; rare in access tokens.
- **`iat` (issued at)** — when the token was minted. Useful for
  cache keys and for "max token age" policies (e.g. reject tokens
  older than 24 h even if they haven't expired).
- **`jti` (JWT id)** — a unique identifier for this specific token.
  Used to implement one-time-use tokens or to look the token up in
  a revocation list.

## Lecture

A JWT without claims is just a signed assertion. The claims are what
make it useful — they're the structured fields your authorizer
inspects to decide Allow or Deny. Of the seven, **`iss`, `sub`, `aud`,
and `exp` are the four your authorizer should always check**.

### `iss` (issuer)

```json
"iss": "https://auth.example.com"
```

The `iss` claim is the URL of the IdP that minted the token. Pin
this in your authorizer:

```python
claims = jwt.decode(token, public_key, algorithms=["RS256"],
                    issuer="https://auth.example.com")
```

If the token was minted by a different issuer, PyJWT raises
`jwt.InvalidIssuerError` and you return a Deny.

### `sub` (subject)

```json
"sub": "user-12345"
```

The `sub` is the *thing the token is about* — usually a user id.
It's the canonical value to put in `principalId`. A common pattern
is `f"user|{sub}"` for Cognito or `sub` directly for first-party
auth.

### `aud` (audience)

```json
"aud": "api.example.com"
```

The `aud` claim is the *intended recipient*. It can be a string or
an array of strings:

```json
"aud": ["api.example.com", "admin.example.com"]
```

A token minted for `api-b.example.com` must NOT be accepted by
`api.example.com`. The `aud` check is what stops a token from being
replayed across services that happen to share a signing key.

Pin it in your authorizer:

```python
claims = jwt.decode(token, public_key, algorithms=["RS256"],
                    audience="api.example.com")
```

### `exp` (expiration)

```json
"exp": 1700000000
```

Numeric date (seconds since 1970-01-01 UTC). The token is invalid
after this moment. PyJWT checks this automatically when you call
`jwt.decode` and raises `jwt.ExpiredSignatureError`.

A 5-minute access token is a sane default for service-to-service
calls. A 15-minute access token is the OAuth2 / OIDC default. A
24-hour access token is the practical upper bound; anything longer
should be a refresh token, not an access token.

### `nbf` (not before)

```json
"nbf": 1700000000
```

Numeric date. The token is invalid *before* this moment. PyJWT
checks this automatically.

In practice `nbf` is rare for access tokens (the IdP would just
*not* mint the token yet). It's used by some refresh-token flows
where the IdP wants to delay token activation.

### `iat` (issued at)

```json
"iat": 1699996400
```

Numeric date. The moment the token was minted. PyJWT does *not*
check `iat` automatically — but you can use it for a "max age"
policy:

```python
MAX_AGE_SECONDS = 24 * 3600
if (int(time.time()) - claims["iat"]) > MAX_AGE_SECONDS:
    return _deny(method_arn)
```

This protects you against a long-lived token that an attacker
captured and is replaying after the original session has ended.

### `jti` (JWT id)

```json
"jti": "9c3a4e1d-2c1f-4d8e-b6a7-1234567890ab"
```

A unique identifier for this *specific* token. The verifier can
keep a list of revoked `jti`s (e.g. in a Redis set) and reject any
token whose `jti` is in the list. This is the "log out everywhere"
mechanism.

The trade-off: every authorizer call now hits Redis, which adds
latency. Most teams use a short access-token TTL (5–15 min) and
skip the explicit revocation list.

### Putting it all together

A well-formed access token for `api.example.com` issued by
`auth.example.com` might look like:

```json
{
  "iss": "https://auth.example.com",
  "sub": "user-12345",
  "aud": "api.example.com",
  "exp": 1700000900,
  "iat": 1700000000,
  "jti": "9c3a4e1d-2c1f-4d8e-b6a7-1234567890ab",
  "tenant": "acme",
  "scope": "read"
}
```

In your authorizer:

```python
claims = jwt.decode(
    token,
    public_key,
    algorithms=["RS256"],
    audience="api.example.com",
    issuer="https://auth.example.com",
    options={"require": ["exp", "iat", "iss", "sub", "aud"]},
)
```

The `options={"require": [...]}` line tells PyJWT to reject the
token if any of the required claims is missing. **Always set this
list** — a token that omits `exp` is, by default, a token that
never expires.

## Hands-on

Decode the example token in `02_jwt_basics/code/jwt_verify.py` and
check the claims by hand. We'll automate this in L10.

## Quiz prep

- Which four claims should your authorizer always check?
- What's the difference between `exp` and `iat`?
- What does `options={"require": [...]}` do in `jwt.decode`?

## Further reading

- RFC 7519 §4.1 — the registered claims.

## What's next

**L08 — Signing Algorithms** — HS256 (HMAC) vs RS256 (RSA) vs ES256
(ECDSA). When to pick which and why the choice matters for security.
