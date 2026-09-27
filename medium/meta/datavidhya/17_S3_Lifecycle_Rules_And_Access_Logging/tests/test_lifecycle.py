"""Offline pytest for the S3 lifecycle + access logging lab."""
from __future__ import annotations

import json
import os

from botocore.exceptions import ClientError

from conftest import DATA_BUCKET, LOG_BUCKET


def _has_lifecycle(s3, bucket: str) -> bool:
    try:
        cfg = s3.get_bucket_lifecycle_configuration(Bucket=bucket)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
            return False
        raise
    return bool(cfg.get("Rules"))


# ============================================================== stage 1
def test_stage1_seeded_buckets_are_present(seeded_buckets) -> None:
    """Lab stage 1: data + log bucket exist; log bucket has its seed file."""
    listed = sorted(b["Name"] for b in seeded_buckets.list_buckets()["Buckets"])
    assert DATA_BUCKET in listed
    assert LOG_BUCKET in listed

    resp = seeded_buckets.list_objects_v2(Bucket=LOG_BUCKET)
    keys = sorted(o["Key"] for o in resp["Contents"])
    assert keys == ["example-access-log.txt"], keys

    # Pre-stage: data bucket has no lifecycle or logging configuration.
    assert not _has_lifecycle(seeded_buckets, DATA_BUCKET)
    log = seeded_buckets.get_bucket_logging(Bucket=DATA_BUCKET)
    assert "LoggingEnabled" not in log, log


# ============================================================== stage 2
def test_stage2_lifecycle_rule_attaches(seeded_buckets) -> None:
    """Lab stage 2: lifecycle rule attached to data bucket, round-trips."""
    lifecycle_path = os.path.join(os.path.dirname(__file__), "..",
                                  "sample_data", "lifecycle-rule.json")
    with open(lifecycle_path, encoding="utf-8") as fh:
        rule_doc = json.load(fh)

    seeded_buckets.put_bucket_lifecycle_configuration(
        Bucket=DATA_BUCKET, LifecycleConfiguration=rule_doc)

    got = seeded_buckets.get_bucket_lifecycle_configuration(Bucket=DATA_BUCKET)
    rule = got["Rules"][0]

    assert rule["ID"] == "AgeOutRawAndCurated"
    assert rule["Status"] == "Enabled"
    assert rule["Filter"]["Prefix"] == "raw/"
    assert rule["Transitions"][0]["Days"] == 30
    assert rule["Transitions"][0]["StorageClass"] == "STANDARD_IA"
    assert rule["Transitions"][1]["Days"] == 90
    assert rule["Transitions"][1]["StorageClass"] == "GLACIER_IR"
    assert rule["Expiration"]["Days"] == 365


def test_lifecycle_rule_handles_noncurrent_versions(seeded_buckets) -> None:
    """NoncurrentVersionTransitions + Expiration keep old versions cheap."""
    lifecycle_path = os.path.join(os.path.dirname(__file__), "..",
                                  "sample_data", "lifecycle-rule.json")
    with open(lifecycle_path, encoding="utf-8") as fh:
        rule_doc = json.load(fh)

    seeded_buckets.put_bucket_lifecycle_configuration(
        Bucket=DATA_BUCKET, LifecycleConfiguration=rule_doc)

    got = seeded_buckets.get_bucket_lifecycle_configuration(Bucket=DATA_BUCKET)
    rule = got["Rules"][0]

    assert rule["NoncurrentVersionTransitions"][0]["NoncurrentDays"] == 30
    assert rule["NoncurrentVersionTransitions"][0]["StorageClass"] == "GLACIER_IR"
    assert rule["NoncurrentVersionExpiration"]["NoncurrentDays"] == 365
    assert rule["AbortIncompleteMultipartUpload"]["DaysAfterInitiation"] == 7


