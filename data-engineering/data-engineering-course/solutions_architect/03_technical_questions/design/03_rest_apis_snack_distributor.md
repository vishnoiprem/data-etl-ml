# 03 — Evaluating REST APIs for a Snack Distributor

> **Lesson 3 of 7 — Technical Questions for SAs** · ~25 min

A real-world API design problem: design the REST API for a
snack distributor with 50 products, 1,000 customers, 200
retail locations, and daily deliveries. Resource model,
endpoint design, sample request/response, error model,
pagination strategy, auth model.

---

## 1. The problem statement

> *"Design the REST API for a snack distributor with 50
> products, 1,000 customers, 200 retail locations, and
> daily deliveries. The distributor has 5 sales reps who
> visit the retail locations, take orders, and arrange
> next-day delivery. The customers (retail managers) can
> also place orders through a mobile app. The distributor
> needs real-time inventory visibility and integration
> with their ERP."*

This is a classic B2B-distributor API design problem. The
candidate needs to model the resources, design the
endpoints, handle auth, and think about real-world
constraints (offline sales reps, real-time inventory,
ERP integration).

---

## 2. The clarifying questions (5 minutes)

Before designing the API, ask 5 clarifying questions:

1. **What are the user roles?** (Sales rep with offline
   access, retail manager on the mobile app, ERP system
   for inventory sync, distributor's admin team.)
2. **What's the order volume?** (~200 orders/day total —
   5 reps × 40 orders/day each, plus 20-30 mobile app
   orders/day. So ~10k orders/month, 120k orders/year.)
3. **What's the real-time inventory requirement?** (Reps
   need to know inventory at the visit time, so latency
   requirement is sub-second. Inventory updates from
   deliveries are near-real-time, not batch.)
4. **What's the offline requirement?** (Sales reps in
   areas with poor connectivity need to be able to take
   orders offline and sync when they reconnect.)
5. **What's the integration with ERP?** (The ERP owns
   master inventory and product catalog. The API needs
   to sync with the ERP via webhooks or polling, and
   needs to handle eventual consistency between the API
   and the ERP.)

The 5 questions surface the *real-world constraints*.
Without them, you'd design a generic e-commerce API
without offline support, without real-time inventory,
and without ERP integration. The candidate who designs
without the constraints is the candidate who fails the
round.

---

## 3. The resource model

The 5 main resources:

| Resource | Description | Cardinality |
|---|---|---|
| **Product** | A snack product (e.g., "Lays Classic 1oz") | ~50 |
| **Customer** | A retail location (e.g., "7-Eleven Store #1234") | ~200 |
| **Order** | A purchase order from a customer | ~10/day |
| **Delivery** | A delivery from the warehouse to a customer | ~10/day (one per order) |
| **Inventory** | Real-time inventory level per product per warehouse | ~50 × 3 warehouses = 150 |

Plus the auxiliary resources:

| Resource | Description |
|---|---|
| **SalesRep** | A field sales rep |
| **Visit** | A sales rep's visit to a customer |
| **Warehouse** | A distribution warehouse |
| **InventoryAdjustment** | An adjustment to inventory (returns, damages) |

---

## 4. The endpoint design

The 4 main endpoint groups:

### Products (`/products`)

```
GET    /products                  # List all products (with pagination)
GET    /products/{product_id}     # Get a specific product
POST   /products                  # Create a product (admin only)
PATCH  /products/{product_id}     # Update a product (admin only)
```

### Customers (`/customers`)

```
GET    /customers                 # List customers (with pagination)
GET    /customers/{customer_id}   # Get a specific customer
POST   /customers                 # Create a customer
PATCH  /customers/{customer_id}   # Update a customer
GET    /customers/{customer_id}/orders    # List a customer's orders
```

### Orders (`/orders`)

```
GET    /orders                    # List orders (with pagination, filtering)
GET    /orders/{order_id}         # Get a specific order
POST   /orders                    # Create an order
PATCH  /orders/{order_id}         # Update an order (status changes)
POST   /orders/{order_id}/cancel  # Cancel an order
GET    /orders/{order_id}/delivery    # Get the delivery for an order
```

### Inventory (`/inventory`)

