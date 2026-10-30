"""Offline pytest for the S3 data lake lab -- no AWS credentials required.

Each test corresponds to one lab stage. The simulation runs against moto's
in-process S3 mock, so the assertions are byte-stable and fast.
"""
from __future__ import annotations

import io
import json
import os

import pytest
from botocore.exceptions import ClientError


# ============================================================== stage 1
def test_stage1_seeded_raw_files_are_visible(seeded_bucket, bucket_name) -> None:
    """Lab stage 1: inspect raw/ contents.

    The lab seeds sales/january-sales.csv and customers/customers.json under
    raw/. Both are immediately list-able.
    """
    resp = seeded_bucket.list_objects_v2(Bucket=bucket_name, Prefix="raw/")
    keys = sorted(o["Key"] for o in resp["Contents"])

    assert keys == ["raw/customers/customers.json",
                    "raw/sales/january-sales.csv"], keys

    # Both are readable as text.
    sales = seeded_bucket.get_object(Bucket=bucket_name,
                                     Key="raw/sales/january-sales.csv")["Body"]
    assert b"order_id,customer_id,amount" in sales.read()

    cust = seeded_bucket.get_object(Bucket=bucket_name,
                                   Key="raw/customers/customers.json")["Body"]
    parsed = json.loads(cust.read())
    assert len(parsed) == 5 and parsed[0]["customer_id"] == 17


# ============================================================== stage 2
def test_stage2_zones_created_and_files_copied(seeded_bucket, bucket_name) -> None:
    """Lab stage 2: create curated/ and processed/, copy raw -> curated/."""
    # Create the zone "folders" (S3 prefixes).
    seeded_bucket.put_object(Bucket=bucket_name, Key="curated/")
    seeded_bucket.put_object(Bucket=bucket_name, Key="processed/")

    # Copy raw into curated/.
    for src_key, dst_key in [
        ("raw/customers/customers.json", "curated/customers/customers.json"),
        ("raw/sales/january-sales.csv",  "curated/sales/january-sales.csv"),
    ]:
        body = seeded_bucket.get_object(Bucket=bucket_name, Key=src_key)["Body"]
        seeded_bucket.put_object(Bucket=bucket_name, Key=dst_key,
                                 Body=body.read())

    # The bucket should now contain all six keys.
    resp = seeded_bucket.list_objects_v2(Bucket=bucket_name)
    keys = sorted(o["Key"] for o in resp["Contents"])
    assert keys == [
        "curated/",
        "curated/customers/customers.json",
        "curated/sales/january-sales.csv",
        "processed/",
        "raw/customers/customers.json",
        "raw/sales/january-sales.csv",
    ], keys


# ============================================================== stage 3
def test_stage3_storage_class_transitions_to_ia(seeded_bucket, bucket_name) -> None:
    """Lab stage 3: move curated sales to STANDARD_IA."""
    key = "curated/sales/january-sales.csv"

    # Set up an object in the curated/ zone first.
    sales_path = os.path.join(os.path.dirname(__file__), "..", "sample_data",
                              "january-sales.csv")
    with open(sales_path, encoding="utf-8") as fh:
        seeded_bucket.put_object(Bucket=bucket_name, Key=key,
                                 Body=fh.read().encode("utf-8"))

    # Default storage class is STANDARD.
    head = seeded_bucket.head_object(Bucket=bucket_name, Key=key)
    # moto may omit StorageClass on default puts; treat absent as STANDARD.
    assert head.get("StorageClass", "STANDARD") in ("STANDARD", None), head.get("StorageClass")

    # Move to STANDARD_IA via re-PutObject (S3 rejects in-place StorageClass edits).
    body = seeded_bucket.get_object(Bucket=bucket_name, Key=key)["Body"].read()
    seeded_bucket.put_object(Bucket=bucket_name, Key=key,
                             Body=body, StorageClass="STANDARD_IA")

    head = seeded_bucket.head_object(Bucket=bucket_name, Key=key)
    assert head["StorageClass"] == "STANDARD_IA", head


# ============================================================== stage 4
def test_stage4_versioning_can_be_enabled(seeded_bucket, bucket_name) -> None:
    """Lab stage 4: enable versioning. Once enabled, stays enabled."""
    # Initial status: not configured.
    status = seeded_bucket.get_bucket_versioning(Bucket=bucket_name)
    assert status.get("Status") in (None, "Suspended"), status

    seeded_bucket.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Enabled"})

    enabled = seeded_bucket.get_bucket_versioning(Bucket=bucket_name)
    assert enabled["Status"] == "Enabled", enabled


