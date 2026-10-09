# 24 — Zillow (Real-Estate Listings with Geolocation)

A real-estate listings backend: properties indexed by id, searchable by
geographic radius and price. Mirrors Zillow's "search homes near X"
experience at a tiny scale.

## Requirements

### Functional
- Create listing: `POST /api/listings` with `{lat, lng, price, beds, baths,
  sqft, address?}`.
- Get listing: `GET /api/listings/{id}`.
- Search: `GET /api/search?lat=&lng=&radius_km=&max_price=&min_beds=`.

### Non-functional
- Sub-100ms search for the in-memory dataset.
- Haversine for great-circle distance.
- Bounded in-memory storage; backed by `KeyValueStore`.

## Capacity

| Dimension | Assumption |
| --- | --- |
| Listings | 1M |
| Search QPS | 1k |
| Avg listings within 5km radius (urban) | 5–50k |
| Read/write ratio | 100:1 |

## High-level architecture

```
   client ──POST /api/listings ─▶ ZillowService
                                       │
                                       ▼
                                 KeyValueStore
                                  ├ listing:<id> -> dict
                                  └ listings:index -> [id, ...]
                                       │
   client ──GET /api/search ───────────┘
                                       │
                                       ▼
                              scan + haversine filter
                                       │
                                       ▼
                                  sorted response
```

Search is a linear scan over `listings:index` with a Haversine filter
plus price / beds / baths / sqft filters. This is fine for the in-memory
example; production would use a geohash / S2 index.

## API

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/listings` | Create a listing. |
| GET  | `/api/listings/{id}` | Fetch a listing. |
| GET  | `/api/search` | Search by geo + filters. |
| GET  | `/health` | Liveness. |
| GET  | `/metrics` | Service-internal metrics. |

### Search query params
- `lat`, `lng` (required) — search center.
- `radius_km` (default 5).
- `max_price` (optional) — drop listings above this price.
- `min_beds` / `min_baths` (optional).
- `min_sqft` (optional).
- `limit` (default 50).

## Data model

```
kv["listing:<id>"]  -> {
  "id": str,
  "lat": float,
  "lng": float,
  "price": float,
  "beds": int,
  "baths": float,
  "sqft": int,
  "address": str,
  "created_at_ms": int,
}
kv["listings:index"] -> [id, ...]   # ordered by creation
```

## Read / Write paths

**Create**:
1. Generate `id` (Snowflake → str).
2. Validate lat/lng/price.
3. Persist listing and append to index.

**Search**:
1. Iterate `listings:index`.
2. Compute haversine distance to (lat, lng).
3. Drop if > `radius_km` or any filter fails.
4. Sort by distance ascending, take `limit`.

## Failure modes

| Failure | Mitigation |
| --- | --- |
| Invalid lat/lng | Validate on create; return 400. |
| Search returns nothing | Empty list with `total = 0`. |
| Hot listing keeps getting read | Add LRU cache for id lookups. |

## Tradeoffs

- **Linear scan** is `O(n)` per search. For 1M listings × 1k QPS this
  is too slow in production; switch to a spatial index (S2 / geohash /
  PostGIS).
- **No pagination beyond `limit`**; offset-based pagination is simple
  and good enough for the demo.
- **No updates/deletes** for listings. A real Zillow allows both;
  here we keep the API surface focused on the search problem.

## Code map

- `code/service.py` — `ZillowService` (CRUD + haversine search).
- `code/app.py` — Flask app.
- `tests/test_service.py` — service tests.
- `tests/test_app.py` — HTTP tests.
