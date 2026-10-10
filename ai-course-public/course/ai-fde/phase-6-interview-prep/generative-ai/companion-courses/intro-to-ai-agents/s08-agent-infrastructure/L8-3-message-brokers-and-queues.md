# L8.3: Message brokers and queues — async, fan-out, and exactly-once

> **FDE framing in one line:** the message broker is the FDE's response to scale. Synchronous HTTP works for 50 concurrent runs; SQS works for 1000; Kafka works for 100,000. The FDE picks the broker that matches the customer's scale + latency + durability requirements. The wrong choice is a broker that's too big (over-engineering) or too small (lost messages).

## The 3 things you'll learn

1. The 4 message broker patterns: synchronous (request/response, easy, no durability), queue (SQS, RabbitMQ, durable, point-to-point), pub-sub (Kafka, NATS, durable, fan-out), and event sourcing (Kafka, durable, replay). The FDE picks the pattern based on the workload shape.
2. The 3 broker options compared: SQS (managed, simple, no replay), Kafka (self-hosted or managed, complex, replay), Redis Streams (in-memory, fast, no replay). The right choice depends on the durability + replay + scale requirements.
3. The "agent as a worker" pattern: the agent is a consumer of a queue; the API enqueues a task; the agent processes it; the result is returned via callback, webhook, or polling. The pattern decouples the API latency from the agent latency; the customer sees a 100ms response; the agent processes for 5 seconds.

## Concept

The message broker is the FDE's response to scale. When the customer has 5 concurrent runs, synchronous HTTP works fine. When the customer has 500 concurrent runs, the agent can't process them all at once; the queue absorbs the spike. When the customer has 50,000 concurrent runs, the queue is the only way to make the system work. **The broker is the buffer; the agent is the worker; the customer is the producer.**

The 4 message broker patterns:

1. **Synchronous (request/response).** The customer calls the API; the API calls the agent; the agent processes; the API returns the result. The pattern is the simplest; the latency is the agent's latency. The right choice when the customer has <50 concurrent runs, the agent's latency is acceptable (1-5s), and the customer can wait. The cost: 0 (no broker needed).
2. **Queue (point-to-point).** The customer calls the API; the API enqueues a task; the agent dequeues and processes; the result is returned via callback, webhook, or polling. The pattern decouples the API latency from the agent latency. The right choice when the customer has 100-1000 concurrent runs, the agent's latency is variable, or the customer needs durability (don't lose tasks if the agent is down).
3. **Pub-sub (fan-out).** The customer publishes an event; multiple consumers (agents, analytics, audit log) receive the event. The pattern is the right choice when the same event needs to trigger multiple actions (e.g., a refund event triggers: the agent, the analytics warehouse, the customer notification).
4. **Event sourcing.** The customer publishes every state change as an event; the events are stored in a log; the system can replay events to reconstruct state. The right choice when the customer needs audit trail, time travel, or to build multiple views of the same data. The right choice when the customer's compliance requires event retention.

The 3 broker options compared:

1. **SQS (AWS Simple Queue Service).** Managed queue; the FDE doesn't operate the broker. The right choice when the customer is on AWS, has 100-10,000 concurrent tasks, and doesn't need replay. SQS Standard offers at-least-once delivery; SQS FIFO offers exactly-once. The cost: $0.40 per 1M requests.
2. **Kafka (self-hosted or managed).** Distributed log; the FDE operates the cluster (or uses Confluent Cloud, MSK, or Redpanda). The right choice when the customer has 10,000+ concurrent tasks, needs replay, or has multiple consumers (pub-sub). The cost: $0.11/GB-month for storage + $0.10/M reads.
3. **Redis Streams.** In-memory log; the FDE uses an existing Redis. The right choice when the customer has Redis, has <1000 concurrent tasks, and can tolerate losing tasks if Redis crashes. The cost: included in existing Redis.

