"""HTTP-level tests for the ChatGPT-style service (Flask test client)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.app import create_app  # noqa: E402
from code.service import ChatService  # noqa: E402


class ChatAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        store = KeyValueStore(
            "test_chat_app",
            persist_path=os.path.join(self.tmpdir, "chat.json"),
        )
        self.svc = ChatService(store=store, context_window=4)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_create_conversation(self):
        r = self.client.post(
            "/api/conversations",
            json={"user_id": "u1", "model": "mock-fast"},
        )
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertEqual(body["user_id"], "u1")
        self.assertEqual(body["model"], "mock-fast")
        self.assertEqual(body["messages"][0]["role"], "system")

    def test_create_rejects_unknown_model(self):
        r = self.client.post(
            "/api/conversations",
            json={"user_id": "u1", "model": "no-such"},
        )
        self.assertEqual(r.status_code, 400)

    def test_post_message(self):
        r1 = self.client.post(
            "/api/conversations",
            json={"user_id": "u1"},
        )
        cid = r1.get_json()["conversation_id"]
        r2 = self.client.post(
            f"/api/conversations/{cid}/messages",
            json={"role": "user", "content": "hi"},
        )
        self.assertEqual(r2.status_code, 201)
        self.assertEqual(r2.get_json()["role"], "user")

    def test_complete(self):
        r1 = self.client.post("/api/conversations", json={"user_id": "u1"})
        cid = r1.get_json()["conversation_id"]
        self.client.post(
            f"/api/conversations/{cid}/messages",
            json={"role": "user", "content": "hi"},
        )
        r2 = self.client.post(f"/api/conversations/{cid}/complete")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["role"], "assistant")
        self.assertGreater(len(r2.get_json()["content"]), 0)

    def test_stream_endpoint(self):
        r1 = self.client.post("/api/conversations", json={"user_id": "u1"})
        cid = r1.get_json()["conversation_id"]
        self.client.post(
            f"/api/conversations/{cid}/messages",
            json={"role": "user", "content": "explain caching"},
        )
        r = self.client.post(f"/api/conversations/{cid}/stream")
        self.assertEqual(r.status_code, 200)
        # SSE has the right content type and contains at least one event.
        self.assertIn("text/event-stream", r.headers["Content-Type"])
        body = r.get_data(as_text=True)
        self.assertIn("data: ", body)
        self.assertIn("[DONE]", body)

    def test_get_conversation(self):
        r1 = self.client.post("/api/conversations", json={"user_id": "u1"})
        cid = r1.get_json()["conversation_id"]
        r2 = self.client.get(f"/api/conversations/{cid}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["conversation_id"], cid)

    def test_get_conversation_404(self):
        r = self.client.get("/api/conversations/999")
        self.assertEqual(r.status_code, 404)

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("conversations_created_total", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
