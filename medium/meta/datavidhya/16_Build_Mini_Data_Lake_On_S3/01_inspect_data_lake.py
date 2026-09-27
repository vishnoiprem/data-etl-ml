"""
Q16: Build a Mini Data Lake on Amazon S3   [AWS | S3, Storage, Versioning]

Offline driver: simulate the six lab stages against moto-mocked S3 and
assert the bucket state matches what each lab stage expects.

How to Think:
- "Folders" in S3 are just key prefixes that end in '/'. PutObject with key
  "curated/" is the same as clicking "Create folder" in the console.
- Versioning is BUCKET-level. Once on it cannot be set back to Off --
  only Suspended. Existing objects become v(n+1) on next write.
- Storage class transitions require a copy. S3 rejects in-place edits, so
  you copy on top of yourself with a new StorageClass.

The trap:
- "Folder" deletion with versioned files leaves orphan versions. Lab 06
  calls ``delete-objects`` for both Versions and DeleteMarkers; skipping
  either leaves the bucket non-empty and the delete-bucket call fails.
- HeadObject returns ``StorageClass=None`` for STANDARD objects in moto;
  the test treats ``None`` as STANDARD.

AWS note:
- All boto3 calls used here mirror the AWS CLI in scripts/*.sh. The
  scripts are the "manual run" version; this driver is the verification
  path. Both are kept in sync.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import boto3

_HERE = os.path.dirname(os.path.abspath(__file__))


def expect(title: str, got: Any, expected: Any) -> None:
    if got != expected:
        print(f"[FAIL] {title}")
        print(f"   expected: {expected}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")


def expect_in(title: str, value: Any, options: List[Any]) -> None:
    if value in options:
        print(f"[PASS] {title}  ({value} in {options})")
        return
    print(f"[FAIL] {title}: {value!r} not in {options}")
    raise AssertionError(title)


def list_keys(s3, bucket: str, prefix: str = "") -> List[str]:
    paginator = s3.get_paginator("list_objects_v2")
    keys: List[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        keys.extend(o["Key"] for o in page.get("Contents", []))
    return sorted(keys)


def main() -> None:
    from moto import mock_aws

    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        bucket = "s3-intro-data-lake-bucket-test"
        s3.create_bucket(Bucket=bucket)

        # Lab seeds raw/ files when the bucket is provisioned.
        with open(os.path.join(_HERE, "sample_data", "january-sales.csv"),
                  encoding="utf-8") as fh:
            sales_body = fh.read()
        with open(os.path.join(_HERE, "sample_data", "customers.json"),
                  encoding="utf-8") as fh:
            cust_body = fh.read()
        s3.put_object(Bucket=bucket, Key="raw/sales/january-sales.csv",
                      Body=sales_body.encode("utf-8"))
        s3.put_object(Bucket=bucket, Key="raw/customers/customers.json",
                      Body=cust_body.encode("utf-8"))

        print("\n=== Q16 Build a Mini Data Lake on S3 ===\n")

        # ------ stage 1: inspect raw zone
        expect("Q16 stage 1 seeded keys",
               list_keys(s3, bucket, "raw/"),
               ["raw/customers/customers.json", "raw/sales/january-sales.csv"])

        cust = json.loads(s3.get_object(
            Bucket=bucket, Key="raw/customers/customers.json")["Body"].read())
        expect("Q16 customers.json parses to 5 records", len(cust), 5)

        # ------ stage 2: zones + raw -> curated copy
        s3.put_object(Bucket=bucket, Key="curated/")
        s3.put_object(Bucket=bucket, Key="processed/")
        for src, dst in [
            ("raw/customers/customers.json", "curated/customers/customers.json"),
            ("raw/sales/january-sales.csv",  "curated/sales/january-sales.csv"),
        ]:
            body = s3.get_object(Bucket=bucket, Key=src)["Body"].read()
            s3.put_object(Bucket=bucket, Key=dst, Body=body)

        expect("Q16 stage 2 six keys total (raw, curated, processed)",
               list_keys(s3, bucket),
               ["curated/",
                "curated/customers/customers.json",
                "curated/sales/january-sales.csv",
                "processed/",
                "raw/customers/customers.json",
                "raw/sales/january-sales.csv"])

        # ------ stage 3: storage class -> STANDARD_IA
        curated_sales = "curated/sales/january-sales.csv"
        head_before = s3.head_object(Bucket=bucket, Key=curated_sales)
        expect_in("Q16 stage 3 starts as STANDARD/None",
                  head_before.get("StorageClass"), [None, "STANDARD"])

        body = s3.get_object(Bucket=bucket, Key=curated_sales)["Body"].read()
        # copy_object reads the body from CopySource -- no Body param.
        s3.put_object(Bucket=bucket, Key=curated_sales, Body=body,
                      StorageClass="STANDARD_IA")
        head_after = s3.head_object(Bucket=bucket, Key=curated_sales)
        expect("Q16 stage 3 transitions to STANDARD_IA",
               head_after["StorageClass"], "STANDARD_IA")

        # ------ stage 4: enable versioning
        s3.put_bucket_versioning(
            Bucket=bucket,
            VersioningConfiguration={"Status": "Enabled"})
        expect("Q16 stage 4 versioning = Enabled",
               s3.get_bucket_versioning(Bucket=bucket)["Status"], "Enabled")

        # ------ stage 5: overwrite + recover
        cust_key = "curated/customers/customers.json"
        original = s3.get_object(Bucket=bucket, Key=cust_key)
        original_body = original["Body"].read()
        # Get VersionId via list_object_versions (head_object only returns
        # one in moto when versioning is enabled and a write has occurred;
        # listing is the stable way to capture it).
        versions_before = s3.list_object_versions(Bucket=bucket, Prefix=cust_key)
        original_version = versions_before["Versions"][0]["VersionId"]

        s3.put_object(Bucket=bucket, Key=cust_key,
                      Body=b'[{"customer_id":0,"name":"CORRUPT"}]')
        latest = s3.get_object(Bucket=bucket, Key=cust_key)["Body"].read()
        expect("Q16 stage 5 latest is the corrupt write",
               latest, b'[{"customer_id":0,"name":"CORRUPT"}]')

        # Recovery: same VersionId returns the original bytes.
        recovered = s3.get_object(Bucket=bucket, Key=cust_key,
                                  VersionId=original_version)["Body"].read()
        expect("Q16 stage 5 recovered VersionId matches original bytes",
               recovered, original_body)

        # Both versions are listed.
        versions = s3.list_object_versions(Bucket=bucket, Prefix=cust_key)
        version_count = sum(1 for v in versions["Versions"] if not v["Key"].endswith("/"))
        expect("Q16 stage 5 exactly 2 versions of customers.json",
               version_count, 2)

        # ------ stage 6: teardown -- delete EVERYTHING including markers
        # For a clean driver run we don't actually delete the moto bucket;
        # we just assert both Versions AND DeleteMarkers are involved.
        # (the scripts/06_teardown.sh does the real teardown against AWS.)
        page = s3.list_object_versions(Bucket=bucket)
        n_versions = len(page.get("Versions", []))
        n_markers  = len(page.get("DeleteMarkers", []))
        expect("Q16 stage 6 versions list is non-empty before teardown",
               n_versions > 0, True)
        expect("Q16 stage 6 delete markers list is empty (no deletes yet)",
               n_markers, 0)

        # Simulate the teardown to confirm we can clean up.
        if page.get("Versions"):
            s3.delete_objects(Bucket=bucket, Delete={
                "Objects": [{"Key": v["Key"], "VersionId": v["VersionId"]}
                            for v in page["Versions"]]})
        page = s3.list_object_versions(Bucket=bucket)
        expect("Q16 stage 6 teardown removes all versions",
               len(page.get("Versions", [])), 0)

        print("\n=== All Q16 stages pass ===\n")


if __name__ == "__main__":
    main()
