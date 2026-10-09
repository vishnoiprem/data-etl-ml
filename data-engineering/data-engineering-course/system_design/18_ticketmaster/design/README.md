# 18 — Ticketmaster (Concurrency-Safe Seat Reservation)

A single-node, in-memory version of a Ticketmaster-style ticketing service.
The interesting problem here is **transactional seat reservation**: many users
simultaneously try to hold the same seat, and **only one** must win — every
other attempt must lose cleanly with a structured error, never silently
overwriting state.

## 1. Requirements

Functional
- Create events with a fixed seat layout (rows × cols, or named sections).
- List seats for an event with their current state (`available`, `held`,
  `sold`).
- Place a 10-minute hold on a seat for a user; the hold is revocable and
  has a unique opaque token.
- Convert a hold into a final purchase by presenting the hold token.
- Release a hold before its expiry.

Non-Functional
- **Atomicity**: at most one user can hold a given seat at a time. No
  double-booking, ever, even under concurrent traffic.
- **Fairness**: when two requests race, exactly one wins; the loser sees
  a structured `seat_unavailable` error, not an exception.
- **Bounded latency**: hold / purchase / release are O(1) on a hot path.
- **Observability**: every state transition is counted, every hold has
  an expiry that can be swept.

## 2. Capacity

- 1,000 events × 200 seats = 200k seats in memory at any time.
- Hold path: ~5k req/s, p99 < 5 ms (in-process; no network hop on the
  critical section).
- Sweeper: a background thread evicts expired holds every 1s.

## 3. High-Level Architecture

```
                +------------------+
   client --->  |  Flask app:8018  |
                +--------+---------+
                         |
                         v
                +------------------+
                | TicketmasterSvc  |
                |  - RLock (agg)   |
                |  - per-seat Lock |
                |  - KeyValueStore |
                |  - Snowflake ids |
                +--------+---------+
                         |
              +----------+----------+
              |          |          |
              v          v          v
         events      seats      holds (KV)
                                     |
                              sweeper thread
                              (1 Hz, drops expired)
```

Two layers of locking:
1. A coarse `RLock` on the service guards collection-level state changes
   (event creation, lookups).
2. A **per-seat `threading.Lock`** serializes the read-check-write sequence
   inside the hold/purchase/release path so two threads cannot both observe
   `available` and then both transition to `held`.

The sweeper background thread is *also* a writer; because it goes through
the same per-seat lock as the user-facing path, it cannot race with an
in-flight hold.

## 4. API

| Method | Path | Body | Returns |
| ------ | ---- | ---- | ------- |
| POST   | `/api/events` | `{name, rows, cols}` | event + seat map |
| GET    | `/api/events/{id}` | — | event summary |
| GET    | `/api/events/{id}/seats` | — | list of seats with status |
| POST   | `/api/events/{id}/seats/{seat_id}/hold` | `{user_id}` | `{hold_token, expires_at}` |
| POST   | `/api/events/{id}/seats/{seat_id}/purchase` | `{user_id, hold_token}` | `{ticket_id}` |
| POST   | `/api/events/{id}/seats/{seat_id}/release` | `{user_id, hold_token}` | `{released: true}` |
| GET    | `/health` | — | stats |
| GET    | `/metrics` | — | counters + histograms |
| GET    | `/` | — | endpoint index |

Error codes (HTTP 409 for conflicts, 404 for missing, 410 for expired):
- `seat_unavailable`
- `hold_token_mismatch`
- `hold_expired`
- `event_not_found`
- `seat_not_found`

## 5. Data Model

```
Event { event_id, name, rows, cols, created_at }
Seat  { event_id, seat_id, label, section, row, col,
        status: available|held|sold,
        held_by?, hold_token?, hold_expires_at? }
Hold  { event_id, seat_id, user_id, hold_token, expires_at }
Ticket{ ticket_id, event_id, seat_id, user_id, purchased_at }
```

State machine for a seat:

```
                hold           purchase
   available ---------> held ----------> sold
                       |   |
              release  |   |  expiry (sweeper)
                       v   v
                   available
```

- A `hold` is only valid if the seat is `available` *and* not already
  held by anyone.
- A `purchase` is only valid if a matching `hold` token exists for this
  seat/user, and `now < expires_at`.
- A `release` requires the matching hold token; it is the user's
  responsibility, but expiry is the system's.

## 6. Read / Write Paths

Read: `GET /api/events/{id}/seats` is a simple KeyValueStore scan. No
locks, no sweeper interaction. Cached in a TTLCache so the popular
event pages don't re-scan the KV.

Write — hold (the interesting one):
1. Acquire aggregate `RLock` to confirm event exists.
2. Acquire per-seat `threading.Lock`.
3. Read seat status.
4. If not `available` or hold has expired but not yet swept, return
   `seat_unavailable`.
5. Generate Snowflake hold token, set `status=held`, write seat back to
   KV.
6. Release per-seat lock.
7. Return `{hold_token, expires_at}`.

Write — purchase:
1. Acquire per-seat lock.
2. Verify `hold_token` matches *and* `now < hold_expires_at`.
3. Transition `held -> sold`, write ticket record.
4. Release lock.

Sweeper:
- Every 1s, scans active holds.
- For each whose `expires_at < now`, acquires the per-seat lock and
  transitions `held -> available`.

## 7. Failure Modes

| Failure | Detection | Recovery |
| ------- | --------- | -------- |
| Two requests race for same seat | per-seat lock serializes | exactly one wins; loser gets 409 |
| Process crash mid-hold | state lost; held seats become phantom | in production, persist `holds` to Postgres and rehydrate on boot |
| User never purchases | 10-min hold expires | sweeper thread releases |
| User purchases after expiry | server checks `expires_at` on every purchase | 410 `hold_expired` |
| Clock skew | `time.time()` is monotonic enough on one host | rely on NTP; document TTL as advisory |
| Sweeper blocked on a hot seat | per-seat lock makes sweeper wait its turn | acceptable; < 1s sweeper pause per locked seat |

## 8. Tradeoffs

- **Per-seat `threading.Lock` is fine in-process.** For 200k seats the
  Lock dict is fine, but at 10M+ you would shard seats across processes
  and use Redis `SETNX` (or `SELECT ... FOR UPDATE` on Postgres) as a
  distributed lock.
- **`RLock` not `Lock` on the service.** We use a reentrant lock because
  some methods call each other (e.g., `purchase` may call internal
  helpers that take the aggregate lock).
- **Opaque hold tokens are Snowflakes.** 64-bit, time-sortable, 41 bits
  of ms timestamp — collisions are practically impossible. A real system
  might add a random salt and return a UUID, but a Snowflake is enough
  to demonstrate the contract.
- **Sweeper is best-effort.** It can be late under load, but the
  purchase path checks `expires_at` itself so users can't sneak in a
  purchase after their own deadline.

## 9. Code Map

| File | Purpose |
| ---- | ------- |
| `code/service.py` | `TicketmasterService` — events, seats, hold/purchase/release, sweeper |
| `code/app.py` | Flask HTTP layer, metrics, health |
| `tests/test_service.py` | Service-level tests including the concurrent hold race |
| `tests/test_app.py` | HTTP-level tests |
