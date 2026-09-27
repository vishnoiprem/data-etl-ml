"""Offline pytest for the Glue-crawler lab.

Mirrors the 7 lab stages against a moto-mocked Glue + S3 backend so the
suite runs with zero AWS credentials.
"""
from __future__ import annotations

import csv
import io
import json
import os

from catalog import Catalog, _infer_type
from conftest import _cols


# ============================================================== stage 1
def test_stage1_s3_objects_are_uploaded(catalog: Catalog) -> None:
    """Stage 1: S3 bucket has the seed orders CSV + customers JSON."""
    keys = sorted(o["Key"] for o in
                  catalog.s3.list_objects_v2(Bucket=catalog.bucket)["Contents"])
    assert keys == ["raw/customers/customers.json", "raw/orders/orders.csv"]


# ============================================================== stage 2
def test_stage2_crawler_registered_with_two_targets(catalog: Catalog) -> None:
    """Stage 2: crawler configured against both prefixes + the lab role + DB."""
    crawler = catalog.glue.get_crawler(Name="c")["Crawler"]
    paths = sorted(t["Path"] for t in crawler["Targets"]["S3Targets"])
    assert paths == sorted([f"s3://{catalog.bucket}/raw/orders/",
                             f"s3://{catalog.bucket}/raw/customers/"])
    assert crawler["DatabaseName"] == catalog.database
    assert crawler["Role"] == catalog.role_arn


# ============================================================== stage 3
def test_stage3_crawler_registered_one_table_per_prefix(catalog: Catalog) -> None:
    """Stage 3: crawl produces one table per folder of homogeneous files."""
    assert catalog.list_tables() == ["customers", "orders"]
    assert catalog.get_location("orders") == f"s3://{catalog.bucket}/raw/orders/"
    assert catalog.get_location("customers") == f"s3://{catalog.bucket}/raw/customers/"


# ============================================================== stage 4
def test_stage4_clean_columns_inferred_as_narrow_types(catalog: Catalog) -> None:
    """Stage 4: order_id, amount, currency come out bigint/double/string."""
    cols = _cols(catalog, "orders")
    assert cols["order_id"]    == "bigint"
    assert cols["amount"]      == "double"
    assert cols["currency"]    == "string"


def test_stage4_trap_order_date_inferred_as_string(catalog: Catalog) -> None:
    """The single N/A row poisons the order_date column -- crawler falls
    back to ``string`` instead of ``date``."""
    cols = _cols(catalog, "orders")
    assert cols["order_date"] == "string", cols


def test_stage4_customers_signup_date_inferred_as_date(catalog: Catalog) -> None:
    """The customers JSON has clean dates -- crawler picks ``date``."""
    cols = _cols(catalog, "customers")
    assert cols["signup_date"] == "date"


def test_stage4_inference_helpers_handle_mixed_types() -> None:
    """The _infer_type helper implements Glue's "broadest type wins" rule."""
    assert _infer_type(["1", "2", "3"]) == "bigint"
    assert _infer_type(["1.0", "2.5"]) == "double"
    assert _infer_type(["2026-09-20", "2026-09-21"]) == "date"
    assert _infer_type(["N/A", "2026-09-20"]) == "string"
    assert _infer_type([]) == "string"


# ============================================================== stage 5
def test_stage5_update_column_type_does_not_touch_data(catalog: Catalog) -> None:
    """Stage 5: ``update_column_type`` rewrites Glue but the S3 file is
    still 'N/A'-bearing."""
    catalog.update_column_type("orders", "order_date", "date")
    assert _cols(catalog, "orders")["order_date"] == "date"

    body = catalog.s3.get_object(Bucket=catalog.bucket,
                                  Key="raw/orders/orders.csv")["Body"].read().decode()
    assert "N/A" in body


# ============================================================== stage 6
def test_stage6_join_two_tables_by_customer_id(catalog: Catalog) -> None:
    """Stage 6: Athena-style SELECT-JOIN aggregates orders per customer."""
    orders_body = catalog.s3.get_object(
        Bucket=catalog.bucket, Key="raw/orders/orders.csv")["Body"].read().decode()
    orders = list(csv.DictReader(io.StringIO(orders_body)))

    cust_body = catalog.s3.get_object(
        Bucket=catalog.bucket,
        Key="raw/customers/customers.json")["Body"].read().decode()
    customers = json.loads(cust_body)

    by_id = {c["customer_id"]: c for c in customers}

    per_customer: dict = {}
    for o in orders:
        cid = int(o["customer_id"])
        if cid in by_id:
            per_customer.setdefault(by_id[cid]["name"], 0.0)
            per_customer[by_id[cid]["name"]] += float(o["amount"])

    # 12 orders joined cleanly against 7 customers (no orphans).
    joined_rows = [o for o in orders if int(o["customer_id"]) in by_id]
    assert len(joined_rows) == 12
    # Alice Johnson (id=42) appears in rows 1001, 1006, 1012.
    assert round(per_customer["Alice Johnson"], 2) == 354.75


# ============================================================== stage 7
def test_stage7_drop_table_leaves_s3_intact(catalog: Catalog) -> None:
    """Stage 7: DROP TABLE removes the catalog entry but S3 objects survive."""
    catalog.drop_table("orders")
    catalog.drop_table("customers")
    assert catalog.list_tables() == []

    keys_left = sorted(o["Key"] for o in
                       catalog.s3.list_objects_v2(Bucket=catalog.bucket)["Contents"])
    assert keys_left == ["raw/customers/customers.json",
                         "raw/orders/orders.csv"]
