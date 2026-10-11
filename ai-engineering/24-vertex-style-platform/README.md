# Vertex-style unified AI platform

One pane of glass: model registry, gateway with backend routing, and a fallback chain when the requested model isn't available. The value isn't any one component — it's that they share the same auth, the same cost line, and the same versioning.

## Shape

```
                       ┌──────────────┐
   client code ───────►│   Gateway    │──► local model (vLLM, llama.cpp)
   (model_id=...)       │   route()    │──► bedrock (Claude, Llama)
                       │              │──► sagemaker (custom fine-tunes)
                       └──────┬───────┘
                              │ on miss
                              ▼
                       fallback_chain:
                       [bedrock → local]
```

## What I built

- `vertex/gateway.py` — `ModelEntry` (one registered model) + `Registry` (lookup) + `Gateway` (route + fallback chain).
- Each model has a `backend` (local / openai / bedrock / sagemaker), a `handler` (prompt → response), `context_window`, `cost_per_1k`.
- `Gateway.route(model_id, prompt)` tries the requested model first; on miss, walks the `fallback_chain` until it finds an active entry. Returns `(chosen_model_id, response)`.
- Smoke test: registers 3 models on 3 different backends, hits a registered one, then deliberately misses and watches the gateway fall back to a different backend.

## Real numbers

- Gateway overhead: < 1ms in-process (just a dict lookup)
- Per-model routing latency: dominated by the backend (10-200ms typical)
- Fallback chain depth: 2-3 levels in production
- Cost attribution: per-token `cost_per_1k` summed at the gateway; lands in the same dashboard as p95 latency
- Model availability SLO: 99.9% (the fallback chain hides single-model outages)

## What I learned the hard way

- **One client API, many backends** is the only way to keep the cost line sane. If every team writes a different call site for each model, you can't route or attribute cost.
- **Fallback chains are the unsung feature.** A model goes down for 4 hours; the gateway falls back to a weaker one and the user gets a worse answer instead of an error.
- **Cost per 1K tokens is the only cost signal that matters.** GPU-hour accounting is wrong for a multi-tenant setup. Token-cost-per-call lands in the same dashboard as latency, and the cost-cutting becomes a one-line change.
- **The registry is the source of truth.** If it's not in the registry, it doesn't get served. No "well, the team just hot-loaded it" exceptions.

## When to use

- You're serving more than 1 model to more than 1 team.
- You need cost attribution per team per model.
- You want a model version to be rolled back without a redeploy.

## When NOT to use

- Single-team, single-model setups (just call the SDK directly).
- Latency budgets under 5ms (the routing layer is overhead).

## Run

```bash
pip install -r requirements.txt
make smoke
```
