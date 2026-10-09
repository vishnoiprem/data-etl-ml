"""Tiny load-tester for the URL shortener.

Usage:
    # terminal 1
    python3 01_url_shortener/code/app.py

    # terminal 2
    python3 01_url_shortener/code/loadtest.py 5000 90
    # 5000 requests, 90% reads (cache-warming) and 10% writes
"""

from __future__ import annotations

import random
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8001"


def shorten(i: int) -> tuple[float, int]:
    body = b'{"url": "https://example.com/article/' + str(i).encode() + b'"}'
    req = Request(
        BASE + "/api/shorten",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urlopen(req) as r:
        r.read()
        code = r.status
    return (time.perf_counter() - t0) * 1000, code


def resolve(i: int) -> tuple[float, int]:
    # Pick a key in the [0, 2000) range we know exists after seeding.
    key = "k" + str(i % 2000)
    t0 = time.perf_counter()
    try:
        with urlopen(BASE + "/" + key) as r:
            r.read()
            code = r.status
    except Exception as e:
        code = getattr(e, "code", 0)
    return (time.perf_counter() - t0) * 1000, code


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    read_pct = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0

    latencies: list[float] = []
    statuses: list[int] = []

    ops: list[tuple[str, int]] = []
    for i in range(n):
        if random.random() * 100 < read_pct:
            ops.append(("read", i))
        else:
            ops.append(("write", i))

    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = [
            ex.submit(resolve, i) if op == "read" else ex.submit(shorten, i)
            for op, i in ops
        ]
        for f in as_completed(futs):
            ms, code = f.result()
            latencies.append(ms)
            statuses.append(code)

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    print(f"requests: {n}  ok: {sum(1 for s in statuses if s in (200, 201, 302))}")
    print(f"p50={p50:.1f}ms  p95={p95:.1f}ms  p99={p99:.1f}ms  "
          f"mean={statistics.mean(latencies):.1f}ms")
    print(f"max={latencies[-1]:.1f}ms  min={latencies[0]:.1f}ms")


if __name__ == "__main__":
    main()
