# 25 — Weather App (Cache + Provider Fanout + Circuit Breaker)

A weather backend that fans out to multiple upstream providers, caches
results by lat/lng grid cell, and isolates failures with a
**circuit-breaker** per provider.

## Requirements

### Functional
- `GET /api/weather?lat=&lng=` — return current weather for a location.
- `GET /api/providers` — list providers with health stats.
- Three simulated providers with different reliability profiles.
- Cache responses by grid cell (round lat/lng to 0.1° ≈ ~11km).
- Circuit breaker: after N consecutive failures, mark provider "open"
  for a cooldown window.

### Non-functional
- A failing provider must not block requests (use timeout / breaker).
- Cache hit avoids all provider calls.
- Healthy providers are tried in priority order.

## Capacity

| Dimension | Assumption |
| --- | --- |
| QPS | 5k |
| Unique grid cells | 50k |
| Cache TTL | 5 min |
| Provider fanout | 3 providers |
| Breaker threshold | 3 failures |
| Breaker cooldown | 30 s |

## High-level architecture

```
   client ──GET /api/weather──▶ WeatherService
                                    │
                            ┌───────┴───────┐
                            │   grid cache  │──hit──▶ response
                            └───────┬───────┘
                                    │ miss
                                    ▼
                            ┌───────────────┐
                            │  providers[]  │  (priority order)
                            │  each with:   │
                            │   - circuit   │
                            │   breaker     │
                            │   - latency   │
                            └───────┬───────┘
                                    │ first success
                                    ▼
                            write to cache, return
```

- **Grid cell key**: `grid:<round(lat,1)>:<round(lng,1)>`.
- **Provider**: a function that returns `{temp, conditions, wind, ...}`
  or raises. Each provider has a name, a reliability knob (random fail
  rate), and a priority.
- **Circuit breaker** state per provider: `CLOSED → OPEN → HALF_OPEN`.
  - `CLOSED`: try the provider.
  - `OPEN`: skip until cooldown elapses.
  - `HALF_OPEN`: allow one trial; success → CLOSED, failure → OPEN.

## API

| Method | Path | Description |
| --- | --- | --- |
| GET  | `/api/weather` | Returns weather (cached or freshly fetched). |
| GET  | `/api/providers` | Returns provider health. |
| GET  | `/health` | Liveness. |
| GET  | `/metrics` | Service-internal metrics. |

### `/api/weather` params
- `lat`, `lng` (required)
- `nocache=1` — bypass cache

## Data model

```
kv["grid:<lat>:<lng>"] -> {payload, fetched_at_ms, provider}
kv["cb:<provider>"]    -> {state, failures, opened_at_ms}
```

## Read / Write paths

**Weather request**:
1. Compute grid key.
2. If cache hit (and not stale), return payload + `cache_hit: true`.
3. Iterate providers in priority order:
   - If breaker is OPEN and cooldown not elapsed, skip.
   - Try provider with a per-call simulated latency/failure.
   - On success: close breaker, cache, return.
   - On failure: register failure, try next.
4. If all providers fail, return 503 with breaker states.

**Provider health**: read breaker states + per-provider success / fail
counters.

## Failure modes

| Failure | Mitigation |
| --- | --- |
| Provider times out | Treat as failure; breaker eventually opens. |
| All providers down | Return last cached value (if any) or 503. |
| Cache miss + breaker open | Try other providers; degrade gracefully. |
| Cache stale | TTL enforces freshness; honor `nocache` to bypass. |

## Tradeoffs

- **Provider priority is static**. Production would use a
  success-rate-weighted scheduler.
- **Cache key is coarse** (0.1°). Two addresses 5 km apart may share
  a cached forecast. Tighten by tuning the rounding.
- **In-process state** for breakers. A multi-instance deployment
  would centralize breaker state in Redis.

## Code map

- `code/service.py` — `WeatherService`, `CircuitBreaker`,
  `SimulatedProvider`.
- `code/app.py` — Flask app.
- `tests/test_service.py` — service tests.
- `tests/test_app.py` — HTTP tests.
