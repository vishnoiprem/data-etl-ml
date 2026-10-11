"""Edge analytics worker: enrich + forward.

The shape every Cloudflare Worker / Vercel Edge / Fastly Compute
analytics pattern follows. The worker runs on the request, does cheap
enrichment (geo, session-cookie merge, A/B bucket), and forwards the
event to a central collector.
"""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Request:
    url: str
    headers: dict
    user_id: Optional[str]
    ts: float = field(default_factory=time.time)


@dataclass
class Event:
    user_id: str
    ab_bucket: str
    session_id: str
    url: str
    ts: float


class KV:
    """Toy KV: in-memory + edge-cached. Real impl: Cloudflare KV / Vercel Edge Config."""

    def __init__(self):
        self._store: dict[str, str] = {}
        self._cache: dict[str, str] = {}  # edge-cached

    def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            return self._cache[key]
        v = self._store.get(key)
        if v is not None:
            self._cache[key] = v
        return v

    def put(self, key: str, value: str):
        self._store[key] = value
        self._cache[key] = value


class AnalyticsWorker:
    def __init__(self, kv: KV, forwarder: Callable[[Event], None]):
        self.kv = kv
        self.forwarder = forwarder

    def ab_bucket(self, user_id: str) -> str:
        """Stable hash -> bucket. Same user always sees the same bucket."""
        h = int(hashlib.sha256(user_id.encode()).hexdigest(), 16) % 100
        return "A" if h < 50 else "B"

    def session_id(self, user_id: str) -> str:
        """Sticky session id, rotates every 30 minutes."""
        s = self.kv.get(f"session:{user_id}")
        if s:
            return s
        new = hashlib.sha1(f"{user_id}:{time.time()//1800}".encode()).hexdigest()[:16]
        self.kv.put(f"session:{user_id}", new)
        return new

    def handle(self, req: Request) -> Event:
        uid = req.user_id or "anon"
        ev = Event(
            user_id=uid,
            ab_bucket=self.ab_bucket(uid),
            session_id=self.session_id(uid),
            url=req.url,
            ts=req.ts,
        )
        self.forwarder(ev)
        return ev


if __name__ == "__main__":
    kv = KV()
    forwarded = []
    worker = AnalyticsWorker(kv=kv, forwarder=forwarded.append)
    for i in range(3):
        req = Request(url=f"/page/{i}", headers={}, user_id="user_42")
        ev = worker.handle(req)
        print(json.dumps(ev.__dict__))
