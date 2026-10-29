"""
Q17: S3 Lifecycle Rules and Access Logging   [AWS | S3, Cost, Auditing]

Offline driver: simulate the six lab stages against moto-mocked S3 and
assert the bucket state matches what each lab stage expects.

How to Think:
- A lifecycle rule is a "standing instruction" -- once attached, S3 walks
  every object under the prefix daily and applies the transitions /
  expiration. There is no manual refresh.
- Server access logging requires the LOG BUCKET to have a policy
  granting `logging.s3.amazonaws.com:PutObject`. Without it, the data
  bucket refuses to enable logging. The policy is the "permissions side"
  of the audit story; the data bucket's logging config is the
  "destination side".

The trap:
- Lifecycle rules don't move objects IMMEDIATELY after Days=N. S3 checks
  once per day, applies the rule, and may delay transitions by up to
  24h. The lab's "verify" check is therefore about the *configuration*
  being correct, not objects transitioning in real time.
- Disabling logging is NOT just deleting the lifecycle -- it's calling
  put-bucket-logging with an empty `LoggingEnabled` block. A common
  mistake is deleting just the lifecycle which leaves logging on.
- Access logs are delivered to the LOG bucket *asynchronously*. They
  may be missing for the first minute or two of lab session. Stage 5
  reads the SEEDED example log rather than waiting for fresh entries.

AWS note:
- Server access logs differ from CloudTrail data events: CloudTrail
  records API calls (control plane); access logs record requests
  (data plane). The lab covers data plane; CloudTrail is a separate
  service.
"""
from __future__ import annotations

import json
import os
import sys

import boto3
from botocore.exceptions import ClientError

_HERE = os.path.dirname(os.path.abspath(__file__))

DATA_BUCKET = "s3-lifecycle-data-bucket-test"
LOG_BUCKET  = "s3-lifecycle-logs-bucket-test"

LOG_BUCKET_POLICY = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "AllowS3LogDelivery",
        "Effect": "Allow",
        "Principal": {"Service": "logging.s3.amazonaws.com"},
        "Action": "s3:PutObject",
        "Resource": f"arn:aws:s3:::{LOG_BUCKET}/*",
        "Condition": {"StringEquals": {"aws:SourceAccount": "123456789012"}},
    }],
}


def expect(title: str, got, expected) -> None:
    if got != expected:
        print(f"[FAIL] {title}")
        print(f"   expected: {expected}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")


def _has_lifecycle(s3, bucket: str) -> bool:
    """True iff the bucket has a non-empty lifecycle configuration."""
    try:
        cfg = s3.get_bucket_lifecycle_configuration(Bucket=bucket)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
            return False
        raise
    return bool(cfg.get("Rules"))


