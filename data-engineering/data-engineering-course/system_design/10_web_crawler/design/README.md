# Design: Web Crawler (BFS, politeness, per-host frontier)

## 1. Requirements

### Functional
- **Seed-based BFS crawl.** Caller `POST /api/crawl` with one seed URL;
  the crawler expands by following links discovered on the seed page
  and continues breadth-first until a configurable depth/page cap.
- **Politeness.** Between any two requests to the same host we sleep
  at least `host_delay_ms` (default 250 ms). No more than one request
  in flight per host at a time.
- **Dedup.** A URL is fetched at most once per crawl (and across crawls,
  via the persistent `seen` set).
- **Status visibility.** `GET /api/crawl/status` reports queue length,
  pages fetched, hosts contacted, errors.
- **Page retrieval.** `GET /api/pages/<url>` returns the parsed page
  (title, links, fetch time, status code).
- **Persistent state.** Crawl state survives process restarts.

### Non-functional
- Single-process, in-memory + JSON-on-disk. No external services.
- Bounded memory: URL frontier cap and a max-pages-per-crawl cap.
- Worker thread runs the BFS; HTTP layer is non-blocking.

## 2. Capacity

For a laptop demo: 1 worker thread, up to 100 pages per crawl, 1000
URLs in the frontier, 0.25s between hits to the same host. That is
roughly 4 req/s worst-case when the URL set spans 1 host, which keeps
the demo polite even to a real site.

For a production crawler:
- N worker threads, K = max-in-flight-per-host (here K=1 for politeness).
- Frontier: Redis sorted set keyed by `(host, priority)`.
- Dedup: Bloom filter in front of a durable key-value store.
- DNS cache, robots.txt cache per host, per-host failure budget.

## 3. High-level architecture

```
                +-------------------+
client ---->    |   Flask app.py    |  (HTTP, /metrics, /health)
                +---------+---------+
                          |
                          v
                +-------------------+
                |  WebCrawler svc   |  (BFS, frontier, dedup)
                +----+-------+------+
                     |       |
            +--------+       +--------+
            v                          v
   +-----------------+         +------------------+
   |  URL frontier   |         |  KeyValueStore   |
   |  (per-host      |         |  (pages + seen)   |
   |   deques)       |         +------------------+
   +--------+--------+
            |
            v
   +-----------------+
   | Worker thread   |  fetch -> parse -> enqueue links
   +-----------------+
```

## 4. API

| Method | Path                       | Body / Query                  | Response                          |
|--------|----------------------------|-------------------------------|-----------------------------------|
| POST   | `/api/crawl`               | `{"seed": "https://x/", "max_pages": 50, "max_depth": 2}` | `{crawl_id, status}`              |
| GET    | `/api/crawl/status`        | —                             | `{crawls: [...], totals: {...}}`  |
| GET    | `/api/crawl/<id>`          | —                             | `{crawl_id, status, pages, ...}`  |
| GET    | `/api/pages/<path:url>`    | —                             | `{url, status, title, links}`     |
| GET    | `/health`                  | —                             | `{ok, ts}`                        |
| GET    | `/metrics`                 | —                             | Prometheus-style text             |

`<path:url>` accepts a URL with `/`s.

## 5. Data model

Stored in `KeyValueStore` (`var/web_crawler.json`):

- `crawl:{crawl_id}` -> `{seed, max_pages, max_depth, status, pages, errors, started_at, finished_at}`
- `page:{url}` -> `{url, status, title, links, fetched_at, crawl_id, depth}`
- `seen` -> set (as list under `seen:` prefix) of canonicalised URLs.
- `crawls` -> list of crawl_ids under `crawlindex:` prefix.

In memory:
- `_frontier: dict[host -> deque[(url, depth, crawl_id)]]`
- `_host_next_due: dict[host -> float]` (next time we may hit a host).

## 6. Read / write paths

### Write (crawl)
1. Validate seed URL, normalise, enqueue at depth 0 for its host.
2. Worker pops the head of any host whose `_host_next_due` is past `now`.
3. Sleep if needed (`max(0, next_due - now)`); fetch (simulated).
4. Parse HTML, extract `<a href>`, canonicalise, dedup against `seen`.
5. Enqueue new URLs at depth+1 if under `max_depth` and `max_pages`.

### Read (page lookup)
- `GET /api/pages/<url>` -> `page:{url}` in `KeyValueStore`; cache
  recently-read pages in a TTL cache.

## 7. Failure modes

| Failure                          | Handling                              |
|----------------------------------|---------------------------------------|
| Network / fetch error            | record under `crawl.errors`, mark host with a 5s backoff |
| Bad HTML / no links              | page stored with empty `links`        |
| Crawl exceeds `max_pages`        | stop enqueuing new links; let queue drain |
| Process crash mid-crawl          | state is durable; restart picks up `status="running"` crawls and resumes the frontier from disk |
| Duplicate URL                    | silently dropped via `seen` set       |

## 8. Tradeoffs

- **BFS vs DFS:** BFS is more "even" and simpler; we prefer BFS here.
- **In-process frontier vs Redis:** for a single laptop we use a `dict`
  of `deque`s; in production a sorted set per host is preferable.
- **Persistent `seen`:** cheap dedup, but infinite growth — mitigated
  by the `max_pages` cap and the fact that the demo URL set is small.
- **Simulated fetch:** we don't actually hit the network. The fetcher
  is a deterministic mapping from URL -> canned HTML so tests are
  reproducible. Swap in `requests`/`httpx` for production.

## 9. Code map

- `code/service.py`  – `WebCrawler` class: BFS, frontier, dedup, worker thread.
- `code/app.py`      – Flask HTTP layer.
- `tests/test_service.py` – 6+ unit tests.
- `tests/test_app.py`     – 5+ HTTP tests.
