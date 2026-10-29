"""
marketplace_client.py — Databricks Marketplace Consumer API wrapper.

The Marketplace API is the **only** external surface this project
depends on. Everything else (Delta, Unity Catalog, MLflow,
Foundation Model API, Lakebase) is internal to the workspace.

API surface used (Consumer API v1, `/api/2.1/marketplace-consumer`):

  GET  /search-listings                 list with filters + paging
  GET  /listings/{id}                   detail (provider, tags, sample)
  POST /listings/{id}/installations     install into a UC catalog
  GET  /listings/{id}/fulfillments      Delta paths / file URLs
  GET  /listings:batchGet               batch detail lookup

Auth: PAT or OAuth with the `marketplace` scope, sent as
`Authorization: Bearer <token>`. Same `WorkspaceClient` flow
as the rest of databricks-sdk.

Pagination: `page_token` + `page_size` (max 100). We never
rely on a single 1000-row result — every caller is page-
bounded.

Rate limiting: undocumented, but the Marketplace frontend
visibly backs off around 60 req/min on shared hosts. We
defensively apply exponential backoff with `tenacity`
on 429/503 responses.

"Personalization required" listings: some listings require
`POST /listings/{id}/personalization-requests` before
install. We do NOT implement that flow in v1 — we skip
the listing and log it. v1.1 will add a 24h-delayed retry
queue for those.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


# ============================================================
# Errors
# ============================================================

class MarketplaceError(Exception):
    """Base class for Marketplace client errors."""


class AuthError(MarketplaceError):
    """401 / 403 — bad token or missing scope."""


class RateLimited(MarketplaceError):
    """429 — we should back off."""
    def __init__(self, message: str, retry_after: float = 5.0):
        super().__init__(message)
        self.retry_after = retry_after


class NotFound(MarketplaceError):
    """404 — listing id doesn't exist (or wasn't installed yet)."""


class PersonalizationRequired(MarketplaceError):
    """The listing needs a personalization request before install.

    Per the Marketplace API docs, these are usually listings
    that gate data behind a use-case form (e.g. financial data
    providers). The driver logs and skips them in v1.
    """


class TransientError(MarketplaceError):
    """5xx other than 503."""


# ============================================================
# Listing dataclass — what the rest of the project uses
# ============================================================

@dataclass
class Listing:
    """A marketplace listing after normalization.

    The raw API response is nested; this flattens it into the
    fields the driver / ingest / DLT / agent actually use.
    """
    id: str
    title: str
    provider: str
    summary: str
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    is_free: bool = True
    is_shared: bool = True
    downloads: int = 0
    sample_query: Optional[str] = None
    file_list: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)  # full API response

    @classmethod
    def from_api(cls, raw: dict) -> "Listing":
        """Parse a single listing from /search-listings or /listings/{id}."""
        listing_id = raw.get("id") or raw.get("listingId") or raw.get("uuid") or ""
        meta = raw.get("metastring") or raw
        # Provider may be nested in `detail` or top-level.
        provider = (
            raw.get("provider")
            or raw.get("publisherName")
            or (raw.get("detail") or {}).get("providerName")
            or "Unknown"
        )
        # Categories are usually a flat list of strings.
        cats = (
            raw.get("categories")
            or raw.get("tags")
            or (raw.get("detail") or {}).get("categories")
            or []
        )
        if isinstance(cats, str):
            cats = [c.strip() for c in cats.split(",") if c.strip()]
        # File list — the actual Delta paths we can COPY INTO.
        file_list = raw.get("fileList") or raw.get("files") or []
        return cls(
            id=str(listing_id),
            title=raw.get("title") or raw.get("name") or "(untitled)",
            provider=provider,
            summary=raw.get("summary") or raw.get("description") or "",
            categories=[str(c) for c in cats],
            tags=[str(t) for t in (raw.get("tags") or [])],
            is_free=bool(raw.get("isFree", True)),
            is_shared=bool(raw.get("isShared", True)),
            downloads=int(raw.get("downloads") or raw.get("numDownloads") or 0),
            sample_query=raw.get("sampleQuery") or raw.get("sample_query"),
            file_list=list(file_list),
            raw=raw,
        )


# ============================================================
# Client
# ============================================================

class MarketplaceClient:
    """Thin wrapper over the Databricks Marketplace Consumer API.

    Usage:
        client = MarketplaceClient()  # reads DATABRICKS_HOST + DATABRICKS_TOKEN
        for listing in client.search_listings(category="Finance", max_pages=2):
            print(listing.id, listing.title)
        detail = client.get_listing("0f3a...")
        install = client.install_listing(detail.id, catalog="marketplace_100")
        files = client.list_fulfillments(detail.id)
    """

    DEFAULT_BASE = "/api/2.1/marketplace-consumer"
    DEFAULT_PAGE_SIZE = 50  # well under the 100 max
    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(
        self,
        host: Optional[str] = None,
        token: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.host = (host or os.getenv("DATABRICKS_HOST", "")).rstrip("/")
        self.token = token or os.getenv("DATABRICKS_TOKEN", "")
        if not self.host:
            raise AuthError("DATABRICKS_HOST not set (e.g. https://<workspace>.cloud.databricks.com)")
        if not self.token:
            raise AuthError("DATABRICKS_TOKEN not set (PAT with `marketplace` scope)")
        self.session = session or requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "marketplace-100/0.1 (+https://github.com/vishnoiprem)",
        })
        self.base = f"{self.host}{self.DEFAULT_BASE}"
        self.timeout = timeout

    # ----- low-level HTTP ------------------------------------------------

    @retry(
        retry=retry_if_exception_type((RateLimited, TransientError)),
        wait=wait_exponential(multiplier=2, min=2, max=120),
        stop=stop_after_attempt(6),
        reraise=True,
    )
    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base}{path}"
        kwargs.setdefault("timeout", self.timeout)
        try:
            resp = self.session.request(method, url, **kwargs)
        except requests.ConnectionError as e:
            raise TransientError(f"connection error: {e}") from e
        if resp.status_code == 401 or resp.status_code == 403:
            raise AuthError(f"{resp.status_code} {resp.text[:200]}")
        if resp.status_code == 404:
            raise NotFound(f"{path}: 404")
        if resp.status_code == 429:
            ra = float(resp.headers.get("Retry-After", 5))
            raise RateLimited(f"{path}: 429", retry_after=ra)
        if resp.status_code == 503:
            raise TransientError(f"{path}: 503 {resp.text[:200]}")
        if resp.status_code >= 500:
            raise TransientError(f"{path}: {resp.status_code} {resp.text[:200]}")
        if not resp.ok:
            # 4xx other than 401/403/404/429 — surface to caller
            raise MarketplaceError(
                f"{path}: {resp.status_code} {resp.text[:300]}"
            )
        # Marketplace sometimes returns empty 204 (rare)
        if not resp.content:
            return {}
        try:
            return resp.json()
        except ValueError as e:
            raise MarketplaceError(f"{path}: invalid JSON: {e}") from e

    # ----- search --------------------------------------------------------

    def search_listings(
        self,
        *,
        text_query: Optional[str] = None,
        category: Optional[str] = None,
        provider: Optional[str] = None,
        is_free: Optional[bool] = None,
        is_shared: Optional[bool] = None,
        sort_by: str = "downloads",  # downloads | createdAt | title
        page_size: int = DEFAULT_PAGE_SIZE,
        max_pages: int = 5,
    ) -> Iterator[Listing]:
        """Yield Listings matching the filter. Paginates internally.

        `max_pages` caps the iterator at `max_pages * page_size`
        results. The driver rotates `category` per iteration, so
        each call is bounded; we don't need unbounded pagination.
        """
        body: dict[str, Any] = {
            "pageSize": min(page_size, 100),
            "sortBy": sort_by,
        }
        pages: dict[str, Any] = {}
        if text_query:
            pages["textQuery"] = text_query
        if category:
            pages["category"] = category
        if provider:
            pages["provider"] = provider
        if is_free is not None:
            pages["isFree"] = is_free
        if is_shared is not None:
            pages["isShared"] = is_shared
        if pages:
            body["pages"] = pages

        yielded = 0
        for page_num in range(max_pages):
            data = self._request("POST", "/search-listings", json=body)
            items = data.get("listings") or data.get("results") or []
            for raw in items:
                try:
                    yield Listing.from_api(raw)
                    yielded += 1
                except Exception as e:
                    logger.warning("skipping unparseable listing: %s", e)
            token = data.get("nextPageToken") or data.get("page_token")
            if not token:
                break
            body["pageToken"] = token
        logger.info("search_listings: yielded %d listings", yielded)

    def pick_top(
        self,
        *,
        category: str,
        exclude_ids: set[str],
        top_n: int = 1,
        **kwargs,
    ) -> list[Listing]:
        """Pick the top-N listings in a category, skipping already-seen ids.

        Used by the driver: rotate category, ask for top-1 (or top-N
        for testing), filter out anything we've already processed.
        """
        picked: list[Listing] = []
        for listing in self.search_listings(category=category, **kwargs):
            if listing.id in exclude_ids:
                continue
            picked.append(listing)
            if len(picked) >= top_n:
                break
        return picked

    # ----- detail + install ----------------------------------------------

    def get_listing(self, listing_id: str) -> Listing:
        """Fetch full detail (includes file_list + sample_query)."""
        data = self._request("GET", f"/listings/{listing_id}")
        return Listing.from_api(data)

    def batch_get(self, listing_ids: list[str]) -> list[Listing]:
        """Batch detail lookup. Caps at 100 ids per call."""
        if not listing_ids:
            return []
        if len(listing_ids) > 100:
            raise ValueError("batch_get caps at 100 ids per call")
        data = self._request(
            "POST", "/listings:batchGet", json={"ids": listing_ids}
        )
        return [Listing.from_api(d) for d in data.get("listings", [])]

    def install_listing(
        self,
        listing_id: str,
        *,
        catalog: str,
        schema: str = "bronze",
        tokenless: bool = False,
    ) -> dict:
        """Install a listing into the target UC catalog.

        Returns the installation record. The actual Delta paths
        appear via `list_fulfillments` after the install completes
        (it can take 5-60 seconds for the share to propagate).
        """
        body = {
            "catalogName": catalog,
            "schemaName": schema,
            "tokenless": tokenless,
        }
        try:
            return self._request(
                "POST", f"/listings/{listing_id}/installations", json=body
            )
        except MarketplaceError as e:
            msg = str(e)
            if "personalization" in msg.lower():
                raise PersonalizationRequired(
                    f"{listing_id} requires personalization — skipping"
                ) from e
            raise

    def list_fulfillments(self, listing_id: str) -> list[dict]:
        """Return the actual Delta paths / file URLs for an installed listing.

        The shape is:
          [{"path": "/dbfs/mnt/...", "format": "delta|csv|parquet|json", ...}]

        We don't try to normalize this — the ingest layer reads
        it as-is and routes by `format`.
        """
        data = self._request("GET", f"/listings/{listing_id}/fulfillments")
        return data.get("files") or data.get("fulfillments") or data.get("paths", [])


# ============================================================
# Convenience — for the driver and the local smoke test
# ============================================================

def categories_to_rotate(cycle: int) -> str:
    """Pick a category for iteration `cycle` from a curated list.

    This is the agent's "exploration policy" — we cycle through
    a known-good list of populated categories so each iteration
    touches a different shape of data. The agent can override
    this with its own `next_category` from the tool-use response.
    """
    rotation = [
        "Finance",
        "Healthcare",
        "Geospatial",
        "Retail",
        "Transportation",
        "Energy",
        "Climate",
        "Public Sector",
        "Marketing",
        "Sports",
    ]
    return rotation[cycle % len(rotation)]


if __name__ == "__main__":
    # Tiny CLI for sanity-checking the connection.
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="Finance")
    ap.add_argument("--max-pages", type=int, default=1)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO)
    client = MarketplaceClient()
    out = []
    for listing in client.search_listings(
        category=args.category, max_pages=args.max_pages
    ):
        out.append({
            "id": listing.id,
            "title": listing.title,
            "provider": listing.provider,
            "downloads": listing.downloads,
            "categories": listing.categories,
        })
    print(json.dumps(out, indent=2))
