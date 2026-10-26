# Month 5: AI + Real-Time Streams — 30 Days of Hands-On Projects
### Theme: "AI that reacts in real-time"

**Data system:** Kafka/Redpanda + Redis Streams + RabbitMQ
**Tools:** Python 3.10+, kafka-python, redis, aio-pika (RabbitMQ), asyncio, OpenTelemetry
**Setup time:** 30 min
**Time per project:** 30-90 min
**Total time:** ~28 hours over 30 days

---

## Setup (do this once, before Day 121)

```bash
mkdir ai-daily && cd ai-daily
python -m venv venv && source venv/bin/activate
pip install openai redis aio-pika kafka-python httpx python-dotenv streamlit opentelemetry-api opentelemetry-sdk

# Local services via Docker
docker run -d -p 6379:6379 --name redis redis:7-alpine
docker run -d -p 9092:9092 -p 9644:9644 --name redpanda \
  -v redpanda_data:/var/lib/redpanda/data \
  docker.redpanda.com/redpandadata/redpanda:latest \
  redpanda start --overprovisioned --smp 1 --memory 1G --reserve-memory 0M \
  --node-id 0 --check=false --kafka-addr PLAINTEXT://0.0.0.0:9092 \
  --advertise-kafka-addr PLAINTEXT://localhost:9092

docker run -d -p 5672:5672 --name rabbitmq rabbitmq:3-management
```

---

## Day 121: Redis Streams Pub/Sub (30 min)

```python
# day121_redis_streams.py
import redis
import time
import json
import threading

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
STREAM = "events"

def producer():
    """Add events to the stream."""
    for i in range(5):
        r.xadd(STREAM, {"type": "page_view", "user_id": f"u_{i}", "path": f"/page/{i}"})
        time.sleep(0.5)

def consumer(group: str = "workers", consumer: str = "c1"):
    """Consume events with a consumer group."""
    try:
        r.xgroup_create(STREAM, group, id="0", mkstream=True)
    except redis.exceptions.ResponseError:
        pass  # group exists
    while True:
        msgs = r.xreadgroup(group, consumer, {STREAM: ">"}, count=10, block=1000)
        for stream, entries in msgs:
            for msg_id, data in entries:
                print(f"  {consumer} got {msg_id}: {data}")
                r.xack(STREAM, group, msg_id)

# Demo: 1 producer + 2 consumers
threading.Thread(target=producer, daemon=True).start()
threading.Thread(target=consumer, consumer="c1", daemon=True).start()
threading.Thread(target=consumer, consumer="c2", daemon=True).start()
time.sleep(5)
```

**Stretch:** `xtrim` for stream length cap, entry IDs as timestamps, blocking reads with timeout.
**Architect note:** Redis Streams give you Kafka-like semantics in 1MB of code. Great for <100K msg/s. Beyond that, use Kafka.

---

## Day 122: Producer/Consumer Pattern (45 min)

```python
# day122_producer_consumer.py
import redis
import json
import time
from dataclasses import dataclass
from typing import Callable

@dataclass
class Job:
    id: str
    payload: dict
    attempts: int = 0

class JobQueue:
    def __init__(self, redis_client: redis.Redis, name: str = "jobs"):
        self.r = redis_client
        self.name = name

    def push(self, payload: dict) -> str:
        job_id = f"{time.time_ns()}"
        self.r.hset(f"{self.name}:jobs", job_id, json.dumps({"payload": payload, "attempts": 0}))
        self.r.lpush(f"{self.name}:queue", job_id)
        return job_id

    def pop(self, timeout: int = 5) -> Job | None:
        result = self.r.brpop(f"{self.name}:queue", timeout=timeout)
        if not result:
            return None
        _, job_id = result
        raw = self.r.hget(f"{self.name}:jobs", job_id)
        if not raw:
            return None
        data = json.loads(raw)
        return Job(id=job_id, payload=data["payload"], attempts=data["attempts"])

    def complete(self, job: Job):
        self.r.hdel(f"{self.name}:jobs", job.id)

    def retry(self, job: Job, delay: int = 0):
        job.attempts += 1
        if delay > 0:
            time.sleep(delay)
        self.r.hset(f"{self.name}:jobs", job.id, json.dumps({"payload": job.payload, "attempts": job.attempts}))
        self.r.lpush(f"{self.name}:queue", job.id)

# Worker
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
q = JobQueue(r, "ai-jobs")

def handle_llm_job(payload: dict) -> dict:
    # Real work here
    return {"answer": f"Processed {payload.get('q', '?')}"}

# Enqueue
q.push({"q": "What is 2+2?"})

# Process
while True:
    job = q.pop(timeout=2)
    if not job:
        break
    try:
        result = handle_llm_job(job.payload)
        print(f"OK: {result}")
        q.complete(job)
    except Exception as e:
        if job.attempts < 3:
            q.retry(job, delay=2 ** job.attempts)
        else:
            q.complete(job)  # dead letter in real impl
```

