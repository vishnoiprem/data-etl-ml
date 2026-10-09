# 21 — Metrics & Logging Service (Prometheus + Loki)

A unified observability backend that ingests **time-series metrics** (counter /
histogram samples) and **structured log streams**, then serves both via
range queries. In spirit this is a tiny Prometheus + Loki combined.

## Requirements

### Functional
- Ingest metrics: `POST /api/metrics` with `{name, value, labels, ts}`.
- Ingest logs:   `POST /api/logs` with `{ts, level, msg, labels}`.
- Range query:   `GET /api/query?metric=&from=&to=&step=&agg=`.
- Log search:    `GET /api/logs?q=<substring>` (substring over msg + labels).
- Aggregations on metrics: `sum`, `avg`, `max`, `min`, `count`.

### Non-functional
- Sub-millisecond ingest on the hot path (in-process).
- Range query buckets to 60s by default.
- Bounded memory via per-series cap and bounded in-memory samples.
- Thread-safe (Flask under threaded WSGI).

## Capacity

| Dimension | Assumption |
| --- | --- |
| Active series | 100k |
| Samples/sec | 50k |
| Log lines/sec | 5k |
| Retention (in-mem) | 1h for metrics, 1h for logs |
| Query rate | 100 QPS, p95 < 50ms |

## High-level architecture

```
   client ──▶ POST /api/metrics ─┐
                                  │
   client ──POST /api/logs ───────┼──▶ In-process pipeline
                                  │         │
                                  │         ▼
                                  │    ┌─────────────────┐
                                  │    │  KeyValueStore  │  (per-series bucket
                                  │    │  (time buckets) │   of samples + log
                                  │    └─────────────────┘   lines by ts index)
                                  │         │
   client ──▶ GET /api/query ─────┘         ▼
                                    Aggregation / search
```

- **Metrics path** mirrors Prometheus: each series is keyed by
  `(name, sorted-label-tuple)`. Samples are bucketed by floor(ts/step) and
  aggregated on read.
- **Log path** mirrors Loki: lines are appended under `(labels, ts)`;
  search is a full scan with a substring filter (we don't implement
  log-QL; this is the minimal cut).

## API

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/metrics` | Ingest one or many samples. |
| GET  | `/api/query` | Range query, returns downsampled series. |
| POST | `/api/logs` | Ingest log lines. |
| GET  | `/api/logs` | Search log lines by `q` substring. |
| GET  | `/health` | Liveness + size stats. |
| GET  | `/metrics` | Scrape service-internal metrics. |

### `/api/query` params
- `metric` — metric name (required).
- `from`, `to` — unix-seconds or ms (required).
- `step` — bucket size in seconds (default 60).
- `agg` — one of `sum|avg|max|min|count` (default `avg`).
- `label.<k>=<v>` — filter by label.

## Data model

```
kv["series:<name>:<labels>"]  -> { "samples": [[ts, value], ...],
                                    "first_ts": int, "last_ts": int }
kv["log:<floor(ts/60)>:<seq>"] -> { "ts": int, "level": str, "msg": str,
                                     "labels": dict }
kv["logs:index"] -> [seq, ...]    # linear list of log keys for full scan
```

## Read / Write paths

**Write (metrics)**:
1. Parse `{name, value, labels, ts}`.
2. Compose series key `series:<name>:<k1=v1,k2=v2>` (label keys sorted).
3. Append to in-memory list, cap at `MAX_SAMPLES_PER_SERIES`.

**Read (range query)**:
1. Lookup all series matching the metric name and label filters.
2. Bucket samples into `[from, to]` by `step`.
3. Apply `agg` per bucket, return `[{t, v}]`.

**Write (logs)**: append under `log:<bucket>:<seq>`, push key to index.

**Read (logs)**: scan index, filter by substring over `msg` and label values.

## Failure modes

| Failure | Mitigation |
| --- | --- |
| Hot series blowup | Per-series cap; oldest samples dropped first. |
| Bad ts in payload | Clamp to current ms. |
| Label cardinality explosion | Not bounded here; in production enforce via admission. |
| Search on huge index | Cap returned rows; add pagination. |

## Tradeoffs

- **Bucket-on-read** keeps ingest simple but adds work at query time.
  Bucket-on-write (e.g. Prometheus' head block) is faster for reads but
  more code; we trade read cost for code clarity.
- **In-process store** loses data on crash. Production would back this
  with TSDB (M3DB, VictoriaMetrics) and Loki/Chunks.

## Code map

- `code/service.py` — `MetricsLoggingService` (ingest + query + log search).
- `code/app.py` — Flask app exposing the API + `/metrics` + `/health`.
- `tests/test_service.py` — service-layer unit tests.
- `tests/test_app.py` — HTTP-level tests.
