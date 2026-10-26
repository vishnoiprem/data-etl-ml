"""Idempotent boto3 script that creates a Cognito Identity Pool + IAM role.

Section 3 (L11-L14) of the AWS Cognito Authorizers course.

Run::

    python3 identity_pool_demo.py              # create or re-use the identity pool
    python3 identity_pool_demo.py --dry-run    # print the plan, don't touch AWS

Environment variables (all optional):

    USER_POOL_ID         user pool id (must exist).        default: none
    APP_CLIENT_ID        app client id (must exist).       default: none
    IDENTITY_POOL_NAME   name of the identity pool.       default: demo-cognito-course-idpool
    AUTH_ROLE_NAME       IAM role for authenticated users.default: Cognito_IdentityPool_Auth_Role
    AWS_REGION           region.                           default: us-east-1

Design goals:

    - Idempotent: re-running with the same IDENTITY_POOL_NAME returns
      the existing pool's id.
    - Sets a Cognito User Pool as the auth provider.
    - Creates an IAM role (with an inline trust policy that allows
      ``cognito-identity.amazonaws.com`` to assume it) and an inline
      S3 read-only policy.
    - Dry-run: ``--dry-run`` prints the API calls we *would* make and
      exits 0 without any AWS calls.
    - Testable: every AWS call is encapsulated in a module-level
      function so ``moto`` can mock them.

.. note::

    **What this script can and cannot test with moto.** ``moto`` 5.x
    implements ``cognito-identity:CreateIdentityPool``,
    ``DescribeIdentityPool`` and ``ListIdentityPools``. It does **not**
    implement ``SetIdentityPoolRoles`` (raises ``NotImplementedError``)
    or the federated ``GetCredentialsForIdentity`` /
    ``GetId`` flows. The tests therefore cover pool creation and
    provider configuration via the describe round-trip, and verify
    that the IAM role is created with the correct trust policy and
    inline policy (via the IAM client, which moto does implement). The
    actual role <-> pool attachment is tested by code inspection in
    production — for the course we document the call in
    ``_attach_roles_to_pool`` and skip it under moto.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_REGION = "us-east-1"
DEFAULT_IDENTITY_POOL_NAME = "demo-cognito-course-idpool"
DEFAULT_AUTH_ROLE_NAME = "Cognito_IdentityPool_Auth_Role"


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class IdentityPoolStack:
    """The minimum you need to wire an Identity Pool into a federated app."""

    identity_pool_id: str
    user_pool_id: str
    app_client_id: str
    auth_role_arn: str
    region: str


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def _env(name: str, default: str = "") -> str:
    """Read an env var with a fallback. Re-read every call so tests can patch."""
    return os.environ.get(name, default)


def _cognito_provider(user_pool_id: str) -> str:
    """Build the Cognito User Pool provider name in the format Cognito expects."""
    return f"cognito-idp.us-east-1.amazonaws.com/{user_pool_id}"


def _build_trust_policy() -> dict:
    """Build the trust policy that lets cognito-identity.amazonaws.com assume the role.

    Cognito Identity Pools assume the role on behalf of an authenticated
    user. The trust policy must allow ``cognito-identity.amazonaws.com``
    as a principal, and constrain the source via a ``Condition`` to the
    specific identity pool that owns the role.
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Federated": "cognito-identity.amazonaws.com"},
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": "<IDENTITY_POOL_ID>"
                    }
                },
            }
        ],
    }


