"""Web crawler core service.

A BFS web crawler with politeness, per-host queueing, dedup, and a
worker thread that processes the frontier. The actual page fetcher
is simulated — we map URLs to canned HTML so the system is fully
deterministic and runnable in tests without a network.

Architecture:

    seed -> enqueue(seed) -> worker pops host -> _fetch -> _parse
                                                       |
                                                       v
                                              enqueue(discovered links)

The frontier is a dict of deques, one per host, so we naturally
serialize requests to the same host and implement politeness via
a per-host "next due at" timestamp.

This module is HTTP-free; `app.py` is the Flask wrapper.
"""

from __future__ import annotations

import html
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Callable, Deque, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore


# ----------------------------- defaults -----------------------------------

DEFAULT_HOST_DELAY_MS = 250.0        # politeness: 250ms between same-host hits
DEFAULT_MAX_PAGES = 50               # cap per crawl
DEFAULT_MAX_DEPTH = 2                # BFS depth cap
DEFAULT_MAX_URLS = 5_000             # hard ceiling on the frontier
DEFAULT_WORKER_IDLE_SLEEP = 0.05     # how long the worker sleeps when idle


# ----------------------------- exceptions ---------------------------------


class CrawlerError(Exception):
    """Base class."""


class InvalidURLError(CrawlerError):
    """URL is not a well-formed http(s) URL."""


class CrawlNotFoundError(CrawlerError):
    """No crawl with that id."""


# ----------------------------- HTML link extraction -----------------------

# Deliberately tiny regex-based extractor. Real crawlers use lxml / beautifulsoup.
_HREF_RE = re.compile(
    r"""<a\s[^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>""",
    re.IGNORECASE | re.DOTALL,
)
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def extract_links(html_text: str, base_url: str) -> List[str]:
    """Extract a list of absolute URLs from a small subset of HTML.

    Only <a href="..."> tags are considered. We absolutise relative
    URLs against `base_url` and drop non-http(s) schemes.
    """
    if not html_text:
        return []
    found = []
    for href, _anchor in _HREF_RE.findall(html_text):
        if not href:
            continue
        # Strip fragments; we treat URLs without fragments as identical.
        if href.startswith("#"):
            continue
        try:
            absolute = urljoin(base_url, href)
        except ValueError:
            continue
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue
        if not parsed.netloc:
            continue
        # Drop fragments for dedup purposes.
        absolute = urlunparse(parsed._replace(fragment=""))
        found.append(absolute)
    return found


def extract_title(html_text: str) -> str:
    if not html_text:
        return ""
    m = _TITLE_RE.search(html_text)
    if not m:
        return ""
    return _WS_RE.sub(" ", _TAG_RE.sub("", html.unescape(m.group(1)))).strip()


