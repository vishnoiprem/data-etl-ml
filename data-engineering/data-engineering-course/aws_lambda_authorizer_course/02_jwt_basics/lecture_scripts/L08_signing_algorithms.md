---
lecture: L08
title: "Signing Algorithms — HS256 (HMAC) vs RS256 (RSA)"
duration: "16:00"
section: 2
prereqs: ["L07"]
---

# L08 — Signing Algorithms — HS256 (HMAC) vs RS256 (RSA)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 2 — JWT Basics
> **Duration:** 16:00

## Prereqs

- L07 — standard claims.

## Key terms

- **HS256** — HMAC with SHA-256. **Symmetric**: the same secret signs
  and verifies. Simple, fast, but the verifier has to hold the secret.
- **RS256** — RSASSA-PKCS1-v1_5 with SHA-256. **Asymmetric**: a
  private key signs, a public key verifies. The verifier only holds
  the public key, which is safe to distribute.
- **ES256** — ECDSA with P-256 and SHA-256. Asymmetric, smaller
  signatures than RS256, but less widely deployed.
- **`alg: none`** — a sentinel for an unsigned JWT. Older libraries
  honored it; modern ones reject it. **Always pin the algorithm on
  the verifier side.**
- **Algorithm confusion** — an attack where the verifier accepts
  `alg: HS256` when the token was supposed to be signed with
  `RS256`, then uses the **public key as the HMAC secret**. The
  attacker can mint a token signed with the public key. The fix is
  to pin the algorithm.
- **Key strength** — for RS256, use at least a 2048-bit RSA key.
  3072-bit is recommended for tokens that will live longer than
  2030.

## Lecture

The signing algorithm is the single biggest security decision in a
JWT system. Pick the wrong one and your "secure" token is signed
with a key the verifier can be tricked into disclosing.

### HS256 (HMAC)

```
signature = base64url(HMAC_SHA256(header.payload, shared_secret))
```

The same secret is used to sign and verify. The verifier holds
*the same secret* the issuer used.

**Pros:**

- Trivial to implement. One secret, one algorithm.
- Fast — symmetric crypto is ~1000× faster than RSA.
- The secret is small (32+ random bytes).

**Cons:**

- The verifier can *forge* a token. Anyone who has the secret can
  mint a token that any other verifier will accept.
- This makes HS256 **unsuitable for federated systems** — every
  service that verifies the token has to be trusted to *issue* the
  token.

**When to use:**

- Single-service systems. Your API mints and verifies its own
  tokens, in the same Lambda, with the same secret pulled from
  SSM Parameter Store. No third party needs to verify.
- The shared secret is stored in AWS Secrets Manager, rotated
  quarterly, and never leaves the Lambda runtime.

### RS256 (RSA)

```
signature = base64url(RSA_sign(SHA256(header.payload), private_key))
```

A private key signs; a **public** key verifies. The verifier only
holds the public key, which is mathematically impossible to use to
sign a new token.

**Pros:**

- The verifier can be *anyone*. You publish the public key as a
  JWK on a JWKS endpoint and anyone with the URL can verify your
  tokens.
- Rotation is easy — generate a new keypair, publish the new public
  key, start signing with the new private key, retire the old
  public key when all old tokens have expired.

**Cons:**

- Slow. RSA signature verification is 10–100× slower than HMAC.
  This matters in a Lambda Authorizer that runs on every request.
- Key material is bigger — a 2048-bit RSA public key is ~300 bytes
  base64-encoded.

**When to use:**

- Federated systems. Auth0, Okta, Cognito, and any other IdP
  issues tokens signed with RS256.
- Multi-service systems where the issuer and the verifier are
  *different* Lambdas in *different* accounts.

### ES256 (ECDSA)

Same shape as RS256 but with elliptic-curve keys. Smaller signatures
(~64 bytes vs 256), faster verification, but less widely supported
in legacy libraries. Newer systems are starting to prefer it.

### The `alg: none` attack

In 2015 a class of vulnerabilities was found where a token with
`"alg": "none"` and an empty signature was accepted by the
verifier. The fix is straightforward: **always pin the algorithm
in your authorizer**:

```python
# NEVER DO THIS
claims = jwt.decode(token, key)  # algorithm is inferred

# ALWAYS DO THIS
claims = jwt.decode(token, key, algorithms=["RS256"])
```

The `algorithms` argument is a *whitelist*. PyJWT will refuse to
verify a token whose `alg` is not in the list, regardless of what
the token says.

### The algorithm-confusion attack

A subtler attack: the token is correctly signed with HS256, but
the verifier was supposed to verify with RS256. The attacker uses
the **public key** as the HMAC secret. The signature verifies
because the attacker chose the secret.

The fix is the same: pin the algorithm. If you say
`algorithms=["RS256"]`, a token with `alg: HS256` is rejected
before the signature is ever checked.

### The decision tree

```
                ┌── Is the issuer a third-party IdP (Auth0, Okta, Cognito)?
                │      YES → RS256 (or ES256 if the IdP supports it)
                │      NO  ──┐
                │            │
                │            ├── Do multiple services need to verify the token,
                │            │   but only one service needs to mint it?
                │            │      YES → RS256
                │            │      NO  ──┐
                │            │            │
                │            │            ├── Single Lambda mints and verifies?
                │            │                   YES → HS256 is fine
                │            │
                │            └── Edge cases (FIPS, hardware-backed keys):
                │                   → ES256 / RS384 per your security team
```

### In this course

- **Section 3** uses **HS256** because the authorizer is the only
  verifier and the demo is single-Lambda.
- **Section 4** uses **RS256** because the public key is fetched
  from a JWKS endpoint — exactly the federated case.
- **Section 5** mentions **ES256** as the modern alternative.

## Hands-on

Generate both kinds of keypair and sign a token with each:

```python
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

# HS256 — same secret signs and verifies
secret = b"super-secret-32-bytes-of-entropy!!"
hs_token = jwt.encode({"sub": "u-1"}, secret, algorithm="HS256")
print("HS256:", hs_token)

# RS256 — private signs, public verifies
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

rs_token = jwt.encode({"sub": "u-1"}, private_key, algorithm="RS256")
print("RS256:", rs_token)

# Verify with the public key only
claims = jwt.decode(rs_token, public_key, algorithms=["RS256"])
print("claims:", claims)
```

In L10 we'll wrap this in tests.

## Quiz prep

- What's the difference between HS256 and RS256?
- Why is `alg: none` dangerous?
- How do you defend against algorithm confusion in `pyjwt`?

## Further reading

- RFC 7518 — JSON Web Algorithms (JWA).
- PortSwigger: [JWT attacks](https://portswigger.net/web-security/jwt).

## What's next

**L09 — JWK and JWKS** — how to verify a token signed by a key
you've never seen before, and how to roll keys without downtime.
