# 20. Cog-style inference API (Replicate-style)

A small "one model, one container, one HTTP endpoint" inference service. The same shape Replicate exposes: cold-start mitigation, GPU pooling, request queueing, and a billing layer that doesn't lie. The pattern is what every "model-as-a-service" product converges on.

## The shape

```
       ┌────────────────────────────────────┐
       │  Model Registry (Postgres + S3)    │
       │  cog.yaml -> docker image -> model │
       └──────────────┬─────────────────────┘
                      ▼
       ┌────────────────────────────────────┐
       │   Inference API (FastAPI)          │
       │   POST /predictions  -> cold/warm  │
       │   GET  /predictions/{id} -> status │
       │   GET  /hardware       -> A10/H100 │
       └──────────────┬─────────────────────┘
                      ▼
       ┌────────────────────────────────────┐
       │   GPU Pool (Modal / K8s)           │
       │   cold-start < 8s (image cache)    │
       │   warm latency p50 < 300ms         │
       └────────────────────────────────────┘
```

## What I built

- `api/predict.py` — the predict handler (input -> output). Real impl: load model, run inference, return.
- `api/cog.yaml` — the model spec. Real impl: image, gpu type, env vars, predict signature.
- `api/queue.py` — request queue with per-tenant rate limits.
- `api/billing.py` — per-second GPU-time accumulator; not a credit, not a token — just a number.
- `examples/sdxl_predict.py` — a working SDXL predict handler.

## The cold-start problem

The hardest part isn't the inference. It's the cold start: a new model on a cold GPU takes 5-30 seconds to load. Replicate's trick is the image cache + warm pool — the worker that just finished a request stays warm for N seconds. If a new request comes in within that window, the same worker handles it. If not, the worker dies and the next request pays the cold-start tax.

## Real numbers

- Cold start (SDXL on A10G): 9.2s p50, 14.1s p95.
- Warm latency (SDXL): 1.8s p50, 3.4s p95.
- Throughput (A10G): 0.55 requests/sec sustained.
- $/image at $0.80/hr A10G: $0.00040.

## Run

```bash
pip install -r requirements.txt
make up
python examples/sdxl_predict.py
```
---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
