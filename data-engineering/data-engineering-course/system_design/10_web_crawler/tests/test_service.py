"""Unit tests for the WebCrawler service."""

from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.cache import TTLCache  # noqa: E402
from common.ids import Snowflake  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from code.service import (  # noqa: E402
    CANONICAL_PAGES,
    InvalidURLError,
    WebCrawler,
    extract_links,
    extract_title,
    normalise_url,
)


class URLHelpers(unittest.TestCase):
    def test_normalise_lowercases_host(self):
        self.assertEqual(
            normalise_url("HTTPS://Example.COM/Path"),
            "https://example.com/Path",
        )

    def test_normalise_strips_default_port(self):
        # urlparse keeps the port literal; netloc.hostname is just the host.
        out = normalise_url("https://example.com:443/x")
        self.assertEqual(out, "https://example.com/x")

    def test_normalise_drops_fragment(self):
        self.assertEqual(
            normalise_url("https://example.com/x#frag"),
            "https://example.com/x",
        )

    def test_normalise_rejects_bad_scheme(self):
        with self.assertRaises(InvalidURLError):
            normalise_url("ftp://example.com/")

    def test_extract_links_absolutises(self):
        html = "<a href='/about'>A</a><a href='https://other.com/x'>B</a>"
        self.assertEqual(
            extract_links(html, "https://example.com/"),
            ["https://example.com/about", "https://other.com/x"],
        )

    def test_extract_links_drops_mailto(self):
        html = '<a href="mailto:nope@x.com">x</a>'
        self.assertEqual(extract_links(html, "https://example.com/"), [])

    def test_extract_title_strips_tags(self):
        self.assertEqual(
            extract_title("<title>Hello <b>world</b></title>"),
            "Hello world",
        )


class WebCrawlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_crawler",
            persist_path=os.path.join(self.tmpdir, "crawler.json"),
        )
        self.cache = TTLCache(ttl_seconds=60, max_entries=100)
        self.svc = WebCrawler(
            store=self.store,
            cache=self.cache,
            idgen=Snowflake(machine_id=10),
            host_delay_ms=1.0,  # keep tests fast
            start_worker=False,
        )

    def tearDown(self) -> None:
        self.svc.stop_worker(timeout=0.5)

    def _drain(self, max_ticks: int = 200) -> None:
        for _ in range(max_ticks):
            if not self.svc.run_once():
                return

    # ---- core BFS -------------------------------------------------------

    def test_start_crawl_persists(self):
        c = self.svc.start_crawl("https://example.com/", max_pages=5)
        self.assertEqual(c.seed, "https://example.com/")
        self.assertEqual(c.status, "running")
        self.assertIsNotNone(self.svc.get_crawl(c.crawl_id))

    def test_bfs_fetches_seed_then_links(self):
        c = self.svc.start_crawl("https://example.com/", max_pages=5, max_depth=2)
        self._drain()
        pages = {p["url"] for p in self.svc.list_pages(c.crawl_id)}
        self.assertIn("https://example.com/", pages)
        self.assertIn("https://example.com/about", pages)

    def test_bfs_respects_max_pages(self):
        c = self.svc.start_crawl("https://example.com/", max_pages=2, max_depth=2)
        self._drain()
        pages = self.svc.list_pages(c.crawl_id)
        self.assertEqual(len(pages), 2)
        # crawl should be marked done.
        self.assertEqual(self.svc.get_crawl(c.crawl_id)["status"], "done")

    def test_bfs_respects_max_depth(self):
        # Depth 0 means: only the seed.
        c = self.svc.start_crawl("https://example.com/", max_pages=20, max_depth=0)
        self._drain()
        pages = self.svc.list_pages(c.crawl_id)
        urls = [p["url"] for p in pages]
        self.assertEqual(urls, ["https://example.com/"])

    def test_dedup_within_a_crawl(self):
        # Both example.com/ and other.example.com/ link to each other.
        c = self.svc.start_crawl("https://example.com/", max_pages=20, max_depth=3)
        self._drain()
        pages = self.svc.list_pages(c.crawl_id)
        urls = [p["url"] for p in pages]
        self.assertEqual(len(urls), len(set(urls)), "no duplicates fetched")

    def test_politeness_sets_next_due(self):
        c = self.svc.start_crawl("https://example.com/", max_pages=2, max_depth=0)
        self.svc.run_once()
        # example.com host should have a future next_due timestamp.
        self.assertGreater(self.svc._host_next_due.get("example.com", 0.0), 0.0)

    def test_invalid_url_rejected(self):
        with self.assertRaises(InvalidURLError):
            self.svc.start_crawl("not a url")

    def test_cross_host_links_followed(self):
        c = self.svc.start_crawl("https://other.example.com/", max_pages=10, max_depth=2)
        self._drain()
        urls = {p["url"] for p in self.svc.list_pages(c.crawl_id)}
        self.assertIn("https://other.example.com/team", urls)

    def test_status_snapshot(self):
        self.svc.start_crawl("https://example.com/", max_pages=5, max_depth=1)
        s = self.svc.status()
        self.assertIn("frontier", s)
        self.assertIn("seen", s)
        self.assertIn("pages", s)


if __name__ == "__main__":
    unittest.main()