def test_versioning_creates_history_on_overwrite(seeded_bucket, bucket_name) -> None:
    """Once versioning is enabled, overwrites create new VersionIds."""
    seeded_bucket.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Enabled"})

    key = "raw/customers/customers.json"
    versions_before = seeded_bucket.list_object_versions(
        Bucket=bucket_name, Prefix=key)
    v1_id = versions_before["Versions"][0]["VersionId"]

    # Overwrite with a small body.
    seeded_bucket.put_object(Bucket=bucket_name, Key=key,
                             Body=b'{"customer_id": 0, "name": "BAD"}',
                             ContentType="application/json")

    versions = seeded_bucket.list_object_versions(Bucket=bucket_name, Prefix=key)
    ids = sorted(v["VersionId"] for v in versions["Versions"])
    assert v1_id in ids and len(ids) == 2, ids


# ============================================================== stage 5
def test_stage5_overwrite_then_recover_original(seeded_bucket, bucket_name) -> None:
    """Lab stage 5: overwrite customers with bad data, recover the original.

    This is the lab's "save me from a botched put" exercise. With versioning
    on, both versions live; the original VersionId can be fetched back.
    """
    seeded_bucket.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Enabled"})

    key = "raw/customers/customers.json"
    versions_before = seeded_bucket.list_object_versions(
        Bucket=bucket_name, Prefix=key)
    original_version = versions_before["Versions"][0]["VersionId"]
    original_body = seeded_bucket.get_object(
        Bucket=bucket_name, Key=key)["Body"].read()

    # Overwrite with corrupt data.
    seeded_bucket.put_object(Bucket=bucket_name, Key=key,
                             Body=b'[{"customer_id":0,"name":"CORRUPT"}]')

    # The latest GET returns the bad data.
    latest = seeded_bucket.get_object(Bucket=bucket_name, Key=key)["Body"].read()
    assert b"CORRUPT" in latest

    # Recover the original via the version id.
    recovered = seeded_bucket.get_object(
        Bucket=bucket_name, Key=key, VersionId=original_version)["Body"].read()
    assert recovered == original_body, (recovered[:80], original_body[:80])


def test_recovering_wrong_version_returns_correct_bytes(seeded_bucket, bucket_name) -> None:
    """Sanity check: VersionId fetches return only that version, not latest."""
    seeded_bucket.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Enabled"})

    key = "raw/sales/january-sales.csv"
    first_body = seeded_bucket.get_object(Bucket=bucket_name, Key=key)["Body"].read()
    versions_before = seeded_bucket.list_object_versions(
        Bucket=bucket_name, Prefix=key)
    first_version = versions_before["Versions"][0]["VersionId"]

    seeded_bucket.put_object(Bucket=bucket_name, Key=key, Body=b"overwritten")
    latest = seeded_bucket.get_object(Bucket=bucket_name, Key=key)["Body"].read()
    assert latest == b"overwritten"

    historical = seeded_bucket.get_object(
        Bucket=bucket_name, Key=key, VersionId=first_version)["Body"].read()
    assert historical == first_body, historical


# ============================================================== stage 6
def test_stage6_delete_markers_hide_current_version(seeded_bucket, bucket_name) -> None:
    """Lab stage 6: deleting a versioned object adds a delete marker.

    The previous version is still recoverable by VersionId even though
    the live GET returns 404.
    """
    seeded_bucket.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Enabled"})

    key = "raw/customers/customers.json"
    versions_before = seeded_bucket.list_object_versions(
        Bucket=bucket_name, Prefix=key)
    original_version = versions_before["Versions"][0]["VersionId"]

    # Delete (creates a delete marker in a versioned bucket).
    seeded_bucket.delete_object(Bucket=bucket_name, Key=key)

    with pytest.raises(ClientError) as exc:
        seeded_bucket.get_object(Bucket=bucket_name, Key=key)
    assert exc.value.response["Error"]["Code"] in ("NoSuchKey", "404")

    # The previous version is still recoverable.
    body = seeded_bucket.get_object(
        Bucket=bucket_name, Key=key, VersionId=original_version)["Body"].read()
    assert b"Vishnoi Prem" in body, body[:120]
