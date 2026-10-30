"""Tests for the IAM policy engine and the cost model."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from cost_model import (  # noqa: E402
    FREE_TIER,
    STORAGE_CLASS_PRICES,
    compare_architectures,
    estimate,
    format_comparison,
    monthly_runway,
)
from iam_policy import (  # noqa: E402
    PERMISSIONS,
    ROLES,
    Binding,
    Policy,
    Principal,
    ancestor_paths,
    blast_radius,
    effective_permissions,
    evaluate,
    explain_principal,
    find_over_privileged,
    role_permissions,
)

PROJECT = "projects/p"
BUCKET = "projects/p/buckets/b"


class TestAncestry:
    def test_paths_are_most_specific_first(self):
        paths = ancestor_paths("projects/p/buckets/b/objects/o")
        assert paths[0] == "projects/p/buckets/b/objects/o"
        assert paths[-1] == "projects/p"

    def test_single_resource(self):
        assert ancestor_paths("projects/p") == ["projects/p"]


class TestEvaluation:
    def test_grant_at_project_applies_to_bucket(self):
        policy = Policy()
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.admin"), PROJECT)
        result = evaluate(policy, "a@example.com", "storage.objects.get", resource=BUCKET)
        assert result.allowed
        assert result.inherited

    def test_no_grant_means_denied(self):
        policy = Policy()
        result = evaluate(policy, "a@example.com", "storage.objects.get", resource=BUCKET)
        assert not result.allowed

    def test_deny_overrides_allow(self):
        policy = Policy()
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.admin"), PROJECT)
        policy.deny(Principal("user", "a@example.com"), "roles/storage.admin", BUCKET)
        result = evaluate(policy, "a@example.com", "storage.objects.get", resource=BUCKET)
        assert not result.allowed
        assert result.denied_roles

    def test_deny_is_scoped_to_its_resource(self):
        policy = Policy()
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.admin"), PROJECT)
        policy.deny(Principal("user", "a@example.com"), "roles/storage.admin", BUCKET)
        other = "projects/p/buckets/other"
        result = evaluate(policy, "a@example.com", "storage.objects.get", resource=other)
        assert result.allowed

    def test_exact_grant_is_not_inherited(self):
        policy = Policy()
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.admin"), BUCKET)
        result = evaluate(policy, "a@example.com", "storage.objects.get", resource=BUCKET)
        assert result.allowed
        assert not result.inherited

    def test_service_account_principal(self):
        policy = Policy()
        sa = Principal("serviceAccount", "sa@p.iam.gserviceaccount.com")
        policy.add(sa, Binding("roles/pubsub.publisher"), PROJECT)
        result = evaluate(policy, "sa@p.iam.gserviceaccount.com", "pubsub.topics.publish")
        assert result.allowed

    def test_domain_principal_matches_members(self):
        policy = Policy()
        policy.add(Principal("domain", "example.com"), Binding("roles/viewer"), PROJECT)
        result = evaluate(policy, "anyone@example.com", "storage.buckets.get")
        assert result.allowed

    def test_domain_principal_does_not_match_others(self):
        policy = Policy()
        policy.add(Principal("domain", "example.com"), Binding("roles/viewer"), PROJECT)
        result = evaluate(policy, "anyone@other.com", "storage.buckets.get")
        assert not result.allowed

    def test_condition_must_match(self):
        policy = Policy()
        policy.add(
            Principal("user", "a@example.com"),
            Binding("roles/storage.admin", condition="env == prod"),
            PROJECT,
        )
        assert not evaluate(policy, "a@example.com", "storage.objects.get").allowed
        assert evaluate(
            policy, "a@example.com", "storage.objects.get", attributes={"env": "prod"}
        ).allowed

    def test_condition_fails_closed_without_attributes(self):
        policy = Policy()
        policy.add(
            Principal("user", "a@example.com"),
            Binding("roles/storage.admin", condition="env == prod"),
            PROJECT,
        )
        assert not evaluate(policy, "a@example.com", "storage.objects.get").allowed


class TestRoleSemantics:
    def test_object_viewer_cannot_write(self):
        permissions = role_permissions("roles/storage.objectViewer")
        assert "storage.objects.get" in permissions
        assert "storage.objects.create" not in permissions

    def test_object_creator_cannot_read(self):
        permissions = role_permissions("roles/storage.objectCreator")
        assert "storage.objects.create" in permissions
        assert "storage.objects.get" not in permissions

    def test_data_viewer_cannot_create_tables(self):
        permissions = role_permissions("roles/bigquery.dataViewer")
        assert "bigquery.tables.getData" in permissions
        assert "bigquery.tables.create" not in permissions

    def test_viewer_is_read_only(self):
        permissions = role_permissions("roles/viewer")
        assert "storage.buckets.get" in permissions
        assert "storage.buckets.create" not in permissions
        assert "storage.buckets.delete" not in permissions

    def test_owner_has_everything(self):
        owner = role_permissions("roles/owner")
        assert owner == frozenset(PERMISSIONS)

    def test_editor_cannot_set_project_iam(self):
        permissions = role_permissions("roles/editor")
        assert "resourcemanager.projects.setIamPolicy" not in permissions

    def test_unknown_role_raises(self):
        with pytest.raises(KeyError):
            role_permissions("roles/does.not.exist")


class TestEffectivePermissions:
    def test_aggregates_across_bindings(self):
        policy = Policy()
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.objectViewer"))
        policy.add(Principal("user", "a@example.com"), Binding("roles/bigquery.dataViewer"))
        permissions = effective_permissions(policy, "a@example.com")
        assert "storage.objects.get" in permissions
        assert "bigquery.tables.getData" in permissions


class TestExplain:
    def test_reports_inherited_grants(self):
        policy = Policy()
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.admin"), PROJECT)
        lines = explain_principal(policy, "a@example.com", resource=BUCKET)
        assert any("inherited" in line for line in lines)

    def test_reports_exact_grants(self):
        policy = Policy()
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.admin"), BUCKET)
        lines = explain_principal(policy, "a@example.com", resource=BUCKET)
        assert any("exact" in line for line in lines)


class TestBlastRadius:
    def test_reports_reachable_resources(self):
        policy = Policy()
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.admin"), PROJECT)
        result = blast_radius(policy, "a@example.com", [BUCKET, "projects/other/buckets/x"])
        assert result[BUCKET] is True
        assert result["projects/other/buckets/x"] is False


class TestOverPrivilege:
    def test_redundant_role_detected(self):
        policy = Policy()
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.admin"))
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.objectViewer"))
        redundant = find_over_privileged(policy, "a@example.com")
        assert "roles/storage.objectViewer" in redundant

    def test_single_role_is_never_redundant(self):
        policy = Policy()
        policy.add(Principal("user", "a@example.com"), Binding("roles/storage.admin"))
        assert find_over_privileged(policy, "a@example.com") == []


class TestCostModel:
    def test_storage_scales_with_gb(self):
        small = estimate("cloud-storage", storage_gb=10).total
        large = estimate("cloud-storage", storage_gb=1000).total
        assert large > small

    def test_archive_is_cheapest_to_store(self):
        standard = estimate("cloud-storage", storage_gb=100, storage_class="standard").total
        archive = estimate("cloud-storage", storage_gb=100, storage_class="archive").total
        assert archive < standard

    def test_archive_is_most_expensive_to_read(self):
        standard = estimate(
            "cloud-storage", storage_gb=0, retrieval_gb=100, storage_class="standard"
        ).total
        archive = estimate(
            "cloud-storage", storage_gb=0, retrieval_gb=100, storage_class="archive"
        ).total
        assert archive > standard

    def test_bigquery_scan_is_linear(self):
        one = estimate("bigquery", scanned_tb=1, apply_free_tier=False).total
        ten = estimate("bigquery", scanned_tb=10, apply_free_tier=False).total
        assert abs(ten - one * 10) < 0.001

    def test_free_tier_reduces_cost(self):
        with_free = estimate("bigquery", scanned_tb=0.5).total
        without = estimate("bigquery", scanned_tb=0.5, apply_free_tier=False).total
        assert with_free < without

    def test_dataflow_costs_by_vcpu_hour(self):
        short = estimate("dataflow", vcpu_hours=1, apply_free_tier=False).total
        long = estimate("dataflow", vcpu_hours=24, apply_free_tier=False).total
        assert abs(long - short * 24) < 0.001

    def test_unknown_service_raises(self):
        with pytest.raises(KeyError):
            estimate("not-a-service")

    def test_monthly_runway(self):
        cost = monthly_runway("dataflow")
        assert cost > 0


class TestArchitectureComparison:
    def test_partitioned_is_cheaper_than_unpartitioned(self):
        options = dict(compare_architectures(scanned_tb=1.0))
        assert (
            options["Batch on BigQuery (partitioned)"]
            < options["Batch on BigQuery (unpartitioned)"]
        )

    def test_options_sorted_cheapest_first(self):
        options = compare_architectures(scanned_tb=1.0)
        costs = [cost for _, cost in options]
        assert costs == sorted(costs)

    def test_formatting(self):
        table = format_comparison(compare_architectures(scanned_tb=1.0))
        assert table.startswith("| Architecture |")
