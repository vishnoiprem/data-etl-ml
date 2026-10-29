# System Design Sub-Lesson 1 — Read-Heavy Systems (the canonical Pattern 1 walkthrough)

> **Read-heavy systems are the most common system design pattern.** 30-40% of system design questions are read-heavy (Twitter timeline, news feed, product catalog, shipment tracker). The FDE signal: a candidate who names the QPS AND the cache hit rate AND the read replica count AND the cost ceiling — is showing they can own a system at scale. **This sub-lesson walks through the canonical read-heavy design.**

---

## Why read-heavy systems are the FDE signal

The 4 things the interviewer is testing:

1. **Can you read the requirements?** Read-heavy = 10:1 reads to writes (or higher). The requirement drives the design.
2. **Can you pick the right cache?** Redis for hot keys (top 1%), CDN for static assets, in-memory for the read model.
3. **Can you handle the read replica lag?** Read replicas lag the primary by 1-5 seconds. The candidate who names the lag and the fallback is showing they understand the operational boundary.
4. **Can you name the cost ceiling?** "$50/month for 10M monthly active users" is the FDE answer. "It would cost $X" without the math is hand-waving.

**The FDE pattern:** clarify → decompose → design → tradeoffs. Same as decomposition, but the design is infrastructure-focused.

---

## The canonical read-heavy design (worked example)

### The prompt

> "Design a read-heavy system: a product catalog for an e-commerce site. 10M monthly active users, 100K products, 1000 reads per second, 10 writes per user per day. The product data is updated by the merchandising team every 6 hours."

### Step 1: Clarify (5-7 minutes)

**The 5 questions:**

1. **What's the user?** End customers browsing the catalog.
2. **What's the scale?** 10M MAU, 1000 QPS reads, ~10 writes per user per day (browsing + cart updates).
3. **What's the constraint?** Latency < 100ms P95, cost < $1000/month.
4. **What's the failure mode?** Product data stale (6-hour update window). The user sees the old price.
5. **What's the timeline?** MVP in 2 weeks; full scale in 6 weeks.

### Step 2: Decompose (10-12 minutes)

**The 3 lists:**

**Entities:**
- Product (id, name, description, image_url, price, inventory, category_id)
- Category (id, name, parent_id)
- User (id, name, cart)
- Cart (user_id, product_id, quantity)
- Event (user_id, event_type, product_id, timestamp)

**Services:**
- ProductService (CRUD for products; called by merchandising team)
- CatalogService (read API for products; called by frontend)
- CartService (CRUD for cart; called by frontend)
- SearchService (full-text search; called by frontend)

**Flows:**
- User browses catalog → CatalogService reads from cache → if cache miss, reads from Postgres → returns to user
- Merchandising team updates product → ProductService writes to Postgres → invalidates cache → next read repopulates cache
- User adds to cart → CartService writes to Postgres → returns to user

### Step 3: Design (15-20 minutes)

**The API contracts (3-5 endpoints):**

```
GET /products?category=X&page=Y&size=Z
  → 200 OK
  → {"products": [{"id": "P1", "name": "...", "price": 19.99, ...}], "total": 1000, "page": 1}

GET /products/{id}
  → 200 OK
  → {"id": "P1", "name": "...", "description": "...", "price": 19.99, "inventory": 100}

POST /products (merchandising only)
  → 201 Created
  → {"id": "P1", ...}

PUT /products/{id} (merchandising only)
  → 200 OK
  → {"id": "P1", ...}

GET /products/{id}/inventory
  → 200 OK
  → {"product_id": "P1", "inventory": 100}
```

**The data model (3-5 tables):**

```
products (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  image_url VARCHAR(255),
  price DECIMAL(10, 2) NOT NULL,
  inventory INT NOT NULL,
  category_id INT REFERENCES categories(id),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
)

categories (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  parent_id INT REFERENCES categories(id)
)

users (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL
)

carts (
  user_id BIGINT REFERENCES users(id),
  product_id BIGINT REFERENCES products(id),
  quantity INT NOT NULL,
  PRIMARY KEY (user_id, product_id)
)

events (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  event_type VARCHAR(50) NOT NULL,
  product_id BIGINT REFERENCES products(id),
  timestamp TIMESTAMP NOT NULL DEFAULT NOW()
)
```

**The scale model:**

