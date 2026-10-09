# 36 — LLM Query Batching (Dynamic Batching / Continuous Batching)

> **Module 4 of 6 — Agentic AI Systems**

A complete, runnable design + implementation of a dynamic batching
dispatcher for LLM queries. The engineering problem is the same one
that vLLM, TGI, and TensorRT-LLM solve:

> GPU inference is dominated by **prefill** (the cost of processing the
> prompt) and the **per-request overhead** of launching a forward pass.
> Amortizing those costs across N requests gives nearly N× throughput.

The classic solution: an *arrival window* collects queries for up to
`window_ms` or until `batch_size` queries are buffered, then issues
*one* combined inference call. Each query is resolved with its own
slice of the response.

---

## 1. Requirements

### Functional
- `POST /api/queries` enqueues a prompt and returns a `query_id` immediately.
- `GET /api/queries/<id>` returns the result (with optional `wait=1` polling).
- The arrival window flushes on EITHER `batch_size` or `window_ms`.
- Batched inference is one call, with N responses.
- `POST /api/queries/flush` forces a manual flush.

### Non-functional
- **Throughput**: N queries should produce `ceil(N / batch_size)` batches.
- **Latency**: per-query wait time ≤ `window_ms` on average.
- **Bounded memory**: only one window's worth of queries held in RAM.
- **Observable**: stats endpoint reports `batches`, `avg_batch_size`,
  `throughput_x`, `avg_wait_ms`, `max_batch_size`.

### Out of scope
- Real LLM forward pass.
- Priority lanes (all queries are equal here).
- Speculative decoding.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Incoming QPS | 1,000 queries/sec |
| batch_size | 8 |
| window_ms | 25 |
| Effective batch rate | ~1,000 / 8 ≈ 125 batches/sec |
| GPU forward passes / sec | ~125 (vs 1,000 unbatched) — **8× reduction** |
| Per-batch GPU time | ~50 ms (prefill + decode) |
| Avg per-query wait | ~12.5 ms (half a window) |

The math: batching 8 queries into one forward pass reduces
per-token prefill cost by ~8× and amortizes launch overhead.

---

## 3. High-level design

```
       client ──► POST /api/queries ──► arrival window
                                            │
                                            │ trigger 1: window full
                                            │ trigger 2: window_ms elapsed
                                            ▼
                                    ┌────────────────┐
                                    │  batched call  │   (mock LLM here,
                                    │   to LLM       │    vLLM in prod)
                                    └────────┬───────┘
                                             │ N responses
                                             ▼
                                    resolve each query
                                             │
                                             ▼
       client ◄── GET /api/queries/<id>?wait=1 ── {response, batch_id, wait_ms}
```

State machine for a single query:

```
  submitted ──► in_window ──► batching ──► done
                    │             │           │
                    └─(timeout)───┘           │
                                              ▼
                                          stats update
```

State machine for the window itself:

```
  empty ──submit──► filling ──(full)──► flushing ──► empty
                       │                  
                       └──(window_ms)──► flushing
```

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/queries` | `{prompt, max_tokens?}` | `{query_id, status:"pending"}` |
| `GET`  | `/api/queries/<id>` | — | `{status, response, batch_id, wait_ms, ...}` |
| `GET`  | `/api/queries/<id>?wait=1&timeout=5` | — | blocks until done |
| `POST` | `/api/queries/flush` | — | `{flushed: N}` |
| `GET`  | `/api/queries` | — | list of recent queries |
| `GET`  | `/stats` | — | batching metrics |
| `GET`  | `/metrics`, `/health` | — | metrics / health |

---

## 5. Data model

### Query

```json
{
  "query_id": 42,
  "prompt": "Explain B+-trees",
  "max_tokens": 256,
  "created_at": 1700000000.0,
  "completed_at": 1700000000.012,
  "response": "[batch-slot 0] response to: ...",
  "tokens": 12,
  "batch_id": 5,
  "wait_ms": 12.3
}
```

### In-flight state

- `inflight: list[Query]` — the current arrival window.
- `queries: dict[int, Query]` — every query ever submitted, indexed by id.
- `_window_started_at: float` — start of the current window.

---

## 6. Write path deep dive: submit

`submit(prompt, max_tokens)`:

1. Validate inputs.
2. Allocate a `query_id`.
3. Append the query to `inflight`. If `inflight` is empty, set
   `_window_started_at = now`.
4. If `len(inflight) >= batch_size`, signal the flusher.
5. Return the `query_id` immediately (the caller polls / waits).

The flusher thread waits on a condition variable. It wakes on:
- A notify (batch full).
- A timeout (window expired).

When it wakes, if `inflight` is non-empty AND either `len >= batch_size`
OR `elapsed_ms >= window_ms`, it calls `_flush_locked`.

`_flush_locked`:
1. Pop the current window.
2. Call the mock LLM with all prompts at once.
3. Stamp each query with its response, batch_id, and wait_ms.
4. Update stats and notify waiters.

---

## 7. Read path deep dive: get

`get(query_id, timeout)`:

1. Wait on the condition variable, with `timeout` if provided.
2. As soon as the query has a `response`, return it.
3. If the timeout expires, return the partial query (response=None).

The HTTP layer exposes this as `GET /api/queries/<id>?wait=1&timeout=5`
— typical "long-poll" pattern that avoids client-side polling.

---

## 8. Failure modes

| Failure | Mitigation |
|---|---|
| Flusher dies | One flusher per process; restart on liveness probe. |
| Hot query stragglers | `window_ms` caps wait time at the cost of small batches. |
| Backpressure | `GET ?wait=1` blocks; clients see a slow query. |
| Crash mid-batch | In-memory state lost; clients resubmit by `query_id`. |
| Out-of-order responses | None here — N responses for N prompts. |

---

## 9. Tradeoffs

- **Static vs dynamic batching**: dynamic (this) adapts to traffic.
  Static would pre-group by prompt length, which is wasteful.
- **Continuous batching** (vLLM): the window flushes when *any* request
  in the batch finishes, not when the slowest finishes. We model the
  simpler window-based version.
- **Per-request priority**: real systems let premium traffic cut the
  line. We treat all queries equally.
- **Memory**: a long window on a hot GPU = more KV cache pressure.
  `batch_size` is the real lever; `window_ms` is the latency lever.

---

## 10. Code map

| File | Role |
|---|---|
| `code/service.py` | `BatchingService` — submit / get / flusher loop / stats. |
| `code/app.py` | Flask HTTP service with long-poll `GET ?wait=1`. |
| `tests/test_service.py` | Service-level tests (batch_size trigger, window trigger, throughput, flush). |
| `tests/test_app.py` | HTTP-level tests for the API. |