**Stretch:** Priority queue (sorted set), delayed jobs (ZADD with score=execute_at), dead-letter queue.
**Architect note:** A simple Redis-backed queue is the right answer for 90% of "I need a queue" use cases. Reach for Kafka/PubSub only when you have 100K+ msg/s or need replay.

---

## Day 123: Worker Pool with Concurrency (45 min)

```python
# day123_worker_pool.py
import asyncio
import redis.asyncio as redis
from openai import OpenAI
import os
import time

client = OpenAI()
r = redis.from_url("redis://localhost:6379")
QUEUE = "ai-jobs"

async def worker(name: str):
    while True:
        # BRPOP is blocking — efficient idle
        result = await r.brpop(QUEUE, timeout=5)
        if not result:
            continue
        _, payload = result
        try:
            data = __import__("json").loads(payload)
            t0 = time.time()
            resp = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": data["q"]}],
            )
            print(f"  [{name}] {time.time()-t0:.2f}s → {resp.choices[0].message.content[:60]}")
            await r.lpush(f"{QUEUE}:results", resp.choices[0].message.content)
        except Exception as e:
            print(f"  [{name}] error: {e}")
            await r.lpush(f"{QUEUE}:dead", payload)

async def main():
    # Start 5 workers
    await asyncio.gather(*[worker(f"w{i}") for i in range(5)])

# Enqueue some jobs
async def enqueue():
    for i in range(20):
        await r.lpush(QUEUE, __import__("json").dumps({"q": f"Question {i}"}))

# asyncio.run(enqueue())
# asyncio.run(main())
```

**Stretch:** Auto-scaling workers, throughput monitoring, queue depth alerting.
**Architect note:** Worker concurrency is bounded by the downstream API rate limit, not by your CPU. Always check the API's rate limit header.

---

## Day 124: Dead-Letter Queue (30 min)

```python
# day124_dlq.py
import json
import redis
import time
from openai import OpenAI
from day122_producer_consumer import JobQueue

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
q = JobQueue(r, "ai-jobs")
DLQ = JobQueue(r, "ai-jobs-dlq")
client = OpenAI()

MAX_ATTEMPTS = 3

def process_with_retry(job):
    try:
        # Simulate LLM call
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": job.payload["q"]}],
        )
        return {"ok": True, "answer": resp.choices[0].message.content}
    except Exception as e:
        return {"ok": False, "error": str(e)}

while True:
    job = q.pop(timeout=2)
    if not job:
        break
    result = process_with_retry(job)
    if result["ok"]:
        q.complete(job)
    else:
        if job.attempts + 1 >= MAX_ATTEMPTS:
            print(f"  → DLQ: {job.id} ({result['error']})")
            DLQ.push({**job.payload, "last_error": result["error"], "attempts": job.attempts + 1})
            q.complete(job)
        else:
            q.retry(job, delay=2 ** job.attempts)
            print(f"  retry {job.attempts + 1}/{MAX_ATTEMPTS}: {job.id}")
```

**Stretch:** DLQ dashboard, automatic replay tool, alert on DLQ depth.
**Architect note:** A dead-letter queue is a *diagnostic tool*, not a graveyard. Every DLQ entry should be reviewed and either fixed (replay) or discarded with a reason.

---

## Day 125: Idempotency Keys (45 min)

```python
# day125_idempotency.py
import redis
import hashlib
import json
import time

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def idempotent(fn, ttl: int = 86400):
    """Cache function results by args hash for `ttl` seconds."""
    def wrapper(*args, **kwargs):
        key_data = json.dumps((args, sorted(kwargs.items())), default=str)
        cache_key = f"idem:{fn.__name__}:{hashlib.md5(key_data.encode()).hexdigest()}"
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)
        result = fn(*args, **kwargs)
        r.setex(cache_key, ttl, json.dumps(result, default=str))
        return result
    return wrapper

@idempotent
def create_user(email: str, name: str) -> dict:
    # Simulated side-effect
    return {"id": f"u_{int(time.time())}", "email": email, "name": name}

# Same args → same result (cached)
print(create_user("a@b.com", "Alice"))
print(create_user("a@b.com", "Alice"))  # cached, same id
```

**Stretch:** Idempotency keys for HTTP endpoints (Stripe-style), partial-result caching.
**Architect note:** Idempotency is what lets you safely retry. Without it, you get duplicate users, duplicate charges, duplicate emails.

---

## Day 126: Priority Queues (45 min)

