"""
test_region_az_demo.py — pytest suite for region_az_demo.py.

> Author: Prem Vishnoi <pvishnoi@avilx.com>
> Section: 02 (EC2 Fundamentals)
> Companion lecture: L06, L08

We use ``@mock_aws`` from ``moto >= 5.0`` to stand up an in-memory
EC2 client. The tests cover the three pieces of behaviour the
lecture actually teaches:

1. ``describe_regions()`` returns a non-trivial number of regions
   (moto seeds 10+ by default; the assertion is ``>= 10`` to match
   the syllabus).
2. ``describe_availability_zones()`` returns AZs in the mocked
   region and exposes the AZ name + AZ ID pair.
3. The ``build_az_name_to_id_map`` helper is a correct dict
   comprehension over the response.

We also cover ``main()``'s graceful-bail behaviour with no AWS
credentials configured, so the demo does not hard-fail on a fresh
laptop.
"""

from __future__ import annotations

import os
import sys
from unittest import mock

import boto3
import pytest
from moto import mock_aws

# Make the demo importable regardless of how pytest is invoked. We
# add the directory of this test file to sys.path so we can do
# ``import region_az_demo`` without packaging concerns.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import region_az_demo  # noqa: E402  (import after sys.path tweak)


# ---------------------------------------------------------------------------
# Pure unit tests — no AWS calls, no moto.
# ---------------------------------------------------------------------------

class TestBuildAzNameToIdMap:
    def test_empty_input_returns_empty_dict(self):
        assert region_az_demo.build_az_name_to_id_map([]) == {}

    def test_single_row(self):
        rows = [{"name": "us-east-1a", "zone_id": "use1-az1"}]
        assert region_az_demo.build_az_name_to_id_map(rows) == {
            "us-east-1a": "use1-az1"
        }

    def test_multiple_rows(self):
        rows = [
            {"name": "us-east-1a", "zone_id": "use1-az1"},
            {"name": "us-east-1b", "zone_id": "use1-az2"},
            {"name": "us-east-1c", "zone_id": "use1-az3"},
        ]
        result = region_az_demo.build_az_name_to_id_map(rows)
        assert result == {
            "us-east-1a": "use1-az1",
            "us-east-1b": "use1-az2",
            "us-east-1c": "use1-az3",
        }
        # Verify the keys are exactly the AZ names.
        assert set(result.keys()) == {"us-east-1a", "us-east-1b", "us-east-1c"}

    def test_lookup_is_constant_time(self):
        # A trivial sanity check that we are returning a dict (O(1)
        # lookups) rather than a list of pairs (O(n)).
        rows = [{"name": f"us-east-1{x}", "zone_id": f"use1-az{x}"} for x in "abcd"]
        result = region_az_demo.build_az_name_to_id_map(rows)
        assert isinstance(result, dict)
        assert result["us-east-1c"] == "use1-azc"


class TestPickDefaultRegion:
    def test_uses_aws_region_env(self, monkeypatch):
        monkeypatch.setenv("AWS_REGION", "eu-west-1")
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        assert region_az_demo.pick_default_region() == "eu-west-1"

    def test_falls_back_to_aws_default_region(self, monkeypatch):
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-2")
        assert region_az_demo.pick_default_region() == "ap-southeast-2"

    def test_falls_back_to_us_east_1(self, monkeypatch):
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        assert region_az_demo.pick_default_region() == "us-east-1"

    def test_aws_region_wins_over_aws_default_region(self, monkeypatch):
        monkeypatch.setenv("AWS_REGION", "us-west-2")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")
        assert region_az_demo.pick_default_region() == "us-west-2"


class TestRenderHelpers:
    def test_render_regions_table_handles_empty(self):
        out = region_az_demo.render_regions_table([])
        assert "no enabled regions" in out

    def test_render_azs_table_handles_empty(self):
        out = region_az_demo.render_azs_table([])
        assert "no availability zones" in out

    def test_render_regions_table_contains_every_region(self):
        regions = [
            {"region": "us-east-1", "endpoint": "ec2.us-east-1.amazonaws.com"},
            {"region": "eu-west-1", "endpoint": "ec2.eu-west-1.amazonaws.com"},
        ]
        out = region_az_demo.render_regions_table(regions)
        assert "us-east-1" in out
        assert "eu-west-1" in out
        assert "ec2.us-east-1.amazonaws.com" in out
        assert "ec2.eu-west-1.amazonaws.com" in out


