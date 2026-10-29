"""HTTP tests for the Google-Docs service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import DocsService  # noqa: E402


class DocsAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = DocsService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_e2e_edit_snapshot(self):
        r = self.client.post("/api/docs", json={"title": "notes"})
        self.assertEqual(r.status_code, 201)
        did = r.get_json()["doc_id"]
        r = self.client.post(
            f"/api/docs/{did}/ops",
            json={"op": "insert", "pos": 0, "text": "Hello world"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["content"], "Hello world")
        r = self.client.get(f"/api/docs/{did}/snapshot")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["content"], "Hello world")

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_invalid_op_returns_400(self):
        r = self.client.post("/api/docs", json={"title": "x"})
        did = r.get_json()["doc_id"]
        r = self.client.post(
            f"/api/docs/{did}/ops",
            json={"op": "delete", "pos": 0, "n": 0},
        )
        self.assertEqual(r.status_code, 400)
        r = self.client.post(
            f"/api/docs/{did}/ops",
            json={"op": "insert", "pos": 0},  # missing text
        )
        self.assertEqual(r.status_code, 400)

    def test_ops_listing(self):
        r = self.client.post("/api/docs", json={"title": "x"})
        did = r.get_json()["doc_id"]
        self.client.post(
            f"/api/docs/{did}/ops",
            json={"op": "insert", "pos": 0, "text": "abc"},
        )
        self.client.post(
            f"/api/docs/{did}/ops",
            json={"op": "insert", "pos": 3, "text": "DEF"},
        )
        r = self.client.get(f"/api/docs/{did}/ops")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["ops"]), 2)

    def test_version_advances(self):
        r = self.client.post("/api/docs", json={"title": "x"})
        did = r.get_json()["doc_id"]
        self.client.post(
            f"/api/docs/{did}/ops",
            json={"op": "insert", "pos": 0, "text": "a"},
        )
        r = self.client.get(f"/api/docs/{did}")
        self.assertEqual(r.get_json()["version"], 1)


if __name__ == "__main__":
    unittest.main()
