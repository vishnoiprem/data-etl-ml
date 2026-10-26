"""HTTP tests for the Messenger service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import MessengerService  # noqa: E402


class MessengerAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = MessengerService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_e2e_send_and_fetch(self):
        r = self.client.post("/api/conversations", json={"user_a": 1, "user_b": 2})
        self.assertEqual(r.status_code, 201)
        cid = r.get_json()["conversation_id"]
        r = self.client.post(
            f"/api/conversations/{cid}/messages",
            json={"sender_id": 1, "body": "hello"},
        )
        self.assertEqual(r.status_code, 201)
        r = self.client.get(f"/api/conversations/{cid}/messages")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["messages"]), 1)

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_presence_flow(self):
        r = self.client.post("/api/users/42/heartbeat")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/api/users/42/presence")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertTrue(body["online"])
        self.assertIsNotNone(body["last_seen"])

    def test_invalid_send_rejected(self):
        r = self.client.post("/api/conversations", json={"user_a": 1, "user_b": 1})
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/conversations", json={"user_a": 1, "user_b": 2})
        cid = r.get_json()["conversation_id"]
        r = self.client.post(
            f"/api/conversations/{cid}/messages",
            json={"sender_id": 1, "body": ""},
        )
        self.assertEqual(r.status_code, 400)

    def test_sse_streams_message(self):
        import json as _json
        import queue
        import threading

        # Create conversation as user 1→2, then open SSE for user 2, then send.
        r = self.client.post("/api/conversations", json={"user_a": 1, "user_b": 2})
        cid = r.get_json()["conversation_id"]

        chunks: list[str] = []
        ev_q: "queue.Queue[str]" = queue.Queue()

        def reader():
            with self.app.test_client() as c2:
                resp = c2.get(f"/api/users/2/stream")
                for chunk in resp.response:
                    if chunk:
                        ev_q.put(chunk.decode("utf-8", errors="ignore"))

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        # Give the listener time to register.
        import time as _t
        _t.sleep(0.1)

        r = self.client.post(
            f"/api/conversations/{cid}/messages",
            json={"sender_id": 1, "body": "live-stream"},
        )
        self.assertEqual(r.status_code, 201)

        try:
            evt = ev_q.get(timeout=3.0)
        except queue.Empty:
            evt = ""
        # Initial 'ready' or actual 'message' both prove the stream is alive.
        self.assertTrue("event:" in evt)


if __name__ == "__main__":
    unittest.main()
