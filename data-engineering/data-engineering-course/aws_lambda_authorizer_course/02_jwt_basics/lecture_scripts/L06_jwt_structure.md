---
lecture: L06
title: "JWT Structure — Header, Payload, Signature (base64url)"
duration: "14:00"
section: 2
prereqs: ["L05"]
---

# L06 — JWT Structure — Header, Payload, Signature (base64url)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 2 — JWT Basics
> **Duration:** 14:00

## Prereqs

- L05 — section overview.

## Key terms

- **base64url** — the URL-safe variant of base64. Replaces `+` with
  `-`, `/` with `_`, and drops the `=` padding. The whole point is
  that the token is safe to drop into a URL, a header, or a JSON
  string without escaping.
- **JOSE Header** — the first part of a JWT. Always a JSON object
  with at least `alg` and usually `typ: "JWT"`.
- **JWS** — JSON Web Signature. The signed form of a JWT (what
  everyone calls a "JWT"). The signature is the third part.
- **JWE** — JSON Web Encryption. The encrypted form. Out of scope
  for this course.
- **Compact serialization** — the three-part dot-separated string.
  Defined in RFC 7515.

## Lecture

A JWT is a string with three dot-separated parts:

```
<header>.<payload>.<signature>
```

Each part is **base64url-encoded JSON**. The whole token is **signed,
not encrypted** — anyone with the token can read the payload. The
signature is what proves the issuer minted it.

### The header

The first part is the JOSE header. It tells the verifier which
algorithm was used and what kind of token this is:

```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "abcd-1234"
}
```

- `alg` — the signing algorithm. `RS256` means RSASSA-PKCS1-v1_5 with
  SHA-256. `HS256` means HMAC with SHA-256. **Pin this on the
  verifier side** — never let the token choose.
- `typ` — almost always `"JWT"`. Some IdPs use `"at+jwt"` for access
  tokens per RFC 9068.
- `kid` — the key id. The IdP may have many signing keys; `kid` tells
  the verifier which public key to use to check the signature. This
  is the hook L09's JWKS rotation depends on.

### The payload

The second part is the claims — the identity information the issuer
is asserting about the subject:

```json
{
  "sub": "user-12345",
  "iss": "https://auth.example.com",
  "aud": "api.example.com",
  "exp": 1700000000,
  "iat": 1699996400,
  "tenant": "acme",
  "scope": "read"
}
```

The first five fields are standard (covered in L07). The last two
are custom — anything you want, as long as it's serializable as JSON
and not too big (a JWT is supposed to fit in a header; 8 KB is a
sane upper bound).

### The signature

The third part is the signature. For RS256 it's:

```
base64url(RSA_sign(
    SHA256("<base64url(header)>.<base64url(payload)>"),
    private_key
))
```

For HS256 it's:

```
base64url(HMAC_SHA256(
    "<base64url(header)>.<base64url(payload)>",
    shared_secret
))
```

The signature is computed **over the first two parts joined by a
dot**. If you change a single byte of the header or the payload, the
signature is invalidated.

### A worked example

Take a real-looking JWT:

```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImFiY2QtMTIzNCJ9
.
eyJzdWIiOiJ1c2VyLTEyMzQ1IiwiaXNzIjoiaHR0cHM6Ly9hdXRoLmV4YW1wbGUuY29tIiwiYXVkIjoiYXBpLmV4YW1wbGUuY29tIiwiZXhwIjoxNzAwMDAwMDAwLCJpYXQiOjE2OTk5OTY0MDAsInRlbmFudCI6ImFjbWUiLCJzY29wZSI6InJlYWQifQ
.
c2lnLW5hdHVyZS1oZXJl
```

Decode the first part (base64url → JSON):

```json
{"alg":"RS256","typ":"JWT","kid":"abcd-1234"}
```

Decode the second part:

```json
{"sub":"user-12345","iss":"https://auth.example.com","aud":"api.example.com","exp":1700000000,"iat":1699996400,"tenant":"acme","scope":"read"}
```

The third part is the signature — without the private key, you can
verify it but you can't compute it.

### The base64url quirk

Note that base64url **strips the `=` padding**. A standard base64
encoder would emit `eyJ…==` for the header above; a base64url
encoder emits `eyJ…` with no padding. This is the single most common
gotcha when you try to verify a JWT by hand — `base64.b64decode` in
Python will fail with `binascii.Error: Invalid base64-encoded string`
if you don't strip the padding first (or use `base64.urlsafe_b64decode`,
which handles it for you).

## Hands-on

Open a Python REPL and decode a real token by hand:

```python
import base64
import json

token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImFiY2QtMTIzNCJ9.eyJzdWIiOiJ1c2VyLTEyMzQ1IiwiaXNzIjoiaHR0cHM6Ly9hdXRoLmV4YW1wbGUuY29tIiwiYXVkIjoiYXBpLmV4YW1wbGUuY29tIiwiZXhwIjoxNzAwMDAwMDAwLCJpYXQiOjE2OTk5OTY0MDAsInRlbmFudCI6ImFjbWUiLCJzY29wZSI6InJlYWQifQ.c2lnLW5hdHVyZS1oZXJl"

def b64url_decode(part: str) -> bytes:
    padding = "=" * (-len(part) % 4)
    return base64.urlsafe_b64decode(part + padding)

header, payload, signature = token.split(".")
print("HEADER :", json.loads(b64url_decode(header)))
print("PAYLOAD:", json.loads(b64url_decode(payload)))
print("SIG    :", b64url_decode(signature).hex())
```

In L10 we'll replace the hand-rolled decoder with `pyjwt.decode`.

## Quiz prep

- How many parts does a JWT have? (3)
- Which part is signed? (The header + payload, joined with a dot.)
- What's the difference between base64 and base64url? (The url-safe
  variant swaps `+/` for `-_` and drops `=` padding.)

## Further reading

- RFC 7515 — JSON Web Signature (JWS)
- RFC 7519 — JSON Web Token (JWT)

## What's next

**L07 — Standard Claims** — the seven RFC-defined fields every JWT
should have, and what each one means.
