# 19 — Hotel Booking System (Date-Range Reservation, No Double-Booking)

A single-node, in-memory version of a hotel-booking system. The
defining problem is **range overlap**: every booking has a half-open
date range `[check_in, check_out)`, and no two bookings on the same
room may overlap. We have to reject overlapping requests, even when
they arrive concurrently from different users.

## 1. Requirements

Functional
- Create hotels and rooms (capacity 2 by default — number of guests).
- Book a room for a date range, returning a booking id.
- Look up availability for a room across a date range.
- Cancel a booking (refund; frees dates).

Non-Functional
- **No double-booking**, ever, on the same room. Two concurrent
  requests for overlapping ranges — only one wins.
- **Date ranges are half-open**: `[check_in, check_out)`. A booking
  that ends on the 5th does NOT conflict with a booking that starts
  on the 5th.
- **Deterministic errors** on conflict: `room_unavailable` with the
  conflicting dates attached, HTTP 409.
- **O(N) availability queries** where N is the number of bookings on
  the room — fine for in-memory; would be indexed in production.

## 2. Capacity

- 10k hotels × 100 rooms = 1M rooms in memory.
- Each room has on average ~5 active bookings; an availability check
  scans 5 entries.
- Book path: ~1k req/s, p99 < 10 ms (one lock per room).

## 3. High-Level Architecture

```
              +---------------------+
   client --> |  Flask app :8019    |
              +----------+----------+
                         |
                         v
              +---------------------+
              | HotelBookingService |
              |  - aggregate RLock  |
              |  - per-room RLock   |
              |  - KV stores        |
              +----------+----------+
                         |
              +----------+----------+
              |          |          |
              v          v          v
          hotels       rooms      bookings
```

- A service-level `RLock` guards collection-level operations (hotel
  creation, room add, global stats). Reentrant because some helpers
  re-enter the lock.
- A **per-room `RLock`** serializes booking/cancel/availability-read
  sequences for that room. Two threads that try to book overlapping
  dates on the same room will collide here; the loser observes the
  winner's persisted state and is rejected.

The per-room RLock is the only thing standing between us and a
double-booking. The booking path is:

```
acquire(room_lock)
  read room's bookings
  check overlap
  if no overlap: append booking
  release(room_lock)
return
```

Because the read-check-write sequence is inside the lock, no two
threads can both observe "no overlap" and both append.

## 4. API

| Method | Path | Body | Returns |
| ------ | ---- | ---- | ------- |
| POST   | `/api/hotels` | `{name, city}` | hotel |
| GET    | `/api/hotels` | — | list of hotels |
| POST   | `/api/hotels/{id}/rooms` | `{room_number, capacity, price_cents}` | room |
| GET    | `/api/hotels/{id}/rooms` | — | rooms in hotel |
| POST   | `/api/rooms/{id}/book` | `{user_id, check_in, check_out}` | booking |
| GET    | `/api/rooms/{id}/availability?from=&to=` | — | `{available, conflicts, bookings}` |
| POST   | `/api/bookings/{id}/cancel` | `{user_id}` | `{cancelled: true}` |
| GET    | `/api/bookings/{id}` | — | booking |
| GET    | `/health` | — | stats |
| GET    | `/metrics` | — | metrics |
| GET    | `/` | — | endpoint index |

Date format: `YYYY-MM-DD`. Date ranges are half-open
(`[check_in, check_out)`).

Error codes:
- `hotel_not_found` (404)
- `room_not_found` (404)
- `booking_not_found` (404)
- `room_unavailable` (409, with `conflicts: [booking_id, ...]`)
- `invalid_date_range` (400)
- `not_authorized` (403)

## 5. Data Model

```
Hotel   { hotel_id, name, city, created_at }
Room    { room_id, hotel_id, room_number, capacity, price_cents,
          created_at }
Booking { booking_id, room_id, user_id, check_in, check_out,
          status: active|cancelled, created_at, cancelled_at? }
```

Indexing
- `bookings_by_room:{room_id} -> [booking_id, ...]` — order of
  insertion, not sorted. We sort on read.

In production this becomes a B-tree index on `(room_id, check_in,
check_out)` and the overlap query is a range scan.

## 6. Read / Write Paths

Read — availability
1. Acquire the room's RLock (a read-write lock would let multiple
   readers in parallel, but RLock is simpler and contention on a
   single room is low in practice).
2. Fetch active bookings for the room, sorted by `check_in`.
3. Compute the union of booked ranges; if `[from, to)` intersects any
   active range, it's not fully available.
4. Release lock, return.

Write — book
1. Validate dates: `check_in < check_out`, both parseable.
2. Acquire the room's RLock.
3. Load active bookings for the room.
4. For each, check overlap: `existing.check_in < new.check_out
   AND new.check_in < existing.check_out`.
5. If any overlap, collect conflicting booking ids, return
   `room_unavailable` with that list. Do NOT mutate state.
6. Otherwise, allocate booking id (Snowflake), persist booking.
7. Release lock, return booking.

Write — cancel
1. Acquire the room's RLock.
2. Load booking; verify it exists, is `active`, and belongs to user.
3. Mark `cancelled`, set `cancelled_at`. Persist.
4. Release lock.

## 7. Failure Modes

| Failure | Detection | Recovery |
| ------- | --------- | -------- |
| Two concurrent overlapping bookings | per-room RLock serializes them | second one sees first's booking, gets 409 |
| Process crash mid-booking | booking is not persisted | in production, write to Postgres in a single transaction with `SELECT ... FOR UPDATE` on the room row |
| Time-zone or DST off-by-one | dates are stored as ISO strings, not timestamps | half-open `[in, out)` semantics remove this class of bug |
| User double-clicks the booking button | per-room RLock + check-on-write | second call either gets the same booking or a 409 |
| Cancelling a cancelled booking | status check inside lock | 200 with `already_cancelled: true` or 409 — chosen `409 not_authorized` here |

## 8. Tradeoffs

- **Per-room `RLock` is fine at this scale.** A real system with 10k+
  rooms and high booking QPS would put each room on a separate
  Postgres row and use `SELECT ... FOR UPDATE` to serialize per-room
  writes, or shard the rooms across processes and use a distributed
  lock (Redis Redlock, ZooKeeper).
- **No per-user locks.** A user can have multiple bookings on the
  same room; we don't prevent that here. A production system would
  enforce per-user uniqueness with a `UNIQUE (user_id, room_id,
  active)` partial index, or a `user_locks:{user_id}` lock.
- **Cancellation does not refund nights already passed.** That logic
  belongs in the payments service.
- **In-memory persistence via `KeyValueStore`.** This gives us
  atomic per-key `set`/`get` semantics; reads are scans. A real DB
  would be a single `SELECT` per query.

## 9. Code Map

| File | Purpose |
| ---- | ------- |
| `code/service.py` | `HotelBookingService` — hotels, rooms, bookings, overlap checks |
| `code/app.py` | Flask HTTP layer with date parsing and metrics |
| `tests/test_service.py` | Service tests including concurrent-overlap race |
| `tests/test_app.py` | HTTP tests |
