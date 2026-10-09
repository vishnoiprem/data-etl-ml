# 20 — Parking Garage (Spot Allocation, Real-Time Availability)

A single-node, in-memory version of a multi-floor parking garage. The
hard part is **spot allocation under contention**: at peak hours
hundreds of cars arrive per minute and each one needs the *closest*
available spot to the entry, but two cars must never be assigned the
same physical spot.

## 1. Requirements

Functional
- A garage has N floors, each with M spots. Each spot has a stable
  id (e.g. `F1-S07`) and a type (`standard`, `compact`, `ev`).
- On check-in, allocate the *closest* available spot to the entry.
  "Closest" here means lowest floor first, then lowest spot number.
- On check-out, free the spot. Compute the duration / fee.
- Real-time availability: how many spots are free per floor, which
  spots are free, and active session details.
- Vehicle spot preference (compact / ev) honored when possible.

Non-Functional
- **No double-allocation**, ever, even with concurrent check-ins.
- **Bounded latency**: check-in < 5 ms p99, check-out < 5 ms p99.
- **Live availability** without expensive scans on the hot path:
  floor-level counts are updated incrementally.

## 2. Capacity

- 1 garage × 10 floors × 100 spots = 1,000 spots in memory.
- ~500 active sessions at peak; each is ~200 bytes.
- Check-in path: ~1k req/s.

## 3. High-Level Architecture

```
              +----------------------+
   client --> |  Flask app :8020     |
              +----------+-----------+
                         |
                         v
              +----------------------+
              | ParkingGarageService |
              |  - aggregate RLock   |
              |  - per-spot Lock     |
              |  - per-floor RLock   |
              |  - KV stores         |
              +----------+-----------+
                         |
              +----------+----------+
              |          |          |
              v          v          v
         garage config  spots   sessions
         (in-memory)    (KV)    (KV)
```

Locking layers
1. **Aggregate RLock** — protects configuration changes (add floor,
   add spot, change price).
2. **Per-floor RLock** — the workhorse for allocation. Within a floor,
   we walk spots in order; the lock guarantees that during one
   allocation, no other thread on the same floor can claim a spot.
3. **Per-spot Lock** — held during the final claim. Same idea as
   Ticketmaster: even if two threads tried to allocate to the same
   `F1-S07` (e.g., via the same-floor lock being briefly held and
   released), the per-spot lock makes the transition
   `free -> occupied` atomic.

The allocation algorithm is **first-fit** within floors, lowest floor
first. So `F1-S01` is the first spot we look at; if it's free, we
take it; otherwise `F1-S02`, etc. If the entire floor is full, we go
to F2.

## 4. API

| Method | Path | Body | Returns |
| ------ | ---- | ---- | ------- |
| POST   | `/api/checkin` | `{vehicle_id, preferred_type?}` | `{ticket_id, spot_id, floor, type, checkin_at}` |
| POST   | `/api/checkout` | `{ticket_id}` | `{ticket_id, spot_id, duration_seconds, fee_cents}` |
| GET    | `/api/availability` | — | per-floor free counts + total |
| GET    | `/api/tickets/{id}` | — | session details |
| GET    | `/api/tickets` | — | list of active sessions |
| GET    | `/api/spots` | — | list of all spots with status |
| GET    | `/health` | — | stats |
| GET    | `/metrics` | — | metrics |
| GET    | `/` | — | endpoint index |

Error codes:
- `garage_full` (503)
- `no_spot_for_type` (409)
- `ticket_not_found` (404)
- `ticket_already_closed` (409)

## 5. Data Model

```
GarageConfig { floors: int, spots_per_floor: int, spot_types: [...] }
Spot        { spot_id, floor, number, type, status: free|occupied }
Session     { ticket_id, vehicle_id, spot_id, type, checkin_at,
              checkout_at?, fee_cents? }
```

Spot ids: `F{floor}-S{number:03d}`, e.g. `F1-S007`.

Spot types rotate by `floor × spots_per_floor`:
- 0..40%  standard
- 40..75% compact
- 75..100% ev (with charging metadata)

## 6. Read / Write Paths

Read — availability
- Per-floor free count is updated **incrementally** on every
  check-in / check-out. So `GET /api/availability` is O(floors).
- For "which exact spots are free", we read from the per-spot
  KeyValueStore; in production this is a B-tree index.

Write — check-in
1. Acquire aggregate RLock to read garage config (cheap, contention
   is low).
2. For each floor (1..N), acquire the floor's RLock, walk spots in
   ascending order, take the first free one matching the preferred
   type (or any if no preference).
3. Acquire the per-spot lock.
4. Verify the spot is still free (TOCTOU defence).
5. Mark occupied, allocate ticket id, create session, release per-spot
   lock and per-floor lock.
6. Decrement per-floor free count.

Write — check-out
1. Find the session by ticket id.
2. Acquire the per-spot lock for `session.spot_id`.
3. Mark spot free, set `checkout_at`, compute fee.
4. Increment per-floor free count.
5. Release lock.

## 7. Failure Modes

| Failure | Detection | Recovery |
| ------- | --------- | -------- |
| Two cars check in at the same instant | per-floor + per-spot locks | exactly one gets `F1-S001`; the other continues to `F1-S002` |
| Process crash mid-check-in | spot state may be inconsistent | in production, write a `pending` row and reconcile on boot |
| Check-out for unknown ticket | session lookup inside lock | 404 |
| Garage totally full | walk completes with no free spot | 503 `garage_full` |
| Fee computation clock skew | `time.time()` on one host | NTP; document |

## 8. Tradeoffs

- **First-fit is O(F × M) in the worst case.** Fine for 1k spots; a
  real garage with 50k spots would maintain a `free_spots_by_floor`
  heap per type, so the next allocation is O(log n) per floor.
- **Per-floor + per-spot is two locks where one would do.** A single
  global RLock would work but serialize *all* check-ins. The two-tier
  approach parallelizes across floors.
- **No reservation / pre-booking.** Some real garages let you reserve
  a spot in advance; that would need a `hold` table with TTL, à la
  Ticketmaster.
- **Fee is simple: rate × hours.** Production garages have peak /
  off-peak pricing, validation discounts, etc.

## 9. Code Map

| File | Purpose |
| ---- | ------- |
| `code/service.py` | `ParkingGarageService` — garage config, spots, sessions, allocation |
| `code/app.py` | Flask HTTP layer with metrics |
| `tests/test_service.py` | Service tests including concurrent check-in race |
| `tests/test_app.py` | HTTP tests |
