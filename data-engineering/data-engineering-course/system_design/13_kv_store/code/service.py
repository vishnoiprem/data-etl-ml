"""Distributed Key-Value Store — core service.

Implements:
  * ConsistentHashRing — sorted ring with N virtual nodes per server.
  * KVCluster — multiple in-process "servers" + replication on writes.
  * KVStore — high-level facade: put(key, value), get(key, quorum=...).

The "servers" are in-process KeyValueStore instances. In production each
would be a separate process/machine reached over gRPC. The point of this
module is the *ring mechanics* and *replication protocol*, not the wire.
"""

from __future__ import annotations

import bisect
import hashlib
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from common.storage import KeyValueStore

# 32-bit hash space — matches MD5/SHA-1 truncation used by classic papers.
RING_SIZE = 1 << 32


def _hash_key(key: str) -> int:
    """Stable 32-bit hash for ``key``. SHA-256 truncated."""
    digest = hashlib.sha256(key.encode("utf-8")).digest()[:4]
    return int.from_bytes(digest, "big")


@dataclass
class RingNode:
    position: int
    server_id: str


class ConsistentHashRing:
    """A consistent-hash ring with virtual nodes.

    >>> r = ConsistentHashRing(["s0", "s1", "s2"], vnodes_per_server=10)
    >>> r.primary_for("hello")
    's0'  # depends on hash
    >>> len(r.ring) == 3 * 10
    True
    """

    def __init__(
        self,
        servers: list[str],
        vnodes_per_server: int = 128,
        replication: int = 3,
    ):
        self.vnodes = max(1, vnodes_per_server)
        self.replication = max(1, replication)
        self._lock = threading.RLock()
        # Sorted list of positions, parallel list of server ids.
        self._positions: list[int] = []
        self._server_at: list[str] = []
        self.add_servers(servers)

    # ---- server management --------------------------------------------

    def add_servers(self, servers: list[str]) -> None:
        with self._lock:
            for s in servers:
                self._add(s)

    def _add(self, server_id: str) -> None:
        # Add V virtual nodes, each with a unique suffix.
        for i in range(self.vnodes):
            pos = _hash_key(f"{server_id}#vnode#{i}") % RING_SIZE
            idx = bisect.bisect_right(self._positions, pos)
            self._positions.insert(idx, pos)
            self._server_at.insert(idx, server_id)

    def remove_server(self, server_id: str) -> None:
        with self._lock:
            i = 0
            while i < len(self._server_at):
                if self._server_at[i] == server_id:
                    self._positions.pop(i)
                    self._server_at.pop(i)
                else:
                    i += 1

    def servers(self) -> list[str]:
        with self._lock:
            return sorted(set(self._server_at))

    @property
    def ring(self) -> list[RingNode]:
        with self._lock:
            return [RingNode(p, s) for p, s in zip(self._positions, self._server_at)]

    def distribution(self) -> dict[str, int]:
        """How many vnodes each server holds. Useful for skew inspection."""
        with self._lock:
            out: dict[str, int] = {}
            for s in self._server_at:
                out[s] = out.get(s, 0) + 1
            return out

    # ---- key → server mapping ----------------------------------------

    def primary_for(self, key: str) -> Optional[str]:
        with self._lock:
            if not self._server_at:
                return None
            idx = self._index_for(key)
            return self._server_at[idx]

    def replicas_for(self, key: str, n: Optional[int] = None) -> list[str]:
        """Return up to ``n`` distinct servers walking clockwise from ``key``."""
        with self._lock:
            if not self._server_at:
                return []
            n = n or self.replication
            n = min(n, len(set(self._server_at)))
            start = self._index_for(key)
            seen: set[str] = set()
            result: list[str] = []
            for i in range(len(self._server_at)):
                s = self._server_at[(start + i) % len(self._server_at)]
                if s in seen:
                    continue
                seen.add(s)
                result.append(s)
                if len(result) >= n:
                    break
            return result

    def _index_for(self, key: str) -> int:
        h = _hash_key(key) % RING_SIZE
        idx = bisect.bisect_right(self._positions, h)
        if idx == len(self._positions):
            idx = 0
        return idx


# ---------------------------------------------------------------------------
# Cluster
# ---------------------------------------------------------------------------


@dataclass
class ReplicaWrite:
    server_id: str
    ok: bool
    error: Optional[str] = None
    ts: float = field(default_factory=time.time)


@dataclass
class PutResult:
    key: str
    primary: str
    replicas: list[str]
    writes: list[ReplicaWrite]
    acks: int
    total: int

    @property
    def success(self) -> bool:
        return self.acks > 0


@dataclass
class GetResult:
    key: str
    value: Optional[object]
    source: Optional[str] = None
    replica_hits: int = 0
    tried: list[str] = field(default_factory=list)


