# System Design Sub-Lesson 2 — Event-Driven Systems (the canonical Pattern 2 walkthrough)

> **Event-driven systems are the second most common system design pattern.** 20-30% of system design questions involve events (carrier webhooks, Stripe payments, audit logs, message bus). The FDE signal: a candidate who names the event ordering guarantee (FIFO vs at-least-once) AND the dead-letter queue AND the consumer lag — is showing they can own an event-driven system. **This sub-lesson walks through the canonical event-driven design.**

---

## Why event-driven systems are the FDE signal

The 4 things the interviewer is testing:

1. **Can you read the requirements?** Event-driven = events flow through a bus; the consumer processes them. The requirement drives the design (FIFO vs at-least-once, batch vs streaming).
2. **Can you pick the right message bus?** Kafka for high throughput + replay; SQS for simple queueing; Postgres `events` table for low scale + ACID.
3. **Can you handle the consumer lag?** If the consumer is slow, the queue grows. The candidate who names the lag and the alert is showing they understand the operational boundary.
4. **Can you handle the dead-letter queue?** When an event fails 5 retries, it goes to the DLQ. The candidate who names the DLQ and the manual replay is showing they understand the failure mode.

**The FDE pattern:** clarify → decompose → design → tradeoffs. Same as read-heavy, but the design is event-focused.

---

## The canonical event-driven design (worked example)

### The prompt

> "Design an event-driven system: a carrier webhook receiver for a shipment tracking service. Carriers send 100 webhooks per second (shipment status updates). The system updates the shipment in Postgres and fires a side effect (email notification to the customer). The customer wants the update within 30 seconds."

### Step 1: Clarify (5-7 minutes)

**The 5 questions:**

1. **What's the user?** Carriers (external) sending webhooks; end customers (internal) receiving email notifications.
2. **What's the scale?** 100 webhooks/sec (peak: 500/sec); ~30 seconds end-to-end latency.
3. **What's the constraint?** 30-second end-to-end latency; cost < $200/month; at-least-once delivery (no events lost).
4. **What's the failure mode?** Carrier sends duplicate webhook; consumer crashes mid-event; database write fails.
5. **What's the timeline?** MVP in 2 weeks; full scale in 6 weeks.

### Step 2: Decompose (10-12 minutes)

**The 3 lists:**

**Entities:**
- Shipment (id, status, carrier, origin, destination, updated_at)
- WebhookEvent (id, carrier, payload, received_at, processed_at)
- Notification (id, shipment_id, user_id, channel, sent_at)
- DeadLetterEvent (id, payload, error_message, failed_at)

**Services:**
- WebhookReceiver (validates + persists the webhook)
- EventBus (Kafka or SQS)
- ShipmentUpdater (consumes from bus, updates Postgres)
- NotificationDispatcher (consumes from bus, sends email)

**Flows:**
- Carrier sends webhook → WebhookReceiver validates → persists to WebhookEvent table → publishes to EventBus
- EventBus → ShipmentUpdater consumes → updates Shipment in Postgres → fires side effect (publishes to notification topic)
- NotificationDispatcher consumes notification topic → sends email → updates Notification in Postgres

### Step 3: Design (15-20 minutes)

**The API contracts (3-5 endpoints):**

```
POST /webhooks/carrier/{carrier_name}
  Headers: X-Carrier-Signature (HMAC)
  Body: {"shipment_id": "PF-1003", "status": "delivered", "timestamp": "2026-10-10T10:00:00Z"}
  → 200 OK
  → {"event_id": "EVT-12345"}

GET /shipments/{id}
  → 200 OK
  → {"id": "PF-1003", "status": "delivered", "carrier": "DHL", ...}

GET /shipments/{id}/events
  → 200 OK
  → [{"event_id": "EVT-12345", "status": "delivered", "timestamp": "..."}, ...]

GET /admin/dlq
  → 200 OK
  → [{"event_id": "EVT-12340", "payload": {...}, "error": "Database timeout", "failed_at": "..."}]
```

**The data model (3-5 tables):**

```
shipments (
  id VARCHAR(20) PRIMARY KEY,
  status VARCHAR(50) NOT NULL,
  carrier VARCHAR(50) NOT NULL,
  origin VARCHAR(100),
  destination VARCHAR(100),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
)

webhook_events (
  id BIGSERIAL PRIMARY KEY,
  carrier VARCHAR(50) NOT NULL,
  shipment_id VARCHAR(20) REFERENCES shipments(id),
  payload JSONB NOT NULL,
  signature VARCHAR(255) NOT NULL,
  received_at TIMESTAMP NOT NULL DEFAULT NOW(),
  processed_at TIMESTAMP
)

notifications (
  id BIGSERIAL PRIMARY KEY,
  shipment_id VARCHAR(20) REFERENCES shipments(id),
  user_id BIGINT,
  channel VARCHAR(20) NOT NULL,
  sent_at TIMESTAMP
)

dead_letter_events (
  id BIGSERIAL PRIMARY KEY,
  event_id BIGINT,
  payload JSONB,
  error_message TEXT,
  failed_at TIMESTAMP NOT NULL DEFAULT NOW()
)
```

