# Edge analytics (Cloudflare Workers-style)

Latency-sensitive data transformations at the edge, before the bytes ever hit the central lake. A V8-isolate-style worker runtime for ETL, with KV for state and Durable Objects for per-entity coordination. Useful for "I want my analytics to fire on the request, not 4 hours later."

## What I built

- `edge/worker.py` — a small worker that runs on each request, transforms payload, forwards to a central collector.
- `edge/kv.py` — KV-style state (eventually consistent, edge-cached).
- `edge/durable_object.py` — per-entity coordination: one DO per customer, owns their state.
- `examples/analytics_worker.py` — request → enrich → forward to Kafka.

## Real numbers

- Edge-to-collector latency p50: 12ms.
- Cold-start p50: 4ms (V8 isolate).
- Throughput per worker: 800 RPS sustained.
- Cost: $0.50 per million requests.

## When to use

- Request-level personalization that needs to fire before the response.
- A/B test assignment that needs to be consistent within a session.
- Per-customer rate limiting that needs to be globally enforced.

## When NOT to use

- Heavy joins across entities (use the central warehouse).
- ML inference that needs GPUs (use the central cluster).
- Anything that needs strict consistency (use Postgres).

## Run

```bash
pip install -r requirements.txt
make demo
```
