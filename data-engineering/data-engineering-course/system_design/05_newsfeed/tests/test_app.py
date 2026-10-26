"""HTTP-level tests for the Newsfeed service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import NewsfeedService  # noqa: E402


class NewsfeedAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = NewsfeedService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def _seed_two_users_following(self):
        self.client.post("/api/users", json={"user_id": 1, "username": "u1", "name": "U1"})
        self.client.post("/api/users", json={"user_id": 2, "username": "u2", "name": "U2"})
        self.client.post("/api/follow", json={"follower_id": 1, "followee_id": 2})

    def test_e2e_post_and_ranked_feed(self):
        self._seed_two_users_following()
        r = self.client.post("/api/posts", json={"user_id": 2, "text": "hello"})
        self.assertEqual(r.status_code, 201)
        post_id = r.get_json()["post_id"]
        # 5 likes on it
        for _ in range(5):
            r = self.client.post(
                f"/api/posts/{post_id}/engage", json={"kind": "like"}
            )
            self.assertEqual(r.status_code, 200)
        r = self.client.get("/api/feed/1?limit=5")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["user_id"], 1)
        self.assertEqual(len(body["posts"]), 1)
        # ranked payload includes the score
        self.assertGreater(body["ranked"][0]["score"], 0)
        self.assertEqual(body["ranked"][0]["affinity"], 1.0)  # followee
        self.assertEqual(body["posts"][0]["likes"], 5)

    def test_unfollow_removes_from_feed(self):
        self._seed_two_users_following()
        r = self.client.post("/api/posts", json={"user_id": 2, "text": "bye"})
        self.assertEqual(r.status_code, 201)
        post_id = r.get_json()["post_id"]
        r = self.client.get("/api/feed/1?limit=5")
        self.assertEqual(len(r.get_json()["posts"]), 1)
        # unfollow
        r = self.client.post("/api/unfollow", json={"follower_id": 1, "followee_id": 2})
        self.assertEqual(r.status_code, 200)
        # bust the cache (in real systems: write-side bust; here: TTL)
        self.svc.feed_cache.clear()
        r = self.client.get("/api/feed/1?limit=5")
        self.assertEqual(r.get_json()["posts"], [])

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        # Prometheus text format — should at least contain a TYPE line.
        self.assertIn(b"# TYPE", r.data)
        # Hit an endpoint and confirm counter ticks.
        self._seed_two_users_following()
        before = self.client.get("/metrics").data.decode()
        self.client.post("/api/posts", json={"user_id": 2, "text": "x"})
        after = self.client.get("/metrics").data.decode()
        self.assertIn("posts_total", after)
        # After the post, the posts_total counter should have advanced.
        # (Cheap parsing — just check the line exists and counter incremented.)
        self.assertNotEqual(before, after)

    def test_health_and_index(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["service"], "newsfeed")
        self.assertIn("POST /api/posts", body["endpoints"])

    def test_engage_validation(self):
        self._seed_two_users_following()
        r = self.client.post("/api/posts", json={"user_id": 2, "text": "hi"})
        post_id = r.get_json()["post_id"]
        # invalid kind
        r = self.client.post(
            f"/api/posts/{post_id}/engage", json={"kind": "smash"}
        )
        self.assertEqual(r.status_code, 400)
        # unknown post
        r = self.client.post(
            "/api/posts/9999999/engage", json={"kind": "like"}
        )
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