# ---------------------------------------------------------------------------
# Mocked-AWS tests — uses moto's @mock_aws decorator.
# ---------------------------------------------------------------------------

@mock_aws
def test_describe_regions_returns_at_least_ten_regions():
    """Moto seeds the global region list; we just need >=10."""
    client = boto3.client("ec2", region_name="us-east-1")
    regions = region_az_demo.list_regions(client)
    assert len(regions) >= 10
    # Every row has the two keys we promise.
    for r in regions:
        assert set(r.keys()) == {"region", "endpoint"}
        assert r["region"]  # non-empty string
        assert r["endpoint"]  # non-empty string


@mock_aws
def test_describe_availability_zones_returns_azs_in_mocked_region():
    """Moto returns several AZs for us-east-1; we should see them all."""
    client = boto3.client("ec2", region_name="us-east-1")
    azs = region_az_demo.list_availability_zones(client)
    assert len(azs) >= 1
    # Every row has the two keys we promise, and the AZ ID is
    # account-specific (the L06 lecture point).
    for az in azs:
        assert set(az.keys()) == {"name", "zone_id"}
        # AZ name matches the ``<region><letter>`` pattern, e.g.
        # ``us-east-1a``.
        assert az["name"].startswith("us-east-1")
        # AZ ID matches the ``<region-short>az<n>`` pattern, e.g.
        # ``use1-az1``.
        assert az["zone_id"].startswith("use1-az")


@mock_aws
def test_full_pipeline_list_then_map():
    """End-to-end: list AZs, then build the name->id mapping."""
    client = boto3.client("ec2", region_name="us-east-1")
    azs = region_az_demo.list_availability_zones(client)
    mapping = region_az_demo.build_az_name_to_id_map(azs)

    # The mapping must cover every AZ we just listed.
    assert set(mapping.keys()) == {az["name"] for az in azs}
    # And every value must be the matching AZ ID.
    for az in azs:
        assert mapping[az["name"]] == az["zone_id"]


# ---------------------------------------------------------------------------
# main() — graceful-bail behaviour when no credentials are configured.
# ---------------------------------------------------------------------------

class TestMainGracefulBail:
    def test_main_returns_zero_when_no_credentials(self, monkeypatch, capsys):
        """No AWS creds -> friendly message, exit code 0, no stack trace."""
        # Strip any credentials the host might have so
        # ``_has_credentials`` returns False.
        for var in (
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
            "AWS_PROFILE",
        ):
            monkeypatch.delenv(var, raising=False)
        # Stub out ``_has_credentials`` directly — this avoids any
        # subtle behaviour from the real default session.
        with mock.patch.object(
            region_az_demo, "_has_credentials", return_value=False
        ):
            exit_code = region_az_demo.main([])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "no AWS credentials" in captured.out
        # We should NOT have printed a traceback.
        assert "Traceback" not in captured.out
        assert "Traceback" not in captured.err

    def test_main_handles_no_credentials_via_env(self, monkeypatch, capsys):
        """With env vars set but no actual AWS access, main still exits 0.

        We mock ``boto3.client`` to raise ``NoCredentialsError`` so we
        exercise the ``except (NoCredentialsError, ...)`` branch in
        ``main``. This is the path that fires when ``boto3.client`` is
        called without credentials even if env vars look plausible.
        """
        for var in (
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
        ):
            monkeypatch.delenv(var, raising=False)
        with mock.patch.object(
            region_az_demo, "_has_credentials", return_value=True
        ), mock.patch.object(
            region_az_demo.boto3,
            "client",
            side_effect=region_az_demo.NoCredentialsError(),
        ):
            exit_code = region_az_demo.main([])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "credentials" in captured.out.lower()