```python
# day126_priority.py
import redis
import json
import time

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Multiple queues, one per priority
PRIORITIES = ["p0_critical", "p1_high", "p2_normal", "p3_low"]

def enqueue(priority: str, payload: dict):
    assert priority in PRIORITIES
    score = PRIORITIES.index(priority) * 1_000_000_000 + time.time_ns()  # FIFO within priority
    r.zadd("queue:priority", {json.dumps(payload): score})

def dequeue() -> dict | None:
    # Always pull the highest-priority first
    items = r.zrange("queue:priority", 0, 0)
    if not items:
        return None
    item = items[0]
    r.zrem("queue:priority", item)
    return json.loads(item)

# Demo
enqueue("p2_normal", {"task": "send_newsletter"})
enqueue("p0_critical", {"task": "alert_oncall"})
enqueue("p2_normal", {"task": "send_newsletter_2"})
enqueue("p1_high", {"task": "process_payment"})

while True:
    item = dequeue()
    if not item:
        break
    print(item)
```

**Stretch:** Starvation prevention (boost p2 if waiting too long), multi-dimensional priority.
**Architect note:** Priority queues are easy to get wrong — without starvation protection, low-priority work can wait forever.

---

## Day 127: WEEKEND — Async Job System (3 hours)

Build a job system with:
- Priority queues
- Worker pool
- Dead-letter
- Idempotency
- Status tracking (queued/running/done/failed)
- Web UI dashboard (Streamlit)
- Deploy to Fly.io

**Architect note:** A "real" job system is more than a queue — it's observability. Every job needs a status, duration, error, retry count, and a way to find it later.

---

## Day 128: Kafka Producer with Redpanda (45 min)

```python
# day128_kafka_producer.py
from kafka import KafkaProducer
import json
import time
import os

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode(),
    key_serializer=lambda k: k.encode() if k else None,
    acks="all",  # wait for all replicas
    retries=3,
    linger_ms=10,  # batch up to 10ms
)

def emit(topic: str, key: str, value: dict):
    future = producer.send(topic, key=key, value=value)
    return future.get(timeout=10)

# Demo
for i in range(100):
    emit("user_events", key=f"user_{i % 10}", value={
        "type": "click", "user_id": f"user_{i % 10}", "page": f"/page/{i}",
        "ts": time.time(),
    })

producer.flush()
print("Sent 100 events")
```

**Stretch:** Compression (`snappy`), idempotent producer, partitioner customization.
**Architect note:** `acks="all"` is the safe default. `linger_ms=10` trades latency for throughput — for low-latency, use 0; for high-throughput, use 100-1000.

---

## Day 129: Kafka Consumer + Offset Management (45 min)

```python
# day129_kafka_consumer.py
from kafka import KafkaConsumer
import json
import time
from openai import OpenAI

client = OpenAI()

consumer = KafkaConsumer(
    "user_events",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda v: json.loads(v.decode()),
    key_deserializer=lambda k: k.decode() if k else None,
    group_id="ai-processor",
    auto_offset_reset="earliest",  # or "latest" for new events only
    enable_auto_commit=False,       # manual commit for at-least-once
    max_poll_records=10,
)

def process(event: dict) -> str:
    """Simulated AI processing."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Categorize: {event.get('page', '')}"}],
    )
    return resp.choices[0].message.content

count = 0
for msg in consumer:
    try:
        result = process(msg.value)
        print(f"  partition={msg.partition} offset={msg.offset} → {result[:50]}")
        consumer.commit()  # commit only after success
        count += 1
        if count >= 50:
            break
    except Exception as e:
        print(f"  error: {e}")
        # Don't commit — message will be reprocessed
```

**Stretch:** Exactly-once semantics, batch commit, manual seek.
**Architect note:** `enable_auto_commit=False` is the safe default for at-least-once. Exactly-once requires idempotency on the consumer side.

---

## Day 130: Topic Partitioning (45 min)

```python
# day130_partitioning.py
from kafka import KafkaProducer, KafkaConsumer
import json
import time

# Producer with custom partitioner (key hash → partition)
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode(),
    key_serializer=lambda k: k.encode() if k else None,
    partitioner=lambda key_bytes, all_partitions, available: (
        hash(key_bytes) % len(all_partitions) if key_bytes else 0
    ),
)

# Create topic with 4 partitions (via CLI: kafka-topics --create --partitions 4 ...)
# Same key → same partition (order preserved per key)
for i in range(20):
    producer.send("user_events", key=f"user_{i % 5}", value={"i": i})

producer.flush()

# Consumer reads from all partitions
consumer = KafkaConsumer(
    "user_events", bootstrap_servers="localhost:9092",
    group_id="p-demo", value_deserializer=lambda v: json.loads(v.decode()),
    key_deserializer=lambda k: k.decode() if k else None,
    auto_offset_reset="earliest",
)

for msg in consumer:
    print(f"  p={msg.partition} key={msg.key} value={msg.value}")
```

**Stretch:** Custom partitioner (sticky, round-robin, geo), partition rebalance, partition count tuning.
**Architect note:** Partition count = max parallelism. For 10K msg/s with 10ms processing, 4 partitions handle 2.5K each. Add partitions as you grow.

