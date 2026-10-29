"""HTTP tests for the Slack service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import SlackService  # noqa: E402


class SlackAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = SlackService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_e2e_post_and_search(self):
        r = self.client.post("/api/workspaces", json={"name": "acme"})
        self.assertEqual(r.status_code, 201)
        wid = r.get_json()["workspace_id"]
        r = self.client.post(
            f"/api/workspaces/{wid}/channels",
            json={"name": "general", "creator_id": 1},
        )
        self.assertEqual(r.status_code, 201)
        cid = r.get_json()["channel_id"]
        r = self.client.post(
            f"/api/channels/{cid}/messages",
            json={"user_id": 1, "body": "deploy pipeline broken"},
        )
        self.assertEqual(r.status_code, 201)
        r = self.client.get("/api/search?q=pipeline")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["results"]), 1)

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_thread_endpoint(self):
        r = self.client.post("/api/workspaces", json={"name": "acme"})
        wid = r.get_json()["workspace_id"]
        r = self.client.post(
            f"/api/workspaces/{wid}/channels",
            json={"name": "general", "creator_id": 1},
        )
        cid = r.get_json()["channel_id"]
        r = self.client.post(
            f"/api/channels/{cid}/messages",
            json={"user_id": 1, "body": "parent"},
        )
        parent_id = r.get_json()["message_id"]
        self.client.post(
            f"/api/channels/{cid}/messages",
            json={"user_id": 2, "body": "reply 1", "thread_to": parent_id},
        )
        r = self.client.get(f"/api/channels/{cid}/threads/{parent_id}")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(len(body["replies"]), 1)
        self.assertEqual(body["parent"]["message_id"], parent_id)

    def test_mentions_endpoint(self):
        r = self.client.post("/api/workspaces", json={"name": "acme"})
        wid = r.get_json()["workspace_id"]
        r = self.client.post(
            f"/api/workspaces/{wid}/channels",
            json={"name": "general", "creator_id": 1},
        )
        cid = r.get_json()["channel_id"]
        self.client.post(
            f"/api/channels/{cid}/messages",
            json={"user_id": 1, "body": "hi @42"},
        )
        r = self.client.get("/api/users/42/mentions")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["mentions"]), 1)

    def test_list_workspace_channels(self):
        r = self.client.post("/api/workspaces", json={"name": "w"})
        wid = r.get_json()["workspace_id"]
        self.client.post(
            f"/api/workspaces/{wid}/channels",
            json={"name": "a", "creator_id": 1},
        )
        self.client.post(
            f"/api/workspaces/{wid}/channels",
            json={"name": "b", "creator_id": 1},
        )
        r = self.client.get(f"/api/workspaces/{wid}/channels")
        self.assertEqual(r.status_code, 200)
        names = sorted(c["name"] for c in r.get_json()["channels"])
        self.assertEqual(names, ["a", "b"])


if __name__ == "__main__":
    unittest.main()
