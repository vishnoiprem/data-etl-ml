# System Design Sub-Lesson 5 — Transactional Systems (the canonical Pattern 5 walkthrough)

> **Transactional systems are the fifth most common system design pattern.** 10-15% of system design questions involve ACID transactions (refund flow, payment processing, inventory management, order placement). The FDE signal: a candidate who names the idempotency key AND the ACID guarantees AND the circuit breaker — is showing they can own a transactional system. **This sub-lesson walks through the canonical transactional design.**

---

## Why transactional systems are the FDE signal

The 4 things the interviewer is testing:

1. **Can you read the requirements?** Transactional = the operation must be atomic, consistent, isolated, and durable. The requirement drives the design (ACID vs BASE, single-region vs multi-region).
2. **Can you pick the right database?** Postgres for ACID + relational; MySQL for ACID + simpler ops; DynamoDB for ACID + serverless.
3. **Can you handle the idempotency?** Duplicate requests are common (network retries, user double-clicks). The candidate who names the idempotency key is showing they understand the failure mode.
4. **Can you handle the external API failure?** The transaction calls an external API (Stripe, payment processor). The candidate who names the circuit breaker is showing they understand the operational boundary.

**The FDE pattern:** clarify → decompose → design → tradeoffs. Same as the other patterns, but the design is ACID-focused.

---

## The canonical transactional design (worked example)

### The prompt

> "Design a transactional system: a refund flow for an e-commerce platform. Customers request refunds; the system processes them via Stripe. 1000 refunds/day, $100 average refund, 30-second end-to-end latency. The system should never double-refund (idempotency) and should never leave the refund in a 'pending' state (atomicity)."

### Step 1: Clarify (5-7 minutes)

**The 5 questions:**

1. **What's the user?** Customers (external) requesting refunds; CS team (internal) processing them.
2. **What's the scale?** 1000 refunds/day = ~0.01 refunds/sec average (peak: 1 refund/sec on Black Friday); 30-second end-to-end latency.
3. **What's the constraint?** Never double-refund; never leave in pending state; cost < $200/month; strong consistency.
4. **What's the failure mode?** Stripe API timeout; database transaction abort; user retries.
5. **What's the timeline?** MVP in 2 weeks; full scale in 4 weeks.

### Step 2: Decompose (10-12 minutes)

**The 3 lists:**

**Entities:**
- Refund (id, order_id, customer_id, amount, status, idempotency_key, created_at, completed_at)
- RefundAttempt (refund_id, stripe_response, attempted_at)
- StripeTransaction (refund_id, stripe_charge_id, amount, status)
- AuditLog (refund_id, action, actor, timestamp)

**Services:**
- RefundAPI (POST /refunds returns refund_id)
- RefundProcessor (validates + processes via Stripe)
- StripeClient (wraps Stripe API with circuit breaker)
- AuditLogger (logs every action)

**Flows:**
- Customer requests refund → RefundAPI validates → checks idempotency_key → starts database transaction → calls Stripe → updates database → commits transaction
- If Stripe succeeds: status = 'completed', completed_at = now
- If Stripe fails: status = 'failed', refund can be retried with the same idempotency_key
- If database transaction aborts: retry with the same idempotency_key

### Step 3: Design (15-20 minutes)

**The API contracts (3-5 endpoints):**

```
POST /refunds
  Headers: Idempotency-Key: <UUID>
  Body: {"order_id": "ORD-12345", "amount": 100.00, "reason": "..."}
  → 201 Created
  → {"refund_id": "REF-12345", "status": "processing", "idempotency_key": "..."}

GET /refunds/{id}
  → 200 OK
  → {"refund_id": "REF-12345", "status": "completed", "amount": 100.00, "stripe_charge_id": "ch_..."}

GET /refunds?status=processing&page=1&size=50
  → 200 OK
  → {"refunds": [...], "total": 10, "page": 1}

POST /refunds/{id}/retry
  → 200 OK
  → {"refund_id": "REF-12345", "status": "processing"}
```

**The data model (3-5 tables):**

```
refunds (
  id BIGSERIAL PRIMARY KEY,
  order_id VARCHAR(50) NOT NULL,
  customer_id BIGINT NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'processing',  -- processing, completed, failed
  idempotency_key VARCHAR(255) UNIQUE NOT NULL,
  stripe_charge_id VARCHAR(255),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMP,
  UNIQUE(idempotency_key)
)

refund_attempts (
  id BIGSERIAL PRIMARY KEY,
  refund_id BIGINT REFERENCES refunds(id),
  stripe_response JSONB,
  attempted_at TIMESTAMP NOT NULL DEFAULT NOW()
)

audit_log (
  id BIGSERIAL PRIMARY KEY,
  refund_id BIGINT REFERENCES refunds(id),
  action VARCHAR(50) NOT NULL,
  actor VARCHAR(50) NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW()
)
```

