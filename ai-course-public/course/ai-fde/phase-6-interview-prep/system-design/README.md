# Module 7 — System Design Interviews

> **System design is the FDE's core technical round.** 60 minutes, open-ended, "design X for Y scale." The interviewer tests whether you can think at the system level, not the function level. **The signal: a candidate who names the QPS AND the cost ceiling AND the failure mode is showing they can own a system at scale.**

---

## The 4-step framework (the same one as decomposition)

System design uses the same 4-step framework as decomposition:

1. **Clarify** (5-7 min): the 5 questions
2. **Decompose** (10-12 min): the 3 lists (entities, services, flows)
3. **Design** (15-20 min): the 3 artifacts (API, data model, scale)
4. **Tradeoffs** (5-7 min): 3 tradeoffs, defended

**The difference:** system design focuses on the 9 patterns below; decomposition focuses on the open-ended problem. The framework is the same.

---

## The 9 system design patterns (the cheat sheet)

Every system design question fits one (or more) of these 9 patterns. **Memorize them.**

### Pattern 1: Read-heavy systems

**Examples:** Twitter timeline, news feed, product catalog, shipment tracker

- **Storage:** Postgres with read replicas (3-5× replicas for 10× QPS)
- **Cache:** Redis with 5-min TTL for hot keys (top 1% of queries)
- **API:** GET-only, 100k QPS, < 50ms P95
- **Cost:** $50/month (Postgres $20 + Redis $10 + 3 read replicas $20)
- **Failure mode:** read replica stale (5s lag) → fall back to primary with longer timeout

**PacificFreight mapping:** Phase 5 P4 (read replica in Tokyo).

**The FDE answer:** "For 100k QPS read-heavy, I'd use Postgres with 3 read replicas, Redis for the top 1% of hot keys, and a CDN for static assets. The cost is $50/month. The failure mode is replica lag; the fallback is the primary with a 2s timeout."

### Pattern 2: Event-driven systems

**Examples:** Carrier webhooks, Stripe payments, audit logs, message bus

- **Storage:** Append-only event log (Kafka, SQS, or Postgres `events` table)
- **Process:** Worker pool consumes events, updates state, fires side effects
- **API:** Webhook receiver + GET /state
- **Cost:** $30/month (Kafka $20 + worker VMs $10)
- **Failure mode:** event not processed → retry with exponential backoff, dead-letter queue at 5 retries

**PacificFreight mapping:** Phase 4 webhook for shipment status updates.

**The FDE answer:** "For event-driven, I'd use Kafka for the event log, a worker pool to consume + update state, and a dead-letter queue at 5 retries. The cost is $30/month. The failure mode is consumer lag; the alert is at 1 minute lag."

### Pattern 3: Async jobs and workers

**Examples:** Email send, draft generation, video transcoding, batch jobs

- **Queue:** Redis with BLPOP, or Celery + RabbitMQ, or AWS SQS
- **Worker:** Background process consumes jobs, calls external API, writes result
- **API:** POST /job (returns job_id), GET /job/{id} (returns status + result)
- **Cost:** $20/month (Redis $10 + worker VM $10)
- **Failure mode:** worker dies → job is re-queued; external API times out → circuit breaker returns 503

**PacificFreight mapping:** The drafter is an async job (the inference service runs in a worker).

**The FDE answer:** "For async jobs, I'd use Redis with BLPOP for the queue, a worker pool with 4 workers, and a circuit breaker on the external API. The cost is $20/month. The failure mode is worker death; the fallback is re-queue with exponential backoff."

### Pattern 4: Distributed data storage & partitioning

**Examples:** User data, time-series, multi-tenant data, sharded Postgres

- **Storage:** Sharded Postgres (by user_id or tenant_id), or Cassandra, or DynamoDB
- **Sharding key:** user_id or tenant_id (the most common query)
- **Cross-shard queries:** denormalize into a read store (Elasticsearch)
- **Cost:** $100/month (10 shards × $10)
- **Failure mode:** shard is down → fall back to read replica with longer timeout; cross-shard query is slow → cache the result

**PacificFreight mapping:** Phase 5 P2 (per-tenant namespacing in Redis).

**The FDE answer:** "For 10TB+ distributed storage, I'd shard Postgres by tenant_id, with 10 shards for 10× growth. Cross-shard queries go to Elasticsearch. The cost is $100/month. The failure mode is shard death; the fallback is the read replica with a 5s timeout."

### Pattern 5: Transactional systems

**Examples:** Refund flow, payment processing, inventory management, order placement

- **Storage:** Postgres with ACID transactions
- **API:** POST /transaction with idempotency key
- **Cost:** $10/month (single Postgres)
- **Failure mode:** transaction fails → idempotency key prevents double-charge; user retries safely

**PacificFreight mapping:** Phase 4 P1 (refund.create tool with policy enforcement).

