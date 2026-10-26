"""Idempotent boto3 script that creates a Cognito User Pool + App Client + test user.

Section 2 (L05-L10) of the AWS Cognito Authorizers course.

Run::

    python3 create_user_pool.py              # create or re-use the pool
    python3 create_user_pool.py --dry-run    # print the plan, don't touch AWS

Environment variables (all optional):

    USER_POOL_NAME   name of the pool.       default: demo-cognito-course-pool
    APP_CLIENT_NAME  name of the app client. default: demo-cognito-course-client
    TEST_USERNAME    user to create.         default: alice@example.com
    TEST_PASSWORD    permanent password.     default: TempPass!2026
    AWS_REGION       region to use.          default: us-east-1

Design goals:

    - Idempotent: re-running with the same USER_POOL_NAME returns the
      existing pool's id, reuses the app client, and skips user
      creation if the user already exists.
    - No secrets: the app client is created with no client secret
      (``GenerateSecret=False``), so it is safe to embed in an SPA or
      mobile app.
    - Password policy: minimum length 8, requires at least one symbol.
    - Email-as-username: ``UsernameAttributes=["email"]`` + email in
      the auto-verified attributes list.
    - Dry-run: ``--dry-run`` prints the API calls we *would* make and
      exits 0 without any AWS calls.
    - Testable: every AWS call is encapsulated in a module-level
      function so ``moto`` can mock them.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError


# ---------------------------------------------------------------------------
# Defaults — overridable via env vars so tests can monkey-patch them
# ---------------------------------------------------------------------------
DEFAULT_REGION = "us-east-1"
DEFAULT_POOL_NAME = "demo-cognito-course-pool"
DEFAULT_CLIENT_NAME = "demo-cognito-course-client"
DEFAULT_USERNAME = "alice@example.com"
DEFAULT_PASSWORD = "TempPass!2026"  # meets our own policy (>=8, has symbol)


# ---------------------------------------------------------------------------
# Result dataclass — main() returns this so callers (and the assignment)
# can consume the created resources
# ---------------------------------------------------------------------------
@dataclass
class UserPoolStack:
    """The minimum you need to wire a Cognito User Pool into an app."""

    user_pool_id: str
    app_client_id: str
    test_username: str
    test_password: str
    region: str


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def _env(name: str, default: str) -> str:
    """Read an env var with a fallback. Re-read every call so tests can patch."""
    return os.environ.get(name, default)


def _build_pool_kwargs(pool_name: str) -> dict:
    """Build the kwargs for ``cognito-idp.create_user_pool``."""
    return {
        "PoolName": pool_name,
        # email-as-username (no separate `username` attribute)
        "UsernameAttributes": ["email"],
        "AutoVerifiedAttributes": ["email"],
        # Password policy — minimum length 8, requires at least one symbol
        "Policies": {
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": False,
                "RequireLowercase": False,
                "RequireNumbers": False,
                "RequireSymbols": True,
                "TemporaryPasswordValidityDays": 7,
            },
        },
        # Schema — minimum needed for email-as-username
        "Schema": [
            {
                "Name": "email",
                "AttributeDataType": "String",
                "Required": True,
                "Mutable": True,
            },
        ],
        # Account-recovery: prefer verified email
        "AccountRecoverySetting": {
            "RecoveryMechanisms": [
                {"Name": "verified_email", "Priority": 1},
            ],
        },
        # Email configuration — use Cognito's built-in sandbox for the course
        "EmailConfiguration": {"EmailSendingAccount": "COGNITO_DEFAULT"},
        # Admin-only sign-up (no self-registration through Hosted UI)
        "AdminCreateUserConfig": {"AllowAdminCreateUserOnly": True},
    }


def _build_client_kwargs(pool_id: str, client_name: str) -> dict:
    """Build the kwargs for ``cognito-idp.create_user_pool_client``."""
    return {
        "UserPoolId": pool_id,
        "ClientName": client_name,
        # No client secret — safe for SPA / mobile apps
        "GenerateSecret": False,
        # Auth flows we will use in section 4
        "AllowedOAuthFlows": ["code"],
        "AllowedOAuthScopes": ["openid", "email", "profile"],
        "AllowedOAuthFlowsUserPoolClient": True,
        "SupportedIdentityProviders": ["COGNITO"],
        # Token validity — slightly tightened vs defaults for the demo
        "AccessTokenValidity": 60,         # minutes
        "IdTokenValidity": 60,             # minutes
        "RefreshTokenValidity": 30,        # days
        "TokenValidityUnits": {
            "AccessToken": "minutes",
            "IdToken": "minutes",
            "RefreshToken": "days",
        },
        # Prevent the OpenID Connect implicit flow — use auth-code only
        "PreventUserExistenceErrors": "ENABLED",
    }


# ---------------------------------------------------------------------------
# Lookup helpers — return the existing resource or None
# ---------------------------------------------------------------------------
def _find_existing_pool(cognito, name: str) -> str | None:
    paginator = cognito.get_paginator("list_user_pools")
    for page in paginator.paginate(MaxResults=60):
        for pool in page["UserPools"]:
            if pool["Name"] == name:
                return pool["Id"]
    return None


def _find_existing_client(cognito, pool_id: str, client_name: str) -> str | None:
    paginator = cognito.get_paginator("list_user_pool_clients")
    for page in paginator.paginate(UserPoolId=pool_id, MaxResults=60):
        for client in page["UserPoolClients"]:
            if client["ClientName"] == client_name:
                return client["ClientId"]
    return None


def _user_exists(cognito, pool_id: str, username: str) -> bool:
    try:
        cognito.admin_get_user(UserPoolId=pool_id, Username=username)
        return True
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"UserNotFoundException", "UserNotFound"}:
            return False
        raise


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------
def bootstrap(
    *,
    pool_name: str | None = None,
    client_name: str | None = None,
    username: str | None = None,
    password: str | None = None,
    region: str | None = None,
    cognito=None,
) -> UserPoolStack:
    """Create the User Pool stack. Idempotent.

    Args:
        pool_name:    overrides env USER_POOL_NAME
        client_name:  overrides env APP_CLIENT_NAME
        username:     overrides env TEST_USERNAME
        password:     overrides env TEST_PASSWORD
        region:       overrides env AWS_REGION
        cognito:      optional pre-built boto3 client (used by tests)

    Returns:
        UserPoolStack with the ids + test user credentials.
    """
    pool_name = pool_name or _env("USER_POOL_NAME", DEFAULT_POOL_NAME)
    client_name = client_name or _env("APP_CLIENT_NAME", DEFAULT_CLIENT_NAME)
    username = username or _env("TEST_USERNAME", DEFAULT_USERNAME)
    password = password or _env("TEST_PASSWORD", DEFAULT_PASSWORD)
    region = region or _env("AWS_REGION", DEFAULT_REGION)

    if cognito is None:
        cognito = boto3.client("cognito-idp", region_name=region)

    # 1. User pool ----------------------------------------------------------
    pool_id = _find_existing_pool(cognito, pool_name)
    if pool_id:
        print(f"[create_user_pool] Reusing existing User Pool: {pool_id}")
    else:
        resp = cognito.create_user_pool(**_build_pool_kwargs(pool_name))
        pool_id = resp["UserPool"]["Id"]
        print(f"[create_user_pool] Created User Pool: {pool_id}")

    # 2. App client ---------------------------------------------------------
    client_id = _find_existing_client(cognito, pool_id, client_name)
    if client_id:
        print(f"[create_user_pool] Reusing existing App Client: {client_id}")
    else:
        resp = cognito.create_user_pool_client(
            **_build_client_kwargs(pool_id, client_name)
        )
        client_id = resp["UserPoolClient"]["ClientId"]
        print(f"[create_user_pool] Created App Client: {client_id}")

    # 3. Test user ----------------------------------------------------------
    if _user_exists(cognito, pool_id, username):
        print(f"[create_user_pool] Reusing existing test user: {username}")
    else:
        cognito.admin_create_user(
            UserPoolId=pool_id,
            Username=username,
            UserAttributes=[
                {"Name": "email", "Value": username},
                {"Name": "email_verified", "Value": "true"},
            ],
            MessageAction="SUPPRESS",  # don't send welcome email in the course
        )
        print(f"[create_user_pool] Created test user: {username}")

        # 4. Set a permanent password (skip FORCE_CHANGE_PASSWORD on first sign-in)
        cognito.admin_set_user_password(
            UserPoolId=pool_id,
            Username=username,
            Password=password,
            Permanent=True,
        )
        print("[create_user_pool] Set permanent password for test user")

    return UserPoolStack(
        user_pool_id=pool_id,
        app_client_id=client_id,
        test_username=username,
        test_password=password,
        region=region,
    )


def _print_dry_run() -> None:
    """Print the API calls we *would* make and exit."""
    pool_name = _env("USER_POOL_NAME", DEFAULT_POOL_NAME)
    client_name = _env("APP_CLIENT_NAME", DEFAULT_CLIENT_NAME)
    username = _env("TEST_USERNAME", DEFAULT_USERNAME)
    region = _env("AWS_REGION", DEFAULT_REGION)

    print("[DRY-RUN] No AWS calls will be made. Plan:")
    print(f"  cognito-idp.create_user_pool({_build_pool_kwargs(pool_name)!r})")
    print(f"  cognito-idp.create_user_pool_client({_build_client_kwargs('<POOL_ID>', client_name)!r})")
    print(f"  cognito-idp.admin_create_user({username!r})")
    print(f"  cognito-idp.admin_set_user_password({username!r}, permanent=True)")
    print(f"  region: {region}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Idempotent Cognito User Pool bootstrap for the Cognito "
            "Authorizers course. Section 2, lecture L10."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the API calls we would make and exit.",
    )
    args = parser.parse_args(argv)

    if args.dry_run:
        _print_dry_run()
        return 0

    stack = bootstrap()
    print()
    print("Set these as environment variables for the next steps:")
    print(f"  export USER_POOL_ID={stack.user_pool_id}")
    print(f"  export APP_CLIENT_ID={stack.app_client_id}")
    print(f"  export TEST_USERNAME={stack.test_username}")
    print(f"  export TEST_PASSWORD={stack.test_password}")
    return 0


if __name__ == "__main__":
    sys.exit(main())