**The scale model:**

- **QPS:** 0.01 refunds/sec average (peak: 1 refund/sec); 30 seconds per refund
- **Storage:** 1000 refunds/day × 1KB = 1MB/day; 1 year = 365MB
- **Bandwidth:** 0.01 QPS × 1KB = 0.01KB/sec
- **Cost:** $200/month (Postgres $100 + Stripe $50 + worker VM $30 + CloudWatch $20)

### Step 4: Tradeoffs (5-7 minutes)

**The 3 tradeoffs:**

1. **Synchronous Stripe call vs async Stripe call.** Synchronous is simpler; async is more resilient. Pick synchronous for 30-second end-to-end; pick async for 1-second end-to-end.
2. **Database transaction vs saga pattern.** Database transaction is ACID but locks the row. Saga is more scalable but eventual consistency. Pick database transaction for single-row refunds; pick saga for multi-step refunds.
3. **Idempotency key in the request vs in the database.** Request idempotency key is more flexible (client can choose). Database idempotency key is more reliable. Pick request idempotency key for client control; pick database idempotency key for server enforcement.

**The closing line:** "For 1000 refunds/day with 30-second end-to-end latency and never-double-refund, I'd use Postgres with ACID transactions, a Stripe client with a circuit breaker, and an idempotency key on every POST. The cost is $200/month, under the $200/month ceiling. The failure mode is Stripe API timeout; the fallback is to retry with the same idempotency key."

---

## The 5 most common transactional questions

The 5 questions that cover 90% of transactional system design:

1. **"Design a refund flow"** — covered by the canonical example above.
2. **"Design a payment processing system"** — same pattern, with Stripe + idempotency + circuit breaker.
3. **"Design an inventory management system"** — same pattern, with row-level locking + ACID.
4. **"Design an order placement system"** — same pattern, with cart + inventory + payment in a single transaction.
5. **"Design a bank transfer system"** — same pattern, with double-entry bookkeeping + ACID.

**The pattern:** transactional = ACID database + idempotency key + circuit breaker on external API. The variations are the latency (30 seconds vs 1 second), the consistency model (strong vs eventual), and the failure mode (network timeout vs duplicate request).

---

## The 5 anti-patterns for transactional systems

1. **Naming a technology in the first 5 minutes.** The framework says: clarify, decompose, design, tradeoffs. The technology comes in step 3.
2. **Skipping the idempotency key.** The candidate who doesn't mention idempotency keys is signaling they don't understand transactional systems.
3. **Skipping the circuit breaker.** The candidate who doesn't mention the circuit breaker on the external API is signaling they don't understand the failure mode.
4. **Skipping the rollback strategy.** The candidate who doesn't mention rollback (compensating transaction) is signaling they don't think about partial failures.
5. **Skipping the audit log.** The candidate who doesn't mention the audit log is signaling they don't think about compliance + debugging.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What if Stripe succeeds but the database transaction aborts?" | "The refund is in 'processing' state. The retry with the same idempotency key will check Stripe (succeeded) and update the database to 'completed'." |
| 2. "What if the database transaction succeeds but the response is lost?" | "The client retries with the same idempotency key. The server checks the database (already 'completed') and returns 200 OK with the existing refund_id." |
| 3. "How do you handle concurrent refunds for the same order?" | "Row-level locking on the order_id. The second refund waits for the first to complete. If both have the same idempotency key, the second returns 200 OK with the existing refund_id." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../decomposition/README.md` | The 4-step framework (clarify → decompose → design → tradeoffs) |
| `../swe-coding/04-trees-graphs.md` | The DFS / BFS patterns (for transaction ordering) |
| `../system-design/README.md` | The 9 patterns cheat sheet (Pattern 5: transactional) |

---

## The thesis

**Transactional systems are the fifth most common system design pattern.** The candidate who names the idempotency key AND the ACID guarantees AND the circuit breaker — is showing they can own a transactional system.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The 5 worked examples (refund, payment, inventory, order placement, bank transfer) are the patterns. Practice them out loud, time yourself at 60 minutes per question, and rehearse with an AI assistant.

**General prep gets you past the resume screen. System design prep gets you past the centerpiece round at Anthropic, OpenAI, AWS FDE, Databricks, and Scale AI.**