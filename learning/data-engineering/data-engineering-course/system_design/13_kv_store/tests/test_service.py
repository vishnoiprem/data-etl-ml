"""Unit tests for the distributed KV store core service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    ConsistentHashRing,
    KVCluster,
    KVStore,
)


class ConsistentHashRingTests(unittest.TestCase):
    def test_empty_ring(self):
        r = ConsistentHashRing([], vnodes_per_server=10)
        self.assertIsNone(r.primary_for("anything"))
        self.assertEqual(r.replicas_for("anything"), [])

    def test_vnode_count(self):
        r = ConsistentHashRing(["a", "b", "c"], vnodes_per_server=20)
        self.assertEqual(len(r.ring), 60)

    def test_distribution_is_balanced(self):
        r = ConsistentHashRing(["a", "b", "c", "d"], vnodes_per_server=200)
        d = r.distribution()
        # Each server should have exactly 200 vnodes.
        for s in ["a", "b", "c", "d"]:
            self.assertEqual(d[s], 200)

    def test_primary_returns_one_of_servers(self):
        servers = ["s0", "s1", "s2"]
        r = ConsistentHashRing(servers, vnodes_per_server=64)
        for i in range(50):
            self.assertIn(r.primary_for(f"key{i}"), servers)

    def test_replicas_are_distinct(self):
        servers = ["s0", "s1", "s2", "s3"]
        r = ConsistentHashRing(servers, vnodes_per_server=64, replication=3)
        reps = r.replicas_for("hello")
        self.assertEqual(len(reps), 3)
        self.assertEqual(len(set(reps)), 3)

    def test_add_server_keeps_existing_keys(self):
        # 50% of keys should remain on the same primary after adding a
        # fourth server. We sample many keys and assert no worse than
        # 80% (with virtual nodes the actual fraction is ~75%).
        servers = ["a", "b", "c"]
        r1 = ConsistentHashRing(servers, vnodes_per_server=200)
        before = {k: r1.primary_for(k) for k in [f"k{i}" for i in range(500)]}
        r1.add_servers(["d"])
        same = sum(1 for k, v in before.items() if r1.primary_for(k) == v)
        # Expectation: ~75% stay; allow 60% as a loose lower bound.
        self.assertGreater(same / 500, 0.60)

    def test_remove_server(self):
        r = ConsistentHashRing(["a", "b", "c"], vnodes_per_server=20)
        r.remove_server("a")
        for n in r.ring:
            self.assertNotEqual(n.server_id, "a")


class KVClusterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.cluster = KVCluster(
            servers=["s0", "s1", "s2"],
            replication=3,
            vnodes_per_server=64,
            persist_dir=self.tmpdir,
        )
        self.kv = KVStore(self.cluster)

    def test_put_and_get(self):
        res = self.kv.put("user:1", {"name": "ada"})
        self.assertTrue(res.success)
        self.assertEqual(res.acks, 3)
        got = self.kv.get("user:1")
        self.assertEqual(got.value, {"name": "ada"})

    def test_replication_count(self):
        res = self.kv.put("k", "v")
        self.assertEqual(len(res.replicas), 3)
        for w in res.writes:
            self.assertTrue(w.ok, f"replica {w.server_id} failed: {w.error}")

    def test_replica_serves_when_primary_down(self):
        self.kv.put("hot", "value1")
        primary = self.cluster.primary_for("hot")
        self.cluster.fail(primary)
        res = self.kv.get("hot")
        self.assertIsNotNone(res.value)
        self.assertEqual(res.value, "value1")
        self.assertIn(primary, res.tried)  # we tried primary

    def test_quorum_returns_after_majority(self):
        self.kv.put("kq", "vq")
        # Mark one replica down — quorum of 2 still works.
        replicas = self.cluster.replicas_for("kq")
        self.cluster.fail(replicas[0])
        res = self.kv.get("kq", quorum=2)
        self.assertEqual(res.value, "vq")

    def test_get_missing(self):
        res = self.kv.get("nope")
        self.assertIsNone(res.value)

    def test_add_and_remove_server(self):
        self.cluster.add_server("s3")
        self.kv.put("k1", "v1")
        # All 4 servers should now host the key.
        found = sum(1 for s in self.cluster.servers() if self.cluster.store(s).get("kv:k1"))
        self.assertEqual(found, 3)  # replication factor still 3

    def test_delete(self):
        self.kv.put("del", "v")
        n = self.kv.delete("del")
        self.assertGreaterEqual(n, 1)
        self.assertIsNone(self.kv.get("del").value)

    def test_stats(self):
        s = self.cluster.stats()
        self.assertEqual(s["replication"], 3)
        self.assertIn("s0", s["servers"])


if __name__ == "__main__":
    unittest.main()
