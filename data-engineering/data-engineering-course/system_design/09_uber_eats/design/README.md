# 09 — Uber Eats (3-Sided Marketplace)

> **Lesson 9 of the System Design course — Event-Driven Systems**

A working design + implementation of a 3-sided food delivery
marketplace: **restaurants** publish menus, **eaters** place orders,
and **drivers** accept and deliver them. The state machine
`PLACED → ACCEPTED → PICKED_UP → DELIVERED` is the spine, and a
simple nearest-driver dispatch heuristic is the hot path.

This lesson is the capstone of the Event-Driven track: lessons 7
and 8 gave us the *plumbing* (message queues, webhook delivery).
Here we use those patterns implicitly — every order transition is
an event that *could* fire a webhook or be published to a topic.

---

## 1. Requirements

### Functional
- **Restaurants** — register with `{name, address, location (lat,lng)}`.
  Add menu items `{name, price_cents}`.
- **Eaters** — implicit: we accept `eater_id` per order (no auth).
- **Drivers** — implicit: `driver_id` per accept. We track location
  so dispatch can pick the nearest.
- **Orders** — an eater creates an order against a restaurant:
  `{eater_id, restaurant_id, items: [{menu_item_id, qty}], address}`.
  The order is priced, persisted, and put in `PLACED` state.
- **Dispatch** — when an order is `PLACED`, the system picks the
  nearest available driver and *offers* the order. In this lesson
  we don't do a real-time offer handshake; we instead let the
  driver call `POST /api/orders/<id>/accept`. The "nearest driver"
  is computed and stored when the order is placed (so we can audit
  it later).
- **State machine** — `PLACED → ACCEPTED → PICKED_UP → DELIVERED`.
  Each transition records a timestamp. The only "leak" is `CANCELLED`
  from `PLACED` or `ACCEPTED`.

### Non-functional
- **Atomic transitions** — the state machine rejects illegal moves
  (e.g. `PICKED_UP` before `ACCEPTED`).
- **Observability** — counts of orders by state surfaced at
  `/metrics`. End-to-end latency histogram for state transitions.
- **Persistence** — all state lives in a `KeyValueStore` so the
  service can restart and resume.

### Out of scope (for this lesson)
- Real payments / Stripe.
- Real maps / geocoding. We use Euclidean distance on `(lat, lng)`
  to compute "nearest" — accurate enough for the lesson, not for
  production.
- Push notifications / real-time offers. The driver polls or the
  system uses the suggested driver.
- Idempotency on order placement. (We should de-dup, but the lesson
  focuses on the state machine.)

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Cities | 1 K |
| Restaurants / city | 1 K avg, 5 K dense cities |
| Total active restaurants | ~1 M |
| Drivers / city (peak) | 10 K |
| Orders / day | 1 M total, ~12 /sec avg, 100 /sec peak |
| Avg delivery time | 25 min |
| Concurrent in-flight orders | 50 K |
| Order row size | ~2 KB (items + state) |
| Total storage (5y) | ~3.6 TB |

The lesson: the read path is dominated by "where's my order?"
(the eater checking) and "what's near me?" (the driver polling).
The write path is dominated by state transitions, which are tiny
in volume compared to menu reads.

---

## 3. High-level design

```
   eater app          driver app           ops dashboards
       │                  │                       │
       │ POST /orders     │ POST /accept          │ GET /metrics
       ▼                  ▼                       ▼
   ┌─────────────────────────────────────────────────────┐
   │                API (Flask)                          │
   └──┬──────────────┬───────────────┬──────────────────┘
      │              │               │
      ▼              ▼               ▼
  ┌────────┐  ┌─────────────┐  ┌──────────────┐
  │ Orders │  │  Dispatch   │  │  Restaurants │
  │  svc   │  │  (nearest   │  │  / menus     │
  │        │  │   driver)   │  │              │
  └───┬────┘  └─────┬───────┘  └──────────────┘
      │             │
      │   ┌─────────┴──────────┐
      │   │  state machine     │
      │   │  PLACED→ACCEPTED   │
      │   │  →PICKED_UP        │
      │   │  →DELIVERED        │
      │   └─────────┬──────────┘
      │             │
      ▼             ▼
   ┌─────────────────────────┐
   │   KeyValueStore (JSON)  │
   │   restaurants, menus,   │
   │   orders, drivers       │
   └─────────────────────────┘
```

- **API**: Flask. Stateless. The interesting logic lives in
  `service.py`.
- **State machine**: encoded as `ALLOWED_TRANSITIONS` in the
  service. The transition methods check the current state and
  reject invalid moves.
- **Dispatch**: pure function `nearest_driver(restaurant_location,
  available_drivers)`. The result is *stored on the order* so we
  can audit "why did this driver get offered this order?".
- **Persistence**: `KeyValueStore` for everything.

---

