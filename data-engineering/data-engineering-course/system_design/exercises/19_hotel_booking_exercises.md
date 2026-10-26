# Exercises — Hotel Booking

Pick 3-5 of these to extend the system. Each one is a real feature a
production Hotel Booking has. Implementing them will teach you more
about the design than re-reading the doc.

## 1. Add metrics for cache hit rate
Expose the cache's hit_rate at `/metrics`; add a counter for misses.

## 2. Add a pagination cursor
Replace `?limit=` with `?cursor=<id>&limit=` so clients can page
through without offset drift.

## 3. Add per-user rate limiting
Reuse the **Rate Limiter** module (14_rate_limiter). Apply 60 req/min
per IP. Return 429 with Retry-After.

## 4. Add persistence audit
The KeyValueStore is JSON-on-disk. Add a write-ahead log so a crash
mid-write doesn't corrupt state.

## 5. Add structured logging
Emit a JSON line per request: `{ts, ip, method, path, status,
latency_ms, request_id}`. Pipe to file; demo a grep for 5xx.

## 6. Add a /health/ready vs /health/live split
`/health/live` = process is up. `/health/ready` = downstream
dependencies (storage, cache) are reachable. Use both at the LB.

## 7. Add an integration test
Spin up two service instances; have one call the other; verify the
end-to-end contract.

## 8. Add a "bulk" endpoint
Accept N items in one request. Use `gunicorn` with `gthread` workers
to handle concurrency; benchmark the improvement.