```
GET    /inventory                 # Get inventory across warehouses
GET    /inventory/{product_id}    # Get inventory for a specific product
GET    /warehouses/{warehouse_id}/inventory   # Get inventory for a warehouse
POST   /inventory/adjustments     # Create an inventory adjustment
```

### Auxiliary

```
GET    /sales-reps                # List sales reps
GET    /sales-reps/{rep_id}/visits    # List a rep's visits
POST   /visits                    # Log a visit
```

### Webhooks (for ERP integration)

```
POST   /webhooks/inventory-updated    # ERP receives inventory updates
POST   /webhooks/order-placed         # ERP receives new orders
```

---

## 5. Sample request/response

A sample `POST /orders` request:

**Request:**

```http
POST /orders HTTP/1.1
Host: api.snackdist.com
Authorization: Bearer <token>
Content-Type: application/json

{
  "customer_id": "cust_abc123",
  "sales_rep_id": "rep_xyz789",
  "order_date": "2026-04-15",
  "delivery_date": "2026-04-16",
  "items": [
    { "product_id": "prod_lays_classic_1oz", "quantity": 24 },
    { "product_id": "prod_doritos_coolranch_1oz", "quantity": 12 }
  ],
  "notes": "Customer requested delivery before 10am"
}
```

**Response (201 Created):**

```http
HTTP/1.1 201 Created
Location: /orders/ord_12345
Content-Type: application/json

{
  "id": "ord_12345",
  "customer_id": "cust_abc123",
  "sales_rep_id": "rep_xyz789",
  "status": "pending",
  "order_date": "2026-04-15",
  "delivery_date": "2026-04-16",
  "items": [
    {
      "product_id": "prod_lays_classic_1oz",
      "product_name": "Lays Classic 1oz",
      "quantity": 24,
      "unit_price": 0.50,
      "subtotal": 12.00
    },
    {
      "product_id": "prod_doritos_coolranch_1oz",
      "product_name": "Doritos Cool Ranch 1oz",
      "quantity": 12,
      "unit_price": 0.55,
      "subtotal": 6.60
    }
  ],
  "subtotal": 18.60,
  "tax": 1.55,
  "total": 20.15,
  "notes": "Customer requested delivery before 10am",
  "created_at": "2026-04-15T10:23:45Z",
  "updated_at": "2026-04-15T10:23:45Z"
}
```

The response includes the computed totals, the status
(initial), the location header for the new resource, and
the timestamps.

---

## 6. The error model

A consistent error model is critical. Use the standard
HTTP status codes and a structured error response:

**Error response:**

```json
{
  "error": {
    "code": "INVENTORY_INSUFFICIENT",
    "message": "Requested quantity exceeds available inventory",
    "details": {
      "product_id": "prod_lays_classic_1oz",
      "requested": 24,
      "available": 18
    },
    "request_id": "req_abc123",
    "documentation_url": "https://docs.snackdist.com/errors/INVENTORY_INSUFFICIENT"
  }
}
```

The error response has 5 fields:

1. **`code`** — a machine-readable error code (stable
   across API versions).
2. **`message`** — a human-readable message.
3. **`details`** — structured details about the error
   (optional).
4. **`request_id`** — a unique ID for the request, useful
   for support and debugging.
5. **`documentation_url`** — a link to the error
   documentation.

The 5 fields are the standard error model. The candidate
who designs this in the interview signals "I've designed
production APIs."

### Common error codes

| Code | HTTP Status | When it occurs |
|---|---|---|
| `INVALID_REQUEST` | 400 | Malformed request body |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Token doesn't have permission |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `INVENTORY_INSUFFICIENT` | 409 | Order quantity exceeds inventory |
| `ORDER_ALREADY_CANCELLED` | 409 | Trying to cancel a cancelled order |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server-side error |

---

## 7. The pagination strategy

For endpoints that return lists (`/orders`,
`/customers`, `/products`), use cursor-based pagination
(also called "keyset pagination"):

**Request:**

```
GET /orders?limit=50&cursor=eyJpZCI6Im9yZF8xMjM0NSJ9
```

**Response:**

```json
{
  "data": [ ... ],
  "pagination": {
    "next_cursor": "eyJpZCI6Im9yZF82Nzg5MCJ9",
    "has_more": true
  }
}
```

Cursor-based pagination is preferred over offset-based
because:

- **Performance:** Offset-based gets slower as the offset
  grows; cursor-based is constant time.
