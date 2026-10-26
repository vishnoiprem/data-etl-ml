"""A tiny thread-safe in-memory key-value store.

This stands in for a real database. It supports point reads, point writes,
and prefix scans — the minimum surface we need to demonstrate sharding and
replication patterns in the design docs. In production you'd swap this for
DynamoDB / Cassandra / Postgres.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Iterator, Optional


class KeyValueStore:
    """JSON-persisted, thread-safe, in-memory key-value store.

    Persistence is optional — pass ``persist_path=None`` to disable writes
    to disk (useful for tests). Default persistence writes to
    ``./var/<name>.json`` so you can inspect the data after a run.
    """

    def __init__(self, name: str = "kv", persist_path: Optional[str] = None):
        self.name = name
        self.persist_path = persist_path or os.path.join(
            "var", f"{name}.json"
        )
        self._data: dict[str, Any] = {}
        self._lock = threading.RLock()
        self._load()

    # ---- public API -----------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self._flush()

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                self._flush()
                return True
            return False

    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._data

    def keys_with_prefix(self, prefix: str) -> list[str]:
        with self._lock:
            return [k for k in self._data.keys() if k.startswith(prefix)]

    def scan(self, prefix: str = "") -> Iterator[tuple[str, Any]]:
        with self._lock:
            for k, v in self._data.items():
                if not prefix or k.startswith(prefix):
                    yield k, v

    def size(self) -> int:
        with self._lock:
            return len(self._data)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self._flush()

    def all(self) -> dict:
        with self._lock:
            return dict(self._data)

    # ---- persistence ----------------------------------------------------

    def _load(self) -> None:
        if not self.persist_path or not os.path.exists(self.persist_path):
            return
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except (OSError, json.JSONDecodeError):
            # Corrupt or partial file — start clean rather than crash.
            self._data = {}

    def _flush(self) -> None:
        if not self.persist_path:
            return
        os.makedirs(os.path.dirname(self.persist_path) or ".", exist_ok=True)
        tmp = f"{self.persist_path}.{int(time.time() * 1000)}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, sort_keys=True)
        os.replace(tmp, self.persist_path)
