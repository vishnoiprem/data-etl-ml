# 22 — Application Performance Monitoring (APM)

A distributed APM that ingests **spans** (parent-linked trace tree),
**per-service metrics**, and **errors**, then serves trace lookups, service
catalogs, and error-rate rollups. Think of a tiny combination of Jaeger +
Datadog APM.

## Requirements

### Functional
- Ingest spans: `POST /api/spans` with `{trace_id, span_id, parent_span_id,
  service, name, start_ms, duration_ms, status, tags}`.
- Get a full trace tree: `GET /api/traces/{trace_id}`.
- List known services: `GET /api/services`.
- Per-service error rate: `GET /api/services/{name}/error_rate?window_s=`.
- Per-service latency percentiles (p50/p95/p99): endpoint above with
  `?latency=true`.

### Non-functional
- Snowflake-generated `span_id` if missing.
- Thread-safe ingest.
- Bounded trace buffers (cap on spans per service).

## Capacity

| Dimension | Assumption |
| --- | --- |
| Services | 200 |
| Spans/sec | 100k |
| Avg trace depth | 8 |
| Active traces | 50k |
| Trace retention | 30 min in-mem |

## High-level architecture

```
 agent/SDK ──▶ POST /api/spans ─▶ SpanStore (KeyValueStore)
                                    │   traces:<id> -> [span, ...]
                                    │   spans:index -> [trace_id, ...]
                                    │   svc:<name>:spans -> [span, ...]
                                    ▼
                                ┌───────────────┐
   client ──▶ GET /api/traces ─┤ Aggregations  ├─▶ p50/p95/p99, error rate
                                └───────────────┘
```

- **Spans** are stored in three projections:
  1. By trace id (for trace lookup).
  2. A global index of trace ids (LRU-ish, capped).
  3. Per-service append-only log (for percentiles / error rate).
- **Errors** are just spans with `status == "error"`. A separate counter
  tracks errors per service over a sliding window.

## API

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/spans` | Ingest a span. |
| GET  | `/api/traces/{trace_id}` | Returns the trace tree. |
| GET  | `/api/services` | List of known services + span count. |
| GET  | `/api/services/{name}/error_rate` | Error rate + latency p50/p95/p99. |
| GET  | `/health` | Liveness. |
| GET  | `/metrics` | Service-internal metrics. |

## Data model

```
kv["trace:<id>"]            -> [span_dict, ...]   (all spans for the trace)
kv["svc:<name>:spans"]       -> [span_dict, ...]   (capped per-service buffer)
kv["services"]               -> {name: span_count}
kv["traces:index"]           -> [trace_id, ...]    (capped)
```

`span_dict`:
```json
{
  "trace_id": "abc",
  "span_id": 12345,
  "parent_span_id": 0,
  "service": "checkout",
  "name": "POST /charge",
  "start_ms": 1700000000000,
  "duration_ms": 80,
  "status": "ok",
  "tags": {}
}
```

## Read / Write paths

**Ingest**:
1. Generate `span_id` (Snowflake) if missing.
2. Append to `trace:<id>`.
3. Append to `svc:<name>:spans` (cap at `MAX_SPANS_PER_SVC`).
4. Update `services` count and `traces:index`.

**Trace lookup**:
1. Fetch `trace:<id>`.
2. Group by `span_id`, link parents → children.
3. Return roots + flat list of all spans.

**Error rate / latency**:
1. Scan `svc:<name>:spans` (last `window_s` seconds).
2. Count `status == "error"` → divide by total.
3. Sort `duration_ms`, take p50/p95/p99.

## Failure modes

| Failure | Mitigation |
| --- | --- |
| Trace id collision | Snowflake gives ~0 collision; we also dedup on span_id. |
| Hot service blows buffer | Per-service cap; oldest spans evicted. |
| Slow percentile scan | Bounded buffer (5k spans) keeps it constant. |
| Cardinality explosion on service names | Not bounded here; production enforces allow-list. |

## Tradeoffs

- **Per-service buffer** is fast for percentiles but means we lose older
  data. Production would push to a TSDB (Prometheus / M3) for proper
  retention.
- **Snowflake span_id** is dense and time-sortable; alternative is random
  64-bit UUIDs. We choose Snowflake for the teaching tie-in.
- **In-memory only**: data lost on restart. Production uses a
  write-ahead log + cold storage.

## Code map

- `code/service.py` — `APMService` (ingest, traces, error rate).
- `code/app.py` — Flask app.
- `tests/test_service.py` — service-level tests.
- `tests/test_app.py` — HTTP tests.
