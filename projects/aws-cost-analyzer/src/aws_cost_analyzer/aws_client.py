"""AWS clients: injected, dry-runnable, and never mutating.

Two rules govern this module.

**Clients are injected.** Every function that talks to AWS takes its
client as a parameter. The tests pass a stub; the demo reads recorded
fixtures; only ``scripts/fetch_aws.py`` constructs a real one. That
means the AWS-facing surface is testable without a network and without
credentials, which is the only way the rest of the project can be
hermetic.

**Nothing here mutates.** There is no ``put_object``, no
``put_bucket_lifecycle_configuration``, no ``delete``. The tool is
read-only by construction, not by convention — you cannot accidentally
delete a bucket with a tool that has no code path that deletes anything.

The ``--dry-run`` flag exists so a person can see the exact API calls a
live run *would* make, without making them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from typing import Any

#: The AWS services this tool reads.
SERVICE_COST_EXPLORER = "ce"
SERVICE_S3 = "s3"
SERVICE_CLOUDWATCH = "cloudwatch"

#: The read-only actions this tool is allowed to take.
ALLOWED_ACTIONS = frozenset(
    {
        "GetCostAndUsage",
        "GetCostAndUsageWithResources",
        "GetDimensionValues",
        "GetTags",
        "ListBuckets",
        "GetBucketLifecycleConfiguration",
        "GetBucketLogging",
        "ListObjectsV2",
        "GetBucketTagging",
        "GetMetricStatistics",
        "GetMetricData",
        "ListMetrics",
    }
)


class AwsClientError(RuntimeError):
    """Raised when an AWS call fails or is not permitted."""


@dataclass(slots=True)
class ClientBundle:
    """The clients a run needs, built once and passed around.

    Holding them together means a run constructs credentials exactly
    once, and a test can substitute the whole set at the same time.
    """

    cost_explorer: Any = None
    s3: Any = None
    cloudwatch: Any = None
    region: str = ""
    dry_run: bool = False
    calls: list[dict[str, Any]] = field(default_factory=list)

    def record(self, service: str, action: str, params: dict[str, Any]) -> None:
        """Log a call for the dry-run report."""
        self.calls.append({"service": service, "action": action, "params": params})


def build_clients(
    region: str,
    *,
    dry_run: bool = False,
    profile: str | None = None,
) -> ClientBundle:
    """Build real boto3 clients for a run.

    Credentials are *not* validated here. boto3 resolves them lazily on
    the first API call, and failing at construction time would mean a
    credential problem masquerading as a configuration problem.
    """
    import boto3
    from botocore.config import Config

    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    config = Config(retries={"max_attempts": 3, "mode": "standard"})

    return ClientBundle(
        cost_explorer=session.client(SERVICE_COST_EXPLORER, region_name=region, config=config),
        s3=session.client(SERVICE_S3, region_name=region, config=config),
        cloudwatch=session.client(
            SERVICE_CLOUDWATCH, region_name=region, config=config
        ),
        region=region,
        dry_run=dry_run,
    )


# --------------------------------------------------------------------------- #
# Cost Explorer
# --------------------------------------------------------------------------- #


def get_cost_and_usage(
    clients: ClientBundle,
    *,
    start: str,
    end: str,
    granularity: str = "MONTHLY",
    group_by: list[dict[str, str]] | None = None,
    metrics: list[str] | None = None,
    filter_spec: dict[str, Any] | None = None,
    page: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One page of Cost Explorer cost-and-usage data.

    ``end`` must already be **exclusive**. The caller owns that
    translation (see ``Settings.exclusive_end``) so there is exactly one
    place in the codebase where the exclusive-end rule lives.
    """
    params: dict[str, Any] = {
        "TimePeriod": {"Start": start, "End": end},
        "Granularity": granularity,
    }
    if group_by:
        params["GroupBy"] = group_by
    if metrics:
        params["Metrics"] = metrics
    if filter_spec:
        params["Filter"] = filter_spec
    if page:
        params["NextPageToken"] = page

    clients.record(SERVICE_COST_EXPLORER, "GetCostAndUsage", params)
    if clients.dry_run:
        return {"ResultsByTime": []}

    if clients.cost_explorer is None:
        raise AwsClientError("no Cost Explorer client configured")

    try:
        return clients.cost_explorer.get_cost_and_usage(**params)
    except Exception as exc:
        raise AwsClientError(f"GetCostAndUsage failed: {exc}") from exc


