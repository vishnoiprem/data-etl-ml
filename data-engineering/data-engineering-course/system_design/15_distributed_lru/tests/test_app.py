"""HTTP-level tests for the distributed LRU (Flask test client)."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import DistributedLRU  # noqa: E402


class DistributedLRUAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.d = DistributedLRU(
            nodes=["n0", "n1", "n2"],
            capacity_per_node=100,
            vnodes_per_node=20,
        )
        self.app = create_app(self.d)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_put_then_get(self):
        r1 = self.client.put("/api/cache/hello", json={"x": 1})
        self.assertEqual(r1.status_code, 200)
        body = r1.get_json()
        self.assertIn(body["node"], {"n0", "n1", "n2"})

        r2 = self.client.get("/api/cache/hello")
        self.assertEqual(r2.status_code, 200)
        body = r2.get_json()
        self.assertEqual(body["value"], {"x": 1})
        self.assertEqual(body["source"], "local")

    def test_get_miss_returns_404_with_peer(self):
        r = self.client.get("/api/cache/missing")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["source"], "peer")

    def test_delete(self):
        self.client.put("/api/cache/k", json={"v": 1})
        r = self.client.delete("/api/cache/k")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["removed"])

    def test_nodes_endpoint(self):
        r = self.client.get("/api/nodes")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(set(body["nodes"]), {"n0", "n1", "n2"})
        self.assertEqual(len(body["per_node"]), 3)

    def test_locate(self):
        r = self.client.get("/api/locate/mykey")
        self.assertEqual(r.status_code, 200)
        self.assertIn(r.get_json()["owner"], {"n0", "n1", "n2"})

    def test_fail_and_revive(self):
        r = self.client.post("/api/nodes/n0/fail")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(any(n["down"] for n in r.get_json()["per_node"] if n["node_id"] == "n0"))
        r = self.client.post("/api/nodes/n0/revive")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(any(n["down"] for n in r.get_json()["per_node"] if n["node_id"] == "n0"))

    def test_metrics_endpoint(self):
        self.client.put("/api/cache/k", json={"v": 1})
        self.client.get("/api/cache/k")
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        text = r.get_data(as_text=True)
        self.assertIn("put_total", text)
        self.assertIn("local_hits", text)

    def test_index(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("cluster", r.get_json())


if __name__ == "__main__":
    unittest.main()
