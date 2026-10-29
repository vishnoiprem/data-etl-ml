"""Sign and verify JWTs with PyJWT + cryptography.

Companion to L10.

Demonstrates:
    * HS256 (symmetric, shared secret)
    * RS256 (asymmetric, RSA keypair)
    * the four common failure modes:
        - expired token
        - wrong key
        - missing claim
        - tampered payload

Run::

    python3 jwt_verify.py            # demo
    pytest -q test_jwt_verify.py     # tests
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

# ---------------------------------------------------------------------------
# 1. Keys (in-memory, demo only — never bake real keys into source)
# ---------------------------------------------------------------------------

# HS256 — 32 bytes of entropy. Real secrets come from SSM/Secrets Manager.
HS_SECRET = b"demo-secret-do-not-use-in-prod-32b!!"

# RS256 — 2048-bit RSA keypair. In production the issuer holds the
# private key; the verifier only needs the public key.
RS_PRIVATE = rsa.generate_private_key(public_exponent=65537, key_size=2048)
RS_PUBLIC = RS_PRIVATE.public_key()

ISSUER = "https://auth.example.com"
AUDIENCE = "api.example.com"

# Pins the algorithm. The token header is *not* trusted to choose
# the algorithm — this prevents the alg=none and alg-confusion attacks.
REQUIRED_CLAIMS = ["exp", "iat", "iss", "sub", "aud"]


# ---------------------------------------------------------------------------
# 2. Sign
# ---------------------------------------------------------------------------

def _now() -> int:
    return int(time.time())


def make_hs256_token(
    sub: str = "user-1",
    *,
    exp_in: int = 60,
    extra_claims: Dict[str, Any] | None = None,
) -> str:
    """Mint an HS256 JWT with the standard claims.

    Parameters
    ----------
    sub:
        The subject (the "who") of the token. Defaults to ``"user-1"``.
    exp_in:
        Seconds from now until the token expires. Use a negative
        value to mint an already-expired token (used in tests).
    extra_claims:
        Additional claims to merge into the payload. Use for custom
        claims like ``tenant`` or ``scope``.
    """
    payload: Dict[str, Any] = {
        "sub": sub,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": _now(),
        "exp": _now() + exp_in,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, HS_SECRET, algorithm="HS256")


def make_rs256_token(
    sub: str = "user-1",
    *,
    exp_in: int = 60,
    kid: str = "abcd-1234",
    extra_claims: Dict[str, Any] | None = None,
) -> str:
    """Mint an RS256 JWT with the standard claims + a ``kid`` header.

    Parameters
    ----------
    sub:
        The subject of the token.
    exp_in:
        Seconds from now until the token expires.
    kid:
        The key id, placed in the JOSE header so the verifier can
        look the public key up in a JWKS. Defaults to ``"abcd-1234"``.
    extra_claims:
        Additional custom claims.
    """
    payload: Dict[str, Any] = {
        "sub": sub,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": _now(),
        "exp": _now() + exp_in,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        RS_PRIVATE,
        algorithm="RS256",
        headers={"kid": kid},
    )


# ---------------------------------------------------------------------------
# 3. Verify
# ---------------------------------------------------------------------------

def verify_hs256(token: str) -> Dict[str, Any]:
    """Verify an HS256 token. Raises ``jwt.PyJWTError`` on any failure."""
    return jwt.decode(
        token,
        HS_SECRET,
        algorithms=["HS256"],          # pin the algorithm
        audience=AUDIENCE,             # verify aud
        issuer=ISSUER,                 # verify iss
        options={"require": REQUIRED_CLAIMS},  # verify exp/iat/sub present
    )


def verify_rs256(token: str) -> Dict[str, Any]:
    """Verify an RS256 token with the public key."""
    return jwt.decode(
        token,
        RS_PUBLIC,
        algorithms=["RS256"],
        audience=AUDIENCE,
        issuer=ISSUER,
        options={"require": REQUIRED_CLAIMS},
    )


# ---------------------------------------------------------------------------
# 4. Demo
# ---------------------------------------------------------------------------

def _print_token(tok: str) -> None:
    """Show the (unverified!) header and (verified) claims."""
    header = jwt.get_unverified_header(tok)
    print(f"  token : {tok[:60]}…")
    print(f"  header: {json.dumps(header, sort_keys=True)}")


def demo() -> None:
    """Run the full sign + verify demo, both algorithms."""
    print("== HS256 ==")
    tok = make_hs256_token(extra_claims={"tenant": "acme", "scope": "read"})
    _print_token(tok)
    print(f"  claims: {json.dumps(verify_hs256(tok), sort_keys=True)}")

    print("\n== RS256 ==")
    tok = make_rs256_token(extra_claims={"tenant": "acme", "scope": "admin"},
                           kid="abcd-1234")
    _print_token(tok)
    print(f"  claims: {json.dumps(verify_rs256(tok), sort_keys=True)}")


if __name__ == "__main__":
    demo()