## 4. API

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| `POST` | `/api/restaurants` | `{"name", "address", "lat", "lng"}` | restaurant record |
| `GET`  | `/api/restaurants` | — | list |
| `GET`  | `/api/restaurants/<id>` | — | restaurant + menu |
| `POST` | `/api/restaurants/<id>/menu` | `{"name", "price_cents"}` | menu item |
| `POST` | `/api/drivers` | `{"name", "lat", "lng"}` | driver record |
| `GET`  | `/api/drivers` | — | list |
| `POST` | `/api/orders` | `{"eater_id", "restaurant_id", "items": [...], "address", "lat", "lng"}` | order record (status=PLACED) |
| `GET`  | `/api/orders/<id>` | — | order + status + history |
| `GET`  | `/api/orders?state=PLACED` | — | filter by state |
| `POST` | `/api/orders/<id>/accept` | `{"driver_id"}` | order (status=ACCEPTED) |
| `POST` | `/api/orders/<id>/status` | `{"status": "picked_up"\|"delivered"\|"cancelled"}` | order |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{"ok": true, "stats": ...}` |
| `GET`  | `/` | — | service index |

Notes:
- `POST /api/orders` also computes and stores the suggested driver
  (`suggested_driver_id`). This is *not* a hard assignment — the
  driver must call `accept` to commit.
- `accept` validates that the driver is the suggested one (in this
  lesson; in real life any available driver can grab it). Easy to
  relax.
- `lat`/`lng` on the order is the *delivery* location (eater's
  address). Restaurant location is on the restaurant record.

---

## 5. Data model

### Restaurant
```
restaurant:<id> = {
  "restaurant_id": int,
  "name": str,
  "address": str,
  "lat": float,
  "lng": float,
  "created_at": float,
  "menu": { item_id: {name, price_cents}, ... }
}
```

### Driver
```
driver:<id> = {
  "driver_id": int,
  "name": str,
  "lat": float,
  "lng": float,
  "available": bool,         # currently accepting offers
  "created_at": float,
}
```

### Order
```
order:<id> = {
  "order_id": int,
  "eater_id": int,
  "restaurant_id": int,
  "items": [
    {"menu_item_id": int, "name": str, "price_cents": int, "qty": int},
    ...
  ],
  "subtotal_cents": int,
  "address": str,
  "lat": float, "lng": float,   # delivery destination
  "status": "PLACED" | "ACCEPTED" | "PICKED_UP" | "DELIVERED" | "CANCELLED",
  "suggested_driver_id": int | None,
  "driver_id": int | None,      # set on accept
  "history": [
    {"status": str, "ts": float, "by": str, "note": str}
  ],
  "created_at": float,
  "updated_at": float,
}
```

### State machine

```
                    ┌────────────┐
                    │   PLACED   │
                    └─────┬──────┘
              cancel      │ accept (driver)
                  ┌───────┴───────┐
                  ▼               ▼
            ┌──────────┐    ┌──────────┐
            │ CANCELLED│    │ ACCEPTED │
            └──────────┘    └─────┬────┘
                  cancel          │ picked_up
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
            ┌──────────┐                  ┌──────────┐
            │ CANCELLED│                  │ PICKED_UP│
            └──────────┘                  └─────┬────┘
                                                │ delivered
                                                ▼
                                          ┌──────────┐
                                          │ DELIVERED│
                                          └──────────┘
```

Allowed transitions:
- `PLACED → ACCEPTED` (driver accepts)
- `PLACED → CANCELLED` (eater cancels before any driver accepts)
- `ACCEPTED → PICKED_UP` (driver picks up the food)
- `ACCEPTED → CANCELLED` (rare; usually only by ops)
- `PICKED_UP → DELIVERED` (driver hands off the food)
- `DELIVERED` is terminal.
- `CANCELLED` is terminal.

Any other move raises `InvalidTransitionError`.

---

## 6. Order placement — write path

`POST /api/orders`:

```
1. Validate body: restaurant exists, every menu_item_id is in
   restaurant.menu, items list is non-empty.
2. Price the order: subtotal_cents = sum(item.price_cents * qty).
   We capture the price at order time so a later menu edit doesn't
   rewrite history.
3. Compute suggested_driver_id via nearest_driver.
4. Create the order with status=PLACED, history=[{PLACED, now}].
5. Return the order record.
```

The pricing step is the subtle one. We *snapshot* the price from
the menu at order time into `items[i].price_cents`, so a restaurant
that edits its menu after the order is placed doesn't surprise the
eater at delivery.

---

## 7. Driver dispatch — read path

`nearest_driver(restaurant, available_drivers)`:

```
def nearest_driver(restaurant_loc, drivers):
    best = None
    best_d = inf
    for d in drivers:
        if not d.available:
            continue
        dist = euclidean(restaurant_loc, (d.lat, d.lng))
        if dist < best_d:
            best = d
            best_d = dist
    return best
