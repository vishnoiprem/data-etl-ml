# 08 — Webhook Delivery System

> **Lesson 8 of the System Design course — Event-Driven Systems**

A working design + implementation of an outbound webhook delivery
service: subscribers register URLs, the system signs each delivery
with an HMAC, dispatches in the background, retries with exponential
backoff, and routes permanently-failed deliveries to a dead-letter
queue (DLQ) that can be replayed on demand.

This is the same shape used by Stripe, GitHub, Shopify, and Twilio:
when *our* system has news for *your* system, we POST it. Getting
that right is hard because the consumer is a black box — we have
to be patient, signed, and observable.

---

## 1. Requirements

### Functional
- **Subscribe** — a client registers `{url, secret, event_types}`,
  and gets back a `subscription_id`.
- **Deliver** — POST a `{event, payload}` to a subscription's URL.
  The body is HMAC-SHA256 signed with the subscription's secret.
- **Retry** — on 5xx / network error / timeout, retry with
  exponential backoff up to `max_attempts` (default 5). The next
  attempt is scheduled at `base_delay * 2^(attempt-1) + jitter`.
- **Dead-letter** — after `max_attempts`, the delivery is moved to
  the DLQ with the full attempt history. The API can list and
  replay DLQ entries.
- **Replay** — re-attempt a previously failed delivery. Resets the
  attempt counter.
- **History** — every attempt (including DLQ arrivals) is recorded
  with status, latency, and error.

### Non-functional
- **At-least-once** — the same event may be delivered more than
  once (the consumer must dedupe on `event_id`).
- **Bounded blast radius** — a bad subscriber cannot block other
  subscribers. The dispatcher is per-subscription.
- **Observability** — per-subscription counters for `delivered`,
  `retried`, `dlq`, and a latency histogram.
- **Security** — HMAC-SHA256 over the raw body; the signature is
  passed in the `X-Signature` header; a timestamp is included to
  prevent replay (a 5-minute window is the convention).

### Out of scope (for this lesson)
- Real HTTP — we *simulate* the network call (configurable outcome
  per attempt) so the lesson focuses on the state machine, not
  on `requests` vs `aiohttp`. The shape is identical: the
  `HTTPTransport` interface is the seam.
- Per-event fanout (we deliver one event to one subscription per
  call; the caller is responsible for iterating subscriptions).
- TLS / certificate pinning (assumed handled by the transport).

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Active subscriptions | 100 K |
| Deliveries / sec | 10 K avg, 50 K peak |
| Avg payload | 4 KB |
| Avg attempt latency | 200 ms (including 50 ms HTTP + processing) |
| DLQ rate target | < 0.1 % (after retries) |
| Attempt storage | ~250 bytes per attempt × attempts × deliveries |
| Retention | 30 days for completed, 90 days for DLQ |

The lesson: the bottleneck is *outbound* HTTP — we're at the mercy
of the slowest subscriber. Concurrency is the main lever (a thread
pool sized to `cores * 32` is typical), plus a per-subscription
in-flight cap so one bad endpoint can't drown the worker.

---

## 3. High-level design

```
   client ─► POST /api/subscriptions
              │
              ▼
         ┌──────────┐                ┌────────────────────┐
         │   API    │ ──register──►  │  subs (KeyValueStore)│
         │  (Flask) │                └────────────────────┘
         └────┬─────┘
              │ POST /api/subscriptions/<id>/deliver
              ▼
         ┌──────────┐                ┌────────────────────┐
         │  service │ ──enqueue───►  │  pending (KV list) │
         │          │                └────────────────────┘
         └────┬─────┘
              │ enqueue returns 202
              │   (delivery_id)
              │
              │ (background thread)
              ▼
        ┌────────────────┐
        │ delivery loop  │  pulls pending, signs, dispatches
        └────┬───────────┘
             │ HMAC + payload
             ▼
        ┌────────────────┐
        │ HTTP transport │  ◄── pluggable; simulator for tests
        └────┬───────────┘
             │ result
             ▼
   2xx   ─► mark DELIVERED, store attempt
   5xx /err
         ─► schedule next retry (exponential backoff)
             on max_attempts reached ─► DLQ
   4xx   ─► permanent failure ─► DLQ immediately
```

- **API**: Flask. Synchronous request → enqueue, return 202.
- **Service**: in-process. Owns the state machine for each delivery.
- **Delivery loop**: background thread that pulls pending deliveries
  and dispatches them. Uses a `threading.Event` for shutdown.
- **Transport**: pluggable. `SimulatedTransport` is the default;
  swap in `HTTPXTransport` for real use.
