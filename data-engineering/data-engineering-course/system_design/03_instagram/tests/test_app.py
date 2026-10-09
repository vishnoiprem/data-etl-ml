"""HTTP-level tests for the Instagram service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import InstagramService  # noqa: E402


class InstagramAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = InstagramService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_e2e(self):
        r = self.client.post("/api/users", json={"user_id": 1, "username": "u1", "name": "U1"})
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/users", json={"user_id": 2, "username": "u2", "name": "U2"})
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/follow", json={"follower_id": 1, "followee_id": 2})
        self.assertEqual(r.status_code, 200)
        r = self.client.post("/api/photos", json={"user_id": 2, "caption": "hi"})
        self.assertEqual(r.status_code, 201)
        photo_id = r.get_json()["photo_id"]
        r = self.client.get(f"/api/feed/1?limit=10")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.get_json()["photos"]), 1)
        r = self.client.get(f"/api/photos/{photo_id}")
        self.assertEqual(r.status_code, 200)

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