```

We use Euclidean distance on `(lat, lng)`. In production you'd
use the Haversine formula and a real ETA from a routing service.
For the lesson, "which driver is geographically closest to the
restaurant" is good enough to illustrate the dispatch pattern.

The dispatch happens at order placement; the suggestion is stored
on the order. In a real system, you'd also send a push notification
to the driver and use a short offer window (e.g. 30s) before
falling back to the next-nearest.

---

## 8. State transitions — write path

`POST /api/orders/<id>/accept`:

```
1. Load order.
2. If status != PLACED, raise InvalidTransitionError.
3. Load driver. Verify driver.available.
4. Update order: status=ACCEPTED, driver_id=driver_id,
   history=[..., {ACCEPTED, now}], updated_at=now.
5. Persist.
6. Return order.
```

`POST /api/orders/<id>/status` is the catch-all for the rest of
the state machine: it accepts `picked_up`, `delivered`, or
`cancelled` and dispatches to the right transition function.

---

## 9. Failure modes

| Failure | What happens | Mitigation |
|---|---|---|
| **Restaurant deletes a menu item mid-order** | Order's `items` are snapshotted, so the existing order is unaffected. The deleted item simply can't be added to new orders. | Pricing snapshot at placement (design §6). |
| **Suggested driver is offline** | They can't accept; the order stays in PLACED. | Real system would re-dispatch. Here, we let the next caller offer it (TODO: implement re-dispatch endpoint). |
| **Driver accepts but never marks picked_up** | Order stuck in ACCEPTED. | Stuck-order sweep in ops; out of scope for the lesson. |
| **Order created with no available drivers** | `suggested_driver_id = None`. The order still enters PLACED. | UI shows "looking for a driver"; in production, the dispatch loop polls. |
| **Duplicate order creation** | We don't dedupe. Two near-simultaneous calls produce two orders. | In production, idempotency key from the client. |
| **State machine violation** (e.g. PICKED_UP before ACCEPTED) | API returns 409. | Atomic check inside the service; client retries after they figure out what went wrong. |
| **Driver accepts but then dies / app crashes** | Order in ACCEPTED forever. | Same as the "never marks picked_up" case. |
| **Bad address / can't find eater** | Driver can't deliver. | Real system triggers a refund flow; out of scope. |

---

## 10. Tradeoffs

### Snapshot pricing vs live pricing
- **Snapshot** (we do): the order records the price at placement.
  Immune to menu edits. The restaurant loses the ability to
  "fix" a price on a placed order, but they also can't accidentally
  re-price a completed order.
- **Live**: the order records only the menu_item_ids and the
  current prices are looked up at delivery / payment time. Saves
  the eater money if the price dropped; costs them if it rose.

We pick snapshot — the lesson is about the state machine, and
prices shouldn't change underneath the contract.

### Suggest-on-place vs continuous-dispatch
- **Suggest-on-place** (we do): compute the suggested driver at
  order time, store it. Simple, predictable, but the suggested
  driver may be busy 5 seconds later.
- **Continuous dispatch**: a background loop re-runs `nearest_driver`
  every 5s while the order is `PLACED`, updating the suggestion.
  More responsive, but more state, more edge cases.

We pick suggest-on-place; the loop is an easy follow-up.

### Hard-assign driver vs offer-then-accept
- **Hard-assign**: the system picks the driver; the order is
  `ACCEPTED` immediately. Simpler, but if the driver is busy, the
  order sits in their queue.
- **Offer-then-accept** (we do): the system suggests, the driver
  accepts, the order is `ACCEPTED` only after confirmation. Adds a
  round-trip, but lets the driver decline (we don't model decline
  here; in real life they'd hit a "no thanks" button and the system
  would re-dispatch).

### Per-order `history` array vs separate event log
- **Per-order array** (we do): each order carries its own
  transition history. Cheap to read, but the history is per-row
  and can't be queried across orders without a scan.
- **Separate event log**: every transition is an event in a global
  log (e.g. a Kafka topic). Enables "show me all orders that went
  PLACED → DELIVERED in < 30 min" but needs an extra read.

We pick the per-order array; lesson 7 already covered event logs.

### Single service vs split (orders / dispatch / restaurants)
- **Single** (we do): one process, one KeyValueStore, one Flask
  app. Easiest to reason about, but every request hits the same
  process.
- **Split**: restaurants service, dispatch service, orders service,
  with the orders service calling the dispatch service. Better
  scaling story, but RPC complexity.

We pick single.

---

## 11. Code map

```
09_uber_eats/
├── design/README.md            # this file
├── code/
│   ├── __init__.py
│   ├── service.py              # UberEatsService (pure logic)
│   └── app.py                  # Flask wrapper
└── tests/
    ├── __init__.py
    ├── test_service.py         # ≥6 unit tests
    └── test_app.py             # ≥4 HTTP tests
```

- `UberEatsService` owns restaurants, drivers, orders, and the
  state machine. Pure Python; takes `KeyValueStore` and `Snowflake`.
- `app.py` is the Flask wrapper. Endpoints are thin; the service
  does the real work.
- The `OrderStatus` enum and `ALLOWED_TRANSITIONS` map are the
  state-machine source of truth.
