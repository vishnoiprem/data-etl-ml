# System Design Sub-Lesson 3 — Async Jobs and Workers (the canonical Pattern 3 walkthrough)

> **Async jobs and workers are the third most common system design pattern.** 15-20% of system design questions involve async processing (email send, draft generation, video transcoding, batch jobs). The FDE signal: a candidate who names the job queue AND the worker pool size AND the retry policy AND the failure isolation — is showing they can own an async system. **This sub-lesson walks through the canonical async job design.**

---

## Why async jobs are the FDE signal

The 4 things the interviewer is testing:

1. **Can you read the requirements?** Async = the request returns immediately with a job_id; the worker processes the job later. The requirement drives the design (synchronous vs async, batch vs streaming).
2. **Can you pick the right job queue?** Redis with BLPOP for simple queueing; Celery + RabbitMQ for rich features; AWS SQS for managed service.
3. **Can you handle worker death?** Workers die (OOM, deploy, hardware failure). The candidate who names the re-queue logic is showing they understand the failure mode.
4. **Can you handle external API failure?** The worker calls an external API. The candidate who names the circuit breaker is showing they understand the operational boundary.

**The FDE pattern:** clarify → decompose → design → tradeoffs. Same as event-driven, but the design is job-focused.

---

## The canonical async job design (worked example)

### The prompt

> "Design an async job system: an email send service for a marketing platform. Customers submit 100K emails per day. Each email takes 5 seconds to send (SMTP + tracking pixel). The system should retry failed emails 3 times with exponential backoff. The customer wants the API to return within 100ms."

### Step 1: Clarify (5-7 minutes)

**The 5 questions:**

1. **What's the user?** Customers (internal) submitting email jobs; end recipients (external) receiving emails.
2. **What's the scale?** 100K emails/day = ~1.2 emails/sec average (peak: 10 emails/sec on campaign launch); 5 seconds per email.
3. **What's the constraint?** API < 100ms P95; cost < $100/month; at-least-once delivery (no emails lost).
4. **What's the failure mode?** SMTP server timeout; tracking pixel blocked; recipient bounces.
5. **What's the timeline?** MVP in 2 weeks; full scale in 6 weeks.

### Step 2: Decompose (10-12 minutes)

**The 3 lists:**

**Entities:**
- EmailJob (id, recipient, subject, body, status, retry_count, created_at)
- EmailSend (job_id, smtp_response, sent_at)
- DeadLetterJob (job_id, error_message, failed_at)
- Worker (id, status, last_heartbeat)

**Services:**
- EmailAPI (POST /jobs returns job_id)
- JobQueue (Redis with BLPOP)
- EmailWorker (consumes from queue, calls SMTP, updates status)
- RetryScheduler (re-queues failed jobs with backoff)

**Flows:**
- Customer submits email → EmailAPI validates → enqueues to JobQueue → returns job_id
- EmailWorker dequeues → sends email → updates EmailJob status → if success, done; if fail, increment retry_count
- RetryScheduler re-queues failed jobs after exponential backoff (1min, 5min, 25min)
- After 3 retries, move to DeadLetterJob + alert

### Step 3: Design (15-20 minutes)

**The API contracts (3-5 endpoints):**

```
POST /jobs
  Body: {"recipient": "alice@example.com", "subject": "...", "body": "..."}
  → 201 Created
  → {"job_id": "JOB-12345", "status": "queued"}

GET /jobs/{id}
  → 200 OK
  → {"job_id": "JOB-12345", "status": "sent", "retry_count": 0, "sent_at": "..."}

GET /jobs?status=queued&page=1&size=50
  → 200 OK
  → {"jobs": [...], "total": 1000, "page": 1}

GET /admin/dlq
  → 200 OK
  → [{"job_id": "JOB-12340", "error": "SMTP timeout", "failed_at": "..."}]

POST /admin/dlq/{job_id}/replay
  → 200 OK
  → {"job_id": "JOB-12340", "status": "queued"}
```

**The data model (3-5 tables):**

```
email_jobs (
  id BIGSERIAL PRIMARY KEY,
  recipient VARCHAR(255) NOT NULL,
  subject VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'queued',  -- queued, processing, sent, failed, dlq
  retry_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  sent_at TIMESTAMP
)

email_sends (
  job_id BIGINT REFERENCES email_jobs(id),
  smtp_response TEXT,
  sent_at TIMESTAMP NOT NULL DEFAULT NOW()
)

dead_letter_jobs (
  job_id BIGINT PRIMARY KEY,
  error_message TEXT NOT NULL,
  failed_at TIMESTAMP NOT NULL DEFAULT NOW()
)

workers (
  id VARCHAR(50) PRIMARY KEY,
  status VARCHAR(20) NOT NULL,
  last_heartbeat TIMESTAMP NOT NULL DEFAULT NOW()
)
```

