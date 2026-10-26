"""HTTP tests for the WhatsApp service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import WhatsAppService  # noqa: E402


class WhatsAppAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = WhatsAppService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_e2e_group_conversation(self):
        r = self.client.post(
            "/api/groups",
            json={"name": "fam", "creator_id": 1, "members": [1, 2, 3]},
        )
        self.assertEqual(r.status_code, 201)
        gid = r.get_json()["group_id"]
        r = self.client.post(
            f"/api/groups/{gid}/messages",
            json={"sender_id": 1, "body": "hi all"},
        )
        self.assertEqual(r.status_code, 201)
        r = self.client.get(f"/api/groups/{gid}/messages")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["messages"]), 1)

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_member_add_and_remove(self):
        r = self.client.post(
            "/api/groups", json={"name": "g", "creator_id": 1, "members": [1]}
        )
        gid = r.get_json()["group_id"]
        r = self.client.post(
            f"/api/groups/{gid}/members", json={"user_id": 2}
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn(2, r.get_json()["members"])
        r = self.client.delete(f"/api/groups/{gid}/members/2")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(2, r.get_json()["members"])

    def test_user_groups_listing(self):
        self.client.post(
            "/api/groups", json={"name": "a", "creator_id": 1, "members": [1, 2]}
        )
        self.client.post(
            "/api/groups", json={"name": "b", "creator_id": 2, "members": [2, 3]}
        )
        r = self.client.get("/api/users/2/groups")
        self.assertEqual(r.status_code, 200)
        names = sorted(g["name"] for g in r.get_json()["groups"])
        self.assertEqual(names, ["a", "b"])

    def test_media_url_send(self):
        r = self.client.post(
            "/api/groups", json={"name": "g", "creator_id": 1, "members": [1]}
        )
        gid = r.get_json()["group_id"]
        r = self.client.post(
            f"/api/groups/{gid}/messages",
            json={"sender_id": 1, "body": "", "media_url": "https://x/y.jpg"},
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["media_url"], "https://x/y.jpg")


if __name__ == "__main__":
    unittest.main()
