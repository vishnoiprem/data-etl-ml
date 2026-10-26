"""HTTP-level tests for the Twitter / X service.

Drives the Flask app via ``test_client`` — exercises the full request
path through ``code/app.py`` into ``code/service.py``.
"""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import TwitterService, CELEB_THRESHOLD  # noqa: E402


class TwitterAppTests(unittest.TestCase):
    def setUp(self) -> None:
        # Fresh service + app per test.
        self.svc = TwitterService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    # --- 1. e2e: create users, follow, post, see in timeline -----------
    def test_e2e_post_and_timeline(self):
        r = self.client.post("/api/users", json={"user_id": 1, "username": "u1", "name": "U1"})
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/users", json={"user_id": 2, "username": "u2", "name": "U2"})
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/follow", json={"follower_id": 1, "followee_id": 2})
        self.assertEqual(r.status_code, 200)
        r = self.client.post("/api/tweets", json={"user_id": 2, "text": "hi"})
        self.assertEqual(r.status_code, 201)
        tweet_id = r.get_json()["tweet_id"]
        r = self.client.get("/api/timeline/1?limit=10")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        ids = [t["tweet_id"] for t in body["tweets"]]
        self.assertIn(tweet_id, ids)
        # and the single-tweet endpoint
        r = self.client.get(f"/api/tweets/{tweet_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["text"], "hi")

    # --- 2. health & metrics & index ------------------------------------
    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_metrics_endpoint(self):
        # Drive a couple of requests so the counters move.
        self.client.post("/api/users", json={"user_id": 1, "username": "u1", "name": "U1"})
        self.client.post("/api/tweets", json={"user_id": 1, "text": "hello"})
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("tweet_total", r.get_data(as_text=True))
        self.assertIn("tweet_latency_ms", r.get_data(as_text=True))

    def test_index_lists_endpoints(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["service"], "twitter")
        self.assertIn("POST /api/tweets", body["endpoints"])

    # --- 3. retweet via HTTP --------------------------------------------
    def test_retweet_via_http(self):
        self.client.post("/api/users", json={"user_id": 1, "username": "u1", "name": "U1"})
        self.client.post("/api/users", json={"user_id": 2, "username": "u2", "name": "U2"})
        r = self.client.post("/api/tweets", json={"user_id": 1, "text": "original"})
        self.assertEqual(r.status_code, 201)
        original_id = r.get_json()["tweet_id"]
        r = self.client.post("/api/tweets", json={
            "user_id": 2, "text": "RT", "retweet_of": original_id
        })
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertEqual(body["retweet_of"], original_id)
        self.assertEqual(body["retweet_of_user"], 1)

    # --- 4. like + not-found handling -----------------------------------
    def test_like_and_404(self):
        self.client.post("/api/users", json={"user_id": 1, "username": "u1", "name": "U1"})
        r = self.client.post("/api/tweets", json={"user_id": 1, "text": "like me"})
        self.assertEqual(r.status_code, 201)
        tid = r.get_json()["tweet_id"]
        r = self.client.post(f"/api/tweets/{tid}/like")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["likes"], 1)
        # 404 path.
        r = self.client.post("/api/tweets/9999999999/like")
        self.assertEqual(r.status_code, 404)
        r = self.client.get("/api/tweets/9999999999")
        self.assertEqual(r.status_code, 404)

    # --- bonus: celebrity hybrid via HTTP -------------------------------
    def test_celebrity_tweet_via_http(self):
        # Build a celeb and a follower.
        self.client.post("/api/users", json={"user_id": 7, "username": "c", "name": "C"})
        self.client.post("/api/users", json={"user_id": 8, "username": "f", "name": "F"})
        # Promote user 7 to celeb by directly editing the user record.
        u = self.svc.get_user(7)
        u.followers_count = CELEB_THRESHOLD + 1
        self.svc.users.set(f"user:7", u.to_dict())
        # F follows C.
        self.client.post("/api/follow", json={"follower_id": 8, "followee_id": 7})
        # C posts a tweet.
        r = self.client.post("/api/tweets", json={"user_id": 7, "text": "from celeb"})
        self.assertEqual(r.status_code, 201)
        tid = r.get_json()["tweet_id"]
        # F's timeline should contain it (via the celeb pull).
        r = self.client.get("/api/timeline/8?limit=10")
        self.assertEqual(r.status_code, 200)
        ids = [t["tweet_id"] for t in r.get_json()["tweets"]]
        self.assertIn(tid, ids)


if __name__ == "__main__":
    unittest.main()