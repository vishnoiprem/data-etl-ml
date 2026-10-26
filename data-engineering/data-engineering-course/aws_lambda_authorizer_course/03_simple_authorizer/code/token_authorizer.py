"""Token-based Lambda Authorizer for AWS API Gateway (REST API).

Companion to L15.

Validates an HS256 JWT carried in the ``Authorization`` header and
returns an IAM policy that allows invocation of the ``methodArn``
from the event.

The function is intentionally side-effect free: it does not call
any AWS service, does not hit a database, and does not log to
stdout. In a real deployment you would add structured logging and a
CloudWatch EMF metric for allow/deny counts.

Environment variables:
    JWT_SECRET     shared secret used to verify HS256 signatures.
                   Defaults to a known test value so the moto test
                   in this folder can run without configuration.
                   NEVER use the default in production.
    JWT_ALG        algorithm to expect. Defaults to HS256.
    JWT_ISSUER     optional. If set, the 'iss' claim must match.
    JWT_AUDIENCE   optional. If set, the 'aud' claim must contain it.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import jwt  # PyJWT

# Test-only default. Production secrets must come from AWS Secrets
# Manager / SSM Parameter Store and be injected via an environment
# variable that has no default value.
_DEFAULT_TEST_SECRET = "test-secret-do-not-use-in-prod"

# Standard claims every token must carry. Without this list, PyJWT
# would happily verify a token with no exp claim — i.e. one that
# never expires.
_REQUIRED_CLAIMS = ["exp", "iat", "iss", "sub", "aud"]


# ---------------------------------------------------------------------------
# Policy builders
# ---------------------------------------------------------------------------

def _allow(method_arn: str, principal_id: str,
           context: Dict[str, str]) -> Dict[str, Any]:
    """Build the standard API Gateway Allow AuthResponse."""
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "execute-api:Invoke",
                    "Resource": method_arn,
                }
            ],
        },
        "context": context,
    }


def _deny(method_arn: str) -> Dict[str, Any]:
    """Build the standard API Gateway Deny AuthResponse."""
    return {
        "principalId": "unauthorized",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Action": "execute-api:Invoke",
                    "Resource": method_arn,
                }
            ],
        },
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _flatten(claims: Dict[str, Any], *, _prefix: str = "") -> Dict[str, str]:
    """Turn a possibly-nested claims dict into the flat string-only
    map API Gateway requires.

    API Gateway rejects the request with HTTP 500 if any value in
    ``context`` is not a string, or if the map is not flat. This
    helper enforces both rules.
    """
    out: Dict[str, str] = {}
    for key, value in claims.items():
        composite = f"{_prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, _prefix=f"{composite}."))
        elif isinstance(value, list):
            # API Gateway cannot carry lists in context. Comma-join.
            out[composite] = ",".join(str(v) for v in value)
        else:
            out[composite] = str(value)
    return out


def _strip_bearer(raw: str) -> str:
    """Drop a leading ``Bearer `` (case-insensitive)."""
    if raw.lower().startswith("bearer "):
        return raw[7:]
    return raw


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """API Gateway TOKEN authorizer entry point.

    Parameters
    ----------
    event:
        The API Gateway authorizer event. Expected fields:
        - authorizationToken: str (raw value of the Authorization header)
        - methodArn: str (the ARN of the method being invoked)
    context:
        Unused. Lambda runtime context object.
    """
    method_arn = event.get("methodArn", "")
    raw_token = event.get("authorizationToken", "")

    token = _strip_bearer(raw_token)
    if not method_arn or not token:
        return _deny(method_arn)

    secret = os.environ.get("JWT_SECRET", _DEFAULT_TEST_SECRET)
    alg = os.environ.get("JWT_ALG", "HS256")
    issuer = os.environ.get("JWT_ISSUER")
    audience = os.environ.get("JWT_AUDIENCE")

    decode_kwargs: Dict[str, Any] = {
        "algorithms": [alg],
        "options": {"require": _REQUIRED_CLAIMS},
    }
    if issuer:
        decode_kwargs["issuer"] = issuer
    if audience:
        decode_kwargs["audience"] = audience

    try:
        claims = jwt.decode(token, secret, **decode_kwargs)
    except jwt.PyJWTError:
        # Any PyJWT exception — Expired, InvalidSignature,
        # MissingRequiredClaim, InvalidIssuer, InvalidAudience — is
        # treated identically: deny.
        return _deny(method_arn)

    principal_id = str(claims.get("sub", "anonymous"))
    flat_context = _flatten(claims)

    return _allow(method_arn, principal_id, flat_context)