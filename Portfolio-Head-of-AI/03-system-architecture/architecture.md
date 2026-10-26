# Architecture

The build-vs-buy doc recommends Path A first. This document describes
the architecture that supports *both* paths, because that's the point
— the serving and monitoring spine is identical whether the model is
a third-party API (Path A) or a fine-tuned self-hosted adapter (Path
C).

If the two paths need different serving stacks, switching paths costs
a quarter. If they share one, switching costs a config change.

## The shape

```
            ┌─────────────────────────────────────────────┐
            │  Control plane (once per initiative)        │
            │                                             │
   curate ──▶│  dataset → tokenize → filter → split       │
            │  eval set ──▶ versioned, held out           │
            │  taxonomy ──▶ versioned buckets             │
            └─────────────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────────────┐
            │  Training plane (Path C only)               │
            │                                             │
   QLoRA ──▶│  base model → LoRA adapter → merge         │
            │  4-bit NF4, r=16, all-linear targets        │
            │  gates: budget · wall-clock · retries      │
            └─────────────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────────────┐
            │  Registry plane (both paths)                │
            │                                             │
            │  MLflow: params · metrics · artifacts      │
            │  run_id on every artifact                   │
            │  @Champion alias → the version being served │
            └─────────────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────────────┐
            │  Serving plane (both paths)                 │
            │                                             │
            │  FastAPI ──▶ OpenAI-compatible surface      │
            │  /v1/chat/completions                       │
            │  /healthz · /metrics                        │
            │  adapter hot-load (Path C)                  │
            └─────────────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────────────┐
            │  Observability plane (both paths)           │
            │                                             │
            │  Prometheus: latency · tokens · cost · err  │
            │  Grafana: provisioned dashboards            │
            │  Evidently: drift on request embeddings    │
            └─────────────────────────────────────────────┘
```

## The design decision everything else follows from

**The client is the same in both paths.**

`agent/client.py` talks to an OpenAI-compatible endpoint. In Path A
that endpoint is a vendor's API. In Path C it's our vLLM server
behind a FastAPI wrapper. Same client, same retry semantics, same cost
accounting, same batch report.

The consequence is specific and important: **the cost column in
`../01-problem-and-constraints/success-metrics.md` and the cost in the
live system cannot drift apart**, because they're computed by the same
code path. If we'd written two clients — one for the vendor, one for
vLLM — we'd have two cost models, and within two quarters they'd
disagree and nobody would know which one Finance believed.

This is the "wired to the reference implementation" claim in every
chapter of this document, and it starts here.

## Why FastAPI in front of vLLM

vLLM already exposes an OpenAI-compatible server and a Prometheus
`/metrics`. Why not point the client at vLLM directly?

Three reasons:

1. **We need instrumentation vLLM doesn't have.** Specifically,
   *cost per request attributed to an adapter alias*. vLLM knows
   about LoRA adapters; it doesn't know that adapter `champion-v3`
   costs $X per 1k tokens for our business. That's business logic,
   and it belongs in our layer.
2. **We need a single budget gate on the serving path.**
   `agent/gates.py` refuses the next request once a limit is hit.
   Putting that in front means we can fail closed — a 429 with a
   reason, not an unbounded bill.
3. **Adapter routing is ours.** Path A → vendor model name. Path C →
   local endpoint + adapter alias. Same client code, different routing
   config.

The cost of the extra hop is one process on localhost and maybe
3–5ms p50. Worth it.

## Why MLflow and not a spreadsheet

Because "which model served this request yesterday" has to be a
one-line query, and it can't be if the answer lives in a doc.

MLflow gives four things this architecture needs:

| Need | MLflow mechanism |
|---|---|
| Compare two training runs | Run params + metrics, same keys |
| Find which version served a request | `run_id` stamped on the artifact, alias on the registry |
| Roll back | Point `@Champion` at the previous run |
| Prove audit trail | Join request log → alias → run_id → params |

That last row is the compliance constraint from
`../01-problem-and-constraints/constraints.md` (§4) — the audit trail
requirement that "looks like paperwork until it doesn't." The audit
trail format is: request → timestamp → adapter alias → `run_id` →
training params → base model revision. All of it exists because of
how we registered the model, not because we wrote a compliance doc.

## The base-model-revision problem

The reference implementation logs the base model name. In production
it must log the **revision hash**.

Base models get updated under the same name. A LoRA adapter trained
against `Llama-3.1-8B-Instruct` from March is not reliably compatible
with the weights from September. If you don't pin the revision, you
get a serving error six weeks after training with no obvious cause.

```python
# agent/config.py
base_model: str = "meta-llama/Llama-3.1-8B-Instruct"
base_model_revision: str = "e5f0..."   # required in production, optional in dev
```

This is a one-line config field that prevents a class of bug that
costs days. It's the kind of thing I want in a design doc explicitly,
because it will not be discovered by reading the code carefully — it
will be discovered by an incident.

## What runs where

| Component | Where | Sizing |
|---|---|---|
| MLflow server | Docker, company network | 2 vCPU / 4 GB |
| vLLM server | Docker, GPU host | 1× A10G or L4, 24 GB |
| Prometheus | Docker | 1 vCPU / 2 GB |
| Grafana | Docker | 1 vCPU / 1 GB |
| QLoRA training | Ephemeral GPU pod | 1× A100 40 GB preferred, 24 GB workable |
| Reranker / embeddings | Same GPU host as vLLM | Shared, watch VRAM |

The VRAM-sharing note is real. vLLM preallocates. If training runs on
the same GPU, one of them OOMs. Separate hosts, or accept that training
and serving don't coexist.

## Deliberately not in this architecture

| Not included | Why |
|---|---|
| Kubernetes manifests | Docker Compose is legible and the team can debug it. k8s is a 3-week project that defers every real question. |
| Multi-node / FSDP training | 8B QLoRA fits on one GPU. Multi-node is a different program. |
| Triton / TensorRT-LLM | vLLM at 8B hits the latency target. Revisit at 70B. |
| RLHF / DPO | SFT first. You can't do preference optimization without preference data, and you don't have it. |
| A feature store | No online features. This is a text-in/text-out system. |

Each of these is a *later* problem. Building them now means building
them without knowing what they'll need to do.

## Failure modes this architecture can survive

| Failure | What happens | Recovery |
|---|---|---|
| Adapter produces garbage | Error rate alert fires | Point `@Champion` at previous run; restart vLLM |
| Drift in request distribution | Drift gauge > 0.3 for 5 days | Re-run Tier 2 eval; decide refresh vs rollback |
| GPU dies | `/healthz` fails, Prometheus alerts | Failover to Path A API — same client, same surface |
| Cost run | Budget gate refuses requests | Gate is a feature; the run is bounded by design |
| vLLM version regression | Latency p95 climbs post-upgrade | Adapter + pinned base revision let us pin vLLM too |

That third row is the one that justifies the shared-client decision.
The Path A → Path C → back-to-Path-A story is a config flip, not a
migration. I've had to do that migration twice and it cost a quarter
each time.

## The rule I hold

> If you cannot answer "which model served this request, from which
> base revision, at what cost, in how long" in under a minute, the
> architecture is not done.

That query spans the registry, the serving layer, the observability
layer, and the cost accounting. If it works, everything else in this
document works. If it doesn't, no amount of additional infrastructure
fixes the underlying problem, which is that you can't observe your own
system.