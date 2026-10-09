"""Service-level tests for the document processing pipeline."""

from __future__ import annotations

import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import DocumentService  # noqa: E402


class DocumentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = DocumentService()

    def tearDown(self) -> None:
        self.svc.stop_worker()

    def test_upload_creates_record(self) -> None:
        rec = self.svc.upload("Hello world", doc_type="text")
        self.assertEqual(rec["status"], "UPLOADED")
        self.assertEqual(rec["content"], "Hello world")
        self.assertTrue(rec["id"])

    def test_upload_validates_content(self) -> None:
        with self.assertRaises(ValueError):
            self.svc.upload(None)

    def test_force_advance_full_pipeline(self) -> None:
        rec = self.svc.upload(
            "Contact us at support@acme.com or call +1 415 555 1234. "
            "Acme Corp charges $99.99.",
            doc_type="text",
        )
        self.svc.force_advance_all()
        rec = self.svc.get(rec["id"])
        self.assertEqual(rec["status"], "INDEXED")
        types = {e["type"] for e in rec["entities"]}
        self.assertIn("email", types)
        self.assertIn("money", types)
        self.assertIn("phone", types)
        self.assertIn("org", types)

    def test_search_after_indexing(self) -> None:
        self.svc.upload("The quick brown fox jumps over the lazy dog")
        self.svc.upload("Acme Corp contact: support@acme.com")
        self.svc.force_advance_all()
        results = self.svc.search("acme")
        self.assertEqual(len(results), 1)
        self.assertIn("acme", results[0]["snippet"].lower())

    def test_search_returns_empty_for_missing(self) -> None:
        self.svc.upload("nothing relevant here")
        self.svc.force_advance_all()
        results = self.svc.search("nonexistent")
        self.assertEqual(results, [])

    def test_search_does_not_include_non_indexed(self) -> None:
        # Don't force advance; doc should not appear in search.
        self.svc.upload("pending document with keyword needle")
        results = self.svc.search("needle")
        self.assertEqual(results, [])

    def test_worker_advances_over_time(self) -> None:
        rec = self.svc.upload("the lazy dog sleeps. Email: a@b.com")
        # Worker tick is 50ms; wait a bit.
        deadline = time.time() + 2.0
        while time.time() < deadline:
            current = self.svc.get(rec["id"])
            if current and current["status"] == "INDEXED":
                break
            time.sleep(0.1)
        final = self.svc.get(rec["id"])
        self.assertEqual(final["status"], "INDEXED")
        self.assertTrue(any(e["type"] == "email" for e in final["entities"]))


if __name__ == "__main__":
    unittest.main()