**The scale model:**

- **QPS:** 1.2 jobs/sec average (peak: 10 jobs/sec); 5 seconds per job
- **Storage:** 100K emails/day × 1KB = 100MB/day; 1 year = 36GB
- **Bandwidth:** 1.2 jobs/sec × 1KB = 1.2KB/sec
- **Cost:** $100/month (Redis $30 + 4 worker VMs $40 + Postgres $20 + SES $10)

### Step 4: Tradeoffs (5-7 minutes)

**The 3 tradeoffs:**

1. **Redis with BLPOP vs Celery + RabbitMQ vs SQS.** Redis is simpler and cheaper; Celery has rich features (scheduled jobs, priorities); SQS is managed but expensive. Pick Redis for simple queueing; Celery for scheduled jobs; SQS for managed service.
2. **Worker pool size: 4 vs 16.** 4 workers can process 0.8 jobs/sec (5 sec/job). 10 jobs/sec needs 16 workers. Pick 4 workers for 1.2 jobs/sec average; pick 16 workers for 10 jobs/sec peak.
3. **Retry policy: 3 retries vs 5 retries with exponential backoff.** 3 retries is simpler; 5 retries with backoff is more resilient. Pick 3 retries for low-value emails; pick 5 retries for high-value emails.

**The closing line:** "For 100K emails/day with < 100ms API latency and 3 retries with exponential backoff, I'd use Redis with BLPOP for the queue, a worker pool with 4 workers, and a circuit breaker on the SMTP API. The cost is $100/month, under the $100/month ceiling. The failure mode is worker death; the fallback is re-queue with exponential backoff (1min, 5min, 25min). After 3 retries, move to DLQ + alert."

---

## The 5 most common async job questions

The 5 questions that cover 90% of async job system design:

1. **"Design an email send service"** — covered by the canonical example above.
2. **"Design a draft generation service"** — same pattern, with LLM call + circuit breaker.
4. **"Design a video transcoding pipeline"** — same pattern, with FFmpeg worker + S3.
5. **"Design a batch job scheduler"** — same pattern, with cron + worker pool + retry.

**The pattern:** async jobs = job queue (Redis/Celery/SQS) + worker pool + retry + DLQ. The variations are the job duration (5 seconds vs 5 minutes), the throughput (1 job/sec vs 100 jobs/sec), and the failure mode (worker death vs external API failure).

---

## The 5 anti-patterns for async job systems

1. **Naming a technology in the first 5 minutes.** The framework says: clarify, decompose, design, tradeoffs. The technology comes in step 3.
2. **Skipping the worker death story.** The candidate who doesn't mention worker death is signaling they don't think about failure modes.
3. **Skipping the retry policy.** The candidate who doesn't mention retries with exponential backoff is signaling they don't understand async systems.
4. **Skipping the circuit breaker.** The candidate who doesn't mention the circuit breaker on the external API is signaling they don't understand the operational boundary.
5. **Skipping the DLQ.** The candidate who doesn't mention the DLQ is signaling they don't think about long-term failures.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What if a worker dies mid-job?" | "The job is re-queued by the heartbeat monitor (every 30 seconds). The new worker picks it up. The idempotency key prevents double-processing." |
| 2. "What if the SMTP server is slow?" | "The circuit breaker opens after 3 failures in 60 seconds. The fallback is to retry with exponential backoff. After 3 retries, move to DLQ." |
| 3. "How do you prioritize jobs?" | "Use a priority queue in Redis (sorted set). High-priority jobs are dequeued first." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../decomposition/README.md` | The 4-step framework (clarify → decompose → design → tradeoffs) |
| `../swe-coding/04-trees-graphs.md` | The DFS / BFS patterns (for queue processing) |
| `../system-design/README.md` | The 9 patterns cheat sheet (Pattern 3: async jobs) |

---

## The thesis

**Async jobs are the third most common system design pattern.** The candidate who names the job queue AND the worker pool size AND the retry policy AND the failure isolation — is showing they can own an async system.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The 5 worked examples (email, draft generation, video transcoding, batch job, image resize) are the patterns. Practice them out loud, time yourself at 60 minutes per question, and rehearse with an AI assistant.

**General prep gets you past the resume screen. System design prep gets you past the centerpiece round at Anthropic, OpenAI, AWS FDE, Databricks, and Scale AI.**