The "agent as a worker" pattern is the canonical pattern for the async agent. The customer calls the API; the API enqueues a task; the agent dequeues and processes; the result is returned via callback (the API provides a webhook URL), webhook (the agent calls the customer's webhook when done), or polling (the customer polls the API for the result). **The pattern decouples the API latency from the agent latency; the customer sees a 100ms response; the agent processes for 5 seconds.**

## The pattern

The 4 broker patterns (the FDE's reference):

```python
BROKER_PATTERNS = {
    "synchronous": {
        "description": "Customer → API → Agent → Response (in-line)",
        "latency": "agent's latency (1-5s)",
        "durability": "none (if the agent crashes, the task is lost)",
        "scale": "<50 concurrent",
        "example": "REST API; the customer waits for the result",
        "use_case": "interactive user requests, simple queries",
    },
    "queue": {
        "description": "Customer → API → Queue → Agent → Callback/Webhook/Polling",
        "latency": "100ms (API) + agent's latency (async)",
        "durability": "high (the queue persists the task; if the agent crashes, another agent picks up)",
        "scale": "100-10,000 concurrent",
        "example": "SQS; the customer is notified when the result is ready",
        "use_case": "long-running tasks, batch processing, async workflows",
    },
    "pub_sub": {
        "description": "Customer → Broker → Multiple consumers (agent, analytics, audit log)",
        "latency": "100ms (publish) + each consumer's latency",
        "durability": "high (each consumer has its own offset)",
        "scale": "10,000+ concurrent",
        "example": "Kafka; the agent, the analytics warehouse, and the audit log all see the same event",
        "use_case": "event-driven architectures, multiple consumers",
    },
    "event_sourcing": {
        "description": "Customer → Broker → Log → Replay (to reconstruct state)",
        "latency": "100ms (publish) + replay latency",
        "durability": "highest (every state change is in the log)",
        "scale": "10,000+ concurrent",
        "example": "Kafka + a state store; the system can replay any time range",
        "use_case": "audit trail, time travel, compliance",
    },
}
```

The 3 broker options (the FDE's reference):

```python
BROKER_OPTIONS = {
    "sqs": {
        "type": "managed queue",
        "scale": "100-10,000 concurrent tasks",
        "durability": "high (SQS persists to disk)",
        "replay": "no (Standard queue has no replay; FIFO supports redrive)",
        "ordering": "FIFO only (Standard is best-effort ordering)",
        "cost_per_1m_requests_usd": 0.40,
        "best_for": "AWS customers, simple async tasks, no replay",
        "weakness": "no replay; Standard has at-least-once (may have duplicates)",
    },
    "kafka": {
        "type": "distributed log (self-hosted or managed)",
        "scale": "10,000-1,000,000+ events/sec",
        "durability": "very high (replicated across brokers)",
        "replay": "yes (consumers have offsets; can reset to any point)",
        "ordering": "per-partition (ordered within a partition)",
        "cost_per_1m_requests_usd": 0.10,  # MSK
        "best_for": "high throughput, event sourcing, multiple consumers, replay",
        "weakness": "operational overhead (ZooKeeper, partitions, brokers); complex to scale",
    },
    "redis_streams": {
        "type": "in-memory log (in Redis)",
        "scale": "100-1,000 concurrent tasks",
        "durability": "medium (configurable persistence; can lose data on crash)",
        "replay": "yes (consumers have IDs; can replay from any point)",
        "ordering": "yes (FIFO within a stream)",
        "cost_per_1m_requests_usd": "minimal (existing Redis)",
        "best_for": "existing Redis, low latency, simple setup",
        "weakness": "limited by Redis memory; not as durable as SQS/Kafka",
    },
}
```

The "agent as a worker" pattern (the canonical async agent):

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Customer │────▶│   API    │────▶│   SQS    │────▶│  Agent   │
│ (POST)   │     │ (enqueue)│     │ (queue)  │     │ (worker) │
└──────────┘     └──────────┘     └──────────┘     └────┬─────┘
     ▲                                                   │
     │                                                   ▼
     │             ┌──────────┐                    ┌──────────┐
     └─────────────│ Callback │◀───────────────────│ Webhook  │
       (poll/wait) │ (POST)   │   (task complete) │ (call)   │
                   └──────────┘                    └──────────┘
```

The SQS + agent worker (the production code):

```python
import boto3
import json
from agent import run_agent

sqs = boto3.client("sqs")
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123/atlasmart-agent-tasks"

def enqueue_task(goal: str, tenant: str, callback_url: str) -> str:
    """Enqueue a task; return the task ID."""
    task_id = str(uuid.uuid4())
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps({
            "task_id": task_id,
            "goal": goal,
            "tenant": tenant,
            "callback_url": callback_url,
        }),
    )
    return task_id

def process_tasks():
    """The agent worker; runs continuously, polls the queue, processes tasks."""
    while True:
        # Long polling: receive up to 10 messages, wait up to 20s
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
        )
        for message in response.get("Messages", []):
            task = json.loads(message["body"])
            try:
                # Process the task
                result = run_agent(goal=task["goal"], tenant=task["tenant"])
                # Send the result to the callback URL
                requests.post(task["callback_url"], json={
                    "task_id": task["task_id"],
                    "status": "success",
                    "result": result,
                }, timeout=5)
                # Delete the message from the queue
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=message["ReceiptHandle"],
                )
            except Exception as e:
                # The message will be retried (SQS visibility timeout)
                # After max retries, the message goes to the DLQ
                logger.exception(f"Task {task['task_id']} failed: {e}")
