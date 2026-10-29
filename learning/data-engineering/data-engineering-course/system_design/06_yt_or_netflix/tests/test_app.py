"""HTTP-level tests for the video service (Flask test client)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.app import create_app  # noqa: E402
from code.service import VideoService  # noqa: E402


class VideoServiceAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        store = KeyValueStore(
            "test_vs_app", persist_path=os.path.join(self.tmpdir, "vs.json")
        )
        self.svc = VideoService(store=store, window_seconds=60)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def _create_user(self, name: str) -> int:
        r = self.client.post("/api/users", json={"name": name})
        self.assertEqual(r.status_code, 201)
        return r.get_json()["user_id"]

    def _upload_video(self, user_id: int, title: str, duration: int = 100) -> int:
        r = self.client.post(
            "/api/videos",
            json={"user_id": user_id, "title": title, "duration_s": duration},
        )
        self.assertEqual(r.status_code, 201)
        return r.get_json()["video_id"]

    # ---- health + index + metrics -----------------------------------

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_index_lists_endpoints(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["service"], "video_service")
        self.assertIn("POST /api/users", body["endpoints"])
        self.assertIn("GET /api/trending?limit=N", body["endpoints"])

    def test_metrics_endpoint(self):
        # Trigger a couple of calls so something is in the registry.
        self._create_user("m_alice")
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        text = r.get_data(as_text=True)
        self.assertIn("upload_total", text)
        self.assertIn("view_total", text)

    # ---- user + video flows -----------------------------------------

    def test_create_user_and_upload_video(self):
        uid = self._create_user("alice")
        vid = self._upload_video(uid, "lesson 1", 600)
        # And we can fetch the video metadata.
        r = self.client.get(f"/api/videos/{vid}")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["title"], "lesson 1")
        self.assertEqual(body["duration_s"], 600)
        self.assertEqual(body["views"], 0)

    def test_get_video_404(self):
        r = self.client.get("/api/videos/9999999")
        self.assertEqual(r.status_code, 404)

    def test_record_view_then_trending(self):
        u1 = self._create_user("alice")
        u2 = self._create_user("bob")
        v_pop = self._upload_video(u1, "popular")
        v_other = self._upload_video(u1, "other")
        # Multiple distinct users watch v_pop; only one watches v_other.
        for _ in range(3):
            u = self._create_user("viewer")
            self.client.post(
                f"/api/videos/{v_pop}/view", json={"user_id": u}
            )
        self.client.post(
            f"/api/videos/{v_other}/view", json={"user_id": u2}
        )
        r = self.client.get("/api/trending?limit=5")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        results = body["results"]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["video_id"], v_pop)
        self.assertEqual(results[0]["views_in_window"], 3)

    def test_record_view_increments_lifetime(self):
        u = self._create_user("alice")
        v = self._upload_video(u, "v")
        for _ in range(2):
            r = self.client.post(
                f"/api/videos/{v}/view", json={"user_id": u}
            )
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.get_json()["recorded"])
        # And lifetime view count is reflected in metadata.
        r = self.client.get(f"/api/videos/{v}")
        self.assertEqual(r.get_json()["views"], 2)

    def test_recommend_endpoint(self):
        alice = self._create_user("alice")
        bob = self._create_user("bob")
        v1 = self._upload_video(alice, "v1")
        v2 = self._upload_video(alice, "v2")
        # Both users watch v1; bob also watches v2.
        self.client.post(f"/api/videos/{v1}/view", json={"user_id": alice})
        self.client.post(f"/api/videos/{v1}/view", json={"user_id": bob})
        self.client.post(f"/api/videos/{v2}/view", json={"user_id": bob})
        r = self.client.get(f"/api/recommend/{alice}?limit=5")
        self.assertEqual(r.status_code, 200)
        ids = {item["video_id"] for item in r.get_json()["results"]}
        self.assertIn(v2, ids)
        self.assertNotIn(v1, ids)


if __name__ == "__main__":
    unittest.main()
