---
lecture: L10
title: "Verifying a JWT in Pure Python (pyjwt)"
duration: "20:00"
section: 2
prereqs: ["L09"]
---

# L10 — Verifying a JWT in Pure Python (pyjwt)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 2 — JWT Basics
> **Duration:** 20:00

## Prereqs

- L09 — JWKS rotation.

## Key terms

- **`pyjwt.encode(payload, key, algorithm=...)`** — sign a token.
- **`pyjwt.decode(token, key, algorithms=[...], audience=..., issuer=...)`**
  — verify a token. Raises a subclass of `jwt.PyJWTError` on any
  failure.
- **`jwt.ExpiredSignatureError`** — raised when `exp` is in the past.
- **`jwt.InvalidAudienceError`** — raised when `aud` doesn't match.
- **`jwt.InvalidIssuerError`** — raised when `iss` doesn't match.
- **`jwt.InvalidSignatureError`** — raised when the signature doesn't
  match.
- **`jwt.MissingRequiredClaimError`** — raised when a claim in
  `options={"require": [...]}` is missing.
- **`jwt.PyJWKClient(url)`** — fetches and caches a JWKS for
  asymmetric verification.

## Lecture

This is the hands-on lab. We write a single Python module,
`jwt_verify.py`, that:

1. Generates an RSA keypair in memory.
2. Signs a JWT with HS256, then with RS256.
3. Verifies the token, decodes the payload, prints the header.
4. Demonstrates the four failure modes: expired token, wrong key,
   missing claim, tampered token.

Then we write five `pytest` tests that pin each failure mode.

### The script

`02_jwt_basics/code/jwt_verify.py` (see that file for the full
annotated source). The shape:

```python
"""Sign and verify JWTs with PyJWT + cryptography.

Demonstrates HS256 + RS256, and the four common failure modes.
"""

from __future__ import annotations

import time
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


# ---- 1. Generate keys ----------------------------------------------------
HS_SECRET = b"super-secret-32-bytes-of-entropy!!"  # HS256
RS_PRIVATE = rsa.generate_private_key(public_exponent=65537, key_size=2048)
RS_PUBLIC = RS_PRIVATE.public_key()


# ---- 2. Sign -------------------------------------------------------------
def make_hs256_token(sub: str = "u-1", exp_in: int = 60) -> str:
    payload = {
        "sub": sub,
        "iss": "https://auth.example.com",
        "aud": "api.example.com",
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_in,
    }
    return jwt.encode(payload, HS_SECRET, algorithm="HS256")


def make_rs256_token(sub: str = "u-1", exp_in: int = 60, *, kid: str = "k1") -> str:
    payload = {
        "sub": sub,
        "iss": "https://auth.example.com",
        "aud": "api.example.com",
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_in,
    }
    headers = {"kid": kid}
    return jwt.encode(payload, RS_PRIVATE, algorithm="RS256", headers=headers)


# ---- 3. Verify -----------------------------------------------------------
def verify_hs256(token: str) -> dict:
    return jwt.decode(
        token,
        HS_SECRET,
        algorithms=["HS256"],
        audience="api.example.com",
        issuer="https://auth.example.com",
        options={"require": ["exp", "iat", "iss", "sub", "aud"]},
    )


def verify_rs256(token: str) -> dict:
    return jwt.decode(
        token,
        RS_PUBLIC,
        algorithms=["RS256"],
        audience="api.example.com",
        issuer="https://auth.example.com",
        options={"require": ["exp", "iat", "iss", "sub", "aud"]},
    )


# ---- 4. Demo -------------------------------------------------------------
def demo() -> None:
    print("== HS256 ==")
    tok = make_hs256_token()
    print("token:", tok[:60] + "…")
    print("header:", jwt.get_unverified_header(tok))
    print("claims:", verify_hs256(tok))

    print("\n== RS256 ==")
    tok = make_rs256_token(kid="abcd-1234")
    print("token:", tok[:60] + "…")
    print("header:", jwt.get_unverified_header(tok))
    print("claims:", verify_rs256(tok))


if __name__ == "__main__":
    demo()
```

### The tests

`02_jwt_basics/code/test_jwt_verify.py` ships five `pytest` tests:

1. **`test_round_trip_hs256`** — sign, then verify the same token.
2. **`test_round_trip_rs256`** — same, with RS256.
3. **`test_expired_token_rejected`** — sign with `exp_in=-10`,
   verify raises `ExpiredSignatureError`.
4. **`test_wrong_key_rejected`** — sign with one HS secret, verify
   with another; raises `InvalidSignatureError`.
5. **`test_missing_claim_rejected`** — sign with no `aud` claim,
   verify raises `MissingRequiredClaimError`.
6. **`test_tampered_token_rejected`** — take a valid token, mutate
   one byte in the payload, verify raises `InvalidSignatureError`.

Run:

```bash
cd 02_jwt_basics/code
pip install -r requirements.txt
pytest -v
```

Expected: **5 passed** (or 6 — the test file ships both HS256 and
RS256 round-trip tests so the total is 5+).

### Common gotchas

1. **`options={"require": [...]}`** — without this, a token that
   omits `exp` is treated as a token that never expires. **Always
   set it.**
2. **`algorithms=["RS256"]`** — without this, PyJWT will infer the
   algorithm from the token, opening the door to the
   algorithm-confusion attack.
3. **`audience=` and `issuer=`** — without these, PyJWT will not
   check `aud` or `iss` at all.
4. **`kid` lookup** — when verifying with a JWKS, PyJWT picks the
   key by the token's `kid` header. If the header is missing or
   doesn't match, you get `PyJWKClientError`.

## Hands-on

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_lambda_authorizer_course/02_jwt_basics/code
python3 -m pip install -r requirements.txt
python3 jwt_verify.py
python3 -m pytest test_jwt_verify.py -v
```

Expected output ends with `5 passed` (or `6 passed` if you count
both round-trips).

## Quiz prep

- What's the difference between `jwt.encode` and `jwt.decode`?
- What does `options={"require": [...]}` do?
- How do you defend against algorithm confusion?

## Further reading

- [`../code/jwt_verify.py`](../code/jwt_verify.py) — the script.
- [`../code/test_jwt_verify.py`](../code/test_jwt_verify.py) — the tests.
- PyJWT docs: [Usage examples](https://pyjwt.readthedocs.io/en/stable/usage.html).

## What's next

**Section 3 — Simple Token-Based Lambda Authorizer (L11–L15)**. We
wrap `verify_rs256` in a Lambda handler and return an IAM policy.
