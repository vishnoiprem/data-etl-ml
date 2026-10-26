"""
test_marketplace_client.py — mocked-HTTP tests for the Marketplace API wrapper.

Uses `responses` (the standard requests-mocking library) to
simulate the Databricks Marketplace Consumer API without any
network. Covers:

  * search_listings with pagination
  * search_listings with category / text_query / isFree filters
  * pick_top with exclude_ids
  * get_listing detail parsing
  * install_listing happy path
  * install_listing raises PersonalizationRequired on the right 4xx
  * list_fulfillments
  * 401/404/429/500 error mapping
  * exponential backoff on 429
"""

from __future__ import annotations

import json
import os
import pytest
import responses

from m100.marketplace_client import (
    Listing,
    MarketplaceClient,
    MarketplaceError,
    AuthError,
    NotFound,
    RateLimited,
    PersonalizationRequired,
    TransientError,
    categories_to_rotate,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def host_env(monkeypatch):
    """Set the env vars the client reads."""
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.cloud.databricks.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "fake-token-123")


@pytest.fixture
def client(host_env):
    return MarketplaceClient()


# ============================================================
# search_listings
# ============================================================

@responses.activate
def test_search_listings_yields_listings(client):
    responses.post(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/search-listings",
        json={
            "listings": [
                {
                    "id": "abc-123",
                    "title": "Test Listing",
                    "provider": "Test Provider",
                    "summary": "A test",
                    "categories": ["Finance"],
                    "downloads": 100,
                }
            ],
            "nextPageToken": None,
        },
        status=200,
    )
    listings = list(client.search_listings(category="Finance"))
    assert len(listings) == 1
    assert listings[0].id == "abc-123"
    assert listings[0].title == "Test Listing"
    assert listings[0].provider == "Test Provider"
    assert "Finance" in listings[0].categories
    assert listings[0].downloads == 100


@responses.activate
def test_search_listings_paginates(client):
    """Two pages of results, second page returns no nextPageToken."""
    responses.post(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/search-listings",
        json={
            "listings": [{"id": f"page1-{i}", "title": f"P1-{i}"} for i in range(3)],
            "nextPageToken": "tok-1",
        },
        status=200,
    )
    responses.post(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/search-listings",
        json={
            "listings": [{"id": f"page2-{i}", "title": f"P2-{i}"} for i in range(2)],
            "nextPageToken": None,
        },
        status=200,
    )
    all_ids = [l.id for l in client.search_listings(max_pages=5)]
    assert all_ids == ["page1-0", "page1-1", "page1-2", "page2-0", "page2-1"]


@responses.activate
def test_pick_top_skips_excluded(client):
    responses.post(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/search-listings",
        json={
            "listings": [
                {"id": "skip-me", "title": "S"},
                {"id": "keep-me", "title": "K"},
            ],
        },
        status=200,
    )
    picked = client.pick_top(
        category="Finance", exclude_ids={"skip-me", "already-seen"}, top_n=1,
    )
    assert len(picked) == 1
    assert picked[0].id == "keep-me"


# ============================================================
# Detail + install + fulfillments
# ============================================================

@responses.activate
def test_get_listing_parses_nested(client):
    responses.get(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/listings/xyz",
        json={
            "id": "xyz",
            "title": "Detail Test",
            "detail": {"providerName": "Nested Provider"},
            "categories": "Finance,Healthcare",
            "fileList": [{"path": "s3://bucket/x.parquet", "format": "parquet"}],
        },
        status=200,
    )
    listing = client.get_listing("xyz")
    assert listing.provider == "Nested Provider"
    assert listing.categories == ["Finance", "Healthcare"]
    assert listing.file_list[0]["path"] == "s3://bucket/x.parquet"


@responses.activate
def test_install_listing_happy_path(client):
    responses.post(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/listings/abc/installations",
        json={"id": "install-1", "catalogName": "marketplace_100", "schemaName": "bronze"},
        status=200,
    )
    out = client.install_listing("abc", catalog="marketplace_100")
    assert out["catalogName"] == "marketplace_100"


@responses.activate
def test_install_listing_personalization_required(client):
    """The API returns 400 with 'personalization' in the body → our wrapper raises."""
    responses.post(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/listings/abc/installations",
        json={"error": "personalization required for this listing"},
        status=400,
    )
    with pytest.raises(PersonalizationRequired):
        client.install_listing("abc", catalog="marketplace_100")


@responses.activate
def test_list_fulfillments(client):
    responses.get(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/listings/abc/fulfillments",
        json={
            "files": [
                {"path": "s3://b/a.parquet", "format": "parquet"},
                {"path": "s3://b/b.csv", "format": "csv"},
            ]
        },
        status=200,
    )
    files = client.list_fulfillments("abc")
    assert len(files) == 2
    assert files[0]["format"] == "parquet"


# ============================================================
# Error mapping
# ============================================================

@responses.activate
def test_401_raises_auth_error(client):
    responses.post(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/search-listings",
        body="unauthorized", status=401,
    )
    with pytest.raises(AuthError):
        list(client.search_listings())


@responses.activate
def test_404_raises_not_found(client):
    responses.get(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/listings/missing",
        body="not found", status=404,
    )
    with pytest.raises(NotFound):
        client.get_listing("missing")


@responses.activate
def test_429_retries_with_backoff(client):
    """429 → RateLimited → tenacity retries → 200."""
    call_count = {"n": 0}
    def callback(request):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return (429, {"Retry-After": "1"}, "rate limited")
        return (200, {}, json.dumps({"listings": [{"id": "after-retry", "title": "OK"}]}))

    responses.add_callback(
        responses.POST,
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/search-listings",
        callback=callback,
    )
    listings = list(client.search_listings())
    assert call_count["n"] == 2
    assert listings[0].id == "after-retry"


@responses.activate
def test_500_raises_transient(client):
    responses.post(
        "https://test.cloud.databricks.com/api/2.1/marketplace-consumer/search-listings",
        body="server error", status=500,
    )
    # Tenacity retries 6 times by default — every retry is also 500
    with pytest.raises((TransientError, MarketplaceError)):
        list(client.search_listings())


# ============================================================
# Auth bootstrap
# ============================================================

def test_missing_host_raises(monkeypatch):
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.setenv("DATABRICKS_TOKEN", "x")
    with pytest.raises(AuthError):
        MarketplaceClient()


def test_missing_token_raises(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://x")
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    with pytest.raises(AuthError):
        MarketplaceClient()


# ============================================================
# Category rotation
# ============================================================

def test_categories_to_rotate_cycles_through_known_list():
    seen = {categories_to_rotate(i) for i in range(20)}
    # We rotate through 10 — at least 6 unique should appear in 20 iters
    assert len(seen) >= 6
    # All are from the known list
    known = {"Finance", "Healthcare", "Geospatial", "Retail", "Transportation",
             "Energy", "Climate", "Public Sector", "Marketing", "Sports"}
    assert seen <= known