- **Consistency:** Offset-based can return duplicate or
  missed rows if data is inserted between requests;
  cursor-based doesn't have this issue.

The pagination is a 2-field response (`next_cursor`,
`has_more`). The candidate who chooses cursor-based
signals "I've thought about this at scale."

---

## 8. The auth model

The 4 user roles, each with different permissions:

| Role | Permissions |
|---|---|
| **Sales rep** | Read products, read customers, create orders, read own orders, read inventory |
| **Retail manager (mobile app)** | Read products, read own customer info, create orders, read own orders |
| **Distributor admin** | Full access (CRUD on all resources) |
| **ERP system** | Read products, read/write inventory, read orders, write inventory adjustments |

The auth model uses **OAuth 2.0 with scopes**:

- `products:read`, `products:write`
- `customers:read`, `customers:write`
- `orders:read`, `orders:write`
- `inventory:read`, `inventory:write`

Each role is granted a specific set of scopes. The
candidate who designs the scope-based auth signals "I
understand multi-tenant API auth."

For the sales reps with offline access, the auth tokens
are long-lived (e.g., 30-day refresh tokens, with offline
storage of the access token).

---

## 9. The API versioning strategy

A versioning strategy is critical for any production API.
The 2 common approaches:

| Approach | Pros | Cons |
|---|---|---|
| **URL versioning** (`/v1/orders`, `/v2/orders`) | Easy to read; easy to route; clear separation | More URLs to maintain |
| **Header versioning** (`Accept: application/vnd.snackdist.v2+json`) | Cleaner URLs; same endpoint, different versions | Harder to test in a browser; harder to debug |

For a B2B distributor API with mobile app clients, **URL
versioning** is preferred. Mobile app updates are slow
(weeks to months), and the distributor needs to support
multiple API versions for older app versions.

The candidate who addresses versioning in the interview
signals "I've thought about API lifecycle."

---

## 10. The offline-support model

The sales reps need offline support. The 3 components:

1. **Local cache.** The mobile app caches a subset of
   data (products, customers, recent orders, recent
   inventory) locally.
2. **Optimistic order creation.** When offline, the
   sales rep can create orders locally; the orders are
   queued for sync.
3. **Conflict resolution.** When the rep comes back
   online, the queued orders are synced. If there's a
   conflict (e.g., the customer is now over their
   credit limit, or the inventory is now insufficient),
   the system flags the conflict for manual review.

The 3 components are the *minimum* for offline support.
A senior SA might also discuss:

- **Idempotency keys** on order creation, so the same
  offline order isn't double-submitted when the rep
  reconnects.
- **Sync strategy** (push-based with exponential
  backoff, vs. pull-based with a sync window).
- **Conflict UI** (how the rep resolves a conflict in
  the field).

---

## 11. The 5 things the design signals

If you design this API in an interview, the 5 things
you signal:

1. **You've designed production APIs.** The resource
   model, error model, pagination, and auth are not
   generic — they're the patterns of real-world APIs.
2. **You think about user roles.** The 4 roles (sales
   rep, retail manager, admin, ERP) are the *spine* of
   the design.
3. **You think about constraints.** The offline support
   and the ERP integration are real-world constraints,
   not generic "best practices."
4. **You think about versioning and lifecycle.** The
   URL versioning and the mobile app update cycle are
   the long-term concerns.
5. **You think about consistency.** The inventory real-
   time requirement and the conflict resolution are the
   *consistency* concerns.

The 5 signals are the senior SA move. A junior SA
designs a generic e-commerce API without the
constraints.

---

## Try it

For a different scenario (e.g., "design the REST API for
a food delivery platform like DoorDash with 10k
restaurants, 1M customers, and 50k daily orders"), apply
the same 4-part structure:

1. **Resource model.** (Restaurants, customers, orders,
   deliveries, drivers, payments.)
2. **Endpoint design.** (With HTTP methods and status
   codes.)
3. **Error model and pagination.** (With the same
   patterns.)
4. **Auth model and versioning.** (With roles and
   scopes.)

Run it by a friend who's done API design. Get feedback on
what's missing. The investment is 60-90 minutes; the
return is the API design round of the interview.

For more system design depth, see
`../system_design/04_twitter/` and
`../system_design/09_uber_eats/`, which are full
worked examples of API design at scale.
