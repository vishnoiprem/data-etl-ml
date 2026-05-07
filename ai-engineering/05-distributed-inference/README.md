# 05 — Distributed Inference & Cost Optimization

> **Customer problem:** GenAI inference spend is tracking to $4.8M/year and growing 22% MoM. Reduce unit cost by ≥50% without breaking SLAs.

This project implements the **router + cache + batch tier** pattern that drives most of the cost wins on production GenAI workloads. The demo is a working in-memory simulator with realistic pricing tables; in production, the same logic ships as an ECS Fargate router in front of Bedrock + SageMaker.

---

## 1. Theory: Where the costs go

For a typical RAG workload at 16M queries/year:

| Layer | Share of cost |
|---|---|
| LLM generation | 90% |
| Reranker | 7% |
| Retrieval (k-NN) | 2% |
| Embeddings | <1% |

So **all** the optimization energy belongs on generation. The four levers, in order of ROI:

| # | Lever | Typical savings |
|---|---|---|
| 1 | **Caching** (semantic + exact) | 25–40% |
| 2 | **Model routing** (small for easy, big for hard) | 30–50% |
| 3 | **Context trimming / compression** | 20–35% |
| 4 | **Batch inference** for non-realtime | 50% on that slice |

Multiplicative compound: 0.7 × 0.6 × 0.7 ≈ **70% reduction** is realistic without quality loss.

## 2. Routing strategy

We classify each query into a difficulty tier and route accordingly:

- **Easy** (≈45% of traffic) — exact-match lookups, simple extractions, factual recall → **Haiku**
- **Medium** (≈40%) — multi-step reasoning, summarization → **Sonnet**
- **Hard** (≈15%) — complex synthesis, long-form analysis → **Opus**

Classification can be:
- **Heuristic** — token count, presence of structural cues (lists, code, math)
- **Tiny LLM classifier** — a few-shot prompt to a Haiku call (<$0.0001 per route)
- **Learned** — distilbert or similar, fine-tuned on routing decisions

## 3. Caching

- **Exact-match cache** — `hash(prompt + model + params)` → response. TTL based on freshness needs.
- **Semantic cache** — embed the prompt, find nearest neighbor in cache; if cosine > 0.95, return cached.
- **Negative cache** — also cache "I don't know" responses to avoid reruns.

## 4. Architecture

```
                        ┌──────────────────┐
                        │   Client / API   │
                        └────────┬─────────┘
                                 │
                                 ▼
                       ┌──────────────────┐
                       │  Router (ECS)    │
                       └─┬────┬────┬─────┘
                  cache  │    │    │ batch
                  hit?   │    │    │ eligible?
                         ▼    ▼    ▼
                ┌────────────────────────┐
                │  ElastiCache (Redis)   │← exact + semantic
                └────────────────────────┘
                         │ miss
                         ▼
              ┌────────────────────────┐
              │ Difficulty classifier  │
              └────┬───────┬───────┬───┘
                   ▼       ▼       ▼
              Haiku   Sonnet   Opus  (Bedrock invoke_model)
                                 │
                       ┌─────────▼─────────┐
                       │  Bedrock Batch    │  ← non-realtime path
                       └───────────────────┘
```

## 5. Quick Start

```bash
pip install -r requirements.txt
make demo
```

Runs 200 simulated queries through the router with realistic difficulty
mix, reports per-strategy cost / latency / cache-hit-rate, and shows the
savings vs. an "always-Opus" baseline.

## 6. What "Done" Looks Like

| Metric | Target |
|---|---|
| Blended cost / 1K tokens | < 50% of baseline |
| p95 latency | < SLO (typically 2.5s) |
| Cache hit rate | ≥ 30% (steady-state) |
| Routing accuracy (vs. quality SLO) | ≥ 95% |
