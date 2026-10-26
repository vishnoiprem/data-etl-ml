"""HTTP-level tests for the WebCrawler (Flask test client)."""

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

from code.app import create_app  # noqa: E402
from code.service import WebCrawler  # noqa: E402


class WebCrawlerAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        store = KeyValueStore(
            "test_crawler_app",
            persist_path=os.path.join(self.tmpdir, "crawler.json"),
        )
        cache = TTLCache(ttl_seconds=60, max_entries=100)
        # Don't auto-start a worker for the test client — we drive ticks manually.
        self.svc = WebCrawler(
            store=store,
            cache=cache,
            idgen=Snowflake(machine_id=10),
            host_delay_ms=1.0,
            start_worker=False,
        )
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.svc.stop_worker(timeout=0.5)

    def _drain(self, max_ticks: int = 200) -> None:
        for _ in range(max_ticks):
            if not self.svc.run_once():
                return

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_start_crawl_returns_id(self):
        r = self.client.post(
            "/api/crawl",
            json={"seed": "https://example.com/", "max_pages": 5, "max_depth": 1},
        )
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertIn("crawl_id", body)
        self.assertEqual(body["seed"], "https://example.com/")

    def test_start_crawl_rejects_missing_seed(self):
        r = self.client.post("/api/crawl", json={})
        self.assertEqual(r.status_code, 400)

    def test_start_crawl_rejects_bad_url(self):
        r = self.client.post("/api/crawl", json={"seed": "not-a-url"})
        self.assertEqual(r.status_code, 400)

    def test_status_after_crawl(self):
        r = self.client.post(
            "/api/crawl",
            json={"seed": "https://example.com/", "max_pages": 4, "max_depth": 1},
        )
        cid = r.get_json()["crawl_id"]
        self._drain()
        s = self.client.get("/api/crawl/status").get_json()
        self.assertGreaterEqual(len(s["crawls"]), 1)
        ids = [c["crawl_id"] for c in s["crawls"]]
        self.assertIn(cid, ids)

    def test_crawl_detail(self):
        r = self.client.post(
            "/api/crawl",
            json={"seed": "https://example.com/", "max_pages": 4, "max_depth": 1},
        )
        cid = r.get_json()["crawl_id"]
        self._drain()
        detail = self.client.get(f"/api/crawl/{cid}").get_json()
        self.assertEqual(detail["crawl_id"], cid)
        self.assertGreaterEqual(detail["pages"], 1)
        self.assertIn("pages_list", detail)

    def test_get_page_by_url(self):
        self.client.post(
            "/api/crawl",
            json={"seed": "https://example.com/", "max_pages": 3, "max_depth": 0},
        )
        self._drain()
        # URL is path-encoded; Flask <path:url> lets us pass /-encoded.
        r = self.client.get("/api/pages/https://example.com/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["url"], "https://example.com/")

    def test_get_page_missing(self):
        r = self.client.get("/api/pages/https://no-such-host.example/")
        self.assertEqual(r.status_code, 404)

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        text = r.get_data(as_text=True)
        self.assertIn("crawl_total", text)

    def test_index(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["service"], "web_crawler")
        self.assertIn("endpoints", body)


if __name__ == "__main__":
    unittest.main()