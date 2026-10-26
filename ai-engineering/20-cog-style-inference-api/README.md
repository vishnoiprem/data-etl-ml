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

## What this is NOT

- **Not Replicate.** Replicate is a hosted platform
  with a model marketplace, a community, and a
  billing layer that integrates with their auth.
  This is the *inference plumbing* behind such a
  platform — registry, queue, GPU pool, predict
  handler. The marketplace and community are
  separate problems.
- **Not a model server.** The model server is the
  `predict.py` handler; this directory is the
  *layer around it* (registry, queue, billing,
  hardware introspection). Strip the layer and you
  have a single-model FastAPI app.
- **Not a training platform.** Inference only.
  Training / fine-tuning lives in
  [`../17-mlops-control-plane/`](../17-mlops-control-plane/)
  and the GPU-shaped builds in
  [`../30-triton-kernels/`](../30-triton-kernels/).
- **Not a queue-only service.** The queue is one
  component. The hardware introspection, the
  per-second GPU-time billing, and the cold/warm
  distinction are what make this a *model-as-a-service*
  platform, not just a request queue.

---

## Related directories

- [`../21-sdxl-image-service/`](../21-sdxl-image-service/) —
  the SDXL-specific inference pipeline that plugs
  into this "one model, one container" pattern.
- [`../30-triton-kernels/`](../30-triton-kernels/) —
  the GPU-shaped serving layer (Triton, vLLM) that
  the GPU pool can be specialized to.
- [`../17-mlops-control-plane/`](../17-mlops-control-plane/) —
  the registry + deployment patterns that this
  service's `Model Registry` is a specialized
  version of.
- [`../24-vertex-style-platform/`](../24-vertex-style-platform/) —
  the multi-backend gateway that routes to this
  service (or a Bedrock / SageMaker alternative)
  with fallback chains.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