- **Persistence**: `KeyValueStore` (JSON) for subscriptions,
  deliveries, and attempts. Reloadable on restart.

---

## 4. API

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| `POST` | `/api/subscriptions` | `{"url", "secret", "event_types": [...]}` | `{"subscription_id", "url", "event_types"}` |
| `GET`  | `/api/subscriptions` | — | list |
| `GET`  | `/api/subscriptions/<id>` | — | subscription + delivery counts |
| `POST` | `/api/subscriptions/<id>/deliver` | `{"event", "payload"}` | `{"delivery_id", "status": "pending"}` |
| `GET`  | `/api/subscriptions/<id>/deliveries` | — | list of deliveries (latest first) |
| `GET`  | `/api/deliveries/<id>` | — | delivery + attempt history |
| `POST` | `/api/subscriptions/<id>/replay/<delivery_id>` | — | re-enqueue the delivery |
| `GET`  | `/api/dlq` | — | list of all DLQ entries |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{"ok": true, "stats": ...}` |
| `GET`  | `/` | — | service index |

Notes:
- `deliver` is **202 Accepted** — the delivery is enqueued, the
  loop will pick it up. The response includes `delivery_id` so the
  client can poll `/api/deliveries/<id>`.
- `replay` resets the attempt counter and re-enqueues. Useful when
  the consumer fixed their endpoint after a DLQ trip.
- `GET /api/dlq` returns deliveries whose `status == "dead"`.

---

## 5. Data model

### Subscription
```
sub:<id> = {
  "subscription_id": str,        # snowflake
  "url": str,
  "secret": str,                 # HMAC key — never returned in plain
  "event_types": [str],          # filter; empty == all
  "created_at": float,
  "delivered_total": int,        # lifetime
  "retried_total": int,
  "dlq_total": int,
}
```

### Delivery
```
del:<id> = {
  "delivery_id":   str,
  "subscription_id": str,
  "event":         str,          # e.g. "order.placed"
  "payload":       dict,         # arbitrary JSON
  "status":        "pending" | "delivered" | "dead",
  "attempts":      int,          # count so far
  "max_attempts":  int,
  "next_attempt_at": float,      # epoch seconds
  "created_at":    float,
  "last_status_code": int | None,
  "last_error": str | None,
  "last_attempt_at": float | None,
}
```

### Attempt (append-only per delivery)
```
attempt:<delivery_id>:<n> = {
  "n": int,                      # attempt number, 1-based
  "ts": float,
  "status_code": int | None,     # None for network error
  "latency_ms": float,
  "error": str | None,
}
```

### Dead-letter index
We don't store a separate DLQ — `del:<id>.status == "dead"` is the
DLQ. `/api/dlq` does a prefix scan over `del:`.

---

## 6. Write path: deliver

`POST /api/subscriptions/<id>/deliver`:

```
1. Validate body {event, payload}.
2. Check subscription exists; check event_type filter.
3. Mint a delivery_id (snowflake).
4. Create the delivery record (status=pending, attempts=0,
   next_attempt_at=now).
