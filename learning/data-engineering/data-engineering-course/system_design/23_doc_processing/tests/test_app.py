"""HTTP-level tests for the document processing pipeline."""

from __future__ import annotations

import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import DocumentService  # noqa: E402


class DocumentAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = DocumentService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.svc.stop_worker()

    def test_upload_and_get(self) -> None:
        r = self.client.post("/api/documents", json={
            "content": "Hello world", "type": "text",
        })
        self.assertEqual(r.status_code, 201)
        doc_id = r.get_json()["id"]
        r = self.client.get(f"/api/documents/{doc_id}")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["id"], doc_id)
        self.assertIn("content_length", body)

    def test_get_missing_returns_404(self) -> None:
        r = self.client.get("/api/documents/9999")
        self.assertEqual(r.status_code, 404)

    def test_full_pipeline_via_force(self) -> None:
        r = self.client.post("/api/documents", json={
            "content": "Reach us at support@acme.com, $19.99 plan.",
        })
        doc_id = r.get_json()["id"]
        self.svc.force_advance_all()
        r = self.client.get(f"/api/documents/{doc_id}/entities")
        self.assertEqual(r.status_code, 200)
        entities = r.get_json()["entities"]
        types = {e["type"] for e in entities}
        self.assertIn("email", types)
        self.assertIn("money", types)

    def test_search(self) -> None:
        self.client.post("/api/documents", json={"content": "alpha bravo charlie"})
        self.client.post("/api/documents", json={"content": "delta echo foxtrot"})
        self.svc.force_advance_all()
        r = self.client.get("/api/search?q=alpha")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["results"]), 1)

    def test_health(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["stats"]["worker_alive"])

    def test_metrics(self) -> None:
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"upload_total", r.data)


if __name__ == "__main__":
    unittest.main()
