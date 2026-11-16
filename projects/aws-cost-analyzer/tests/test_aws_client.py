"""The AWS client layer: injection, dry-run, read-only, and pagination."""

from __future__ import annotations

import pytest

from aws_cost_analyzer.aws_client import (
    ALLOWED_ACTIONS,
    AwsClientError,
    ClientBundle,
    dry_run_report,
    get_bucket_lifecycle,
    get_bucket_logging,
    get_cost_and_usage,
    get_dimension_values,
    get_metric_statistics,
    get_tags,
    list_buckets,
    list_objects,
)


class _StubCe:
    """A Cost Explorer stub that records what it was asked."""

    def __init__(self, payload: dict | None = None, error: Exception | None = None):
        self.payload = payload or {"ResultsByTime": []}
        self.error = error
        self.calls: list[dict] = []

    def _handle(self, **params):
        self.calls.append(params)
        if self.error:
            raise self.error
        return self.payload

    def get_cost_and_usage(self, **params):
        return self._handle(**params)

    def get_cost_and_usage_with_resources(self, **params):
        return self._handle(**params)

    def get_dimension_values(self, **params):
        return self._handle(**params)

    def get_tags(self, **params):
        return self._handle(**params)


class _StubS3:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls: list[dict] = []

    def _handle(self, **params):
        self.calls.append(params)
        if self.error:
            raise self.error
        return {}

    def list_buckets(self):
        self._handle()
        return {"Buckets": [{"Name": "bucket-a"}, {"Name": "bucket-b"}]}

    def get_bucket_lifecycle_configuration(self, **params):
        self.calls.append(params)
        if self.error:
            raise self.error
        return {"Rules": [{"ID": "r1"}]}

    def get_bucket_logging(self, **params):
        self.calls.append(params)
        if self.error:
            raise self.error
        return {"LoggingEnabled": {"TargetBucket": "logs"}}

    def list_objects_v2(self, **params):
        self.calls.append(params)
        if self.error:
            raise self.error
        return {"Contents": [{"Key": "a.csv", "Size": 10}], "IsTruncated": False}

    def get_bucket_tagging(self, **params):
        self.calls.append(params)
        if self.error:
            raise self.error
        return {"TagSet": [{"Key": "team", "Value": "data"}]}


class _StubCloudWatch:
    def __init__(self):
        self.calls: list[dict] = []

    def get_metric_statistics(self, **params):
        self.calls.append(params)
        return {"Datapoints": [{"Timestamp": 1, "Sum": 5.0}]}


class _NoSuchLifecycle(Exception):
    def __init__(self):
        self.response = {"Error": {"Code": "NoSuchLifecycleConfiguration", "Message": "nope"}}


def _clients(**kwargs) -> ClientBundle:
    bundle = ClientBundle(
        cost_explorer=_StubCe(),
        s3=_StubS3(),
        cloudwatch=_StubCloudWatch(),
        region="ap-southeast-1",
    )
    for key, value in kwargs.items():
        setattr(bundle, key, value)
    return bundle