5. Wake the delivery loop (Event.set()).
6. Return 202 {delivery_id, status: "pending"}.
```

The loop picks the delivery up on its next tick and walks the
attempt state machine.

---

## 7. Delivery loop & attempt state machine

```
   ┌─────────┐  attempt OK (2xx)  ┌─────────────┐
   │ pending │ ──────────────────►│ delivered   │
   └────┬────┘                    └─────────────┘
        │
        │ attempt fails (5xx, timeout, network)
        ▼
   ┌─────────┐
   │ pending │ (attempts < max_attempts)
   │         │  schedule next_attempt_at = now + backoff
   └────┬────┘
        │ attempts == max_attempts
        ▼
   ┌─────────┐
   │  dead   │  (DLQ; replay can rescue)
   └─────────┘

   4xx response  ────► dead (immediately; no retry — client's
                       URL is wrong, retrying won't help).
```

The loop body:

```
while not shutdown:
    wait(loop_interval)        # ~100ms
    for each delivery where next_attempt_at <= now:
        if already_in_flight(delivery_id): skip
        dispatch(delivery)
```

`dispatch(delivery)`:
```
1. Bump attempts += 1.
2. Compute signature = HMAC_SHA256(secret, body).
3. POST {body, headers: X-Signature, X-Timestamp} to url.
4. Record attempt.
5. On 2xx: status=delivered, last_status_code=response.
6. On 4xx: status=dead, no retry.
7. On 5xx/timeout/err:
     if attempts < max_attempts:
        backoff = base_delay * 2^(attempts-1) + jitter
        next_attempt_at = now + backoff
     else:
        status=dead.
8. Persist.
```

The HMAC header layout follows the de-facto Stripe convention:

```
X-Signature: t=<unix_ts>,v1=<hex_hmac_of_<ts>.<body>>
```

`v1` is computed over `<ts>.<raw_body>` so the timestamp is bound
to the signature (a replay would need both the body and the
signature to match). The consumer should reject signatures older
than 5 minutes.

---

## 8. Failure modes

| Failure | What happens | Mitigation |
|---|---|---|
| **Subscriber URL is 4xx** | Permanent failure → DLQ. | No retry. Alert the subscriber via a separate channel (e.g. email). |
| **Subscriber URL is 5xx** | Retry with backoff until `max_attempts`. | Surface to subscriber as "transient" — usually fixed in seconds. |
| **Timeout** | Treated as 5xx. | Bounded per-attempt timeout (e.g. 10s) so the loop doesn't get stuck. |
| **Bad HMAC on consumer side** | Consumer rejects. | Our doc page tells them the exact algorithm. We also expose the `secret` once at create time so they can verify. |
| **Worker crash mid-attempt** | The next loop tick re-fires the delivery. Counter is consistent (`attempts` is incremented *before* the network call). | Acceptable at-least-once: an extra delivery is far less bad than a missed one. |
| **Subscriber endpoint is slow** | Slows the per-subscription in-flight. Other subscribers are unaffected. | Per-subscription concurrency cap; per-attempt timeout. |
| **Replay storm** (operator replays 10 K DLQ items) | All 10 K in-flight simultaneously. | Concurrency cap at the loop level; replay calls return 202 with the same delivery_id (idempotent). |
| **Secret leaked** | Attacker can forge deliveries. | Owner can rotate: `POST /api/subscriptions/<id>/secret` overwrites the secret; in-flight deliveries with the old signature fail (caller retries). Out of scope here. |

---

## 9. Tradeoffs

### Synchronous vs background dispatch
- **Synchronous** (block the request): simple, but a slow
  subscriber stalls the API. P50 latency is the consumer's latency.
- **Background** (what we do): 202 Accepted, the loop handles
  dispatch. API is fast (sub-10ms) regardless of subscriber health.

We pick background.

### Thread pool vs asyncio
- `threading.Thread` is dead-simple and the GIL isn't the
  bottleneck for I/O-bound work. Concurrency is bounded by the
  number of in-flight HTTP calls.
- `asyncio` would let us share a single thread, but every HTTP
  library becomes async-only and the test surface is more complex.

We pick threads for clarity.

### In-memory queue vs persistent queue
- **In-memory** (`threading.Event` + list of pending): fast, but
  the server crash drops pending deliveries. They were acked
  (status=pending in KV) but never dispatched — silent loss.
- **Persistent queue** (we use KV): every enqueue and every state
  transition is durably written. A crash replays the KV and
  resumes. We pick persistent.

### Fixed vs exponential backoff
- **Fixed** (e.g. always 30s): simple, but a thundering-herd if
  the subscriber goes down for 1 minute.
- **Exponential** (we do): 1s, 2s, 4s, 8s, 16s... spreads the load.
  Add jitter to avoid synchronized retry waves.

We pick exponential with jitter.

### Retry-then-DLQ vs immediate-DLQ
- **Immediate DLQ** on first failure: simple, but confuses
  transient outages with permanent ones.
- **Retry, then DLQ** (we do): recovers from transient blips, DLQ
  is reserved for genuinely broken endpoints. Tradeoff: longer
  detection time for the truly broken case.

### Per-subscription queue vs global FIFO
- **Global FIFO**: one bad subscriber blocks all others.
- **Per-subscription queue** (we do): one bad subscriber only
  blocks their own deliveries. Cost: more bookkeeping.

---

## 10. Code map

```
08_webhook_delivery/
├── design/README.md            # this file
├── code/
│   ├── __init__.py
│   ├── service.py              # WebhookService (pure logic + bg loop)
│   └── app.py                  # Flask wrapper
└── tests/
    ├── __init__.py
    ├── test_service.py         # ≥6 unit tests
    └── test_app.py             # ≥4 HTTP tests
```

- `WebhookService` owns subscriptions, deliveries, attempts, the
  delivery loop, the HMAC signer, and the transport interface.
  Tests inject a `SimulatedTransport` to control attempt outcomes.
- `app.py` is the Flask wrapper. Endpoints are thin; the service
  does the real work.
- The delivery loop runs in a background thread. The service has
  `start()` and `stop()` methods for clean shutdown (tests don't
  start the loop — they call `dispatch_pending_now()` to drive
  delivery deterministically).