# ============================================================== stage 3
def test_stage3_storage_transition_summary(seeded_buckets) -> None:
    """Lab stage 3: walk the rule and assert the storage-class timeline."""
    lifecycle_path = os.path.join(os.path.dirname(__file__), "..",
                                  "sample_data", "lifecycle-rule.json")
    with open(lifecycle_path, encoding="utf-8") as fh:
        rule_doc = json.load(fh)

    seeded_buckets.put_bucket_lifecycle_configuration(
        Bucket=DATA_BUCKET, LifecycleConfiguration=rule_doc)

    rule = seeded_buckets.get_bucket_lifecycle_configuration(
        Bucket=DATA_BUCKET)["Rules"][0]

    timeline = [(0, "STANDARD")] + [
        (t["Days"], t["StorageClass"]) for t in rule["Transitions"]
    ] + [(rule["Expiration"]["Days"], "DELETED")]

    assert timeline == [
        (0,   "STANDARD"),
        (30,  "STANDARD_IA"),
        (90,  "GLACIER_IR"),
        (365, "DELETED"),
    ], timeline


# ============================================================== stage 4
def test_stage4_access_logging_writes_to_log_bucket(seeded_buckets) -> None:
    """Lab stage 4: data bucket logs every request into the log bucket.

    moto doesn't actually generate log records on each request, but it does
    persist the logging configuration. We assert both:
      - the configuration is round-trippable,
      - the log bucket's existing seed log file is preserved.
    """
    seeded_buckets.put_bucket_logging(
        Bucket=DATA_BUCKET,
        BucketLoggingStatus={
            "LoggingEnabled": {"TargetBucket": LOG_BUCKET,
                               "TargetPrefix": "logs/"},
        },
    )

    got = seeded_buckets.get_bucket_logging(Bucket=DATA_BUCKET)
    assert got["LoggingEnabled"]["TargetBucket"] == LOG_BUCKET
    assert got["LoggingEnabled"]["TargetPrefix"] == "logs/"

    # Seed log file is still there.
    resp = seeded_buckets.list_objects_v2(Bucket=LOG_BUCKET)
    assert any(o["Key"] == "example-access-log.txt" for o in resp["Contents"])


def test_access_logging_disabling_clears_status(seeded_buckets) -> None:
    """Disabling logging (stage 6 prep) clears the LoggingEnabled block."""
    seeded_buckets.put_bucket_logging(
        Bucket=DATA_BUCKET,
        BucketLoggingStatus={"LoggingEnabled": {
            "TargetBucket": LOG_BUCKET, "TargetPrefix": "logs/",
        }},
    )
    seeded_buckets.put_bucket_logging(Bucket=DATA_BUCKET,
                                      BucketLoggingStatus={})
    assert "LoggingEnabled" not in seeded_buckets.get_bucket_logging(
        Bucket=DATA_BUCKET)


# ============================================================== stage 5
def test_stage5_access_log_record_is_parseable(seeded_buckets) -> None:
    """Lab stage 5: read the example log and parse at least one record.

    The S3 server access log format is space-delimited with quoted fields.
    See https://docs.aws.amazon.com/AmazonS3/latest/userguide/LogFormat.html
    """
    body = seeded_buckets.get_object(
        Bucket=LOG_BUCKET, Key="example-access-log.txt")["Body"].read()
    text = body.decode("utf-8")

    lines = [ln for ln in text.splitlines() if ln.strip()]
    assert len(lines) >= 3, f"expected at least 3 log records, got {len(lines)}"

    # First record fields, per the documented format:
    # bucket_owner  bucket  time  remote_ip  requester  request_id  operation  key  ...
    first = lines[0]
    assert first.startswith("79a59df900b949e55d96a1e698fbdedfd6e1d3b7afb66b61d96b66b61d96b66b1 "), \
        f"unexpected bucket owner prefix: {first[:80]!r}"
    # The seeded log mentions the example bucket name (different from this
    # test's DATA_BUCKET constant). Match on the prefix instead.
    assert "s3-lifecycle-data-bucket-" in first
    assert "REST.GET.OBJECT" in first
    assert "raw/sales/january-sales.csv" in first
    # Status code is one of the numeric fields near the middle.
    assert " 200 " in f" {first} ", "expected HTTP 200 in record"


def test_access_log_captures_access_denied(seeded_buckets) -> None:
    """The seeded log includes a 403 -- lab reads it to find who was denied."""
    body = seeded_buckets.get_object(
        Bucket=LOG_BUCKET, Key="example-access-log.txt")["Body"].read()
    text = body.decode("utf-8")
    assert "AccessDenied" in text
    assert " 403 " in f" {text} ", "expected a 403 response in the seeded log"
