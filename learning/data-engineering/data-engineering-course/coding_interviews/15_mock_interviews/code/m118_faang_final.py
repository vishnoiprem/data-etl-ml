"""Mock 118 — FAANG final: thread-safe in-memory KV store with TTL."""

import time
import threading


class ThreadSafeKV:
    """A thread-safe in-memory key-value store with per-key TTL.

    get() applies lazy expiry: if a key has expired, it is deleted
    and None is returned.
    """

    def __init__(self):
        self._data = {}  # key -> (value, expires_at)
        self._lock = threading.Lock()

    def set(self, key, value, ttl_seconds):
        expires_at = time.monotonic() + ttl_seconds
        with self._lock:
            self._data[key] = (value, expires_at)

    def get(self, key):
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() >= expires_at:
                del self._data[key]
                return None
            return value

    def delete(self, key):
        with self._lock:
            self._data.pop(key, None)


if __name__ == "__main__":
    store = ThreadSafeKV()
    store.set("a", 1, ttl_seconds=0.05)
    print(store.get("a"))   # 1
    time.sleep(0.1)
    print(store.get("a"))   # None