```

The 4 broker-decision scenarios:

```python
BROKER_SCENARIOS = {
    "northwind_synchronous": {
        "scale": "200 leads/day = 5 concurrent",
        "latency": "5 seconds is fine",
        "durability": "low (if the request fails, the customer can retry)",
        "verdict": "synchronous HTTP (no broker needed)",
    },
    "atlasmart_queue": {
        "scale": "5,000 requests/day = 200 concurrent",
        "latency": "agent latency is 5s; customer is OK with webhook",
        "durability": "high (don't lose customer requests)",
        "verdict": "SQS (managed, simple, durable)",
    },
    "enterprise_pub_sub": {
        "scale": "50,000 events/day = 2,000 concurrent",
        "latency": "low (event-driven)",
        "durability": "very high (compliance)",
        "replay": "required (audit + analytics)",
        "verdict": "Kafka (high throughput + replay)",
    },
    "existing_redis_streams": {
        "scale": "500 tasks/day = 20 concurrent",
        "latency": "low (Redis is fast)",
        "durability": "medium (Redis is in-memory; persistence is configurable)",
        "verdict": "Redis Streams (existing infrastructure)",
    },
}
```

The pattern that wins interviews is the "4 patterns × 3 brokers + agent as worker" pattern. The candidate who says "I pick synchronous for <50 concurrent; SQS for 100-10,000 with durability; Kafka for 10,000+ with replay; Redis Streams for existing Redis. The agent is a worker; the API enqueues; the agent processes; the result is returned via webhook. The wrong choice is Kafka for 100 concurrent (over-engineering). The wrong choice is synchronous for 1,000 concurrent (lost tasks). The right choice is the broker that matches the scale + durability + replay requirements" is the candidate who demonstrates the broker-mindset.

## Code or example

The 5 most common broker errors and fixes:

```python
BROKER_ERRORS = {
    "message_loss": {
        "symptom": "Tasks submitted but never processed",
        "cause": "Agent crashed; message was in flight; not yet visible to another agent",
        "fix": "SQS visibility timeout (default 30s); increase the agent's processing timeout; add a DLQ for messages that exceed max retries",
    },
    "duplicate_processing": {
        "symptom": "Task processed twice (duplicate customer requests)",
        "cause": "Agent processed the message but crashed before deleting it; another agent picked it up",
        "fix": "Use idempotency keys (Section 6.3 pattern); the agent checks if the task was already processed before re-processing",
    },
    "queue_backlog": {
        "symptom": "Queue depth grows; tasks processed with high latency",
        "cause": "Agent can't keep up with the arrival rate",
        "fix": "Scale the agent (more replicas); add a circuit breaker to shed load; alert when queue depth > threshold",
    },
    "poison_message": {
        "symptom": "Agent crashes on the same message repeatedly",
        "cause": "Bug in the agent; the message triggers the bug every time",
        "fix": "Add max retries; send to DLQ after max retries; investigate the DLQ messages",
    },
    "consumer_lag": {
        "symptom": "Consumer is far behind the producer; events are delayed",
        "cause": "Consumer is slow; consumer crashed; consumer is on a different partition",
        "fix": "Scale the consumer; check consumer health; rebalance the partitions",
    },
}
```

The 3 visibility patterns (how the customer gets the result):

```python
VISIBILITY_PATTERNS = {
    "callback_webhook": {
        "description": "The agent calls the customer's webhook when done",
        "code": "requests.post(callback_url, json={'task_id': task_id, 'result': result})",
        "best_for": "Customer has a public webhook endpoint; low latency",
        "weakness": "Customer's webhook might be down; need retry logic",
    },
    "polling": {
        "description": "The customer polls the API for the result",
        "code": "GET /tasks/{task_id}/result → 200 with result or 202 still processing",
        "best_for": "Customer doesn't have a webhook; simpler integration",
        "weakness": "Polling overhead; latency depends on poll interval",
    },
    "sse_streaming": {
        "description": "The API streams events as the agent processes (Server-Sent Events)",
        "code": "EventSource('/tasks/{task_id}/stream')",
        "best_for": "Customer wants progress updates; long-running tasks",
        "weakness": "Connection must be maintained; not all clients support SSE",
    },
}
```

The AtlasMart broker setup (the case study):

```python
ATLASMART_BROKER = {
    "primary_broker": {
        "type": "SQS",
        "queue_name": "atlasmart-agent-tasks",
        "use_case": "async agent tasks (long-running)",
        "configuration": {
            "visibility_timeout_s": 60,  # agent has 60s to process before retry
            "message_retention_s": 345600,  # 4 days
            "max_receive_count": 3,  # send to DLQ after 3 failed attempts
            "dlq_name": "atlasmart-agent-tasks-dlq",
        },
        "monthly_volume": "150,000 messages (5,000/day * 30)",
        "monthly_cost": "$0.06",
    },
    "synchronous_api": {
        "type": "HTTP REST",
        "use_case": "interactive requests (customer waits for the response)",
        "configuration": {
            "timeout_s": 30,
            "max_concurrent": 50,
        },
        "monthly_volume": "100,000 requests",
        "monthly_cost": "$0 (no broker)",
    },
    "decision_rubric": "Interactive → sync HTTP; long-running → SQS; high throughput + replay → Kafka",
    "alert_thresholds": {
        "queue_depth": "> 1000 messages for > 5 min (page on-call)",
        "dlq_depth": "> 10 messages (page on-call, investigate)",
        "processing_latency_p95": "> 30s (warning)",
    },
}
```

## Production addendum

The message broker question is the answer to "how do you handle 1000s of concurrent runs." The 60-second script:

> "4 patterns: synchronous (HTTP, <50 concurrent, no durability); queue (SQS, 100-10,000, durable, point-to-point); pub-sub (Kafka, 10,000+, durable, fan-out); event sourcing (Kafka + log, 10,000+, replay, audit). 3 brokers: SQS (managed, simple), Kafka (high-throughput, replay), Redis Streams (existing Redis, low-latency). The agent is a worker; the API enqueues; the agent processes; the result is returned via webhook. The wrong choice is Kafka for 100 concurrent (over-engineering). The wrong choice is synchronous for 1,000 concurrent (lost tasks). The right choice is the broker that matches the scale + durability + replay requirements."

This is the difference between a candidate who says "I added a queue" and a candidate who says "4 patterns × 3 brokers, agent as worker, 3 visibility patterns, 5 most common errors, the queue depth + DLQ + processing latency alerts." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/service/circuit.py` — the SQS worker implementation.
- **Reference implementation**: `course/hardcode/level-7-real-time-pipelines/15-kafka-ai-consumer.py` — the canonical broker setup.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — message brokers as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — multi-agent uses queues for fan-out.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — message brokers as a system design topic.