**The FDE answer:** "For transactional, I'd use Postgres with ACID, an idempotency key on every POST, and a circuit breaker on the external payment API. The cost is $10/month. The failure mode is transaction abort; the fallback is the user's retry with the same idempotency key."

### Pattern 6: Batch processing and data pipelines

**Examples:** Daily aggregation, ML training, log analysis, ETL

- **Storage:** S3 for raw data, Postgres for aggregated data
- **Scheduler:** Cron, Airflow, or AWS Step Functions
- **Worker:** Spark, Dask, or a Python script
- **API:** Trigger + status endpoint
- **Cost:** $50/month (S3 $20 + worker VM $30)
- **Failure mode:** worker dies → restart with checkpoint; aggregation is late → alert at 2× SLA

**PacificFreight mapping:** The Monday iteration review is a batch job (aggregates the week's usage.jsonl).

**The FDE answer:** "For batch processing, I'd use S3 for raw data, Airflow for scheduling, and a Python worker for aggregation. The cost is $50/month. The failure mode is worker death; the fallback is a checkpoint + restart."

### Pattern 7: Real-time and collaborative systems

**Examples:** Google Docs, Figma, multiplayer games, chat

- **Storage:** CRDT (Yjs, Automerge) or operational transform
- **Sync:** WebSocket per user, broadcast changes
- **API:** WS /sync
- **Cost:** $50/month (WebSocket server $20 + state store $30)
- **Failure mode:** WS disconnects → client reconnects with last-known version, server replays missed changes

**PacificFreight mapping:** None directly (PacificFreight is not real-time collaborative). The Phase 5 P4 multi-region failover uses similar patterns.

**The FDE answer:** "For real-time collaborative, I'd use a CRDT (Yjs) for the state, WebSocket per user for sync, and S3 for snapshots. The cost is $50/month. The failure mode is disconnect; the fallback is reconnect with last-known version + replay."

### Pattern 8: Media streaming and content delivery

**Examples:** Netflix, YouTube, Spotify, podcast platforms

- **Storage:** S3 for media files
- **CDN:** CloudFront, Fastly, or Cloudflare
- **Transcoding:** FFmpeg worker, or AWS MediaConvert
- **API:** GET /video/{id} (returns signed CDN URL)
- **Cost:** $200/month (S3 $50 + CDN $100 + transcoding $50)
- **Failure mode:** CDN is down → fall back to S3 with longer timeout; transcoding fails → retry with backoff

**PacificFreight mapping:** None directly. This is outside the FDE scope for most roles, but tested at senior levels.

**The FDE answer:** "For media streaming, I'd use S3 for storage, CloudFront for the CDN, and MediaConvert for transcoding. The cost is $200/month. The failure mode is CDN down; the fallback is S3 with a 5s timeout."

### Pattern 9: Agentic AI systems

**Examples:** Claude Code, Cursor, LangChain agents, MCP servers, multi-agent dispatchers

- **Storage:** Vector DB (Pinecone, Weaviate) for context; Postgres for state
- **LLM:** Hosted (GPT-4o-mini) or self-hosted (Qwen-1.5B)
- **Tools:** MCP server with policy enforcement
- **Orchestrator:** LangGraph ReAct, or hand-rolled state machine
- **API:** POST /agent (returns agent_path + result)
- **Cost:** $20-200/month (LLM + vector DB + tools)
- **Failure mode:** LLM hallucinates → citation in every response; tool call fails → retry with backoff; cost ceiling breached → circuit breaker

**PacificFreight mapping:** Phase 4 P1 (MCP server) + P2 (multi-agent dispatcher) + Phase 4 P3 (SLM).

**The FDE answer:** "For agentic AI, I'd use a hybrid retriever (BM25 + dense + RRF), a hosted LLM with a circuit breaker, an MCP server with policy enforcement, and a cost ceiling as the kill switch. The cost is $20-200/month depending on the model. The failure mode is hallucination; the mitigation is citation in every response + thumbs-up/down feedback loop."

---

## The 4 system design anti-patterns

1. **Naming a technology in the first 5 minutes.** The framework says: clarify, decompose, design, tradeoffs. The technology comes in step 3.
2. **Skipping the cost calculation.** "It would cost $X/month" without the math is hand-waving.
3. **Picking 1 pattern when 2 fit.** Most system design questions are 2 patterns combined. (Real-time collaborative = Pattern 7 + Pattern 1.)
4. **Skipping the failure mode.** Every system has a failure mode. The signal is naming it AND the mitigation.

---

## How to use this module

1. **Memorize the 9 patterns.** They're the cheat sheet for 80% of system design questions.
2. **Memorize the 4-step framework** (clarify / decompose / design / tradeoffs). It's the same as decomposition.
3. **Practice on 1 question per pattern.** Total: 9 practice questions, 60 min each = 9 hours of practice.
4. **Rehearse with an AI assistant.** Have it score you on the 4 anti-patterns.
5. **Use the cost calculation as the closing line.** "Total cost: $X/month at Y QPS, under the $Z/month ceiling." That's the FDE answer.
