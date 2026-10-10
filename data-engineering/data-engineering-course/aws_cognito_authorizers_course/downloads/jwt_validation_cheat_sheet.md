# JWT Validation Cheat Sheet (one page, 2026 edition)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Source:** RFC 7519 (JWT) + AWS Cognito documentation, current as of October 2026.
> **Format:** printable one-pager. The "real" deliverable is a PDF generated from this markdown by `pandoc`.

## 1. What is a JWT?

A JWT is three Base64URL-encoded sections separated by dots:

```
header.payload.signature
```

| Section | Contents | Example |
|---|---|---|
| `header` | Algorithm + token type | `{"alg": "RS256", "typ": "JWT", "kid": "abc123"}` |
| `payload` | Claims (the actual data) | `{"sub": "user-1", "email": "alice@example.com", "exp": 1730659200}` |
| `signature` | RSA / ECDSA / HMAC over `header.payload` | opaque to humans |

A JWT is **not encrypted** — the payload is readable by anyone. The
signature only proves the token was issued by a party that holds the
signing key.

## 2. The 7 claims every Cognito JWT has

| Claim | Meaning | Example |
|---|---|---|
| `sub` | Subject (Cognito user UUID) | `f7c1...-0000` |
| `iss` | Issuer | `https://cognito-idp.us-east-1.amazonaws.com/us-east-1_aBcDeFg` |
| `aud` | Audience (App Client ID) | `7a1b2c3d4e5f6g7h` |
| `exp` | Expiry (epoch seconds) | `1730659200` |
| `iat` | Issued-at (epoch seconds) | `1730655600` |
| `token_use` | `"id"` or `"access"` | `"id"` |
| `auth_time` | Last user authentication | `1730655600` |

Plus optionally: `email`, `email_verified`, `phone_number`,
`cognito:groups`, `cognito:username`, and any custom attributes.

## 3. The validation algorithm (5 steps)

```
1. FETCH  the JWKS at
        https://cognito-idp.<region>.amazonaws.com/<user-pool-id>/.well-known/jwks.json
   CACHE  it (5 min TTL) — never call Cognito per request.

2. DECODE the JWT header, look at the `kid`.

3. PICK  the JWK from the JWKS whose `kid` matches.

4. VERIFY the signature (RS256) with the JWK's public key.

5. CHECK  the standard claims:
   • exp > now (not expired)
   • iss == https://cognito-idp.<region>.amazonaws.com/<user-pool-id>
   • aud == <your-app-client-id>
   • token_use == "id" (or "access", depending on the use case)
```

## 4. The `pyjwt` recipe (no AWS SDK needed)

```python
import time
import urllib.request
import json
import jwt  # PyJWT

JWKS_URL = (
    "https://cognito-idp.us-east-1.amazonaws.com/"
    "us-east-1_aBcDeFg/.well-known/jwks.json"
)
ISSUER = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_aBcDeFg"
APP_CLIENT_ID = "7a1b2c3d4e5f6g7h"
_JWKS_CACHE: dict = {"keys": None, "fetched_at": 0.0}

def _get_jwks(force: bool = False) -> dict:
    if not force and time.time() - _JWKS_CACHE["fetched_at"] < 300:
        return _JWKS_CACHE["keys"]
    with urllib.request.urlopen(JWKS_URL, timeout=2) as r:
        _JWKS_CACHE["keys"] = json.loads(r.read())
    _JWKS_CACHE["fetched_at"] = time.time()
    return _JWKS_CACHE["keys"]

def validate_jwt(token: str) -> dict:
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header["kid"]
    jwks = _get_jwks()
    key = next(k for k in jwks["keys"] if k["kid"] == kid)
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
    return jwt.decode(
        token,
        key=public_key,
        algorithms=["RS256"],
        audience=APP_CLIENT_ID,
        issuer=ISSUER,
        options={"require": ["exp", "iss", "aud", "sub", "token_use"]},
    )
```

## 5. Common validation bugs

| Bug | What goes wrong |
|---|---|
| Using `jwt.decode(..., verify=False)` in production | Anyone can mint a token and impersonate any user. |
| Forgetting to check `iss` | A token from a different user pool is accepted. |
| Forgetting to check `aud` | An access token from your *other* app is accepted. |
| Checking only `exp` | Replay attacks work as long as the token is unexpired. |
| Fetching JWKS per request | DoS-able and slow. Cache for ≥ 5 min. |
| Mixing up `id` and `access` tokens | Access tokens don't have `email`; ID tokens don't have `scope`. |
