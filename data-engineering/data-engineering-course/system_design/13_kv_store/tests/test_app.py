"""HTTP-level tests for the distributed KV store (Flask test client)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import KVCluster, KVStore  # noqa: E402


class KVStoreAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        cluster = KVCluster(
            servers=["s0", "s1", "s2"],
            replication=3,
            vnodes_per_server=32,
            persist_dir=self.tmpdir,
        )
        self.svc = KVStore(cluster)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_put_and_get(self):
        r1 = self.client.post("/api/put", json={"key": "alpha", "value": {"x": 1}})
        self.assertEqual(r1.status_code, 200)
        body = r1.get_json()
        self.assertEqual(body["acks"], 3)
        self.assertEqual(len(body["replicas"]), 3)

        r2 = self.client.get("/api/get/alpha")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["value"], {"x": 1})

    def test_put_requires_key(self):
        r = self.client.post("/api/put", json={"value": "v"})
        self.assertEqual(r.status_code, 400)

    def test_get_missing(self):
        r = self.client.get("/api/get/nope")
        self.assertEqual(r.status_code, 404)

    def test_cluster_configure(self):
        r = self.client.post(
            "/api/cluster/servers",
            json={"servers": ["a", "b", "c", "d"], "replication": 2, "vnodes": 16},
        )
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["replication"], 2)
        self.assertEqual(set(body["servers"]), {"a", "b", "c", "d"})

    def test_fail_and_revive(self):
        self.client.post("/api/put", json={"key": "k1", "value": "v1"})
        # Find primary
        primary = self.svc.cluster.primary_for("k1")
        r = self.client.post(f"/api/cluster/servers/{primary}/fail")
        self.assertEqual(r.status_code, 200)
        self.assertIn(primary, r.get_json()["down"])
        # Get should still work via replica
        r2 = self.client.get("/api/get/k1")
        self.assertEqual(r2.status_code, 200)
        # Revive
        r3 = self.client.post(f"/api/cluster/servers/{primary}/revive")
        self.assertNotIn(primary, r3.get_json()["down"])

    def test_metrics_endpoint(self):
        self.client.post("/api/put", json={"key": "k", "value": "v"})
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("put_total", r.get_data(as_text=True))

    def test_index(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("endpoints", r.get_json())


if __name__ == "__main__":
    unittest.main()
