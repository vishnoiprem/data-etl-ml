"""Shared fixtures for the AWS Cost Analyzer test suite.

Everything here is hermetic: no network, no AWS credentials, no live
account. The Cost Explorer responses are recorded fixtures, because
moto does not implement ``ce`` (it returns an empty ``ResultsByTime``)
and pretending otherwise would make the tests lie.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a recorded JSON fixture by file name."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def ce_service_payload() -> dict:
    """Six months of S3 spend, one service group."""
    return load_fixture("ce_s3_monthly_service.json")


@pytest.fixture
def ce_tag_payload() -> dict:
    """One month of S3 spend, split by tag value."""
    return load_fixture("ce_s3_monthly_tag.json")


@pytest.fixture
def ce_malformed_payload() -> dict:
    """A payload with a bad amount and a bad period."""
    return load_fixture("ce_malformed.json")


@pytest.fixture
def ce_with_resources_payload() -> dict:
    """Two months of S3 spend with a resource dimension."""
    return load_fixture("ce_with_resources.json")


@pytest.fixture
def ce_expected_filter() -> dict:
    """The filter payload the console view must translate into."""
    return load_fixture("ce_filter_expected.json")


@pytest.fixture
def ce_pages() -> list[dict]:
    """Three pages of a paginated response."""
    return [
        load_fixture("ce_paginated_page1.json"),
        load_fixture("ce_paginated_page2.json"),
        load_fixture("ce_paginated_page3.json"),
    ]
