"""HTTP-level tests for the URL shortener (Flask test client)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.app import create_app  # noqa: E402
from code.service import URLShortener  # noqa: E402


class URLShortenerAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        store = KeyValueStore("test_us_app", persist_path=os.path.join(self.tmpdir, "us.json"))
        self.svc = URLShortener(store=store)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_shorten_creates_key(self):
        r = self.client.post(
            "/api/shorten",
            json={"url": "https://example.com/x"},
        )
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertIn("key", body)
        self.assertTrue(body["short_url"].endswith(body["key"]))

    def test_shorten_rejects_bad_url(self):
        r = self.client.post("/api/shorten", json={"url": "not-a-url"})
        self.assertEqual(r.status_code, 400)

    def test_resolve_redirects(self):
        r1 = self.client.post(
            "/api/shorten",
            json={"url": "https://example.com/redir"},
        )
        key = r1.get_json()["key"]
        r2 = self.client.get(f"/{key}")
        self.assertEqual(r2.status_code, 302)
        self.assertEqual(r2.headers["Location"], "https://example.com/redir")

    def test_resolve_404(self):
        r = self.client.get("/nope")
        self.assertEqual(r.status_code, 404)

    def test_stats(self):
        r1 = self.client.post("/api/shorten", json={"url": "https://example.com/s"})
        key = r1.get_json()["key"]
        self.client.get(f"/{key}")
        r2 = self.client.get(f"/api/stats/{key}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["clicks"], 1)

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("shorten_total", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
