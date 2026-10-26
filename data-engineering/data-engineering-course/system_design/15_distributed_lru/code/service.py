"""Distributed LRU Cache — core service.

Implements:
  * CacheNode        — one shard's LRU + counters.
  * DistributedLRU   — a fleet of nodes behind a consistent-hash ring.

On miss, the owning node increments a ``peer_fetches`` counter and
returns ``source="peer"``. A real cluster would gRPC to another node;
the simulation is the same code path minus the network call.
"""

from __future__ import annotations

import bisect
import hashlib
import threading
from dataclasses import dataclass, field
from typing import Optional

from common.cache import LRUCache

RING_SIZE = 1 << 32


def _hash(key: str) -> int:
    digest = hashlib.sha256(key.encode("utf-8")).digest()[:4]
    return int.from_bytes(digest, "big")


@dataclass
class CacheNode:
    node_id: str
    cache: LRUCache
    hits: int = 0
    misses: int = 0
    puts: int = 0
    evictions: int = 0
    peer_fetches: int = 0
    down: bool = False

    def stats(self) -> dict:
        s = self.cache.stats()
        s.update({
            "node_id": self.node_id,
            "puts": self.puts,
            "peer_fetches": self.peer_fetches,
            "hits": s["hits"],
            "misses": s["misses"],
            "evictions": s["evictions"],
            "down": self.down,
        })
        return s


class DistributedLRU:
    """Fleet of CacheNode behind a consistent-hash ring.

    >>> d = DistributedLRU(nodes=["n0","n1","n2"], capacity_per_node=100)
    >>> d.put("k", "v")
    'n0'  # owning node, whichever hashes first
    >>> d.get("k").value
    'v'
    """

    def __init__(
        self,
        nodes: Optional[list[str]] = None,
        capacity_per_node: int = 10_000,
        vnodes_per_node: int = 64,
    ):
        nodes = nodes or ["n0", "n1", "n2"]
        self.vnodes = max(1, vnodes_per_node)
        self._lock = threading.RLock()
        # Ring state
        self._positions: list[int] = []
        self._node_at: list[str] = []
        # Per-node state
        self._nodes: dict[str, CacheNode] = {}
        for n in nodes:
            self._add_node(n, capacity_per_node)

    # ---- node management ----------------------------------------------

    def _add_node(self, node_id: str, capacity: int) -> None:
        if node_id in self._nodes:
            return
        self._nodes[node_id] = CacheNode(
            node_id=node_id, cache=LRUCache(max_entries=capacity)
        )
        # Place V virtual nodes
        for i in range(self.vnodes):
            pos = _hash(f"{node_id}#vnode#{i}") % RING_SIZE
            idx = bisect.bisect_right(self._positions, pos)
            self._positions.insert(idx, pos)
            self._node_at.insert(idx, node_id)

    def add_node(self, node_id: str, capacity: int = 10_000) -> None:
        with self._lock:
            self._add_node(node_id, capacity)

    def remove_node(self, node_id: str) -> None:
        with self._lock:
            self._nodes.pop(node_id, None)
            i = 0
            while i < len(self._node_at):
                if self._node_at[i] == node_id:
                    self._positions.pop(i)
                    self._node_at.pop(i)
                else:
                    i += 1

    def fail_node(self, node_id: str) -> None:
        with self._lock:
            n = self._nodes.get(node_id)
            if n:
                n.down = True

    def revive_node(self, node_id: str) -> None:
        with self._lock:
            n = self._nodes.get(node_id)
            if n:
                n.down = False

    def nodes(self) -> list[str]:
        with self._lock:
            return sorted(self._nodes.keys())

    def node(self, node_id: str) -> Optional[CacheNode]:
        with self._lock:
            return self._nodes.get(node_id)

    def ring(self) -> list[dict]:
        with self._lock:
            return [
                {"position": p, "node": n}
                for p, n in zip(self._positions, self._node_at)
            ]

    # ---- routing ------------------------------------------------------

    def locate(self, key: str) -> Optional[str]:
        with self._lock:
            return self._owner(key)

    def _owner(self, key: str) -> Optional[str]:
        if not self._node_at:
            return None
        h = _hash(key) % RING_SIZE
        idx = bisect.bisect_right(self._positions, h)
        if idx == len(self._positions):
            idx = 0
        return self._node_at[idx]

    # ---- public API ---------------------------------------------------

    def put(self, key: str, value) -> dict:
        """Store ``value`` at the owning node. Returns owner info."""
        with self._lock:
            owner = self._owner(key)
            if owner is None or self._nodes[owner].down:
                return {"key": key, "node": owner, "stored": False, "reason": "no owner / down"}
            node = self._nodes[owner]
            node.cache.set(key, value)
            node.puts += 1
            return {"key": key, "node": owner, "stored": True}

    def get(self, key: str):
        """Return a ``GetResult`` with value, source (local/peer), owner."""
        owner = self.locate(key)
        if owner is None:
            return GetResult(key=key, value=None, owner=None, source="none", hit=False)
        with self._lock:
            node = self._nodes.get(owner)
            if node is None or node.down:
                return GetResult(key=key, value=None, owner=owner, source="peer", hit=False)
            v = node.cache.get(key)
            if v is None and not node.cache._data.get(key):
                # Miss — in a real cluster we'd fetch from peer.
                node.peer_fetches += 1
                return GetResult(key=key, value=None, owner=owner, source="peer", hit=False)
            node.hits += 1 if v is not None else 0
            return GetResult(key=key, value=v, owner=owner, source="local", hit=(v is not None))

    def delete(self, key: str) -> bool:
        with self._lock:
            owner = self._owner(key)
            if owner is None or self._nodes[owner].down:
                return False
            self._nodes[owner].cache.delete(key)
            return True

    # ---- stats --------------------------------------------------------

    def cluster_stats(self) -> dict:
        with self._lock:
            per_node = []
            total = {"puts": 0, "hits": 0, "misses": 0, "peer_fetches": 0, "size": 0}
            for n in sorted(self._nodes):
                ns = self._nodes[n].stats()
                per_node.append(ns)
                total["puts"] += ns["puts"]
                total["hits"] += ns["hits"]
                total["misses"] += ns["misses"]
                total["peer_fetches"] += ns["peer_fetches"]
                total["size"] += ns["size"]
            return {
                "nodes": self.nodes(),
                "vnodes_per_node": self.vnodes,
                "ring_size": len(self._positions),
                "per_node": per_node,
                "total": total,
            }


@dataclass
class GetResult:
    key: str
    value: object
    owner: Optional[str]
    source: str  # "local" | "peer" | "none"
    hit: bool

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "owner": self.owner,
            "source": self.source,
            "hit": self.hit,
        }
