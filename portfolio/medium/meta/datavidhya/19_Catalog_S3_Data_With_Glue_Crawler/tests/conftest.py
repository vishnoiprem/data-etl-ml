"""Pytest fixtures shared across the Glue-crawler tests."""
from __future__ import annotations

import os
import sys
from typing import Iterator

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from moto import mock_aws  # noqa: E402

from catalog import Catalog  # noqa: E402


@pytest.fixture
def catalog(monkeypatch: pytest.MonkeyPatch) -> Iterator[Catalog]:
    """Fresh catalog per test -- owns its S3 bucket + Glue DB."""
    cat = Catalog(
        bucket="glue-crawler-catalog-bucket-test",
        database="catalog_db_test",
        role_arn="arn:aws:iam::123456789012:role/GlueCrawlerLabRole-test",
    )
    with mock_aws():
        cat.setUp()
        cat.upload("raw/orders",
                    os.path.join(_ROOT, "sample_data", "orders",
                                 "orders.csv"))
        cat.upload("raw/customers",
                    os.path.join(_ROOT, "sample_data", "customers",
                                 "customers.json"))
        cat.create_crawler(
            "c",
            [f"s3://{cat.bucket}/raw/orders/",
             f"s3://{cat.bucket}/raw/customers/"],
        )
        cat.start_crawler("c")
        cat.infer_catalog_from_crawl("c")
        yield cat


def _cols(cat: Catalog, table: str) -> dict:
    return {c["Name"]: c["Type"] for c in cat.get_columns(table)}