**The scale model:**

- **QPS:** 100 webhooks/sec (peak: 500/sec)
- **Storage:** 100K shipments × 1KB = 100MB; 100 webhooks/sec × 86400 sec × 1KB = 8.6GB/day
- **Bandwidth:** 100 QPS × 1KB = 100KB/sec
- **Cost:** $200/month (Kafka $100 + worker VMs $50 + Postgres $30 + SES $20 + CloudWatch $10)

### Step 4: Tradeoffs (5-7 minutes)

**The 3 tradeoffs:**

1. **Kafka vs SQS vs Postgres events table.** Kafka for high throughput + replay; SQS for simple queueing; Postgres events table for low scale + ACID. Pick Kafka for 100 webhooks/sec with replay; SQS for 10 webhooks/sec without replay.
2. **Idempotency key vs deduplication window.** Idempotency key (carrier-supplied or hash of payload) prevents duplicates at the consumer. Pick idempotency key for strong consistency; pick deduplication window (5-min) for simplicity.
3. **Synchronous notification vs async notification.** Synchronous is simpler but blocks the consumer; async is more resilient but adds latency. Pick async for 30-second end-to-end; pick synchronous for 1-second end-to-end.

**The closing line:** "For 100 webhooks/sec with 30-second end-to-end latency and at-least-once delivery, I'd use Kafka for the event log, a worker pool with 4 workers to consume + update Postgres, and a dead-letter queue at 5 retries. The idempotency key is the carrier-supplied event ID. The cost is $200/month, under the $200/month ceiling. The failure mode is consumer lag; the alert is at 1 minute lag."

---

## The 5 most common event-driven questions

The 5 questions that cover 90% of event-driven system design:

1. **"Design a Stripe payments event bus"** — covered by the canonical example above, with idempotency keys + DLQ.
2. **"Design a carrier webhook receiver"** — covered above.
3. **"Design an audit log"** — same pattern, with append-only event log + replay.
4. **"Design a message bus for a chat application"** — same pattern, with FIFO ordering + per-user queue.
5. **"Design a real-time analytics pipeline"** — same pattern, with streaming + windowing + aggregation.

**The pattern:** event-driven = event log (Kafka/SQS) + consumer + DLQ + idempotency. The variations are the ordering guarantee (FIFO vs at-least-once), the throughput (100 events/sec vs 100K events/sec), and the latency (30 seconds vs 100ms).

---

## The 5 anti-patterns for event-driven systems

1. **Naming a technology in the first 5 minutes.** The framework says: clarify, decompose, design, tradeoffs. The technology comes in step 3.
2. **Skipping the idempotency story.** The candidate who doesn't mention idempotency keys is signaling they don't understand event-driven systems.
3. **Skipping the dead-letter queue.** The candidate who doesn't mention the DLQ is signaling they don't think about failure modes.
4. **Skipping the consumer lag alert.** The candidate who doesn't monitor consumer lag is signaling they don't operate the system.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you prevent duplicate events?" | "The idempotency key is the carrier-supplied event ID. The consumer checks the `webhook_events` table before processing. If the event ID already exists, skip." |
| 2. "How do you handle a slow consumer?" | "The alert is at 1 minute consumer lag. The fallback is to add more workers. The DLQ kicks in at 5 retries." |
| 3. "How do you replay events?" | "Kafka supports replay from any offset. I'd replay from the last 24 hours after a bad deploy." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../decomposition/README.md` | The 4-step framework (clarify → decompose → design → tradeoffs) |
| `../swe-coding/04-trees-graphs.md` | The DFS / BFS / topological sort patterns (for event ordering) |
| `../system-design/README.md` | The 9 patterns cheat sheet (Pattern 2: event-driven) |

---

## The thesis

**Event-driven systems are the second most common system design pattern.** The candidate who names the event ordering guarantee AND the dead-letter queue AND the consumer lag — is showing they can own an event-driven system.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The 5 worked examples (Stripe, carrier webhook, audit log, message bus, analytics) are the patterns. Practice them out loud, time yourself at 60 minutes per question, and rehearse with an AI assistant.

**General prep gets you past the resume screen. System design prep gets you past the centerpiece round at Anthropic, OpenAI, AWS FDE, Databricks, and Scale AI.**