---

## Day 131: Consumer Groups (45 min)

```python
# day131_consumer_groups.py
import subprocess
from kafka import KafkaConsumer
import json
import time
import threading

def worker(name: str, group: str = "ai-group"):
    consumer = KafkaConsumer(
        "user_events", bootstrap_servers="localhost:9092",
        group_id=group, value_deserializer=lambda v: json.loads(v.decode()),
        auto_offset_reset="earliest",
    )
    for msg in consumer:
        time.sleep(0.5)  # simulate work
        print(f"  [{name}] p={msg.partition} offset={msg.offset} key={msg.key}")

# Same group = load balanced (each message to one consumer)
# Different groups = broadcast (each consumer gets all messages)
# Start 3 workers in the same group
for i in range(3):
    threading.Thread(target=worker, args=(f"w{i}", "ai-group"), daemon=True).start()

time.sleep(10)

# List groups
# subprocess.run(["kafka-consumer-groups", "--bootstrap-server", "localhost:9092", "--list"])
```

**Stretch:** Static membership (no rebalance), custom assignment, partition assignment strategy.
**Architect note:** Consumer group = horizontal scaling. Same group + more workers = more throughput. Different group = independent view (good for read replicas).

---

## Day 132: Schema Registry with JSON Schema (45 min)

```python
# day132_schema.py
import json
from jsonschema import validate, ValidationError
from typing import Any

SCHEMAS = {
    "user_event": {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["click", "view", "purchase"]},
            "user_id": {"type": "string"},
            "ts": {"type": "number"},
            "page": {"type": "string"},
        },
        "required": ["type", "user_id", "ts"],
    },
    "ai_response": {
        "type": "object",
        "properties": {
            "request_id": {"type": "string"},
            "model": {"type": "string"},
            "content": {"type": "string"},
            "tokens": {"type": "integer"},
        },
        "required": ["request_id", "model", "content"],
    },
}

def validate_event(schema_name: str, data: Any):
    try:
        validate(data, SCHEMAS[schema_name])
        return True, None
    except ValidationError as e:
        return False, str(e)

# Demo
ok, err = validate_event("user_event", {"type": "click", "user_id": "u_1", "ts": time.time()})
print(f"valid: {ok}, err: {err}")
```

**Stretch:** Confluent Schema Registry, Avro/Protobuf for binary efficiency, schema evolution rules.
**Architect note:** Schemas are the API contract of your event stream. Without them, every change is a breaking change.

---

## Day 133: Stream Processing Basics (60 min)

```python
# day133_stream_processing.py
from kafka import KafkaConsumer
from collections import defaultdict
import json
import time

consumer = KafkaConsumer(
    "user_events", bootstrap_servers="localhost:9092",
    group_id="stream-processor", value_deserializer=lambda v: json.loads(v.decode()),
    auto_offset_reset="earliest",
)

# Stateful stream processing: per-user event count in 60s windows
user_counts: dict[str, list[float]] = defaultdict(list)
WINDOW = 60.0  # seconds

def process(events_batch: list[dict]) -> list[dict]:
    now = time.time()
    # Add events
    for e in events_batch:
        user_counts[e["user_id"]].append(now)
    # Trim old
    for user in list(user_counts.keys()):
        user_counts[user] = [t for t in user_counts[user] if now - t < WINDOW]
        if not user_counts[user]:
            del user_counts[user]
    # Output alerts for high-velocity users
    alerts = []
    for user, times in user_counts.items():
        if len(times) > 10:
            alerts.append({"user_id": user, "events_in_60s": len(times)})
    return alerts

batch = []
for msg in consumer:
    batch.append(msg.value)
    if len(batch) >= 20:
        alerts = process(batch)
        for a in alerts:
            print(f"  ALERT: {a}")
        batch = []
```

**Stretch:** Tumbling vs sliding windows, watermark handling, late events.
**Architect note:** Stream processing state must be externalized (Redis, RocksDB) for crash recovery. In-memory state is fine for ephemeral analytics.

---

## Day 134: WEEKEND — Real-Time Log Pipeline (3 hours)

Build a log ingestion pipeline:
- Filebeat / Vector → Kafka
- Kafka → Stream processor (Day 133) for aggregations
- Anomaly detection (spike alerts)
- LLM-powered log summarization
- Web UI dashboard
- Deploy to Fly.io

**Architect note:** Real-time log pipelines are the foundation of SRE work. The AI add-on (LLM summarization) is what makes them *useful* to humans.

---

## Day 135: Event → AI → Action Pattern (60 min)

