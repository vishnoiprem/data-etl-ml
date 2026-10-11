---
lecture: L19
title: "Building an LRU Cache with TTL (time-bounded, thread-safe)"
duration: "24:00"
section: 4
prereqs: ["L18"]
---

# L19 — Building an LRU Cache with TTL

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 4 — Request-Parameter Authorizer & Policy Caching
> **Duration:** 24:00

## Prereqs

- L18 — `IdentitySource` and `ReauthorizeEvery`.

## Key terms

- **LRU (least-recently-used)** — an eviction policy: when the
  cache is full, the entry that was accessed longest ago is
  removed first.
- **TTL (time-to-live)** — the maximum age of an entry. After
  `now - created_at > ttl`, the entry is considered stale and is
  not returned.
- **Thread-safe** — safe to call from multiple threads
  concurrently. Critical for Lambda, which can have multiple
  worker threads in a single execution environment.
- **`OrderedDict`** — Python's standard-library dict that
  preserves insertion order. Combined with `move_to_end()`, it's
  a one-line LRU.
- **`functools.lru_cache`** — the stdlib alternative. Not
  time-bounded and not thread-safe-by-default for mutable
  arguments, so we don't use it here.

## Lecture

API Gateway's `ReauthorizeEvery` cache lives *outside* the
authorizer Lambda — it's in the API Gateway service. But there's
a second, *internal* cache that lives *inside* the authorizer
itself. It's useful when:

- The authorizer does expensive work that's not just verifying a
  token (e.g. fetching a JWKS endpoint, looking up a user in
  DynamoDB).
- You want to amortize that work across multiple invocations of
  the authorizer within the same Lambda execution environment.
- You want observability: a hit/miss metric in CloudWatch.

The internal cache is a **time-bounded LRU**. It evicts the
oldest entry when full, and ignores entries older than the TTL.

### A 30-line LRU + TTL

```python
import time
from collections import OrderedDict
from threading import Lock
from typing import Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class TTLCache(Generic[K, V]):
    """Thread-safe LRU cache with per-entry TTL."""

    def __init__(self, max_size: int = 1024, ttl_seconds: int = 300):
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._data: "OrderedDict[K, tuple[float, V]]" = OrderedDict()
        self._lock = Lock()

    def get(self, key: K) -> Optional[V]:
        now = time.time()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            created_at, value = entry
            if now - created_at > self._ttl:
                # Expired — drop and report miss.
                self._data.pop(key, None)
                return None
            # Touch — move to the end so it's the "most recent".
            self._data.move_to_end(key)
            return value

    def set(self, key: K, value: V) -> None:
        now = time.time()
        with self._lock:
            self._data[key] = (now, value)
            self._data.move_to_end(key)
            while len(self._data) > self._max_size:
                self._data.popitem(last=False)
```

That's the whole thing. Twenty-eight lines.

### Why each piece

- **`OrderedDict`** — Python's dict is ordered by insertion; an
  `OrderedDict` adds `move_to_end()` and `popitem(last=…)` for
  O(1) LRU. (Since Python 3.7, `dict` is also ordered, but
  `move_to_end` is still `OrderedDict`-only.)
- **`Lock`** — Lambda execution environments are multi-threaded
  (one thread per concurrent invocation). Any shared state must
  be guarded.
- **TTL check on `get`** — entries are *lazily* expired. We
  don't have a background sweeper; the entry is dropped the
  next time it's accessed after the TTL elapses.
- **`move_to_end` on hit** — refreshes the LRU position. Without
  it, a hot key gets evicted under pressure.

### How it slots into the authorizer

```python
_INTERNAL_CACHE: TTLCache[str, dict] = TTLCache(max_size=1024, ttl_seconds=300)


def lambda_handler(event, context):
    user = (event.get("queryStringParameters") or {}).get("user", "")
    token = (event.get("queryStringParameters") or {}).get("token", "")
    cache_key = f"{user}|{token}"

    cached = _INTERNAL_CACHE.get(cache_key)
    if cached is not None:
        return cached  # identity confirmed within the last 5 min

    # Slow path: actually verify.
    if not _verify(user, token):
        return _deny(event.get("methodArn", ""))

    policy = _allow(event["methodArn"], user, {"sub": user})
    _INTERNAL_CACHE.set(cache_key, policy)
    return policy
```

The first request for `(user=alice, token=xyz)` invokes the slow
path. The second request within 5 minutes returns the cached
policy *without* invoking the slow path.

### Edge cases

- **Cache key collisions.** The pipe `|` is a fine separator for
  `(user, token)` because the values themselves don't contain
  pipes. If the values are free-form, use a separator that can't
  appear in either (e.g. `\x00`).
- **Clock skew.** TTL is wall-clock based. If the Lambda's clock
  jumps backward, an entry might appear to live longer than
  expected. In practice this is rare; document it and move on.
- **Cold start.** A cold start means the cache is empty; the
  first request is always a miss. Plan for it.
- **Process recycling.** Lambda execution environments are
  recycled at least every 4 hours. The cache will be empty after
  a recycle.

### Observability

Emit a hit/miss metric via CloudWatch EMF so you can graph
cache effectiveness:

```python
def lambda_handler(event, context):
    cached = _INTERNAL_CACHE.get(cache_key)
    if cached is not None:
        # EMF log line — adds metrics to CloudWatch
        print("CACHE_HIT", flush=True)
        return cached
    print("CACHE_MISS", flush=True)
    # …
```

For a structured metric:

```python
import json
def _metric(name, value):
    print(json.dumps({
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [{
                "Namespace": "Authorizer",
                "Dimensions": [["FunctionName"]],
                "Metrics": [{"Name": name, "Unit": "Count"}]
            }]
        },
        "FunctionName": os.environ["AWS_LAMBDA_FUNCTION_NAME"],
        name: value,
    }))
```

Then graph `Authorizer.CacheHit` / `Authorizer.CacheMiss` in
CloudWatch.

## Hands-on

The hands-on code is in L20. The full module is in
`code/param_authorizer.py` and includes the `TTLCache` plus a
counter for hits/misses.

## Quiz prep

- Why is `OrderedDict` better than `dict` for an LRU?
- Why do we need a `Lock`?
- What happens to the cache on a cold start?

## Further reading

- Python docs: [`collections.OrderedDict`](https://docs.python.org/3/library/collections.html#collections.OrderedDict).
- AWS docs: [Lambda execution environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html).

## What's next

**L20 — End-to-End: REQUEST Authorizer with Policy Cache** — the
working demo.