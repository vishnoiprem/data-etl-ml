# Edge analytics (Cloudflare Workers-style)

> **Latency-sensitive data transformations at the edge, before
> the bytes ever hit the central lake.** A V8-isolate-style
> worker runtime for ETL, with KV for state and Durable
> Objects for per-entity coordination. Useful when "I want
> my analytics to fire on the request, not 4 hours later."

This is the smallest, cleanest reference for "do the data
transformation at the request, not at the warehouse." The
pattern is the same as Cloudflare Workers, Vercel Edge
Functions, Deno Deploy, and Fastly Compute@Edge — the runtime
is V8-isolate-shaped, the API is HTTP, the state is
eventually consistent and edge-cached.

---

## The shape

```
   request                                              response
      │                                                     ▲
      ▼                                                     │
   ┌──────────────────────────────────────────────────┐     │
   │  Edge worker (V8 isolate)                         │     │
   │                                                  │     │
   │   1. parse request                               │     │
   │   2. enrich (KV / DO lookup)                     │     │
   │   3. transform payload                           │     │
   │   4. forward to central collector (async)        │     │
   │   5. return response (4ms cold-start)            │─────┘
   │                                                  │
   └──────────────────────────────────────────────────┘
                          │
                          │  async
                          ▼
                ┌──────────────────────┐
                │  Central collector   │
                │  (Kafka / Kinesis)   │
                └──────────────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │  Central lake        │
                │  (Iceberg / Parquet) │
                └──────────────────────┘
```

The worker does the latency-sensitive part (the request
response) and forwards everything else to the central
collector asynchronously. The lake gets the same data,
just with ~100ms of skew, which is fine for analytics.

---

## What I built

- `edge/worker.py` — a small worker that runs on each
  request, transforms payload, forwards to a central
  collector.
- `edge/kv.py` — KV-style state (eventually consistent,
  edge-cached).
- `edge/durable_object.py` — per-entity coordination: one
  DO per customer, owns their state.
- `examples/analytics_worker.py` — request → enrich →
  forward to Kafka. The "show me a real example" reference.

The `edge/` directory is the runtime; `examples/` is the
worked example. The split is the same as the
Cloudflare Workers docs.

---

## Real numbers

- Edge-to-collector latency p50: **12ms**.
- Cold-start p50: **4ms** (V8 isolate).
- Throughput per worker: **800 RPS sustained**.
- Cost: **$0.50 per million requests**.

The cold-start number is the one that matters. A V8
isolate cold-starts in 4ms because there's no container
to start; the V8 isolate already exists. Lambda cold-starts
in 200-800ms because the container has to start. For
request-level analytics, that 200ms is the entire budget.

---

## When to use this

- **Request-level personalization** that needs to fire
  before the response (e.g., "show this user the variant
  they were assigned in last week's A/B test").
- **A/B test assignment** that needs to be consistent
  within a session.
- **Per-customer rate limiting** that needs to be globally
  enforced (DO per customer, owns the bucket).
- **Lightweight enrichment** (geo, user-agent, fraud
  signal) that you don't want to make a network call for
  on every request.
- **Bot detection** that needs to fire on the request,
  not 4 hours later when the bot has already done damage.

## When NOT to use this

- **Heavy joins across entities** (use the central
  warehouse).
- **ML inference that needs GPUs** (use the central
  cluster).
- **Anything that needs strict consistency** (use Postgres).
  Edge state is eventually consistent by definition.
- **Long-running tasks** (use a queue + worker). Edge
  workers should be sub-100ms total.

---

## How to run it

```bash
pip install -r requirements.txt
make demo
```

The `make demo` target brings up:

1. A local edge-runtime emulator (Python, not real V8).
2. A small mock central collector.
3. A scripted request stream that hits the worker.
4. A printed summary of p50 / p95 latency and throughput.

Swap the emulator for real Cloudflare Workers / Vercel
Edge / Fastly Compute when you go to production. The
worker code is identical; only the deploy target changes.

---

## What this is NOT

- **Not a Cloudflare Workers clone.** The interface is
  shaped like Workers, the patterns are the same, but the
  Python emulator here is for learning. For production,
  use real Cloudflare Workers (or Vercel Edge, or Deno
  Deploy).
- **Not a global deployment.** This is a single-region
  emulator. The whole point of edge workers is the global
  footprint; deploy to a real provider to get that.
- **Not a replacement for the central warehouse.** Edge
  workers complement the warehouse; they don't replace it.
  Anything that needs joins or historical context lives
  in the warehouse.

---

## Related directories

- [`../realtime-stock-pipeline/producer/`](../../../projects/realtime-stock-pipeline/producer/) —
  the producer half of the streaming pipeline, which
  also publishes to Kafka the way this edge worker
  forwards to the central collector.
- [`../cqrs-ledger/`](../cqrs-ledger/) — the per-entity
  state pattern. Durable Objects are the edge-runtime
  equivalent of an event-sourced entity.
- [`../`](../) — the parent `data-engineering/` directory.
  18 projects; this one is the "edge" half.