```python
# day135_event_ai_action.py
import redis
import json
import time
from openai import OpenAI

client = OpenAI()
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
EVENTS = "raw_events"
ACTIONS = "actions"

# Producer
def produce_event(event: dict):
    r.xadd(EVENTS, event)

# Consumer: classify event with LLM, route to action queue
def classify_and_route(event: dict) -> dict | None:
    if event.get("type") != "message":
        return None
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content":
            f"Classify this event. Reply JSON: {{\"action\": \"notify|ignore|escalate\", \"reason\": \"...\"}}\n\n{json.dumps(event)}"}],
        response_format={"type": "json_object"},
    )
    decision = json.loads(resp.choices[0].message.content)
    if decision["action"] != "ignore":
        return {"event": event, "decision": decision}
    return None

# Action handler
def handle_action(action: dict):
    decision = action["decision"]
    if decision["action"] == "notify":
        r.xadd("notifications", {"msg": f"Notification: {decision['reason']}"})
    elif decision["action"] == "escalate":
        r.xadd("escalations", {"msg": f"ESCALATION: {decision['reason']}"})

# Loop
def consumer_loop():
    last_id = "$"
    while True:
        msgs = r.xread({EVENTS: last_id}, count=10, block=1000)
        for stream, entries in msgs:
            for msg_id, data in entries:
                action = classify_and_route(data)
                if action:
                    handle_action(action)
                last_id = msg_id

# consumer_loop()
```

**Stretch:** Multi-step AI (plan → decide → act), feedback loop, A/B test decision strategies.
**Architect note:** The "event → AI → action" pattern is the core of agent systems. The hard part is *reliability* — the AI must be predictable enough to put in a hot loop.

---

## Day 136: Stream Enrichment with LLM (45 min)

```python
# day136_enrich.py
from kafka import KafkaConsumer, KafkaProducer
import json
from openai import OpenAI
import time

client = OpenAI()
consumer = KafkaConsumer(
    "raw_events", bootstrap_servers="localhost:9092",
    group_id="enricher", value_deserializer=lambda v: json.loads(v.decode()),
    auto_offset_reset="earliest",
)
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode(),
    key_serializer=lambda k: k.encode() if k else None,
)

def enrich(event: dict) -> dict:
    """Add LLM-generated tags, sentiment, summary."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content":
            f"""Add metadata to this event. Return JSON: {{"sentiment": "positive|negative|neutral", "tags": ["..."], "summary": "..."}}
Event: {json.dumps(event)}"""}],
        response_format={"type": "json_object"},
    )
    enrichment = json.loads(resp.choices[0].message.content)
    return {**event, "enrichment": enrichment, "enriched_at": time.time()}

for msg in consumer:
    enriched = enrich(msg.value)
    producer.send("enriched_events", key=msg.key, value=enriched)
    print(f"  enriched {msg.key}")
```

**Stretch:** Cache enrichment per (event_hash), batch enrichment, multi-language detection.
**Architect note:** Enrichment should be *idempotent* — the same event must always produce the same enrichment. Use a stable hash of the input as the cache key.

---

## Day 137: Real-Time Content Moderation (60 min)

```python
# day137_moderation.py
import redis
import json
from openai import OpenAI

client = OpenAI()
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def moderate(text: str) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content":
            f"""Moderate this message. Reply JSON: {{"verdict": "allow|warn|delete|escalate", "categories": ["hate"|"spam"|"violence"|"nsfw"|...], "confidence": 0-1, "reason": "..."}}

Message: "{text}"""}],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)

def moderation_loop():
    last_id = "$"
    while True:
        msgs = r.xread({"messages:incoming": last_id}, count=10, block=1000)
        for stream, entries in msgs:
            for msg_id, data in entries:
                verdict = moderate(data["text"])
                r.xadd(f"moderation:{verdict['verdict']}", {"msg_id": msg_id, "data": json.dumps(data), "verdict": json.dumps(verdict)})
                last_id = msg_id

# moderation_loop()
```

**Stretch:** Confidence threshold (low → human review), per-channel policies, A/B test prompt variations.
**Architect note:** Never auto-delete on AI verdict alone. Always have a human-review queue for borderline cases.

---

## Day 138: Live Chat AI Assistant (60 min)

```python
# day138_chat_assistant.py
import redis
import json
import time
from openai import OpenAI

client = OpenAI()
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

HISTORY_KEY = "chat:{user_id}:history"

def chat(user_id: str, message: str) -> str:
    history_key = HISTORY_KEY.format(user_id=user_id)
    history = r.lrange(history_key, 0, 19)  # last 10 turns
    history = [json.loads(m) for m in history]

    messages = [
        {"role": "system", "content": "You are a helpful AI assistant in a live chat. Be concise."},
        *history,
        {"role": "user", "content": message},
    ]
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply = resp.choices[0].message.content

    # Update history (with TTL)
    pipe = r.pipeline()
    pipe.rpush(history_key, json.dumps({"role": "user", "content": message}))
    pipe.rpush(history_key, json.dumps({"role": "assistant", "content": reply}))
    pipe.ltrim(history_key, -20, -1)
    pipe.expire(history_key, 3600)
    pipe.execute()

    # Publish to channel for real-time delivery
    r.publish(f"chat:{user_id}", json.dumps({"role": "assistant", "content": reply}))
    return reply

# chat("u_123", "What's the weather?")
```

