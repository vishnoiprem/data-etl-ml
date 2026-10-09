"""Paginated HTTP API extractor with rate-limit handling.

Implements cursor-based pagination, 429 backoff, and a tiny
``http.server``-based mock so tests don't need a real API.

The poll is a generator that yields rows one at a time. The caller
can materialize it (``list(poller.poll_all())``) or stream it into
a sink.

Example::

    poller = ApiPoller(
        base_url="http://localhost:8080/items",
        page_size=5,
        cursor_param="after",
        page_param="page_size",
    )
    for row in poller.poll_all():
        process(row)

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

import json
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse


class ApiPoller:
    """Paginated HTTP API extractor with rate-limit handling.

    Parameters
    ----------
    base_url:
        The endpoint to poll, e.g. ``"http://api.example.com/items"``.
    page_size:
        Number of rows per page (sent as the ``page_size`` query param).
    cursor_param:
        Query string key for the cursor, e.g. ``"after"`` (Stripe-style)
        or ``"cursor"``.
    page_param:
        Query string key for the page size, e.g. ``"limit"`` (Stripe)
        or ``"page_size"``.
    data_key:
        JSON key under which the rows live in the response, e.g.
        ``"data"`` (Stripe) or ``"results"`` (Django REST).
    next_cursor_key:
        JSON key under which the next cursor lives, e.g.
        ``"next_cursor"`` or ``"has_more"`` (boolean).
    fetch:
        Optional callable for the HTTP fetch — defaults to a tiny
        stdlib-based GET. Tests can inject a mock.
    max_retries:
        Maximum retries on 429 (rate limited). Each retry respects
        the ``Retry-After`` header.
    sleep:
        Sleep function — defaults to ``time.sleep``. Tests inject a
        no-op.
    """

    def __init__(
        self,
        base_url: str,
        page_size: int = 100,
        cursor_param: str = "after",
        page_param: str = "page_size",
        data_key: str = "data",
        next_cursor_key: str = "next_cursor",
        fetch: Optional[Callable[[str], Tuple[int, Dict[str, str], str]]] = None,
        max_retries: int = 5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.base_url = base_url
        self.page_size = page_size
        self.cursor_param = cursor_param
        self.page_param = page_param
        self.data_key = data_key
        self.next_cursor_key = next_cursor_key
        self.fetch = fetch or _default_fetch
        self.max_retries = max_retries
        self._sleep = sleep

    def _build_url(self, cursor: Optional[str]) -> str:
        sep = "&" if "?" in self.base_url else "?"
        url = f"{self.base_url}{sep}{self.page_param}={self.page_size}"
        if cursor:
            url += f"&{self.cursor_param}={cursor}"
        return url

    def _fetch_page(self, cursor: Optional[str]) -> Tuple[List[Any], Optional[str]]:
        url = self._build_url(cursor)
        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries):
            status, headers, body = self.fetch(url)
            if status == 429:
                # Honor Retry-After; fall back to exponential backoff.
                retry_after = float(headers.get("Retry-After", 0))
                backoff = max(retry_after, 0.5 * (2 ** attempt))
                backoff *= 1 + random.random() * 0.1  # jitter
                self._sleep(backoff)
                last_err = RuntimeError("rate limited")
                continue
            if status >= 500:
                # Server error — back off and retry.
                self._sleep(0.5 * (2 ** attempt))
                last_err = RuntimeError(f"server error {status}")
                continue
            if status != 200:
                raise RuntimeError(
                    f"GET {url} failed: status={status} body={body!r}"
                )
            payload = json.loads(body)
            rows = payload.get(self.data_key, [])
            next_cursor = payload.get(self.next_cursor_key)
            return rows, next_cursor
        raise RuntimeError(
            f"GET {url} failed after {self.max_retries} retries: {last_err}"
        )

    def poll_all(self) -> Iterator[Any]:
        """Yield rows from all pages."""
        cursor: Optional[str] = None
        while True:
            rows, next_cursor = self._fetch_page(cursor)
            for row in rows:
                yield row
            if not next_cursor:
                return
            cursor = next_cursor


# ---- stdlib fetch helper ---------------------------------------------


def _default_fetch(url: str) -> Tuple[int, Dict[str, str], str]:
    """A minimal stdlib HTTP GET. Not for production use."""
    import urllib.request

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        return resp.status, dict(resp.headers), resp.read().decode("utf-8")


# ---- a tiny mock server for tests ------------------------------------


class _MockHandler(BaseHTTPRequestHandler):
    """A test-only handler that returns paginated JSON.

    The handler is parameterized via class attributes set by
    :class:`MockPaginatedAPI` below.
    """

    rows: List[Dict[str, Any]] = []
    page_size: int = 5

    def do_GET(self) -> None:  # noqa: N802
        qs = parse_qs(urlparse(self.path).query)
        cursor = qs.get("after", [None])[0]
        page_size = int(qs.get("page_size", [str(self.page_size)])[0])

        if cursor is None:
            start = 0
        else:
            start = int(cursor)

        end = min(start + page_size, len(self.rows))
        page = self.rows[start:end]
        next_cursor = str(end) if end < len(self.rows) else None

        body = json.dumps({"data": page, "next_cursor": next_cursor}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any, **kwargs: Any) -> None:  # quiet
        pass


class MockPaginatedAPI:
    """Context manager that runs a mock paginated API in a thread.

    Example::

        rows = [{"id": i, "name": f"row-{i}"} for i in range(15)]
        with MockPaginatedAPI(rows, page_size=5) as base:
            poller = ApiPoller(base_url=base, page_size=5)
            all_rows = list(poller.poll_all())
            assert len(all_rows) == 15
    """

    def __init__(self, rows: List[Dict[str, Any]], page_size: int = 5) -> None:
        self.rows = rows
        self.page_size = page_size
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def __enter__(self) -> str:
        # Bind to an OS-assigned port.
        handler = type(
            "_H",
            (_MockHandler,),
            {"rows": self.rows, "page_size": self.page_size},
        )
        self._server = HTTPServer(("127.0.0.1", 0), handler)
        port = self._server.server_address[1]
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._thread.start()
        return f"http://127.0.0.1:{port}/items"

    def __exit__(self, *exc: Any) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
