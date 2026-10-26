"""HTTP-level tests for the Reddit service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import RedditService  # noqa: E402


class RedditAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = RedditService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_e2e(self):
        r = self.client.post("/api/users", json={"user_id": 1, "username": "a"})
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/subreddits", json={"name": "py", "description": ""})
        self.assertEqual(r.status_code, 201)
        sid = r.get_json()["subreddit_id"]
        r = self.client.post(f"/api/users/1/subscribe", json={"subreddit_id": sid})
        self.assertEqual(r.status_code, 200)
        r = self.client.post(f"/api/subreddits/{sid}/posts",
                             json={"user_id": 1, "title": "hi", "body": ""})
        self.assertEqual(r.status_code, 201)
        pid = r.get_json()["post_id"]
        r = self.client.post(f"/api/posts/{pid}/vote",
                             json={"user_id": 1, "direction": 1})
        self.assertEqual(r.status_code, 200)
        r = self.client.get(f"/api/subreddits/{sid}?sort=hot")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.get_json()["posts"]), 1)

    def test_home(self):
        r = self.client.get("/api/users/1/home")
        self.assertEqual(r.status_code, 200)
        self.assertIn("feed", r.get_json())

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
