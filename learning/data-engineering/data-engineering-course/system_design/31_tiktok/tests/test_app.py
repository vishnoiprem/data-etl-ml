"""HTTP-level tests for the TikTok service (Flask test client)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.cache import TTLCache  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402
from code.app import create_app  # noqa: E402
from code.service import TikTokService  # noqa: E402


class TikTokServiceAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        store = KeyValueStore(
            "test_tiktok_app",
            persist_path=os.path.join(self.tmpdir, "tiktok.json"),
        )
        self.foryou_cache = TTLCache(ttl_seconds=60, max_entries=200)
        self.svc = TikTokService(
            store=store, foryou_cache=self.foryou_cache
        )
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def _create_user(self, name: str) -> int:
        r = self.client.post("/api/users", json={"name": name})
        self.assertEqual(r.status_code, 201)
        return r.get_json()["user_id"]

    def _post_video(
        self,
        user_id: int,
        caption: str,
        duration: int = 15,
        tags=None,
    ) -> int:
        r = self.client.post(
            "/api/videos",
            json={
                "user_id": user_id,
                "caption": caption,
                "duration_s": duration,
                "tags": tags or [],
            },
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
        self.assertEqual(body["service"], "tiktok_service")
        self.assertIn("POST /api/users", body["endpoints"])
        self.assertIn("GET /api/foryou/<user_id>?limit=N", body["endpoints"])

    def test_metrics_endpoint(self):
        # Trigger a couple of calls so something is in the registry.
        self._create_user("m_alice")
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        text = r.get_data(as_text=True)
        self.assertIn("user_total", text)
        self.assertIn("video_post_total", text)

    # ---- user + video flows -----------------------------------------

    def test_create_user_and_post_video(self):
        uid = self._create_user("alice")
        vid = self._post_video(uid, "hi", 15, tags=["cat"])
        # And we can fetch the video metadata.
        r = self.client.get(f"/api/videos/{vid}")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["caption"], "hi")
        self.assertEqual(body["duration_s"], 15)
        self.assertEqual(body["tags"], ["cat"])
        self.assertEqual(body["views"], 0)

    def test_get_video_404(self):
        r = self.client.get("/api/videos/9999999")
        self.assertEqual(r.status_code, 404)

    def test_post_rejects_too_long_duration(self):
        uid = self._create_user("alice")
        r = self.client.post(
            "/api/videos",
            json={"user_id": uid, "caption": "too long", "duration_s": 601},
        )
        self.assertEqual(r.status_code, 400)

    def test_record_view_increments_and_avg(self):
        u = self._create_user("alice")
        v = self._post_video(u, "v", 20)
        # Two views, one 100%, one 50%.
        r1 = self.client.post(
            f"/api/videos/{v}/view",
            json={"user_id": u, "watch_pct": 100.0},
        )
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.post(
            f"/api/videos/{v}/view",
            json={"user_id": u, "watch_pct": 50.0},
        )
        self.assertEqual(r2.status_code, 200)
        body = r2.get_json()
        self.assertEqual(body["views"], 2)
        # Lifetime view count reflected in metadata.
        r = self.client.get(f"/api/videos/{v}")
        self.assertEqual(r.get_json()["views"], 2)

    def test_like_endpoint(self):
        u = self._create_user("alice")
        v = self._post_video(u, "v")
        r = self.client.post(
            f"/api/videos/{v}/like", json={"user_id": u}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["likes"], 1)

    # ---- For You feed -----------------------------------------------

    def test_foryou_endpoint_first_call_miss(self):
        u = self._create_user("alice")
        self._post_video(u, "v1", tags=["x"])
        self._post_video(u, "v2", tags=["x"])
        r = self.client.get(f"/api/foryou/{u}?limit=10")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["user_id"], u)
        self.assertEqual(body["limit"], 10)
        self.assertFalse(body["cached"])
        self.assertGreaterEqual(len(body["results"]), 2)

    def test_foryou_endpoint_second_call_cached(self):
        u = self._create_user("alice")
        self._post_video(u, "v1", tags=["x"])
        # First call populates the cache.
        self.client.get(f"/api/foryou/{u}?limit=10")
        # Second call within TTL is served from cache.
        r = self.client.get(f"/api/foryou/{u}?limit=10")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["cached"])

    def test_foryou_view_invalidates_cache(self):
        u1 = self._create_user("u1")
        u2 = self._create_user("u2")
        v = self._post_video(u1, "v", tags=["x"])
        # Populate u2's For You cache.
        self.client.get(f"/api/foryou/{u2}?limit=10")
        # u2 records a view — their cache should be invalidated.
        self.client.post(
            f"/api/videos/{v}/view",
            json={"user_id": u2, "watch_pct": 80.0},
        )
        r = self.client.get(f"/api/foryou/{u2}?limit=10")
        self.assertFalse(r.get_json()["cached"])


if __name__ == "__main__":
    unittest.main()