**Stretch:** Streaming responses via pub/sub, multi-channel routing, sentiment-aware responses.
**Architect note:** Chat history in Redis is fine for single-session. For cross-session memory, use a vector store with conversation summaries.

---

## Day 139: Real-Time Translation Pipeline (60 min)

```python
# day139_translate.py
import redis
import json
from openai import OpenAI

client = OpenAI()
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def translate(text: str, target: str = "en") -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content":
            f"Translate to {target}. Reply with ONLY the translation, no preamble.\n\n{text}"}],
    )
    return resp.choices[0].message.content.strip()

def translation_loop():
    last_id = "$"
    while True:
        msgs = r.xread({"messages:raw": last_id}, count=20, block=1000)
        for stream, entries in msgs:
            for msg_id, data in entries:
                target = data.get("target_lang", "en")
                translated = translate(data["text"], target)
                r.xadd(f"messages:translated:{target}", {
                    "original": data["text"][:500],
                    "translated": translated,
                    "user_id": data.get("user_id", ""),
                })
                last_id = msg_id

# translation_loop()
```

**Stretch:** Per-language model selection (Whisper for speech), batch translation, glossary enforcement.
**Architect note:** GPT-4o-mini is 50+ languages. For domain-specific (legal, medical), fine-tune or use a glossary in the prompt.

---

## Day 140: Anomaly Detection on Streams (60 min)

```python
# day140_stream_anomaly.py
import redis
import time
import statistics
from collections import defaultdict

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
EVENTS = "metrics:raw"
ALERTS = "anomalies"

# Per-key sliding window
WINDOW = 60  # seconds
buckets: dict[str, list[tuple[float, float]]] = defaultdict(list)

def update(user: str, value: float):
    now = time.time()
    buckets[user].append((now, value))
    # Trim
    buckets[user] = [(t, v) for t, v in buckets[user] if now - t < WINDOW]

def detect(user: str) -> dict | None:
    series = buckets[user]
    if len(series) < 10:
        return None
    values = [v for _, v in series]
    mean = statistics.mean(values)
    stdev = statistics.stdev(values) or 1
    latest = values[-1]
    z = (latest - mean) / stdev
    if abs(z) > 3:
        return {"user": user, "value": latest, "z_score": round(z, 2), "mean": round(mean, 2)}
    return None

def loop():
    last_id = "$"
    while True:
        msgs = r.xread({EVENTS: last_id}, count=50, block=1000)
        for stream, entries in msgs:
            for msg_id, data in entries:
                user = data["user"]
                value = float(data["value"])
                update(user, value)
                anomaly = detect(user)
                if anomaly:
                    r.xadd(ALERTS, anomaly)
                    print(f"  ANOMALY: {anomaly}")
                last_id = msg_id

# loop()
```

**Stretch:** Multi-variate anomaly detection, model retraining on confirmed anomalies, alert dedup.
**Architect note:** Anomaly detection is only useful if you can act on it. Wire every alert to PagerDuty/Slack with runbook link.

---

## Day 141: WEEKEND — Real-Time AI Dashboard (3 hours)

Build a dashboard showing:
- Event throughput (per topic, per consumer)
- AI decision latency (p50, p95, p99)
- Cost per event
- Anomaly count
- Live event stream
- Deploy to Fly.io

**Architect note:** A dashboard without alerts is wallpaper. Every chart needs a "if X > Y, page someone" rule.

---

## Day 142: OpenTelemetry Tracing (60 min)

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-httpx opentelemetry-exporter-otlp
```

```python
# day142_otel.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
import httpx
import time

# Setup
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317")))
trace.set_tracer_provider(provider)
HTTPXClientInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

def process_event(event: dict) -> dict:
    with tracer.start_as_current_span("process_event") as span:
        span.set_attribute("event.type", event.get("type", ""))
        with tracer.start_as_current_span("classify"):
            r = httpx.post("https://api.openai.com/v1/chat/completions", json={...})
            # ... etc
        with tracer.start_as_current_span("route"):
            ...
        return {...}

# View traces at http://localhost:16686 (Jaeger) or Honeycomb
```

**Stretch:** Auto-instrumentation for SQL/Redis, custom span events, sampling strategies.
**Architect note:** Tracing turns "it's slow" into "this DB call takes 2s" — and that's the difference between a 5-minute fix and a 5-day hunt.

---

## Day 143: Metrics: Throughput, Latency, Errors (45 min)

```python
# day143_metrics.py
import time
import redis
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Prometheus metrics
events_total = Counter("events_processed_total", "Total events processed", ["topic", "status"])
event_latency = Histogram("event_latency_seconds", "Event processing latency", ["topic"])
queue_depth = Gauge("queue_depth", "Current queue depth", ["queue"])
errors_total = Counter("errors_total", "Total errors", ["type"])

