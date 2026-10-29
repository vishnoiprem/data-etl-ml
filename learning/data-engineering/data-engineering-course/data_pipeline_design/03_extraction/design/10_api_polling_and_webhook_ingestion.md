# 10 — API Polling and Webhook Ingestion

> **Lesson 10 of 30 — Extraction**

Most data doesn't live in your database. It lives in SaaS APIs:
Stripe, Salesforce, HubSpot, internal microservices. This lesson
is how to extract from APIs reliably — pagination, rate limits,
and the alternative pattern (webhooks).

---

## 1. The two API patterns

**Polling:** the pipeline calls the API on a schedule, asks "what
changed since last time?", and processes the response.

**Webhooks:** the source system calls *your* endpoint whenever
something changes. The pipeline receives events, not polls.

Polling is universal: every API supports it. Webhooks are not:
most APIs support them, but some don't, and the ones that do
have different reliability stories. The senior move is to know
both and pick the right one.

---

## 2. Polling: the three pagination patterns

| Pattern | How it works | When to use |
|---|---|---|
| **Offset** | `?page=1&page_size=100` | Small, stable datasets (< 10K rows) |
| **Cursor** | `?after=cursor_xyz&page_size=100` | Modern APIs (Stripe, Slack, Notion) |
| **Keyset** | `?since_id=12345` | Internal APIs, monotonic keys |

**Offset pagination** is the simplest: page 1, page 2, page 3.
The pitfall: a row inserted between page 1 and page 2 shifts every
subsequent page. You can miss rows or see them twice. Use it only
for small, append-only datasets.

**Cursor pagination** is the modern default. The cursor is an
opaque token — the server controls it, the client just passes it
back. The server guarantees stability under inserts. The pitfall:
you can't jump to "page 50" without iterating; long backfills
take time.

**Keyset pagination** is `WHERE id > last_id`. Stable, simple,
fast. The pitfall: only works for monotonic keys (auto-increment,
UUIDv7). Doesn't catch updates to old rows.

---

## 3. The cursor polling pattern

The standard cursor-polling code:

```python
def poll_all(base_url, headers):
    cursor = None
    while True:
        url = base_url
        if cursor:
            url += f"&after={cursor}"
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for row in data["data"]:
            yield row
        if not data.get("has_more"):
            return
        cursor = data["next_cursor"]
```

The senior move: respect rate limits (Lesson below), checkpoint
the cursor, and resume on restart.

---

## 4. Rate limit handling

Every modern API rate-limits its clients. The standard headers:

| Header | Meaning |
|---|---|
| `X-RateLimit-Limit` | Total quota per window |
| `X-RateLimit-Remaining` | Quota left in this window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |
| `Retry-After` | (On 429) seconds until you can retry |

The 429 response means "you're calling too fast." The senior
pattern:

```python
def call_with_backoff(url, headers, max_attempts=5):
    for attempt in range(max_attempts):
        resp = requests.get(url, headers=headers)
        if resp.status_code != 429:
            return resp
        retry_after = int(resp.headers.get("Retry-After", 60))
        time.sleep(retry_after * (1 + random.random() * 0.1))  # jitter
    raise RuntimeError(f"Rate limited after {max_attempts} retries")
```

The senior move: respect `Retry-After`, add jitter (so multiple
workers don't all retry at the same time), and emit a metric on
429s so on-call sees when you're hitting the limit.

---

## 5. The checkpoint pattern

Polling is *stateful*. The pipeline needs to know "where I am in
the API" so a restart doesn't re-fetch everything. The pattern:

```
api_state(cursor='abc123', last_full_sync=2024-01-01T00:00:00Z)
```

The cursor is stored in a small table or file. On restart, the
pipeline reads the cursor and continues. The senior move: store
the cursor *atomically* with the last successful page, so a crash
mid-page doesn't lose the page.

```sql
-- The checkpoint pattern
CREATE TABLE pipeline_state (
  pipeline_name TEXT PRIMARY KEY,
  cursor TEXT,
  last_updated_at TIMESTAMP
);

UPDATE pipeline_state
SET cursor = :new_cursor, last_updated_at = NOW()
WHERE pipeline_name = 'stripe_charges';
```

---

## 6. Webhooks: the alternative

A webhook is the API *calling you* when something changes:

```
Stripe ──► POST /webhooks/stripe ──► Your endpoint
                                                  │
                                                  └─► 200 OK (or 4xx for retry)
```

The benefits:

- **Lower latency** (sub-second, vs minutes for polling).
- **Less load on the source** (they call you, not the other way around).
- **Always complete** (you get every event, in order).

The pitfalls:

- **You need a public endpoint.** A misconfigured firewall or
  load balancer can drop events.
- **The source may retry on failure.** Stripe retries for up to
  3 days. You need idempotent processing.
- **The source can lie.** Webhooks can be spoofed. Verify the
  signature on every event.
- **Ordering is not guaranteed.** Webhooks can arrive out of
  order. Sort by event timestamp on the consumer side.

---

## 7. The hybrid pattern

The senior pattern: webhooks for the hot path, polling for the
backfill. Stripe has both: webhooks for real-time events, the
Events API for backfill. The pipeline:

1. Subscribes to webhooks for live events.
2. Polls the Events API every hour to catch anything the webhook
   missed (or to backfill after a deploy).
3. Dedupes on `event_id` — the same event from webhook and poll
   is recognized by the same id.

This is the production-grade API extraction pattern. The senior
move: name this hybrid in the interview. "I'd use webhooks for
real-time and poll for backfill. Dedup on event_id."

---

## 8. The failure modes

| Failure | Mitigation |
|---|---|
| API down (5xx) | Exponential backoff with jitter. |
| Rate limited (429) | Respect `Retry-After`, back off. |
| Auth expired (401) | Refresh OAuth token, retry once. |
| Schema change | Schema contract test (Lesson 12). |
| Cursor stale | Some APIs expire cursors; fall back to full re-fetch. |
| Webhook dropped | Re-poll the source to catch up. |

The senior move: name the cursor-stale failure mode. "If the API
expires cursors after 24 hours, my pipeline must checkpoint the
last *timestamp* and re-fetch from there on restart, not just
resume from the cursor."

---

## 9. Code: the ApiPoller

The `code/api_poller.py` module implements the polling pattern:

```python
from data_pipeline_design.03_extraction.code.api_poller import ApiPoller

poller = ApiPoller(
    base_url="http://localhost:8080/items",
    page_size=5,
)
rows = poller.poll_all()
# returns a flat list of all rows across all pages
```

It handles pagination, rate limits (via configurable backoff), and
returns the full set of rows. The test in `tests/test_extraction.py`
spins up a tiny `http.server` to verify the 3-page, 5-rows-per-page
case.

---

## Try it

Sketch the API extraction for a system you've worked on. Is it
polling or webhooks? Where's the cursor stored? What happens on
restart? What happens on a 429? If you can't answer all four, the
pipeline is one bad deploy away from a data loss incident.