def normalise_url(url: str) -> str:
    """Normalise a URL for dedup: lowercase scheme/host, drop default ports, drop fragments."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise InvalidURLError(f"unsupported scheme: {parsed.scheme!r}")
    if not parsed.netloc:
        raise InvalidURLError(f"missing host: {url!r}")
    host = parsed.hostname or ""
    if not host:
        raise InvalidURLError(f"missing host: {url!r}")
    netloc = host.lower()
    if (parsed.scheme == "http" and parsed.port == 80) or (
        parsed.scheme == "https" and parsed.port == 443
    ):
        # urlparse will leave :80/:443 in netloc; drop.
        netloc = host.lower()
    path = parsed.path or "/"
    # Drop trailing slash on non-root paths for dedup.
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse(
        (parsed.scheme.lower(), netloc, path, parsed.params, parsed.query, "")
    )


# ----------------------------- canned pages (simulated fetch) -------------

# A tiny in-process "web" so the demo is fully reproducible.
CANONICAL_PAGES: Dict[str, str] = {
    "https://example.com/": (
        "<html><head><title>Example</title></head><body>"
        "<a href='/about'>About</a>"
        "<a href='/contact'>Contact</a>"
        "</body></html>"
    ),
    "https://example.com/about": (
        "<html><head><title>About</title></head><body>"
        "<a href='/'>Home</a>"
        "<a href='https://other.example.com/team'>Team</a>"
        "</body></html>"
    ),
    "https://example.com/contact": (
        "<html><head><title>Contact</title></head><body>"
        "<a href='mailto:nope@example.com'>Email</a>"
        "<a href='/'>Home</a>"
        "</body></html>"
    ),
    "https://other.example.com/": (
        "<html><head><title>Other</title></head><body>"
        "<a href='/team'>Team</a>"
        "<a href='https://example.com/'>Example</a>"
        "</body></html>"
    ),
    "https://other.example.com/team": (
        "<html><head><title>Team</title></head><body></body></html>"
    ),
}


def default_fetch(url: str) -> Tuple[int, str]:
    """Simulated fetch. Returns (status_code, body)."""
    if url in CANONICAL_PAGES:
        return 200, CANONICAL_PAGES[url]
    return 404, "<html><head><title>Not Found</title></head><body>404</body></html>"


# ----------------------------- dataclasses --------------------------------


@dataclass
class Page:
    url: str
    status: int
    title: str
    links: List[str]
    fetched_at: float
    crawl_id: int
    depth: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Crawl:
    crawl_id: int
    seed: str
    max_pages: int
    max_depth: int
    status: str = "running"   # running | done | failed
    pages: int = 0
    errors: int = 0
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ----------------------------- the service --------------------------------


class WebCrawler:
    """BFS web crawler with per-host politeness and a worker thread.

    >>> c = WebCrawler(start_worker=False)
    >>> cid = c.start_crawl("https://example.com/")
    >>> c.run_once()  # synchronous tick
    >>> "https://example.com/" in [p.url for p in c.list_pages(cid)]
    True
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        cache: Optional[TTLCache] = None,
        idgen: Optional[Snowflake] = None,
        host_delay_ms: float = DEFAULT_HOST_DELAY_MS,
        max_urls: int = DEFAULT_MAX_URLS,
        fetcher: Optional[Callable[[str], Tuple[int, str]]] = None,
        start_worker: bool = True,
    ):
        self.store = store or KeyValueStore("web_crawler")
        self.cache = cache or TTLCache(ttl_seconds=300.0, max_entries=2_000)
        self.idgen = idgen or Snowflake(machine_id=10)
        self.host_delay_s = host_delay_ms / 1000.0
        self.max_urls = max_urls
        self.fetcher = fetcher or default_fetch

        # frontier: host -> deque of (url, depth, crawl_id)
        self._frontier: Dict[str, Deque[Tuple[str, int, int]]] = {}
        # next-due timestamp per host
        self._host_next_due: Dict[str, float] = {}
        # set of URLs we have already enqueued (in-memory; persisted too)
        self._pending: Set[str] = set()

        self._lock = threading.RLock()
        self._wake = threading.Event()         # signal worker to wake up
        self._stop = threading.Event()
        self._worker: Optional[threading.Thread] = None
        if start_worker:
            self.start_worker()

    # ---- lifecycle ------------------------------------------------------

    def start_worker(self) -> None:
        with self._lock:
            if self._worker and self._worker.is_alive():
                return
            self._stop.clear()
            self._worker = threading.Thread(
                target=self._worker_loop,
                name="web-crawler-worker",
                daemon=True,
            )
            self._worker.start()

    def stop_worker(self, timeout: float = 1.0) -> None:
        with self._lock:
            self._stop.set()
            self._wake.set()
        if self._worker:
            self._worker.join(timeout=timeout)

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            try:
                progressed = self.run_once()
            except Exception:  # pragma: no cover - never let the worker die
                progressed = False
            if not progressed:
                # Wait for either a new enqueue or shutdown.
                self._wake.wait(timeout=DEFAULT_WORKER_IDLE_SLEEP)
                self._wake.clear()

    # ---- public write paths --------------------------------------------

    def start_crawl(
        self,
        seed: str,
        max_pages: int = DEFAULT_MAX_PAGES,
        max_depth: int = DEFAULT_MAX_DEPTH,
    ) -> Crawl:
        """Register a crawl and enqueue its seed URL."""
        norm = normalise_url(seed)
        crawl = Crawl(
            crawl_id=self.idgen.next_id(),
            seed=norm,
            max_pages=max_pages,
            max_depth=max_depth,
        )
        self._persist_crawl(crawl)
        self._enqueue(norm, depth=0, crawl_id=crawl.crawl_id)
        return crawl

    def _enqueue(self, url: str, depth: int, crawl_id: int) -> bool:
        """Add URL to its host's queue. Returns False if it was a duplicate or capped."""
        try:
            host = urlparse(url).netloc.lower()
        except ValueError:
            return False
        with self._lock:
            if url in self._pending:
                return False
            if self._seen_persisted(url):
                return False
            total = sum(len(q) for q in self._frontier.values()) + len(self._pending)
            if total >= self.max_urls:
                return False
            self._frontier.setdefault(host, deque()).append((url, depth, crawl_id))
            self._pending.add(url)
            self._persist_seen(url)
        self._wake.set()
        return True

    def _seen_persisted(self, url: str) -> bool:
        return self.store.exists(f"seen:{url}")

    def _persist_seen(self, url: str) -> None:
        # Use a marker; this is fast and bounded by the URL cap.
        self.store.set(f"seen:{url}", True)

    def _persist_crawl(self, crawl: Crawl) -> None:
        self.store.set(f"crawl:{crawl.crawl_id}", crawl.to_dict())
        idx = self.store.get("crawlindex:all", [])
        if crawl.crawl_id not in idx:
            idx.append(crawl.crawl_id)
            self.store.set("crawlindex:all", idx)

    def _persist_page(self, page: Page) -> None:
        self.store.set(f"page:{page.url}", page.to_dict())
        # write-through cache
        self.cache.set(f"page:{page.url}", page.to_dict(), ttl_seconds=300.0)

    def _update_crawl(self, crawl_id: int, **fields) -> None:
        data = self.store.get(f"crawl:{crawl_id}")
        if not data:
            return
        data.update(fields)
        self.store.set(f"crawl:{crawl_id}", data)

    # ---- one tick of the worker ----------------------------------------

    def run_once(self) -> bool:
        """Pop one URL from the frontier, fetch, parse, enqueue links.

        Returns True if we did meaningful work, False if we waited.
        Tests call this directly to advance the crawler deterministically.
        """
        with self._lock:
            now = time.time()
            target = None
            target_host = None
            sleep_for = 0.0
            for host, q in self._frontier.items():
                if not q:
                    continue
                next_due = self._host_next_due.get(host, 0.0)
                if next_due <= now:
                    target = q.popleft()
                    target_host = host
                    break
                else:
                    # Find the soonest due time.
                    wait = next_due - now
                    if sleep_for == 0.0 or wait < sleep_for:
                        sleep_for = wait
            if target is None:
                # Nothing immediately runnable.
                if sleep_for > 0:
                    # Release the lock while we sleep briefly.
                    pass
                return False

            url, depth, crawl_id = target
            self._pending.discard(url)
            crawl = self.store.get(f"crawl:{crawl_id}") or {}
            max_pages = int(crawl.get("max_pages", DEFAULT_MAX_PAGES))
            max_depth = int(crawl.get("max_depth", DEFAULT_MAX_DEPTH))
            pages_so_far = int(crawl.get("pages", 0))
            # Politeness: bump this host's next-due.
            self._host_next_due[target_host] = time.time() + self.host_delay_s

        # Outside the lock now — fetch and parse.
        try:
            status, body = self.fetcher(url)
        except Exception:
            status, body = 599, ""
            with self._lock:
                self._update_crawl(crawl_id, errors=int(crawl.get("errors", 0)) + 1)

        page = Page(
            url=url,
            status=status,
            title=extract_title(body),
            links=[],
            fetched_at=time.time(),
            crawl_id=crawl_id,
            depth=depth,
        )

        if status < 400:
            page.links = extract_links(body, url)
            # BFS: only enqueue children if under caps.
            with self._lock:
                if pages_so_far < max_pages and depth < max_depth:
                    for link in page.links:
                        if not self._enqueue(link, depth + 1, crawl_id):
                            continue
                        pages_so_far += 1
                        if pages_so_far >= max_pages:
                            break

        with self._lock:
            self._persist_page(page)
            new_pages = int(crawl.get("pages", 0)) + 1
            update = {"pages": new_pages}
            if status >= 400:
                update["errors"] = int(crawl.get("errors", 0)) + 1
            # Mark crawl done if queue is empty for it.
            self._update_crawl(crawl_id, **update)
            if self._crawl_done(crawl_id):
                self._update_crawl(
                    crawl_id, status="done", finished_at=time.time()
                )

        return True

    def _crawl_done(self, crawl_id: int) -> bool:
        for q in self._frontier.values():
            for _url, _depth, cid in q:
                if cid == crawl_id:
                    return False
        return True

    # ---- reads ----------------------------------------------------------

    def get_crawl(self, crawl_id: int) -> Optional[dict]:
        return self.store.get(f"crawl:{crawl_id}")

    def list_crawls(self) -> List[dict]:
        ids = self.store.get("crawlindex:all", [])
        out = []
        for cid in ids:
            d = self.store.get(f"crawl:{cid}")
            if d:
                out.append(d)
        return out

    def get_page(self, url: str) -> Optional[dict]:
        try:
            key = normalise_url(url)
        except InvalidURLError:
            return None
        cached = self.cache.get(f"page:{key}")
        if cached:
            return cached
        data = self.store.get(f"page:{key}")
        if data:
            self.cache.set(f"page:{key}", data, ttl_seconds=300.0)
        return data

    def list_pages(self, crawl_id: int) -> List[dict]:
        out = []
        for _k, v in self.store.scan("page:"):
            if v.get("crawl_id") == crawl_id:
                out.append(v)
        return out

    # ---- inspection helpers -------------------------------------------

    def frontier_size(self) -> int:
        with self._lock:
            return sum(len(q) for q in self._frontier.values())

    def status(self) -> dict:
        with self._lock:
            return {
                "frontier": sum(len(q) for q in self._frontier.values()),
                "hosts": {h: len(q) for h, q in self._frontier.items()},
                "seen": len([k for k in self.store.all() if k.startswith("seen:")]),
                "pages": sum(
                    1 for k in self.store.all() if k.startswith("page:")
                ),
                "crawls": len(self.store.get("crawlindex:all", [])),
            }

    def cache_stats(self) -> dict:
        return self.cache.stats()