# Expose on /metrics
start_http_server(8000)

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def process(topic: str, event: dict):
    start = time.time()
    try:
        # ... do work ...
        events_total.labels(topic=topic, status="ok").inc()
        event_latency.labels(topic=topic).observe(time.time() - start)
    except Exception as e:
        events_total.labels(topic=topic, status="error").inc()
        errors_total.labels(type=type(e).__name__).inc()
        raise

def update_queue_depth(queue: str):
    queue_depth.labels(queue=queue).set(r.llen(queue))

# Periodically update queue depth
import threading
def depth_loop():
    while True:
        update_queue_depth("ai-jobs")
        time.sleep(5)
threading.Thread(target=depth_loop, daemon=True).start()
```

**Stretch:** Alertmanager rules, recording rules, push gateway for batch jobs.
**Architect note:** Latency histograms need explicit buckets. `Histogram(buckets=(0.01, 0.05, 0.1, 0.5, 1, 5))` matches typical SLO buckets.

---

## Day 144: Cost Attribution per Consumer (45 min)

```python
# day144_cost.py
import redis
import json
import time
from collections import defaultdict

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Token costs (per 1M tokens)
COST = {
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "gpt-4o": {"in": 2.50, "out": 10.00},
    "text-embedding-3-small": {"in": 0.02, "out": 0},
}

def track(consumer: str, model: str, prompt_tokens: int, completion_tokens: int):
    cost = (
        prompt_tokens / 1_000_000 * COST[model]["in"] +
        completion_tokens / 1_000_000 * COST[model]["out"]
    )
    # Increment Redis counter
    r.incrbyfloat(f"cost:total:{consumer}", cost)
    r.incrby(f"tokens:in:{consumer}", prompt_tokens)
    r.incrby(f"tokens:out:{consumer}", completion_tokens)
    return cost

def get_costs() -> dict:
    consumers = ["ai-processor", "ai-enricher", "ai-moderator"]
    return {c: float(r.get(f"cost:total:{c}") or 0) for c in consumers}

# track("ai-processor", "gpt-4o-mini", 100, 50)
print(get_costs())
```

**Stretch:** Cost alerts (>$X/day), per-tenant cost breakdown, Grafana dashboard.
**Architect note:** Per-consumer cost attribution is the single most important metric for AI systems. Without it, you can't prioritize optimizations.

---

## Day 145: Auto-Scaling Workers (45 min)

```python
# day145_autoscale.py
import time
import threading
import redis
from day123_worker_pool import worker  # hypothetical

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
active_workers = []
MAX_WORKERS = 10
MIN_WORKERS = 2
SCALE_UP_THRESHOLD = 100   # queue depth
SCALE_DOWN_THRESHOLD = 5

def controller():
    while True:
        depth = r.llen("ai-jobs")
        workers = len(active_workers)
        if depth > SCALE_UP_THRESHOLD and workers < MAX_WORKERS:
            # Scale up
            t = threading.Thread(target=worker, args=(f"w{workers}",), daemon=True)
            t.start()
            active_workers.append(t)
            print(f"  scaled up: {workers+1} workers (depth={depth})")
        elif depth < SCALE_DOWN_THRESHOLD and workers > MIN_WORKERS:
            # Scale down (just stop the thread — daemon dies with main)
            active_workers.pop()
            print(f"  scaled down: {len(active_workers)} workers")
        time.sleep(10)

# controller()
```

**Stretch:** Predictive scaling (ML on queue depth), per-topic scaling, K8s HPA integration.
**Architect note:** Auto-scaling is harder than it looks. Workers need warmup time, queue depth fluctuates, and scaling events cost money. Always add hysteresis (don't flip-flop).

---

## Day 146: Backpressure Handling (45 min)

```python
# day146_backpressure.py
import redis
import time

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
MAX_QUEUE_DEPTH = 1000

def push_with_backpressure(payload: str) -> bool:
    """Returns False if rejected due to backpressure."""
    depth = r.llen("ai-jobs")
    if depth >= MAX_QUEUE_DEPTH:
        return False
    r.lpush("ai-jobs", payload)
    return True

def adaptive_throttle():
    """Producer slows down when queue is filling."""
    while True:
        depth = r.llen("ai-jobs")
        ratio = depth / MAX_QUEUE_DEPTH
        if ratio < 0.5:
            sleep_s = 0
        elif ratio < 0.8:
            sleep_s = 0.05
        else:
            sleep_s = 0.5
        # ... do producer work ...
        if sleep_s:
            time.sleep(sleep_s)

