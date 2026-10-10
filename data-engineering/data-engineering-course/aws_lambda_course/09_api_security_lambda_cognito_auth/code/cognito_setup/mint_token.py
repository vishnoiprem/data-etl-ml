"""Mint a client_credentials access token for the section 9 demo pool.

Required env vars:
    USER_POOL_ID       e.g. us-east-1_xxxxxxxxx
    APP_CLIENT_ID      the App Client id from create_user_pool.py
    APP_CLIENT_SECRET  the App Client secret (only visible at create
                       time — fetch with describe-user-pool-client if
                       you did not capture it)
    COGNITO_DOMAIN     the User Pool domain prefix
                       (e.g. demo-section9-1730000000)
    AWS_REGION         default us-east-1
"""

from __future__ import annotations

import base64
import json
import os
import sys

import requests

REGION = os.environ.get("AWS_REGION", "us-east-1")
USER_POOL_ID = os.environ["USER_POOL_ID"]
APP_CLIENT_ID = os.environ["APP_CLIENT_ID"]
APP_CLIENT_SECRET = os.environ["APP_CLIENT_SECRET"]
DOMAIN = os.environ["COGNITO_DOMAIN"]

# The resource server identifier is the pool name used in
# create_user_pool.py. Keep them in sync.
RESOURCE_SERVER_IDENTIFIER = os.environ.get(
    "RESOURCE_SERVER_IDENTIFIER",
    os.environ.get("USER_POOL_NAME", "demo-section9-pool"),
)
SCOPE_NAME = os.environ.get("SCOPE_NAME", "read:items")


def _decode_jwt(jwt_str: str) -> dict:
    body = jwt_str.split(".")[1]
    body += "=" * (-len(body) % 4)
    return json.loads(base64.urlsafe_b64decode(body))


def main() -> int:
    basic = base64.b64encode(
        f"{APP_CLIENT_ID}:{APP_CLIENT_SECRET}".encode()
    ).decode()

    resp = requests.post(
        f"https://{DOMAIN}.auth.{REGION}.amazoncognito.com/oauth2/token",
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "scope": f"{RESOURCE_SERVER_IDENTIFIER}/{SCOPE_NAME}",
        },
        timeout=10,
    )
    resp.raise_for_status()
    body = resp.json()
    token = body["access_token"]

    # Print the raw token for the caller, then the decoded claims for
    # quick inspection.
    print(token)
    print("---")
    print(json.dumps(_decode_jwt(token), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