- **QPS:** 1000 reads/sec (peak: 3000 reads/sec on Black Friday)
- **Storage:** 100K products × 1KB each = 100MB; 10M users × 100 events = 1B events × 100 bytes = 100GB
- **Bandwidth:** 1000 QPS × 1KB = 1MB/sec
- **Cost:** $400/month (Postgres $200 + Redis $50 + CDN $50 + 3 read replicas $50 + S3 $50)

### Step 4: Tradeoffs (5-7 minutes)

**The 3 tradeoffs:**

1. **Redis vs Memcached for the cache.** Redis is more featureful (persistence, sorted sets) but Memcached is simpler and cheaper. Pick Redis for the catalog cache (need to invalidate by category), Memcached for the session cache (just key-value).
2. **Postgres read replicas (3-5x) vs Cassandra.** Postgres read replicas are simpler and cheaper at 1000 QPS. Cassandra is more scalable but adds operational complexity. Pick Postgres for 1000 QPS; consider Cassandra at 10K+ QPS.
3. **Cache TTL: 5 minutes vs invalidate on write.** TTL is simpler; invalidate-on-write is more correct. Pick TTL for product descriptions (eventual consistency is fine), invalidate-on-write for product prices (must be fresh).

**The closing line:** "For 10M MAU at 1000 QPS reads with 100ms P95 latency, I'd use Postgres with 3 read replicas, Redis for the top 1% of hot keys (5-minute TTL for descriptions, invalidate-on-write for prices), and a CDN for static assets. The cost is $400/month, under the $1000/month ceiling. The failure mode is read replica lag (5s lag at P99); the fallback is the primary with a 2s timeout."

---

## The 5 most common read-heavy questions

The 5 questions that cover 90% of read-heavy system design:

1. **"Design a Twitter timeline"** — covered by the canonical example above, with fan-out on read vs fan-out on write.
2. **"Design a news feed"** — same pattern, with ranking by recency + engagement.
3. **"Design a product catalog"** — covered above.
4. **"Design a shipment tracker"** — same pattern, with read-heavy on shipment status + write-heavy on carrier webhooks.
5. **"Design a URL shortener"** — same pattern, with cache + read replicas + ID generator.

**The pattern:** read-heavy = Postgres + read replicas + Redis + CDN. The variations are the ranking algorithm (timeline), the update frequency (6-hour catalog vs 1-minute shipment), and the consistency requirement (eventual vs strong).

---

## The 5 anti-patterns for read-heavy systems

1. **Naming a technology in the first 5 minutes.** The framework says: clarify, decompose, design, tradeoffs. The technology comes in step 3.
2. **Skipping the cost calculation.** "It would cost $X/month" without the math is hand-waving. The cost model is the FDE signal.
3. **Picking 1 pattern when 2 fit.** Most read-heavy questions are 2 patterns combined (read-heavy + caching, or read-heavy + search).
4. **Skipping the failure mode.** Every system has a failure mode. The signal is naming it AND the fallback.
5. **Skipping the read replica lag.** The candidate who doesn't know read replicas lag the primary is signaling they can't operate a read-heavy system.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What's the read replica lag?" | "5 seconds at P99. The fallback is the primary with a 2-second timeout." |
| 2. "How would you handle a hot key (the iPhone launch)?" | "I'd pre-warm the cache for the iPhone product page. I'd use a CDN for the static assets. I'd add a rate limiter for the product page." |
| 3. "How would you scale to 10x?" | "I'd add 10 more read replicas (30 total). I'd move the cache to a Redis cluster. I'd move the static assets to a multi-region CDN." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../decomposition/README.md` | The 4-step framework (clarify → decompose → design → tradeoffs) |
| `../swe-coding/01-arrays.md` | The 2 pointers / sliding window patterns (for the search ranking) |
| `../system-design/README.md` | The 9 patterns cheat sheet (Pattern 1: read-heavy) |

---

## The thesis

**Read-heavy systems are the most common system design pattern.** The candidate who names the QPS AND the cache hit rate AND the read replica count AND the cost ceiling — is showing they can own a system at scale.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The 5 worked examples (Twitter, news feed, catalog, shipment tracker, URL shortener) are the patterns. Practice them out loud, time yourself at 60 minutes per question, and rehearse with an AI assistant.

**General prep gets you past the resume screen. System design prep gets you past the centerpiece round at Anthropic, OpenAI, AWS FDE, Databricks, and Scale AI.**