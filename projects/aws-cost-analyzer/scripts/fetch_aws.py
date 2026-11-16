#!/usr/bin/env python3
"""Pull live data from AWS into a snapshot.

This is the only script in the project that constructs a real AWS
client. Everything else reads a snapshot.

    python scripts/fetch_aws.py                       # the default window
    python scripts/fetch_aws.py --start 2026-01-01 --end 2026-06-30
    python scripts/fetch_aws.py --dry-run             # print the API calls, call nothing
    python scripts/fetch_aws.py --tag-keys Data Data-Squad

The ``--dry-run`` flag is the one to use first. It prints every API call
the run *would* make — including the exact filter payload — without
making any of them, so a mistyped window or a wrong filter is visible
before it becomes a snapshot.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from aws_cost_analyzer.aws_client import (  # noqa: E402
    ClientBundle,
    build_clients,
    dry_run_report,
    get_cost_and_usage,
    get_cost_and_usage_with_resources,
    get_tags,
)
from aws_cost_analyzer.ce_normalizer import (  # noqa: E402
    merge_pages,
    normalize_cost_and_usage,
    normalize_with_resources,
    paginate,
)
from aws_cost_analyzer.config import load_settings  # noqa: E402
from aws_cost_analyzer.snapshots import (  # noqa: E402
    DEFAULT_SNAPSHOT_DIR,
    KIND_COST_RECORDS,
    snapshot_from_result,
    write_snapshot,
)
from aws_cost_analyzer.tag_filter import build_tag_key_filter  # noqa: E402

SERVICE_GROUP = [{"Type": "DIMENSION", "Key": "SERVICE"}]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pull live AWS cost data into a snapshot.")
    parser.add_argument("--start", help="Window start (YYYY-MM-DD). Inclusive.")
    parser.add_argument("--end", help="Window end (YYYY-MM-DD). Inclusive.")
    parser.add_argument("--region", help="AWS region.")
    parser.add_argument("--profile", help="AWS profile name.")
    parser.add_argument("--granularity", default="MONTHLY", choices=["MONTHLY", "DAILY"])
    parser.add_argument(
        "--tag-keys",
        nargs="*",
        help="Cost-allocation tag *names* to filter on, e.g. Data Data-Squad.",
    )
    parser.add_argument(
        "--with-resources",
        action="store_true",
        help="Also pull the per-resource breakdown (per-bucket for S3).",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_SNAPSHOT_DIR),
        help="Directory to write the snapshot into.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the API calls that would be made. Makes none of them.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    settings = load_settings(
        {
            "AWS_REGION": args.region,
            "AWSCA_START": args.start,
            "AWSCA_END": args.end,
            "AWSCA_GRANULARITY": args.granularity,
        }
    )

    clients: ClientBundle = build_clients(
        settings.region,
        dry_run=args.dry_run,
        profile=args.profile,
    )

    # The end date is exclusive on the wire. Sending the user's
    # 2026-10-31 literally would make October vanish with no error.
    start = settings.start
    end = settings.exclusive_end

    filter_spec = None
    if args.tag_keys:
        filter_spec = build_tag_key_filter(args.tag_keys)

    print(f"Region:      {settings.region}")
    print(f"Window:      {start} .. {settings.end}  (sent as End={end}, exclusive)")
    print(f"Granularity: {settings.granularity}")
    if filter_spec:
        print(f"Filter:      {filter_spec}")
    print()

    # --- the plain service-level view ------------------------------------ #
    pages = paginate(
        lambda token: get_cost_and_usage(
            clients,
            start=start,
            end=end,
            granularity=settings.granularity,
            group_by=SERVICE_GROUP,
            filter_spec=filter_spec,
            page={"NextPageToken": token} if token else None,
        )
    )
    merged = merge_pages(pages)
    result = normalize_cost_and_usage(
        merged,
        region=settings.region,
        group_definitions=SERVICE_GROUP,
        granularity=settings.granularity,
    )

    if args.dry_run:
        print(dry_run_report(clients))
        print()
        print(f"{len(result.records)} records would be produced.")
        return 0

    snapshot = snapshot_from_result(
        result,
        kind=KIND_COST_RECORDS,
        region=settings.region,
        start=settings.start,
        end=settings.end,
        granularity=settings.granularity,
        group_definitions=SERVICE_GROUP,
        raw=merged,
        notes="service-level view",
    )
    path = write_snapshot(snapshot, args.out)
    print(f"Wrote {len(result.records)} records to {path}")

    if result.errors:
        print(f"\n{len(result.errors)} normalisation error(s):")
        for error in result.errors:
            print(f"  - {error}")

    if result.estimated_periods:
        print(f"\nEstimated (partial) periods: {', '.join(result.estimated_periods)}")

    # --- the per-resource view -------------------------------------------- #
    if args.with_resources:
        resource_pages = paginate(
            lambda token: get_cost_and_usage_with_resources(
                clients,
                start=start,
                end=end,
                granularity=settings.granularity,
                group_by=SERVICE_GROUP,
                filter_spec=filter_spec,
            )
        )
        resource_merged = merge_pages(resource_pages)
        resource_result = normalize_with_resources(
            resource_merged,
            region=settings.region,
            group_definitions=SERVICE_GROUP,
            granularity=settings.granularity,
        )
        resource_snapshot = snapshot_from_result(
            resource_result,
            kind=KIND_COST_RECORDS,
            region=settings.region,
            start=settings.start,
            end=settings.end,
            granularity=settings.granularity,
            group_definitions=SERVICE_GROUP,
            raw=resource_merged,
            notes="per-resource view",
        )
        resource_path = write_snapshot(resource_snapshot, args.out)
        print(f"Wrote {len(resource_result.records)} per-resource records to {resource_path}")

    # --- the tag names that exist in the account -------------------------- #
    try:
        tags = get_tags(clients)
        tag_list = tags.get("Tags", []) or []
        if tag_list:
            print("\nCost-allocation tags in this account:")
            for tag in tag_list:
                print(f"  {tag.get('Key', '?')} = {tag.get('Values', [])}")
    except Exception as exc:  # noqa: BLE001 — a tag listing is a convenience
        print(f"\nCould not list cost-allocation tags: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
