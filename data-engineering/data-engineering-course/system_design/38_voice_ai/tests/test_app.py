"""HTTP-level tests for the real-time voice AI service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.app import create_app  # noqa: E402
from code.service import VoiceService  # noqa: E402


class VoiceAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        store = KeyValueStore(
            "test_voice_app",
            persist_path=os.path.join(self.tmpdir, "v.json"),
        )
        self.svc = VoiceService(store=store)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_create_session(self):
        r = self.client.post("/api/sessions", json={"user_id": "u1"})
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertEqual(body["user_id"], "u1")
        self.assertEqual(body["state"], "idle")

    def test_push_audio(self):
        r1 = self.client.post("/api/sessions", json={"user_id": "u1"})
        sid = r1.get_json()["session_id"]
        r2 = self.client.post(
            f"/api/sessions/{sid}/audio",
            data=b"\x00\x01\x02",
        )
        self.assertEqual(r2.status_code, 200)
        body = r2.get_json()
        self.assertIn(body["state"], ("playing", "done"))
        self.assertGreater(len(body["audio_chunks"]), 0)
        # Each chunk has metadata (text, size, sha256, is_final).
        for c in body["audio_chunks"]:
            self.assertIn("text", c)
            self.assertIn("size", c)
            self.assertIn("is_final", c)

    def test_get_transcript(self):
        r1 = self.client.post("/api/sessions", json={"user_id": "u1"})
        sid = r1.get_json()["session_id"]
        self.client.post(f"/api/sessions/{sid}/audio", data=b"\x00")
        r2 = self.client.get(f"/api/sessions/{sid}/transcript")
        self.assertEqual(r2.status_code, 200)
        body = r2.get_json()
        self.assertGreater(len(body["transcript"]), 0)
        roles = [t["role"] for t in body["transcript"]]
        self.assertIn("user", roles)
        self.assertIn("assistant", roles)

    def test_stream_endpoint(self):
        r1 = self.client.post("/api/sessions", json={"user_id": "u1"})
        sid = r1.get_json()["session_id"]
        self.client.post(f"/api/sessions/{sid}/audio", data=b"\x00")
        r = self.client.get(f"/api/sessions/{sid}/audio/stream")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/event-stream", r.headers["Content-Type"])
        body = r.get_data(as_text=True)
        self.assertIn("data: ", body)
        self.assertIn("[DONE]", body)

    def test_clear_outbox(self):
        r1 = self.client.post("/api/sessions", json={"user_id": "u1"})
        sid = r1.get_json()["session_id"]
        self.client.post(f"/api/sessions/{sid}/audio", data=b"\x00")
        r = self.client.post(f"/api/sessions/{sid}/outbox/clear")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.get_json()["cleared"], 0)

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("sessions_created_total", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
