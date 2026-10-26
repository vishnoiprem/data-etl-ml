"""
Token-based Lambda Authorizer for AWS API Gateway (REST API).

Validates an HS256 JWT carried in the `Authorization` header and returns
an IAM policy that allows invocation of the methodArn from the event.

The function is intentionally side-effect free: it does not call any
AWS service, does not hit a database, and does not log to stdout. In a
real deployment you would add structured logging and a CloudWatch EMF
metric for allow/deny counts.

Environment variables:
    JWT_SECRET     shared secret used to verify HS256 signatures.
                   Defaults to a known test value so the moto test in
                   this folder can run without configuration. NEVER
                   use the default in production.
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


def _allow(method_arn: str, principal_id: str, context: Dict[str, str]) -> Dict[str, Any]:
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
    token = event.get("authorizationToken", "")
    method_arn = event.get("methodArn", "")

    # The token arrives as "Bearer <jwt>". API Gateway sends the raw
    # value of the Authorization header; strip the scheme if present.
    if token.lower().startswith("bearer "):
        token = token[7:]

    secret = os.environ.get("JWT_SECRET", _DEFAULT_TEST_SECRET)
    alg = os.environ.get("JWT_ALG", "HS256")
    issuer = os.environ.get("JWT_ISSUER")
    audience = os.environ.get("JWT_AUDIENCE")

    decode_options: Dict[str, Any] = {}
    if issuer:
        decode_options["issuer"] = issuer
    if audience:
        decode_options["audience"] = audience

    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[alg],
            options=decode_options or None,
        )
    except jwt.PyJWTError:
        return _deny(method_arn)

    # Surface a small, flat, string-only context to the integration.
    principal_id = str(claims.get("sub", "anonymous"))
    flat_context: Dict[str, str] = {
        "sub": principal_id,
        "tenant": str(claims.get("tenant", "")),
        "scope": str(claims.get("scope", "")),
    }

    return _allow(method_arn, principal_id, flat_context)
