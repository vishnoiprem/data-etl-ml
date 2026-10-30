#!/usr/bin/env python3
"""
local_runner.py — the command-line entry point for the GCP course project.

This is the "console" the course's labs run against. Every command
works with no GCP account, no credentials and no bill.

Usage:
    python project/local_runner.py --list
    python project/local_runner.py --services
    python project/local_runner.py --regions
    python project/local_runner.py --iam
    python project/local_runner.py --run
    python project/local_runner.py --cost
    python project/local_runner.py --compare
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent / "core"
sys.path.insert(0, str(CORE_DIR))

from cost_model import compare_architectures, format_comparison  # noqa: E402
from iam_policy import ROLE_SUMMARY  # noqa: E402
from platform_sim import (  # noqa: E402
    build_demo_project,
    format_pipeline_log,
    format_resource_tree,
)
from service_catalog import (  # noqa: E402
    CATEGORIES,
    REGIONS,
    SERVICES,
    format_region_matrix,
    format_service_table,
    services_by_category,
)

COURSE_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA = COURSE_ROOT / "sample_data" / "events.csv"
MALFORMED_DATA = COURSE_ROOT / "sample_data" / "malformed_events.csv"


def cmd_list() -> None:
    """Print the available commands."""
    print("Available commands:")
    for name in (
        "--list",
        "--services",
        "--categories",
        "--regions",
        "--iam",
        "--run",
        "--cost",
        "--compare",
    ):
        print(f"  {name}")


def cmd_services() -> None:
    """Print the full service inventory."""
    print(format_service_table())


def cmd_categories() -> None:
    """Print the services grouped by category."""
    for category in CATEGORIES:
        services = services_by_category(category)
        print(f"\n{category} ({len(services)})")
        for service in services:
            link = " → deep dive in the sibling course" if service.deep_dive else ""
            print(f"  {service.name:<28} {service.summary}{link}")


def cmd_regions() -> None:
    """Print the region availability matrix."""
    print(format_region_matrix())


def cmd_iam() -> None:
    """Print the demo project's IAM policy and what each identity can do."""
    project = build_demo_project()
    print("IAM policy")
    print("----------")
    for resource, bindings in sorted(project.policy.bindings.items()):
        print(f"  {resource}:")
        for principal, binding in bindings:
            print(f"    {principal}  →  {binding.role}")

    print("\nEffective access")
    print("---------------")
    checks = [
        ("analytics@example.com", "storage.objects.get", "projects/gcp-de-course/buckets/raw-events"),
        ("analytics@example.com", "storage.objects.create", "projects/gcp-de-course/buckets/raw-events"),
        ("analytics@example.com", "bigquery.tables.getData", "projects/gcp-de-course/datasets/curated"),
        ("analytics@example.com", "bigquery.tables.create", "projects/gcp-de-course/datasets/curated"),
        ("pipeline-sa@gcp-de-course.iam.gserviceaccount.com", "pubsub.topics.publish", "projects/gcp-de-course"),
        ("pipeline-sa@gcp-de-course.iam.gserviceaccount.com", "pubsub.subscriptions.consume", "projects/gcp-de-course"),
        ("stranger@example.com", "storage.objects.get", "projects/gcp-de-course"),
    ]
    for identity, permission, resource in checks:
        allowed = project.can(identity, permission, resource=resource)
        mark = "✓" if allowed else "✗"
        print(f"  {mark} {identity:<50} {permission}")


def cmd_run() -> None:
    """Run the pipeline against the sample data."""
    if not SAMPLE_DATA.exists():
        print(
            f"sample data not found at {SAMPLE_DATA}\n"
            "Generate it first:\n"
            "  python resources/sample_data.py --output-dir ./sample_data"
        )
        raise SystemExit(1)

    project = build_demo_project()
    print(format_resource_tree(project))
    print()

    lines = SAMPLE_DATA.read_text(encoding="utf-8").splitlines()
    result = project.run_pipeline(lines)
    print(format_pipeline_log(result))
    print()

    # The malformed rows are a separate file, so the clean run above
    # rejects nothing. Merge them in so the dead-letter path is visible:
    # a pipeline that can reject bad input must have bad input to reject.
    if MALFORMED_DATA.exists():
        malformed = MALFORMED_DATA.read_text(encoding="utf-8").splitlines()
        combined = project.run_pipeline(lines + malformed)
        print("Dead-letter path")
        print("----------------")
        print(f"  malformed rows rejected: {len(combined.rejected)}")
        for reason, count in sorted(combined.rejected_counts.items()):
            print(f"    {reason:<24} {count}")
        print()
        print("Reject counts:", combined.rejected_counts or "{}")


def cmd_cost() -> None:
    """Print the monthly cost estimate for the demo project."""
    project = build_demo_project()
    costs = project.estimate_monthly_cost()
    print("Monthly cost estimate (us-central1 list prices)")
    print("-----------------------------------------------")
    total = 0.0
    for service, cost in sorted(costs.items()):
        print(f"  {service:<20} ${cost:>10.4f}")
        total += cost
    print(f"  {'TOTAL':<20} ${total:>10.4f}")


def cmd_compare() -> None:
    """Compare the cost of the same workload across architectures."""
    print("Same workload, different architectures")
    print("---------------------------------------")
    options = compare_architectures(scanned_tb=1.0, partition_factor=0.01)
    print(format_comparison(options))


def main(argv: list[str] | None = None) -> int:
    """Run the local runner.

    Args:
        argv: The argument list, or None for ``sys.argv``.

    Returns:
        The process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--list", action="store_true", help="List the commands")
    parser.add_argument("--services", action="store_true", help="Print the service inventory")
    parser.add_argument("--categories", action="store_true", help="Group services by category")
    parser.add_argument("--regions", action="store_true", help="Print the region matrix")
    parser.add_argument("--iam", action="store_true", help="Print the IAM policy and access")
    parser.add_argument("--run", action="store_true", help="Run the pipeline")
    parser.add_argument("--cost", action="store_true", help="Estimate the monthly cost")
    parser.add_argument("--compare", action="store_true", help="Compare architecture costs")
    args = parser.parse_args(argv)

    if args.services:
        cmd_services()
    elif args.categories:
        cmd_categories()
    elif args.regions:
        cmd_regions()
    elif args.iam:
        cmd_iam()
    elif args.run:
        cmd_run()
    elif args.cost:
        cmd_cost()
    elif args.compare:
        cmd_compare()
    else:
        cmd_list()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