class KVCluster:
    """A simulated cluster of in-memory KV servers.

    Each "server" is a `KeyValueStore`. The cluster owns the ring and
    routes writes/reads to the right set of servers.
    """

    def __init__(
        self,
        servers: Optional[list[str]] = None,
        replication: int = 3,
        vnodes_per_server: int = 128,
        persist_dir: Optional[str] = None,
    ):
        servers = servers or ["s0", "s1", "s2"]
        self.replication = replication
        self.vnodes = vnodes_per_server
        self._lock = threading.RLock()
        self._stores: dict[str, KeyValueStore] = {}
        self._down: set[str] = set()  # simulated failures

        for s in servers:
            persist = None
            if persist_dir:
                import os
                persist = os.path.join(persist_dir, f"{s}.json")
            self._stores[s] = KeyValueStore(f"kv_{s}", persist_path=persist)

        self.ring = ConsistentHashRing(
            servers, vnodes_per_server=vnodes_per_server, replication=replication
        )

    # ---- cluster management -------------------------------------------

    def add_server(self, server_id: str) -> None:
        with self._lock:
            if server_id in self._stores:
                return
            self._stores[server_id] = KeyValueStore(f"kv_{server_id}")
            self.ring.add_servers([server_id])

    def remove_server(self, server_id: str) -> None:
        with self._lock:
            self._stores.pop(server_id, None)
            self._down.discard(server_id)
            self.ring.remove_server(server_id)

    def servers(self) -> list[str]:
        with self._lock:
            return list(self._stores.keys())

    def is_up(self, server_id: str) -> bool:
        with self._lock:
            return server_id in self._stores and server_id not in self._down

    def fail(self, server_id: str) -> None:
        with self._lock:
            self._down.add(server_id)

    def revive(self, server_id: str) -> None:
        with self._lock:
            self._down.discard(server_id)

    def store(self, server_id: str) -> Optional[KeyValueStore]:
        with self._lock:
            return self._stores.get(server_id)

    # ---- routing ------------------------------------------------------

    def primary_for(self, key: str) -> Optional[str]:
        return self.ring.primary_for(key)

    def replicas_for(self, key: str) -> list[str]:
        return self.ring.replicas_for(key)

    # ---- write path ---------------------------------------------------

    def put(self, key: str, value, require_acks: int = 1) -> PutResult:
        """Write ``key=value`` to primary + replicas.

        ``require_acks`` defaults to 1 (best-effort). For quorum, pass
        ``replication // 2 + 1``.
        """
        with self._lock:
            primary = self.primary_for(key)
            if primary is None:
                return PutResult(key, "", [], [], 0, 0)
            replica_set = self.replicas_for(key)
            writes: list[ReplicaWrite] = []
            for s in replica_set:
                if not self.is_up(s):
                    writes.append(ReplicaWrite(s, False, "down"))
                    continue
                try:
                    self._stores[s].set(self._k(key), value)
                    writes.append(ReplicaWrite(s, True))
                except Exception as e:  # pragma: no cover - defensive
                    writes.append(ReplicaWrite(s, False, str(e)))
            acks = sum(1 for w in writes if w.ok)
            return PutResult(
                key=key,
                primary=primary,
                replicas=replica_set,
                writes=writes,
                acks=acks,
                total=len(replica_set),
            )

    # ---- read path ----------------------------------------------------

    def get(self, key: str, quorum: int = 1) -> GetResult:
        """Read ``key``. Tries primary first, then replicas.

        ``quorum`` controls how many replicas must agree before returning
        a value. Quorum > 1 is useful for divergent-replica reconciliation.
        """
        with self._lock:
            replica_set = self.replicas_for(key)
            tried: list[str] = []
            value = None
            source = None
            hits = 0
            counts: dict[str, int] = {}
            for s in replica_set:
                if not self.is_up(s):
                    continue
                tried.append(s)
                v = self._stores[s].get(self._k(key), default=None)
                if v is not None:
                    hits += 1
                    key_str = str(v)
                    counts[key_str] = counts.get(key_str, 0) + 1
                    if source is None:
                        source = s
                        value = v
                    if quorum <= hits:
                        break
            if hits == 0:
                return GetResult(key=key, value=None, tried=tried)
            return GetResult(
                key=key,
                value=value,
                source=source,
                replica_hits=hits,
                tried=tried,
            )

    def delete(self, key: str) -> int:
        with self._lock:
            n = 0
            for s in self.replicas_for(key):
                if self.is_up(s) and self._stores[s].delete(self._k(key)):
                    n += 1
            return n

    # ---- diagnostics --------------------------------------------------

    def stats(self) -> dict:
        with self._lock:
            ring_dist = self.ring.distribution()
            return {
                "servers": list(self._stores.keys()),
                "replication": self.replication,
                "vnodes_per_server": self.vnodes,
                "ring_size": len(self.ring.ring),
                "ring_distribution": ring_dist,
                "down": sorted(self._down),
            }

    @staticmethod
    def _k(key: str) -> str:
        return f"kv:{key}"


# ---------------------------------------------------------------------------
# High-level facade
# ---------------------------------------------------------------------------


class KVStore:
    """User-facing API. Wraps a KVCluster with optional default quorum."""

    def __init__(
        self,
        cluster: Optional[KVCluster] = None,
        default_quorum: int = 1,
    ):
        self.cluster = cluster or KVCluster()
        self.default_quorum = default_quorum

    def put(self, key: str, value, require_acks: Optional[int] = None) -> PutResult:
        require_acks = require_acks if require_acks is not None else 1
        return self.cluster.put(key, value, require_acks=require_acks)

    def get(self, key: str, quorum: Optional[int] = None) -> GetResult:
        quorum = quorum if quorum is not None else self.default_quorum
        return self.cluster.get(key, quorum=quorum)

    def delete(self, key: str) -> int:
        return self.cluster.delete(key)
