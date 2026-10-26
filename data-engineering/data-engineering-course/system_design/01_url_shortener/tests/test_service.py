"""Unit tests for the URL shortener core service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from common.cache import TTLCache  # noqa: E402
from code.service import URLShortener  # noqa: E402


class URLShortenerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_us",
            persist_path=os.path.join(self.tmpdir, "us.json"),
        )
        self.cache = TTLCache(ttl_seconds=60, max_entries=100)
        self.svc = URLShortener(store=self.store, cache=self.cache)

    # ---- validation ----------------------------------------------------

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            self.svc.shorten("")

    def test_rejects_non_http(self):
        with self.assertRaises(ValueError):
            self.svc.shorten("ftp://example.com/x")

    def test_rejects_oversize(self):
        with self.assertRaises(ValueError):
            self.svc.shorten("https://example.com/" + "a" * 5000)

    # ---- happy path ----------------------------------------------------

    def test_shorten_and_resolve(self):
        rec = self.svc.shorten("https://example.com/abc")
        self.assertEqual(rec.long_url, "https://example.com/abc")
        again = self.svc.resolve(rec.key)
        self.assertIsNotNone(again)
        self.assertEqual(again.long_url, "https://example.com/abc")

    def test_idempotent_shorten(self):
        a = self.svc.shorten("https://example.com/dup")
        b = self.svc.shorten("https://example.com/dup")
        self.assertEqual(a.key, b.key)

    def test_distinct_urls_get_distinct_keys(self):
        a = self.svc.shorten("https://example.com/one")
        b = self.svc.shorten("https://example.com/two")
        self.assertNotEqual(a.key, b.key)

    def test_custom_alias(self):
        rec = self.svc.shorten("https://example.com/x", alias="my-link")
        self.assertEqual(rec.key, "my-link")
        self.assertTrue(rec.is_alias)
        again = self.svc.resolve("my-link")
        self.assertEqual(again.long_url, "https://example.com/x")

    def test_alias_taken(self):
        self.svc.shorten("https://example.com/a", alias="dup")
        with self.assertRaises(ValueError):
            self.svc.shorten("https://example.com/b", alias="dup")

    def test_reserved_alias(self):
        with self.assertRaises(ValueError):
            self.svc.shorten("https://example.com/x", alias="admin")

    def test_resolve_missing(self):
        self.assertIsNone(self.svc.resolve("nope"))

    def test_click_counter(self):
        rec = self.svc.shorten("https://example.com/click")
        for _ in range(3):
            self.svc.record_click(rec.key)
        self.assertEqual(self.svc.stats(rec.key)["clicks"], 3)

    def test_cache_used_on_second_resolve(self):
        rec = self.svc.shorten("https://example.com/cache")
        # first resolve → cache populated
        self.svc.resolve(rec.key)
        # drop store to prove cache is hit
        self.store.delete(f"url:{rec.key}")
        again = self.svc.resolve(rec.key)
        self.assertIsNotNone(again)
        # cache should now have a hit
        self.assertGreaterEqual(self.cache.stats()["hits"], 1)


if __name__ == "__main__":
    unittest.main()
