"""
region_az_demo.py — list enabled AWS regions and the AZs in the current region.

> Author: Prem Vishnoi <prem.vishnoi@example.com>
> Section: 02 (EC2 Fundamentals)
> Companion lecture: L06, L08

The script demonstrates two EC2 read-only API calls:

1. ``ec2.describe_regions()`` returns every region the calling account
   is allowed to use, together with the region endpoint. We use it to
   build the "world view" of AWS.
2. ``ec2.describe_availability_zones()`` returns the AZs in the current
   region. The response includes BOTH the conventional AZ name (for
   example ``us-east-1a``) AND the account-specific AZ ID (for example
   ``use1-az1``) — which is exactly the L06 lecture point about AZ IDs
   being randomized per account.

The script uses only the Python standard library + boto3 (which is
already a dependency of the rest of the AWS course). No third-party
packages required to run the demo.

Usage:

    export AWS_REGION=us-east-1     # optional, defaults to us-east-1
    python region_az_demo.py

The ``main()`` function bails out gracefully — prints a friendly
message and exits with code 0 — when ``AWS_REGION`` is unset OR when
no AWS credentials can be found. This makes the demo safe to run on
a laptop with no AWS configuration: it does not crash, it just
explains what to do.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
)


# ---------------------------------------------------------------------------
# Helpers — the work that the tests will exercise directly.
# ---------------------------------------------------------------------------

def list_regions(client: Any) -> List[Dict[str, str]]:
    """Call ``ec2.describe_regions`` and return a list of normalized rows.

    Each row is a dict with two keys: ``region`` (for example
    ``us-east-1``) and ``endpoint`` (for example
    ``ec2.us-east-1.amazonaws.com``). Only enabled regions are
    returned (``AllRegions=False`` is the API default).
    """
    response = client.describe_regions()
    return [
        {"region": r["RegionName"], "endpoint": r["Endpoint"]}
        for r in response.get("Regions", [])
    ]


def list_availability_zones(client: Any) -> List[Dict[str, str]]:
    """Call ``ec2.describe_availability_zones`` and return normalized rows.

    Each row is a dict with two keys: ``name`` (the conventional
    ``us-east-1a`` style AZ name) and ``zone_id`` (the
    account-specific ``use1-az1`` style AZ ID). This pairing is the
    L06 "AZ IDs are randomized per account" point.
    """
    response = client.describe_availability_zones()
    return [
        {"name": z["ZoneName"], "zone_id": z["ZoneId"]}
        for z in response.get("AvailabilityZones", [])
    ]


def build_az_name_to_id_map(azs: List[Dict[str, str]]) -> Dict[str, str]:
    """Return a ``{az_name: az_id}`` dict for the AZ rows in ``azs``.

    This is the helper the L06 lecture calls out: "given the AZs in
    your account, build the table that maps ``us-east-1a`` →
    ``use1-az1``". A dict is the natural shape — lookup is O(1) and
    Python's ``str(Dict)`` is human-readable.
    """
    return {az["name"]: az["zone_id"] for az in azs}


def pick_default_region() -> str:
    """Return the region the demo should run against.

    Order of precedence:

    1. ``AWS_REGION`` environment variable (the standard AWS SDK
       convention).
    2. ``AWS_DEFAULT_REGION`` environment variable (the AWS CLI
       convention).
    3. Hard-coded fallback ``us-east-1`` (the original AWS region
       and the most common default).
    """
    return (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "us-east-1"
    )


# ---------------------------------------------------------------------------
# Pretty-printing — small fixed-width tables, no external deps.
# ---------------------------------------------------------------------------

def _format_table(headers: List[str], rows: List[List[str]]) -> List[str]:
    """Return a list of lines that print a small fixed-width table.

    No external deps; just a straightforward "compute column widths,
    then format" routine. Empty rows produce just the header.
    """
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if len(cell) > widths[i]:
                widths[i] = len(cell)
    sep = "-+-".join("-" * w for w in widths)
    out = [" | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))]
    out.append(sep)
    for row in rows:
        out.append(" | ".join(c.ljust(widths[i]) for i, c in enumerate(row)))
    return out


def render_regions_table(regions: List[Dict[str, str]]) -> str:
    """Return a printable string showing all enabled regions."""
    if not regions:
        return "(no enabled regions returned)"
    rows = [[r["region"], r["endpoint"]] for r in regions]
    return "\n".join(_format_table(["Region", "Endpoint"], rows))


def render_azs_table(azs: List[Dict[str, str]]) -> str:
    """Return a printable string showing AZ name -> AZ ID for the current region."""
    if not azs:
        return "(no availability zones returned)"
    rows = [[az["name"], az["zone_id"]] for az in azs]
    return "\n".join(_format_table(["AZ Name", "AZ ID (account-specific)"], rows))


# ---------------------------------------------------------------------------
# Top-level entry point.
# ---------------------------------------------------------------------------

# Errors that mean "no credentials configured" or "the SDK cannot talk
# to AWS". We treat all of them as "bail out gracefully".
_CREDENTIAL_ERRORS: Tuple[type, ...] = (
    NoCredentialsError,
    PartialCredentialsError,
    EndpointConnectionError,
)


def _has_credentials() -> bool:
    """Return True iff the default boto3 session can find credentials.

    We do this by asking the default session to load credentials. If
    the underlying provider chain raises ``NoCredentialsError`` we
    treat it as "not configured". Anything else (for example a
    network blip) is also "not configured" for the purposes of this
    demo — we want a friendly message, not a stack trace.
    """
    try:
        # Importing inside the function keeps the module importable
        # even on systems that have not yet installed boto3.
        import boto3.session

        session = boto3.session.Session()
        # ``get_credentials()`` returns ``None`` if no provider
        # in the chain had credentials. The chain itself does not
        # raise; it just returns ``None`` on miss.
        return session.get_credentials() is not None
    except Exception:
        return False


def main(argv: Optional[List[str]] = None) -> int:
    """Run the demo. Returns the process exit code (0 = success)."""
    region = pick_default_region()

    # Bail out gracefully when the environment is not set up.
    if not _has_credentials():
        print("region_az_demo: no AWS credentials found.")
        print("Configure credentials with one of:")
        print("  - AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY env vars")
        print("  - aws configure (writes ~/.aws/credentials)")
        print("  - AWS_PROFILE + aws sso login")
        print(f"Target region (would have been): {region}")
        return 0

    print(f"region_az_demo — region = {region}")
    print()

    try:
        ec2 = boto3.client("ec2", region_name=region)

        regions = list_regions(ec2)
        print(f"Enabled regions visible to this account: {len(regions)}")
        print(render_regions_table(regions))
        print()

        azs = list_availability_zones(ec2)
        print(f"Availability Zones in {region}: {len(azs)}")
        print(render_azs_table(azs))
        print()

        mapping = build_az_name_to_id_map(azs)
        print("AZ name -> AZ ID mapping (this account):")
        for name, zone_id in mapping.items():
            print(f"  {name}  ->  {zone_id}")
        print()

        print("Note: in a different AWS account, the same AZ name")
        print("may map to a different AZ ID. See lecture L06.")
        return 0

    except (NoCredentialsError, PartialCredentialsError) as exc:
        print(f"region_az_demo: credentials error: {exc}")
        return 0
    except (EndpointConnectionError, BotoCoreError, ClientError) as exc:
        # EndpointConnectionError = cannot reach AWS at all.
        # BotoCoreError / ClientError = API call failed for some
        # other reason. Either way: friendly message, exit 0.
        print(f"region_az_demo: could not reach AWS ({type(exc).__name__}): {exc}")
        print("The demo bails out gracefully so it can be run on any laptop.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
