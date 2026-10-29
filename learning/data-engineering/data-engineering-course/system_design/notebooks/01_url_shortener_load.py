"""URL shortener load test analysis.

Run the URL shortener first:
    python3 01_url_shortener/code/app.py

Then in this notebook (or just `python3 notebooks/01_url_shortener_load.py`):

    1. Warm the cache with N writes.
    2. Run a read-heavy load test (90% reads).
    3. Pull /metrics from the service and print the latency percentiles.
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8001"


def shorten(url: str) -> dict:
    body = json.dumps({"url": url}).encode()
    req = urllib.request.Request(
        BASE + "/api/shorten",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def resolve(key: str) -> int:
    try:
        with urllib.request.urlopen(BASE + "/" + key) as r:
            r.read()
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def metrics() -> str:
    with urllib.request.urlopen(BASE + "/metrics") as r:
        return r.read().decode()


def main(n_writes: int = 200, n_reads: int = 1000) -> None:
    print(f"Writing {n_writes} URLs...")
    keys: list[str] = []
    for i in range(n_writes):
        rec = shorten(f"https://example.com/article/{i}")
        keys.append(rec["key"])

    print(f"Reading {n_reads} times...")
    latencies: list[float] = []
    for i in range(n_reads):
        key = keys[i % len(keys)]
        t0 = time.perf_counter()
        resolve(key)
        latencies.append((time.perf_counter() - t0) * 1000)

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    print(f"p50={p50:.2f}ms  p95={p95:.2f}ms  p99={p99:.2f}ms")

    print("\nService metrics (excerpt):")
    m = metrics()
    for line in m.splitlines():
        if line.startswith(("resolve_latency_ms", "shorten_latency_ms",
                            "cache_hits", "cache_misses", "resolve_total")):
            print("  " + line)


if __name__ == "__main__":
    main()
