# Exercises — URL Shortener

Pick 3-5 of these to extend the system. Each one is a real feature a
production URL shortener has. Implementing them will teach you more
about the design than re-reading the doc.

## 1. Add link expiry
Right now links live forever. Add a `ttl_seconds` field on
`shorten(...)`. After expiry, `resolve` returns 410 Gone.

Hint: store `expires_at` in the record. On resolve, check it.

## 2. Add analytics
Per-link click analytics: total clicks, last clicked, click count by
day. Persist in a separate `clicks:<key>:<yyyy-mm-dd>` counter.

## 3. Add rate limiting per IP
Use the **Rate Limiter** module (14_rate_limiter) — or copy the token
bucket from it. Apply 100 req/min per IP. Reject with 429.

## 4. Add a vanity-preview endpoint
`GET /api/preview/<key>` — returns the long URL with safety checks
(no SSRF: refuse internal IPs). Return the host only by default;
return full URL with `?expand=true`.

## 5. Make keys URL-safe
The current `short_hash` produces base62 which is fine, but if you
generate from a random counter, you can avoid 0/O/1/l confusion. Add
a transliteration pass.

## 6. Add a fanout-on-write prefetch
When a link becomes hot (>100 clicks/min), pre-warm the cache on all
app replicas via a pub/sub topic. Implement: the request handler that
detects the hot key publishes, every replica subscribes and pre-fills
its in-process LRU.

## 7. Add a /api/admin endpoint
List all links created in the last hour. Block a key. Useful for
abuse handling.

## 8. Add structured logging
Use `loguru` or stdlib `logging` to emit a JSON line per request:
`{ts, ip, method, path, status, latency_ms}`. Pipe to file.
