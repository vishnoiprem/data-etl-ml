"""HTTP-level tests for the Twitch service (Flask test client)."""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.app import create_app  # noqa: E402
from code.service import TwitchService  # noqa: E402


class TwitchServiceAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        store = KeyValueStore(
            "test_twitch_app",
            persist_path=os.path.join(self.tmpdir, "twitch.json"),
        )
        self.svc = TwitchService(store=store, heartbeat_timeout_s=30.0)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def _create_user(self, name: str) -> int:
        r = self.client.post("/api/users", json={"name": name})
        self.assertEqual(r.status_code, 201)
        return r.get_json()["user_id"]

    def _start_stream(self, user_id: int, title: str, game: str) -> int:
        r = self.client.post(
            "/api/streams",
            json={"user_id": user_id, "title": title, "game": game},
        )
        self.assertEqual(r.status_code, 201)
        return r.get_json()["stream_id"]

    # ---- health + index + metrics -----------------------------------

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_index_lists_endpoints(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["service"], "twitch_service")
        self.assertIn("POST /api/streams", body["endpoints"])
        self.assertIn("GET /api/streams/<id>/chat/sse", body["endpoints"])

    def test_metrics_endpoint(self):
        # Trigger a couple of calls so something is in the registry.
        self._create_user("m_alice")
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        text = r.get_data(as_text=True)
        self.assertIn("user_total", text)
        self.assertIn("stream_start_total", text)

    # ---- stream flows -----------------------------------------------

    def test_create_user_and_start_stream(self):
        uid = self._create_user("alice")
        sid = self._start_stream(uid, "playing zelda", "zelda")
        # And we can fetch the stream metadata.
        r = self.client.get(f"/api/streams/{sid}")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["title"], "playing zelda")
        self.assertEqual(body["game"], "zelda")
        self.assertTrue(body["live"])
        self.assertEqual(body["viewers"], 0)

    def test_get_stream_404(self):
        r = self.client.get("/api/streams/9999999")
        self.assertEqual(r.status_code, 404)

    def test_end_stream_marks_not_live(self):
        uid = self._create_user("alice")
        sid = self._start_stream(uid, "title", "game")
        r = self.client.post(f"/api/streams/{sid}/end")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.get_json()["live"])
        # And the stream now reports live: false.
        r = self.client.get(f"/api/streams/{sid}")
        self.assertFalse(r.get_json()["live"])

    def test_list_streams_by_game(self):
        u = self._create_user("alice")
        s1 = self._start_stream(u, "a", "zelda")
        s2 = self._start_stream(u, "b", "minecraft")
        s3 = self._start_stream(u, "c", "zelda")
        r = self.client.get("/api/streams?game=zelda")
        self.assertEqual(r.status_code, 200)
        ids = {item["stream_id"] for item in r.get_json()["results"]}
        self.assertIn(s1, ids)
        self.assertIn(s3, ids)
        self.assertNotIn(s2, ids)

    # ---- chat flows --------------------------------------------------

    def test_post_and_get_chat(self):
        u = self._create_user("alice")
        sid = self._start_stream(u, "title", "game")
        r = self.client.post(
            f"/api/streams/{sid}/chat",
            json={"user_id": u, "body": "hello chat"},
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["body"], "hello chat")
        # And GET returns the log.
        r = self.client.get(f"/api/streams/{sid}/chat?limit=10")
        self.assertEqual(r.status_code, 200)
        results = r.get_json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["body"], "hello chat")

    def test_post_chat_rejects_when_offline(self):
        u = self._create_user("alice")
        sid = self._start_stream(u, "title", "game")
        self.client.post(f"/api/streams/{sid}/end")
        r = self.client.post(
            f"/api/streams/{sid}/chat",
            json={"user_id": u, "body": "after end"},
        )
        self.assertEqual(r.status_code, 400)

    def test_post_chat_rejects_too_long(self):
        u = self._create_user("alice")
        sid = self._start_stream(u, "title", "game")
        r = self.client.post(
            f"/api/streams/{sid}/chat",
            json={"user_id": u, "body": "x" * 501},
        )
        self.assertEqual(r.status_code, 400)

    # ---- viewer flows -----------------------------------------------

    def test_heartbeat_increments_viewers(self):
        u1 = self._create_user("alice")
        u2 = self._create_user("bob")
        sid = self._start_stream(u1, "title", "game")
        r1 = self.client.post(
            f"/api/streams/{sid}/heartbeat",
            json={"viewer_id": u2},
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.get_json()["viewers"], 1)
        # GET /viewers agrees.
        r2 = self.client.get(f"/api/streams/{sid}/viewers")
        self.assertEqual(r2.get_json()["viewers"], 1)

    def test_heartbeat_updates_peak_viewers(self):
        u1 = self._create_user("alice")
        u2 = self._create_user("bob")
        u3 = self._create_user("carol")
        sid = self._start_stream(u1, "title", "game")
        self.client.post(
            f"/api/streams/{sid}/heartbeat", json={"viewer_id": u2}
        )
        r = self.client.post(
            f"/api/streams/{sid}/heartbeat", json={"viewer_id": u3}
        )
        self.assertEqual(r.get_json()["viewers"], 2)
        self.assertEqual(r.get_json()["peak_viewers"], 2)
        # And the stream metadata reflects the peak.
        r = self.client.get(f"/api/streams/{sid}")
        self.assertEqual(r.get_json()["peak_viewers"], 2)

    # ---- SSE --------------------------------------------------------

    def test_sse_streams_initial_hello(self):
        u = self._create_user("alice")
        sid = self._start_stream(u, "title", "game")
        # Use the test client to consume the SSE stream for ~2.5s.
        # We post a chat message from another thread, then verify
        # the SSE response includes the "hello" event and the chat.
        result: dict = {"lines": [], "got_chat": False, "done": False}

        def consume():
            with self.client.get(
                f"/api/streams/{sid}/chat/sse",
                buffered=False,
            ) as resp:
                self.assertEqual(resp.status_code, 200)
                # Read a few lines: hello + at least one chat.
                # The hello is yielded immediately; chat comes after.
                deadline = time.time() + 3.0
                buf = ""
                for raw in resp.response:
                    if time.time() > deadline:
                        break
                    chunk = raw.decode("utf-8", errors="ignore")
                    buf += chunk
                    result["lines"].append(chunk)
                    if "event: hello" in buf:
                        result["got_hello"] = True
                    if "event: chat" in buf:
                        result["got_chat"] = True
                        result["done"] = True
                        break

        t = threading.Thread(target=consume)
        t.start()
        # Give the consumer a moment to subscribe, then post.
        time.sleep(0.3)
        self.client.post(
            f"/api/streams/{sid}/chat",
            json={"user_id": u, "body": "live chat!"},
        )
        t.join(timeout=4.0)
        self.assertTrue(result.get("got_hello"))
        self.assertTrue(result.get("got_chat"))
        # The chat event payload should contain our message body.
        joined = "".join(result["lines"])
        self.assertIn("live chat!", joined)
        self.assertIn("event: chat", joined)


if __name__ == "__main__":
    unittest.main()