def main() -> None:
    from moto import mock_aws

    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")

        # Stage 1 fixture: lab provisions two buckets + seeds the log bucket.
        s3.create_bucket(Bucket=DATA_BUCKET)
        s3.create_bucket(Bucket=LOG_BUCKET)
        s3.put_bucket_policy(Bucket=LOG_BUCKET,
                             Policy=json.dumps(LOG_BUCKET_POLICY))
        seed_path = os.path.join(_HERE, "sample_data", "example-access-log.txt")
        with open(seed_path, encoding="utf-8") as fh:
            s3.put_object(Bucket=LOG_BUCKET, Key="example-access-log.txt",
                          Body=fh.read().encode("utf-8"))

        print("\n=== Q17 S3 Lifecycle Rules and Access Logging ===\n")

        # ------ stage 1
        listed = sorted(b["Name"] for b in s3.list_buckets()["Buckets"])
        expect("Q17 stage 1 data + log buckets provisioned",
               listed, [DATA_BUCKET, LOG_BUCKET])

        seeded = sorted(o["Key"] for o in
                        s3.list_objects_v2(Bucket=LOG_BUCKET)["Contents"])
        expect("Q17 stage 1 log bucket has example-access-log.txt",
               seeded, ["example-access-log.txt"])

        expect("Q17 stage 1 data bucket has no lifecycle yet",
               _has_lifecycle(s3, DATA_BUCKET), False)
        expect("Q17 stage 1 data bucket has no logging yet",
               "LoggingEnabled" in s3.get_bucket_logging(Bucket=DATA_BUCKET),
               False)

        # ------ stage 2
        with open(os.path.join(_HERE, "sample_data", "lifecycle-rule.json"),
                  encoding="utf-8") as fh:
            rule_doc = json.load(fh)

        s3.put_bucket_lifecycle_configuration(
            Bucket=DATA_BUCKET, LifecycleConfiguration=rule_doc)

        rule = s3.get_bucket_lifecycle_configuration(
            Bucket=DATA_BUCKET)["Rules"][0]

        expect("Q17 stage 2 rule ID", rule["ID"], "AgeOutRawAndCurated")
        expect("Q17 stage 2 rule enabled", rule["Status"], "Enabled")
        expect("Q17 stage 2 prefix is raw/", rule["Filter"]["Prefix"], "raw/")
        expect("Q17 stage 2 first transition (30d -> STANDARD_IA)",
               rule["Transitions"][0],
               {"Days": 30, "StorageClass": "STANDARD_IA"})
        expect("Q17 stage 2 second transition (90d -> GLACIER_IR)",
               rule["Transitions"][1],
               {"Days": 90, "StorageClass": "GLACIER_IR"})
        expect("Q17 stage 2 expiration is 365 days",
               rule["Expiration"], {"Days": 365})

        # ------ stage 3
        timeline = [(0, "STANDARD")] + [
            (t["Days"], t["StorageClass"]) for t in rule["Transitions"]
        ] + [(rule["Expiration"]["Days"], "DELETED")]

        expect("Q17 stage 3 lifecycle timeline",
               timeline,
               [(0, "STANDARD"),
                (30, "STANDARD_IA"),
                (90, "GLACIER_IR"),
                (365, "DELETED")])

        # ------ stage 4
        s3.put_bucket_logging(
            Bucket=DATA_BUCKET,
            BucketLoggingStatus={"LoggingEnabled": {
                "TargetBucket": LOG_BUCKET, "TargetPrefix": "logs/",
            }},
        )
        log = s3.get_bucket_logging(Bucket=DATA_BUCKET)["LoggingEnabled"]
        expect("Q17 stage 4 logging target bucket", log["TargetBucket"], LOG_BUCKET)
        expect("Q17 stage 4 logging target prefix", log["TargetPrefix"], "logs/")

        # ------ stage 5
        body = s3.get_object(
            Bucket=LOG_BUCKET, Key="example-access-log.txt")["Body"].read()
        text = body.decode("utf-8")
        lines = [ln for ln in text.splitlines() if ln.strip()]

        expect("Q17 stage 5 access log has at least 3 records",
               len(lines) >= 3, True)
        expect("Q17 stage 5 first record is REST.GET.OBJECT 200",
               ("REST.GET.OBJECT" in lines[0]
                and " 200 " in f" {lines[0]} "
                and "raw/sales/january-sales.csv" in lines[0]),
               True)
        expect("Q17 stage 5 log contains a 403 AccessDenied",
               ("AccessDenied" in text and " 403 " in f" {text} "), True)

        # ------ stage 6
        s3.put_bucket_logging(Bucket=DATA_BUCKET, BucketLoggingStatus={})
        expect("Q17 stage 6 logging disabled",
               "LoggingEnabled" in s3.get_bucket_logging(Bucket=DATA_BUCKET),
               False)

        # Lifecycle rule stays even after logging is off (separate concern).
        still_there = s3.get_bucket_lifecycle_configuration(Bucket=DATA_BUCKET)
        expect("Q17 stage 6 lifecycle rule survives teardown of logging",
               still_there["Rules"][0]["ID"], "AgeOutRawAndCurated")

        print("\n=== All Q17 stages pass ===\n")


if __name__ == "__main__":
    main()