class TestInjection:
    def test_a_stub_client_is_used_as_is(self):
        clients = _clients()
        ce = clients.cost_explorer
        get_cost_and_usage(
            clients,
            start="2026-05-01",
            end="2026-11-01",
            group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        assert ce.calls, "the injected client should have been called"

    def test_a_call_is_recorded(self):
        clients = _clients()
        get_cost_and_usage(clients, start="2026-05-01", end="2026-11-01")
        assert len(clients.calls) == 1
        assert clients.calls[0]["action"] == "GetCostAndUsage"

    def test_the_period_is_passed_through(self):
        clients = _clients()
        get_cost_and_usage(clients, start="2026-05-01", end="2026-11-01")
        params = clients.calls[0]["params"]
        assert params["TimePeriod"] == {"Start": "2026-05-01", "End": "2026-11-01"}

    def test_a_filter_is_passed_through(self):
        clients = _clients()
        spec = {"Tags": {"Key": "TagKey", "Values": ["Data"], "MatchOptions": ["CONTAINS"]}}
        get_cost_and_usage(clients, start="2026-05-01", end="2026-11-01", filter_spec=spec)
        assert clients.calls[0]["params"]["Filter"] == spec


class TestDryRun:
    def test_nothing_is_called_in_a_dry_run(self):
        clients = _clients(dry_run=True)
        get_cost_and_usage(clients, start="2026-05-01", end="2026-11-01")
        assert clients.cost_explorer.calls == []

    def test_a_dry_run_still_returns_an_empty_payload(self):
        clients = _clients(dry_run=True)
        payload = get_cost_and_usage(clients, start="2026-05-01", end="2026-11-01")
        assert payload == {"ResultsByTime": []}

    def test_a_dry_run_lists_buckets_as_empty(self):
        clients = _clients(dry_run=True)
        assert list_buckets(clients) == []

    def test_the_dry_run_report_lists_the_planned_calls(self):
        clients = _clients(dry_run=True)
        get_cost_and_usage(clients, start="2026-05-01", end="2026-11-01")
        report = dry_run_report(clients)
        assert "GetCostAndUsage" in report
        assert "dry run" in report

    def test_the_dry_run_report_says_so_when_nothing_was_planned(self):
        assert "No AWS calls" in dry_run_report(_clients())


class TestErrors:
    def test_a_failing_call_raises_the_project_error(self):
        clients = _clients(cost_explorer=_StubCe(error=RuntimeError("boom")))
        with pytest.raises(AwsClientError, match="GetCostAndUsage failed"):
            get_cost_and_usage(clients, start="2026-05-01", end="2026-11-01")

    def test_a_missing_client_raises_rather_than_returning_empty(self):
        clients = ClientBundle(region="ap-southeast-1")
        with pytest.raises(AwsClientError, match="no Cost Explorer client"):
            get_cost_and_usage(clients, start="2026-05-01", end="2026-11-01")

    def test_a_missing_s3_client_raises(self):
        clients = ClientBundle(region="ap-southeast-1")
        with pytest.raises(AwsClientError, match="no S3 client"):
            list_buckets(clients)


class TestLifecycle:
    def test_a_lifecycle_config_is_returned(self):
        clients = _clients()
        assert get_bucket_lifecycle(clients, "bucket-a") == {"Rules": [{"ID": "r1"}]}

    def test_a_missing_lifecycle_is_none_not_an_error(self):
        # "Forgot the rule" is itself a finding, so this must not raise.
        clients = _clients(s3=_StubS3(error=_NoSuchLifecycle()))
        assert get_bucket_lifecycle(clients, "bucket-a") is None

    def test_a_missing_lifecycle_is_checked_by_code_not_by_message(self):
        class Weird(Exception):
            def __init__(self):
                self.response = {"Error": {"Code": "NoSuchLifecycleConfiguration"}}

        clients = _clients(s3=_StubS3(error=Weird()))
        assert get_bucket_lifecycle(clients, "bucket-a") is None

    def test_another_error_still_raises(self):
        clients = _clients(s3=_StubS3(error=RuntimeError("access denied")))
        with pytest.raises(AwsClientError, match="GetBucketLifecycleConfiguration failed"):
            get_bucket_lifecycle(clients, "bucket-a")


class TestS3Reads:
    def test_buckets_are_listed(self):
        assert list_buckets(_clients()) == ["bucket-a", "bucket-b"]

    def test_logging_is_read(self):
        clients = _clients()
        assert get_bucket_logging(clients, "bucket-a")["LoggingEnabled"]["TargetBucket"] == "logs"

    def test_objects_are_listed(self):
        clients = _clients()
        payload = list_objects(clients, "bucket-a", prefix="data/")
        assert payload["Contents"][0]["Key"] == "a.csv"
        assert clients.s3.calls[0]["Prefix"] == "data/"

    def test_bucket_tags_are_read(self):
        assert get_bucket_tagging_safe(_clients()) == {"team": "data"}


def get_bucket_tagging_safe(clients):
    from aws_cost_analyzer.aws_client import get_bucket_tagging

    return get_bucket_tagging(clients, "bucket-a")


class TestCloudWatch:
    def test_the_statistics_are_returned(self):
        clients = _clients()
        points = get_metric_statistics(
            clients,
            namespace="AWS/S3",
            metric_name="BucketSizeBytes",
            dimensions=[{"Name": "BucketName", "Value": "bucket-a"}],
            start=__import__("datetime").date(2026, 9, 1),
            end=__import__("datetime").date(2026, 11, 1),
        )
        assert points[0]["Sum"] == 5.0

    def test_the_dimensions_are_passed_through(self):
        clients = _clients()
        get_metric_statistics(
            clients,
            namespace="AWS/S3",
            metric_name="BucketSizeBytes",
            dimensions=[{"Name": "BucketName", "Value": "bucket-a"}],
            start=__import__("datetime").date(2026, 9, 1),
            end=__import__("datetime").date(2026, 11, 1),
        )
        assert clients.cloudwatch.calls[0]["Dimensions"] == [
            {"Name": "BucketName", "Value": "bucket-a"}
        ]


class TestReadOnly:
    def test_no_mutating_action_is_allowed(self):
        # The tool is read-only by construction: there is no code path
        # that can delete a bucket or write a lifecycle rule.
        for forbidden in (
            "DeleteBucket",
            "DeleteObject",
            "PutBucketLifecycleConfiguration",
            "PutObject",
            "DeleteBucketLifecycle",
        ):
            assert forbidden not in ALLOWED_ACTIONS

    def test_every_allowed_action_is_a_read(self):
        for action in ALLOWED_ACTIONS:
            assert action.startswith(("Get", "List", "Describe"))


class TestDimensionValues:
    def test_the_dimension_is_passed_through(self):
        clients = _clients()
        get_dimension_values(
            clients, dimension="TAG", start="2026-05-01", end="2026-11-01"
        )
        assert clients.cost_explorer.calls[0]["Dimension"] == "TAG"

    def test_the_tags_call_works(self):
        clients = _clients()
        assert get_tags(clients) is not None
