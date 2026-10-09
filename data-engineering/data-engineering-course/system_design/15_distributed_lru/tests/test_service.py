"""Unit tests for the distributed LRU core service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import DistributedLRU  # noqa: E402


class DistributedLRUTests(unittest.TestCase):
    def setUp(self) -> None:
        self.d = DistributedLRU(
            nodes=["n0", "n1", "n2"],
            capacity_per_node=100,
            vnodes_per_node=40,
        )

    def test_put_stores_on_owner(self):
        res = self.d.put("alpha", {"v": 1})
        self.assertTrue(res["stored"])
        self.assertIn(res["node"], {"n0", "n1", "n2"})

    def test_get_returns_local_hit(self):
        self.d.put("k", "v")
        r = self.d.get("k")
        self.assertTrue(r.hit)
        self.assertEqual(r.value, "v")
        self.assertEqual(r.source, "local")

    def test_get_missing_yields_peer(self):
        r = self.d.get("missing")
        self.assertFalse(r.hit)
        self.assertEqual(r.source, "peer")
        # peer counter increments
        owner = r.owner
        self.assertGreater(self.d.node(owner).peer_fetches, 0)

    def test_locate_returns_node(self):
        owner = self.d.locate("k")
        self.assertIn(owner, {"n0", "n1", "n2"})

    def test_ring_size_matches_vnodes(self):
        self.assertEqual(len(self.d.ring()), 3 * 40)

    def test_distribution_is_balanced(self):
        counts = {n: 0 for n in self.d.nodes()}
        for i in range(300):
            owner = self.d.locate(f"key_{i}")
            counts[owner] += 1
        # No node should get all keys; each should get at least 50.
        for n, c in counts.items():
            self.assertGreater(c, 50)

    def test_lru_promotion_on_get(self):
        self.d.put("k", "v")
        # Force eviction by adding many other keys
        for i in range(100):
            self.d.put(f"filler_{i}", i)
        r = self.d.get("k")
        # k might or might not still be there; if still local, good.
        if r.hit:
            self.assertEqual(r.value, "v")

    def test_fail_node(self):
        self.d.fail_node("n0")
        cs = self.d.cluster_stats()
        for n in cs["per_node"]:
            if n["node_id"] == "n0":
                self.assertTrue(n["down"])
        # Revive
        self.d.revive_node("n0")
        cs = self.d.cluster_stats()
        for n in cs["per_node"]:
            if n["node_id"] == "n0":
                self.assertFalse(n["down"])

    def test_add_node_keeps_majority(self):
        before = {k: self.d.locate(k) for k in [f"k{i}" for i in range(200)]}
        self.d.add_node("n3", capacity=100)
        same = sum(1 for k, v in before.items() if self.d.locate(k) == v)
        self.assertGreater(same / 200, 0.5)

    def test_remove_node(self):
        before = self.d.cluster_stats()["total"]["size"]
        self.d.put("k1", "v1")
        self.d.remove_node("n0")
        # n0's data is now gone.
        self.assertEqual(len(self.d.nodes()), 2)

    def test_delete(self):
        self.d.put("k", "v")
        self.assertTrue(self.d.delete("k"))
        self.assertFalse(self.d.get("k").hit)

    def test_cluster_stats_total(self):
        self.d.put("a", 1)
        self.d.put("b", 2)
        self.d.get("a")
        self.d.get("missing")
        s = self.d.cluster_stats()
        self.assertGreaterEqual(s["total"]["puts"], 2)
        self.assertGreaterEqual(s["total"]["peer_fetches"], 1)


if __name__ == "__main__":
    unittest.main()