# Producer with backpressure
ok = push_with_backpressure('{"q": "..."}')
if not ok:
    return {"error": "queue full, try again later"}, 503
```

**Stretch:** Load shedding (drop low-priority first), circuit breaker on downstream, rate-limit at edge.
**Architect note:** Backpressure is the alternative to "queue blows up and OOMs." A 503 is better than a crashed process.

---

## Day 147: Multi-Region Replication (45 min)

```python
# day147_replication.py
"""
Multi-region Kafka replication via MirrorMaker 2.

Architecture:
  Region A (primary) ─── MirrorMaker 2 ──→ Region B (DR)
  Region A (primary) ─── MirrorMaker 2 ──→ Region C (read replica)

For disaster recovery:
  - Replicate async to DR
  - RPO (Recovery Point Objective): < 1 minute
  - RTO (Recovery Time Objective): < 5 minutes

For read replicas:
  - Replicate async
  - Region-local reads (lower latency)
  - Eventually consistent
"""

# Minimal config for MirrorMaker 2
MIRRORMAKER_CONFIG = """
clusters = primary, replica
primary.bootstrap.servers = region-a.kafka:9092
replica.bootstrap.servers = region-b.kafka:9092

primary->replica.enabled = true
primary->replica.topics = .*
replication.factor.of.configs = 3
refresh.topics.interval.seconds = 30
"""

# For application-level failover
import os

def get_kafka_brokers():
    region = os.environ.get("REGION", "us-east-1")
    brokers = {
        "us-east-1": "region-a.kafka:9092",
        "us-west-2": "region-b.kafka:9092",
    }
    return brokers[region]

# In Python code: from kafka import KafkaProducer
# producer = KafkaProducer(bootstrap_servers=get_kafka_brokers(), ...)
```

**Stretch:** Active-active multi-region, geo-routing, conflict resolution.
**Architect note:** Multi-region is *expensive* and *complex*. Only do it if your SLO requires it (most apps don't need it).

---

## Day 148: WEEKEND — Production-Grade Stream App (3 hours)

Build a production-grade stream app with:
- Multi-worker (Day 123)
- Backpressure (Day 146)
- Auto-scaling (Day 145)
- Tracing (Day 142)
- Metrics (Day 143)
- Cost tracking (Day 144)
- DLQ (Day 124)
- Health check endpoint
- Deploy to Fly.io + managed Kafka (Upstash / Redpanda Cloud)

**Architect note:** A "production-grade" app has 1) observability, 2) error handling, 3) graceful degradation, 4) automated recovery. The AI is the smallest part.

---

## Day 149: Load Test + Chaos Test (60 min)

Tools to use:
- **k6** for HTTP load testing
- **Locust** for Python load testing
- **Chaos Mesh** or AWS Fault Injection Simulator
- **Toxiproxy** for network latency/failure injection

```python
# day149_loadtest.py
"""Locust load test for the streaming API."""
from locust import HttpUser, task, between

class StreamUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def submit_event(self):
        self.client.post("/events", json={
            "type": "message", "text": "Hello world", "user_id": "u_load",
        })

# Run: locust -f day149_loadtest.py --host=http://localhost:8000
# Open http://localhost:8089 to start the test
```

Test scenarios:
- Steady 100 RPS for 10 min
- Spike to 1000 RPS for 1 min
- 50% failure rate in downstream
- Worker crash (kill -9) — system recovers?
- 10× traffic burst — queue depth stays bounded?

**Architect note:** Load tests find capacity limits. Chaos tests find *correctness* failures. You need both.

---

## Day 150: MONTH PROJECT — AI Incident Response for SREs (6 hours)

**Goal:** Real-time AI incident response system.

**Spec:**
- Logs stream in (via Vector/Fluent Bit)
- LLM classifies: severity, category, runbook
- Severity ≥ P2 → PagerDuty + Slack alert
- Runbook attached to alert
- SRE can ack via Slack button
- Auto-remediation for known issues (Day 124 retry patterns)
- Cost per incident tracked
- Dashboard with MTTR, MTTA
- Deploy to Fly.io + Upstash Kafka

**Architect note:** This is the SRE killer app. Companies pay $50K+/year for PagerDuty + StatusPage + custom runbook tools. Build it in a day.

---

## Month 5 Summary

**Built:** 30 projects · 1 async job system · 1 Kafka pipeline · 1 real-time AI dashboard · 1 incident response system
**Time:** ~30 hours over 30 days
**Cost:** ~$20 in API + cloud fees

**Key skills learned:**
- Redis Streams & queues
- Kafka / Redpanda fundamentals
- Event-driven AI patterns
- Real-time processing
- Observability (OpenTelemetry, Prometheus)
- Auto-scaling & backpressure
- Chaos engineering

**Next:** Month 6 — AI + Vector Search at Scale. 30 projects on Pinecone, Weaviate, Qdrant, Chroma, and your final capstone SaaS.
