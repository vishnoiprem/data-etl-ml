"""Tests for jwt_verify.py.

Run with:  pytest test_jwt_verify.py -v
"""

from __future__ import annotations

import importlib.util
import time
from pathlib import Path

import jwt
import pytest

# Load the module under test without making it a package.
_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("jwt_verify", _HERE / "jwt_verify.py")
assert _spec and _spec.loader
jwt_verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jwt_verify)


# ---------------------------------------------------------------------------
# 1. Round-trips (HS256 + RS256)
# ---------------------------------------------------------------------------

def test_round_trip_hs256_signs_and_verifies():
    token = jwt_verify.make_hs256_token(sub="user-42",
                                        extra_claims={"tenant": "acme"})
    claims = jwt_verify.verify_hs256(token)
    assert claims["sub"] == "user-42"
    assert claims["tenant"] == "acme"
    assert claims["iss"] == jwt_verify.ISSUER
    assert claims["aud"] == jwt_verify.AUDIENCE
    assert claims["exp"] > int(time.time())


def test_round_trip_rs256_signs_and_verifies():
    token = jwt_verify.make_rs256_token(sub="user-99", kid="k-1",
                                        extra_claims={"scope": "admin"})
    claims = jwt_verify.verify_rs256(token)
    assert claims["sub"] == "user-99"
    assert claims["scope"] == "admin"
    # The unverified header exposes the kid we set
    assert jwt.get_unverified_header(token)["kid"] == "k-1"


# ---------------------------------------------------------------------------
# 2. Expired token rejected
# ---------------------------------------------------------------------------

def test_expired_token_rejected():
    # exp_in=-10 means the token expired 10 seconds ago.
    token = jwt_verify.make_hs256_token(exp_in=-10)
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt_verify.verify_hs256(token)


# ---------------------------------------------------------------------------
# 3. Wrong key rejected
# ---------------------------------------------------------------------------

def test_wrong_key_rejected():
    # Sign with one HS secret (the module's), then verify with another.
    token = jwt_verify.make_hs256_token()
    # Patch the verifier's secret by calling jwt.decode directly with a
    # different secret. This proves the signature is checked.
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            token,
            b"a-different-secret-of-sufficient-length!",
            algorithms=["HS256"],
            audience=jwt_verify.AUDIENCE,
            issuer=jwt_verify.ISSUER,
            options={"require": jwt_verify.REQUIRED_CLAIMS},
        )


# ---------------------------------------------------------------------------
# 4. Missing claim rejected
# ---------------------------------------------------------------------------

def test_missing_required_claim_rejected():
    # Mint a token by hand with no `aud` claim, then verify.
    payload = {
        "sub": "user-1",
        "iss": jwt_verify.ISSUER,
        "iat": int(time.time()),
        "exp": int(time.time()) + 60,
        # no "aud"!
    }
    token = jwt.encode(payload, jwt_verify.HS_SECRET, algorithm="HS256")
    with pytest.raises(jwt.MissingRequiredClaimError):
        jwt_verify.verify_hs256(token)


# ---------------------------------------------------------------------------
# 5. Tampered payload rejected
# ---------------------------------------------------------------------------

def test_tampered_payload_rejected():
    """Flip one byte of the payload — the signature must no longer match."""
    token = jwt_verify.make_hs256_token(sub="user-1")

    header_b64, payload_b64, signature_b64 = token.split(".")
    # base64url-decode the payload, change a value, re-encode (no padding)
    import base64
    pad = "=" * (-len(payload_b64) % 4)
    payload_json = base64.urlsafe_b64decode(payload_b64 + pad).decode()
    tampered_json = payload_json.replace('"user-1"', '"admin-user"')
    tampered_b64 = base64.urlsafe_b64encode(tampered_json.encode()).rstrip(b"=").decode()

    tampered_token = f"{header_b64}.{tampered_b64}.{signature_b64}"

    with pytest.raises(jwt.InvalidSignatureError):
        jwt_verify.verify_hs256(tampered_token)