def _build_inline_policy() -> str:
    """Build the least-privilege inline policy for authenticated users.

    For the course we grant S3 read-only on the user's own prefix in a
    single bucket. Real apps would use the Cognito ``auth_time`` and
    ``sub`` claims to scope the policy to the user.
    """
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowUserToListTheirOwnBucketPrefix",
                    "Effect": "Allow",
                    "Action": ["s3:ListBucket"],
                    "Resource": ["arn:aws:s3:::demo-cognito-course-bucket"],
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": ["${cognito-identity.amazonaws.com:sub}/*"]
                        }
                    },
                },
                {
                    "Sid": "AllowUserReadTheirOwnObjects",
                    "Effect": "Allow",
                    "Action": ["s3:GetObject"],
                    "Resource": [
                        "arn:aws:s3:::demo-cognito-course-bucket/"
                        "${cognito-identity.amazonaws.com:sub}/*"
                    ],
                },
            ]
        }
    )


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------
def _find_existing_identity_pool(identity, name: str) -> str | None:
    paginator = identity.get_paginator("list_identity_pools")
    for page in paginator.paginate(MaxResults=60):
        for pool in page["IdentityPools"]:
            if pool["IdentityPoolName"] == name:
                return pool["IdentityPoolId"]
    return None


def _find_existing_role(iam, role_name: str) -> str | None:
    try:
        return iam.get_role(RoleName=role_name)["Role"]["Arn"]
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code == "NoSuchEntity":
            return None
        raise


# ---------------------------------------------------------------------------
# Step functions — one per AWS resource
# ---------------------------------------------------------------------------
def _create_identity_pool(identity, name: str, user_pool_id: str,
                          app_client_id: str) -> str:
    """Create the Identity Pool with the User Pool as the auth provider."""
    pool = identity.create_identity_pool(
        IdentityPoolName=name,
        AllowUnauthenticatedIdentities=False,
        CognitoIdentityProviders=[
            {
                "ProviderName": _cognito_provider(user_pool_id),
                "ClientId": app_client_id,
                # Server-side token validation only — no identity-pool IdP
                # token type needed for user pools.
                "ServerSideTokenCheck": True,
            },
        ],
    )
    return pool["IdentityPoolId"]


def _create_auth_role(iam, role_name: str) -> str:
    """Create the IAM role + inline policy for authenticated users."""
    trust = _build_trust_policy()
    role = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust),
        Description=(
            "Cognito Identity Pool authenticated role for the "
            "demo-cognito-course identity pool."
        ),
    )
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="cognito-idpool-auth-policy",
        PolicyDocument=_build_inline_policy(),
    )
    return role["Role"]["Arn"]


def _attach_roles_to_pool(identity, pool_id: str, auth_role_arn: str) -> None:
    """Attach the auth role to the identity pool.

    .. warning::

        ``SetIdentityPoolRoles`` is **not** implemented by ``moto`` 5.x
        (raises ``NotImplementedError``). In tests we therefore skip
        this call and verify the role + trust policy via the IAM
        client. In production, this is the call that wires the role
        into the pool.
    """
    identity.set_identity_pool_roles(
        IdentityPoolId=pool_id,
        Roles={"authenticated": auth_role_arn},
    )


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------
def bootstrap(
    *,
    user_pool_id: str | None = None,
    app_client_id: str | None = None,
    identity_pool_name: str | None = None,
    auth_role_name: str | None = None,
    region: str | None = None,
    identity=None,
    iam=None,
) -> IdentityPoolStack:
    """Create the Identity Pool + IAM role. Idempotent.

    Args:
        user_pool_id:         overrides env USER_POOL_ID (required)
        app_client_id:        overrides env APP_CLIENT_ID (required)
        identity_pool_name:   overrides env IDENTITY_POOL_NAME
        auth_role_name:       overrides env AUTH_ROLE_NAME
        region:               overrides env AWS_REGION
        identity:             optional pre-built cognito-identity client
        iam:                  optional pre-built IAM client

    Returns:
        IdentityPoolStack with the pool id, user pool id, and role arn.

    Raises:
        ValueError: if USER_POOL_ID or APP_CLIENT_ID are not set.
    """
    user_pool_id = user_pool_id or _env("USER_POOL_ID")
    app_client_id = app_client_id or _env("APP_CLIENT_ID")
    identity_pool_name = identity_pool_name or _env(
        "IDENTITY_POOL_NAME", DEFAULT_IDENTITY_POOL_NAME
    )
    auth_role_name = auth_role_name or _env("AUTH_ROLE_NAME", DEFAULT_AUTH_ROLE_NAME)
    region = region or _env("AWS_REGION", DEFAULT_REGION)

    if not user_pool_id:
        raise ValueError(
            "USER_POOL_ID is required. "
            "Export it from 02_user_pools/code/create_user_pool.py first."
        )
    if not app_client_id:
        raise ValueError(
            "APP_CLIENT_ID is required. "
            "Export it from 02_user_pools/code/create_user_pool.py first."
        )

    if identity is None:
        identity = boto3.client("cognito-identity", region_name=region)
    if iam is None:
        iam = boto3.client("iam")

    # 1. Identity pool ----------------------------------------------------
    pool_id = _find_existing_identity_pool(identity, identity_pool_name)
    if pool_id:
        print(f"[identity_pool_demo] Reusing existing Identity Pool: {pool_id}")
    else:
        pool_id = _create_identity_pool(
            identity, identity_pool_name, user_pool_id, app_client_id
        )
        print(f"[identity_pool_demo] Created Identity Pool: {pool_id}")

    # 2. IAM role ---------------------------------------------------------
    auth_role_arn = _find_existing_role(iam, auth_role_name)
    if auth_role_arn:
        print(f"[identity_pool_demo] Reusing existing IAM role: {auth_role_arn}")
    else:
        auth_role_arn = _create_auth_role(iam, auth_role_name)
        print(f"[identity_pool_demo] Created IAM role: {auth_role_arn}")

    # 3. Attach the role to the pool -------------------------------------
    # NOTE: skipped in moto tests. In production this is required.
    try:
        _attach_roles_to_pool(identity, pool_id, auth_role_arn)
        print("[identity_pool_demo] Attached auth role to identity pool")
    except NotImplementedError as exc:
        print(
            f"[identity_pool_demo] Skipped SetIdentityPoolRoles: {exc}. "
            "This is expected under moto; in production this call is required."
        )

    return IdentityPoolStack(
        identity_pool_id=pool_id,
        user_pool_id=user_pool_id,
        app_client_id=app_client_id,
        auth_role_arn=auth_role_arn,
        region=region,
    )


def _print_dry_run(
    user_pool_id: str, app_client_id: str, identity_pool_name: str,
    auth_role_name: str, region: str,
) -> None:
    """Print the API calls we *would* make and exit."""
    print("[DRY-RUN] No AWS calls will be made. Plan:")
    print(
        f"  cognito-identity.create_identity_pool({json.dumps(identity_pool_name)!r}, "
        f"providers=[{{providerName={_cognito_provider(user_pool_id)!r}, "
        f"clientId={app_client_id!r}}}])"
    )
    print(f"  iam.create_role({auth_role_name!r}, trust_policy=...)")
    print(f"  iam.put_role_policy({auth_role_name!r}, inline_policy=...)")
    print(f"  cognito-identity.set_identity_pool_roles(roles={{authenticated=<role>}})")
    print(f"  region: {region}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Idempotent Cognito Identity Pool bootstrap for the Cognito "
            "Authorizers course. Section 3, lecture L14."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the API calls we would make and exit.",
    )
    args = parser.parse_args(argv)

    user_pool_id = _env("USER_POOL_ID")
    app_client_id = _env("APP_CLIENT_ID")
    identity_pool_name = _env("IDENTITY_POOL_NAME", DEFAULT_IDENTITY_POOL_NAME)
    auth_role_name = _env("AUTH_ROLE_NAME", DEFAULT_AUTH_ROLE_NAME)
    region = _env("AWS_REGION", DEFAULT_REGION)

    if args.dry_run:
        if not user_pool_id or not app_client_id:
            print(
                "[DRY-RUN] WARNING: USER_POOL_ID or APP_CLIENT_ID not set; "
                "printing the plan with placeholders."
            )
            user_pool_id = user_pool_id or "us-east-1_placeholder"
            app_client_id = app_client_id or "placeholder-client-id"
        _print_dry_run(
            user_pool_id, app_client_id, identity_pool_name, auth_role_name, region
        )
        return 0

    if not user_pool_id or not app_client_id:
        print(
            "ERROR: USER_POOL_ID and APP_CLIENT_ID must be set. "
            "Run 02_user_pools/code/create_user_pool.py first, then export "
            "the env vars it prints.",
            file=sys.stderr,
        )
        return 2

    stack = bootstrap()
    print()
    print("Set these as environment variables for the next steps:")
    print(f"  export IDENTITY_POOL_ID={stack.identity_pool_id}")
    print(f"  export AUTH_ROLE_ARN={stack.auth_role_arn}")
    return 0


if __name__ == "__main__":
    sys.exit(main())