## The 3 questions this lecture preps you for

1. **"How do you handle 1000s of concurrent runs?"** Answer: use a message broker. SQS for 100-10,000 concurrent (managed, simple, durable). Kafka for 10,000+ concurrent (high-throughput, replay, multiple consumers). Redis Streams for existing Redis (low-latency, simple). The agent is a worker; the API enqueues; the agent processes; the result is returned via webhook.
2. **"What is the agent as a worker pattern?"** Answer: the API enqueues a task; the agent dequeues and processes; the result is returned via callback (POST to customer's URL), webhook (agent calls customer's URL when done), or polling (customer polls the API for the result). The pattern decouples API latency from agent latency; the customer sees a 100ms response; the agent processes for 5 seconds.
3. **"When do you use SQS vs Kafka?"** Answer: SQS for 100-10,000 concurrent tasks, managed simplicity, no replay needed, AWS-native. Kafka for 10,000+ events/sec, replay required, multiple consumers, event sourcing, audit trail. The wrong choice is Kafka for 100 concurrent (operational overhead + cost). The right choice is the broker that matches scale + durability + replay.

## Read next

`L8-4-observability-stack.md` — the observability pillar. The 3 pillars of observability (logs, metrics, traces) in production detail. OpenTelemetry, Prometheus, Grafana, Datadog, Honeycomb. The 3am dashboard that tells the on-call whether the agent is healthy.