def get_cost_and_usage_with_resources(
    clients: ClientBundle,
    *,
    start: str,
    end: str,
    granularity: str = "MONTHLY",
    group_by: list[dict[str, str]] | None = None,
    metrics: list[str] | None = None,
    filter_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Cost-and-usage **with the resource dimension** — i.e. per-bucket.

    This is the call that turns "S3 costs $4,000" into "bucket X costs
    $2,900 of it", which is the difference between a bill and a root
    cause.
    """
    params: dict[str, Any] = {
        "TimePeriod": {"Start": start, "End": end},
        "Granularity": granularity,
    }
    if group_by:
        params["GroupBy"] = group_by
    if metrics:
        params["Metrics"] = metrics
    if filter_spec:
        params["Filter"] = filter_spec

    clients.record(SERVICE_COST_EXPLORER, "GetCostAndUsageWithResources", params)
    if clients.dry_run:
        return {"ResultsByTime": []}

    if clients.cost_explorer is None:
        raise AwsClientError("no Cost Explorer client configured")

    try:
        return clients.cost_explorer.get_cost_and_usage_with_resources(**params)
    except Exception as exc:
        raise AwsClientError(f"GetCostAndUsageWithResources failed: {exc}") from exc


def get_dimension_values(
    clients: ClientBundle,
    *,
    dimension: str,
    start: str,
    end: str,
    search: str = "",
) -> dict[str, Any]:
    """The values of a dimension — services, or tag values."""
    params: dict[str, Any] = {
        "TimePeriod": {"Start": start, "End": end},
        "Dimension": dimension,
    }
    if search:
        params["Search"] = search

    clients.record(SERVICE_COST_EXPLORER, "GetDimensionValues", params)
    if clients.dry_run:
        return {"DimensionValues": []}

    if clients.cost_explorer is None:
        raise AwsClientError("no Cost Explorer client configured")

    try:
        return clients.cost_explorer.get_dimension_values(**params)
    except Exception as exc:
        raise AwsClientError(f"GetDimensionValues failed: {exc}") from exc


def get_tags(clients: ClientBundle) -> dict[str, Any]:
    """The cost-allocation tags that exist in the account.

    This is how the tool learns the *names* of the tag keys it may
    filter on, rather than guessing them.
    """
    clients.record(SERVICE_COST_EXPLORER, "GetTags", {})
    if clients.dry_run:
        return {"Tags": []}

    if clients.cost_explorer is None:
        raise AwsClientError("no Cost Explorer client configured")

    try:
        return clients.cost_explorer.get_tags()
    except Exception as exc:
        raise AwsClientError(f"GetTags failed: {exc}") from exc


# --------------------------------------------------------------------------- #
# S3
# --------------------------------------------------------------------------- #


def list_buckets(clients: ClientBundle) -> list[str]:
    """Every bucket name in the account."""
    clients.record(SERVICE_S3, "ListBuckets", {})
    if clients.dry_run:
        return []

    if clients.s3 is None:
        raise AwsClientError("no S3 client configured")

    try:
        response = clients.s3.list_buckets()
    except Exception as exc:
        raise AwsClientError(f"ListBuckets failed: {exc}") from exc
    return [b["Name"] for b in response.get("Buckets", [])]


def get_bucket_lifecycle(clients: ClientBundle, bucket: str) -> dict[str, Any] | None:
    """A bucket's lifecycle rules, or ``None`` if it has none.

    A missing lifecycle configuration is *itself* a finding — "forgot
    the rule" — so this returns ``None`` rather than raising. The S3 API
    raises ``NoSuchLifecycleConfiguration``, which the caller turns into
    that finding.
    """
    clients.record(SERVICE_S3, "GetBucketLifecycleConfiguration", {"Bucket": bucket})
    if clients.dry_run:
        return None

    if clients.s3 is None:
        raise AwsClientError("no S3 client configured")

    try:
        return clients.s3.get_bucket_lifecycle_configuration(Bucket=bucket)
    except Exception as exc:
        if _is_no_such_lifecycle(exc):
            return None
        raise AwsClientError(f"GetBucketLifecycleConfiguration failed for {bucket}: {exc}") from exc


def get_bucket_logging(clients: ClientBundle, bucket: str) -> dict[str, Any] | None:
    """A bucket's server access logging configuration, or ``None``."""
    clients.record(SERVICE_S3, "GetBucketLogging", {"Bucket": bucket})
    if clients.dry_run:
        return None

    if clients.s3 is None:
        raise AwsClientError("no S3 client configured")

    try:
        return clients.s3.get_bucket_logging(Bucket=bucket)
    except Exception as exc:
        raise AwsClientError(f"GetBucketLogging failed for {bucket}: {exc}") from exc


def list_objects(
    clients: ClientBundle,
    bucket: str,
    *,
    prefix: str = "",
    max_keys: int = 1000,
    start_after: str = "",
) -> dict[str, Any]:
    """One page of a bucket's objects."""
    params: dict[str, Any] = {"Bucket": bucket, "MaxKeys": max_keys}
    if prefix:
        params["Prefix"] = prefix
    if start_after:
        params["StartAfter"] = start_after

    clients.record(SERVICE_S3, "ListObjectsV2", params)
    if clients.dry_run:
        return {"Contents": [], "IsTruncated": False}

    if clients.s3 is None:
        raise AwsClientError("no S3 client configured")

    try:
        return clients.s3.list_objects_v2(**params)
    except Exception as exc:
        raise AwsClientError(f"ListObjectsV2 failed for {bucket}: {exc}") from exc


def get_bucket_tagging(clients: ClientBundle, bucket: str) -> dict[str, str]:
    """A bucket's tags."""
    clients.record(SERVICE_S3, "GetBucketTagging", {"Bucket": bucket})
    if clients.dry_run:
        return {}

    if clients.s3 is None:
        raise AwsClientError("no S3 client configured")

    try:
        response = clients.s3.get_bucket_tagging(Bucket=bucket)
    except Exception as exc:
        raise AwsClientError(f"GetBucketTagging failed for {bucket}: {exc}") from exc
    return {t["Key"]: t["Value"] for t in response.get("TagSet", [])}


# --------------------------------------------------------------------------- #
# CloudWatch
# --------------------------------------------------------------------------- #


def get_metric_statistics(
    clients: ClientBundle,
    *,
    namespace: str,
    metric_name: str,
    dimensions: list[dict[str, str]],
    start: date,
    end: date,
    period: int = 86400,
    statistics: list[str] | None = None,
) -> list[dict[str, Any]]:
    """One metric's datapoints.

    The dimension list is what makes this per-bucket: CloudWatch's
    ``AWS/S3`` metrics are keyed by ``BucketName``, and there is no
    prefix dimension — which is exactly why per-prefix analysis needs
    access logs instead.
    """
    params: dict[str, Any] = {
        "Namespace": namespace,
        "MetricName": metric_name,
        "Dimensions": dimensions,
        "StartTime": start,
        "EndTime": end,
        "Period": period,
        "Statistics": statistics or ["Average", "Sum", "Maximum"],
    }

    clients.record(SERVICE_CLOUDWATCH, "GetMetricStatistics", params)
    if clients.dry_run:
        return []

    if clients.cloudwatch is None:
        raise AwsClientError("no CloudWatch client configured")

    try:
        response = clients.cloudwatch.get_metric_statistics(**params)
    except Exception as exc:
        raise AwsClientError(f"GetMetricStatistics failed for {metric_name}: {exc}") from exc
    return response.get("Datapoints", [])


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _is_no_such_lifecycle(exc: Exception) -> bool:
    """Whether an exception is S3's "no lifecycle configuration" error.

    Checked by code rather than by message, because botocore's message
    wording is not part of its contract.
    """
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return False
    code = response.get("Error", {}).get("Code", "")
    return code == "NoSuchLifecycleConfiguration"


def dry_run_report(clients: ClientBundle) -> str:
    """A readable summary of the calls a live run would make."""
    if not clients.calls:
        return "No AWS calls were planned."
    lines = [f"{len(clients.calls)} AWS call(s) planned (dry run, nothing was called):"]
    for index, call in enumerate(clients.calls, start=1):
        lines.append(f"  {index}. {call['service']}.{call['action']}")
        for key, value in sorted(call["params"].items()):
            lines.append(f"       {key} = {value!r}")
    return "\n".join(lines)


def has_credentials() -> bool:
    """Whether any AWS credential source is present.

    A convenience for the CLI's error message — a run without
    credentials should say so plainly rather than surfacing a botocore
    traceback.
    """
    if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        return True
    if os.environ.get("AWS_PROFILE") or os.environ.get("AWS_ROLE_ARN"):
        return True
    return os.path.exists(os.path.expanduser("~/.aws/credentials"))
