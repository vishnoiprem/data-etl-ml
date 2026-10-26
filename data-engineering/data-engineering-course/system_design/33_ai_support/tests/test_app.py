"""HTTP-level tests for the AI-Powered Customer Support service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.app import create_app  # noqa: E402
from code.service import SupportService  # noqa: E402


class SupportAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        store = KeyValueStore(
            "test_ai_support_app",
            persist_path=os.path.join(self.tmpdir, "ai.json"),
        )
        self.svc = SupportService(store=store, top_k=2)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_ingest_article(self):
        r = self.client.post(
            "/api/articles",
            json={
                "title": "Refunds",
                "body": "Refunds within 30 days.",
                "tags": ["refund"],
            },
        )
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertEqual(body["title"], "Refunds")
        self.assertEqual(body["article_id"], 1)

    def test_ingest_rejects_missing(self):
        r = self.client.post("/api/articles", json={"title": "x"})
        self.assertEqual(r.status_code, 400)

    def test_open_and_get_ticket(self):
        r = self.client.post(
            "/api/tickets",
            json={"user_id": "u1", "subject": "Help", "body": "I need help"},
        )
        self.assertEqual(r.status_code, 201)
        tid = r.get_json()["ticket_id"]
        r2 = self.client.get(f"/api/tickets/{tid}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["user_id"], "u1")

    def test_auto_reply_endpoint(self):
        self.client.post(
            "/api/articles",
            json={
                "title": "Reset password",
                "body": "Click Forgot Password.",
                "tags": ["login"],
            },
        )
        r = self.client.post(
            "/api/tickets",
            json={
                "user_id": "u1",
                "subject": "Can't log in",
                "body": "I forgot my password",
            },
        )
        tid = r.get_json()["ticket_id"]
        r2 = self.client.post(f"/api/tickets/{tid}/reply", json={})
        self.assertEqual(r2.status_code, 200)
        body = r2.get_json()
        self.assertEqual(body["reply"]["role"], "assistant")
        self.assertGreater(len(body["reply"]["citations"]), 0)

    def test_agent_reply_endpoint(self):
        r = self.client.post(
            "/api/tickets",
            json={"user_id": "u1", "subject": "x", "body": "y"},
        )
        tid = r.get_json()["ticket_id"]
        r2 = self.client.post(
            f"/api/tickets/{tid}/reply",
            json={"role": "agent", "body": "Looking into it."},
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["reply"]["role"], "agent")

    def test_retrieve_endpoint(self):
        self.client.post(
            "/api/articles",
            json={"title": "Refunds", "body": "Refunds in 30 days.", "tags": ["refund"]},
        )
        r = self.client.post("/api/retrieve", json={"query": "refund policy"})
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertGreater(len(body["results"]), 0)

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        text = r.get_data(as_text=True)
        self.assertIn("articles_ingested_total", text)


if __name__ == "__main__":
    unittest.main()
