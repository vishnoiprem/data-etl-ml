# Serving Decisions

The serving plane in `architecture.md` is the part that touches a
customer request. Every decision below is reversible cheaply. The
mistakes that aren't cheaply reversible are the ones I want to be
specific about.

## The decision tree

```
                  ┌─────────────────────────┐
                  │  Latency budget?        │
                  └────────────┬────────────┘
                               │
              ┌────── <100ms ──┴── ≥100ms ──────┐
              ▼                                  ▼
    NOT building an LLM            ┌──────────────────────────┐
    product. Use a smaller          │ Concurrency target?      │
    classifier / cache.             └────────────┬───────────┘
                                               ┌┴─┐
                                               ▼  ▼
                                       <10 RPS   ≥10 RPS
                                       one vLLM  pool + load balance
```

If the latency budget is <100ms, the right answer is almost never an
LLM. That decision is upstream of everything else in this document.
The latency table is from
`../01-problem-and-constraints/constraints.md` (§3); it's worth
copying here because it bounds which serving shape is even on the
menu:

| Latency budget | Realistic serving target |
|---|---|
| <100ms p95 | Small base + aggressive caching + small context. Edge-only. |
| <500ms p95 | Open 7B-class on a GPU, continuous batching |
| <2s p95 | Same with longer context, or 8B with vLLM |
| <10s p95 | Anything reasonable; chat assistants easily here |

The ticket-classification workload in
`../01-problem-and-constraints/build-vs-buy-decision.md` sits in the
500ms–2s band. That's the band vLLM hits handily.

## Why vLLM, not TGI, not Triton

| Option | Reason not |
|---|---|
| **HuggingFace TGI** | Strong Rust core, weaker LoRA hot-swap story. The adapter workflow is the whole point of Path C. |
| **NVIDIA Triton + TensorRT-LLM** | Best latency per watt at 70B+. Overkill at 8B; we don't have the engineering team to maintain the build artifacts. |
| **vLLM (chosen)** | OpenAI-compatible, `--enable-lora`, continuous batching default-on, PagedAttention handles long-prompt/short-burst mix naturally. |

None of these is wrong; they're different points on the engineering
investment curve. vLLM is the point where investment is roughly equal
to feature fit.

## Adapter hot-load vs. baked-in serving

Two ways to serve a LoRA adapter on top of a base model:

1. **Merge at build time.** Adapter is fused into a new model
   weights set. Single artifact, no vLLM `--enable-lora` needed.
2. **Hot-load at runtime.** Base weights stay in VRAM; adapter is
   loaded per-request into KV-cache pages. Different adapters per
   request.

We use option 2 because:

- **Rollback** is one alias change, not one container rebuild.
- **A/B testing** two adapter versions becomes *route by adapter*,
  not *route by URL*.
- **Build time stays sub-30-seconds.** A merged 8B with our 16-rank
  adapter is still ~16 GB; re-serving it on every iteration is
  impractical.

The cost is complexity in vLLM's request routing and slightly lower
QPS per adapter, both of which are bounded problems with monitoring.

## Continuous batching

On by default in vLLM. Why I'm naming it explicitly: the alternative
is static batching, where a batch of 8 in-flight requests blocks for
the longest of them. Continuous batching slots the next request in as
each generation completes. For the workload mix here (long reasoning
+ short classification in the same pool), this is the difference
between 200 RPS and 60 RPS at the same GPU.

## The budget gate is in the serving plane

`agent/gates.py` is imported by `agent/serve.py`. The gate refuses
the request with a 429 before it touches the model. This is unusual
but worth being specific about:

- **Most places don't put a budget gate on inference.** They put it
  on training runs. I argue for putting it on inference *because
  inference is where the spend actually compounds*. A training run
  that goes over budget costs a few hundred dollars; an inference
  path that doesn't refuse can cost that in an afternoon.
- **The gate is a feature, not a safety net.** When the gate fires
  the user gets a structured response (`reason="monthly_budget"`)
  and a queued retry, not a hard failure. The product gets to
  decide whether to show a degraded experience or refuse.
- **The gate's units matter.** It checks *dollar spend per
  rolling window*, not *request count* — because the cost of 1
  request to a 70B model is 20× the cost of 1 request to an 8B
  model, and a request-count gate is broken at the moment you swap
  adapters.

## Connection pooling and timeouts

Tuning that bites people in production:

| Setting | Default | What I'd set | Why |
|---|---|---|---|
| Client-side timeout | 30s | 10s | A 30s request is a 30s user-perceived failure. Fail fast, retry. |
| Server-side queue timeout | ∞ | 5s | An unbounded queue grows memory and stalls. Refuse fast instead. |
| Client-side retries | 3 | 2 | Beyond 2, you're hiding a real outage. |
| Server-side keepalive | 5s | 30s | Long-lived streaming clients. |
| Server-side max concurrent | default | GPU_memory_budget / KV_per_request | Derive from VRAM, not from a number. |

The "fail fast, retry" pattern looks flip until you measure: each
minute of a 30s timeout costs the user the page-load and you the
serving slot. Re-trying with a 10s timeout saves both.

## Token streaming vs. batch-completion

| Pattern | Use when |
|---|---|
| `stream=True` | Long completions, anything user-facing |
| `stream=False` | Internal batch classification, anything behind a worker |

Reference implementation supports both; the cost report in
`agent/client.py` reports per-pattern p50/p95 separately. Mixing
streaming and non-streaming latencies into one bucket is a classic
dashboard lie.

## What I would refuse to do

| Refusal | Why |
|---|---|
| Build the serving plane before the latency budget is measured | "Sub-second" has 4 meanings; pick one before picking the serving shape |
| Run on the cheapest GPU and call it done | A 7B model on a T4 looks fine in demo; under load it's a different system |
| Skip continuous batching because the workload "isn't that bursty" yet | Once you commit a 200ms p95 contract, retooling batching is a quarter |
| Let the client pick the adapter | The serving layer holds the alias; the client holds the budget |
| Ship without a budget gate on inference | A budget gate on training is half a measure |

## The rule I hold

> The serving plane is the unit of productization. Everything upstream
> is research; everything downstream is business model.

The 9.4% hallucination rate in the build-vs-buy doc is a training
problem. The $4k/day burn is a serving problem. The serving problem
is the one that closes the loop with Finance, and Finance is the
constraint the Head of AI gets hired to make legible.