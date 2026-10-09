# Step 3 — Design (API contracts, data model, scale)

> **The design step is the system's body.** After 3 lists (entities, services, flows), you pick the simplest technology that satisfies the constraints. **The signal: a candidate who names the QPS AND the cost ceiling AND the failure mode is showing they understand the operational boundary.**

---

## The 3 artifacts (always, in this order)

### 1. API contracts (3-5 endpoints, with request/response shape)

API contracts are the system's surface area. Each endpoint has a request shape, a response shape, and a 1-line description.

```
POST /draft
  Request:  { email_id: str, user_id: str }
  Response: { draft_text: str, citations: list[str], request_id: str }
  Description: Generates a draft reply for the email.
  Errors:    429 (rate limit), 503 (LLM down), 500 (unknown)

POST /feedback
  Request:  { draft_id: str, user_id: str, rating: "up" | "down", comment?: str }
  Response: { feedback_id: str }
  Description: Records user feedback on a draft.
  Errors:    404 (draft not found)

GET /shipment/{shipment_id}
  Response: { shipment_id: str, status: str, eta: str, last_updated: str }
  Description: Looks up a shipment by ID.
  Errors:    404 (not found)
```

**The signal:** 3-5 endpoints, with the request/response shape on the whiteboard. Not "we'd have an API" but "POST /draft with this shape." The shape is the contract.

### 2. Data model (3-5 tables/collections, with keys + indexes)

Data model is the system's persistence. Each table has a primary key, foreign keys, and indexes for the queries you actually run.

```
shipments
  PK  shipment_id (str)
      customer_id (str, indexed)
      status (str)
      eta (datetime)
      last_updated (datetime)

emails
  PK  email_id (str)
      customer_id (str, indexed)
      subject (str)
      body (text)
      received_at (datetime, indexed)

drafts
  PK  draft_id (str)
  FK  email_id (str, indexed)
      draft_text (text)
      citations (jsonb)
      created_at (datetime, indexed)

feedback
  PK  feedback_id (str)
  FK  draft_id (str, indexed)
      user_id (str)
      rating (str)
      comment (text, nullable)
      created_at (datetime, indexed)
```

**The signal:** the candidate who names the primary key AND the index for the query is showing they understand the operational reality. (PacificFreight's most common query is "all drafts by user_id, last 7 days" — so the index on user_id + created_at is the signal.)

### 3. Scale model (QPS, storage, bandwidth, cost)

Scale model is the system's envelope. It answers "how big does this need to be?" in 4 numbers.

| Metric | Value | Calculation |
|---|---|---|
| QPS (avg) | 0.12 | 10k emails/day ÷ 86400 sec |
| QPS (peak) | 1.2 | 10× avg |
| Storage (1 yr) | 50 GB | (10k emails × 5 KB) + (10k drafts × 1 KB) + (10k feedback × 0.5 KB) × 365 |
| Bandwidth (peak) | 1 MB/s | 1.2 QPS × 100 KB response |
| Cost (monthly) | $4.09 | $0.50 LLM × 4.33 + $0.10 infra + $0.10 storage |

**The signal:** the candidate who names the QPS AND the cost ceiling AND the storage growth is showing they understand the operational boundary.

**The cost calculation is the FDE signal.** A senior FDE knows the cost of their system in $/month. A junior FDE names a technology and hopes the cost is fine.

---

## The 4 design anti-patterns

1. **Picking a technology before the design.** "We'd use Pinecone" is a technology. "We'd use a vector store with a BM25 fallback" is a design. The design names the requirement; the technology is a candidate.
2. **Skipping the indexes.** Every table needs at least 1 index for the queries you actually run. If you can't name the query, you can't name the index.
3. **Naming a cost without the calculation.** "$5/month" without "0.50 LLM × 4.33 + 0.10 infra" is hand-waving. The calculation is the signal.
4. **Skipping the failure mode.** Every API endpoint has a failure mode. If you don't name it, the interviewer assumes you haven't shipped one.

---

## The 5 design patterns (the cheat sheet)

### Pattern 1: Read-heavy (e.g., shipment tracker)

- **Storage:** Postgres with read replicas (3-5× replicas for 10× QPS)
- **Cache:** Redis with 5-min TTL for hot keys
- **API:** GET-only, 100k QPS, < 50ms P95
- **Cost:** $50/month (Postgres + Redis + 3 read replicas)
- **Failure mode:** read replica stale → fall back to primary with longer timeout

### Pattern 2: Event-driven (e.g., carrier webhooks)

- **Storage:** Append-only event log (Kafka, SQS, or Postgres `events` table)
- **Process:** Worker pool consumes events, updates state, fires side effects
- **API:** Webhook receiver + GET /state
- **Cost:** $30/month (Kafka + worker VMs)
- **Failure mode:** event not processed → retry with exponential backoff, dead-letter queue at 5 retries

### Pattern 3: Async jobs (e.g., draft generation)

- **Queue:** Redis with BLPOP or Celery
- **Worker:** Background process consumes jobs, calls LLM, writes result
- **API:** POST /job (returns job_id), GET /job/{id} (returns status + result)
- **Cost:** $20/month (Redis + worker VM)
- **Failure mode:** worker dies → job is re-queued; LLM times out → circuit breaker returns 503

### Pattern 4: Transactional (e.g., refund.create)

- **Storage:** Postgres with ACID transactions
- **API:** POST /transaction with idempotency key
- **Cost:** $10/month (single Postgres)
- **Failure mode:** transaction fails → idempotency key prevents double-charge; user retries safely

### Pattern 5: Real-time (e.g., collaborative editing)

- **Storage:** CRDT (e.g., Yjs) or operational transform
- **Sync:** WebSocket per user, broadcast changes
- **API:** WS /sync
- **Cost:** $50/month (WebSocket server + state store)
- **Failure mode:** WS disconnects → client reconnects with last-known version, server replays missed changes

**PacificFreight's drafter is Pattern 3 (async job).** The 5 case-study questions map to Patterns 1, 2, 3, 4, 1. The candidate who recognizes the pattern buys 5 minutes of thinking time.

---

## How to use this file

1. **Memorize the 3 artifacts** (API contracts, data model, scale model).
2. **Memorize the 5 patterns.** They're the cheat sheet for 80% of design questions.
3. **Practice on the 5 sample questions in `../README.md`.** Time yourself: 15-20 minutes for the 3 artifacts.
4. **Rehearse with an AI assistant.** Have it score you on the 4 anti-patterns.
5. **Use the cost calculation as the closing line.** "Total cost: $4.09/month at 10k emails/day, under the $5/month ceiling." That's the FDE signal.
